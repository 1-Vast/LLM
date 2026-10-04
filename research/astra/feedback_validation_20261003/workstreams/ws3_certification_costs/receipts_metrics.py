"""WS3 receipt-level recomputation of certification metrics (read-only over frozen receipts).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/receipts_metrics.py
- Purpose: recompute, from the row-level campaign receipts of research/certified_discovery, the
  quantities the frozen analysis merges or omits: mean FDP with empty lists counted as 0, FDP
  conditional on a nonempty list, pooled precision, nomination frequency, per-list and
  simultaneous yield-bound coverage, and valid aggregate (Bonferroni, pooled Chernoff) bounds.
- Core points:
  - A "list" is one certify record (one audit draw of one campaign). Deterministic arms have 20
    draws per line; seeded arms (random, wm_menu_random) have 20 seeds x 1 draw per line.
  - Simultaneous coverage is evaluated per draw index j (the same j across all lines).
  - Exact per-line coverage probability of the hypergeometric bound is computed from the
    receipts' (shortlist N, audit n, shortlist hits K = audit_hits + remainder_hits).
  - Never writes into research/certified_discovery (frozen); output goes next to this file.
- Run: D:/anaconda/envs/maestro/python.exe research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/receipts_metrics.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import certify as cert  # noqa: E402  (frozen; import only)

RESULTS = ROOT / "research/certified_discovery/results"
OUT = Path(__file__).resolve().parent / "receipts_metrics.json"
RUNS = {
    "dev_v2": ["dev_20261003_v2"],
    "dev_llm_v2": ["dev_llm_20261003_v2"],
    "dev_llm_v1_INVALID": ["dev_llm_20261003_v1"],
    "dev_v1_kappa3_superseded": ["dev_20261003_v1"],
    "confirm_replay": ["confirm_almanac_20261003/replay"],
    "confirm_llm": ["confirm_almanac_20261003/llm"],
    "promoted_parity_almanac": ["promoted_parity_almanac_20261003"],
}
BOOT = 10_000


def load(run: str) -> list[dict]:
    with open(RESULTS / run / "campaigns.jsonl", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def hyper_pmf(x: int, N: int, K: int, n: int) -> float:
    if x < max(0, n - (N - K)) or x > min(n, K):
        return 0.0
    lc = lambda a, b: math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)
    return math.exp(lc(K, x) + lc(N - K, n - x) - lc(N, n))


_bound_cache: dict = {}


def bound(N: int, n: int, x: int, delta: float) -> int:
    key = (N, n, x, delta)
    if key not in _bound_cache:
        _bound_cache[key] = cert.yield_lower_bound(N, n, x, delta)
    return _bound_cache[key]


def exact_coverage(N: int, n: int, K: int, delta: float) -> float:
    """P over the uniformly random audit that bound(X) <= K - X (exact, hypergeometric)."""
    return float(sum(hyper_pmf(x, N, K, n) for x in range(0, min(n, K) + 1) if bound(N, n, x, delta) <= K - x))


def chernoff_lower_mu(x_obs: int, delta: float) -> float:
    """Smallest mu with exp(-mu) (e mu / x)^x > delta (Poisson-Chernoff upper tail, x >= mu)."""
    if x_obs == 0:
        return 0.0
    lo, hi = 0.0, float(x_obs)

    def tail(mu: float) -> float:
        if mu >= x_obs:
            return 1.0
        if mu <= 0:
            return 0.0
        return math.exp(-mu + x_obs * (1.0 + math.log(mu / x_obs)))

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if tail(mid) > delta:
            hi = mid
        else:
            lo = mid
    return hi


def boot_ci(values: np.ndarray, stat, seed: int = 20261003) -> list[float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.shape[0], size=(BOOT, values.shape[0]))
    stats = np.array([stat(values[i]) for i in idx])
    return [float(np.nanpercentile(stats, 2.5)), float(np.nanpercentile(stats, 97.5))]


def arm_metrics(records: list[dict]) -> dict:
    lines = sorted({r["line"] for r in records})
    L = len(lines)
    seeded = len(records) > L
    # lists[line] = list of (draw_index, cert record)
    by_line: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for r in records:
        for j, c in enumerate(r["certify"]):
            by_line[r["line"]].append(((r["seed"] if seeded else j), c))
    flat = [c for line in lines for _, c in by_line[line]]
    nom = np.array([c["nominated"] for c in flat], float)
    tru = np.array([c["nominated_true"] for c in flat], float)
    fdp = np.array([c["fdp"] for c in flat], float)
    nonempty = nom > 0
    alpha, delta = flat[0]["alpha"], flat[0]["delta"]
    # line-level arrays for bootstrap (unit = line)
    per_line = []
    for line in lines:
        cs = [c for _, c in by_line[line]]
        n_ = np.array([c["nominated"] for c in cs], float)
        t_ = np.array([c["nominated_true"] for c in cs], float)
        f_ = np.array([c["fdp"] for c in cs], float)
        ne = n_ > 0
        per_line.append([f_.mean(), (f_ * ne).sum(), ne.sum(), n_.sum(), t_.sum(), len(cs)])
    per_line = np.array(per_line)

    def cond_fdp(a):
        return a[:, 1].sum() / a[:, 2].sum() if a[:, 2].sum() else np.nan

    def precision(a):
        return a[:, 4].sum() / a[:, 3].sum() if a[:, 3].sum() else np.nan

    out = {
        "lines": L, "lists": len(flat), "lists_per_line": len(flat) / L, "alpha": alpha, "delta": delta,
        "fdr_mean_fdp_incl_empty": float(per_line[:, 0].mean()),
        "fdr_ci_lines": boot_ci(per_line, lambda a: a[:, 0].mean()),
        "share_lists_nonempty": float(nonempty.mean()),
        "lines_with_any_nomination": int((per_line[:, 2] > 0).sum()),
        "mean_list_size": float(nom.mean()),
        "mean_list_size_given_nonempty": float(nom[nonempty].mean()) if nonempty.any() else None,
        "fdp_given_nonempty": float(fdp[nonempty].mean()) if nonempty.any() else None,
        "fdp_given_nonempty_ci_lines": boot_ci(per_line, cond_fdp) if nonempty.any() else None,
        "pooled_precision": float(tru.sum() / nom.sum()) if nom.sum() else None,
        "pooled_precision_ci_lines": boot_ci(per_line, precision) if nom.sum() else None,
        "nominated_total_per_draw": float(nom.sum() / (len(flat) / L)),
        "nominated_true_total_per_draw": float(tru.sum() / (len(flat) / L)),
        "share_nonempty_with_any_false": float((fdp[nonempty] > 0).mean()) if nonempty.any() else None,
        "share_nonempty_majority_false": float((fdp[nonempty] >= 0.5).mean()) if nonempty.any() else None,
        "share_nonempty_all_false": float((fdp[nonempty] == 1.0).mean()) if nonempty.any() else None,
        "identity_check_fdr_equals_pnonempty_times_condfdp": float(nonempty.mean() * fdp[nonempty].mean()) if nonempty.any() else 0.0,
        "refusals": dict(Counter(str(c["refusal"] or "CERTIFIED") for c in flat)),
    }
    # ---- yield bound: per list, per line, simultaneous, aggregate
    cov = np.array([c["yield_covered"] for c in flat], bool)
    K_line = {}
    for line in lines:
        Ks = {(c["shortlist"], c["audit"], c["audit_hits"] + c["remainder_hits"]) for _, c in by_line[line]}
        K_line[line] = sorted(Ks)
    shortlist_constant = all(len(v) == 1 for v in K_line.values())
    out["yield"] = {
        "per_list_coverage": float(cov.mean()),
        "line_mean_coverage": float(np.mean([np.mean([c["yield_covered"] for _, c in by_line[l]]) for l in lines])),
        "share_bound_zero": float(np.mean([c["yield_bound"] == 0 for c in flat])),
        "sum_bound_per_draw": float(sum(c["yield_bound"] for c in flat) / (len(flat) / L)),
        "sum_remainder_hits_per_draw": float(sum(c["remainder_hits"] for c in flat) / (len(flat) / L)),
        "shortlist_hits_constant_within_campaign": shortlist_constant,
        "audit_fraction_values": sorted({round(c["audit"] / c["shortlist"], 6) for c in flat if c["shortlist"]}),
    }
    if shortlist_constant and not seeded:
        exact = {l: exact_coverage(*K_line[l][0][:2], K_line[l][0][2], delta) for l in lines}
        out["yield"]["exact_per_line_coverage_min"] = float(min(exact.values()))
        out["yield"]["exact_per_line_coverage_mean"] = float(np.mean(list(exact.values())))
        out["yield"]["exact_simultaneous_all_lines_if_independent"] = float(np.prod(list(exact.values())))
    # per draw index
    draws = sorted({j for l in lines for j, _ in by_line[l]})
    sim, sum_ok, slack, bonf_ok, bonf_sum, pooled_ok, pooled_bnd, truth_tot, naive_sum = [], [], [], [], [], [], [], [], []
    for j in draws:
        cs = [c for l in lines for jj, c in by_line[l] if jj == j]
        if len(cs) != L:
            continue
        sim.append(all(c["yield_covered"] for c in cs))
        sb = sum(c["yield_bound"] for c in cs)
        st = sum(c["remainder_hits"] for c in cs)
        sum_ok.append(sb <= st)
        slack.append(st - sb)
        naive_sum.append(sb)
        truth_tot.append(st)
        bb = [bound(c["shortlist"], c["audit"], c["audit_hits"], delta / L) for c in cs]
        bonf_sum.append(sum(bb))
        bonf_ok.append(all(b <= c["remainder_hits"] for b, c in zip(bb, cs)))
        fracs = {c["audit"] / c["shortlist"] for c in cs if c["shortlist"]}
        if len(fracs) == 1:
            f = fracs.pop()
            x = sum(c["audit_hits"] for c in cs)
            mu_l = chernoff_lower_mu(x, delta)
            pb = max(math.ceil(mu_l / f - 1e-9) - x, 0)  # total shortlist hits >= mu_L / f
            pooled_bnd.append(pb)
            pooled_ok.append(pb <= st)
    out["yield"]["by_draw_index"] = {
        "draw_indices": len(sim),
        "simultaneous_all_lines_covered_share": float(np.mean(sim)) if sim else None,
        "sum_of_per_line_bounds_le_total_share": float(np.mean(sum_ok)) if sum_ok else None,
        "sum_of_per_line_bounds_mean": float(np.mean(naive_sum)) if naive_sum else None,
        "total_remainder_hits_mean": float(np.mean(truth_tot)) if truth_tot else None,
        "min_slack_total_minus_sum_bounds": float(np.min(slack)) if slack else None,
        "bonferroni_delta_over_L_sum_mean": float(np.mean(bonf_sum)) if bonf_sum else None,
        "bonferroni_simultaneous_covered_share": float(np.mean(bonf_ok)) if bonf_ok else None,
        "pooled_chernoff_total_bound_mean": float(np.mean(pooled_bnd)) if pooled_bnd else None,
        "pooled_chernoff_covered_share": float(np.mean(pooled_ok)) if pooled_ok else None,
    }
    # ---- recorded laboratory cost (as written; see cost_audit for what it omits)
    out["recorded_cost"] = {
        "budget_experiments_per_line_mean": float(np.mean([r["budget"] for r in records])),
        "dose_points_per_campaign_mean": float(np.mean([r["dose_points"] for r in records])),
        "wells_per_campaign_mean": float(np.mean([r["wells"] for r in records])),
        "days": sorted({r["days"] for r in records}),
        "wells_per_point": sorted({r.get("spec", {}).get("wells_per_point", None) or -1 for r in records}),
    }
    if records[0].get("planner_events"):
        codes = Counter(e.get("code") or "VALID" for r in records for e in (r["planner_events"] or []))
        returned = [e.get("returned") for r in records for e in (r["planner_events"] or []) if e.get("returned") is not None]
        ks = [e.get("k") for r in records for e in (r["planner_events"] or [])]
        out["planner_events"] = {"codes": dict(codes), "returned_median": float(np.median(returned)) if returned else None,
                                 "returned_max": int(max(returned)) if returned else None,
                                 "k_median": float(np.median(ks))}
    return out


def main() -> int:
    result = {"generated_by": Path(__file__).name, "runs": {}}
    for label, runs in RUNS.items():
        records = [r for run in runs for r in load(run)]
        arms = sorted({r["arm"] for r in records})
        result["runs"][label] = {arm: arm_metrics([r for r in records if r["arm"] == arm]) for arm in arms}
        print(label, "done", flush=True)
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    key = ["fdr_mean_fdp_incl_empty", "share_lists_nonempty", "mean_list_size_given_nonempty",
           "fdp_given_nonempty", "pooled_precision"]
    for label, arms in result["runs"].items():
        for arm, m in arms.items():
            y = m["yield"]; d = y["by_draw_index"]
            print(f"{label:24s} {arm:18s} FDR {m['fdr_mean_fdp_incl_empty']:.3f} P(ne) {m['share_lists_nonempty']:.3f} "
                  f"size|ne {m['mean_list_size_given_nonempty'] or 0:.2f} FDP|ne {m['fdp_given_nonempty'] or 0:.3f} "
                  f"prec {m['pooled_precision'] or 0:.3f} cov {y['per_list_coverage']:.3f} sim {d['simultaneous_all_lines_covered_share']} "
                  f"sumOK {d['sum_of_per_line_bounds_le_total_share']} sumB {d['sum_of_per_line_bounds_mean']:.1f} "
                  f"tot {d['total_remainder_hits_mean']:.1f} bonf {d['bonferroni_delta_over_L_sum_mean']:.1f} "
                  f"pool {d['pooled_chernoff_total_bound_mean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
