"""Independent ledger accounting and decision-boundary audit after replay."""
import gzip
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from maestro.campaign_budget import CampaignBudget
import study as S


def main():
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    for relative, digest in frozen["sha256"].items():
        assert S.C.sha256(ROOT / relative) == digest, relative
    S.C.verify_sources()
    inherited = S.R.verify_execution()
    rows = pd.read_csv(HERE / "ROWS.csv").set_index(["drug", "arm"])
    budget = CampaignBudget(total=18, measurement_cost=1, turnaround_cost=2, unit="declared_read_equivalents")
    checked = 0
    maximum_metric_error = 0.0
    for name in ("LEDGER.jsonl.gz", "GATED_LEDGER.jsonl.gz"):
        with gzip.open(HERE / name, "rt", encoding="utf-8") as stream:
            for line in stream:
                ledger = json.loads(line)
                row = rows.loc[(ledger["drug"], ledger["arm"])]
                purchases = ledger["purchases"]
                events = ledger["events"]
                assert len(events) <= 2
                cost = budget.require_feasible(len(purchases), len(events), other_cost=0)
                assert cost == ledger["resource"] == row.resource
                bought = [item["line"] for item in purchases]
                assert len(set(bought)) == len(bought)
                assert not set(item["line_id"] for item in purchases).intersection(ledger["target_lines"])
                assert [line for event in events for line in event["plan"]] == bought
                for event in events:
                    assert len(event["plan"]) == len(event["values"]) == len(event["predicted_gains"])
                prediction = np.array(ledger["prediction"])
                truth = np.array(ledger["truth"])
                selected = np.argsort(prediction, kind="stable")[:10]
                assert ledger["selected"] == [ledger["target_lines"][index] for index in selected]
                utility = -float(truth[selected].mean())
                maximum_metric_error = max(maximum_metric_error, abs(utility - row.utility))
                assert abs(utility - row.utility) < 1e-12
                assert abs(utility - 0.001 * cost - row.net_utility) < 1e-12
                sd = np.array(ledger["posterior_sd"])
                scores = [float(np.max(np.abs(truth[selected] - prediction[selected]) / sd[selected]))]
                if len(events) == 2:
                    first = ledger["first_decision"]
                    fsel = np.argsort(first["prediction"], kind="stable")[:10]
                    scores.append(float(np.max(np.abs(np.array(first["truth"])[fsel] - np.array(first["prediction"])[fsel]) /
                                               np.array(first["posterior_sd"])[fsel])))
                    assert events[0]["plan"] == [p["line"] for p in first["purchases"]]
                assert abs(max(scores) - row.path_standardized_error) < 1e-10
                if ledger["arm"] == "gated_two_stage":
                    gate = ledger["gate"]
                    proceed = gate["lower_gain_estimate"] > gate["incremental_cost"]
                    assert len(events) == (2 if proceed else 1)
                    assert len(purchases) == (14 if proceed else 4)
                checked += 1
    assert checked == len(rows) == 8424
    output = {"status": "PASS", "ledgers_checked": checked, "maximum_utility_error": maximum_metric_error,
              "source_and_code_hashes_match": True, "resource_budget": budget.__dict__,
              "duplicate_purchases": 0, "terminal_purchases": 0,
              "note": "Zero other_cost is the declared scenario; compute and pre-existing assay costs are not authenticated procurement prices.",
              "analysis_dependency_audit": {"scope": "Postexecution verification of the existing transitive pin, not a new preregistration.",
                                            "chain": "FREEZE.json -> prior CALIBRATION_FREEZE.json -> execution_sha256.run.py",
                                            "prior_run_sha256": S.C.sha256(S.PRIOR / "run.py"),
                                            "inherited_expected_sha256": inherited["execution_sha256"]["run.py"]},
              "output_sha256": {name: S.C.sha256(HERE / name) for name in ("RESULTS.json", "ROWS.csv", "GATED_LEDGER.jsonl.gz")}}
    result = json.loads((HERE / "RESULTS.json").read_text())
    coverage = {}
    for arm, entry in result["reliability"].items():
        coverage[arm] = {}
        for subgroup, nkey, pkey in (("all", "n", "selected_path_coverage"),
                                     ("active", "active_n", "active_selected_path_coverage")):
            n, rate = entry[nkey], entry[pkey]
            count = round(n * rate)
            z = 1.959963984540054
            center = (rate + z * z / (2 * n)) / (1 + z * z / n)
            radius = z * np.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / (1 + z * z / n)
            coverage[arm][subgroup] = {"n": n, "covered": count,
                                       "wilson95_descriptive": [float(center - radius), float(center + radius)]}
    output["coverage_uncertainty_audit"] = {"scope": "Postexecution descriptive Wilson intervals treating drugs as independent; mechanism dependence is not corrected. Not a reliability certificate or changed success rule.", "arms": coverage}
    S.dump(HERE / "VERIFIED.json", output)
    print(json.dumps(output))


if __name__ == "__main__":
    main()
