"""Fitted binary response factors; diagnostic probe order is metadata only.

A gate is a hidden binary state of a new background that shifts the residual of every pair in its scope classes by a signed, pair-specific amount.
State posteriors are updated in r1_core.Belief. This is not a branching research
procedure. Lineage IDs persist during adaptation; identity fingerprints the
current executable definition, including numerical effects and prior.
Unknown stays unknown: a gate whose scope has not been probed contributes its prior, never a zero state.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from itertools import product

import numpy as np


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=lambda a: np.round(np.asarray(a), 6).tolist()).encode()).hexdigest()[:12]


@dataclass
class Gate:
    gid: str
    b: np.ndarray                       # [n_cls] signed class-level loading, canonical orientation
    beta: np.ndarray = None             # [n] pair-level effect of the gate being on
    pi: float = 0.5
    scope: tuple = ()                   # classes with |b| above threshold (derived from b)
    probe_order: tuple = ()
    gen: int = 0
    parents: tuple = ()
    evidence_cells: tuple = ()
    fit_version: str = ""
    sep: float = 0.0
    states: tuple = ()

    def identity(self) -> str:
        obj = {"scope": sorted(self.scope), "b": self.b.tolist(),
               "beta": None if self.beta is None else self.beta.tolist(),
               "pi": float(self.pi), "probe_order": list(self.probe_order)}
        return hashlib.sha256(json.dumps(obj, sort_keys=True, allow_nan=False).encode()).hexdigest()


def scope_of(b: np.ndarray, rel: float = 0.4) -> tuple:
    m = np.abs(b).max()
    return tuple(int(c) for c in np.nonzero(np.abs(b) >= rel * m)[0]) if m > 0 else ()


def canonical(b: np.ndarray, s: np.ndarray):
    """Flip so the largest-magnitude loading is positive: state 1 means that class is raised."""
    j = int(np.argmax(np.abs(b)))
    if b[j] < 0:
        return -b, 1 - s
    return b, s


def infer_states(cmc: np.ndarray, B: np.ndarray, sbar: np.ndarray):
    """Best binary state combination per history cell (exhaustive over 2^G)."""
    G = B.shape[1]
    S_all = np.array(list(product([0, 1], repeat=G)), float)                    # [2^G, G]
    pred = (S_all - sbar) @ B.T                                                 # [2^G, C]
    d = ((cmc.T[:, None, :] - pred[None]) ** 2).sum(2)                          # [h, 2^G]
    return S_all[np.argmin(d, 1)], d.min(1).sum()


def binary_factors(cmc: np.ndarray, G: int, rng, restarts: int = 12, iters: int = 12, ridge: float = 1e-3):
    C, h = cmc.shape
    best = (np.inf, None, None)
    for _ in range(restarts):
        S = (rng.random((h, G)) < 0.5).astype(float)
        for g in range(G):
            if S[:, g].sum() in (0, h):
                S[rng.integers(h), g] = 1 - S[0, g]
        for _it in range(iters):
            sbar = S.mean(0)
            X = S - sbar
            B = np.linalg.solve(X.T @ X + ridge * np.eye(G), X.T @ cmc.T).T       # [C, G]
            S_new, sse = infer_states(cmc, B, sbar)
            if (S_new == S).all():
                break
            S = S_new
        sbar = S.mean(0)
        X = S - sbar
        B = np.linalg.solve(X.T @ X + ridge * np.eye(G), X.T @ cmc.T).T
        sse = ((cmc - B @ X.T) ** 2).sum()
        if sse < best[0]:
            best = (sse, B, S)
    return best


def separation(cm_row_scores: np.ndarray, s: np.ndarray) -> float:
    on, off = cm_row_scores[s == 1], cm_row_scores[s == 0]
    if len(on) < 2 or len(off) < 2:
        return 0.0
    sd = np.sqrt((on.var() * len(on) + off.var() * len(off)) / len(s)) + 1e-9
    return float(abs(on.mean() - off.mean()) / sd)


def pair_betas(E: np.ndarray, pc: np.ndarray, S: np.ndarray, B: np.ndarray, scopes: list, kappa: float = 2.0):
    """Pair-level effects per gate: ridge regression of each pair's residuals on the gate states, shrunk to the class-level loading, restricted to scope."""
    n, h = E.shape
    G = S.shape[1]
    sbar = S.mean(0)
    X = S - sbar
    beta = np.zeros((G, n))
    for p in range(n):
        gs = [g for g in range(G) if pc[p] in scopes[g]]
        if not gs:
            continue
        Xg = X[:, gs]
        prior = np.array([B[pc[p], g] for g in gs])
        coef = np.linalg.solve(Xg.T @ Xg + kappa * np.eye(len(gs)), Xg.T @ E[p] + kappa * prior)
        beta[gs, p] = coef
    return beta


def build_gates(M, E, B, S, gen: int, prefix: str, scope_rel: float = 0.4, min_sep: float = 2.0, min_load: float = 0.02):
    """From class loadings B and states S -> list of Gate (canonical orientation); gates with weak loading or weak separation are dropped."""
    from r1_core import class_matrix   # local import to avoid a cycle
    cm = class_matrix(M, E)
    gates, keep = [], []
    scopes = [scope_of(B[:, g], scope_rel) for g in range(B.shape[1])]
    beta_all = pair_betas(E, M.pc, S, B, scopes)
    for g in range(B.shape[1]):
        b, s = canonical(B[:, g].copy(), S[:, g].copy())
        flip = -1.0 if not np.allclose(b, B[:, g]) else 1.0
        sc = scope_of(b, scope_rel)
        if np.abs(b).max() < min_load or len(sc) == 0:
            continue
        w = np.zeros(len(b))
        w[list(sc)] = b[list(sc)]
        score = w @ (cm - cm.mean(1, keepdims=True))
        sep = separation(score, s)
        if sep < min_sep or s.sum() < 2 or (1 - s).sum() < 2:
            continue
        beta = flip * beta_all[g]
        order = tuple(int(q) for q in np.argsort(-np.abs(beta) / M.sigma) if np.abs(beta[q]) > 0)
        gt = Gate(f"{prefix}{gen}_", b, beta, float(s.mean()), sc, order, gen, (), tuple(M.cells), M.version, sep, tuple(int(x) for x in s))
        gt.gid = f"{prefix}{gen}_{gt.identity()}"
        gates.append(gt)
        keep.append(g)
    return gates


def discover_gates(M, E=None, gen: int = 0, prefix: str = "g", rng=None, Gmax: int = 4, restarts: int = 12, min_gain: float = 0.12, min_sep: float = 2.0, existing=()):
    """Bounded discovery of gate sets on (the residual of) a released history; `existing` gates are held fixed and explain what they can first."""
    from r1_core import class_matrix
    rng = np.random.default_rng(0) if rng is None else rng
    E = M.E if E is None else E
    cm = class_matrix(M, E)
    cmc = cm - cm.mean(1, keepdims=True)
    total = (cmc ** 2).sum() + 1e-12
    if existing:
        B0 = np.stack([g.b for g in existing], 1)
        S0, _ = infer_states(cmc, B0, np.array([g.pi for g in existing]))
        cmc = cmc - B0 @ (S0 - S0.mean(0)).T
    found = []
    prev = (cmc ** 2).sum()
    for G in range(1, Gmax + 1):
        sse, B, S = binary_factors(cmc, G, rng, restarts=restarts)
        if B is None or (prev - sse) / total < min_gain * (1 if G == 1 else 0.6):
            break
        found = (B, S)
        prev = sse
    if not found:
        return []
    B, S = found
    gates = build_gates(M, E, B, S, gen, prefix, min_sep=min_sep)
    return gates


def refit_gates(M, gates: list, E=None, adapt: float = 0.5):
    """Executable reuse on a new history: hold the inherited gate profiles (adapting them inside their declared scope), re-infer the states and refit
    pair effects. Returns (fitted gates, states [h,G]) or (None, None) if an inherited gate is not supported by this history."""
    from r1_core import class_matrix
    E = M.E if E is None else E
    cm = class_matrix(M, E)
    cmc = cm - cm.mean(1, keepdims=True)
    B = np.stack([g.b for g in gates], 1)
    sbar = np.array([g.pi for g in gates])
    S = None
    for _ in range(4):
        S, _ = infer_states(cmc, B, sbar)
        sbar = S.mean(0)
        X = S - sbar
        B_ls = np.linalg.solve(X.T @ X + 1e-3 * np.eye(B.shape[1]), X.T @ cmc.T).T
        mask = np.zeros_like(B, bool)
        for k, g in enumerate(gates):
            mask[list(g.scope), k] = True
        B = np.where(mask, (1 - adapt) * np.stack([g.b for g in gates], 1) + adapt * B_ls, np.stack([g.b for g in gates], 1))
    out = []
    scopes = [g.scope for g in gates]
    beta = pair_betas(E, M.pc, S, B, scopes)
    for k, g in enumerate(gates):
        s = S[:, k]
        if s.sum() < 2 or (1 - s).sum() < 2:
            return None, None
        w = np.zeros(B.shape[0])
        w[list(g.scope)] = B[list(g.scope), k]
        sep = separation(w @ cmc, s)
        if sep < 1.5:
            return None, None
        order = tuple(int(q) for q in np.argsort(-np.abs(beta[k]) / M.sigma) if np.abs(beta[k][q]) > 0)
        out.append(Gate(g.gid, B[:, k].copy(), beta[k], float(s.mean()), g.scope, order, g.gen, g.parents, tuple(M.cells), M.version, sep, tuple(int(x) for x in s)))
    return out, S
