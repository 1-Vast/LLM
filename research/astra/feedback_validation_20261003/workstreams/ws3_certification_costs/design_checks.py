"""WS3 design-based checks on the captured rerun: exact FDR per real shortlist, costs, stress tests.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/design_checks.py
- Purpose: using capture_<screen>.pkl from rerun_capture.py (frozen code, receipts reproduced
  exactly), compute what the 20 recorded audit draws can only estimate:
  A. cost of each terminal branch (exploit vs certify) in dose points, the audit's overlap with
     the exploit pick, and the cost of verifying nominations;
  B. the design-based FDR, nomination frequency, conditional FDP and coverage given each real
     shortlist, by Monte Carlo over B fresh uniform audits (the only randomness the theorem uses);
  C. synthetic stress tests of conformal selection + BH with the frozen tie rule;
  D. what optional stopping would do to the hypergeometric yield bound;
  E. whether seeded arms reuse the same audit positions across lines.
- Empirical checks are not proofs; they test the implementation against the theorem's claim.
- Run: D:/anaconda/envs/maestro/python.exe research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/design_checks.py
"""
from __future__ import annotations

import itertools
import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import certify as cert  # noqa: E402

ALPHA, DELTA = 0.2, 0.1
B_MC = 4000
SEEDED = {"random", "wm_menu_random"}


def load(screen: str) -> list[dict]:
    with open(HERE / f"capture_{screen}.pkl", "rb") as handle:
        return pickle.load(handle)


# --------------------------------------------------------------------------- vectorised selection
def select_many(scores: np.ndarray, hits: np.ndarray, audit_mask: np.ndarray, alpha: float) -> np.ndarray:
    """audit_mask: (B, N) bool. Returns (B, N) bool nominated (remainder members only).

    Same rule as cert.conformal_select: p_j = (1 + #{audit nulls with score >= s_j}) / (n + 1),
    then BH(alpha) over the remainder.
    """
    Bn, N = audit_mask.shape
    n = audit_mask.sum(axis=1)                                    # audit sizes
    null_audit = audit_mask & ~hits[None, :]
    ge = scores[None, :] >= scores[:, None]                       # ge[j, i]: s_i >= s_j
    counts = np.rint(null_audit.astype(np.float32) @ ge.T.astype(np.float32))  # exact small-integer counts
    p = (1.0 + counts) / (n[:, None] + 1.0)
    rem = ~audit_mask
    m = rem.sum(axis=1)
    p_rem = np.where(rem, p, np.inf)
    order = np.sort(p_rem, axis=1)
    ranks = np.arange(1, N + 1)[None, :]
    passing = order <= alpha * ranks / np.maximum(m[:, None], 1)
    passing &= np.isfinite(order)
    kstar = np.where(passing.any(axis=1), N - np.argmax(passing[:, ::-1], axis=1), 0)
    thresh = np.where(kstar > 0, alpha * kstar / np.maximum(m, 1), -1.0)
    return rem & (p <= thresh[:, None])


def validate_vectorised(rng) -> dict:
    worst = 0
    for trial in range(400):
        N = int(rng.integers(8, 60))
        n = int(rng.integers(1, N))
        scores = np.round(rng.normal(size=N), int(rng.integers(0, 3)))   # induce ties
        hits = rng.random(N) < rng.uniform(0.05, 0.6)
        masks = np.zeros((20, N), bool)
        for b in range(20):
            masks[b, rng.permutation(N)[:n]] = True
        mine = select_many(scores, hits, masks, ALPHA)
        for b in range(20):
            audit = np.flatnonzero(masks[b])
            rem = np.flatnonzero(~masks[b])
            sel, _ = cert.conformal_select(scores[audit], hits[audit], scores[rem], ALPHA)
            if n < cert.minimum_audit(ALPHA):
                continue
            ref = np.zeros(N, bool)
            ref[rem[sel]] = True
            worst += int((ref != mine[b]).any())
    return {"trials": 400 * 20, "disagreements_with_frozen_conformal_select": worst}


def design_fdr(scores, hits, n_audit, rng, B=B_MC) -> dict:
    N = scores.size
    masks = np.zeros((B, N), bool)
    perm = np.argsort(rng.random((B, N)), axis=1)[:, :n_audit]
    np.put_along_axis(masks, perm, True, axis=1)
    nominated = select_many(scores, hits, masks, ALPHA)
    size = nominated.sum(axis=1)
    false = (nominated & ~hits[None, :]).sum(axis=1)
    fdp = false / np.maximum(size, 1)
    ne = size > 0
    return {"fdr": float(fdp.mean()), "fdr_se": float(fdp.std(ddof=1) / math.sqrt(B)),
            "p_nonempty": float(ne.mean()), "fdp_given_nonempty": float(fdp[ne].mean()) if ne.any() else None,
            "mean_size_given_nonempty": float(size[ne].mean()) if ne.any() else None,
            "nominated": float(size.mean()), "nominated_true": float((size - false).mean()),
            "shortlist_hits": int(hits.sum()), "N": int(N), "n": int(n_audit)}


# --------------------------------------------------------------------------- A. costs
def cost_audit(records: list[dict]) -> dict:
    by_arm = defaultdict(list)
    for r in records:
        by_arm[r["arm"]].append(r)
    out = {}
    for arm, rs in sorted(by_arm.items()):
        w = [r["_ws3"] for r in rs]
        rec = np.array([r["dose_points"] for r in rs], float)
        exp_pts = np.array([x["shared_points"] + x["exploit_points"] for x in w], float)
        cert_pts = np.array([x["shared_points"] + np.mean(x["audit_points"]) for x in w], float)
        cert_min = np.array([x["shared_points"] + min(x["audit_points"]) for x in w], float)
        cert_max = np.array([x["shared_points"] + max(x["audit_points"]) for x in w], float)
        overlap = np.array([np.mean(x["audit_exploit_overlap"]) / max(x["exploit_n"], 1) for x in w])
        nom_pts = np.array([np.mean(x["nominated_points"]) for x in w])
        exp_hits = np.array([r["exploit"]["hits"] for r in rs], float)
        cert_hits = np.array([np.mean([c["hits"] for c in r["certify"]]) for r in rs], float)
        per_draw = np.array([[x["shared_points"] + a for a in x["audit_points"]] for x in w if len(x["audit_points"]) > 1], float)
        out[arm] = {
            "campaigns": len(rs),
            "recorded_dose_points_mean": float(rec.mean()),
            "recorded_equals_exploit_branch": bool(np.all(rec == exp_pts)),
            "exploit_branch_points_mean": float(exp_pts.mean()),
            "certify_branch_points_mean": float(cert_pts.mean()),
            "certify_minus_recorded_mean": float((cert_pts - rec).mean()),
            "certify_minus_recorded_relative": float((cert_pts - rec).mean() / rec.mean()),
            "certify_minus_recorded_campaign_range": [float((cert_min - rec).min()), float((cert_max - rec).max())],
            "within_campaign_draw_sd_points": float(per_draw.std(axis=1).mean()) if per_draw.size else None,
            "audit_points_per_experiment": float(np.mean([np.mean(x["audit_points"]) / max(np.mean(x["audit_n"]), 1) for x in w])),
            "exploit_points_per_experiment": float(np.mean([x["exploit_points"] / max(x["exploit_n"], 1) for x in w])),
            "audit_overlap_with_exploit_pick_share": float(overlap.mean()),
            "exploit_pick_inside_shortlist_share": float(np.mean([x["exploit_in_shortlist"] / max(x["exploit_n"], 1) for x in w])),
            "verification_points_if_nominations_verified_mean": float(nom_pts.mean()),
            "hits_per_1000_points_exploit": float(1000 * exp_hits.sum() / exp_pts.sum()),
            "hits_per_1000_points_certify": float(1000 * cert_hits.sum() / cert_pts.sum()),
            "score_ties_in_shortlist_mean": float(np.mean([x["score_ties_in_shortlist"] for x in w])),
        }
    return out


def h1_cost(records: list[dict]) -> dict:
    lines = defaultdict(dict)
    for r in records:
        if r["arm"] in ("wm_full", "history"):
            lines[r["line"]][r["arm"]] = r
    d_pts, d_hits = [], []
    for line, arms in lines.items():
        wf, hi = arms["wm_full"], arms["history"]
        wf_pts = wf["_ws3"]["shared_points"] + np.mean(wf["_ws3"]["audit_points"])
        d_pts.append(wf_pts - hi["dose_points"])
        d_hits.append(np.mean([c["hits"] for c in wf["certify"]]) - hi["exploit"]["hits"])
    d_pts, d_hits = np.array(d_pts), np.array(d_hits)
    return {"lines": len(d_pts), "wm_full_certify_minus_history_exploit_points_sum": float(d_pts.sum()),
            "points_diff_mean_per_line": float(d_pts.mean()), "points_diff_range": [float(d_pts.min()), float(d_pts.max())],
            "hits_diff_sum": float(d_hits.sum()),
            "corr_points_diff_hits_diff": float(np.corrcoef(d_pts, d_hits)[0, 1]) if d_pts.std() > 0 else None}


# --------------------------------------------------------------------------- B. design FDR per shortlist
def design_fdr_all(records: list[dict], rng) -> dict:
    out = {}
    by_arm = defaultdict(list)
    for r in records:
        if r["arm"] not in SEEDED:
            by_arm[r["arm"]].append(r)
    for arm, rs in sorted(by_arm.items()):
        rows = []
        for r in rs:
            x = r["_ws3"]
            res = design_fdr(x["scores"], np.asarray(x["shortlist_hits"], bool), int(x["audits"].shape[1]), rng)
            res["recorded_fdr_20_draws"] = float(np.mean([c["fdp"] for c in r["certify"]]))
            res["line"] = r["line"]
            rows.append(res)
        fdr = np.array([q["fdr"] for q in rows])
        se = np.array([q["fdr_se"] for q in rows])
        pne = np.array([q["p_nonempty"] for q in rows])
        nom = np.array([q["nominated"] for q in rows])
        tru = np.array([q["nominated_true"] for q in rows])
        cond = [(q["fdp_given_nonempty"], q["p_nonempty"]) for q in rows if q["fdp_given_nonempty"] is not None]
        worst = int(np.argmax(fdr))
        out[arm] = {
            "lines": len(rows), "B_per_line": B_MC,
            "design_fdr_mean_over_lines": float(fdr.mean()),
            "design_fdr_max_line": float(fdr.max()), "design_fdr_max_line_se": float(se[worst]),
            "max_line_z_above_alpha": float((fdr.max() - ALPHA) / max(se[worst], 1e-12)),
            "lines_fdr_point_estimate_above_alpha": int((fdr > ALPHA).sum()),
            "lines_fdr_above_alpha_by_3se": int((fdr - 3 * se > ALPHA).sum()),
            "p_nonempty_mean": float(pne.mean()),
            "fdp_given_nonempty_weighted": float(sum(c * p for c, p in cond) / max(sum(p for _, p in cond), 1e-12)) if cond else None,
            "pooled_precision": float(tru.sum() / nom.sum()) if nom.sum() else None,
            "expected_nominated_total": float(nom.sum()), "expected_true_total": float(tru.sum()),
            "recorded_20draw_fdr_mean": float(np.mean([q["recorded_fdr_20_draws"] for q in rows])),
            "worst_line": rows[worst],
        }
    return out


# --------------------------------------------------------------------------- C. synthetic stress tests
def stress(rng) -> list[dict]:
    """Exact (full enumeration) or MC design FDR for adversarial / tied shortlists."""
    cases = []
    configs = [
        ("random_scores", lambda N, K: (rng.random(N), _hits(N, K))),
        ("anti_informative", lambda N, K: (np.r_[np.zeros(K), np.arange(1, N - K + 1)].astype(float), np.r_[np.ones(K, bool), np.zeros(N - K, bool)])),
        ("all_tied", lambda N, K: (np.zeros(N), _hits(N, K))),
        ("informative", lambda N, K: (np.r_[np.arange(N - K, N), np.arange(0, N - K)].astype(float), np.r_[np.ones(K, bool), np.zeros(N - K, bool)])),
        ("two_level_ties_nulls_high", lambda N, K: (np.r_[np.zeros(K), np.ones(N - K)], np.r_[np.ones(K, bool), np.zeros(N - K, bool)])),
        ("hits_tied_with_top_nulls", lambda N, K: (np.r_[np.ones(K), np.ones(min(5, N - K)), np.zeros(N - K - min(5, N - K))], np.r_[np.ones(K, bool), np.zeros(N - K, bool)])),
    ]
    for (name, make), (N, n), K in itertools.product(configs, [(10, 5), (16, 8), (30, 15), (256, 128)], [0, 1, 3, 6]):
        if K > N:
            continue
        scores, hits = make(N, K)
        if math.comb(N, n) <= 20000:
            combos = list(itertools.combinations(range(N), n))
            masks = np.zeros((len(combos), N), bool)
            for i, c in enumerate(combos):
                masks[i, list(c)] = True
            exact = True
        else:
            masks = np.zeros((20000, N), bool)
            perm = np.argsort(rng.random((20000, N)), axis=1)[:, :n]
            np.put_along_axis(masks, perm, True, axis=1)
            exact = False
        nominated = select_many(scores, hits, masks, ALPHA)
        size = nominated.sum(axis=1)
        fdp = (nominated & ~hits[None, :]).sum(axis=1) / np.maximum(size, 1)
        cases.append({"case": name, "N": N, "n": n, "K": K, "exact_enumeration": exact, "fdr": float(fdp.mean()),
                      "p_nonempty": float((size > 0).mean())})
    return cases


def _hits(N, K):
    h = np.zeros(N, bool)
    h[:K] = True
    return h


# --------------------------------------------------------------------------- D. optional stopping
_BOUND: dict = {}


def _bound(N: int, t: int, x: int) -> int:
    if (N, t, x) not in _BOUND:
        _BOUND[(N, t, x)] = cert.yield_lower_bound(N, t, x, DELTA)
    return _BOUND[(N, t, x)]


def optional_stopping(rng, reps=4000) -> list[dict]:
    """Peek at the hypergeometric bound after every audit item; stop at the first 'useful' bound."""
    out = []
    for N, K, target in [(256, 10, 2), (256, 20, 6), (256, 8, 1)]:
        fixed_cov, stop_cov, stopped = 0, 0, 0
        for _ in range(reps):
            labels = np.zeros(N, bool)
            labels[rng.choice(N, K, replace=False)] = True
            order = rng.permutation(N)
            x = 0
            claim = None
            for t in range(1, N // 2 + 1):
                x += labels[order[t - 1]]
                bnd = _bound(N, t, int(x))
                if claim is None and bnd >= target:
                    claim = (bnd, K - x)
                    stopped += 1
                if t == N // 2:
                    fixed_cov += bnd <= K - x
                    if claim is None:
                        claim = (bnd, K - x)
            stop_cov += claim[0] <= claim[1]
        out.append({"N": N, "K_true": K, "stop_when_bound_at_least": target, "reps": reps,
                    "fixed_sample_coverage_n_half": fixed_cov / reps, "optional_stopping_coverage": stop_cov / reps,
                    "share_runs_that_stopped_early": stopped / reps, "nominal": 1 - DELTA})
    return out


# --------------------------------------------------------------------------- E. shared audit seeds
def shared_audit_positions(records: list[dict]) -> dict:
    out = {}
    for arm in sorted({r["arm"] for r in records}):
        groups = defaultdict(list)
        for r in records:
            if r["arm"] != arm:
                continue
            x = r["_ws3"]
            pos = {int(np.flatnonzero(x["shortlist"] == a)[0]) for a in x["audits"][0]}
            groups[(r["seed"], int(x["shortlist"].size))].append(frozenset(pos))
        pairs = same = 0
        for sets in groups.values():
            for i in range(len(sets)):
                for j in range(i + 1, len(sets)):
                    pairs += 1
                    same += sets[i] == sets[j]
        out[arm] = {"line_pairs_same_seed_same_shortlist_size": pairs, "identical_audit_rank_positions": same}
    return out


def main() -> int:
    rng = np.random.default_rng(20261003)
    result = {"alpha": ALPHA, "delta": DELTA, "vectorised_rule_check": validate_vectorised(rng)}
    print(result["vectorised_rule_check"], flush=True)
    for screen in ("oneil", "almanac"):
        records = load(screen)
        result[screen] = {"costs": cost_audit(records), "h1_cost": h1_cost(records),
                          "shared_audit_positions": shared_audit_positions(records)}
        print(screen, "costs done", flush=True)
        result[screen]["design_fdr"] = design_fdr_all(records, rng)
        print(screen, "design fdr done", flush=True)
    result["stress"] = stress(rng)
    result["optional_stopping"] = optional_stopping(rng)
    (HERE / "design_checks.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    for screen in ("oneil", "almanac"):
        for arm, d in result[screen]["design_fdr"].items():
            print(f"{screen:8s} {arm:20s} designFDR {d['design_fdr_mean_over_lines']:.4f} max {d['design_fdr_max_line']:.4f}"
                  f"(se {d['design_fdr_max_line_se']:.4f}) P(ne) {d['p_nonempty_mean']:.3f} FDP|ne {d['fdp_given_nonempty_weighted']}"
                  f" prec {d['pooled_precision']} rec20 {d['recorded_20draw_fdr_mean']:.4f}")
        for arm, c in result[screen]["costs"].items():
            print(f"{screen:8s} {arm:20s} rec {c['recorded_dose_points_mean']:.1f} cert {c['certify_branch_points_mean']:.1f} "
                  f"diff {c['certify_minus_recorded_mean']:+.1f} ({100 * c['certify_minus_recorded_relative']:+.2f}%) "
                  f"overlap {c['audit_overlap_with_exploit_pick_share']:.3f} verify {c['verification_points_if_nominations_verified_mean']:.1f} "
                  f"ties {c['score_ties_in_shortlist_mean']:.1f}")
        print(screen, "H1 cost", result[screen]["h1_cost"])
        print(screen, "shared audit positions", result[screen]["shared_audit_positions"])
    print("stress max fdr", max(c["fdr"] for c in result["stress"]))
    for c in result["optional_stopping"]:
        print(c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
