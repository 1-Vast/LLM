"""Whole-pool target task, lookahead features and policy evaluation for the acquisition-program study.

File summary
- Path: research/acquisition_program_20261018/ap_task.py
- Purpose: one development task with a shared, predeclared target set of whole PRISM pools. Probes may only buy pools
  outside the target, so no probe reveals a target entry. Event definition, nomination constraints (32 per 64
  compounds, at most 3 per compound), query budget (3 pools per compound) and the scoring rule (the ridge-plus-feedback
  conditional mean passed through `call_score`) are those of the predecessor and are not changed.
- Acquisition decision studied: after a fixed seed pool, which of the remaining non-target pools to read second; the
  third pool is bought by the fixed policy (the next pool of the fixed order not yet bought).
- Features (per compound and candidate pool, all computed from the seed history, the training set and the fitted world;
  nothing from the hidden side): `la` expected terminal nomination utility of a one-step lookahead using the joint
  posterior over the pool's lines, posterior-sampled outcomes and posterior-sampled event estimates (model
  probabilities are unvalidated estimates); `ev0` the same quantity without a further observation; `vr`/`vr_rel`
  posterior variance reduction on the target; `shift` expected absolute mean shift on the target; `flip` probability that
  the top-3 nominated set changes; `rank` position in the fixed order; `n_lines`, `obs_min`.
- Counterfactual table: for the evaluation, the final ridge scores after each possible choice are tabulated once per
  scenario (the same oracle answers an executed run would receive); a policy only indexes that table with its choice.
- Interfaces: `groups`, `Task`, `build_scenario`, `evaluate_choice`, `comparator_arms`, `ProgramError`, `eval_program`.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PRED = HERE.parent / "feedback_propagation_20261018"
if str(PRED) not in sys.path:
    sys.path.insert(0, str(PRED))
import bench  # noqa: E402
import loop as L  # noqa: E402
import metrics as M  # noqa: E402
import rules as R  # noqa: E402
from bench import CAP, FOLLOW_UP, tc  # noqa: E402

B_POOLS = 3
S_OUT, K_DRAW = 16, 32          # posterior-sampled outcomes and event draws per outcome
FEATURES = ("la", "ev0", "gain", "vr", "vr_rel", "shift", "flip", "rank", "n_lines", "obs_min")


def groups(fold) -> list:
    """Predeclared target groups: the pools ordered by a salted hash, cut into 6, 6, 6, 5 whole pools."""

    pools = sorted(set(int(p) for p in fold.pid))
    order = sorted(pools, key=lambda p: tc.h(f"pool{p}", "ap-target-group"))
    return [order[0:6], order[6:12], order[12:18], order[18:]]


@dataclass
class Task:
    fold: object            # predecessor Fold with campaigns restricted to the task's complete campaigns
    group: int
    pools_target: list
    target: np.ndarray      # (L,) bool
    fixed: list             # probe pools outside the target in the fixed (A-optimal) order
    rows: np.ndarray        # compound indices of the evaluated campaigns
    name: str


def make_task(fold, group: int, n_campaigns: int) -> Task:
    pools_t = groups(fold)[group]
    target = np.isin(fold.pid, pools_t) & fold.avail
    fixed = [p for p in bench.pool_order(fold) if p not in pools_t and len(bench.pool_lines(fold, p)) > 0]
    camps = [ix for ix in fold.campaigns if len(ix) == M.CAMPAIGN][:n_campaigns]
    sub = replace(fold, campaigns=camps)
    return Task(sub, group, pools_t, target, fixed, np.concatenate(camps), f"f{fold.fold}g{group}")


def scenario_hidden(fold, salt: str):
    """Hidden side with a different frozen noise draw (same cells, same truth); keyed by (core, salt)."""

    h = fold.hidden
    z = np.stack([np.random.default_rng(tc.h(str(c), salt) % (2 ** 32)).standard_normal(h.Y.shape[1]) for c in fold.cores])
    return bench.Hidden(Y=h.Y, truth=h.truth, sd=h.sd, z=z, family=h.family)


def _full_cov(fold) -> np.ndarray:
    if "S_full" not in fold.cache:
        w = fold.world
        fold.cache["S_full"] = w.V @ w.V.T + np.diag(w.D)
    return fold.cache["S_full"]


def _events_of(profiles: np.ndarray, G: np.ndarray) -> np.ndarray:
    return tc.events(profiles, G)


def _top3_value(m2: np.ndarray, p: np.ndarray, T: np.ndarray, G: np.ndarray) -> np.ndarray:
    """For each row s: the sum of the event estimates of the 3 target lines the scoring rule would nominate."""

    sc = bench.call_score(m2, G)[:, T]
    top = np.argsort(-sc, axis=1)[:, :CAP]
    return np.take_along_axis(p, top, axis=1).sum(1), top


def _state(fold, i, P, y):
    w = fold.world
    m = fold.prior[i]
    ok = np.isfinite(y)
    P, y = P[ok], y[ok]
    S = _full_cov(fold)
    Spp, SLP = w._blocks(P)
    A = Spp + w.s2 * np.eye(len(P))
    Kg = np.linalg.solve(A, SLP.T).T
    m1 = m + Kg @ (y - m[P])
    Sig1 = S - Kg @ SLP.T
    return m1, Sig1


def _sample_events(m_rows: np.ndarray, cholT: np.ndarray, T: np.ndarray, e: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Event estimates on the target lines for each posterior mean row: (rows, |T|)."""

    rows = m_rows.shape[0]
    base = np.repeat(m_rows[:, None, :], e.shape[0], axis=1)                 # rows, K, L
    noise = e @ cholT.T                                                      # K, |T|
    base[:, :, T] = m_rows[:, None, T] + noise[None, :, :]
    ev = _events_of(base.reshape(rows * e.shape[0], -1), G).reshape(rows, e.shape[0], -1)
    return ev[:, :, T].mean(1)


def features_for(fold, task: Task, i: int, P, y, cands: list, rng_key: str) -> dict:
    """Lookahead features of every candidate pool for compound i (hidden side never touched)."""

    w = fold.world
    T = np.where(task.target)[0]
    G = fold.G
    m1, Sig1 = _state(fold, i, np.asarray(P, int), np.asarray(y, float))
    rng = np.random.default_rng(tc.h(str(fold.cores[i]), rng_key) % (2 ** 32))
    e = rng.standard_normal((K_DRAW, len(T)))
    zs = rng.standard_normal((S_OUT, 64))
    SigTT = Sig1[np.ix_(T, T)]
    jitter = 1e-8 * np.trace(SigTT) / len(T)
    chol0 = np.linalg.cholesky(SigTT + jitter * np.eye(len(T)))
    p0 = _sample_events(m1[None, :], chol0, T, e, G)
    ev0, top0 = _top3_value(m1[None, :], p0, T, G)
    ev0 = float(ev0[0])
    set0 = set(top0[0].tolist())
    trT = float(np.trace(SigTT))
    out = {k: np.zeros(len(cands)) for k in FEATURES}
    ysf = np.asarray(y, float)
    for j, c in enumerate(cands):
        Q = bench.pool_lines(fold, c)
        Sqq = Sig1[np.ix_(Q, Q)] + w.s2 * np.eye(len(Q))
        cq = np.linalg.cholesky(Sqq)
        Z = zs[:, :len(Q)] if len(Q) <= 64 else rng.standard_normal((S_OUT, len(Q)))
        SQ = Sig1[:, Q]
        W = np.linalg.solve(cq.T, Z.T).T                                     # S, |Q|
        delta = W @ SQ.T                                                     # S, L
        m2 = m1[None, :] + delta
        SigT2 = SigTT - Sig1[np.ix_(T, Q)] @ np.linalg.solve(Sqq, Sig1[np.ix_(Q, T)])
        chol2 = np.linalg.cholesky(SigT2 + jitter * np.eye(len(T)))
        p = _sample_events(m2, chol2, T, e, G)
        vals, top = _top3_value(m2, p, T, G)
        out["la"][j] = vals.mean()
        out["gain"][j] = vals.mean() - ev0
        out["ev0"][j] = ev0
        vr = trT - float(np.trace(SigT2))
        out["vr"][j] = vr
        out["vr_rel"][j] = vr / trT
        out["shift"][j] = float(np.abs(delta[:, T]).mean())
        out["flip"][j] = float(np.mean([set(t.tolist()) != set0 for t in top]))
        out["rank"][j] = j
        out["n_lines"][j] = len(Q)
        out["obs_min"][j] = float(np.nanmin(ysf)) if np.isfinite(ysf).any() else 0.0
    return out


def build_scenario(task: Task, salt: str, with_features: bool = True) -> dict:
    """Seed observations, candidate features and the counterfactual table of final scores for one noise scenario."""

    fold = task.fold
    hid = scenario_hidden(fold, salt)
    fixed = task.fixed
    seed_p, cands = fixed[0], fixed[1:]
    seed = bench.pool_lines(fold, seed_p)
    T = np.where(task.target)[0]
    rows = task.rows
    nC = len(cands)
    feats = {k: np.zeros((len(rows), nC)) for k in FEATURES}
    final = np.zeros((len(rows), nC, len(T)), dtype=np.float32)
    oracle = bench.Oracle(hid)
    for r, i in enumerate(rows):
        y1 = oracle.observe(i, seed)
        if with_features:
            f = features_for(fold, task, int(i), seed, y1, cands, f"ap-mc-{salt}")
            for k in FEATURES:
                feats[k][r] = f[k]
        for j, c in enumerate(cands):
            q3 = next(p for p in fixed[1:] if p != c)
            P = np.concatenate([seed, bench.pool_lines(fold, c), bench.pool_lines(fold, q3)])
            y = np.concatenate([y1, oracle.observe(i, bench.pool_lines(fold, c)), oracle.observe(i, bench.pool_lines(fold, q3))])
            prof = R.conditional_mean(fold, fold.prior[i], P, y)
            final[r, j] = bench.call_score(prof, fold.G)[T]
    truth = hid.truth[rows][:, T]
    out = {"salt": salt, "features": feats, "final": final, "truth": truth, "cands": cands, "T": T, "hidden": hid}
    out["comparators"] = comparator_scores(task, out)
    return out


def grade_scores(task: Task, scen: dict, F: np.ndarray) -> dict:
    """Nominate on the target from scores F (rows x |T|); per-compound hits and campaign hits (reads the hidden side)."""

    fold = task.fold
    rows = task.rows
    T = scen["T"]
    n_all = len(fold.cores)
    S = np.full((n_all, fold.world.L), -np.inf)
    S[np.ix_(rows, T)] = F
    f2 = replace(fold, hidden=scen["hidden"])
    zeros = np.zeros((n_all, fold.world.L), dtype=bool)
    lists = L.nominate_lists(f2, S, zeros, only_unmeasured=False, target=task.target)
    g = L.grade_lists(f2, lists, zeros)
    camp = [c["hits"] for c in g["campaigns"]]
    return {"hits_c": g["hits_c"][rows], "campaign_hits": camp, "unknown": int(sum(c["unknown"] for c in g["campaigns"])),
            "hits": int(sum(camp)), "unique": int(sum(c["unique"] for c in g["campaigns"]))}


def grade_choice(task: Task, scen: dict, choice: np.ndarray) -> dict:
    fold = task.fold
    g = grade_scores(task, scen, scen["final"][np.arange(len(task.rows)), choice])
    lines = [len(bench.pool_lines(fold, p)) for p in task.fixed]
    seedn = lines[0]
    g["lines"] = float(np.mean([seedn + lines[1 + int(k)] + len(bench.pool_lines(fold, next(p for p in task.fixed[1:] if p != task.fixed[1 + int(k)])))
                                for k in choice]))
    return g


COMPARATORS = (("prior", "prior", {}), ("ridge", "ridge", {}), ("mixture_mean", "mixture_mean", {}), ("empcov_0.1", "empcov", {"alpha": 0.1}),
               ("knn10", "knn", {"K": 10}), ("knn20", "knn", {"K": 20}), ("knn40", "knn", {"K": 40}), ("forest", "forest", {}),
               ("R1", "anchored", {"K": 10, "lam": 1.0}), ("gated", "repair", {"K": 10, "lam": 1.0, "loss": "kill", "gate": "lopo"}))


def comparator_scores(task: Task, scen: dict) -> dict:
    """Every predecessor update rule on the fixed-design history (seed, then the next two pools of the fixed order)."""

    fold = task.fold
    T = scen["T"]
    P = np.concatenate([bench.pool_lines(fold, p) for p in task.fixed[:B_POOLS]])
    oracle = bench.Oracle(scen["hidden"])
    hist = {int(i): (P, oracle.observe(int(i), P)) for i in task.rows}
    out = {}
    for name, rule, prm in COMPARATORS:
        out[name] = np.stack([R.score(rule, fold, int(i), *(() if rule == "prior" else hist[int(i)]), **prm) if rule != "prior"
                              else R.score("prior", fold, int(i), [], []) for i in task.rows])[:, T].astype(np.float32)
    return out


# ------------------------------------------------------------------ programs
class ProgramError(ValueError):
    pass


_ALLOWED_FUNCS = {"abs": np.abs, "sqrt": lambda x: np.sqrt(np.maximum(x, 0)), "log1p": lambda x: np.log1p(np.maximum(x, -0.999)),
                  "exp": lambda x: np.exp(np.clip(x, -30, 30)), "tanh": np.tanh, "minimum": np.minimum, "maximum": np.maximum,
                  "where": np.where, "zs": lambda x: (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-9),
                  "rk": lambda x: np.argsort(np.argsort(x, axis=1), axis=1).astype(float)}
_ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult,
                  ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Compare, ast.Gt, ast.Lt, ast.GtE, ast.LtE)


def compile_program(expr: str):
    """A restricted vectorised expression over the feature names; rows = compounds, columns = candidate pools."""

    if len(expr) > 400:
        raise ProgramError("expression too long")
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise ProgramError(f"syntax: {e}") from e
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ProgramError(f"node {type(node).__name__} not allowed")
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS):
            raise ProgramError("call not allowed")
        if isinstance(node, ast.Name) and node.id not in FEATURES and node.id not in _ALLOWED_FUNCS:
            raise ProgramError(f"unknown name {node.id}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ProgramError("constant type")
        if isinstance(node, ast.Pow):
            raise ProgramError("power not allowed")
    code = compile(tree, "<program>", "eval")

    def run(feats: dict) -> np.ndarray:
        env = dict(_ALLOWED_FUNCS)
        env.update({k: v for k, v in feats.items()})
        with np.errstate(all="ignore"):
            v = eval(code, {"__builtins__": {}}, env)  # noqa: S307 (whitelisted AST, numeric arrays only)
        v = np.broadcast_to(np.asarray(v, float), next(iter(feats.values())).shape)
        return np.where(np.isfinite(v), v, -1e9)

    return run


def choose(feats: dict, run) -> np.ndarray:
    """argmax over candidate pools; ties go to the fixed order (the smallest rank)."""

    v = run(feats)
    tie = feats["rank"] * 1e-9
    return np.argmax(v - tie, axis=1)


def eval_program(task: Task, scenarios: list, expr: str | None) -> dict:
    """Mean over scenarios of campaign hits; expr None = the fixed design (second pool is the next in the fixed order)."""

    run = compile_program(expr) if expr else None
    res = []
    for sc in scenarios:
        ch = np.zeros(len(task.rows), dtype=int) if run is None else choose(sc["features"], run)
        g = grade_choice(task, sc, ch)
        g["changed_share"] = float(np.mean(ch != 0))
        res.append(g)
    return {"per_scenario": res}
