"""Independent receipt checks; probe banks are parsed, full banks are hashed only."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
ARMS = {"fixed_none", "baseline_reference", "anchored_reference", "anchored_permuted"}


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     default=str, allow_nan=False).encode()).hexdigest()


def json_lines(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream)


def identity(row):
    steps = json.loads(row["steps"]) if isinstance(row["steps"], str) else row["steps"]
    return {"steps": [{k: step[k] for k in ("action", "outcome", "qc", "eliminated")} for step in steps],
            "stop": row["stop"], "final": row["final"],
            "measurements": int(row["measurements"]), "days": float(row["days"])}


def validate(run, out):
    out.mkdir(parents=True, exist_ok=False)
    errors, examples, counts = Counter(), [], Counter()

    def check(condition, name, detail=None):
        counts[name] += 1
        if not condition:
            errors[name] += 1
            if len(examples) < 20:
                examples.append({"check": name, "detail": detail})

    predeclared_path = run.parent / "predeclared.json"
    predeclared = json.loads(predeclared_path.read_text(encoding="utf-8"))
    receipt = json.loads((run / "run_record.json").read_text(encoding="utf-8"))
    inputs = {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(run.iterdir()) if p.is_file()}
    inputs[str(predeclared_path.relative_to(ROOT))] = file_hash(predeclared_path)
    check(receipt["predeclared_sha256"] == inputs[str(predeclared_path.relative_to(ROOT))], "predeclared_hash")
    for name, expected in receipt["outputs_sha256"].items():
        check(inputs[str((run / name).relative_to(ROOT))] == expected, "run_output_hash", name)
    for kind in ("input", "source"):
        for name, expected in predeclared[kind + "_sha256"].items():
            actual = file_hash(ROOT / name)
            inputs[name] = actual
            check(actual == expected, "frozen_" + kind + "_hash", name)

    metrics = {(r["task"], r["episode"], r["arm"]): r for r in csv_rows(run / "episode_metrics.csv")}
    by_episode, observed, needed_bundles = defaultdict(set), {}, set()
    scalar_fields = ("measurements", "days", "utility", "correct", "wrong", "undetermined", "deferred",
                     "acted", "decided", "utility_lo", "utility_hi", "all_ce", "all_brier", "all_accuracy",
                     "selected_ce", "selected_brier", "selected_accuracy")
    for row in json_lines(run / "episodes.jsonl.gz"):
        key = row["task"], row["episode"], row["arm"]
        check(key not in observed and key in metrics, "episode_key_unique_and_joined", key)
        observed[key] = identity(row)
        by_episode[key[:2]].add(row["arm"])
        flat = metrics[key]
        for field in scalar_fields:
            wanted, actual = row[field], flat[field]
            check((wanted is None and actual == "") or (wanted is not None and actual != "" and
                  math.isclose(float(wanted), float(actual), rel_tol=1e-12, abs_tol=1e-12)), "episode_metric", [key, field])
        check(all(str(row[k]) == flat[k] for k in ("final", "stop", "independent_unit")), "episode_labels", key)
        check(json.loads(flat["sequence"]) == [s["action"] for s in row["steps"]], "episode_sequence", key)
        check(not row["forecast_entered_repair"] and not row["forecast_entered_final_evidence"], "prediction_evidence_boundary", key)
        if row["arm"] == "fixed_none":
            check(row["forecast_receipt"]["calls"] == 0 and not row["forecast_entered_selector"], "fixed_no_forecast", key)
        for decision in row["decisions"]:
            if decision["note"].get("reason") == "registered_validator_cannot_eliminate":
                check(decision["forecast_calls"] == 0, "structural_no_forecast", key)
        coverage = row["coverage"]
        check(coverage["point_identified"] == (not bool(coverage["potential_missing_results"] or
              coverage["potential_unresolved_sources"])), "coverage_flag", key)
        expected = (row["utility"], row["utility"]) if coverage["point_identified"] else (-2, 1)
        check((row["utility_lo"], row["utility_hi"]) == expected, "declared_bounds", key)
        needed_bundles.add(row["forecast_receipt"]["bundle_sha256"])
    check(len(observed) == len(metrics), "all_metrics_joined")
    check(all(arms == ARMS for arms in by_episode.values()), "four_arms_per_episode")
    gate = json.loads((run / "gate.json").read_text())
    check(gate["passed"] and gate["reference_fits"] == 0 and gate["episode_arm_paths"] == len(observed), "gate")
    for task in sorted({k[0] for k in observed}):
        for old in csv_rows(ROOT / "outputs/identifiability_round2_20260930/interventions" / (task + "_episodes.csv")):
            arm = {("none", "fixed"): "fixed_none", ("reference", "baseline"): "baseline_reference"}.get((old["forecast"], old["policy"]))
            key = task, old["episode"], arm
            if key in observed:
                check(identity(old) == observed[key], "independent_historical_parity", key)
    parity = json.loads((run / "parity.json").read_text())
    check(len(parity) == len(observed) // 2 and all(p["same"] for p in parity), "parity_receipt")

    bank_scope = "probe_all_banks" if run.name == "probe" else "full_bank_bytes_only"
    content_pairs = None
    if run.name == "probe":
        outputs, queries, bundles, contexts = {}, {}, set(), defaultdict(dict)
        for row in json_lines(run / "forecast_outputs.jsonl.gz"):
            content = row["content"]
            check(digest(content) == row["output_sha256"], "forecast_output_hash")
            for branch in content["branches"]:
                p = list(branch["probabilities"].values())
                check(all(math.isfinite(v) and v >= 0 for v in p) and math.isclose(sum(p), 1, abs_tol=1e-9), "probability_distribution")
            outputs[row["output_sha256"]] = digest({"refusal": content["refusal"],
                "probabilities": {b["hypothesis"]: b["probabilities"] for b in content["branches"]}})
        for row in json_lines(run / "queries.jsonl.gz"):
            query = row["query"]
            check(digest(query) == row["input_sha256"], "forecast_query_hash")
            check(row["output_sha256"] in outputs, "query_output_reference")
            queries[row["input_sha256"]] = row["output_sha256"]
            if not query["history"]:
                context = tuple(query[k] for k in ("task_input", "compound", "h1", "h2", "action"))
                contexts[context][query["forecast"]] = outputs[row["output_sha256"]]
        for row in json_lines(run / "call_bundles.jsonl.gz"):
            check(digest(row["queries"]) == row["bundle_sha256"], "call_bundle_hash")
            bundles.add(row["bundle_sha256"])
            for call in row["queries"]:
                check(queries.get(call["input_sha256"]) == call["output_sha256"] and call["calls"] > 0, "call_query_reference")
        check(needed_bundles <= bundles, "episode_bundle_reference")
        paired = [p for p in contexts.values() if "reference" in p and "permuted" in p]
        content_pairs = {"paired_initial_contexts": len(paired), "actual_content_differences":
                         sum(p["reference"] != p["permuted"] for p in paired)}
        check(bool(paired), "initial_content_pairs_present")
    else:
        for path in csv_rows(run / "path_attribution.csv"):
            a = metrics[path["task"], path["episode"], path["arm"]]
            b = metrics[path["task"], path["episode"], path["anchor"]]
            seq_a, seq_b = json.loads(a["sequence"]), json.loads(b["sequence"])
            values = {"sequence_changed": seq_a != seq_b, "first_changed": seq_a[:1] != seq_b[:1],
                      "later_changed": seq_a[1:] != seq_b[1:], "terminal_changed": a["final"] != b["final"],
                      "delta_utility": float(a["utility"]) - float(b["utility"]),
                      "delta_lo": float(a["utility_lo"]) - float(b["utility_hi"]),
                      "delta_hi": float(a["utility_hi"]) - float(b["utility_lo"])}
            check(all(float(path[k]) == float(v) for k, v in values.items()), "path_attribution_row")
        summary = json.loads((run / "task_summary.json").read_text())
        for task, result in summary.items():
            check(set(result["arms"]) == ARMS and "unavailable" in result["physical_ci"], "summary_scope", task)
            for arm, statistics in result["arms"].items():
                rows = [r for key, r in metrics.items() if key[0] == task and key[2] == arm]
                for field, statistic in statistics.items():
                    units = defaultdict(list)
                    for r in rows:
                        if r[field] != "":
                            units[r["independent_unit"]].append(float(r[field]))
                    mean = sum(sum(v) / len(v) for v in units.values()) / len(units) if units else None
                    check(statistic["units"] == len(units) and ((mean is None and statistic["mean"] is None) or
                          (mean is not None and math.isclose(mean, statistic["mean"], rel_tol=1e-12, abs_tol=1e-12))),
                          "summary_arm_unit_mean", [task, arm, field])

    report = {"passed": not errors, "counts": dict(counts), "errors": dict(errors), "examples": examples,
              "bank_scope": bank_scope, "initial_content_comparison": content_pairs,
              "limitations": "Full bank semantics and bootstrap/comparison-summary calculations are not independently recomputed; full bank byte hashes, all episode/parity/path rows and all arm unit means are checked.",
              "command": [sys.executable, *sys.argv], "code_sha256": file_hash(Path(__file__)), "input_sha256": inputs,
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "environment": {"python": sys.version, "interpreter": sys.executable, "platform": platform.platform(),
                              "pytest": importlib.metadata.version("pytest")}}
    target = out / "validation.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    with (out / "artifact_hashes.json").open("x", encoding="utf-8") as stream:
        json.dump({target.name: file_hash(target)}, stream, indent=2)
    print(json.dumps({"passed": report["passed"], "counts": report["counts"], "errors": report["errors"],
                      "bank_scope": bank_scope, "initial_content_comparison": content_pairs}, indent=2))
    return report["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if validate(args.run.resolve(), args.out.resolve()) else 1)
