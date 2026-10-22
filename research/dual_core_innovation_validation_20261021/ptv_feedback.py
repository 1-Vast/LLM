"""Experiment Q: real-feedback updating.  Support experiments of a held-out background are revealed (labels = functional feedback, 24 h proteome = molecular
feedback), a declared update is applied, and the effect is evaluated on the UNCHANGED target pool (the other contested drugs of the same background).
Target outcomes are never used for updating.  Support rule is fixed: the S contested-pool drugs whose training label rate is closest to 0.5 (ties by id)."""
from __future__ import annotations
import copy, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch
import torch.nn.functional as F
import ptv_data as D, ptv_tasks as T, ptv_models as M

N_SUPPORT = 3
TRAJ_PARAMS = ("linear_input", "conv1", "conv1_norm", "conv2", "f1", "f2", "layer_final")
HEAD_PARAMS = ("head_x", "drugs_conv2", "fc1", "fc2")


def support_split(train_ex: pd.DataFrame, pool: list[str], s=N_SUPPORT):
    rate = train_ex.groupby("perts").y.mean()
    order = sorted(pool, key=lambda d: (abs(rate.get(d, 0.5) - 0.5), d))
    sup = order[:s]
    return sup, [d for d in pool if d not in sup]


def _params(model, prefixes):
    return [p for n, p in model.named_parameters() if n.split(".")[0] in prefixes]


def fine_tune(model, items, arm: str, steps: int, lr: float, lam=0.8, t_index=1):
    """items: support items with outcomes.  arm in {none, func, mol, both}.  Returns an updated copy (on the same device)."""
    if arm == "none":
        return model
    m = copy.deepcopy(model); dev = next(m.parameters()).device
    tens = {k: v.to(dev) for k, v in M.make_tensors(items).items()}
    pre = (HEAD_PARAMS if arm == "func" else TRAJ_PARAMS if arm == "mol" else HEAD_PARAMS + TRAJ_PARAMS)
    params = _params(m, pre)
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
    m.train()
    for _ in range(steps):
        y, p = m(tens["x"], tens["pert"], tens["fpA"], tens["fpB"])
        loss = 0.0
        if arm in ("mol", "both"):
            mk = tens["yobs"][:, t_index]
            loss = loss + (1 - lam) * (((y[:, t_index] - tens["y"][:, t_index]) ** 2) * mk).sum() / mk.sum().clamp(min=1)
        if arm in ("func", "both"):
            loss = loss + lam * F.binary_cross_entropy(p.clamp(1e-5, 1 - 1e-5), tens["lab"])
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step()
    m.eval()
    return m
