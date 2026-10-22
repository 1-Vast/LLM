"""M0: strong direct functional predictors on the same available information (drug fingerprint/targets, baseline proteome, training labels), plus
the deterministic comparators B0 (drug prior) and B1 (baseline-similarity-weighted prior)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def logit(p, eps=0.02):
    p = np.clip(p, eps, 1 - eps); return np.log(p / (1 - p))


class Direct:
    def __init__(self, prep, n_fp=8, n_bg=3, tau=0.15):
        self.P = prep; self.tau = tau
        drugs = sorted(prep.fp); F = np.stack([prep.fp[d] for d in drugs])
        self.fp_pc = dict(zip(drugs, PCA(n_fp, random_state=0).fit_transform(F - F.mean(0))))
        self.ntarg = {d: float(prep.tv[d].sum()) for d in drugs}
        cells = sorted({c for c in prep.R.rows.cell.unique()})
        B = np.stack([prep.baseline(c) for c in cells])
        self.bg_pc = dict(zip(cells, PCA(n_bg, random_state=0).fit_transform(B - B.mean(0))))
        self.base = {c: prep.baseline(c) for c in cells}

    def sim(self, a, b):
        return float(np.corrcoef(self.base[a], self.base[b])[0, 1])

    def priors(self, train: pd.DataFrame, cell: str, drug: str, exclude_self=True):
        """(drug prior, neighbour prior) for (cell, drug) from training rows of OTHER backgrounds."""
        sub = train[(train.perts == drug) & (train.lineage != cell.replace("(ATCC)", "").strip()) & train.y.notna()]
        if sub.empty:
            return np.nan, np.nan
        w = np.exp(np.array([self.sim(cell, c) for c in sub.cell]) / self.tau)
        return float(sub.y.mean()), float((w * sub.y.values).sum() / w.sum())

    def features(self, train, rows: pd.DataFrame, prior_scope: pd.DataFrame):
        out = []
        gm = float(train.y.mean())
        for _, r in rows.iterrows():
            dp, nb = self.priors(prior_scope, r.cell, r.perts)
            dp = gm if dp != dp else dp; nb = dp if nb != nb else nb
            out.append(np.concatenate([[logit(dp), logit(nb), self.ntarg[r.perts]], self.fp_pc[r.perts], self.bg_pc[r.cell]]))
        return np.array(out)

    def fit_predict(self, train: pd.DataFrame, test: pd.DataFrame, kind="lr", seed=0):
        """train/test: single-agent experiments with columns cell, perts, y.  Returns P(sensitive) for test rows."""
        tr = train[train.y.notna()].reset_index(drop=True)
        Xtr = self.features(tr, tr, tr); Xte = self.features(tr, test, tr)
        if kind == "lr":
            sc = StandardScaler().fit(Xtr)
            m = LogisticRegression(C=0.3, max_iter=2000).fit(sc.transform(Xtr), tr.y.values)
            return m.predict_proba(sc.transform(Xte))[:, 1]
        m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, l2_regularization=1.0, random_state=seed).fit(Xtr, tr.y.values)
        return m.predict_proba(Xte)[:, 1]
