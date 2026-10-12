"""Routed knowledge transfer (RKT): typed transfer routes, each certified, for unprofiled compounds.

File summary
- Path: src/virtual_cell/knowledge_transfer.py
- Purpose: predict a compound's centred transcriptional response in a cell line from separately
  routed knowledge, with a per-query certificate that says how far to trust the specific part of
  the prediction and when to refuse it.
- Routes. Each reads reference compounds only, plus the query compound's own visible lines.
  - ``context``: the same compound profiled in other lines, mapped line to line by ridge maps fitted
    on references profiled in both lines, with leave-one-out lambda.
  - ``pheno``: references whose responses in the visible lines resemble the query's (cosine kNN).
  - ``chem``: structural analogues (Morgan Tanimoto kNN).
  - ``know``: knowledge analogues (Jaccard kNN over targets, mechanisms and signed graph edges).
- Prediction: ``gamma * g_T + rho * sqrt(1 - gamma^2) * s``.
  - ``g_T`` is the line's generic active direction, and ``gamma`` the expected generic share of an
    active response.
  - ``s`` pools the routes' specific directions with weights ``rho_r / (1 - rho_r^2)``.
  - ``rho`` is the certified expected specific cosine.
  - The prediction's expected centred cosine is ``sqrt(gamma^2 + rho^2 (1 - gamma^2))``.
- Refusals: ``NO_TRANSFER_ROUTE`` when nothing transfers, and ``SPECIFIC_DIRECTION_UNSUPPORTED``
  when ``rho < rho_min``. The prediction is then the generic direction alone.
- Interfaces: `TransferAtlas`, `Route`, `TransferCertificate`, `TransferPrediction`, `Certifier`,
  `fit_certifier`, `routes_for`, `predict`, `transfer_table`, `expected_cosine`.
- Depends on: numpy. scikit-learn is needed only by `fit_certifier`, and by `Certifier` objects it
  returns (the research extra).

Scope of the evidence: 2026-10-12 block Q, ``research/knowledge_transfer_20261012``.
* Frozen 2026-10-12T12:24:32Z and run once.
* Meta-models were fitted on GSE92742; the reference atlas was 979 GSE70138 compounds.
* Test set: 702 sealed GSE70138 compounds absent from GSE92742, 7 lines, 10 uM / 24 h landmark
  responses, and 1,105 active cells on 348 compounds.

With one profiled line (regime A1), the pooled prediction scored centred cosine 0.529:
* against the generic direction (0.287): +0.218 [+0.202, +0.235];
* against the best single route (context, 0.510): +0.033 [+0.015, +0.052];
* the certificate's expected cosine was 0.547;
* the certificate ranks errors better than applicability distance: AURC 0.347 against 0.428.

With no profiled line, the gain is small:
* 0.360 against 0.287 generic, and against 0.318 for a monolithic ridge on the same knowledge;
* 45% of queries refuse the specific direction.

With every line visible, pooling did not beat the context route alone. Outside L1000 landmark
responses at this dose and time, the certificates are uncalibrated.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

VALIDATED_SCOPE = "lincs_l1000_landmark_10uM_24h_unprofiled_compounds_gse70138_from_gse92742_metamodels"
ROUTES = ("context", "pheno", "chem", "know")
NO_TRANSFER_ROUTE = "NO_TRANSFER_ROUTE"
SPECIFIC_DIRECTION_UNSUPPORTED = "SPECIFIC_DIRECTION_UNSUPPORTED"
RIDGE_LAMBDAS = (1e1, 1e2, 1e3, 1e4, 1e5)
# (k, similarity exponent, similarity floor) of the analogue routes, fixed on GSE92742 development.
ANALOGUE_PARAMS = {"pheno": (10, 2.0, 0.0), "chem": (10, 2.0, 0.3), "know": (10, 1.0, 0.0)}


def unit_rows(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return np.where(n > 0, x / np.maximum(n, 1e-12), 0.0)


def centred_cosine(pred: np.ndarray, true: np.ndarray) -> np.ndarray:
    num = (pred * true).sum(-1)
    den = np.linalg.norm(pred, axis=-1) * np.linalg.norm(true, axis=-1)
    return np.where(den > 1e-9, num / np.maximum(den, 1e-12), 0.0)


def perp(x: np.ndarray, g: np.ndarray) -> np.ndarray:
    """Remove the component along the unit rows of ``g``."""
    return x - (x * g).sum(-1, keepdims=True) * g


def expected_cosine(gamma: float, rho: np.ndarray) -> np.ndarray:
    return np.sqrt(gamma ** 2 + np.asarray(rho) ** 2 * (1 - gamma ** 2))


@dataclass(frozen=True)
class RidgeMap:
    B: np.ndarray            # genes x genes map on centred responses
    lam: float
    loo_cosine: float        # mean leave-one-out centred cosine on the fitting compounds
    n: int


def fit_ridge_map(X: np.ndarray, Z: np.ndarray, lams=RIDGE_LAMBDAS) -> RidgeMap:
    """Multi-output ridge Z ~ X B with lambda chosen by leave-one-out mean centred cosine."""
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    UtZ = U.T @ Z
    best = None
    for lam in lams:
        d = S ** 2 / (S ** 2 + lam)
        hat = (U ** 2 * d).sum(1)
        loo = Z - (Z - U @ (d[:, None] * UtZ)) / np.maximum(1 - hat, 1e-6)[:, None]
        score = float(np.mean(centred_cosine(loo, Z)))
        if best is None or score > best[1]:
            best = (lam, score, d, hat)
    lam, score = best[0], best[1]
    B = Vt.T @ ((S / (S ** 2 + lam))[:, None] * UtZ)
    return RidgeMap(B.astype(np.float32), lam, score, len(X))


@dataclass
class TransferAtlas:
    """Reference responses and knowledge, the line-to-line maps and the generic directions.

    ``Y`` stacks references (``ref`` True) and queries; query rows are read only through an explicit
    visibility mask. ``thr`` is each line's activity threshold on the raw response norm.
    """
    Yc: np.ndarray           # compounds x lines x genes, centred by the reference line means; NaN if missing
    mu: np.ndarray           # lines x genes
    ref: np.ndarray          # compounds, boolean
    fps: np.ndarray          # compounds x bits, boolean fingerprints
    know: np.ndarray         # compounds x tokens, boolean knowledge tokens
    thr: np.ndarray          # lines
    maps: dict = field(default_factory=dict)
    G: np.ndarray | None = None
    gamma: float = 0.0

    @classmethod
    def build(cls, Y: np.ndarray, ref: np.ndarray, fps: np.ndarray, know: np.ndarray, thr: np.ndarray, *,
              min_shared: int = 50) -> "TransferAtlas":
        Y = np.asarray(Y, dtype=np.float32)
        ref = np.asarray(ref, bool)
        if Y.ndim != 3 or len(ref) != len(Y) or len(fps) != len(Y) or len(know) != len(Y) or len(thr) != Y.shape[1]:
            raise ValueError("AXIS_MISMATCH: Y, ref, fps, know and thr must share the compound and line axes")
        if not ref.any():
            raise ValueError("NO_REFERENCES")
        mu = np.nanmean(np.where(ref[:, None, None], Y, np.nan), axis=0)
        atlas = cls((Y - mu[None]).astype(np.float32), mu.astype(np.float32), ref, np.asarray(fps, bool),
                    np.asarray(know, bool), np.asarray(thr, float))
        have = np.isfinite(atlas.Yc[..., 0]) & ref[:, None]
        L = Y.shape[1]
        for s in range(L):
            for t in range(L):
                rows = have[:, s] & have[:, t]
                if s != t and rows.sum() >= min_shared:
                    atlas.maps[(s, t)] = fit_ridge_map(atlas.Yc[rows, s].astype(np.float64), atlas.Yc[rows, t].astype(np.float64))
        atlas.G, atlas.gamma = atlas._generic()
        return atlas

    def ref_rows(self, T: int) -> np.ndarray:
        return np.flatnonzero(self.ref & np.isfinite(self.Yc[:, T, 0]))

    def active_refs(self, T: int) -> np.ndarray:
        rows = self.ref_rows(T)
        return rows[np.linalg.norm(self.Yc[rows, T] + self.mu[T], axis=1) > self.thr[T]]

    def _generic(self) -> tuple[np.ndarray, float]:
        """Unit mean active reference response per line, and the leave-one-out generic share."""
        L, p = self.Yc.shape[1], self.Yc.shape[2]
        G = np.zeros((L, p))
        shares = []
        for T in range(L):
            a = self.active_refs(T)
            if len(a) >= 5:
                Ya = self.Yc[a, T].astype(np.float64)
                G[T] = Ya.mean(0)
                shares.append(centred_cosine(unit_rows(Ya.sum(0)[None] - Ya), Ya))
        return unit_rows(G), float(np.mean(np.concatenate(shares))) if shares else 0.0


@dataclass(frozen=True)
class Route:
    pred: np.ndarray          # queries x genes centred prediction (0 where unavailable)
    available: np.ndarray     # queries
    support: np.ndarray       # queries x features describing what the route had


def _knn(sim: np.ndarray, Yref: np.ndarray, k: int, gamma: float, floor: float) -> Route:
    s = np.where(np.isfinite(sim) & (sim > floor), sim, -np.inf)
    kk = min(k, s.shape[1])
    idx = np.argpartition(-s, kk - 1, axis=1)[:, :kk]
    top = np.take_along_axis(s, idx, 1)
    order = np.argsort(-top, axis=1)
    idx, top = np.take_along_axis(idx, order, 1), np.take_along_axis(top, order, 1)
    ok = np.isfinite(top)
    w = np.where(ok, np.clip(top, 0, None) ** gamma, 0.0)
    pred = np.einsum("qk,qkp->qp", w, Yref[idx]) / np.maximum(w.sum(1, keepdims=True), 1e-12)
    avail = ok.any(1)
    pred[~avail] = 0.0
    nn = ok.sum(1)
    agree = np.einsum("qkp,qp->qk", unit_rows(Yref[idx]), unit_rows(pred))
    support = np.stack([np.where(ok[:, 0], top[:, 0], 0.0), np.where(ok, top, 0.0).sum(1) / np.maximum(nn, 1), nn,
                        np.where(ok, agree, 0.0).sum(1) / np.maximum(nn, 1), np.linalg.norm(pred, axis=1)], 1)
    return Route(pred, avail, support)


def _jaccard(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = a.astype(np.float32), b.astype(np.float32)
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), np.nan)


def route_context(atlas: TransferAtlas, q: np.ndarray, T: int, visible: np.ndarray) -> Route:
    n, p = len(q), atlas.Yc.shape[2]
    num, wsum, nsrc, best = np.zeros((n, p)), np.zeros(n), np.zeros(n), np.zeros(n)
    for s in range(atlas.Yc.shape[1]):
        m = atlas.maps.get((s, T))
        if s == T or m is None:
            continue
        ok = visible[:, s] & np.isfinite(atlas.Yc[q, s, 0])
        if not ok.any():
            continue
        pred = atlas.Yc[q[ok], s].astype(np.float64) @ m.B
        w = max(m.loo_cosine, 0.0) ** 2
        num[ok] += w * pred
        wsum[ok] += w
        nsrc[ok] += 1
        best[ok] = np.maximum(best[ok], m.loo_cosine)
    avail = wsum > 0
    pred = np.where(avail[:, None], num / np.maximum(wsum, 1e-12)[:, None], 0.0)
    return Route(pred, avail, np.stack([nsrc, best, np.where(avail, np.linalg.norm(pred, axis=1), 0.0)], 1))


def route_pheno(atlas: TransferAtlas, q: np.ndarray, T: int, visible: np.ndarray) -> Route:
    R = atlas.ref_rows(T)
    acc, cnt = np.zeros((len(q), len(R))), np.zeros((len(q), len(R)))
    for s in range(atlas.Yc.shape[1]):
        if s == T:
            continue
        qa = visible[:, s] & np.isfinite(atlas.Yc[q, s, 0])
        rb = np.isfinite(atlas.Yc[R, s, 0])
        if not qa.any() or not rb.any():
            continue
        c = unit_rows(np.nan_to_num(atlas.Yc[q, s])) @ unit_rows(np.nan_to_num(atlas.Yc[R, s])).T
        m = qa[:, None] & rb[None]
        acc += np.where(m, c, 0.0)
        cnt += m
    sim = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    sim[np.equal.outer(q, R)] = np.nan
    return _knn(sim, atlas.Yc[R, T], *ANALOGUE_PARAMS["pheno"])


def route_static(atlas: TransferAtlas, q: np.ndarray, T: int, kind: str) -> Route:
    """``chem`` (fingerprints) or ``know`` (knowledge tokens): independent of what is visible."""
    R = atlas.ref_rows(T)
    bits = atlas.fps if kind == "chem" else atlas.know
    sim = _jaccard(bits[q], bits[R])
    sim[np.equal.outer(q, R)] = np.nan
    return _knn(sim, atlas.Yc[R, T], *ANALOGUE_PARAMS[kind])


def own_activity(atlas: TransferAtlas, q: np.ndarray, T: int, visible: np.ndarray) -> np.ndarray:
    """Activity in the query's visible other lines: count active, max and mean norm/threshold."""
    norms = np.linalg.norm(np.nan_to_num(atlas.Yc[q] + atlas.mu[None]), axis=2) / atlas.thr[None]
    have = np.isfinite(atlas.Yc[q, :, 0]) & visible
    have[:, T] = False
    out = np.zeros((len(q), 3))
    n = have.sum(1)
    out[:, 0] = np.where(have, norms > 1, False).sum(1)
    out[:, 1] = np.where(n > 0, np.where(have, norms, -np.inf).max(1), 0.0)
    out[:, 2] = np.where(n > 0, np.where(have, norms, 0.0).sum(1) / np.maximum(n, 1), 0.0)
    return out


def routes_for(atlas: TransferAtlas, q: np.ndarray, T: int, visible: np.ndarray, static: dict | None = None) -> dict:
    q = np.asarray(q)
    routes = {"context": route_context(atlas, q, T, visible), "pheno": route_pheno(atlas, q, T, visible)}
    routes.update(static or {k: route_static(atlas, q, T, k) for k in ("chem", "know")})
    return routes


def features(routes: dict, activity: np.ndarray) -> np.ndarray:
    cols = []
    for r in ROUTES:
        o = routes[r]
        cols += [o.available.astype(float)[:, None], np.where(o.available[:, None], o.support, 0.0)]
    return np.concatenate(cols + [activity], 1)


@dataclass(frozen=True)
class TransferCertificate:
    p_active: np.ndarray        # P(the response exceeds the line's activity threshold)
    rho: np.ndarray             # expected specific cosine of the pooled direction (0 when refused)
    rho_route: dict             # per-route expected specific cosine
    expected_cosine: np.ndarray # expected centred cosine of the prediction if active
    refusal: np.ndarray         # "" or a refusal code per query


@dataclass(frozen=True)
class TransferPrediction:
    direction: np.ndarray       # queries x genes unit centred prediction
    specific: np.ndarray        # queries x genes pooled specific direction (orthogonal to g_T)
    certificate: TransferCertificate


class Certifier:
    """Meta-models for activity, per-route specific accuracy and pooled specific accuracy."""

    def __init__(self, act_model, route_models: dict, pool_model, rho_min: float = 0.10):
        self.act_model, self.route_models, self.pool_model, self.rho_min = act_model, route_models, pool_model, rho_min

    def route_rho(self, F: np.ndarray, av: dict) -> dict:
        return {r: np.where(av[r], np.clip(m.predict(F), -0.2, 0.95) if (m := self.route_models.get(r)) is not None else 0.0, 0.0)
                for r in ROUTES}

    @staticmethod
    def pooled_features(rho_r: dict, agree: np.ndarray, av: dict) -> np.ndarray:
        R = np.stack([rho_r[r] for r in ROUTES], 1)
        top = -np.sort(-R, axis=1)[:, :2]
        n_av = np.stack([av[r] for r in ROUTES], 1).sum(1)
        return np.concatenate([R, top, agree[:, None], n_av[:, None]], 1)

    def combine(self, preds: dict, G: np.ndarray, F: np.ndarray, av: dict):
        rho_r = self.route_rho(F, av)
        w = {r: np.where(av[r], np.clip(rho_r[r], 0, 0.95) / (1 - np.clip(rho_r[r], 0, 0.95) ** 2), 0.0) for r in ROUTES}
        S = {r: unit_rows(perp(preds[r], G)) for r in ROUTES}
        s = unit_rows(sum(w[r][:, None] * S[r] for r in ROUTES))
        W = np.stack([w[r] for r in ROUTES], 1)
        order = np.argsort(-W, axis=1)
        Sx = np.stack([S[r] for r in ROUTES], 1)
        first = np.take_along_axis(Sx, order[:, :1, None], 1)[:, 0]
        second = np.take_along_axis(Sx, order[:, 1:2, None], 1)[:, 0]
        agree = np.where(np.take_along_axis(W, order[:, 1:2], 1)[:, 0] > 0, (first * second).sum(1), 0.0)
        return s, rho_r, agree

    def certify(self, preds: dict, G: np.ndarray, F: np.ndarray, av: dict, gamma: float):
        s, rho_r, agree = self.combine(preds, G, F, av)
        any_route = np.stack([av[r] for r in ROUTES], 1).any(1)
        rho = np.where(any_route, np.clip(self.pool_model.predict(self.pooled_features(rho_r, agree, av)), 0, 0.95), 0.0)
        refusal = np.where(~any_route, NO_TRANSFER_ROUTE, np.where(rho < self.rho_min, SPECIFIC_DIRECTION_UNSUPPORTED, ""))
        used = np.where(refusal == "", rho, 0.0)
        cert = TransferCertificate(self.act_model.predict_proba(F)[:, 1], used, rho_r, expected_cosine(gamma, used), refusal)
        return s, cert


def predict(atlas: TransferAtlas, certifier: Certifier, q: np.ndarray, T: int, visible: np.ndarray,
            static: dict | None = None) -> TransferPrediction:
    """Certified unit predictions for queries ``q`` in line ``T`` given which of their lines are visible."""
    q = np.asarray(q)
    visible = np.asarray(visible, bool)
    if visible.shape != (len(q), atlas.Yc.shape[1]):
        raise ValueError("AXIS_MISMATCH: visible must be queries x lines")
    routes = routes_for(atlas, q, T, visible, static)
    F = features(routes, own_activity(atlas, q, T, visible))
    Gq = np.repeat(atlas.G[T][None], len(q), 0)
    s, cert = certifier.certify({r: routes[r].pred for r in ROUTES}, Gq, F, {r: routes[r].available for r in ROUTES},
                                atlas.gamma)
    g = atlas.gamma
    direction = unit_rows(g * Gq + (cert.rho * np.sqrt(max(1 - g * g, 0.0)))[:, None] * s)
    return TransferPrediction(direction, s, cert)


def transfer_table(atlas: TransferAtlas) -> np.ndarray:
    """kappa[s, t]: leave-one-out specific cosine of single-line context transfer s -> t on active references."""
    L = atlas.Yc.shape[1]
    kappa = np.zeros((L, L))
    have = np.isfinite(atlas.Yc[..., 0]) & atlas.ref[:, None]
    for (s, t), m in atlas.maps.items():
        rows = have[:, s] & have[:, t]
        X, Z = atlas.Yc[rows, s].astype(np.float64), atlas.Yc[rows, t].astype(np.float64)
        U, S, _ = np.linalg.svd(X, full_matrices=False)
        d = S ** 2 / (S ** 2 + m.lam)
        loo = Z - (Z - U @ (d[:, None] * (U.T @ Z))) / np.maximum(1 - (U ** 2 * d).sum(1), 1e-6)[:, None]
        act = np.linalg.norm(Z + atlas.mu[t], axis=1) > atlas.thr[t]
        if act.sum() >= 5:
            Gt = np.repeat(atlas.G[t][None], int(act.sum()), 0)
            kappa[s, t] = float(np.mean(centred_cosine(perp(loo[act], Gt), perp(Z[act], Gt))))
    return kappa


def fit_certifier(F: np.ndarray, av: dict, preds: dict, G: np.ndarray, truth: np.ndarray, active: np.ndarray,
                  groups: np.ndarray, *, rho_min: float = 0.10, seed: int = 0) -> Certifier:
    """Fit the meta-models on development queries; the pooled model learns from out-of-group pooling.

    ``groups`` partitions the queries (by compound) so a query's pooled-direction accuracy comes from
    route models that did not see its group. Needs scikit-learn.
    """
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

    kw = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, random_state=seed)
    tperp = perp(truth, G)
    spec = {r: np.where(av[r], centred_cosine(perp(preds[r], G), tperp), np.nan) for r in ROUTES}

    def route_models(rows):
        out = {}
        for r in ROUTES:
            m = rows & av[r] & active & np.isfinite(spec[r])
            out[r] = HistGradientBoostingRegressor(**kw).fit(F[m], spec[r][m]) if m.sum() > 100 else None
        return out

    n = len(truth)
    P_in, agree_in = np.full(n, np.nan), np.zeros(n)
    rho_in = {r: np.zeros(n) for r in ROUTES}
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        inner = Certifier(None, route_models(tr), None, rho_min)
        s, rr, ag = inner.combine({r: v[te] for r, v in preds.items()}, G[te], F[te], {r: v[te] for r, v in av.items()})
        P_in[te], agree_in[te] = centred_cosine(s, tperp[te]), ag
        for r in ROUTES:
            rho_in[r][te] = rr[r]
    every = np.ones(n, bool)
    act_model = HistGradientBoostingClassifier(**kw).fit(F, active)
    feats = Certifier.pooled_features(rho_in, agree_in, av)
    m = active & np.isfinite(P_in)
    pool_model = HistGradientBoostingRegressor(**kw).fit(feats[m], P_in[m])
    return Certifier(act_model, route_models(every), pool_model, rho_min)
