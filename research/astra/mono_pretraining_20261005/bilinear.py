"""Low-capacity drug x context head shared by the mono-pretrained and scratch arms.

File summary
- Path: research/astra/mono_pretraining_20261005/bilinear.py
- Purpose: one architecture, one optimiser, one regulariser for every learned arm. A standardised
  cell-context vector z (14 PROGENy scores) goes through W (14 x k) to r = zW; r meets a drug embedding
  e_a (k):
    mono  : y(c, a) = beta_a + r_c . e_a
    combo : with u_a = r_c . e_a (line-specific shift of drug a; invariant to any rotation of the rank basis)
            g(c; anchor a, library b) = t1 (u_a + u_b) + t2 u_a u_b + t3 (u_a - u_b)          ["invariant"]
            "h6" adds headroom terms of the predicted potency m_a = beta_a + u_a (rho = sigmoid(m/2), i.e. how far
            drug a is from killing at its top dose): + t4 (rho_a + rho_b) + t5 rho_a rho_b + t6 (rho_a - rho_b)
            "p3" uses only the headroom terms with u = 0 (drug-level potency, no cell context)
            or the coordinate-wise protocol-literal form
            t1 . r(e_a + e_b) + t2 . r(e_a e_b) + t3 . r(e_a - e_b)                            ["elementwise"]
            whose coordinates are identified only up to rotation by mono pretraining.
  Mono pretraining fits (W, E, beta) on single-drug labels of cells that never enter a combination
  evaluation. Combination fine-tuning fits (theta, W, E) on residual combination labels, with an L2 pull
  of W and E towards their initial values (pretrained values, or random scratch values).
- Core points: identical code path, steps, learning rate and penalties for pretrained / scratch /
  permuted-mono arms; the only difference is the initial (W, E). Deterministic CPU float64.
- Interfaces: `MonoConfig`, `ComboConfig`, `init_params`, `pretrain_mono`, `finetune_combo`,
  `predict_combo`, `predict_mono`, `n_theta`.
- Depends on: numpy, torch (CPU).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

torch.set_num_threads(1)


@dataclass(frozen=True)
class MonoConfig:
    rank: int = 4
    steps: int = 600
    lr: float = 0.02
    l2_w: float = 1e-3          # mean-squared parameter penalty
    l2_e: float = 1e-3
    init_scale: float = 0.3


@dataclass(frozen=True)
class ComboConfig:
    features: str = "h6"  # "invariant"/"h3" (3) | "h6" (6) | "p3" (3, potency only) | "elementwise" (3 x rank)
    steps: int = 200
    lr: float = 0.02
    l2_theta: float = 1.0
    l2_init: float = 10.0       # pull of W, E towards their initial values (L2-SP)


def n_theta(features: str, rank: int) -> int:
    return {"invariant": 3, "h3": 3, "h6": 6, "p3": 3, "elementwise": 3 * rank}[features]


def init_params(n_features: int, n_drugs: int, rank: int, seed: int, scale: float = 0.3) -> dict:
    g = np.random.default_rng([seed, n_features, n_drugs, rank])
    return {"W": g.normal(0, scale / np.sqrt(n_features) * np.sqrt(rank), (n_features, rank)),
            "E": g.normal(0, scale, (n_drugs, rank)),
            "beta": np.zeros(n_drugs)}


def _t(a) -> torch.Tensor:
    return torch.as_tensor(np.asarray(a, dtype=np.float64))


def pretrain_mono(z: np.ndarray, cell: np.ndarray, drug: np.ndarray, y: np.ndarray, n_drugs: int,
                  cfg: MonoConfig, seed: int, drug_weight: np.ndarray | None = None) -> dict:
    """Fit beta_a + (zW).e_a on (cell, drug, y) records. `z` is cells x features, rows indexed by `cell`."""
    if not np.all(np.isfinite(y)):
        raise ValueError("non-finite mono target")
    p = init_params(z.shape[1], n_drugs, cfg.rank, seed, cfg.init_scale)
    W, E, beta = (torch.nn.Parameter(_t(p[k])) for k in ("W", "E", "beta"))
    zt, ct, dt, yt = _t(z), torch.as_tensor(cell), torch.as_tensor(drug), _t(y)
    wt = None if drug_weight is None else _t(drug_weight)[dt]
    opt = torch.optim.Adam([W, E, beta], lr=cfg.lr)
    for _ in range(cfg.steps):
        opt.zero_grad()
        r = zt @ W
        pred = beta[dt] + (r[ct] * E[dt]).sum(1)
        res = (pred - yt) ** 2
        loss = (res if wt is None else res * wt).mean() + cfg.l2_w * (W ** 2).mean() + cfg.l2_e * (E ** 2).mean()
        loss.backward()
        opt.step()
    return {"W": W.detach().numpy().copy(), "E": E.detach().numpy().copy(), "beta": beta.detach().numpy().copy()}


def predict_mono(params: dict, z: np.ndarray, cell: np.ndarray, drug: np.ndarray) -> np.ndarray:
    r = np.asarray(z) @ params["W"]
    return params["beta"][drug] + (r[cell] * params["E"][drug]).sum(1)


def _sig(x, lib):
    return torch.sigmoid(x / 2.0) if lib is torch else 1.0 / (1.0 + np.exp(-x / 2.0))


def _feats(r, ea, eb, features: str, ba, bb, lib=np, uo=None):
    stack = (lambda xs: torch.stack(xs, 1)) if lib is torch else (lambda xs: np.stack(xs, axis=1))
    if features == "elementwise":
        parts = [r * (ea + eb), r * (ea * eb), r * (ea - eb)]
        return torch.cat(parts, 1) if lib is torch else np.concatenate(parts, axis=1)
    ua, ub = (r * ea).sum(1), (r * eb).sum(1)
    if uo is not None:                                  # observed own-mono shifts replace the predicted ones where known
        oa, ob = uo
        if lib is torch:
            ua, ub = torch.where(torch.isnan(oa), ua, oa), torch.where(torch.isnan(ob), ub, ob)
        else:
            ua, ub = np.where(np.isnan(oa), ua, oa), np.where(np.isnan(ob), ub, ob)
    cols = []
    if features in ("invariant", "h3", "h6"):
        cols += [ua + ub, ua * ub, ua - ub]
    if features in ("h6", "p3"):
        pa, pb = _sig(ba + (ua if features == "h6" else 0 * ua), lib), _sig(bb + (ub if features == "h6" else 0 * ub), lib)
        cols += [pa + pb, pa * pb, pa - pb]
    return stack(cols)


def finetune_combo(params: dict, z: np.ndarray, cell: np.ndarray, anchor: np.ndarray, library: np.ndarray,
                   y: np.ndarray, cfg: ComboConfig, sample_weight: np.ndarray | None = None, uo=None) -> dict:
    """Fit residual combination labels. `y` rows are ordered (anchor, library) experiments, already centred."""
    if not np.all(np.isfinite(y)):
        raise ValueError("non-finite combo target")
    k = params["W"].shape[1]
    beta = _t(params["beta"])                      # fixed during fine-tuning (drug-level potency from mono)
    W0, E0 = _t(params["W"]), _t(params["E"])
    W, E = torch.nn.Parameter(W0.clone()), torch.nn.Parameter(E0.clone())
    th = torch.nn.Parameter(_t(np.zeros(n_theta(cfg.features, k))))
    zt, ct, at, bt, yt = _t(z), torch.as_tensor(cell), torch.as_tensor(anchor), torch.as_tensor(library), _t(y)
    wt = _t(np.ones(len(y)) if sample_weight is None else sample_weight)
    uot = None if uo is None else (_t(uo[0]), _t(uo[1]))
    opt = torch.optim.Adam([W, E, th], lr=cfg.lr)
    n = float(len(y))
    for _ in range(cfg.steps):
        opt.zero_grad()
        r = (zt @ W)[ct]
        g = _feats(r, E[at], E[bt], cfg.features, beta[at], beta[bt], torch, uot) @ th
        loss = ((g - yt) ** 2 * wt).sum() / n + cfg.l2_theta * (th ** 2).sum() / n \
            + cfg.l2_init * (((W - W0) ** 2).sum() + ((E - E0) ** 2).sum()) / n
        loss.backward()
        opt.step()
    out = dict(params)
    out.update({"W": W.detach().numpy().copy(), "E": E.detach().numpy().copy(),
                "theta": th.detach().numpy().copy(), "features": cfg.features})
    return out


def predict_combo(params: dict, z: np.ndarray, cell: np.ndarray, anchor: np.ndarray, library: np.ndarray,
                  uo=None) -> np.ndarray:
    r = (np.asarray(z) @ params["W"])[cell]
    b = params["beta"]
    return _feats(r, params["E"][anchor], params["E"][library], params["features"],
                  b[anchor], b[library], np, uo) @ params["theta"]
