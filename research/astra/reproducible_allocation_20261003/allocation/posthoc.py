"""POST HOC summary of the allocation replay: time-matched contrasts and compact resource tables.

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/posthoc.py
- Purpose: answer, after the replay, how arms compare at equal elapsed rounds and what each arm
  consumes by branch under both plate models, without re-reading any outcome
  (`plan_addendum_1.json`).
- Core points:
  - Inputs are only `results/replay.json` (per-line confirmed discoveries) and
    `receipts/accounting.json`; nothing is simulated again and no ticket is taken.
  - Contrasts use the frozen `verdict.contrast` (stratified line bootstrap, 10,000, seed 20261003)
    and are labelled POST HOC and EXPLORATORY.
  - Outputs are never overwritten (refusal if they exist).
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.allocation.posthoc`.
- Depends on: numpy; research.astra.feedback_validation_20261003.verdict (imported only).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from research.astra.feedback_validation_20261003.verdict import contrast

HERE = Path(__file__).resolve().parent
PLATE_WELLS = 1536
STATUS = "POST HOC, EXPLORATORY (plan_addendum_1.json): computed from written replay outputs; no outcome read"
TIME_MATCHED = {
    "T1_verify_hits_R1_minus_fixed_split_R1__2_vs_2_rounds": ("verify_hits_terminal_R1", "fixed_split_dev_R1"),
    "T2_verify_hits_R2_minus_fixed_split_R1__3_vs_2_rounds": ("verify_hits_terminal_R2", "fixed_split_dev_R1"),
    "T3_verify_hits_R1_minus_paired_R1__2_vs_1_rounds": ("verify_hits_terminal_R1", "paired_full_R1"),
    "T4_fixed_split_R1_minus_paired_R1__2_vs_1_rounds": ("fixed_split_dev_R1", "paired_full_R1"),
}
MAIN = ("screen_only", "paired_full", "verify_hits_terminal", "fixed_split_dev", "conf_per_cost", "random_verify_hits",
        "feedback_verify_hits", "feedback_paired", "verify_hits_noterminal")
BRANCH_FIELDS = ("orientation_measurements", "dose_points", "combination_wells", "custom_plates", "custom_control_wells",
                 "custom_single_anchor_wells", "custom_single_library_wells", "native_plates", "native_combination_wells",
                 "native_purchased_combination_wells")


def main() -> int:
    targets = [HERE / "results/posthoc_time_matched.json", HERE / "results/summary_tables.json"]
    if any(p.exists() for p in targets):
        raise SystemExit(f"REFUSED: outputs exist: {[str(p) for p in targets if p.exists()]}")
    replay = json.loads((HERE / "results/replay.json").read_text(encoding="utf-8"))
    accounting = json.loads((HERE / "receipts/accounting.json").read_text(encoding="utf-8"))["units"]
    out = {"status": STATUS, "contrasts": {}}
    tables = {"status": STATUS, "units": {}}
    for unit, block in replay["units"].items():
        per_line = block["per_line_confirmed"]
        keys = sorted(per_line["screen_only"])
        strata = np.array([k.split("|")[0] for k in keys])
        arr = {arm: np.array([per_line[arm][k] for k in keys]) for arm in per_line}
        out["contrasts"][unit] = {name: dict(contrast(arr[x], arr[y], strata), rounds={
            x: block["table"][x]["scheduled_rounds"], y: block["table"][y]["scheduled_rounds"]})
            for name, (x, y) in TIME_MATCHED.items()}
        rows = {}
        for arm in tuple(block["table"]):
            t, a = block["table"][arm], accounting[unit][arm]
            tot = a["total"]
            rows[arm] = {
                "confirmed": t["confirmed"], "screens": t["screens"], "screen_hits": t["screen_hits"],
                "verifications": t["verifications"], "spent": t["spent"], "budget": t["budget"],
                "remainder_unavoidable": t["remainder_unavoidable"], "remainder_avoidable": t["remainder_avoidable"],
                "scheduled_rounds": t["scheduled_rounds"], "min_protocol_days": t["min_protocol_days"],
                "by_branch": {b: {f: a["by_branch"][b][f] for f in BRANCH_FIELDS} for b in ("screen", "verify")},
                "custom_plates_branch_separate": tot["custom_plates"],
                "custom_plates_joint_diagnostic": a["custom_joint_plates_diagnostic"],
                "custom_used_wells": tot["custom_control_wells"] + tot["custom_single_anchor_wells"]
                + tot["custom_single_library_wells"] + tot["custom_combination_wells"],
                "custom_plate_wells": PLATE_WELLS * tot["custom_plates"],
                "native_plates": tot["native_plates"],
                "native_used_wells": tot["native_control_wells"] + tot["native_single_agent_wells"]
                + tot["native_combination_wells"],
                "native_plate_wells": PLATE_WELLS * tot["native_plates"],
                "native_share_of_combination_wells_purchased": tot["native_purchased_combination_wells"]
                / tot["native_combination_wells"] if tot["native_combination_wells"] else None,
                "failed_measurements": tot["failed_measurements"],
            }
        tables["units"][unit] = rows
    targets[0].write_text(json.dumps(out, indent=1), encoding="utf-8")
    targets[1].write_text(json.dumps(tables, indent=1), encoding="utf-8")
    for unit in out["contrasts"]:
        for name, c in out["contrasts"][unit].items():
            print(unit, name, c["sum_x"], c["sum_y"], round(c["relative_gain"], 4),
                  [round(v, 4) for v in c["relative_gain_ci"]], c["better"], c["worse"])
    for unit, rows in tables["units"].items():
        print("=====", unit)
        for arm in MAIN:
            r = rows[arm]
            print(arm, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "by_branch"})
            for b in ("screen", "verify"):
                print("   ", b, r["by_branch"][b])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
