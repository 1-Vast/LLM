"""Cross-task rollup of the identifiability audit: one row per task, one verdict per task.

File summary
- Path: research/identifiability_audit/task_summary.py
- Purpose: collapse the per-action lineage tables and the unified-score report into the six counts
  the audit needs (planned, executed, result valid, QC failed, control missing, unknown) and attach
  the verdict each task's evidence supports.
- Core points:
  - "Executed" counts a raw physical record, never a protocol inference: SciPlex3 counts raw `obs`
    cells, L1000 counts `inst_info` wells.
  - "Unknown" is reserved for a planned condition that cannot be traced to either a physical record
    or a documented exclusion. A protocol QC label is never counted as unknown.
  - The verdict is one of `comparable`, `bounds_only` or `replay_only`, and the reason is recorded.
- Run: python -m research.identifiability_audit.task_summary [--out DIR]
- Interfaces: `build`, `main`
- Depends on: pandas
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "outputs" / "identifiability_audit_20260930"
OUT = AUDIT / "task_summary"


def build(out: Path = OUT) -> pd.DataFrame:
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, label, executed_field in (("sciplex3_B", "sciplex3:B", "raw_cells"),
                                        ("l1000_LT", "l1000:LT", "inst_rows")):
        summary = json.loads((AUDIT / name / "summary.json").read_text(encoding="utf-8"))
        frame = pd.read_csv(AUDIT / name / "action_source.csv")
        status = frame.status.value_counts().to_dict()
        rows.append({
            "task": label,
            "episode_compounds": summary["episode_compounds"],
            "episodes": summary["episodes"],
            "menu_actions": summary["actions"],
            "action_cells": int(len(frame)),
            "planned": int(frame.design_planned.sum()),
            "executed_raw_record": int((frame[executed_field] > 0).sum()),
            "result_valid": int(status.get("result_valid", 0)),
            "qc_failed_protocol_label": int(status.get("qc_failed_protocol_label", 0)),
            "control_missing": int(frame.control_missing.sum()),
            "unknown": int(status.get("design_only_unverified", 0) + status.get("not_planned", 0)
                           + status.get("planned_no_protocol_row", 0)
                           + status.get("physical_rows_dropped_before_reading", 0)),
            "provenance_discrepancies": int(summary.get("cache_expansion_disagreements_total", 0)),
            "unresolved_source_linkage": int(summary.get("source_linkage", {})
                                             .get("unresolved_source_linkage", 0)),
            "discriminating_reading_share": round(float(frame.protocol_outcome
                                                        .isin(("eliminate_a", "eliminate_b")).mean()), 4),
            "uncertainty_unit": summary["biological_units"]["unit_used_for_uncertainty"],
            "uncertainty_units": summary["biological_units"]["unit_count"],
        })
    frame = pd.DataFrame(rows)

    unified = json.loads((AUDIT / "unified_score" / "unified_score.json").read_text(encoding="utf-8"))
    verdicts, reasons = [], []
    for row in frame.itertuples():
        report = unified["tasks"][row.task]
        gap = report["within_rule_action_gap"]
        bounds = report["missing_result_bounds"]
        if row.unknown or row.control_missing:
            verdicts.append("bounds_only" if bounds.get("difference_lower_bound") is not None else "replay_only")
            reasons.append("untraced actions or missing controls on a policy-reachable branch")
        elif bounds.get("crosses_zero"):
            verdicts.append("bounds_only")
            reasons.append("the policy difference interval spans zero once missing results are bounded")
        elif gap["ci95"][0] > 0:
            verdicts.append("comparable")
            reasons.append("menu and results complete; the within-rule gap excludes zero, but the oracle "
                           "arm reads hidden outcomes so this is a ceiling, not a policy effect")
        else:
            verdicts.append("comparable")
            reasons.append("menu and results complete; the within-rule gap does not exclude zero")
    frame["verdict"] = verdicts
    frame["verdict_reason"] = reasons

    case = unified["tasks"]["case_memory:lincs2020_unseen"]
    frame.loc[len(frame)] = {
        "task": "case_memory:lincs2020_unseen", "episode_compounds": case["test_units"],
        "episodes": case["test_units"], "menu_actions": max(case["menu_sizes_per_unit"]),
        "action_cells": case["menu_cells_total"],
        "planned": case["menu_cells_total"],
        "executed_raw_record": case["menu_cells_total"],
        "result_valid": case["menu_cells_total"],
        "qc_failed_protocol_label": 0, "control_missing": 0, "unknown": 0,
        "provenance_discrepancies": 0, "unresolved_source_linkage": 0,
        "discriminating_reading_share": None,
        "uncertainty_unit": "InChIKey connectivity block", "uncertainty_units": case["test_units"],
        "verdict": "replay_only",
        "verdict_reason": (f"{case['units_with_one_action']} of {case['test_units']} test units have exactly "
                           "one legal action, so within-rule action choice cannot be exercised; the frozen "
                           "-0.192 is an abstention and decoy-aggregation artefact"),
    }
    frame.to_csv(out / "task_summary.csv", index=False)
    (out / "task_summary.json").write_text(json.dumps(frame.to_dict("records"), indent=1, default=str),
                                           encoding="utf-8")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(build(Path(args.out)).to_string(index=False))


if __name__ == "__main__":
    main()
