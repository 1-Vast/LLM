"""Stream-level paired statistics. The unit of replication is the independent stream (world); tasks inside a stream are averaged first.
Decision rule against a prespecified engineering margin DELTA (absolute shortlist utility):
  SUPPORT       lower confidence bound of the paired gain >= DELTA
  NO_SUPPORT    upper confidence bound < DELTA
  INCONCLUSIVE  otherwise
No confidence interval is formed from unique() values; bootstrap resamples whole streams.
"""
from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

DELTA = 0.01
LEVEL_PRIMARY = 1 - 0.05 / 3          # three primary hypotheses H1, H2, H3: Bonferroni
LEVEL_SECONDARY = 0.95
BOOT = 20000


def load_streams(run_dir: Path, pattern="*.json.gz"):
    out = {}
    for p in sorted((Path(run_dir) / "streams").glob(pattern)):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            d = json.load(f)
        out[d["sid"]] = d
    return out


def task_table(streams: dict, contract: str, gen_min: int = 2, role: str = "task"):
    """sid -> arm -> mean utility over the tasks of batches gen_min..4 (one number per stream and arm)."""
    tab = {}
    for sid, d in streams.items():
        acc = defaultdict(list)
        for r in d["rows"]:
            if r["contract"] == contract and r["role"] == role and r["gen"] >= gen_min:
                acc[r["arm"]].append(r["utility"])
        tab[sid] = {a: float(np.mean(v)) for a, v in acc.items()}
    return tab


def oracle_table(streams: dict, contract: str, gen_min: int = 2):
    tab = {}
    for sid, d in streams.items():
        acc = defaultdict(list)
        for r in d["rows"]:
            if r["contract"] == contract and r["role"] == "task" and r["gen"] >= gen_min and r["arm"] == "prior":
                acc["oracle"].append(r["oracle"])
        tab[sid] = float(np.mean(acc["oracle"])) if acc["oracle"] else np.nan
    return tab


def anchor_table(streams: dict):
    """sid -> (role, arm, gen) -> mean utility over that anchor set at that checkpoint."""
    tab = {}
    for sid, d in streams.items():
        acc = defaultdict(list)
        for r in d["rows"]:
            if r["role"] in ("A_old", "A_new"):
                acc[(r["role"], r["arm"], r["gen"])].append(r["utility"])
        tab[sid] = {k: float(np.mean(v)) for k, v in acc.items()}
    return tab


def boot_ci(x: np.ndarray, level: float, seed: int = 0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(BOOT, len(x)))
    m = x[idx].mean(1)
    a = (1 - level) / 2
    return float(np.quantile(m, a)), float(np.quantile(m, 1 - a))


def decide(lo: float, hi: float, delta: float = DELTA) -> str:
    if lo >= delta:
        return "SUPPORT"
    if hi < delta:
        return "NO_SUPPORT"
    return "INCONCLUSIVE"


def paired(tab: dict, sids: list, a, b):
    """Per-stream difference a - b. a, b: arm name, or a list of arm names meaning the per-stream maximum (post hoc 'best of')."""
    def val(row, arm):
        if isinstance(arm, (list, tuple)):
            return max(row[x] for x in arm)
        return row[arm]
    d = []
    for s in sids:
        row = tab[s]
        try:
            d.append(val(row, a) - val(row, b))
        except KeyError:
            continue
    return np.array(d)


def contrast_row(name, d: np.ndarray, level: float, delta: float = DELTA, seed: int = 0, primary: bool = False):
    if len(d) < 3:
        return {"contrast": name, "n_streams": int(len(d)), "verdict": "NOT_TESTED"}
    lo, hi = boot_ci(d, level, seed)
    lo95, hi95 = boot_ci(d, 0.95, seed + 1)
    out = {"contrast": name, "n_streams": int(len(d)), "mean_gain": float(d.mean()), "ci_level": level, "ci": [lo, hi], "ci95": [lo95, hi95],
           "share_streams_positive": float((d > 0).mean()), "margin": delta, "verdict_vs_margin": decide(lo, hi, delta), "verdict": decide(lo, hi, delta) if primary else None}
    return out


def kind_of(sid: str) -> str:
    return sid.split("_")[0]


def is_dec(sid: str) -> bool:
    return sid.endswith("_dec")


def sids_of(tab: dict, kinds, dec=False):
    return [s for s in tab if kind_of(s) in kinds and is_dec(s) == dec]


def arm_means(tab: dict, sids: list, seed: int = 0):
    arms = sorted({a for s in sids for a in tab[s]})
    out = {}
    for a in arms:
        v = np.array([tab[s][a] for s in sids if a in tab[s]])
        if len(v) >= 3:
            lo, hi = boot_ci(v, 0.95, seed)
            out[a] = {"mean": float(v.mean()), "ci95": [lo, hi], "n": int(len(v))}
    return out
