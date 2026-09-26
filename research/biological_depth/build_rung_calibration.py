"""Assemble the calibration file virtual_cell.response_rung reads, from recorded results only.

File summary
- Path: research/biological_depth/build_rung_calibration.py
- Purpose: combine the served arm's cross-conformal quantiles and coverage, the acceptance rule
  written in calibration_spec.json, and the informativeness comparison against the
  average-response (systematic) arm into one file beside the signature library.
- Core points:
  - A readout is informative only when its mean calibrated width is at most 0.95 of the
    systematic arm's; this gate was added after the widths were seen, and it can only
    withhold readouts, never widen a claim.
  - Every number comes from a result file named in the output's provenance block.
- Run: python research/biological_depth/build_rung_calibration.py --audit-dir <dir> --arm knn_chem
       --output data/virtual_cell/sciplex3_signature_library/calibration.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INFORMATIVE_RATIO = 0.95


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--arm", default="knn_chem")
    parser.add_argument("--baseline", default="systematic")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report_path = args.audit_dir / f"calibration_{args.arm}.json"
    baseline_path = args.audit_dir / f"calibration_{args.baseline}.json"
    serving_path = args.audit_dir / f"serving_quantiles_{args.arm}.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    serving = json.loads(serving_path.read_text(encoding="utf-8"))
    ratio = {r: report["mean_width"][r] / baseline["mean_width"][r] for r in report["mean_width"]}
    out = {
        "level": serving["level"], "strata": serving["strata"], "quantiles": serving["quantiles"],
        "gene_sets": serving["gene_sets"], "coverage": report["coverage"],
        "acceptance": {"per_readout_minimum": 0.70, "overall_passed": report["passed"],
                       "rule": "research/biological_depth/calibration_spec.json"},
        "informative": {r: bool(v <= INFORMATIVE_RATIO) for r, v in ratio.items()},
        "width_ratio_to_average_response": ratio,
        "informative_rule": (f"mean calibrated width at most {INFORMATIVE_RATIO} of the '{args.baseline}' arm's; "
                             "added after the widths were seen, and it only withholds readouts"),
        "arm": args.arm,
        "provenance": {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (report_path, baseline_path, serving_path)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    served = [r for r, ok in out["informative"].items() if ok]
    print(json.dumps({"served_readouts": served, "withheld": len(ratio) - len(served),
                      "overall_passed": report["passed"], "mean_coverage": report["mean_coverage"]}, indent=1))


if __name__ == "__main__":
    main()
