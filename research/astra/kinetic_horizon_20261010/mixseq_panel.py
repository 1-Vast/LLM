"""MIX-Seq panels on the STATE axis: observed responses, abundance and phase per (line, drug).

Observed response of line L to drug d (pool A, 24 h) = mean projected treated cells minus mean
projected control cells of L's own sub-pool control channel, on the 1,905 axis genes present in
MIX-Seq, in the same projection (calibration variant) as STATE's input.
Abundance A(L, d) = log2((n_treated + 0.5) / (n_control + 0.5)); selectivity removes the sub-pool
mean over the evaluated reference panel.
Phase counts use the full-gene fixed-reference phase call stored by ``mixseq_extract.py``.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mixseq_state as MS  # noqa: E402

DATA = MS.DATA
MIX_DRUGS = {"Trametinib": 0.05, "Afatinib": 0.5, "Everolimus": 5.0, "Gemcitabine": 0.05}  # STATE dose nearest MIX-Seq dose (log scale)
MIN_TREATED = 10


@dataclass
class MixPanel:
    lines: list
    drugs: list
    present: np.ndarray
    obs: np.ndarray        # lines x drugs x 1905 observed response (NaN if refused)
    n_treated: np.ndarray  # lines x drugs
    n_control: np.ndarray  # lines
    abundance: np.ndarray  # lines x drugs
    phase_t: np.ndarray    # lines x drugs x 3 counts
    phase_c: np.ndarray    # lines x 3 counts
    basal: np.ndarray      # lines x 2000 projected control mean
    subpool: np.ndarray    # lines
    halves: np.ndarray     # lines x drugs x 2 x 1905 split-half observed responses


def split() -> dict:
    return json.loads((HERE / "MIXSEQ_SPLIT.json").read_text(encoding="utf-8"))


def load_units(units: list) -> dict:
    zs = [np.load(DATA / "mixseq" / f"{u}.npz", allow_pickle=True) for u in units]
    return {k: np.concatenate([z[k] for z in zs]) for k in zs[0].files if k != "present"} | {"present": zs[0]["present"]}


def pool_a_panel(lines: list, treated_units: list, variant: str, drugs: list | None = None) -> MixPanel:
    sp = split()
    cal = MS.calibration(sp)
    c = load_units(["A_control"])
    t = load_units(treated_units)
    drugs = drugs or list(MIX_DRUGS)
    present = c["present"]
    P = len(lines), len(drugs)
    obs = np.full(P + (int(present.sum()),), np.nan, np.float32)
    halves = np.full(P + (2, int(present.sum())), np.nan, np.float32)
    n_t = np.zeros(P, int)
    ab = np.full(P, np.nan)
    ph_t = np.zeros(P + (3,), int)
    n_c = np.zeros(len(lines), int)
    ph_c = np.zeros((len(lines), 3), int)
    basal = np.zeros((len(lines), 2000), np.float32)
    sub = np.array([sp["lines"][d]["pool_A_subpool"] for d in lines])
    rng = np.random.default_rng(MS_SEED)
    for i, d in enumerate(lines):
        cm = c["depmap"] == d
        cx = MS.project(c["frac"][cm], cal, variant)
        basal[i] = cx.mean(0)
        n_c[i] = int(cm.sum())
        ph_c[i] = np.bincount(c["phase"][cm], minlength=3)
        for j, drug in enumerate(drugs):
            tm = (t["depmap"] == d) & (t["perturbation"] == drug)
            n_t[i, j] = int(tm.sum())
            ab[i, j] = np.log2((n_t[i, j] + 0.5) / (n_c[i] + 0.5))
            ph_t[i, j] = np.bincount(t["phase"][tm], minlength=3)
            if n_t[i, j] >= MIN_TREATED:
                tx = MS.project(t["frac"][tm], cal, variant)[:, present]
                obs[i, j] = tx.mean(0) - cx[:, present].mean(0)
                perm_t = rng.permutation(len(tx)); perm_c = rng.permutation(len(cx))
                for h in range(2):
                    halves[i, j, h] = tx[perm_t[h::2]].mean(0) - cx[perm_c[h::2]][:, present].mean(0)
    return MixPanel(lines, drugs, present, obs, n_t, n_c, ab, ph_t, ph_c, basal, sub, halves)


MS_SEED = 20261010


def state_forecast(pool: str, variant: str, lines: list, drugs: list | None = None) -> dict:
    z = np.load(DATA / "mixseq_state" / f"{pool}_{variant}.npz", allow_pickle=True)
    drugs = drugs or list(MIX_DRUGS)
    li = {d: i for i, d in enumerate(z["lines"])}
    labs = list(z["labels"])
    rows = np.array([li[d] for d in lines])
    cols = np.array([labs.index(MS.label(dr, MIX_DRUGS[dr])) for dr in drugs])
    paired = z["paired_delta"][rows][:, cols]
    phase = z["phase_prob"][rows][:, 1:][:, cols]
    phase_dmso = z["phase_prob"][rows][:, 0]
    return {"paired": paired, "phase": phase, "phase_dmso": phase_dmso, "basal": z["basal_mean"][rows]}
