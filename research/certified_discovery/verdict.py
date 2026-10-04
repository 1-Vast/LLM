"""Registered verdicts for the certified-discovery protocol, computed from replay records.

File summary
- Path: research/certified_discovery/verdict.py
- Purpose: turn one or more replay directories into the protocol's PASS / FAIL verdicts and its
  registered secondary estimates. Frozen with the protocol, so the decision rule cannot move
  after the confirmatory outcomes are seen.
- Core points:
  - H1 (discovery): the certified dual-core loop, which pays for its audit, against static
    retrieval from history without any audit. Unit: target line. PASS iff the 95% percentile
    bootstrap interval of the mean per-line hit difference lies above zero.
  - H2 (certification): certified nominations of the dual-core arm. PASS iff the mean
    false-discovery proportion over lines x audit draws is <= alpha and its bootstrap upper
    bound is <= alpha + 0.05, and the yield-bound coverage is >= 1 - delta - 0.03.
  - The framework claim requires both. Secondary estimates are reported with intervals and
    never re-labelled as confirmatory.
- Interfaces: `verdicts`, `main` (python -m research.certified_discovery.verdict RUN [RUN...]).
- Depends on: numpy, `analysis`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import analysis

PRIMARY_ARM = "wm_full"
COMPARATOR = "history"


def _paired(table, left: str, left_variant: str, right: str, right_variant: str, lines) -> dict | None:
    if left not in table or right not in table:
        return None
    diff = np.array([table[left][l][left_variant] - table[right][l][right_variant] for l in lines])
    return {"sum": float(diff.sum()), "mean": float(diff.mean()), "ci_mean": analysis._bootstrap(diff),
            "lines_better": int((diff > 0).sum()), "lines_worse": int((diff < 0).sum())}


def verdicts(records: list[dict], alpha: float, delta: float) -> dict:
    table = analysis.per_line(records)
    lines = sorted(table[PRIMARY_ARM])
    summary = analysis.summarise(records, reference=COMPARATOR, focus=PRIMARY_ARM)
    h1 = _paired(table, PRIMARY_ARM, "certify_hits", COMPARATOR, "exploit_hits", lines)
    arm = summary["arms"][PRIMARY_ARM]
    h2_fdr = arm["fdr"] <= alpha and arm["fdr_ci"][1] <= alpha + 0.05
    h2_cover = arm["yield_coverage"] >= 1 - delta - 0.03
    out = {
        "lines": len(lines), "alpha": alpha, "delta": delta,
        "H1": {**h1, "verdict": "PASS" if h1["ci_mean"][0] > 0 else "FAIL",
               "rule": "95% bootstrap CI of mean per-line (wm_full[certify] - history[exploit]) above 0"},
        "H2": {"fdr": arm["fdr"], "fdr_ci": arm["fdr_ci"], "yield_coverage": arm["yield_coverage"],
               "nominated_total": arm["nominated_total"], "nominated_true_total": arm["nominated_true_total"],
               "lines_with_nominations": arm["lines_with_nominations"],
               "verdict": "PASS" if (h2_fdr and h2_cover) else "FAIL",
               "rule": f"FDR <= {alpha} with upper bound <= {alpha + 0.05}; coverage >= {1 - delta - 0.03:.2f}"},
    }
    out["framework"] = "SUPPORTED" if out["H1"]["verdict"] == out["H2"]["verdict"] == "PASS" else "NOT_SUPPORTED"
    secondary = {
        "S1_feedback": _paired(table, "wm_full", "exploit_hits", "wm_static", "exploit_hits", lines),
        "S2a_context": _paired(table, "wm_full", "exploit_hits", "wm_nocontext", "exploit_hits", lines),
        "S2b_context_vs_shuffled": _paired(table, "wm_full", "exploit_hits", "wm_shuffled", "exploit_hits", lines),
        "S3_uncertainty": _paired(table, "wm_full", "exploit_hits", "wm_greedy", "exploit_hits", lines),
        "S5_price_of_certification": _paired(table, "wm_full", "exploit_hits", "wm_full", "certify_hits", lines),
        "S6_llm_knowledge": _paired(table, "llm_blind", "exploit_hits", "wm_menu_random", "exploit_hits", lines),
        "S7_llm_planner": _paired(table, "llm_named", "exploit_hits", "wm_full", "exploit_hits", lines),
        "S9_vs_random": _paired(table, "wm_full", "certify_hits", "random", "exploit_hits", lines),
        "S9_exploit_vs_history": _paired(table, "wm_full", "exploit_hits", "history", "exploit_hits", lines),
    }
    secondary["S4_optimizers_curse"] = {
        "claimed_over_realised": arm.get("claimed_over_realised"), "ci": arm.get("claimed_over_realised_ci"),
        "predicted_hits": arm.get("predicted_hits_total"), "predicted_true": arm.get("predicted_true_total"),
        "predicted_claimed_true": arm.get("predicted_claimed_true_total"),
    }
    secondary["S8_certification_under_llm"] = {
        name: {"fdr": summary["arms"][name]["fdr"], "fdr_ci": summary["arms"][name]["fdr_ci"],
               "yield_coverage": summary["arms"][name]["yield_coverage"]}
        for name in ("llm_named", "llm_blind", "llm_anonymous") if name in summary["arms"]
    }
    out["secondary"] = secondary
    out["ladder"] = {name: {"exploit": v["exploit_hits_total"], "certify": v["certify_hits_total"],
                            "recall_exploit": v["recall_exploit"], "fdr": v["fdr"],
                            "seconds_per_campaign": v["seconds_per_campaign"],
                            "wells_per_campaign": v["wells_per_campaign"], "days_per_campaign": v["days_per_campaign"]}
                     for name, v in summary["arms"].items()}
    out["total_line_hits"] = summary["total_line_hits"]
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--delta", type=float, default=0.1)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    records = [record for run in args.runs for record in analysis.load(Path(run))]
    result = verdicts(records, args.alpha, args.delta)
    text = json.dumps(result, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(json.dumps({"H1": result["H1"]["verdict"], "H2": result["H2"]["verdict"], "framework": result["framework"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
