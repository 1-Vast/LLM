"""Variant 2: positives are signatures of the same compound in two DIFFERENT core lines (blocks the same-plate
shortcut); optional transductive training on every compound's signatures (no viability values are read)."""
import sys
import numpy as np
import torch
import torch.nn.functional as F
sys.path.insert(0, ".")
from contrastive import Encoder, prep

def train(corpus, exclude, out, seed=0, steps=12000, batch=512, tau=0.1, corrupt=0.2, lr=1e-3, device="cuda"):
    rng = np.random.default_rng(seed); torch.manual_seed(seed)
    d = np.load(corpus, allow_pickle=True)
    key = np.where(d["ik14"] != "", d["ik14"], d["pert_id"])
    keep = ~np.isin(key, list(exclude))
    X, key, cell = d["x"][keep], key[keep], d["cell"][keep]
    tas = np.nan_to_num(d["tas"][keep])
    uk, inv = np.unique(key, return_inverse=True)
    uc, cinv = np.unique(cell, return_inverse=True)
    # per compound: list of per-cell index arrays
    order = np.lexsort((cinv, inv))
    groups = {}
    for i in order:
        groups.setdefault(inv[i], {}).setdefault(cinv[i], []).append(i)
    comps = [c for c, g in groups.items() if len(g) >= 2]
    cells = [[np.array(v) for v in groups[c].values()] for c in comps]
    w = np.array([tas[np.concatenate(cl)].max() for cl in cells]); p = (0.05 + w) / (0.05 + w).sum()
    Xt = torch.from_numpy(prep(X)).to(device)
    model = Encoder().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.05)
    print(f"train compounds with >=2 lines: {len(comps)} (signatures {len(X)})", flush=True)
    for step in range(steps):
        pick = rng.choice(len(comps), size=batch, replace=False, p=p)
        a = np.empty(batch, dtype=np.int64); b = np.empty(batch, dtype=np.int64)
        for j, c in enumerate(pick):
            cl = cells[c]; u, v = rng.choice(len(cl), 2, replace=False)
            a[j] = cl[u][rng.integers(len(cl[u]))]; b[j] = cl[v][rng.integers(len(cl[v]))]
        xa, xb = Xt[a], Xt[b]
        xa = xa * (torch.rand_like(xa) >= corrupt).float(); xb = xb * (torch.rand_like(xb) >= corrupt).float()
        model.train(); _, za = model(xa); _, zb = model(xb)
        za, zb = F.normalize(za, dim=1), F.normalize(zb, dim=1)
        logits = za @ zb.T / tau; t = torch.arange(batch, device=device)
        loss = 0.5 * (F.cross_entropy(logits, t) + F.cross_entropy(logits.T, t))
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        if step % 2000 == 0 or step == steps - 1:
            print(f"step {step} loss {loss.item():.3f} top1 {(logits.argmax(1) == t).float().mean().item():.3f}", flush=True)
    torch.save({"state": model.state_dict(), "seed": seed, "variant": "cross_line", "n_train_compounds": len(comps),
                "n_excluded": len(exclude)}, out)

if __name__ == "__main__":
    excl = set(open(sys.argv[2]).read().split()) if sys.argv[2] != "none" else set()
    train(sys.argv[1], excl, sys.argv[3], seed=int(sys.argv[4]) if len(sys.argv) > 4 else 0)
