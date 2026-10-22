"""ProteinTalks-style world model (reimplemented from the released model.py; torchdyn replaced by fixed-step RK4) and variants.

Faithfulness notes (recorded in PROTOCOL.md): hidden width is a parameter (released 64, this study 16 for CPU budget); the intervention pathway is a
per-protein pointwise neural ODE on (baseline abundance, target flag) - it has no cross-protein interaction, those only occur in the phenotype head; the
fingerprint enters only the phenotype head; the MSE term is masked to quantified proteins (the release trains on zero-imputed values).
Variants: full (M1), no_traj (M2: the phenotype head sees the baseline only, no ODE), no_fp (M3: no fingerprint branch into the head).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import torch
import torch.nn as nn
import torch.nn.functional as F


def minmax(v: np.ndarray) -> np.ndarray:
    lo, hi = float(v.min()), float(v.max())
    return (v - lo) / (hi - lo) if hi > lo else np.zeros_like(v)


class FC(nn.Module):
    def __init__(self, i, o, act, p):
        super().__init__()
        self.fc = nn.Linear(i, o); self.norm = nn.LayerNorm(o); self.act = act; self.drop = nn.Dropout(p) if p else None
        s = 1.0 / math.sqrt(i); self.fc.weight.data.uniform_(-s, s); self.fc.bias.data.uniform_(-s, s)

    def forward(self, h):
        if self.drop: h = self.drop(h)
        h = self.norm(self.fc(h))
        return self.act(h) if self.act else h


class PPODE(nn.Module):
    def __init__(self, n_prot, n_fp, hidden=16, variant="full", dropout=0.0):
        super().__init__()
        self.variant = variant; self.n_prot = n_prot; self.hidden = hidden
        mid = 32
        if variant != "no_traj":
            self.linear_input = FC(2, mid, nn.Softplus(), dropout)
            self.conv1 = nn.Conv1d(mid, hidden, 1); self.conv1_norm = nn.GroupNorm(1, hidden); self.conv2 = nn.Conv1d(hidden, mid, 1)
            self.f1 = FC(hidden, hidden, nn.Softplus(), dropout); self.f2 = FC(hidden, hidden, None, dropout)
            self.layer_final = nn.Linear(mid, 1)
            self.head_x = nn.Conv1d(n_prot, 32, kernel_size=4)          # channels: proteins; length: [baseline, 6h, 24h, 48h]
        else:
            self.head_x = nn.Linear(n_prot, 32)
        if variant != "no_fp":
            self.drugs_conv2 = nn.Conv1d(n_fp, 32, kernel_size=2)
            self.fc1 = nn.Linear(64, 32)
        else:
            self.fc1 = nn.Linear(32, 32)
        self.fc2 = nn.Linear(32, 1)

    def vf(self, h):
        return self.f2(self.f1(h))

    def ode(self, h0):
        outs = []; h = h0
        for _ in range(3):                                           # dt = 1 between ticks, classic RK4
            k1 = self.vf(h); k2 = self.vf(h + 0.5 * k1); k3 = self.vf(h + 0.5 * k2); k4 = self.vf(h + k3)
            h = h + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
            outs.append(h)
        return torch.stack(outs, 1)                                  # [B, 3, N, hidden]

    def forward(self, x, pert, fpA, fpB):
        """x, pert: [B, N, 1]; fpA, fpB: [B, F, 1].  Returns (y [B,3,N], p [B])."""
        y = None
        if self.variant != "no_traj":
            e = self.linear_input(torch.cat([x, pert], -1)).transpose(1, 2)           # [B, mid, N]
            e = F.relu(self.conv1_norm(self.conv1(e))).transpose(1, 2)                # [B, N, hidden]
            tr = self.ode(e)                                                          # [B, 3, N, hidden]
            B, T, N, H = tr.shape
            z = self.conv2(tr.reshape(B * T, N, H).transpose(1, 2)).transpose(1, 2)   # [B*T, N, mid]
            y = self.layer_final(z).view(B, T, N)
            seq = torch.cat([x.transpose(1, 2), y], 1)                               # [B, 4, N]
            h = F.relu(self.head_x(seq.transpose(1, 2))).squeeze(-1)                  # [B, 32]
        else:
            h = F.relu(self.head_x(x.squeeze(-1)))
        if self.variant != "no_fp":
            d = F.relu(self.drugs_conv2(torch.cat([fpA, fpB], -1))).squeeze(-1)
            h = torch.cat([h, d], 1)
        p = torch.sigmoid(self.fc2(F.relu(self.fc1(h)))).squeeze(-1)
        return y, p


def make_tensors(items):
    """items: list of dict(x[N], pert[N], fpA[F], fpB[F], y[3,N] or None, yobs[3,N] or None, lab or nan, is_single)."""
    t = lambda k: torch.tensor(np.stack([i[k] for i in items]), dtype=torch.float32)
    out = {"x": t("x").unsqueeze(-1), "pert": t("pert").unsqueeze(-1), "fpA": t("fpA").unsqueeze(-1), "fpB": t("fpB").unsqueeze(-1),
           "lab": torch.tensor([i["lab"] for i in items], dtype=torch.float32),
           "single": torch.tensor([bool(i["is_single"]) for i in items])}
    if items[0].get("y") is not None:
        out["y"] = t("y"); out["yobs"] = t("yobs")
    return out


def train(model, tens, epochs=60, lr=5e-4, bs=32, lam=0.8, seed=0, wd=1e-4, log=None, w_pheno=True):
    g = torch.Generator().manual_seed(seed); torch.manual_seed(seed)
    dev = next(model.parameters()).device
    tens = {k: v.to(dev) for k, v in tens.items()}
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    n = tens["x"].shape[0]
    for ep in range(epochs):
        model.train(); perm = torch.randperm(n, generator=g).to(dev); tot = 0.0
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            y, p = model(tens["x"][idx], tens["pert"][idx], tens["fpA"][idx], tens["fpB"][idx])
            loss = 0.0
            if y is not None:
                m = tens["yobs"][idx]
                mse = ((y - tens["y"][idx]) ** 2 * m).sum() / m.sum().clamp(min=1)
                loss = loss + (1 - lam) * mse
            lab = tens["lab"][idx]; ok = tens["single"][idx] & ~torch.isnan(lab)
            if ok.any() and w_pheno:
                loss = loss + lam * F.binary_cross_entropy(p[ok].clamp(1e-5, 1 - 1e-5), lab[ok])
            if torch.is_tensor(loss):
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); tot += float(loss.detach())
        if log: log(ep, tot)
    return model


@torch.no_grad()
def predict(model, tens, bs=64):
    model.eval(); ys = []; ps = []
    dev = next(model.parameters()).device
    for i in range(0, tens["x"].shape[0], bs):
        y, p = model(*[tens[k][i:i + bs].to(dev) for k in ("x", "pert", "fpA", "fpB")])
        ps.append(p.cpu().numpy()); ys.append(None if y is None else y.cpu().numpy())
    return (None if ys[0] is None else np.concatenate(ys)), np.concatenate(ps)
