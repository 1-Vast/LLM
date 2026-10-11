"""Feature evidence for block N: CCLE features, the line split and statistical biomarker selection.

* ``feature_matrix``: CCLE 19Q4 log2(TPM+1) expression of genes with SD > 0.5 across PRISM lines
  (``GENE:expr``) and damaging/hotspot mutations present in 5 to n-5 lines (``GENE:mut``).
* ``line_split``: one fixed split of lines with complete features into discovery and test halves
  (seed 20261011); ``discovery(size)`` gives nested random subsets of the discovery half.
* ``predict_top``: choose the k candidate features with the largest |r| with the selective profile
  on discovery lines and predict test lines by the sign-adjusted mean z.
* ``predict_claims``: the agent's features with the agent's own signs (no fitting).
* ``ridge_predict``: ridge on all expression features, alpha by 5-fold CV on discovery lines.
"""
from __future__ import annotations

import numpy as np

SEED = 20261011


class Features:
    def __init__(self, world):
        expr, mutated = world.ccle()
        E = expr.to_numpy(float)
        keep = np.nanstd(E, axis=0) > 0.5
        genes = np.array(expr.columns)[keep]
        mg = [g for g, s in mutated.items() if 5 <= len(s) <= len(world.lines) - 5]
        M = np.array([[1.0 if line in mutated[g] else 0.0 for g in mg] for line in world.lines])
        self.names = [f"{g}:expr" for g in genes] + [f"{g}:mut" for g in mg]
        self.F = np.concatenate([E[:, keep], M], axis=1)
        self.n_expr = int(keep.sum())
        self.index = {n: i for i, n in enumerate(self.names)}
        self.ok_lines = np.isfinite(self.F).all(axis=1)
        rng = np.random.default_rng(SEED)
        lines = np.where(self.ok_lines)[0]
        perm = rng.permutation(lines)
        self.disc_all = np.sort(perm[: len(perm) // 2])
        self.test = np.sort(perm[len(perm) // 2:])
        self.disc_order = rng.permutation(self.disc_all)

    def discovery(self, size: int | None) -> np.ndarray:
        return np.sort(self.disc_order[:size]) if size else self.disc_all

    def columns(self, claims) -> tuple[np.ndarray, np.ndarray]:
        """Feature columns and agent signs (-1 sensitizing: lower log fold change) for mappable claims."""
        cols, signs = [], []
        for c in claims:
            key = f"{c['gene']}:{'mut' if c['feature'] == 'mutation' else 'expr'}"
            if key in self.index and self.index[key] not in cols:
                cols.append(self.index[key])
                signs.append(-1.0 if c["effect"] == "sensitizing" else 1.0)
        return np.array(cols, int), np.array(signs, float)

    def _z(self, d_rows):
        mu, sd = np.nanmean(self.F[d_rows], axis=0), np.nanstd(self.F[d_rows], axis=0)
        sd = np.where(sd == 0, np.inf, sd)
        return mu, sd

    def corr(self, cols, y_d, d_rows):
        X = self.F[d_rows][:, cols]
        Xc = X - X.mean(axis=0)
        yc = y_d - y_d.mean()
        den = np.sqrt((Xc ** 2).sum(axis=0) * (yc ** 2).sum())
        with np.errstate(invalid="ignore", divide="ignore"):
            r = (Xc * yc[:, None]).sum(axis=0) / den
        return np.where(np.isfinite(r), r, 0.0)

    def predict_top(self, cols, y_d, d_rows, t_rows, k):
        if len(cols) == 0:
            return None
        r = self.corr(cols, y_d, d_rows)
        order = np.argsort(-np.abs(r))[:k]
        mu, sd = self._z(d_rows)
        c = cols[order]
        return (((self.F[t_rows][:, c] - mu[c]) / sd[c]) * np.sign(r[order])).mean(axis=1)

    def predict_claims(self, cols, signs, d_rows, t_rows, k=None):
        if len(cols) == 0:
            return None
        c, s = cols[:k], signs[:k]
        mu, sd = self._z(d_rows)
        return (((self.F[t_rows][:, c] - mu[c]) / sd[c]) * s).mean(axis=1)

    def ridge_predict(self, y_d, d_rows, t_rows):
        from sklearn.linear_model import RidgeCV
        X = self.F[:, : self.n_expr]
        mu, sd = np.nanmean(X[d_rows], axis=0), np.nanstd(X[d_rows], axis=0)
        sd = np.where(sd == 0, np.inf, sd)
        m = RidgeCV(alphas=np.logspace(1, 5, 9), cv=5).fit((X[d_rows] - mu) / sd, y_d)
        return m.predict((X[t_rows] - mu) / sd)
