"""Read only released result artifacts for the constructive post-result review."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(log, timing=False):
    out = log / "advocate"
    out.mkdir(exist_ok=True)
    target = out / "POST_RESULT_EVIDENCE.json"
    if target.exists():
        raise RuntimeError("Do not overwrite an existing post-result evidence record")
    names = ("TEST_METRICS.json", "GATES.json", "ALL_PAIRED_COMPARISONS.json",
             "COSTS.json", "SUPPORT_PLATEAU_DIAGNOSTICS.json")
    before = {name: sha(log / name) for name in names}
    metrics, gates, paired, costs, diagnostic = [read(log / name) for name in names]
    paired = paired["comparisons"]
    selected = {name: {k: record[k] for k in ("mae", "utility", "regret", "coverage_pass")}
                for name, record in metrics.items()}
    primary = {}
    for endpoint in ("mae", "utility"):
        saved = gates["comparisons"][endpoint]
        candidate = metrics["effect__" + endpoint]
        baseline = metrics[saved["ordinary"] + "__" + endpoint]
        gain = (baseline["mae"] - candidate["mae"] if endpoint == "mae"
                else candidate["utility"] - baseline["utility"])
        headroom = baseline["mae"] if endpoint == "mae" else baseline["regret"]
        passed = gain >= .02 and gain >= .1 * headroom and saved["bootstrap"]["lower"] > 0
        if endpoint == "utility":
            passed = passed and headroom > .02
        primary[endpoint] = {"candidate": candidate[endpoint], "baseline": baseline[endpoint],
                             "ordinary": saved["ordinary"], "gain_recomputed": gain,
                             "headroom": headroom, "relative_gain": gain / headroom,
                             "ci95": saved["bootstrap"]["ci95"], "pass_recomputed": passed,
                             "matches_gate": passed == gates["gates"][endpoint]}
    local_names = ("effect_vs_dose__mae", "effect_vs_dose__utility", "direct_vs_combo_direct__mae",
                   "direct_vs_combo_direct__utility", "effect_vs_effect_offset__mae",
                   "effect_vs_effect_offset__utility")
    plateau = diagnostic["plateau"]
    n_finite = sum(r["finite_response_pairs"] for r in plateau)
    representative = metrics["effect__mae"]
    result = {"utc": datetime.now(timezone.utc).isoformat(), "model_fits": 0,
              "new_target_reads": 0, "raw_source_reads": 0, "input_sha256": before,
              "script_sha256": sha(Path(__file__)), "primary": primary,
              "local_paired_comparisons": {name: paired[name] for name in local_names},
              "selected_metrics": selected, "costs": costs,
              "coverage": {"all_22_policy_coverage_pass": all(m["coverage_pass"] for m in metrics.values()),
                           "master_count": len(representative["assigned_masters"]),
                           "nominal_episodes": representative["nominal_episodes"],
                           "nominal_rows": representative["nominal_rows"],
                           "panels": {name: representative[name] for name in ("input", "forecast", "recommendation")}},
              "support": diagnostic["support"],
              "plateau": {"episodes": len(plateau), "pairs": diagnostic["plateau_pair_count"],
                          "finite_pairs": n_finite,
                          "pair_weighted_mean_absolute_gap": sum(r["finite_response_pairs"] * r["mean_absolute_response_gap"] for r in plateau if r["finite_response_pairs"]) / n_finite,
                          "maximum_absolute_gap": max(r["max_absolute_response_gap"] for r in plateau)},
              "no_absent_target_pair": not diagnostic["pairs_absent_from_training"]}
    if timing:
        path = log / "FIT_RUNS.jsonl"
        before[path.name] = sha(path)
        grouped = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            phase, arm = record["phase"], record["arm"]
            slot = grouped.setdefault(phase, {}).setdefault(arm, {"fits": 0, "fit_seconds": 0., "total_seconds": 0.})
            slot["fits"] += 1
            slot["fit_seconds"] += record["fit_seconds"]
            slot["total_seconds"] += record["total_seconds"]
        result["timing_by_phase_arm"] = grouped
    result["all_inputs_unchanged"] = all(sha(log / name) == h for name, h in before.items())
    target.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"output": str(target), "primary": primary,
                      "timing_by_phase_arm": result.get("timing_by_phase_arm"),
                      "all_inputs_unchanged": result["all_inputs_unchanged"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", type=Path, default=Path(__file__).resolve().parents[2] / "log/20261022/az_paid_reference_gate")
    parser.add_argument("--timing", action="store_true", help="Use only when FIT_RUNS timing fields have been authorized")
    args = parser.parse_args()
    main(args.log_dir, timing=args.timing)
