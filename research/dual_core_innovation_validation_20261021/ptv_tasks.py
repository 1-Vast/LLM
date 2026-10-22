"""Item construction for model training/evaluation and the decision-task definitions."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import ptv_data as D
from ptv_models import minmax

K_NOM = 5                       # nomination size (frozen)
CONTEST_LO, CONTEST_HI = 0.2, 0.8   # contested pool: training-background label rate in [lo, hi]


class Prep:
    def __init__(self, release: D.Release | None = None):
        self.R = release or D.Release()
        fp = self.R.fingerprints()
        self.nan_fp_drugs = sorted(k for k, v in fp.items() if np.isnan(v).any())
        self.fp = {k: minmax(np.nan_to_num(v, nan=0.0)) for k, v in fp.items()}
        self.tv = {k: self.R.target_vector(k) for k in fp}
        self._base = {}; self._ctl = {}

    def baseline(self, cell):
        if cell not in self._base:
            self._base[cell] = minmax(self.R.baseline(cell))
        return self._base[cell]

    def control(self, cell, t):
        key = (cell, t)
        if key not in self._ctl:
            c = self.R.control(cell, t)
            self._ctl[key] = None if c is None else minmax(c)
        return self._ctl[key]

    def pert(self, perts: str) -> np.ndarray:
        v = np.zeros(len(self.R.nodes))
        for d in perts.split():
            v = np.maximum(v, self.tv[d])
        return 0.5 * v

    def item(self, cell, perts, lab, with_outcome=True):
        ids = perts.split()
        fa = self.fp[ids[0]]; fb = self.fp[ids[1]] if len(ids) == 2 else fa
        it = {"cell": cell, "perts": perts, "x": self.baseline(cell), "pert": self.pert(perts), "fpA": fa, "fpB": fb,
              "lab": float(lab) if lab == lab else float("nan"), "is_single": len(ids) == 1, "y": None, "yobs": None}
        if with_outcome:
            ys, ms = [], []
            for t in D.TIMES:
                raw = self.R.treated(cell, perts, t)
                if raw is None:
                    return None
                obs = (raw > 0).astype(float)
                ys.append(minmax(raw)); ms.append(obs)
            it["y"] = np.stack(ys); it["yobs"] = np.stack(ms)
        return it

    def items(self, ex: pd.DataFrame, with_outcome=True):
        out, keep = [], []
        for i, r in ex.iterrows():
            it = self.item(r.cell, r.perts, r.y, with_outcome)
            if it is not None:
                out.append(it); keep.append(i)
        return out, ex.loc[keep].reset_index(drop=True)


def contested_pool(train_ex: pd.DataFrame, avail: list[str]) -> list[str]:
    """Drugs available in the held-out background whose label rate over the TRAINING backgrounds lies in [lo, hi]."""
    rate = train_ex.groupby("perts").y.mean()
    return [d for d in avail if d in rate.index and CONTEST_LO <= rate[d] <= CONTEST_HI]


def precision_at_k(scores: pd.Series, labels: pd.Series, k: int = K_NOM) -> float:
    top = scores.sort_values(ascending=False, kind="stable").index[:k]
    return float(labels[top].mean())
