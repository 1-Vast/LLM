"""Rebuild frozen repeat contrasts with CSV projection and independent arithmetic."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
OLD = ROOT / "research/context_probe_20261011"
RAW = ROOT / "data/external/prism_19q4/raw"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check(actual, expected):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (set(actual) - set(expected), set(expected) - set(actual))
        for key, value in expected.items():
            check(actual[key], value)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), (len(actual), len(expected))
        for left, right in zip(actual, expected):
            check(left, right)
    elif isinstance(expected, float):
        assert actual is not None and math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def pairs(number):
    return number * (number - 1) // 2


def verify(output):
    output = Path(output).resolve()
    freeze, receipt = read(output / "FREEZE.json"), read(output / "RECEIPT.json")
    gate_path = HERE / "METADATA_VERIFICATION.json"
    gate = read(gate_path)
    assert gate["status"] == "PASS_INDEPENDENT_METADATA_AUDIT"
    assert gate["secondary_response_values_read"] == 0 and gate["intended_pairs"] == 10600
    assert sha(ROOT / gate["verifier_path"]) == gate["verifier_sha256"]
    required = [STUDY / "PROTOCOL.json", STUDY / "run.py", STUDY / "prepare.py", gate_path,
                OLD / "data/output.npz", OLD / "runs/fixed8/predictions.npz", RAW / "secondary-screen-logfold-change.csv"]
    for path in required:
        assert path.relative_to(ROOT).as_posix() in freeze["files"], path
    for relative, expected in freeze["files"].items():
        assert sha(ROOT / relative) == expected, relative
    for relative, expected in gate["files"].items():
        assert sha(ROOT / relative) == expected, relative
    assert receipt["freeze_sha256"] == sha(output / "FREEZE.json")
    for filename, key in (("ROWS.json", "rows_sha256"), ("RESULTS.json", "results_sha256")):
        assert sha(output / filename) == receipt[key]
    for key in ("new_model_fits", "new_llm_calls", "new_wet_measurements"):
        assert receipt[key] == 0

    cases, contexts = read(STUDY / "data/PAIR_CASES.json"), read(STUDY / "data/CONTEXTS.json")
    rows, result = read(output / "ROWS.json"), read(output / "RESULTS.json")
    assert len(cases) == len(rows) == receipt["intended_cases"] == 10600 and len(contexts) == 106
    selected_columns = {r[f"{side}_column"] for case in cases if case["eligible"]
                        for r in case["repeat_columns"] for side in ("left", "right")}
    selected_rows = {case["secondary_row_name"] for case in cases if case["eligible"]}
    # Only after the completed source/menu hash chain validates, admit fixed values.
    observed_rows, response_values = set(), {}
    with (RAW / "secondary-screen-logfold-change.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        positions = {i: name for i, name in enumerate(header) if name in selected_columns}
        for row in reader:
            assert len(row) == len(header) and row[0] not in observed_rows
            observed_rows.add(row[0])
            if row[0] in selected_rows:
                response_values[row[0]] = {name: float(row[i]) if row[i] not in ("", "NA") else math.nan for i, name in positions.items()}
    assert len(positions) == receipt["secondary_response_columns_materialized"]
    assert len(observed_rows) == receipt["secondary_response_rows"]
    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        primary = archive["y"]
    rebuilt = []
    for case, row in zip(cases, rows):
        fixed_values = response_values.get(case["secondary_row_name"], {})
        differences = []
        for repeat in case["repeat_columns"]:
            a, b = fixed_values.get(repeat["left_column"], math.nan), fixed_values.get(repeat["right_column"], math.nan)
            differences.append(a - b if math.isfinite(a) and math.isfinite(b) else None)
        finite = [d for d in differences if d is not None and math.isfinite(d)]
        expected_repeats, observed_repeats = len(differences), len(finite)
        positive, negative, zero = sum(d > 0 for d in finite), sum(d < 0 for d in finite), sum(d == 0 for d in finite)
        complete = expected_repeats >= 2 and expected_repeats == observed_repeats
        if not expected_repeats:
            status = "NO_METADATA_PAIR"
        elif not complete:
            status = "INCOMPLETE_REPEAT_OBSERVATIONS"
        elif positive * negative:
            status = "DIRECTION_DISAGREEMENT"
        elif zero == expected_repeats:
            status = "ALL_ZERO_TIES"
        elif zero:
            status = "TIES_WITH_ONE_DIRECTION"
        else:
            status = "STABLE_OPPOSES_PRIOR_ORDER" if positive else "STABLE_SUPPORTS_PRIOR_ORDER"
        primary_difference = float(primary[case["index"], case["left_index"]] - primary[case["index"], case["right_index"]])
        primary_difference = primary_difference if math.isfinite(primary_difference) else None
        nonzero_pairs = pairs(positive + negative)
        expected = {"case_id": case["case_id"], "context": case["context"], "index": case["index"],
            "eligible": case["eligible"], "eligibility_reason": case["reason"], "left_index": case["left_index"], "right_index": case["right_index"],
            "secondary_differences": differences, "expected_repeats": expected_repeats, "observed_repeats": observed_repeats,
            "complete": complete, "positive_repeats": positive, "negative_repeats": negative, "zero_repeats": zero,
            "nonzero_repeat_comparisons": nonzero_pairs, "discordant_repeat_comparisons": positive * negative,
            "tied_repeat_comparisons": pairs(observed_repeats) - nonzero_pairs,
            "missing_repeat_comparisons": pairs(expected_repeats) - pairs(observed_repeats),
            "mean_secondary_difference": fmean(finite) if finite else None,
            "min_abs_secondary_difference": min(map(abs, finite)) if finite else None,
            "primary_difference": primary_difference, "prior_difference": case["predicted_difference"],
            "prior_prediction_tied": case["predicted_difference"] == 0,
            "primary_opposes_prior_order": primary_difference > 0 if primary_difference is not None else None, "status": status}
        check(row, expected)
        assert nonzero_pairs + expected["tied_repeat_comparisons"] + expected["missing_repeat_comparisons"] == pairs(expected_repeats)
        rebuilt.append(expected)

    status_names = ("STABLE_OPPOSES_PRIOR_ORDER", "STABLE_SUPPORTS_PRIOR_ORDER", "DIRECTION_DISAGREEMENT", "ALL_ZERO_TIES", "TIES_WITH_ONE_DIRECTION")
    comparison_names = ("nonzero_repeat_comparisons", "discordant_repeat_comparisons", "tied_repeat_comparisons", "missing_repeat_comparisons")
    macro_names = ("repeat_discordance_fraction", "stable_opposes_fraction_complete", "primary_wrong_replication_fraction")
    ledger = []
    for context in contexts:
        intended = [r for r in rebuilt if r["context"] == context["context"]]
        eligible = [r for r in intended if r["eligible"]]
        complete = [r for r in eligible if r["complete"]]
        wrong = [r for r in complete if r["primary_opposes_prior_order"] is True]
        replicated = sum(r["status"] == "STABLE_OPPOSES_PRIOR_ORDER" for r in wrong)
        statuses = {name: sum(r["status"] == name for r in complete) for name in status_names}
        counts = {name: sum(r[name] for r in eligible) for name in comparison_names}
        assert len(intended) == 100 and sum(statuses.values()) == len(complete)
        ledger.append({"context": context["context"], "index": context["index"], "intended_pairs": len(intended),
            "metadata_eligible_pairs": len(eligible), "complete_pairs": len(complete), "incomplete_eligible_pairs": len(eligible)-len(complete),
            "statuses": statuses, **counts, "repeat_discordance_fraction": counts["discordant_repeat_comparisons"]/counts["nonzero_repeat_comparisons"] if counts["nonzero_repeat_comparisons"] else None,
            "stable_opposes_fraction_complete": statuses["STABLE_OPPOSES_PRIOR_ORDER"]/len(complete) if complete else None,
            "primary_wrong_complete_pairs": len(wrong), "replicated_primary_wrong_pairs": replicated,
            "primary_wrong_replication_fraction": replicated/len(wrong) if wrong else None})
    expected_result = {"scope": "Released, jointly processed, matched same-plate contrasts only; no inference or full-menu decision benefit",
        "contexts": len(ledger), "intended_pairs": len(rebuilt),
        "metadata_eligible_pairs": sum(r["metadata_eligible_pairs"] for r in ledger), "complete_pairs": sum(r["complete_pairs"] for r in ledger),
        "contexts_with_eligible_pairs": sum(r["metadata_eligible_pairs"] > 0 for r in ledger),
        "contexts_with_complete_pairs": sum(r["complete_pairs"] > 0 for r in ledger),
        "repeat_comparison_counts": {name: sum(r[name] for r in ledger) for name in comparison_names},
        "status_counts_complete": {name: sum(r["statuses"][name] for r in ledger) for name in status_names},
        "context_macro": {name: {"mean": fmean(r[name] for r in ledger if r[name] is not None) if any(r[name] is not None for r in ledger) else None,
                                  "contributing_contexts": sum(r[name] is not None for r in ledger)} for name in macro_names},
        "primary_wrong_complete_pairs": sum(r["primary_wrong_complete_pairs"] for r in ledger),
        "replicated_primary_wrong_pairs": sum(r["replicated_primary_wrong_pairs"] for r in ledger), "context_rows": ledger}
    check(result, expected_result)
    assert result["metadata_eligible_pairs"] == gate["metadata_eligible_pairs"]
    files = [output / name for name in ("FREEZE.json", "ROWS.json", "RESULTS.json", "RECEIPT.json")]
    files += [gate_path, HERE / "verify.py", STUDY / "tests/test_safety.py"]
    return {"status": "PASS_INDEPENDENT_REPLICATE_ARITHMETIC_AUDIT", "contexts": 106, "intended_pairs": 10600,
        "metadata_eligible_pairs": result["metadata_eligible_pairs"], "complete_pairs": result["complete_pairs"],
        "contexts_with_complete_pairs": result["contexts_with_complete_pairs"], "behavioral_safety_cases": 18,
        "reviewer_imports": "No prepare/run/selection/reduction/summary helpers imported; secondary values independently projected by csv.reader",
        "verified": ["unchanged historical pre-outcome metadata-review script, gate and final source/menu hashes",
            "all frozen intended pairs and every admitted same-plate contrast, missing value, sign, exact tie and magnitude",
            "combinatorial nonzero, discordant, tied and missing repeat-pair arithmetic",
            "all 106 context ledgers, completeness/status counts and unweighted context-macro denominators",
            "declared primary cross-screen contrast status and replication arithmetic"],
        "not_verified": ["raw QC/ComBat isolation or independent culture-start hierarchy", "sample-specific elapsed exposure linkage",
            "independent biological variance, mechanism origins, purchasable information value or framework effectiveness"],
        "scientific_scope": "Exposed, jointly processed same-plate assay-repeat reliability only; fixed8 remains stopped and production promotion remains NONE",
        "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in files}, "verifier_sha256": sha(__file__)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    report = verify(parser.parse_args().output)
    (HERE / "VERIFICATION.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "contexts", "intended_pairs", "metadata_eligible_pairs", "complete_pairs")}))
