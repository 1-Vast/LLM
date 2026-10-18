"""Campaign execution: histories, nomination of unmeasured pairs, grading, and the closed feedback loop.

File summary
- Path: research/feedback_propagation_20261018/loop.py
- Purpose: (1) build identical probe histories for update attribution; (2) run the closed loop
  (acquire an allowed observation, update predictions, recompute admissible actions, continue);
  (3) nominate and grade follow-up lists from the unmeasured pairs and, separately, from all pairs.
- Definitions:
  - A unit is one acquisition. In the pool grain it is a (compound, pool) well that returns every admissible line
    of the pool; in the logical grain it is one (compound, line) query. Costs are in units and are hypothetical
    (see AUDIT.json). A failed cell (missing in the scoring matrix) is spent and returns NaN.
  - Admissible actions: lines the training set measured for >= MIN_TRAIN_FINITE of its compounds, not yet queried
    for that compound.
  - Nominations: top FOLLOW_UP pairs per campaign, at most CAP per compound. `unmeasured` nominations come only
    from pairs no unit was spent on; `any` nominations may also use measured pairs.
  - Utilities: hits = nominated pairs that are registered events in the scoring matrix; unique = distinct compounds
    with at least one such hit; unknown = nominated pairs whose scoring-matrix cell is missing (counted as
    non-hits, reported as an upper-bound allowance).
  - Closed loop (pool grain): a seed pool (first pool of the design order), then in every round each compound
    recomputes its scores with the update rule from its whole history and buys the pool whose unqueried admissible
    lines have the largest sum of their CAP highest scores. The acquisition form is identical for every update rule.
- Interfaces: `pool_history`, `fixed_histories`, `closed_loop`, `evaluate_rule`, `grade_lists`, `nominate_lists`,
  `oracle_lists`, `derange`, `queried_from`.
"""
from __future__ import annotations

import numpy as np

import bench
import rules as R
from bench import CAP, FOLLOW_UP, Fold, tc


# ---------------------------------------------------------------- histories
def fixed_histories(fold: Fold, oracle, w: int, design_lines: np.ndarray | None = None) -> dict:
    """Identical logical histories: the first `w` sparse-design lines for every compound."""

    lines = fold.design[:w] if design_lines is None else np.asarray(design_lines)
    return {i: (lines.copy(), oracle.observe(i, lines)) for i in range(len(fold.cores))}


def pool_lines_for(fold: Fold, B: int) -> np.ndarray:
    return np.concatenate([bench.pool_lines(fold, p) for p in bench.pool_order(fold)[:B]])


def pool_history(fold: Fold, oracle, B: int) -> dict:
    """Identical pool histories: the first `B` pools of the design order for every compound."""

    return fixed_histories(fold, oracle, B, pool_lines_for(fold, B))


def derange(fold: Fold, hist: dict, shift: int = 1) -> dict:
    """Negative control: each compound receives the observed values of another compound of its campaign (same lines)."""

    out = {}
    for idx in fold.campaigns:
        for k, i in enumerate(idx):
            j = int(idx[(k + shift) % len(idx)])
            out[int(i)] = (hist[int(i)][0], hist[j][1].copy())
    return out


def queried_from(fold: Fold, histories: dict) -> np.ndarray:
    q = np.zeros((len(fold.cores), len(fold.lines)), dtype=bool)
    for i, (P, _) in histories.items():
        q[i, P] = True
    return q


# ---------------------------------------------------------------- scores, lists, grades
def score_matrix(fold: Fold, rule: str, histories: dict, rows=None, **params) -> np.ndarray:
    rows = range(len(fold.cores)) if rows is None else rows
    out = np.full((len(fold.cores), len(fold.lines)), -np.inf)
    for i in rows:
        P, y = histories[i]
        out[i] = R.score(rule, fold, i, P, y, **params)
    return out


def admissible(fold: Fold, queried: np.ndarray, only_unmeasured: bool) -> np.ndarray:
    ok = np.broadcast_to(fold.avail[None, :], queried.shape).copy()
    if only_unmeasured:
        ok &= ~queried
    return ok


def nominate_lists(fold: Fold, S: np.ndarray, queried: np.ndarray, *, only_unmeasured: bool,
                   target: np.ndarray | None = None) -> list:
    """One follow-up list per campaign: [(campaign-local compound, line)]. `target` restricts the candidate lines."""

    mask = admissible(fold, queried, only_unmeasured)
    if target is not None:
        mask &= np.asarray(target, dtype=bool)[None, :]
    lists = []
    for idx in fold.campaigns:
        sc = np.where(mask[idx], S[idx], -np.inf)
        lists.append(tc.nominate(sc, fold.cores[idx], FOLLOW_UP, CAP))
    return lists


def grade_lists(fold: Fold, lists: list, queried: np.ndarray) -> dict:
    """Per-campaign and per-compound utilities of the nominated lists (reads the hidden side)."""

    h = fold.hidden
    n = len(fold.cores)
    hits_c = np.zeros(n)
    unknown_c = np.zeros(n)
    listed_c = np.zeros(n)
    measured_hits = np.zeros(n)
    rows = []
    for idx, picks in zip(fold.campaigns, lists):
        hit_pairs = [(int(idx[i]), l) for i, l in picks if h.truth[idx[i], l]]
        unk = [(int(idx[i]), l) for i, l in picks if not np.isfinite(h.Y[idx[i], l])]
        for i, l in picks:
            listed_c[idx[i]] += 1
        for i, l in hit_pairs:
            hits_c[i] += 1
            measured_hits[i] += bool(queried[i, l])
        for i, l in unk:
            unknown_c[i] += 1
        rows.append({"hits": len(hit_pairs), "unique": len({i for i, _ in hit_pairs}), "unknown": len(unk),
                     "listed": len(picks), "compounds": int(len(idx)),
                     "lineage_hits": len({(i, str(fold.lineage[l])) for i, l in hit_pairs})})
    return {"campaigns": rows, "hits_c": hits_c, "unknown_c": unknown_c, "listed_c": listed_c,
            "measured_hits_c": measured_hits}


def evaluate_scores(fold: Fold, S: np.ndarray, queried: np.ndarray, target: np.ndarray | None = None) -> dict:
    return {"unmeasured": grade_lists(fold, nominate_lists(fold, S, queried, only_unmeasured=True, target=target), queried),
            "any": grade_lists(fold, nominate_lists(fold, S, queried, only_unmeasured=False, target=target), queried)}


def evaluate_rule(fold: Fold, rule: str, histories: dict, queried: np.ndarray, **params) -> dict:
    return evaluate_scores(fold, score_matrix(fold, rule, histories, **params), queried)


def oracle_lists(fold: Fold, queried: np.ndarray, only_unmeasured: bool) -> list:
    """Ceiling: nominate true events (ties by the salted hash) among the admissible pairs."""

    return nominate_lists(fold, fold.hidden.truth.astype(float), queried, only_unmeasured=only_unmeasured)


# ---------------------------------------------------------------- closed loop (pool grain)
def _pool_value(fold: Fold, s: np.ndarray, queried_i: np.ndarray, pools: list) -> tuple[int, float]:
    """The unqueried pool whose admissible lines have the largest sum of their CAP highest scores."""

    best, best_v = None, -np.inf
    for p in pools:
        ls = bench.pool_lines(fold, p)
        ls = ls[~queried_i[ls]]
        if len(ls) == 0:
            continue
        v = float(np.sort(s[ls])[::-1][:CAP].sum())
        if v > best_v:
            best, best_v = p, v
    return best, best_v


def closed_loop(fold: Fold, rule: str, *, B: int = 3, params: dict | None = None, allocation: str = "uniform",
                rows=None) -> tuple:
    """Run the closed feedback loop for every compound of a fold with the given update rule.

    Seed: the first pool of the design order. `allocation='uniform'`: every compound buys B-1 more pools, one per
    round, each chosen by `_pool_value` from the rule's scores on its whole history. `allocation='two_stage'`
    (conventional adaptive screen): after the seed pool the compounds with the strongest observed kill (lowest seed
    value) buy 4 more pools each until the same total, B pools per compound on average, is spent.
    Returns (histories, queried, oracle).
    """

    params = params or {}
    oracle = fold.oracle()
    n = len(fold.cores)
    rows = list(range(n)) if rows is None else list(rows)
    order = bench.pool_order(fold)
    seed = bench.pool_lines(fold, order[0])
    hist = {i: (seed.copy(), oracle.observe(i, seed)) for i in rows}
    queried = queried_from(fold, hist)
    if allocation == "uniform":
        extra = np.zeros(n, dtype=int)
        extra[rows] = B - 1
    elif allocation == "two_stage":
        total = (B - 1) * len(rows)
        potency = np.array([np.nanmin(hist[i][1]) if np.isfinite(hist[i][1]).any() else np.inf for i in rows])
        ranked = [rows[k] for k in np.argsort(potency, kind="stable")]
        extra = np.zeros(n, dtype=int)
        per = 4
        for i in ranked:
            give = min(per, total)
            extra[i] = give
            total -= give
            if total <= 0:
                break
    else:
        raise ValueError(allocation)
    pools_all = list(order)
    for r in range(int(extra.max()) if n else 0):
        for i in rows:
            if extra[i] <= r:
                continue
            P, y = hist[i]
            s = R.score(rule, fold, i, P, y, **params)
            p, _ = _pool_value(fold, s, queried[i], pools_all)
            if p is None:
                continue
            ls = bench.pool_lines(fold, p)
            hist[i] = (np.concatenate([P, ls]), np.concatenate([y, oracle.observe(i, ls)]))
            queried[i, ls] = True
    return hist, queried, oracle
