"""Compound-identity contrastive encoder for L1000 landmark signatures (no viability labels).

Views of a compound are two of its signatures (different line/time/dose/batch) plus SCARF-style
feature corruption. Loss: symmetric InfoNCE over compounds in the batch. Compounds whose keys are
listed in the exclusion file never enter training (inductive with respect to evaluation compounds).

Usage: contrastive.py corpus.npz exclude_ik14.txt out_model.pt [seed]
"""
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class Encoder(nn.Module):
    def __init__(self, d_in=978, width=1024, d_rep=256, d_proj=128, p_drop=0.1):
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(d_in, width), nn.LayerNorm(width), nn.GELU(), nn.Dropout(p_drop),
            nn.Linear(width, width // 2), nn.LayerNorm(width // 2), nn.GELU(), nn.Dropout(p_drop),
            nn.Linear(width // 2, d_rep))
        self.head = nn.Sequential(nn.GELU(), nn.Linear(d_rep, d_proj))

    def forward(self, x):
        h = self.body(x)
        return h, self.head(h)


def prep(x):
    """Signature z-scores -> bounded network input."""
    return np.clip(np.nan_to_num(x.astype(np.float32)), -10, 10) / 4.0


def embed(model, X, device="cuda", batch=4096):
    model.eval()
    out = []
    with torch.no_grad():
        for a in range(0, len(X), batch):
            h, _ = model(torch.from_numpy(prep(X[a:a + batch])).to(device))
            out.append(h.float().cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 256), dtype=np.float32)


def train(corpus, exclude, out, seed=0, steps=12000, batch=512, tau=0.1, corrupt=0.2, lr=1e-3, device="cuda"):
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    d = np.load(corpus, allow_pickle=True)
    key = np.where(d["ik14"] != "", d["ik14"], d["pert_id"])
    keep = ~np.isin(key, list(exclude))
    X = d["x"][keep]
    key = key[keep]
    tas = np.nan_to_num(d["tas"][keep])
    uk, inv = np.unique(key, return_inverse=True)
    members = [[] for _ in uk]
    for i, k in enumerate(inv):
        members[k].append(i)
    members = [np.array(m) for m in members]
    multi = np.array([len(m) >= 2 for m in members])
    # sample compounds with probability increasing in their strongest signature's activity
    wmax = np.array([tas[m].max() for m in members])
    p = np.where(multi, 0.05 + wmax, 0.0)
    p = p / p.sum()
    Xt = torch.from_numpy(prep(X)).to(device)
    model = Encoder().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.05)
    print(f"train compounds {multi.sum()} (signatures {len(X)}), excluded keys {len(exclude)}", flush=True)
    for step in range(steps):
        comp = rng.choice(len(members), size=batch, replace=False, p=p)
        a = np.empty(batch, dtype=np.int64)
        b = np.empty(batch, dtype=np.int64)
        for j, c in enumerate(comp):
            a[j], b[j] = rng.choice(members[c], 2, replace=False)
        xa, xb = Xt[a], Xt[b]
        ma = (torch.rand_like(xa) < corrupt).float()
        mb = (torch.rand_like(xb) < corrupt).float()
        xa = xa * (1 - ma)
        xb = xb * (1 - mb)
        model.train()
        _, za = model(xa)
        _, zb = model(xb)
        za, zb = F.normalize(za, dim=1), F.normalize(zb, dim=1)
        logits = za @ zb.T / tau
        target = torch.arange(batch, device=device)
        loss = 0.5 * (F.cross_entropy(logits, target) + F.cross_entropy(logits.T, target))
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        if step % 1000 == 0 or step == steps - 1:
            acc = (logits.argmax(1) == target).float().mean().item()
            print(f"step {step} loss {loss.item():.3f} top1 {acc:.3f}", flush=True)
    torch.save({"state": model.state_dict(), "seed": seed, "steps": steps, "tau": tau, "corrupt": corrupt,
                "n_train_compounds": int(multi.sum()), "n_excluded": len(exclude)}, out)


if __name__ == "__main__":
    excl = set(open(sys.argv[2]).read().split())
    train(sys.argv[1], excl, sys.argv[3], seed=int(sys.argv[4]) if len(sys.argv) > 4 else 0)
