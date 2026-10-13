"""Prediction routes for unseen compounds: chemistry, annotation, typed knowledge and target context.

File summary
- Path: research/knowledge_reality_20261013/models.py
- Purpose: every arm's prediction of a held-out compound's selective profile across cell lines.
- Core points:
  - The target is the selective residual: a compound's log2 fold change after removing its own
    intercept and its slope on the generic profile G (the per-line median over training
    compounds). Predictions are residualised the same way, so a route that predicts only general
    line sensitivity scores zero.
  - Routes. Each reads training compounds' outcomes, the query's admissible inputs, and the lines'
    basal state:
    - `chem_knn`: Morgan Tanimoto kNN (k 10, weight sim^2, floor 0.3, RKT's chem parameters).
    - `chem_ridge`: kernel ridge on the Tanimoto kernel; the penalty is chosen by inner grouped CV.
    - `annot`: Jaccard kNN over PRISM Hub targets and MoA strings (plain annotation).
    - `rkt_know`: RKT's knowledge route: Jaccard kNN over Hub targets, MoA and signed (inhibit or
      activate) MAP-KG curated edges, with k 10, weight sim^1 and floor 0.
    - `kn_typed`: weighted Jaccard kNN over typed, provenance-qualified T0 edges:
      - token = (gene, relation, provenance group);
      - weights: curated 1.0, measured 0.5, MoA 1.0.
    - `tc`, the target-context route: a pooled ridge on (compound, line) rows. Features, for each
      relation type x provenance group:
      - mean and max expression z of the targets in that line;
      - target hotspot and deleterious mutation;
      - fraction of targets expressed.
      Its weights are shared across compounds, so it can predict a mechanism family absent from
      training.
  - Refusals: a route with no neighbour or no admissible target returns NaN rows with a named
    reason. A stack then counts the route as contributing zero for that compound.
  - `stack`: non-negative least squares on inner out-of-fold route predictions, pooled over
    (compound, line), fitted per outer fold. A logistic calibrator for the selective-hit event is
    fitted on the same inner predictions.
- Interfaces: `residualise`, `tanimoto`, `knn_predict`, `KernelRidge`, `token_matrix`,
  `weighted_jaccard`, `tc_features`, `TargetContext`, `nnls_stack`.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.optimize import nnls

NO_NEIGHBOUR = "NO_NEIGHBOUR"
NO_T0_TARGET = "NO_T0_TARGET"
CHEM_PARAMS = (10, 2.0, 0.3)
KNOW_PARAMS = (10, 1.0, 0.0)
TYPED_WEIGHTS = {0: 1.0, 1: 0.5}          # provenance group -> token weight (curated, measured)
RIDGE_ALPHAS = (0.3, 1.0, 3.0, 10.0, 30.0)
TC_ALPHA = 1e3


def residualise(M: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Remove each row's intercept and slope on G over its finite entries (NaN stays NaN)."""

    out = np.full_like(M, np.nan, dtype=np.float64)
    for i, y in enumerate(M):
        f = np.isfinite(y) & np.isfinite(G)
        if f.sum() < 10:
            continue
        X = np.column_stack([np.ones(f.sum()), G[f]])
        beta, *_ = np.linalg.lstsq(X, y[f], rcond=None)
        out[i, f] = y[f] - X @ beta
    return out


def tanimoto(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    A = A.astype(np.float32)
    B = B.astype(np.float32)
    inter = A @ B.T
    na = A.sum(1)[:, None]
    nb = B.sum(1)[None, :]
    den = na + nb - inter
    return np.where(den > 0, inter / np.maximum(den, 1e-9), 0.0)


def knn_predict(sim: np.ndarray, S_ref: np.ndarray, k: int, power: float, floor: float) -> np.ndarray:
    """Similarity-weighted mean of the k most similar references' residual profiles (NaN-aware)."""

    out = np.full((sim.shape[0], S_ref.shape[1]), np.nan)
    finite = np.isfinite(S_ref)
    S0 = np.where(finite, S_ref, 0.0)
    for i, s in enumerate(sim):
        idx = np.argpartition(-s, min(k, len(s) - 1))[:k]
        idx = idx[(s[idx] > floor) & (s[idx] > 0)]
        if idx.size == 0:
            continue
        w = s[idx] ** power
        num = w @ S0[idx]
        den = w @ finite[idx]
        out[i] = np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)
    return out


class KernelRidge:
    """Multi-output kernel ridge on a precomputed kernel, solved once by eigendecomposition."""

    def __init__(self, K: np.ndarray, S: np.ndarray):
        self.evals, self.evecs = np.linalg.eigh(K.astype(np.float64))
        self.proj = self.evecs.T @ np.where(np.isfinite(S), S, 0.0)

    def predict(self, K_query: np.ndarray, alpha: float) -> np.ndarray:
        return self.predict_many(K_query, (alpha,))[alpha]

    def predict_many(self, K_query: np.ndarray, alphas) -> dict:
        KE = K_query.astype(np.float64) @ self.evecs
        return {a: (KE @ (self.proj / (self.evals + a)[:, None])).astype(np.float32) for a in alphas}


def token_matrix(n_drugs: int, rows: list[tuple[int, str, float]]) -> tuple[sparse.csr_matrix, np.ndarray]:
    """Binary drug x token matrix and the per-token weight vector."""

    vocab: dict = {}
    weight: list = []
    r, c = [], []
    for d, tok, w in rows:
        if tok not in vocab:
            vocab[tok] = len(vocab)
            weight.append(w)
        r.append(d)
        c.append(vocab[tok])
    X = sparse.csr_matrix((np.ones(len(r), dtype=np.float32), (r, c)), shape=(n_drugs, max(len(vocab), 1)))
    X.data[:] = 1.0
    X.sum_duplicates()
    X.data[:] = 1.0
    return X, np.asarray(weight if weight else [0.0], dtype=np.float32)


def weighted_jaccard(X: sparse.csr_matrix, w: np.ndarray, qi: np.ndarray, ri: np.ndarray) -> np.ndarray:
    Xw = X.multiply(w[None, :]).tocsr()
    inter = (Xw[qi] @ X[ri].T).toarray()
    wq = np.asarray(Xw[qi].sum(1)).ravel()[:, None]
    wr = np.asarray(Xw[ri].sum(1)).ravel()[None, :]
    den = wq + wr - inter
    return np.where(den > 0, inter / np.maximum(den, 1e-9), 0.0)


TC_GROUPS = [(rel, pg) for rel in (0, 1, 2) for pg in (0, 1)]
TC_STATS = ("mean_z", "max_z", "hotspot", "deleterious", "expressed")


def tc_features(edge_drug, edge_gene, edge_rel, edge_prov, n_drugs: int, Z: np.ndarray, expressed: np.ndarray,
                hotspot: np.ndarray, deleterious: np.ndarray, typed: bool = True,
                groups: tuple = (0, 1)) -> tuple[np.ndarray, np.ndarray]:
    """Per-drug feature tensor [drug, line, feature] and the mask of drugs with an admissible target.

    With ``typed`` False every target falls into one group, the untyped ablation.
    """

    keep = np.isin(edge_prov, groups)
    ed, eg, er, ep = edge_drug[keep], edge_gene[keep], edge_rel[keep], edge_prov[keep]
    glist = [(rel, pg) for rel in (0, 1, 2) for pg in groups] if typed else [(-1, -1)]
    L = Z.shape[0]
    F = np.zeros((n_drugs, L, len(glist) * len(TC_STATS)), dtype=np.float32)
    has = np.zeros(n_drugs, dtype=bool)
    for gi_, (rel, pg) in enumerate(glist):
        m = np.ones(len(ed), bool) if rel < 0 else (er == rel) & (ep == pg)
        if not m.any():
            continue
        A = sparse.csr_matrix((np.ones(m.sum(), np.float32), (ed[m], eg[m])), shape=(n_drugs, Z.shape[1]))
        A.data[:] = 1.0
        A.sum_duplicates()
        A.data[:] = 1.0
        cnt = np.asarray(A.sum(1)).ravel()
        ok = cnt > 0
        has |= ok
        An = sparse.diags(np.where(ok, 1.0 / np.maximum(cnt, 1), 0.0)) @ A
        base = gi_ * len(TC_STATS)
        F[:, :, base + 0] = (An @ Z.T).astype(np.float32)
        F[:, :, base + 2] = ((A @ hotspot.T.astype(np.float32)) > 0).astype(np.float32)
        F[:, :, base + 3] = ((A @ deleterious.T.astype(np.float32)) > 0).astype(np.float32)
        F[:, :, base + 4] = (An @ expressed.T.astype(np.float32)).astype(np.float32)
        Ac = A.tocsr()
        for d in np.where(ok)[0]:
            cols = Ac.indices[Ac.indptr[d]:Ac.indptr[d + 1]]
            F[d, :, base + 1] = Z[:, cols].max(1)
    return F, has


class TargetContext:
    """Pooled ridge of selective residual on target-context features, shared across compounds.

    Fitting and prediction run over compound chunks, so memory stays at one chunk of features.
    """

    CHUNK = 400

    def __init__(self, alpha: float = TC_ALPHA):
        self.alpha = alpha
        self.beta = None

    @staticmethod
    def _residual_features(F: np.ndarray, G: np.ndarray) -> np.ndarray:
        X = np.column_stack([np.ones_like(G), G])     # lines x 2; rank-2 projection onto [1, G]
        C = np.einsum("kl,dlf->dkf", np.linalg.pinv(X), F)
        return F - np.einsum("lk,dkf->dlf", X, C)

    def fit(self, F: np.ndarray, S: np.ndarray, G: np.ndarray, drugs: np.ndarray) -> "TargetContext":
        nf = F.shape[2]
        XtX = np.zeros((nf, nf))
        Xty = np.zeros(nf)
        s1 = np.zeros(nf)
        s2 = np.zeros(nf)
        n = 0
        for i in range(0, len(drugs), self.CHUNK):
            d = drugs[i:i + self.CHUNK]
            Fr = self._residual_features(F[d].astype(np.float64), G)
            y = S[d]
            m = np.isfinite(y)
            Fm = np.where(m[..., None], Fr, 0.0).reshape(-1, nf)
            yv = np.where(m, y, 0.0).ravel()
            XtX += Fm.T @ Fm
            Xty += Fm.T @ yv
            s1 += Fm.sum(0)
            s2 += (Fm ** 2).sum(0)
            n += Fm.shape[0]
        sd = np.sqrt(np.maximum(s2 / max(n, 1) - (s1 / max(n, 1)) ** 2, 0.0))
        self.scale = np.where(sd > 1e-8, sd, 1.0)
        A = XtX / np.outer(self.scale, self.scale) + self.alpha * np.eye(nf)
        self.beta = np.linalg.solve(A, Xty / self.scale)
        return self

    def predict(self, F: np.ndarray, G: np.ndarray, drugs: np.ndarray) -> np.ndarray:
        out = np.empty((len(drugs), F.shape[1]))
        b = self.beta / self.scale
        for i in range(0, len(drugs), self.CHUNK):
            d = drugs[i:i + self.CHUNK]
            out[i:i + len(d)] = np.einsum("dlf,f->dl", self._residual_features(F[d].astype(np.float64), G), b)
        return out


def nnls_stack(preds: list[np.ndarray], S: np.ndarray) -> np.ndarray:
    """Non-negative weights of route predictions (NaN = refused, counted as 0) for the residual S."""

    m = np.isfinite(S)
    cols = [np.where(np.isfinite(p), p, 0.0)[m] for p in preds]
    X = np.column_stack(cols)
    w, _ = nnls(X, S[m])
    return w


def combine(preds: list[np.ndarray], w: np.ndarray) -> np.ndarray:
    out = np.zeros_like(np.where(np.isfinite(preds[0]), preds[0], 0.0))
    for p, wi in zip(preds, w):
        out = out + wi * np.where(np.isfinite(p), p, 0.0)
    return out
