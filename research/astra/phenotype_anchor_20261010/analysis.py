"""Arms, bridge and leave-one-reference-line-out harness for the phenotype-anchor study.

Everything here is fitted on reference lines only. A held-out line enters through
``predict_heldout`` with already-chosen hyperparameters; its outcomes are never an input.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

import phenotypes as P

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "data/external/tahoe_phenotype_20261010"
DOSE_RE = re.compile(r", ([0-9.]+), 'uM'\)\]$")
QUALIFIED_MIN_MEDIAN = 200
TOP_K = 10
BRIDGE_GRID = {"n_pc": (20, 50, 100), "alpha": (1.0, 10.0, 100.0, 1e3, 1e4), "doses": ("5uM", "all")}
KERNEL_GRID = {"tau": (0.02, 0.05, 0.1), "top_m": (3, 5, 10, 40)}


def dose_of(label: str) -> float | None:
    m = DOSE_RE.search(label)
    return float(m.group(1)) if m else None


def drug_of(label: str) -> str:
    return re.sub(r"^\[\('", "", DOSE_RE.sub("", label)).rstrip("'")


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


@dataclass
class Panel:
    """Per-line arrays aligned on a common label list (all doses)."""
    files: list
    names: dict
    labels: list
    survival: np.ndarray            # lines x labels (plate-mean relative survival), NaN if unmeasured
    g1: np.ndarray                  # lines x labels (plate-mean G1 log-odds shift)
    delta: np.ndarray | None = None  # lines x labels x 2000 observed deviation (treated - same-plate DMSO)
    basal: np.ndarray | None = None  # lines x 2000 mean DMSO profile
    meta: dict = field(default_factory=dict)


def qualified_reference() -> tuple[list, dict]:
    files = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in P.HELDOUT]
    table, names = P.load_counts(files)
    med = {f: float(np.median([v["n"] for (ff, lab, _), v in table.items() if ff == f and lab != P.DMSO])) for f in files}
    keep = [f for f in files if med[f] >= QUALIFIED_MIN_MEDIAN]
    refused = {f: {"name": names[f], "median_treated_count": med[f], "reason": "CONTEXT_UNDERCOUNTED"} for f in files if f not in keep}
    return keep, {"medians": med, "refused": refused, "table": table, "names": names}


def phenotype_panel(files: list, denominator_files: list, table: dict, names: dict) -> Panel:
    frame = P.phenotype_frame(table, files, denominator_files)
    labels = sorted({k[1] for k in frame if dose_of(k[1]) is not None})
    li = {l: i for i, l in enumerate(labels)}
    surv = np.full((len(files), len(labels)), np.nan)
    g1 = np.full_like(surv, np.nan)
    acc = {}
    for (f, lab, pl), rec in frame.items():
        if lab not in li or f not in files:
            continue
        acc.setdefault((f, lab), []).append(rec)
    fi = {f: i for i, f in enumerate(files)}
    for (f, lab), recs in acc.items():
        surv[fi[f], li[lab]] = np.mean([r["survival"] for r in recs])
        g1[fi[f], li[lab]] = np.mean([r["G1"] for r in recs])
    return Panel(files=files, names={f: names[f] for f in files}, labels=labels, survival=surv, g1=g1)


def attach_expression(panel: Panel) -> Panel:
    """Observed deviation per (line, label): plate-mean of treated mean minus same-plate DMSO mean."""
    li = {l: i for i, l in enumerate(panel.labels)}
    delta = np.full((len(panel.files), len(panel.labels), 2000), np.nan, dtype=np.float32)
    basal = np.zeros((len(panel.files), 2000), dtype=np.float32)
    for i, f in enumerate(panel.files):
        t = np.load(CACHE / "expression" / f / "treated.npz")
        b = np.load(CACHE / "expression" / f / "basal.npz")
        plate_mean = {p: b["x"][b["plate"] == p].mean(0) for p in np.unique(b["plate"])}
        basal[i] = b["x"].mean(0)
        sums, counts = {}, {}
        for lab, pl, mean in zip(t["label"], t["plate"], t["mean"]):
            if lab not in li or pl not in plate_mean:
                continue
            sums[lab] = sums.get(lab, 0) + (mean - plate_mean[pl])
            counts[lab] = counts.get(lab, 0) + 1
        for lab, s in sums.items():
            delta[i, li[lab]] = s / counts[lab]
    panel.delta, panel.basal = delta, basal
    return panel


# ----------------------------------------------------------------------------- arms

def selectivity(values: np.ndarray, train_rows: np.ndarray) -> np.ndarray:
    """T = value minus the reference-panel mean over ``train_rows`` (NaN-aware)."""
    return values - np.nanmean(values[train_rows], axis=0, keepdims=True)


def organ_prior(target_organ: str | None, train_organs: list, T_train: np.ndarray) -> tuple[np.ndarray, str | None]:
    same = [i for i, o in enumerate(train_organs) if target_organ is not None and o == target_organ]
    if not same:
        return np.zeros(T_train.shape[1]), "NO_SAME_ORGAN_REFERENCE"
    return np.nan_to_num(np.nanmean(T_train[same], axis=0)), None


def kernel_prior(basal_target: np.ndarray, basal_train: np.ndarray, T_train: np.ndarray, tau: float, top_m: int) -> np.ndarray:
    center = basal_train.mean(0)
    a = basal_target - center
    B = basal_train - center
    sim = (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a) + 1e-12)
    order = np.argsort(-sim)[:top_m]
    w = np.exp((sim[order] - sim[order].max()) / tau)
    Tm = T_train[order]
    mask = ~np.isnan(Tm)
    num = np.nansum(w[:, None] * np.nan_to_num(Tm), axis=0)
    den = (w[:, None] * mask).sum(0)
    return np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)


def response_profile(delta_rows: np.ndarray, panel_delta: np.ndarray) -> np.ndarray:
    """Flattened context-specific deviation over a label set (missing labels contribute 0)."""
    return np.nan_to_num(delta_rows - panel_delta).ravel()


def knowledge_prior(drivers: set, labels: list, targets: dict) -> np.ndarray:
    """-1 where a drug target equals a driver gene of the line (predicts selective loss), else 0."""
    return -np.array([float(bool(targets.get(norm(drug_of(l)), set()) & drivers)) for l in labels])


class Bridge:
    """PCA + ridge from context-specific RNA deviation to a phenotype selectivity target."""

    def __init__(self, n_pc: int, alpha: float):
        self.n_pc, self.alpha = n_pc, alpha

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Bridge":
        self.mu = X.mean(0)
        Xc = X - self.mu
        _, _, vt = np.linalg.svd(Xc[np.random.RandomState(0).permutation(len(Xc))[:20000]], full_matrices=False)
        self.components = vt[: self.n_pc]
        Z = Xc @ self.components.T
        self.ymu = y.mean()
        self.w = np.linalg.solve(Z.T @ Z + self.alpha * np.eye(self.n_pc), Z.T @ (y - self.ymu))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return ((X - self.mu) @ self.components.T) @ self.w + self.ymu


def bridge_rows(delta: np.ndarray, T: np.ndarray, rows: np.ndarray, cols: np.ndarray, panel_delta: np.ndarray):
    X, y = [], []
    for i in rows:
        ok = cols[~np.isnan(T[i, cols]) & ~np.isnan(delta[i, cols, 0])]
        X.append(delta[i, ok] - panel_delta[ok])
        y.append(T[i, ok])
    return np.concatenate(X), np.concatenate(y)


# ----------------------------------------------------------------------------- metrics

def within_r(pred: np.ndarray, obs: np.ndarray) -> float:
    ok = ~np.isnan(obs) & ~np.isnan(pred)
    if ok.sum() < 3 or np.std(pred[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(pred[ok], obs[ok])[0, 1])


def topk_utility(pred: np.ndarray, obs: np.ndarray, generic: np.ndarray, k: int = TOP_K) -> float:
    """-mean observed selectivity of the k most negative predictions (ties broken by generic panel survival)."""
    ok = np.flatnonzero(~np.isnan(obs))
    order = ok[np.lexsort((generic[ok], pred[ok]))][:k]
    return float(-np.mean(obs[order]))
