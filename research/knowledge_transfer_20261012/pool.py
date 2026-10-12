"""Decomposed pooling and transfer certificates for RKT (block Q research implementation).

A centred response is split into three parts, each predicted separately:
* activity: P(the response in T exceeds the vehicle noise quantile);
* generic direction ``g_T``: the mean centred response of active references in T, shared by most
  active compounds (the systematic component Systema warns about);
* specific direction: the part orthogonal to ``g_T``, pooled over routes.

Each route's expected *specific* cosine (rho_r) is predicted from its support features by a
meta-model fitted on development queries. Routes are pooled with weights rho/(1 - rho^2), the
optimal weight for independent noisy estimates of one direction, and a second meta-model gives the
pooled expectation rho. With gamma the expected generic share of an active response, the
prediction that maximises expected centred cosine is ``gamma * g + rho * sqrt(1 - gamma^2) * s``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

import rkt

SPECIFIC_ROUTES = ("context", "pheno", "chem", "know")


def perp(X: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Remove the component along the unit rows of G."""
    return X - (X * G).sum(-1, keepdims=True) * G


def route_features(sup: dict, av: dict, pred_norm: dict, line: np.ndarray, n_lines: int,
                   own_activity: np.ndarray) -> np.ndarray:
    """Support features shared by the meta-models (unavailable routes contribute zeros)."""
    cols = []
    for r in SPECIFIC_ROUTES:
        cols.append(av[r].astype(float)[:, None])
        cols.append(np.where(av[r][:, None], sup[r], 0.0))
    cols.append(np.eye(n_lines)[line])
    cols.append(own_activity)
    return np.concatenate(cols, 1)


@dataclass
class Certificate:
    p_active: np.ndarray        # P(active in T)
    rho: np.ndarray             # expected specific cosine of the pooled specific direction (actives)
    rho_route: dict             # per-route expected specific cosine
    weights: dict               # per-route pooling weights
    agreement: np.ndarray       # cosine between the two highest-weighted routes' specific directions
    refusal: np.ndarray         # reason code per query ("" if none)


class Pooler:
    """Meta-models for activity, per-route specific accuracy and pooled specific accuracy."""

    def __init__(self, gamma: float, rho_min: float = 0.10, seed: int = 0):
        self.gamma = gamma
        self.rho_min = rho_min
        self.seed = seed

    def _hgb(self, cls=False):
        kw = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, random_state=self.seed)
        return HistGradientBoostingClassifier(**kw) if cls else HistGradientBoostingRegressor(**kw)

    def fit(self, F, av, spec_cos, active, pooled_inputs):
        """F: features; av/spec_cos: per-route availability and realised specific cosine (actives)."""
        self.act_model = self._hgb(cls=True).fit(F, active)
        self.route_models = {}
        for r in SPECIFIC_ROUTES:
            m = av[r] & active & np.isfinite(spec_cos[r])
            self.route_models[r] = self._hgb().fit(F[m], spec_cos[r][m]) if m.sum() > 100 else None
        P, agree, rho_r = pooled_inputs
        feats = self._pooled_features(rho_r, agree, av)
        m = active & np.isfinite(P)
        self.pool_model = self._hgb().fit(feats[m], P[m])
        return self

    def route_rho(self, F, av):
        out = {}
        for r in SPECIFIC_ROUTES:
            model = self.route_models.get(r)
            out[r] = np.where(av[r], np.clip(model.predict(F), -0.2, 0.95) if model is not None else 0.0, 0.0)
        return out

    @staticmethod
    def weights(rho_r, av):
        return {r: np.where(av[r], np.clip(rho_r[r], 0, 0.95) / (1 - np.clip(rho_r[r], 0, 0.95) ** 2), 0.0)
                for r in SPECIFIC_ROUTES}

    @staticmethod
    def _pooled_features(rho_r, agree, av):
        R = np.stack([rho_r[r] for r in SPECIFIC_ROUTES], 1)
        srt = -np.sort(-R, axis=1)
        n_av = np.stack([av[r] for r in SPECIFIC_ROUTES], 1).sum(1)
        return np.concatenate([R, srt[:, :2], agree[:, None], n_av[:, None]], 1)

    def combine(self, preds: dict, G: np.ndarray, F, av):
        """Pooled specific direction (unit, orthogonal to G) and per-route expectations."""
        rho_r = self.route_rho(F, av)
        w = self.weights(rho_r, av)
        S = {r: rkt.unit_rows(perp(preds[r], G)) for r in SPECIFIC_ROUTES}
        num = sum(w[r][:, None] * S[r] for r in SPECIFIC_ROUTES)
        s = rkt.unit_rows(num)
        W = np.stack([w[r] for r in SPECIFIC_ROUTES], 1)
        order = np.argsort(-W, axis=1)
        names = np.array(SPECIFIC_ROUTES)
        agree = np.zeros(len(G))
        for i in range(len(G)):
            a, b = names[order[i, 0]], names[order[i, 1]]
            if W[i, order[i, 1]] > 0:
                agree[i] = float(S[a][i] @ S[b][i])
        return s, rho_r, w, agree

    def certify(self, preds, G, F, av, *, predict_pooled: bool = True):
        s, rho_r, w, agree = self.combine(preds, G, F, av)
        p_act = self.act_model.predict_proba(F)[:, 1]
        any_route = np.stack([av[r] for r in SPECIFIC_ROUTES], 1).any(1)
        rho = np.where(any_route, np.clip(self.pool_model.predict(self._pooled_features(rho_r, agree, av)), 0, 0.95), 0.0)
        refusal = np.where(~any_route, "NO_TRANSFER_ROUTE",
                           np.where(rho < self.rho_min, "SPECIFIC_DIRECTION_UNSUPPORTED", ""))
        return s, Certificate(p_act, rho, rho_r, w, agree, refusal)

    def predict(self, s, cert: Certificate, G, magnitude: np.ndarray):
        """Centred prediction: generic plus specific direction in the ratio that maximises expected cosine."""
        g = self.gamma
        rho = np.where(cert.refusal == "", cert.rho, 0.0)
        direction = rkt.unit_rows(g * G + (rho * np.sqrt(max(1 - g * g, 0.0)))[:, None] * s)
        return magnitude[:, None] * direction


def fit_nested(F, av, preds, G, truth, active, groups, gamma, *, rho_min=0.10, seed=0):
    """Fit a Pooler whose pooled meta-model is trained on inner out-of-group pooled directions.

    ``groups`` partitions the training queries (by compound fold) so a query's pooled-direction
    accuracy is computed from route meta-models that did not see that query's group.
    """
    tperp = perp(truth, G)
    spec = {r: np.where(av[r], rkt.centred_cosine(perp(preds[r], G), tperp), np.nan) for r in SPECIFIC_ROUTES}
    n = len(truth)
    P_in = np.full(n, np.nan); agree_in = np.zeros(n); rho_in = {r: np.zeros(n) for r in SPECIFIC_ROUTES}
    dummy = lambda k: (np.zeros(k), np.zeros(k), {r: np.zeros(k) for r in SPECIFIC_ROUTES})
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        pm = Pooler(gamma, rho_min, seed).fit(F[tr], {r: v[tr] for r, v in av.items()},
                                              {r: v[tr] for r, v in spec.items()}, active[tr], dummy(int(tr.sum())))
        s, rr, w, ag = pm.combine({r: v[te] for r, v in preds.items()}, G[te], F[te], {r: v[te] for r, v in av.items()})
        P_in[te] = rkt.centred_cosine(s, tperp[te]); agree_in[te] = ag
        for r in SPECIFIC_ROUTES:
            rho_in[r][te] = rr[r]
    return Pooler(gamma, rho_min, seed).fit(F, av, spec, active, (P_in, agree_in, rho_in))
