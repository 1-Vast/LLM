"""Measured-state features for molecular queries: change from the stock baseline on quantified proteins, projected on training principal components.
A measured state of (background b, drug d, time t) exists only for experiments whose treated proteome is in the release; for a held-out background it
is available to a procedure ONLY through a paid molecular query (outcome gate enforced by ptv_data)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import ptv_data as D
from ptv_models import minmax  # noqa  (re-exported; torch is available in the interpreter used for this study)

N_PC = 8
MOL_TIME = 24


def delta(prep, cell, perts, t=MOL_TIME):
    raw = prep.R.treated(cell, perts, t)
    if raw is None:
        return None
    base = prep.baseline(cell)
    d = minmax(raw) - base
    d[raw <= 0] = 0.0
    return d


class MolSpace:
    """PCA of training deltas (mean of duplicates); fitted on training backgrounds only."""
    def __init__(self, prep, train_ex: pd.DataFrame, n_pc=N_PC):
        self.prep = prep
        V, keys = [], []
        for _, r in train_ex.iterrows():
            d = delta(prep, r.cell, r.perts)
            if d is not None:
                V.append(d); keys.append((r.cell, r.perts))
        V = np.stack(V)
        self.mean = V.mean(0)
        self.pca = PCA(n_pc, random_state=0).fit(V - self.mean)
        self.sd = np.sqrt(self.pca.explained_variance_)
        self.train_keys = keys
        self.train_z = dict(zip(keys, self.project(V)))

    def project(self, V):
        return self.pca.transform(V - self.mean) / self.sd

    def z(self, cell, perts):
        d = delta(self.prep, cell, perts)
        return None if d is None else self.project(d[None])[0]
