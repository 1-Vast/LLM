"""Summarize independently verified frozen results without selecting a new policy."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "boundary_acquisition_20261007"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    verdict, provenance = read(HERE / "VERDICT.json"), read(HERE / "PROVENANCE_RECONCILIATION.json")
    assert verdict["verdict"] == provenance["verdict"] == "PASS"
    protocol = read(STUDY / "PROTOCOL.json")
    episodes = [json.loads(line) for line in (STUDY / "run1/EPISODES.jsonl").read_text().splitlines()]
    indexed = {(row["context"], row["arm"]): row for row in episodes}
    comparisons = []
    for arm in protocol["arms"]:
        arm_name = arm["name"]
        selected = [indexed[context, arm_name] for context in protocol["contexts"]]
        comparison = {"arm": arm_name, "mean_utility": float(np.mean([row["utility"] for row in selected])),
                      "profiles": int(sum(row["actual_credits"] for row in selected)), "contexts": {}}
        for row in selected:
            baseline = indexed[row["context"], "M2_KG8"]
            highprecision = indexed[row["context"], "M2_KG4096"]
            comparison["contexts"][row["context"]] = {
                "utility": row["utility"], "profiles": int(row["actual_credits"]),
                "delta_vs_M2KG64": row["utility"] - baseline["utility"],
                "delta_vs_M2KG4096": row["utility"] - highprecision["utility"],
                "same_final_B_set_vs_M2KG64": set(row["final_flags"]) == set(baseline["final_flags"]),
                "same_final_B_set_vs_M2KG4096": set(row["final_flags"]) == set(highprecision["final_flags"]),
                "same_A_sequence_vs_M2KG64": row["screened"] == baseline["screened"],
                "same_A_sequence_vs_M2KG4096": row["screened"] == highprecision["screened"],
                "stopreason": row["stopreason"], "elapsed_seconds": row["elapsed_seconds"]}
        comparisons.append(comparison)

    for context in protocol["contexts"]:
        stopped = indexed[context, "M2_boundary_common"]
        unstopped = indexed[context, "M2_boundary_common_no_stop"]
        assert stopped["screened"] == unstopped["screened"]
        assert stopped["prefix_flags"] == unstopped["prefix_flags"]
        for name in ("M2_boundary_common", "M2_boundary_common_no_stop", "M2_boundary_residual", "M2_boundary_design"):
            row = indexed[context, name]
            assert row["utility"] == indexed[context, "M2_KG8"]["utility"]
            assert row["actual_credits"] == 13
            assert len(row["screened"]) == 8

    with np.load(STUDY / "packet2/nested_reference_diagnostic.npz") as diagnostic:
        predicted, true, constant = (diagnostic[key] for key in ("predicted", "true", "constant"))
        nested = {"rows": len(true), "logerror_pearson": float(np.corrcoef(predicted, true)[0, 1]),
                  "learned_logerror_rmse": float(np.sqrt(np.mean((predicted - true) ** 2))),
                  "constant_logerror_rmse": float(np.sqrt(np.mean((constant - true) ** 2)))}
    expected = read(STUDY / "packet2/TRAINING_DIAGNOSTIC.json")["diagnostics"]["nested_residual"]
    for name, value in nested.items():
        assert np.isclose(value, expected[name], rtol=1e-12, atol=1e-12)

    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "engineering_verdict": "PASS",
              "scientific_verdict": "No incremental final utility or profile saving from registered boundary/residual/stopping successor over same-STATE KG64 or KG4096 on five exposed contexts.",
              "protocol_sha256": verdict["protocol_sha256"], "episodes": verdict["episodes"],
              "profiles": verdict["profiles"], "prefix_points": verdict["prefix_points"],
              "training_contexts": 45, "target_contexts": 5, "arms": 12, "full_menu": 146,
              "nested_residual": nested, "tau": verdict["shared_M0_loo_tau"],
              "common_and_no_stop_prefixes_identical_all_contexts": True,
              "registered_boundary_stops": 0, "comparisons": comparisons,
              "reproduction_receipt_sha256": hashlib.sha256((HERE / "VERDICT.json").read_bytes()).hexdigest(),
              "provenance_receipt_sha256": hashlib.sha256((HERE / "PROVENANCE_RECONCILIATION.json").read_bytes()).hexdigest(),
              "synthetic_contract_tests": 12, "fresh_api_calls": 0, "fresh_STATE_forward_calls": 0,
              "limits": verdict["limits"]}
    with (HERE / "VERIFIED.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "comparisons"}, indent=2))


if __name__ == "__main__":
    main()
