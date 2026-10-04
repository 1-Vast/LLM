"""EXPLORATORY gated feedback diagnostic: does purchased target-line feedback improve within-line ordering?

File summary
- Path: research/astra/confirmation_campaign_20261004/design/feedback.py
- Purpose: contract v2 `feedback_diagnostic`. Under P3 with R's round-1 purchases, compute the frozen
  TransferWorld (WorldConfig(context=False)) feedback F_i = posterior mean - prior mean on the screen
  scale, split it into a line-level part m_line (mean over the eligible = unscreened candidates at the
  round-2 decision) and a centered part f_i, and compare three logistic models of P(joint call):
  F0 (a + b logit p_sv, b > 0), Fm (+ c_m m_line), Ff (+ c_f f_i; c_f = 0 when its HD line-bootstrap
  95% interval contains 0). Existing comparators U_lambda (V0 + lambda F) and U_screen_post (S0 + F)
  from repeats/model_id.py are reported too. The models change only the round-2 screen order of P3.
- Core points:
  - Worlds: HD campaign -> the <tissue>_<role> panel without any E line; E campaign -> without every
    other E line (asserted). Only the campaign's purchased round-1 screen labels enter the posterior,
    read from the policy state (never from the hidden outcomes).
  - Fitting uses HD development campaigns only (their hidden joint outcomes are legal development
    data). Logistic fits are Newton-Raphson (IRLS) maximum likelihood; b <= 0 -> b fixed at 1e-6.
  - Every campaign is logged: frozen prediction hashes before each paid reveal, reveals, scores, update.
- Interfaces: `fit_world`, `Signal`, `Decision2`, `collect`, `fit_models`, `predictions`, `evaluate_campaign`,
  `logistic_fit`, `lambda_fit`.
- Depends on: numpy, scipy; frozen research.certified_discovery.world and feedback_validation study
  (imported only); `campaign.py`.
"""
from __future__ import annotations

import numpy as np
from scipy.special import expit

from . import campaign as cp

B_FLOOR = 1e-6
MODELS = ("F0", "Fm", "Ff")
COMPARATORS = ("R", "U_lambda", "U_screen_post", "U_V0")
ALL_RANKINGS = ("R",) + MODELS + ("U_lambda", "U_screen_post", "U_V0")
PROB_RANKINGS = ("R", "F0", "Fm", "Ff")


def fit_world(panel, keep_sidms, target_sidm: str, e_lines):
    """Frozen TransferWorld on the role panel restricted to `keep_sidms` (+ target); asserts no other E line."""
    from research.astra.feedback_validation_20261003.study import WORLD
    from research.certified_discovery.world import TransferWorld

    lib = panel.library
    keep = set(keep_sidms) | {target_sidm}
    keep_idx = sorted(lib.lines.index(s) for s in keep)
    mask = np.isin(lib.c, keep_idx)
    sub = lib.subset(mask, f"{lib.name}_design_{target_sidm}")
    present = {lib.lines[k] for k in np.unique(sub.c)}
    leak = (present & set(e_lines)) - {target_sidm}
    if leak:
        raise AssertionError(f"LEAK: E lines in the world library: {sorted(leak)}")
    li = lib.lines.index(target_sidm)
    world = TransferWorld(sub, li, WORLD)
    full_rows = np.flatnonzero(lib.c == li)
    if not np.array_equal(np.flatnonzero(mask)[world.rows], full_rows):
        raise AssertionError("world rows differ from the target's menu rows")
    return world, sorted(present)


class Signal:
    """F(measured, values) = posterior mean - prior mean of the frozen world, for every menu candidate."""

    def __init__(self, world, positions: np.ndarray | None = None):
        self.world = world
        self.S0 = world.prior_target.copy()
        self.positions = None if positions is None else np.asarray(positions, np.int64)   # sub-menu -> world rows

    def F(self, measured: np.ndarray, values: np.ndarray) -> np.ndarray:
        measured = np.asarray(measured, np.int64)
        values = np.asarray(values, float)
        pos = measured if self.positions is None else self.positions[measured]
        if pos.size == 0:
            full = np.zeros(self.S0.size)
        else:
            mean, _ = self.world.posterior(pos, values)
            full = mean - self.S0
        return full if self.positions is None else full[self.positions]

    def prior(self) -> np.ndarray:
        return self.S0 if self.positions is None else self.S0[self.positions]


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, float), cp.CLIP, 1 - cp.CLIP)
    return np.log(p / (1 - p))


def logistic_fit(X: np.ndarray, y: np.ndarray, w: np.ndarray | None = None, offset: np.ndarray | None = None,
                 max_iter: int = 200, tol: float = 1e-10) -> np.ndarray:
    """Weighted maximum-likelihood logistic regression by damped Newton-Raphson."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    w = np.ones(y.size) if w is None else np.asarray(w, float)
    off = np.zeros(y.size) if offset is None else np.asarray(offset, float)
    beta = np.zeros(X.shape[1])

    def nll(b):
        eta = X @ b + off
        return float(np.sum(w * (np.logaddexp(0, eta) - y * eta)))

    cur = nll(beta)
    for _ in range(max_iter):
        eta = X @ beta + off
        p = expit(eta)
        grad = X.T @ (w * (y - p))
        H = X.T @ (X * (w * p * (1 - p))[:, None]) + 1e-12 * np.eye(X.shape[1])
        step = np.linalg.solve(H, grad)
        t = 1.0
        while True:
            new = beta + t * step
            val = nll(new)
            if val <= cur + 1e-12 or t < 1e-8:
                break
            t *= 0.5
        beta, cur = new, val
        if np.max(np.abs(t * step)) < tol:
            break
    return beta


def fit_constrained(x: np.ndarray, extra: np.ndarray | None, y: np.ndarray, w: np.ndarray | None = None) -> dict:
    """logit P = a + b x + extra @ c with b > 0 (b <= 0 -> b fixed at B_FLOOR, a and c refitted)."""
    cols = [np.ones(x.size), x] + ([] if extra is None else [extra[:, j] for j in range(extra.shape[1])])
    beta = logistic_fit(np.column_stack(cols), y, w)
    constrained = False
    if beta[1] <= 0:
        constrained = True
        cols2 = [np.ones(x.size)] + ([] if extra is None else [extra[:, j] for j in range(extra.shape[1])])
        b2 = logistic_fit(np.column_stack(cols2), y, w, offset=B_FLOOR * x)
        beta = np.r_[b2[0], B_FLOOR, b2[1:]]
    return {"beta": beta, "b_constrained": constrained}


class Decision2:
    """Quantities at the round-2 decision of one campaign (state after R's round-1 reveal)."""

    def __init__(self, tg: cp.Target, signal: Signal, st: cp.State):
        measured = np.flatnonzero(st.screened)
        self.eligible = ~st.screened
        self.F = signal.F(measured, st.y[measured])
        self.m = float(self.F[self.eligible].mean()) if self.eligible.any() else 0.0
        self.f = self.F - self.m
        self.x = logit(tg.scores["R"][0])
        self.S0 = signal.prior()
        self.V0 = tg.scores["L_v"][0]


def predictions(d: Decision2, tg: cp.Target, fit: dict) -> dict[str, np.ndarray]:
    a0, b0 = fit["F0"]["beta"]
    am, bm, cm = fit["Fm"]["beta"]
    af, bf, cfm, cf = fit["Ff_used"]["beta"]
    return {"R": tg.scores["R"][0].copy(),
            "F0": expit(a0 + b0 * d.x),
            "Fm": expit(am + bm * d.x + cm * d.m),
            "Ff": expit(af + bf * d.x + cfm * d.m + cf * d.f),
            "U_lambda": d.V0 + fit["lambda"]["lambda"] * d.F,
            "U_screen_post": d.S0 + d.F,
            "U_V0": d.V0.copy()}


def round1_state(tg: cp.Target, truth: dict) -> cp.State:
    """R's P3 round 1 only (identical for every feedback arm); returns the policy state after the reveal."""
    cs = cv = np.ones(tg.n, np.int64)
    lab, st = cp.Lab(truth, cs, cv, tg.M, deadline=3), cp.State(tg.n)
    order = tg.order(tg.scores["R"][0])
    reveals = lab.run_round(1, [int(i) for i in order[:(tg.M + 1) // 2]], [])
    st.update(1, reveals, cs, cv)
    return st


def collect(tg: cp.Target, truth: dict, signal: Signal) -> dict:
    """Development fitting rows of one campaign: eligible candidates at the round-2 decision."""
    st = round1_state(tg, truth)
    d = Decision2(tg, signal, st)
    e = d.eligible
    joint = (np.asarray(truth["h_s"], bool) & np.asarray(truth["h_v"], bool)).astype(float)
    return {"x": d.x[e], "m": np.full(int(e.sum()), d.m), "f": d.f[e], "joint": joint[e], "F": d.F[e],
            "V0": d.V0[e], "v": np.asarray(truth["y_v"], float)[e], "n_eligible": int(e.sum()), "m_line": d.m}


def lambda_fit(per_line: dict) -> float:
    """model_id.fit_lambda: lambda = sum_l a_l / sum_l b_l, a_l = mean F (v - V0), b_l = mean F^2 (roles averaged)."""
    A = np.array([np.mean([u[0] for u in per_line[k]]) for k in sorted(per_line)])
    B = np.array([np.mean([u[1] for u in per_line[k]]) for k in sorted(per_line)])
    return float(A.sum() / B.sum()) if B.sum() > 0 else 0.0


def fit_models(rows_by_campaign: dict, keys: list, resamples: int = cp.RESAMPLES) -> dict:
    """Fit F0, Fm, Ff on HD campaigns; c_f line-bootstrap (registered scheme); lambda for U_lambda."""
    camp_keys = sorted(rows_by_campaign)
    line_of = {ck: (ck[0], ck[1]) for ck in camp_keys}
    cat = {f: np.concatenate([rows_by_campaign[ck][f] for ck in camp_keys]) for f in ("x", "m", "f", "joint")}
    line_id = np.concatenate([np.full(rows_by_campaign[ck]["x"].size, keys.index(line_of[ck])) for ck in camp_keys])
    x, m, f, y = cat["x"], cat["m"], cat["f"], cat["joint"]
    F0 = fit_constrained(x, None, y)
    Fm = fit_constrained(x, m[:, None], y)
    Ff = fit_constrained(x, np.column_stack([m, f]), y)
    idx = cp.boot_indices(keys, resamples)
    cf = np.empty(len(idx))
    for b, ii in enumerate(idx):
        w = np.bincount(ii, minlength=len(keys)).astype(float)[line_id]
        cf[b] = fit_constrained(x, np.column_stack([m, f]), y, w)["beta"][3]
    lo, hi = (float(v) for v in np.percentile(cf, [2.5, 97.5]))
    zeroed = bool(lo <= 0.0 <= hi)
    used = {"beta": np.r_[Fm["beta"], 0.0] if zeroed else Ff["beta"], "c_f_zeroed": zeroed}
    per_line: dict = {}
    for ck in camp_keys:
        r = rows_by_campaign[ck]
        if r["F"].size:
            per_line.setdefault(line_of[ck], []).append((float(np.mean(r["F"] * (r["v"] - r["V0"]))),
                                                         float(np.mean(r["F"] ** 2))))
    lam = lambda_fit(per_line)
    lam_draws = np.empty(len(idx))
    lk = sorted(per_line)
    A = np.array([np.mean([u[0] for u in per_line[k]]) for k in lk])
    B = np.array([np.mean([u[1] for u in per_line[k]]) for k in lk])
    pos = np.array([keys.index(k) for k in lk])
    for b, ii in enumerate(idx):
        w = np.bincount(ii, minlength=len(keys)).astype(float)[pos]
        lam_draws[b] = float((w * A).sum() / (w * B).sum()) if (w * B).sum() > 0 else 0.0

    def ll(beta, X):
        p = np.clip(expit(X @ beta), cp.CLIP, 1 - cp.CLIP)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    one = np.ones(x.size)
    return {"rows": int(y.size), "campaigns": len(camp_keys), "lines": len(keys), "joint_rate": float(y.mean()),
            "F0": F0, "Fm": Fm, "Ff": Ff, "Ff_used": used,
            "c_f_bootstrap": {"ci": [lo, hi], "resamples": len(idx), "seed": cp.SEED,
                              "scheme": "registered tissue-stratified line bootstrap over HD lines"},
            "lambda": {"lambda": lam, "ci": [float(v) for v in np.percentile(lam_draws, [2.5, 97.5])],
                       "rule": "model_id.fit_lambda on eligible round-2 candidates (v = verification label)"},
            "in_sample_log_loss": {"F0": ll(F0["beta"], np.column_stack([one, x])),
                                   "Fm": ll(Fm["beta"], np.column_stack([one, x, m])),
                                   "Ff": ll(Ff["beta"], np.column_stack([one, x, m, f]))}}


def fit_from_json(obj: dict) -> dict:
    """Rebuild the fit dict from feedback_fit.json (betas as arrays)."""
    out = dict(obj)
    for k in ("F0", "Fm", "Ff", "Ff_used"):
        out[k] = dict(obj[k], beta=np.asarray(obj[k]["beta"], float))
    return out


def evaluate_campaign(tg: cp.Target, truth: dict, signal: Signal, fit: dict) -> dict:
    """Round-2 predictions (frozen before the round-2 reveal), their scores, and P3 yields per ranking."""
    st = round1_state(tg, truth)
    d = Decision2(tg, signal, st)
    preds = predictions(d, tg, fit)
    e = d.eligible
    joint = np.asarray(truth["h_s"], bool) & np.asarray(truth["h_v"], bool)
    out = {"tissue": tg.tissue, "line": tg.sidm, "role": tg.role, "n_menu": tg.n, "M": tg.M,
           "n_eligible": int(e.sum()), "eligible_joint_hits": int(joint[e].sum()), "m_line": d.m,
           "F_sha256": cp.score_hash(d.F), "frozen_predictions_sha256": {k: cp.score_hash(v) for k, v in preds.items()},
           "auc": {}, "probability": {}, "p3": {}}
    for k, v in preds.items():
        out["auc"][k] = cp.auc(v[e], joint[e])
    for k in PROB_RANKINGS:
        out["probability"][k] = cp.prob_scores(preds[k][e], joint[e]) if e.any() else None
    logs = {}
    for k in ALL_RANKINGS:
        if k == "R":
            rec = cp.run_p3(tg, truth, "R", arm_label="R")
        else:
            def hook(state, key=k):
                dd = Decision2(tg, signal, state)
                p = predictions(dd, tg, fit)[key]
                return tg.order(p), p
            rec = cp.run_p3(tg, truth, "R", round2_order=hook, arm_label=k)
        out["p3"][k] = {f: rec[f] for f in ("confirmed", "n_screens", "n_screen_hits", "n_verifications",
                                            "n_verification_hits", "spent", "round2_screens", "round2_screen_hits",
                                            "rounds_used", "missed_unscreened", "missed_screened_not_verified")}
        logs[k] = rec
    out["identical_round1"] = len({tuple(r["rounds"][0]["screens"]) for r in logs.values()}) == 1
    out["F0_equals_R_purchases"] = logs["F0"]["screens"] == logs["R"]["screens"] and \
        logs["F0"]["verifies"] == logs["R"]["verifies"]
    return out, logs
