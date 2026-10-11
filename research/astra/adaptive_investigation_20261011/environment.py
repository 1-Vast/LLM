"""Offline campaign environment for block O: buy real observations of an unseen compound, then predict.

A campaign is one query compound. The hidden truth is its recorded data:
* its GSE92742 landmark signatures (each line x time option it has);
* its PRISM 19Q4 primary viability profile (578 lines).

A policy spends a budget on actions from a recorded menu:
* ``("l1000", option)``: reveals the query's real signature for that line x time option;
* ``("viability", line)``: reveals the query's real log fold change in one discovery-half line.

Nothing absent from the data can be bought. At the end the policy submits a predicted profile
over all lines. It is scored on the test-half lines, which no policy may buy (block N line
split, seed 20261011).

The world model is ``Posterior``, a library Gaussian process over lines:
* Reference weights w ∝ exp(L1000 similarity / tau_l), over the options measured so far (an
  optional knowledge prior adds to the log weights).
* Profiles are modelled as offset + potency x G + selective part.
  * Offset and potency are nuisance terms with a broad prior (variance kappa on the constant
    and on G).
  * The selective part has the w-weighted mean and covariance of the references' selective
    (G-residualised) profiles, plus alpha times their unweighted covariance, plus sigma^2 noise.
* Viability observations condition the Gaussian linearly.
* The planner's target is the posterior variance of the *selective* part on test lines, so it
  does not pay to learn generic potency.

It does not collapse onto one reference as lines accumulate, as a mixture likelihood does
(feasibility F1 smoke test). With every option measured and no viability data, the mean is
block N's similarity-weighted transfer up to the kernel (softmax vs top-5).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BLOCK_N = HERE.parent / "mechanism_routing_20261011"
sys.path.insert(0, str(BLOCK_N))
import mining as MI  # noqa: E402
import predictors as PR  # noqa: E402


@dataclass
class Library:
    """Open drugs with L1000 signatures and PRISM profiles; every campaign draws its pool from here."""

    world: object
    fe: object
    P: np.ndarray            # raw primary profiles (n_drug, n_line), NaN where unmeasured
    Pf: np.ndarray           # profiles with NaN filled by the drug's mean (for moments only)
    X: np.ndarray            # L1000 signatures (n_drug, n_option, n_gene), zeros where absent
    have: np.ndarray         # (n_drug, n_option) option measured
    norm: np.ndarray         # (n_drug, n_option)
    G: np.ndarray
    test: np.ndarray         # test-half line indices
    disc: np.ndarray         # discovery-half line indices (buyable)
    R: np.ndarray = None     # selective (G-residualised) profiles, NaN filled by 0
    Gmean: np.ndarray = None # mean raw profile over the library (prior mean of offset + potency)

    @classmethod
    def open(cls):
        w = PR.load_world("open")
        fe = MI.Features(w)
        P = w.P.astype(float)
        Pf = np.where(np.isfinite(P), P, np.nanmean(P, axis=1, keepdims=True))
        G = np.nanmean(P, axis=0)  # generic profile over every open drug (each query is 1/982 of it)
        R = np.stack([PR.residual(Pf[j], G) for j in range(len(Pf))])
        return cls(world=w, fe=fe, P=P, Pf=Pf, X=w.Xf, have=w.l1000_have, norm=w.l1000_norm, G=G,
                   test=fe.test, disc=fe.disc_all, R=np.nan_to_num(R), Gmean=np.nanmean(Pf, axis=0))

    def option_cos(self, i: int, o: int, pool: np.ndarray) -> np.ndarray:
        """Cosine between query i's signature in option o and each pool drug's (NaN where absent)."""
        num = self.X[pool, o] @ self.X[i, o]
        den = self.norm[pool, o] * self.norm[i, o]
        ok = self.have[pool, o] & (den > 0)
        return np.where(ok, num / np.maximum(den, 1e-12), np.nan)

    def pool(self, i: int, regime: str = "novel_class") -> np.ndarray:
        idx = np.arange(len(self.P))
        keep = idx != i
        if regime == "novel_class":
            keep &= self.world.moa != self.world.moa[i]
        return idx[keep]


def score(lib: Library, i: int, pred: np.ndarray | None) -> dict:
    """Selective r on test lines, and precision of the 10 lines predicted most selectively killed."""
    y = PR.residual(lib.P[i], lib.G)
    t = lib.test[np.isfinite(y[lib.test])]
    if pred is None or not np.isfinite(pred[t]).all():
        return {"r": 0.0, "p10": 0.1}  # no prediction: chance precision (hits are 10% of test lines)
    p = PR.residual(pred, lib.G)
    r = PR.pearson(p[t], y[t], 30)
    hits = set(t[np.argsort(y[t])[: max(1, int(round(0.1 * len(t))))]])
    top = t[np.argsort(p[t])[:10]]
    return {"r": 0.0 if not np.isfinite(r) else float(r), "p10": float(np.mean([j in hits for j in top]))}


@dataclass
class Posterior:
    """Library Gaussian process on selective profiles, with offset and potency as nuisance terms."""

    lib: Library
    i: int
    pool: np.ndarray
    tau_l: float = 0.05
    sigma: float = 0.5
    alpha: float = 0.2
    kappa: float = 4.0
    options: list = field(default_factory=list)
    lines: dict = field(default_factory=dict)
    prior_logw: np.ndarray | None = None  # optional external prior (knowledge), log scale

    def __post_init__(self):
        R = self.lib.R[self.pool]
        self._R = R
        self._Gc = (R - R.mean(axis=0)) / np.sqrt(len(self.pool))      # unweighted library factor
        g = self.lib.G - np.nanmean(self.lib.G)
        self._N = np.sqrt(self.kappa) * np.stack([np.ones_like(g), g / np.std(g)])  # nuisance factor (2, L)

    def l1000_sim(self) -> np.ndarray:
        """Mean similarity over measured options (least similar where no option is shared)."""
        if not self.options:
            return np.zeros(len(self.pool))
        sims = np.stack([self.lib.option_cos(self.i, o, self.pool) for o in self.options])
        with np.errstate(invalid="ignore"):
            s = np.nanmean(sims, axis=0)
        if not np.isfinite(s).any():
            return np.zeros(len(self.pool))
        return np.where(np.isfinite(s), s, np.nanmin(s))

    def weights(self, sim: np.ndarray | None = None) -> np.ndarray:
        lw = (self.l1000_sim() if sim is None else sim) / self.tau_l
        if self.prior_logw is not None:
            lw = lw + self.prior_logw
        lw = lw - lw.max()
        w = np.exp(lw)
        return w / w.sum()

    def factors(self, w: np.ndarray, cols: np.ndarray):
        """Mean and covariance factors on ``cols``: Sigma = D^T D + Gf^T Gf + N^T N (+ sigma^2 I)."""
        Rc = self._R[:, cols]
        mu = w @ Rc + self.lib.Gmean[cols]
        D = np.sqrt(w)[:, None] * (Rc - w @ Rc)
        return mu, np.vstack([D, np.sqrt(self.alpha) * self._Gc[:, cols], self._N[:, cols]])

    def _solve_parts(self, w):
        S = np.array(list(self.lines.keys()))
        yS = np.array([self.lines[k] for k in S])
        muS, FS = self.factors(w, S)
        A = FS.T @ FS + self.sigma ** 2 * np.eye(len(S))
        return S, yS, muS, FS, A

    def predict(self, w: np.ndarray | None = None) -> np.ndarray:
        w = self.weights() if w is None else w
        cols = np.arange(self.lib.Pf.shape[1])
        mu, F = self.factors(w, cols)
        if self.lines:
            S, yS, muS, FS, A = self._solve_parts(w)
            mu = mu + (F.T @ FS) @ np.linalg.solve(A, yS - muS)
            for k, v in self.lines.items():  # measured lines are known
                mu[k] = v
        return mu

    def test_projector(self):
        """Columns spanning the nuisance directions on test lines (removed from the target)."""
        t = self.lib.test
        B = np.stack([np.ones(len(t)), self.lib.G[t]], axis=1)
        Qb, _ = np.linalg.qr(B)
        return Qb

    def _project(self, M, Qb):
        """Remove the nuisance directions from the rows-as-test-lines matrix M (n_test x k)."""
        return M - Qb @ (Qb.T @ M)

    def test_trace(self, w: np.ndarray, Qb=None) -> float:
        """Posterior variance of the selective part on test lines, given the measured lines, under weights w."""
        t = self.lib.test
        Qb = self.test_projector() if Qb is None else Qb
        _, Ft = self.factors(w, t)
        Ftp = self._project(Ft.T, Qb)            # (n_test, k)
        tr = float((Ftp ** 2).sum())
        if self.lines:
            S, yS, muS, FS, A = self._solve_parts(w)
            K = Ftp @ FS                          # (n_test, |S|)
            tr -= float(np.sum(K * np.linalg.solve(A, K.T).T))
        return tr
