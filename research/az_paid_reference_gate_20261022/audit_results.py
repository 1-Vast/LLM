"""Post-freeze independent verification; not experimental method or a fit.

No imports from the driver, metrics, prepare, or model implementation. The CLI
refuses all access unless --run-after-test-open is explicitly supplied.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = ROOT / "log/20261022/az_paid_reference_gate"
ARMS = ("bliss", "historical", "effect", "dose", "direct", "combo_direct",
        "effect_offset", "dose_offset", "direct_offset", "mixture", "enumerator")
ORDINARY = ("bliss", "historical", "dose", "combo_direct", "direct",
            "dose_offset", "direct_offset")
ENDPOINTS = ("mae", "utility")
N_BOOT, SEED, TOL = 10000, 20261022, 1e-12


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_assigned_masters(design):
    # Canonical identity order is independent of outcomes. DESIGN's stored
    # hash-ranking determines role membership, not bootstrap vector order.
    assigned = [str(x) for x in design["role_cells"]["test"]]
    require(len(assigned) == len(set(assigned)), "Duplicate assigned MASTER")
    return sorted(assigned)


def score_independent(y, prediction, episode, master, effect, valid, actions,
                      assigned, global_rows, minimum_coverage=.95):
    """All arguments describe the nominal test role, preserving global rows."""
    n = len(y)
    require(n > 0 and len(assigned) == len(set(assigned)), "Empty role/duplicate MASTER")
    require(all(len(a) == n for a in (prediction, episode, master, effect, valid, global_rows)),
            "Array length mismatch")
    require(effect.shape == (n, 2), "Expected two paid effects per row")
    require(len(set(global_rows.tolist())) == n, "Duplicate global row index")
    require(set(master.tolist()) <= set(assigned), "Unassigned MASTER in test")
    records, expected_actions = [], {}
    for ep in np.unique(episode):
        rows = np.flatnonzero(episode == ep)
        cells = set(master[rows].tolist())
        require(len(cells) == 1, "Episode crosses MASTERs")
        require(np.all(valid[rows] == valid[rows[0]]), "Validity varies within episode")
        good_input = bool(valid[rows[0]])
        finite = rows[np.isfinite(y[rows])]
        record = {"episode": int(ep), "master": str(master[rows[0]]),
                  "nominal_rows": len(rows), "input": good_input,
                  "finite_target_rows": 0, "forecast": False, "recommendation": False}
        if good_input:
            require(np.isfinite(prediction[rows]).all() and np.isfinite(effect[rows]).all(),
                    "Nonfinite prediction or paid effects on valid inputs")
            if len(rows) >= 5:
                excess = prediction[rows] - np.max(effect[rows], axis=1)
                ranked = rows[np.lexsort((global_rows[rows], -excess))[:5]]
                expected_actions[str(int(ep))] = [int(x) for x in global_rows[ranked]]
            if len(finite) >= 5:
                record.update(forecast=True, finite_target_rows=len(finite),
                              mae=float(np.mean(np.abs(y[finite] - prediction[finite]))))
            if len(rows) >= 5 and len(finite) == len(rows):
                true_excess = y[rows] - np.max(effect[rows], axis=1)
                oracle = float(np.mean(np.sort(true_excess)[-5:]))
                selected_global = expected_actions[str(int(ep))]
                lookup = {int(global_rows[r]): r for r in rows}
                selected = np.array([lookup[r] for r in selected_global], dtype=int)
                utility = float(np.mean(y[selected] - np.max(effect[selected], axis=1)))
                record.update(recommendation=True, utility=utility,
                              oracle_utility=oracle, regret=oracle - utility)
        records.append(record)
    # Compare the complete nominal action map, including target-incomplete panels.
    require(actions == expected_actions, "Sealed actions differ from prediction-only global-row top5")
    stages = ("input", "forecast", "recommendation")
    counts = {s: [sum(r[s] and r["master"] == m for r in records) for m in assigned]
              for s in stages}
    per_master = {}
    for metric in ("mae", "utility", "oracle_utility", "regret"):
        stage = "forecast" if metric == "mae" else "recommendation"
        per_master[metric] = []
        for m in assigned:
            values = [r[metric] for r in records if r["master"] == m and r[stage]]
            per_master[metric].append(float(np.mean(values)) if values else None)
    result = {metric: float(np.mean([v for v in values if v is not None]))
              if any(v is not None for v in values) else None
              for metric, values in per_master.items()}
    result.update(nominal_rows=n, nominal_episodes=len(records), assigned_masters=assigned,
                  per_master=per_master, per_master_episode_counts=counts)
    for stage in stages:
        count = sum(r[stage] for r in records)
        absent = [m for m, c in zip(assigned, counts[stage]) if c == 0]
        result[stage] = {"episodes": count, "episode_coverage": count / len(records),
                         "zero_contributor_masters": absent,
                         "coverage_pass": count / len(records) >= minimum_coverage and not absent}
    finite_count = sum(r["finite_target_rows"] for r in records)
    result["forecast"].update(mae=result["mae"], finite_target_rows=finite_count,
                               finite_target_row_coverage=finite_count / n)
    result["forecast"]["coverage_pass"] &= finite_count / n >= minimum_coverage
    result["recommendation"].update({k: result[k] for k in ("utility", "oracle_utility", "regret")})
    result["coverage_pass"] = all(result[s]["coverage_pass"] for s in stages)
    return result, records


def bootstrap_independent(candidate, baseline, higher_is_better=False):
    a, b = np.asarray(candidate, dtype=float), np.asarray(baseline, dtype=float)
    require(a.shape == b.shape and a.ndim == 1 and len(a) > 0 and
            np.isfinite(a).all() and np.isfinite(b).all(), "Unqualified paired MASTER vector")
    delta = a - b if higher_is_better else b - a
    rng = np.random.default_rng(SEED)
    sampled = delta[rng.integers(0, len(a), size=(N_BOOT, len(a)))].mean(axis=1)
    low, high = np.percentile(sampled, [2.5, 97.5])
    gain = float(np.mean(delta))
    return {"gain": gain, "mean": gain, "ci95": [float(low), float(high)],
            "lower": float(low), "upper": float(high), "n_masters": len(a),
            "n_boot": N_BOOT, "seed": SEED}


def recompute_gates(metrics, selection):
    covered = all(m["coverage_pass"] for m in metrics.values())
    gates = {"coverage": covered, "mae": False, "utility": False, "both": False}
    comparisons = {}
    if covered:
        for endpoint in ENDPOINTS:
            ordinary = selection["ordinary"][endpoint]["arm"]
            require(ordinary in ORDINARY, "Unregistered ordinary comparator")
            base = metrics[f"{ordinary}__{endpoint}"]
            candidate = metrics[f"effect__{endpoint}"]
            boot = bootstrap_independent(candidate["per_master"][endpoint],
                                         base["per_master"][endpoint], endpoint == "utility")
            gain = base["mae"] - candidate["mae"] if endpoint == "mae" else candidate["utility"] - base["utility"]
            headroom = base["mae"] if endpoint == "mae" else base["regret"]
            gates[endpoint] = bool(gain >= .02 and gain >= .1 * headroom and boot["lower"] > 0
                                   and (endpoint == "mae" or headroom > .02))
            comparisons[endpoint] = {"ordinary": ordinary, "candidate": "effect",
                                     "gain": gain, "baseline_headroom": headroom, "bootstrap": boot}
        gates["both"] = gates["mae"] and gates["utility"]
    return {"gates": gates, "comparisons": comparisons,
            "interpretation": "ordinary source-specific family gate; no new algorithm, agent or RSI claim"}


def compare_tree(actual, expected):
    errors, maxdiff = [], 0.0
    def visit(a, b, path):
        nonlocal maxdiff
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a) != set(b):
                errors.append({"path": path, "reason": "keys", "actual": sorted(a), "expected": sorted(b)})
            for key in sorted(set(a) & set(b)):
                visit(a[key], b[key], f"{path}/{key}")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                errors.append({"path": path, "reason": "length"})
            for i, (x, y) in enumerate(zip(a, b)):
                visit(x, y, f"{path}/{i}")
        elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
            diff = abs(float(a) - float(b))
            if not np.isfinite(diff) or diff > TOL:
                errors.append({"path": path, "actual": a, "expected": b, "absdiff": diff})
            maxdiff = max(maxdiff, diff)
        elif type(a) is not type(b) or a != b:
            errors.append({"path": path, "actual": a, "expected": b})
    visit(actual, expected, "")
    return {"passed": not errors, "maximum_absolute_numeric_difference": maxdiff,
            "tolerance": TOL, "mismatches": errors}


def verify_hashes(folder, root, synthetic=False):
    checks = []
    def check(path, expected, provenance):
        actual = digest(path)
        checks.append({"path": str(path), "provenance": provenance, "sha256": actual,
                       "expected_sha256": expected, "passed": actual == expected})
    seal = read_json(folder / "PREDICTIONS_SEAL.json")
    for name, field in (("TEST_PREDICTIONS.npz", "predictions_sha256"),
                        ("TEST_ACTIONS.json", "actions_sha256"), ("SELECTION.json", "selection_sha256")):
        check(folder / name, seal[field], "predictions seal")
    for receipt_name in ("INPUTS_RECEIPT.json", "TEST_TARGETS_RECEIPT.json"):
        receipt = read_json(folder / receipt_name)
        required = {"DATA.npz", "EPISODE_META.json", "ROWS.json"} if receipt_name == "INPUTS_RECEIPT.json" else {"TEST_TARGETS.npz"}
        require(required <= set(receipt["outputs_sha256"]), "Receipt omits required output hash")
        for name, expected in receipt["outputs_sha256"].items():
            path = (folder / name).resolve()
            require(path.is_relative_to(folder.resolve()), "Receipt path leaves phase")
            check(path, expected, receipt_name)
        links = {"design_sha256": folder / "DESIGN.json",
                 "protocol_sha256": folder / "MEASURED_PROTOCOL.md",
                 "schema_sha256": folder / "FEATURE_SCHEMA.json",
                 "code_sha256": root / "research/az_paid_reference_gate_20261022/prepare.py"}
        for field, path in links.items():
            if field in receipt:
                check(path, receipt[field], receipt_name)
    # The archive is deliberately not opened, decompressed, or rehashed here.
    if not synthetic:
        freeze = read_json(folder / "PRE_RESPONSE_FREEZE.json")
        for name, expected in freeze["files"].items():
            if name.endswith(".zip"):
                continue
            path = (root / name).resolve()
            require(path.is_relative_to(root.resolve()), "Freeze path leaves workspace")
            check(path, expected, "pre-response freeze")
    require(all(c["passed"] for c in checks), "Hash/seal verification failed")
    return checks


def audit(folder, root=ROOT, synthetic=False):
    hashes = verify_hashes(folder, root, synthetic)
    selection = read_json(folder / "SELECTION.json")
    actions = read_json(folder / "TEST_ACTIONS.json")
    assigned = canonical_assigned_masters(read_json(folder / "DESIGN.json"))
    meta = read_json(folder / "EPISODE_META.json")
    by_episode = {int(m["episode_id"]): m for m in meta}
    require(len(by_episode) == len(meta), "Duplicate metadata episode")
    # Access only these input arrays. Do not load full, without_mono, or DATA.y.
    with np.load(folder / "DATA.npz", allow_pickle=False) as data:
        ep, role = data["episode"], data["role"]
        effect, valid = data["effect"], data["valid_mask"]
    require(valid.dtype == np.bool_, "Validity must be boolean")
    rows = np.flatnonzero(role == "test")
    require(len(rows) > 0, "No test rows")
    cells = []
    for e in ep[rows]:
        item = by_episode[int(e)]
        require(item["role"] == "test", "Test metadata role mismatch")
        cells.append(str(item["cell"]))
    master = np.asarray(cells)
    for e in np.unique(ep[rows]):
        require(set(role[ep == e].tolist()) == {"test"}, "Episode leaks across roles")
        require(bool(by_episode[int(e)]["valid"]) == bool(valid[np.flatnonzero(ep == e)[0]]),
                "Metadata validity differs")
    with np.load(folder / "TEST_TARGETS.npz", allow_pickle=False) as target_file:
        y = target_file["y"]
    require(y.shape == ep.shape, "Target shape differs from input rows")
    keys = {f"{a}__{e}" for a in ARMS for e in ENDPOINTS}
    require(set(actions) == keys, "Unexpected action policy set")
    results, episode_records = {}, {}
    with np.load(folder / "TEST_PREDICTIONS.npz", allow_pickle=False) as prediction_file:
        require(set(prediction_file.files) == keys, "Unexpected prediction policy set")
        for key in sorted(keys):
            pred = prediction_file[key]
            require(pred.shape == ep.shape, "Prediction shape differs from input rows")
            results[key], episode_records[key] = score_independent(
                y[rows], pred[rows], ep[rows], master, effect[rows], valid[rows],
                actions[key], assigned, rows)
    gates = recompute_gates(results, selection)
    comparisons = {}
    if gates["gates"]["coverage"]:
        for endpoint in ENDPOINTS:
            for arm in ARMS:
                comparisons[f"effect_vs_{arm}__{endpoint}"] = bootstrap_independent(
                    results[f"effect__{endpoint}"]["per_master"][endpoint],
                    results[f"{arm}__{endpoint}"]["per_master"][endpoint], endpoint == "utility")
            comparisons[f"direct_vs_combo_direct__{endpoint}"] = bootstrap_independent(
                results[f"direct__{endpoint}"]["per_master"][endpoint],
                results[f"combo_direct__{endpoint}"]["per_master"][endpoint], endpoint == "utility")
    matches = {"metrics": compare_tree(results, read_json(folder / "TEST_METRICS.json")),
               "gates": compare_tree(gates, read_json(folder / "GATES.json"))}
    paired_path = folder / "ALL_PAIRED_COMPARISONS.json"
    if paired_path.exists():
        matches["paired_comparisons"] = compare_tree(
            comparisons, read_json(paired_path)["comparisons"])
    source_paths = [folder / n for n in ("TEST_PREDICTIONS.npz", "TEST_ACTIONS.json", "SELECTION.json",
                    "PREDICTIONS_SEAL.json", "TEST_TARGETS.npz", "TEST_METRICS.json", "GATES.json",
                    "DESIGN.json", "EPISODE_META.json", "INPUTS_RECEIPT.json", "TEST_TARGETS_RECEIPT.json")]
    return {"utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if all(m["passed"] for m in matches.values()) else "FAIL",
            "purpose": "post-freeze independent verification; not method, selection, or fitting",
            "synthetic": synthetic, "auditor_sha256": digest(Path(__file__)),
            "imports_experiment_modules": False, "model_fits": 0, "archive_accesses": 0,
            "data_arrays_read": ["episode", "role", "effect", "valid_mask"],
            "master_vector_order": "lexicographic MASTER ID; membership from frozen DESIGN",
            "source_hashes": {str(p): digest(p) for p in source_paths}, "hash_checks": hashes,
            "test_role_counts": {"nominal_rows": len(rows), "nominal_episodes": len(np.unique(ep[rows])),
                                 "assigned_masters": len(assigned), "observed_masters": len(set(cells)),
                                 "finite_target_rows": int(np.isfinite(y[rows]).sum())},
            "comparison_with_saved_outputs": matches,
            "maxdiff": max(m["maximum_absolute_numeric_difference"] for m in matches.values()),
            "metrics": results, "gates": gates, "paired_comparisons": comparisons,
            "per_episode": episode_records,
            "limitations": ["Source chemical identity remains unknown unless separately qualified; unknown is not proof of leakage.",
                            "This verifies exported-array arithmetic and bindings, not independent source normalization or wet-lab validity.",
                            "MASTER bootstrap is conditional on this source, not biological source independence.",
                            "No new core, world/agent/inheritance/joint/RSI claim is established by an audit PASS."]}


def save_report(report, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists() and not output.with_suffix(".md").exists(), "Refuse to replace audit evidence")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# Independent post-freeze result verification", "", f"Status: {report['status']}",
             f"Synthetic: {report['synthetic']}; model fits: 0; archive accesses: 0.",
             f"Maximum numeric difference: {report.get('maxdiff')}; tolerance: {TOL}.", "",
             f"Test role counts: {json.dumps(report.get('test_role_counts'))}",
             f"Recomputed gates: {json.dumps(report.get('gates', {}).get('gates'))}", "",
             "Every policy's counts, MASTER vectors, episode scores and hash checks are in the JSON.", ""]
    if "verification_error" in report:
        lines.extend([f"Verification error: {report['verification_error']}", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-after-test-open", action="store_true")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--synthetic-fixture", action="store_true")
    args = parser.parse_args()
    if not args.run_after_test_open:
        parser.error("Refusing access: explicit --run-after-test-open is required")
    folder = args.log_dir.resolve()
    if args.synthetic_fixture:
        require(folder != DEFAULT_LOG.resolve() and "SYNTHETIC" in folder.name.upper(),
                "Synthetic mode requires a separately named SYNTHETIC fixture directory")
    output = args.output or folder / "INDEPENDENT_RESULTS_AUDIT.json"
    require(output.resolve().is_relative_to((ROOT / "log").resolve()), "Audit evidence must be under log/")
    require(not output.exists() and not output.with_suffix(".md").exists(), "Refuse to replace audit evidence")
    try:
        report = audit(folder, synthetic=args.synthetic_fixture)
    except Exception as error:
        report = {"utc": datetime.now(timezone.utc).isoformat(), "status": "FAIL",
                  "synthetic": args.synthetic_fixture, "auditor_sha256": digest(Path(__file__)),
                  "purpose": "post-freeze independent verification; not method, selection, or fitting",
                  "verification_error": f"{type(error).__name__}: {error}", "model_fits": 0,
                  "archive_accesses": 0, "maxdiff": None}
    save_report(report, output)
    print(json.dumps({"status": report["status"], "maxdiff": report["maxdiff"], "output": str(output)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
