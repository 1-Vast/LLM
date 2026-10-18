"""Corrected decision pipeline on top of the frozen program-revision engine (nothing frozen is edited).

File summary
- Path: research/seed_attribution_20261017/corrected.py
- Purpose: the decision machinery of `program_revision_20261017` with four repairs, each switchable so
  the frozen behaviour can be reproduced exactly and every correction measured on its own.
  1. `CorrectedDomain`: reference median, threshold, labels and known status all come from
     `contract.endpoint` (one implementation). The frozen `Domain.thr` is kept as ``frozen_thr``.
  2. `SafeContextFold`: the strong-model fit cache is keyed by a digest of the training matrix. The
     frozen key (training lines, settings, shape) ignores the data, so a changed label with the same
     lines returns a stale fit and can hide a leak.
  3. Out-of-sample uncertainty of the COMPLETE corrected predictor: `crossfit_variance` refits the
     correction on inner folds of the training residuals and measures the residual variance of the
     held-out lines. The frozen library variance (`resid_var`) is measured on the residuals the
     correction was just fitted to, which is optimistic for every drug inside a program scope.
  4. `ReplayInterface`: outcomes of the target lines are reachable only through `probe` and `confirm`.
     The domain handed to every fit has them masked, and a ledger records each reveal.
- Correctors (all share the duck-typed interface that `ProgramLibrary` has, so the frozen
  `LinePredictor` can use them): `ProgramLibrary` itself, `GlobalInteractionRidge` (shared loadings of
  chosen scope x gate products, ridge strength by inner cross-fitting), `PerDrugGateRidge` (each drug
  regressed on the same gate genes, no scope), `PooledGBM` (boosted trees on scope flags and gate
  flags). Every tuning choice is made on the training residuals only, from a fixed small grid.
- Interfaces: `CorrectedDomain`, `SafeContextFold`, `decide`, `crossfit_variance`, `CorrectedPredictor`,
  `run_campaign_masked`, `ReplayInterface`, `corrector_key`, `GlobalInteractionRidge`, `PerDrugGateRidge`, `PooledGBM`,
  `AdditiveRidge`, `gate_columns`, `scope_columns`.
"""
from __future__ import annotations

import copy
import hashlib
import sys
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN = ROOT / "research" / "program_revision_20261017"
if str(FROZEN) not in sys.path:
    sys.path.insert(0, str(FROZEN))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import engine  # noqa: E402  (frozen)
import policy  # noqa: E402  (frozen)
from common import hash_unit  # noqa: E402  (frozen)
from vc import LineContext, ProgramLibrary, blr, scope_mask  # noqa: E402  (frozen)

import contract  # noqa: E402

TAU_DENOM = 6.0  # frozen convention: predictive variance adds rep_var / 6 (endpoint mean vs the X1-X3 target)
LAMBDAS = (1.0, 10.0, 100.0, 1e3, 1e4, 1e5)


# ------------------------------------------------------------------ domain, fits, cache


class CorrectedDomain(engine.Domain):
    """`engine.Domain` with the endpoint, reference and threshold defined once, by `contract`."""

    def __init__(self, open_future: bool = False):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            super().__init__(open_future)
        self.frozen_thr, self.frozen_med = self.thr.copy(), self.med.copy()
        self.endpoint = contract.endpoint(self.X2, self.X3, self.src_line)
        self.med, self.thr = self.endpoint.med, self.endpoint.thr
        self.hit, self.known = self.endpoint.hit, self.endpoint.known
        self._model_cache = {}


def safe_fitted_model(dom, train_rows, Ytr, strong):
    """Strong-model fit cache keyed by the data too (the frozen key is lines + settings + shape)."""

    cache = dom.__dict__.setdefault("_safe_model_cache", {})
    digest = hashlib.sha256(np.ascontiguousarray(np.nan_to_num(Ytr, nan=1e9)).tobytes()).hexdigest()
    key = (np.asarray(train_rows).tobytes(), tuple(sorted(strong.items())), Ytr.shape, digest)
    if key not in cache:
        cache[key] = engine.StrongModel(**strong).fit(Ytr)
    return copy.copy(cache[key])


class SafeContextFold(engine.ContextFold):
    """`engine.ContextFold` whose fits cannot be served from a stale cache."""

    def _predict(self, Ytr, train_rows, new_rows):
        dom = self.dom
        m = safe_fitted_model(dom, train_rows, Ytr, self.strong)
        m.line_prior(dom.line_Z(train_rows, self.info, self.lin_cols))
        Znew = dom.line_Z(new_rows, self.info, self.lin_cols)
        probes = None
        noise = None
        if self.probe_cores:
            noise = m.resid_var + 0.67 * dom.rep_var[self.drows]
            probes = []
            for c in new_rows:
                obs = {}
                for p, d in zip(self.probe_pos, self.probe_idx):
                    v = dom.X1[d, c]
                    if np.isfinite(v):
                        obs[int(p)] = float(v)
                probes.append(obs)
        mean, S, C = m.predict_lines(Znew, probes, noise)
        self._last_model = m
        return mean, S, C


# ------------------------------------------------------------------ feature columns


def gate_columns(dom, genes) -> np.ndarray:
    """(lines, genes) panel status of the named genes (legal decision-time inputs)."""

    idx = {g: i for i, g in enumerate(dom.lf["panel_genes"])}
    return np.column_stack([dom.lf["panel"][:, idx[g]] for g in genes])


def scope_columns(dom, scopes, drug_rows) -> np.ndarray:
    """(drugs, scopes) membership of each drug in each scope token."""

    return np.column_stack([scope_mask(s, dom.df, drug_rows) for s in scopes]).astype(float)


def _fold_ids(fold, salt: str, n: int) -> np.ndarray:
    h = hash_unit(fold.dom.lines.depmap_id.to_numpy()[fold.train], salt)
    return np.minimum((h * n).astype(int), n - 1)


# ------------------------------------------------------------------ conventional correctors


class _Corrector:
    """Shared plumbing: gate states, standardisation, and the ProgramLibrary-like surface."""

    kind = "corrector"

    def __init__(self, genes, scopes=(), pairs=()):
        self.genes, self.scopes, self.pairs = list(genes), list(scopes), list(pairs)
        self.programs = [f"{self.kind}:{i}" for i in range(max(1, len(self.pairs) or len(self.genes)))]

    def copy(self):
        return copy.deepcopy(self)

    def digest(self) -> str:
        return hashlib.sha256(repr((self.kind, self.genes, self.scopes, self.pairs)).encode()).hexdigest()[:16]

    def states(self, ctx: LineContext) -> np.ndarray:
        return np.column_stack([ctx.atom(("mut", g)) for g in self.genes]).astype(float)

    def _standardise(self, Phi):
        self.mu = Phi.mean(0)
        self.sd = Phi.std(0) + 1e-9
        return (Phi - self.mu) / self.sd


def _cv_lambda(fit_predict, R, X, folds, grid):
    """Pick the ridge strength with the smallest held-out squared error; ties go to the larger one."""

    best = None
    for lam in grid:
        err, n = 0.0, 0
        for f in range(folds.max() + 1):
            tr, te = np.flatnonzero(folds != f), np.flatnonzero(folds == f)
            if len(te) == 0 or len(tr) == 0:
                continue
            pred = fit_predict(R[:, tr], X[tr], X[te], lam)
            ok = np.isfinite(R[:, te])
            err += float(((R[:, te][ok] - pred[ok]) ** 2).sum())
            n += int(ok.sum())
        score = err / max(n, 1)
        if best is None or score <= best[0]:
            best = (score, lam)
    return best[1]


class GlobalInteractionRidge(_Corrector):
    """R[d, c] ~ sum_k beta_k * scope_k(d) * gate_k(c) with ONE ridge-penalised beta per product.

    ``pairs`` is a list of (scope, gene). The seed library's ten pairs give the 'same features' model;
    the full cross of the seed scopes and genes gives the model that must learn the correspondence.
    No per-drug term and no hierarchy, so it is the conventional regularised counterpart of a program
    layer with shared loadings.
    """

    kind = "global_ridge"

    def __init__(self, pairs):
        genes = sorted({g for _, g in pairs})
        super().__init__(genes, sorted({s for s, _ in pairs}), pairs)
        self.col = [genes.index(g) for _, g in pairs]

    def _design(self, dfeat, drows):
        return np.column_stack([scope_mask(s, dfeat, drows) for s, _ in self.pairs]).astype(float)

    def _solve(self, R, X, A, lam):
        K = len(self.pairs)
        gram = np.zeros((K, K))
        rhs = np.zeros(K)
        obs = np.isfinite(R)
        active = np.flatnonzero(A.any(1))
        for d in active:
            o = obs[d]
            Xo = X[o][:, self.col] * A[d][None, :]
            gram += Xo.T @ Xo
            rhs += Xo.T @ R[d, o]
        return np.linalg.solve(gram + lam * np.eye(K), rhs)

    def fit(self, R, Phi, dfeat, drows):
        X = self._standardise(Phi)
        A = self._design(dfeat, drows)
        folds = np.minimum((hash_unit(np.arange(len(X)), "global-ridge-cv") * 5).astype(int), 4)

        def fit_predict(Rtr, Xtr, Xte, lam):
            beta = self._solve(Rtr, Xtr, A, lam)
            return A @ (beta[:, None] * Xte[:, self.col].T)

        self.lam = _cv_lambda(fit_predict, R, X, folds, LAMBDAS)
        self.beta = self._solve(R, X, A, self.lam)
        self._A = A
        fitted = A @ (self.beta[:, None] * X[:, self.col].T)
        res = np.where(np.isfinite(R), R - fitted, np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.resid_var = np.nanmean(res ** 2, axis=1)
        return self

    def correction(self, Phi_new, dfeat, drows, novel=False):
        X = (Phi_new - self.mu) / self.sd
        A = self._design(dfeat, drows)
        return A @ (self.beta[:, None] * X[:, self.col].T)


class PerDrugGateRidge(_Corrector):
    """R[d, :] ~ gate genes, one ridge per drug (closed-form leave-one-out strength), no scope input."""

    kind = "per_drug_ridge"

    def __init__(self, genes):
        super().__init__(genes)

    def fit(self, R, Phi, dfeat, drows):
        X = self._standardise(Phi)
        D, p = R.shape[0], X.shape[1]
        W = np.zeros((D, p))
        resid = np.full(R.shape, np.nan)
        for d in range(D):
            o = np.isfinite(R[d])
            if o.sum() < 10:
                continue
            Xo, y = X[o], R[d, o]
            U, s, Vt = np.linalg.svd(Xo, full_matrices=False)
            Uy = U.T @ y
            best = None
            for lam in LAMBDAS:
                f = s ** 2 / (s ** 2 + lam)
                h = (U ** 2 * f).sum(1)
                loo = (y - U @ (f * Uy)) / np.maximum(1 - h, 1e-6)
                err = float((loo ** 2).mean())
                if best is None or err <= best[0]:
                    best = (err, lam)
            lam = best[1]
            W[d] = Vt.T @ ((s / (s ** 2 + lam)) * Uy)
            resid[d, o] = y - Xo @ W[d]
        self.W = W
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.resid_var = np.nanmean(resid ** 2, axis=1)
        return self

    def correction(self, Phi_new, dfeat, drows, novel=False):
        X = (Phi_new - self.mu) / self.sd
        return self.W @ X.T


class AdditiveRidge(_Corrector):
    """Same inputs as the seed layer, no interaction: R[d, c] ~ b0 + sum_k a_k scope_k(d) + sum_g c_g gate_g(c).

    The control for the question 'is it the interaction structure or only the inputs?'. Drug-level scope
    effects are already in the strong model, and a gate main effect shifts every drug of a line alike, so
    this model can change a decision only through the level of the line relative to each drug's threshold.
    """

    kind = "additive_ridge"

    def __init__(self, scopes, genes):
        super().__init__(genes, scopes)

    def _stats(self, R, A, G):
        obs = np.isfinite(R)
        R0 = np.where(obs, R, 0.0)
        O = obs.astype(float)
        K, p = A.shape[1], G.shape[1]
        gram = np.zeros((K + p, K + p))
        gram[:K, :K] = A.T @ (O.sum(1)[:, None] * A)
        gram[K:, K:] = G.T @ (O.sum(0)[:, None] * G)
        gram[:K, K:] = A.T @ O @ G
        gram[K:, :K] = gram[:K, K:].T
        rhs = np.concatenate([A.T @ R0.sum(1), G.T @ R0.sum(0)])
        return gram, rhs

    def fit(self, R, Phi, dfeat, drows):
        G = self._standardise(Phi)
        A = np.column_stack([scope_mask(s, dfeat, drows) for s in self.scopes] + [np.ones(len(drows))]).astype(float)
        K = A.shape[1]
        folds = np.minimum((hash_unit(np.arange(len(G)), "additive-ridge-cv") * 5).astype(int), 4)
        best = None
        for lam in LAMBDAS:
            err, n = 0.0, 0
            for f in range(5):
                tr, te = np.flatnonzero(folds != f), np.flatnonzero(folds == f)
                gram, rhs = self._stats(R[:, tr], A, G[tr])
                pen = lam * np.eye(len(rhs))
                pen[K - 1, K - 1] = 0.0  # the intercept is not shrunk
                w = np.linalg.solve(gram + pen, rhs)
                pred = (A @ w[:K])[:, None] + (G[te] @ w[K:])[None, :]
                ok = np.isfinite(R[:, te])
                err += float(((R[:, te][ok] - pred[ok]) ** 2).sum())
                n += int(ok.sum())
            if best is None or err / max(n, 1) <= best[0]:
                best = (err / max(n, 1), lam)
        self.lam = best[1]
        gram, rhs = self._stats(R, A, G)
        pen = self.lam * np.eye(len(rhs))
        pen[K - 1, K - 1] = 0.0
        self.w = np.linalg.solve(gram + pen, rhs)
        fitted = (A @ self.w[:K])[:, None] + (G @ self.w[K:])[None, :]
        res = np.where(np.isfinite(R), R - fitted, np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.resid_var = np.nanmean(res ** 2, axis=1)
        return self

    def correction(self, Phi_new, dfeat, drows, novel=False):
        G = (Phi_new - self.mu) / self.sd
        A = np.column_stack([scope_mask(s, dfeat, drows) for s in self.scopes] + [np.ones(len(drows))]).astype(float)
        K = A.shape[1]
        return (A @ self.w[:K])[:, None] + (G @ self.w[K:])[None, :]


class PooledGBM(_Corrector):
    """Boosted trees on [scope flags of the drug, gate flags of the line], one model for all pairs.

    Early stopping on a random 15% of the pairs replaces a tuning grid; the seed is fixed. This is the
    same-input nonlinear baseline: it may learn any interaction of the 8 scope flags with the 8 gates.
    """

    kind = "pooled_gbm"

    def __init__(self, scopes, genes):
        super().__init__(genes, scopes)

    def _rows(self, A, Xg, d_idx, c_idx):
        return np.column_stack([A[d_idx], Xg[c_idx]])

    def fit(self, R, Phi, dfeat, drows):
        from sklearn.ensemble import HistGradientBoostingRegressor

        self._dfeat_key = None
        self._A = np.column_stack([scope_mask(s, dfeat, drows) for s in self.scopes]).astype(float)
        self.mu = Phi.mean(0)
        self.sd = np.ones(Phi.shape[1])
        d_idx, c_idx = np.nonzero(np.isfinite(R))
        X = self._rows(self._A, Phi, d_idx, c_idx)
        y = R[d_idx, c_idx]
        self.model = HistGradientBoostingRegressor(
            max_depth=3, learning_rate=0.05, max_iter=300, min_samples_leaf=200, l2_regularization=1.0,
            early_stopping=True, validation_fraction=0.15, n_iter_no_change=15, random_state=0).fit(X, y)
        pred = self.model.predict(X)
        res = np.full(R.shape, np.nan)
        res[d_idx, c_idx] = y - pred
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.resid_var = np.nanmean(res ** 2, axis=1)
        return self

    def correction(self, Phi_new, dfeat, drows, novel=False):
        D, n = len(drows), len(Phi_new)
        A = np.column_stack([scope_mask(s, dfeat, drows) for s in self.scopes]).astype(float)
        X = np.column_stack([np.tile(A, (n, 1)), np.repeat(Phi_new, D, axis=0)])
        return self.model.predict(X).reshape(n, D).T


# ------------------------------------------------------------------ decisions


def crossfit_variance(fold, corrector, n_inner: int = 5) -> np.ndarray:
    """Out-of-sample residual variance per drug of the complete corrected predictor.

    The correction is refitted on inner folds of the training residuals ``fold.R_train`` and scored on
    the held-out lines. Drugs outside every scope keep the base out-of-sample variance exactly.
    """

    dom = fold.dom
    ctx_tr, _ = fold.contexts()
    Phi = corrector.states(ctx_tr)
    ids = _fold_ids(fold, "variance-crossfit", n_inner)
    res = np.full(fold.R_train.shape, np.nan)
    for f in range(n_inner):
        tr, te = np.flatnonzero(ids != f), np.flatnonzero(ids == f)
        if len(te) == 0 or len(tr) == 0:
            continue
        c = corrector.copy()
        c.fit(fold.R_train[:, tr], Phi[tr], dom.df, fold.drows)
        res[:, te] = fold.R_train[:, te] - c.correction(Phi[te], dom.df, fold.drows, novel=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        v = np.nanmean(res ** 2, axis=1)
    return np.where(np.isfinite(v), v, fold.oos_var)


def corrector_key(corrector) -> tuple:
    """Cache identity of a corrector: `ProgramLibrary.digest` ignores shared_only and tau, so they are added."""

    return (type(corrector).__name__, corrector.digest(), getattr(corrector, "shared_only", None),
            getattr(corrector, "tau", None))


def decide(fold, corrector, thr: np.ndarray, mean_from: str = "lib", var_from: str = "crossfit",
           cache: dict | None = None):
    """Predictive mean, variance and the threshold-crossing score of one fold.

    ``mean_from``: "lib" (base + correction) or "base". ``var_from``: "base" (out-of-sample variance of
    the strong model), "frozen" (the fitted-on-the-same-residuals variance of the frozen library) or
    "crossfit" (out-of-sample variance of the complete corrected predictor). ``thr`` is the threshold
    per decision drug (the corrected one for repaired decisions, the frozen one to reproduce them).
    """

    dom = fold.dom
    mean = fold.base_mean.copy()
    var = fold.oos_var.copy()
    if corrector is not None and corrector.programs:
        ctx_tr, ctx_te = fold.contexts()
        c = corrector.copy()
        c.fit(fold.R_train, c.states(ctx_tr), dom.df, fold.drows)
        if mean_from == "lib":
            mean = mean + c.correction(c.states(ctx_te), dom.df, fold.drows, novel=False)
        if var_from == "frozen":
            var = np.where(np.isfinite(c.resid_var), c.resid_var, var)
        elif var_from == "crossfit":
            key = (corrector_key(corrector), id(fold))
            if cache is not None and key in cache:
                var = cache[key]
            else:
                var = crossfit_variance(fold, corrector)
                if cache is not None:
                    cache[key] = var
    var = var + dom.rep_var[fold.drows] / TAU_DENOM
    mean, var = fold._own_probe(mean, var)
    score = contract.crossing_probability(mean, var, thr[:, None])
    return mean, var, score


# ------------------------------------------------------------------ policies on the masked interface


class CorrectedPredictor(policy.LinePredictor):
    """`LinePredictor` with the corrected threshold and, optionally, the out-of-sample variance of the
    complete corrected predictor in place of the strong model's."""

    def __init__(self, fold, corrector=None, oos_var=None, thr=None):
        super().__init__(fold, corrector)
        if oos_var is not None:
            sv = np.einsum("di,lij,dj->d", self.H, fold.C_target, self.H) / len(fold.target)
            self.s2 = np.maximum(oos_var - sv, self.m.resid_var) + fold.dom.rep_var[self.drows] / TAU_DENOM
        if thr is not None:
            self.thr = thr


class ReplayInterface:
    """Holds the target lines' outcomes privately; every fit sees a masked domain.

    ``visible`` is a `CorrectedDomain` with every non-source line and novel drug set to NaN before any
    derived quantity is computed. `probe` and `confirm` are the only ways a target outcome reaches a
    policy, and each call is written to the ledger (logical replay queries, wells charged).
    """

    def __init__(self, truth: CorrectedDomain | None = None, visible: CorrectedDomain | None = None):
        self._truth = truth if truth is not None else CorrectedDomain(open_future=True)
        self.visible = visible if visible is not None else CorrectedDomain(open_future=False)
        self.ledger: list[dict] = []

    def probe(self, d: int, c: int) -> float:
        v = float(self._truth.X1[d, c])
        self.ledger.append({"kind": "probe", "drug": int(d), "line": int(c), "wells": 1, "returned": bool(np.isfinite(v))})
        return v

    def confirm(self, d: int, c: int):
        x2, x3 = float(self._truth.X2[d, c]), float(self._truth.X3[d, c])
        self.ledger.append({"kind": "confirm", "drug": int(d), "line": int(c), "wells": 2,
                            "returned": bool(np.isfinite(x2) or np.isfinite(x3))})
        return x2, x3

    def with_probes(self, design_rows, target_rows) -> CorrectedDomain:
        """A copy of the visible domain whose design-probe X1 cells on the targets were purchased."""

        vis = copy.copy(self.visible)
        vis.X1 = self.visible.X1.copy()
        for d in design_rows:
            for c in target_rows:
                vis.X1[d, c] = self.probe(int(d), int(c))
        vis._safe_model_cache = {}
        vis._model_cache = {}
        return vis

    def score(self, nom: np.ndarray, drug_rows: np.ndarray, line_rows: np.ndarray):
        """Evaluator only (never called by a policy): hits and unknowns of nominations vs the truth."""

        return engine.score_nominations(self._truth, nom, drug_rows, line_rows)

    def wells(self) -> dict:
        out = {"probe": 0, "confirm": 0}
        for r in self.ledger:
            out[r["kind"]] += r["wells"]
        out["queries"] = len(self.ledger)
        return out


def run_campaign_masked(pred, j: int, spec: dict, iface: ReplayInterface):
    """The frozen campaign loop, but every outcome comes from the interface and labels from `contract`."""

    vis = pred.dom
    c = int(pred.fold.target[j])
    readouts, trace = [], []
    wells = rounds = 0
    confirmed, hits, first3 = set(), 0, None
    for size in spec["batches"]:
        if wells + 2 > spec["budget"]:
            break
        rounds += 1
        sc, _, _, _ = pred.score(j, readouts)
        order = np.lexsort((vis.tie_drug[pred.drows], -sc))
        batch = []
        for i in order:
            d = int(pred.drows[i])
            if d in confirmed:
                continue
            if len(batch) >= size or wells + 2 > spec["budget"]:
                break
            batch.append((d, float(sc[i])))
            wells += 2
        for d, p in batch:
            confirmed.add(d)
            x2, x3 = iface.confirm(d, c)
            m, n = contract.replicate_summary(np.array([x2]), np.array([x3]))
            known = bool(n[0] >= 1)
            neg = (not np.isfinite(x2) or x2 < 0) and (not np.isfinite(x3) or x3 < 0)
            h = bool(known and neg and m[0] <= vis.thr[d])
            hits += h
            if hits >= 3 and first3 is None:
                first3 = wells
            if known:
                readouts.append((d, float(m[0]), float(vis.rep_var[d]) / int(n[0]), "confirm"))
            trace.append({"round": rounds, "drug": int(d), "p": round(p, 4), "known": known, "hit": h})
    unknown = sum(1 for t in trace if not t["known"])
    return {"hits": int(hits), "wells": int(wells), "rounds": int(rounds), "confirmed": len(confirmed),
            "unknown": int(unknown), "wells_to_3_hits": first3}
