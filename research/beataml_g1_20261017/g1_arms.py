"""Arms of gate G1: item ranking, S_ridge, ridge plus feedback, the confirmed engine and the frozen candidate.

File summary
- Path: research/beataml_g1_20261017/g1_arms.py
- Purpose: every arm of PROTOCOL.md on one fold, and the inner choice of the probe count on source patients.
- Core points:
  - All arms spend 16 queries per sample and are scored by TOTAL known frozen events (probes included).
  - The low-rank arms are the attribution study's, unchanged (`BridgedTransferModel`, `CoherentScorer`,
    exploit-first probes, tie-breaks, availability weight `q`). The ridge arm is that study's `strong_state`
    S_ridge, re-derived here so that its mean, variance and residuals are available; `ridge_parts` is checked
    against `strong_state` (parity) before a record is written.
  - `RF` (ridge plus feedback): the S_ridge event residual is updated by the returned probe readouts through
    a conditional Gaussian on the ridge's own leave-one-out residuals (PROTOCOL.md section 4). No latent
    factor model, no Virtual Cell.
  - `choose_k` fits and replays only on the fold's source patients (patient-disjoint inner folds), so the
    outer targets cannot influence the choice.
- Interfaces: `ridge_parts`, `residual_cov`, `rf_probs`, `evaluate`, `choose_k`, constants.
- This folder must not contain a module named ``agent``, ``virtual_cell``, ``maestro``, ``common`` or any
  module of `feedback_attribution_20261017` (it is on ``sys.path``).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FEEDBACK = ROOT / "research" / "feedback_attribution_20261017"
if str(FEEDBACK) not in sys.path:
    sys.path.append(str(FEEDBACK))

from coherent import CoherentScorer  # noqa: E402  (feedback_attribution; puts src on sys.path)
from common import basal_pcs, hash_folds, tie  # noqa: E402

from agent.bridge_design import nominate  # noqa: E402
from virtual_cell.bridged_transfer import RIDGE_ALPHAS, BridgedTransferModel, normal_cdf  # noqa: E402

BUDGET = 16
KS = (4, 8, 12)
RANK = 20
MIN_MEASURED, IMPUTE = 100, 15
INNER_FOLDS = 3
LAMBDA_RF, LAMBDA_ALT = 0.1, 0.5
MIN_PAIR = 30
EIG_FLOOR = 1e-3
VAR_FLOOR = 0.05
ROUNDS = {"A_item": 1, "S_ridge": 1, "C0": 1, "RF": 2, "RF_s": 2, "E": 2, "CAND": 2}
ARMS_FIXED = ["A_item", "S_ridge", "C0", "E"] + [f"C_{k}" for k in KS] + [f"RF_{k}" for k in KS] + [f"RFs_{k}" for k in KS]


# ---------------------------------------------------------------- ridge prior


def _ridge_loo(P1: np.ndarray, y: np.ndarray):
    """Ridge on [1, PCs] with the penalty chosen by closed-form leave-one-out (the attribution study's)."""

    best = None
    pen = np.diag([0.0] + [1.0] * (P1.shape[1] - 1))
    for alpha in RIDGE_ALPHAS:
        A = P1.T @ P1 + alpha * pen
        B = np.linalg.solve(A, P1.T @ y)
        H = np.einsum("ij,jk,ik->i", P1, np.linalg.inv(A), P1)
        loo = (y - P1 @ B) / (1 - H)
        err = float((loo ** 2).mean())
        if best is None or err < best[0]:
            best = (err, B, loo)
    return best[1], best[2]


def ridge_parts(d: dict, src: np.ndarray, tgt: np.ndarray, model: BridgedTransferModel) -> dict:
    """S_ridge for the fold: per target the event probability, mean, variance and ridge predictions, plus the
    source leave-one-out residual matrix (items, then the sample median G).

    ``prob`` equals ``attribution.strong_state(...)["S_ridge"]`` exactly (checked in the run's parity step).
    """

    Y = d["Y"]
    D = Y.shape[1]
    P = basal_pcs(d["X"], rows=src)
    P1 = np.column_stack([np.ones(len(P)), P])
    Gs = np.nanmedian(Y[src], axis=1)
    bG, rG = _ridge_loo(P1[src], Gs)
    predG = P1[tgt] @ bG
    c = model.med - 3.0 * model.mad
    prob = np.zeros((len(tgt), D))
    mean0 = np.full((len(tgt), D), np.nan)
    var0 = np.full((len(tgt), D), np.nan)
    pred = np.full((len(tgt), D), np.nan)
    R = np.full((len(src), D + 1), np.nan)
    R[:, D] = rG
    fitted = np.zeros(D, bool)
    for j in range(D):
        if not model.threshold_ok[j]:
            continue
        rows = np.flatnonzero(np.isfinite(Y[src, j]))
        if len(rows) < 30:
            prob[:, j] = model.source_event_rate[j]
            continue
        y = Y[src[rows], j]
        bj, rj = _ridge_loo(P1[src[rows]], y)
        R[rows, j] = rj
        b = model.b[j]
        rg = rG[rows]
        var = rj.var() + b * b * rg.var() - 2 * b * np.mean((rj - rj.mean()) * (rg - rg.mean()))
        pred[:, j] = P1[tgt] @ bj
        mean0[:, j] = pred[:, j] - model.a[j] - b * predG
        var0[:, j] = max(var, 1e-9)
        prob[:, j] = normal_cdf((c[j] - mean0[:, j]) / np.sqrt(var0[:, j]))
        fitted[j] = True
    return {"prob": prob, "mean0": mean0, "var0": var0, "pred": pred, "R": R, "fitted": fitted, "c": c,
            "b": np.where(model.threshold_ok, model.b, 0.0)}


def residual_cov(R: np.ndarray, lam: float) -> np.ndarray:
    """Pairwise-complete second moments of the leave-one-out residuals, shrunk to the diagonal, made PD."""

    M = np.isfinite(R)
    R0 = np.where(M, R, 0.0)
    cnt = M.T.astype(float) @ M.astype(float)
    S = (R0.T @ R0) / np.maximum(cnt, 1.0)
    S = np.where(cnt >= MIN_PAIR, S, 0.0)
    diag = np.array([np.mean(R[M[:, j], j] ** 2) if M[:, j].any() else 0.0 for j in range(R.shape[1])])
    S[np.diag_indices_from(S)] = diag
    S = (1.0 - lam) * S + lam * np.diag(np.diag(S))
    S = (S + S.T) / 2.0
    w, V = np.linalg.eigh(S)
    floor = EIG_FLOOR * max(float(w.mean()), 1e-12)
    return (V * np.maximum(w, floor)) @ V.T


def rf_probs(parts: dict, S: np.ndarray, ti: int, probes: np.ndarray, y_probe: np.ndarray) -> np.ndarray:
    """Event probabilities for target ``ti`` after the returned probe readouts (S_ridge when none returned)."""

    prob = parts["prob"][ti].copy()
    D = len(prob)
    probes = np.asarray(probes, dtype=int)
    y = np.asarray(y_probe, dtype=float)
    keep = np.isfinite(y) & parts["fitted"][probes]
    if not keep.any():
        return prob
    P, e = probes[keep], y[keep] - parts["pred"][ti, probes[keep]]
    Spp = S[np.ix_(P, P)] + 1e-9 * np.eye(len(P))
    s = S[:D, :][:, P] - parts["b"][:, None] * S[D, P][None, :]
    W = np.linalg.solve(Spp, s.T)
    shift = e @ W
    red = np.einsum("jp,pj->j", s, W)
    f = parts["fitted"]
    m = parts["mean0"][ti] + shift
    v = np.maximum(parts["var0"][ti] - red, VAR_FLOOR * parts["var0"][ti])
    post = normal_cdf((parts["c"] - m) / np.sqrt(np.where(f, v, 1.0)))
    return np.where(f, post, prob)


# ---------------------------------------------------------------- one fold


def evaluate(d: dict, src: np.ndarray, tgt: np.ndarray, arms: str = "all") -> list[dict]:
    """Replay the arms on ``tgt`` with everything fitted on ``src``.

    ``arms="all"`` evaluates every arm; ``arms="k"`` only the fixed-k candidate and ridge-feedback arms (the
    inner choice of k); ``arms="parity"`` only the low-rank arms that the attribution study already computed
    (``C0``, ``E``, ``C_k``), so a parity check cannot print a G1 contrast. Returns one record per target with totals ``t_<arm>``, returned probe readouts
    ``r_<arm>`` and wasted (unmeasured) queries ``w_<arm>``.
    """

    Y, X, ev = d["Y"], d["X"], d["events"]
    order = tie(d["items"])
    model = BridgedTransferModel(rank=RANK, abs_gate=None, min_measured=MIN_MEASURED, impute_iters=IMPUTE).fit(Y[src], X[src])
    sc = CoherentScorer(model, Y[src])
    q = model.measured_rate
    ridge = arms in ("all", "k")
    if ridge:
        parts = ridge_parts(d, src, tgt, model)
        S1, S2 = residual_cov(parts["R"], LAMBDA_RF), residual_cov(parts["R"], LAMBDA_ALT)
    item = q * model.source_event_rate
    out = []
    for ti, c in enumerate(tgt):
        truth, row = ev[c], Y[c]
        rec = {"context": str(d["contexts"][c]), "group": str(d["groups"][c]), "events": int(truth.sum())}

        def top(score, n, exclude=()):
            s = np.asarray(score, dtype=float)
            picks = nominate(s, n, list(exclude), order)
            return picks[np.isfinite(s[picks])]

        def book(name, wells, probes=None):
            rec["t_" + name] = int(truth[wells].sum())
            rec["w_" + name] = int((~np.isfinite(row[wells])).sum())
            if probes is not None:
                rec["r_" + name] = int(np.isfinite(row[probes]).sum())

        st_rna = model.prior(X[c])
        coh = lambda st: q * sc.event_prob(st)  # noqa: E731
        p_rna = coh(st_rna)
        if arms in ("all", "parity"):
            book("C0", top(p_rna, BUDGET))
            prom = lambda st: q * model.event_prob(st)  # noqa: E731
            Pe = top(prom(st_rna), 4)
            Fe = top(prom(model.posterior(st_rna, Pe, row[Pe])), BUDGET - len(Pe), Pe)
            book("E", np.concatenate([Pe, Fe]), Pe)
        if arms == "all":
            book("A_item", top(item, BUDGET))
            book("S_ridge", top(q * parts["prob"][ti], BUDGET))
        for k in KS:
            P = top(p_rna, k)
            st1 = model.posterior(st_rna, P, row[P])
            F = top(coh(st1), BUDGET - len(P), P)
            book(f"C_{k}", np.concatenate([P, F]), P)
            if not ridge:
                continue
            p_ridge = q * parts["prob"][ti]
            Pr = top(p_ridge, k)
            for tag, S in (("RF", S1), ("RFs", S2)):
                if arms != "all" and tag == "RFs":
                    continue
                post = q * rf_probs(parts, S, ti, Pr, row[Pr])
                Fr = top(post, BUDGET - len(Pr), Pr)
                book(f"{tag}_{k}", np.concatenate([Pr, Fr]), Pr)
        out.append(rec)
    return out


def choose_k(d: dict, src: np.ndarray, fold: int) -> dict:
    """The probe count for the candidate and for ridge-plus-feedback, from replays on source patients only."""

    ids = hash_folds(d["groups"][src], f"g1-k:{fold}", INNER_FOLDS)
    tot = {a: {k: [] for k in KS} for a in ("C", "RF")}
    patients_overlap = 0
    for i in range(INNER_FOLDS):
        tr, te = src[ids != i], src[ids == i]
        patients_overlap += len(set(d["groups"][tr]) & set(d["groups"][te]))
        for rec in evaluate(d, tr, te, arms="k"):
            for a in tot:
                for k in KS:
                    tot[a][k].append(rec[f"t_{a}_{k}"])
    means = {a: {k: float(np.mean(v)) for k, v in by.items()} for a, by in tot.items()}
    pick = {a: max(KS, key=lambda k: (means[a][k], -k)) for a in means}
    return {"k_candidate": pick["C"], "k_ridge_feedback": pick["RF"], "inner_means": means,
            "inner_samples": len(tot["C"][KS[0]]), "inner_patient_overlap": patients_overlap}


def assemble(d: dict, fold: int, src: np.ndarray, tgt: np.ndarray, choice: dict) -> list[dict]:
    """Outer records of one fold: every arm at every k, plus the chosen-k aliases ``CAND``, ``RF``, ``RF_s``."""

    recs = evaluate(d, src, tgt, arms="all")
    for r in recs:
        r["fold"] = int(fold)
        kc, kr = choice["k_candidate"], choice["k_ridge_feedback"]
        for field in ("t", "w", "r"):
            if f"{field}_C_{kc}" in r:
                r[f"{field}_CAND"] = r[f"{field}_C_{kc}"]
            if f"{field}_RF_{kr}" in r:
                r[f"{field}_RF"] = r[f"{field}_RF_{kr}"]
            if f"{field}_RFs_{kr}" in r:
                r[f"{field}_RF_s"] = r[f"{field}_RFs_{kr}"]
        r["k_candidate"], r["k_ridge_feedback"] = kc, kr
    return recs
