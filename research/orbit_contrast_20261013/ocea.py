"""OCEA estimator: orbit decomposition, falsification-calibrated admission, stacking, arms and statistics.

File summary
- Path: research/orbit_contrast_20261013/ocea.py
- Purpose: turn per-setting route outputs into the arms of PROTOCOL.md section 5 and score them.
- Core points:
  - `compress` keeps, per query, only inner products among the base arrays (generic, chem, f_r,
    g-bar_r) and with the truth, so every arm's least-squares fit and cosine is exact without holding
    vectors in memory.
  - Gates: ridge on standardised label-free descriptors; alpha by leave-one-inner-fold-out from
    {0.1, 1, 10, 100}; out-of-fold gate values for training queries, a model on all inner folds for
    test queries. Identity gate target: c_r = cos(f, y) - mean_m cos(f_m, y). Accuracy gate target:
    cos(f, y).
  - Stacker: vector least squares on the unit truth with penalty 1e-6, pooled over lines.
- Interfaces: `Compressed`, `compress`, `ARMS`, `fit_predict`, `entity_means`, `paired`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ALPHAS = (0.1, 1.0, 10.0, 100.0)
PENALTY = 1e-6
BOOT, FLIPS, SEED = 2000, 10000, 20261013


@dataclass
class Compressed:
    names: list            # base array names
    D: np.ndarray          # nq x nb x nb inner products
    Dy: np.ndarray         # nq x nb inner products with the truth
    ynorm: np.ndarray      # nq
    avail: dict            # route -> nq bool
    desc: dict             # route -> nq x d route-specific descriptors
    spread: dict           # route -> nq
    cos_f: dict            # route -> nq  cos(f, y)
    cos_orbit: dict        # route -> nq  mean_m cos(f_m, y)
    line: np.ndarray       # nq
    entity: np.ndarray     # nq
    fold: np.ndarray       # nq (inner fold, or -1 for test)

    def subset(self, m: np.ndarray) -> "Compressed":
        return Compressed(self.names, self.D[m], self.Dy[m], self.ynorm[m], {k: v[m] for k, v in self.avail.items()},
                          {k: v[m] for k, v in self.desc.items()}, {k: v[m] for k, v in self.spread.items()},
                          {k: v[m] for k, v in self.cos_f.items()}, {k: v[m] for k, v in self.cos_orbit.items()},
                          self.line[m], self.entity[m], self.fold[m])


def concat(parts: list) -> Compressed:
    c0 = parts[0]
    cat = lambda xs: np.concatenate(xs, 0)
    return Compressed(c0.names, cat([p.D for p in parts]), cat([p.Dy for p in parts]), cat([p.ynorm for p in parts]),
                      {k: cat([p.avail[k] for p in parts]) for k in c0.avail}, {k: cat([p.desc[k] for p in parts]) for k in c0.desc},
                      {k: cat([p.spread[k] for p in parts]) for k in c0.spread}, {k: cat([p.cos_f[k] for p in parts]) for k in c0.cos_f},
                      {k: cat([p.cos_orbit[k] for p in parts]) for k in c0.cos_orbit}, cat([p.line for p in parts]),
                      cat([p.entity for p in parts]), cat([p.fold for p in parts]))


def compress(res: dict, gen: np.ndarray, y: np.ndarray, base_routes: tuple, orbit_routes: tuple, line, entity, fold) -> Compressed:
    arrays, names = [gen], ["generic"]
    for r in base_routes:
        arrays.append(res[r].f); names.append(f"f:{r}")
    for r in orbit_routes:
        arrays.append(res[r].f); names.append(f"f:{r}")
        arrays.append(res[r].gbar); names.append(f"g:{r}")
    A = np.stack(arrays, 1)                                  # nq x nb x p
    D = np.einsum("qip,qjp->qij", A, A)
    Dy = np.einsum("qip,qp->qi", A, y)
    routes = tuple(base_routes) + tuple(orbit_routes)
    return Compressed(names, D, Dy, np.linalg.norm(y, axis=1), {r: res[r].avail.copy() for r in routes},
                      {r: res[r].desc.copy() for r in routes}, {r: res[r].spread.copy() for r in routes},
                      {r: (res[r].cos_f.copy() if res[r].cos_f is not None else np.zeros(len(y))) for r in routes},
                      {r: (res[r].cos_orbit.copy() if res[r].cos_orbit is not None else np.zeros(len(y))) for r in routes},
                      np.asarray(line), np.asarray(entity), np.full(len(y), fold) if np.isscalar(fold) else np.asarray(fold))


# ----------------------------------------------------------------------------------------- gates

def route_rms(c: Compressed, r: str) -> float:
    i = c.names.index(f"f:{r}")
    a = c.avail[r]
    return float(np.sqrt(np.mean(c.D[a, i, i]))) if a.any() else 1.0


def gate_features(c: Compressed, r: str, rms: float, n_lines: int) -> np.ndarray:
    i, j = c.names.index(f"f:{r}"), c.names.index(f"g:{r}")
    ff, gg, fg = c.D[:, i, i], c.D[:, j, j], c.D[:, i, j]
    dd = np.maximum(ff - 2 * fg + gg, 0.0)
    nf, ng, nd = np.sqrt(ff) / rms, np.sqrt(np.maximum(gg, 0)) / rms, np.sqrt(dd) / rms
    sp = c.spread[r] / rms
    sep = np.where(sp > 1e-9, nd / np.maximum(sp, 1e-9), 0.0)
    cfg = np.where(ff * gg > 1e-18, fg / np.sqrt(np.maximum(ff * gg, 1e-18)), 0.0)
    onehot = np.eye(n_lines)[c.line]
    return np.column_stack([c.desc[r], nf, ng, nd, sp, sep, cfg, onehot])


class Ridge:
    def __init__(self, alpha: float):
        self.alpha = alpha

    def fit(self, X, y):
        self.mu, self.sd = X.mean(0), X.std(0)
        self.sd[self.sd < 1e-9] = 1.0
        Z = (X - self.mu) / self.sd
        self.b0 = y.mean()
        self.w = np.linalg.solve(Z.T @ Z + self.alpha * np.eye(Z.shape[1]), Z.T @ (y - self.b0))
        return self

    def predict(self, X):
        return self.b0 + ((X - self.mu) / self.sd) @ self.w


def choose_alpha(X, y, groups) -> float:
    best, best_err = ALPHAS[0], np.inf
    ug = np.unique(groups)
    if len(ug) < 2:
        return 10.0
    for a in ALPHAS:
        err = 0.0
        for g in ug:
            tr, te = groups != g, groups == g
            if tr.sum() < 5 or te.sum() == 0:
                continue
            err += ((Ridge(a).fit(X[tr], y[tr]).predict(X[te]) - y[te]) ** 2).sum()
        if err < best_err:
            best, best_err = a, err
    return best


def gates(train: Compressed, test: Compressed, r: str, target: str, n_lines: int):
    """Out-of-fold gate values for training queries and model gate values for test queries (0 where unavailable)."""
    rms = route_rms(train, r)
    Xtr, Xte = gate_features(train, r, rms, n_lines), gate_features(test, r, rms, n_lines)
    ytr = (train.cos_f[r] - train.cos_orbit[r]) if target == "identity" else train.cos_f[r]
    a_tr, a_te = train.avail[r], test.avail[r]
    oof, out = np.zeros(len(ytr)), np.zeros(len(Xte))
    if a_tr.sum() < 20:
        return oof, out, {"alpha": None, "n_train": int(a_tr.sum())}
    alpha = choose_alpha(Xtr[a_tr], ytr[a_tr], train.fold[a_tr])
    for g in np.unique(train.fold[a_tr]):
        tr = a_tr & (train.fold != g)
        te = a_tr & (train.fold == g)
        if tr.sum() >= 5:
            oof[te] = Ridge(alpha).fit(Xtr[tr], ytr[tr]).predict(Xtr[te])
    model = Ridge(alpha).fit(Xtr[a_tr], ytr[a_tr])
    out[a_te] = model.predict(Xte[a_te])
    return oof, out, {"alpha": alpha, "n_train": int(a_tr.sum())}


# ----------------------------------------------------------------------------------------- arms

def arm_components(names: list, base_routes: tuple, orbit_routes: tuple, arm: str, drop: str | None = None):
    """[(coefficient vector over base arrays, gate key or None)] for one arm."""
    nb = len(names)
    e = lambda n: np.eye(nb)[names.index(n)]
    base = [(e("generic"), None)] + [(e(f"f:{r}"), None) for r in base_routes]
    orbit = [(e(f"g:{r}"), None) for r in orbit_routes]
    delta = lambda r: e(f"f:{r}") - e(f"g:{r}")
    if arm == "B0":
        return base
    if arm == "O":
        return base + orbit
    if arm == "N":
        return base + [(e(f"f:{r}"), None) for r in orbit_routes]
    if arm == "C":
        return base + [(e(f"f:{r}"), ("acc", r)) for r in orbit_routes]
    if arm == "R":
        return base + orbit + [(delta(r), None) for r in orbit_routes]
    if arm == "Cp":
        return base + orbit + [(delta(r), ("acc", r)) for r in orbit_routes]
    if arm == "F":
        return base + orbit + [(delta(r), ("id", r)) for r in orbit_routes if r != drop]
    raise ValueError(arm)


ARMS = ("B0", "O", "N", "C", "R", "Cp", "F")


def _gate_vals(comps, gate_tab, n):
    G = np.ones((n, len(comps)))
    for k, (_, gk) in enumerate(comps):
        if gk is not None:
            G[:, k] = np.maximum(gate_tab[gk], 0.0)
    return G


def stack_and_score(train: Compressed, test: Compressed, comps, gtr: dict, gte: dict):
    C = np.stack([c for c, _ in comps], 0)                      # J x nb
    Gt = _gate_vals(comps, gtr, len(train.ynorm))              # nq x J
    ok = train.ynorm > 1e-9
    Mq = np.einsum("ja,qab,kb->qjk", C, train.D[ok], C)         # per-query component Gram
    gram = np.einsum("qj,qk,qjk->jk", Gt[ok], Gt[ok], Mq)
    b = np.einsum("qj,ja,qa->j", Gt[ok], C, train.Dy[ok] / train.ynorm[ok][:, None])
    beta = np.linalg.solve(gram + PENALTY * np.eye(len(b)) * max(np.trace(gram) / len(b), 1e-12), b)
    Ge = _gate_vals(comps, gte, len(test.ynorm))
    w = (Ge * beta[None]) @ C                                   # nq x nb weights on base arrays
    num = np.einsum("qa,qa->q", w, test.Dy)
    den = np.sqrt(np.maximum(np.einsum("qa,qab,qb->q", w, test.D, w), 0.0)) * test.ynorm
    return np.where(den > 1e-12, num / np.maximum(den, 1e-12), 0.0), beta


def fit_predict(train: Compressed, test: Compressed, base_routes: tuple, orbit_routes: tuple, n_lines: int,
                ablate: tuple = ()) -> dict:
    """Scores per test query for every arm (and F without each route in `ablate`), plus gates and diagnostics."""
    gtr, gte, info = {}, {}, {}
    for r in orbit_routes:
        for kind, key in (("identity", "id"), ("accuracy", "acc")):
            o, t, meta = gates(train, test, r, kind, n_lines)
            gtr[(key, r)], gte[(key, r)], info[f"{key}:{r}"] = o, t, meta
    scores, betas = {}, {}
    for arm in ARMS:
        comps = arm_components(train.names, base_routes, orbit_routes, arm)
        scores[arm], betas[arm] = stack_and_score(train, test, comps, gtr, gte)
    for r in ablate:
        comps = arm_components(train.names, base_routes, orbit_routes, "F", drop=r)
        scores[f"F-{r}"], betas[f"F-{r}"] = stack_and_score(train, test, comps, gtr, gte)
    return {"scores": scores, "betas": {k: v.tolist() for k, v in betas.items()}, "gates_test": gte, "gate_info": info}


# ----------------------------------------------------------------------------------------- statistics

def entity_means(values: np.ndarray, entity: np.ndarray, mask: np.ndarray):
    e = entity[mask]
    v = values[mask]
    ue, inv = np.unique(e, return_inverse=True)
    s = np.bincount(inv, weights=v, minlength=len(ue))
    n = np.bincount(inv, minlength=len(ue))
    return ue, s / n


def paired(diff_by_entity: np.ndarray) -> dict:
    d = np.asarray(diff_by_entity, float)
    n = len(d)
    if n < 5:
        return {"units": int(n)}
    rng = np.random.default_rng(SEED)
    boots = d[rng.integers(0, n, (BOOT, n))].mean(1)
    signs = rng.choice((-1.0, 1.0), (FLIPS, n))
    null = (signs * d[None]).mean(1)
    obs = d.mean()
    return {"difference": float(obs), "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "p_greater": float((1 + (null >= obs).sum()) / (1 + FLIPS)), "units": int(n), "sd": float(d.std(ddof=1))}


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3:
        return float("nan")
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])
