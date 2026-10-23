"""Independent validation-only selection verification; never fit or open test labels."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np


BASES = ("effect", "dose", "direct", "combo_direct")
VARIANTS = BASES + ("effect_offset", "dose_offset", "direct_offset")
ORDINARY = ("bliss", "historical", "dose", "combo_direct", "direct", "dose_offset", "direct_offset")
ETAS = (0., .25, .5, .75, 1.)
ENDPOINTS = ("mae", "utility")
TOLERANCE = 1e-12


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def value(record, endpoint):
    return record["metrics"]["mae" if endpoint == "mae" else "utility"]


def winner(records, endpoint):
    values = np.array([value(r, endpoint) for r in records])
    index = int(np.argmin(values) if endpoint == "mae" else np.argmax(values))
    return records[index], np.flatnonzero(values == values[index]).tolist()


def independently_score(y, prediction, effect, episode, master, valid):
    """Separate implementation: nominal top-five, then episode-to-MASTER means."""
    assigned = sorted(set(master.tolist()))
    panels = {k: defaultdict(list) for k in ("mae", "utility", "oracle_utility", "regret")}
    counts = {k: defaultdict(int) for k in ("input", "forecast", "recommendation")}
    finite_rows = 0
    keys = np.unique(episode)
    for key in keys:
        rows = np.flatnonzero(episode == key)
        if np.any(valid[rows]) != np.all(valid[rows]):
            raise ValueError("Input validity varies within episode")
        identities = set(master[rows].tolist())
        if len(identities) != 1:
            raise ValueError("Episode contains multiple MASTERs")
        cell = identities.pop()
        if not valid[rows].all():
            continue
        if not (np.isfinite(prediction[rows]).all() and np.isfinite(effect[rows]).all()):
            raise ValueError("Nonfinite valid-input prediction or effect")
        counts["input"][cell] += 1
        finite = np.isfinite(y[rows])
        finite_rows += int(finite.sum())
        if finite.sum() >= 5:
            panels["mae"][cell].append(float(np.abs(y[rows[finite]] - prediction[rows[finite]]).mean()))
            counts["forecast"][cell] += 1
        if len(rows) < 5 or not finite.all():
            continue
        predicted_u = prediction[rows] - effect[rows].max(axis=1)
        # Python's stable sort independently preserves nominal row order in ties.
        chosen = np.array(sorted(rows.tolist(), key=lambda r: -float(predicted_u[np.searchsorted(rows, r)]))[:5])
        observed = y[rows] - effect[rows].max(axis=1)
        utility = float((y[chosen] - effect[chosen].max(axis=1)).mean())
        oracle = float(np.sort(observed)[-5:].mean())
        for metric, result in (("utility", utility), ("oracle_utility", oracle), ("regret", oracle - utility)):
            panels[metric][cell].append(result)
        counts["recommendation"][cell] += 1
    per_master = {metric: [float(np.mean(by_cell[c])) if by_cell[c] else None for c in assigned]
                  for metric, by_cell in panels.items()}
    aggregates = {metric: float(np.mean([v for v in values if v is not None]))
                  for metric, values in per_master.items()}
    coverage = {}
    for panel, by_cell in counts.items():
        n = sum(by_cell.values())
        absent = [c for c in assigned if by_cell[c] == 0]
        coverage[panel] = {"episodes": n, "episode_coverage": n / len(keys),
                           "zero_contributor_masters": absent,
                           "coverage_pass": bool(n / len(keys) >= .95 and assigned and not absent)}
    coverage["forecast"].update(mae=aggregates["mae"], finite_target_rows=finite_rows,
                                finite_target_row_coverage=finite_rows / len(y))
    coverage["forecast"]["coverage_pass"] &= finite_rows / len(y) >= .95
    coverage["recommendation"].update({k: aggregates[k] for k in ("utility", "oracle_utility", "regret")})
    return {**aggregates, "nominal_rows": len(y), "nominal_episodes": len(keys),
            "assigned_masters": assigned, **coverage, "per_master": per_master,
            "per_master_episode_counts": {k: [v[c] for c in assigned] for k, v in counts.items()},
            "coverage_pass": bool(all(c["coverage_pass"] for c in coverage.values()))}


def run(log):
    started = time.perf_counter()
    output = log / "SELECTION_INDEPENDENT_AUDIT.json"
    report = log / "SELECTION_INDEPENDENT_AUDIT.md"
    if output.exists() or report.exists():
        raise RuntimeError("Existing independent audit will not be overwritten")
    names = ("VALIDATION_TRIALS.json", "SELECTION.json", "VALIDATION_SELECTED_METRICS.json",
             "VALIDATION_PREDICTIONS.npz", "VALIDATION_OFFSET_AUDIT.json", "PAID_SUMMARIES.json",
             "EPISODE_META.json", "DATA.npz")
    before = {name: digest(log / name) for name in names}
    trials = read_json(log / names[0])
    selection = read_json(log / names[1])
    selected_metrics = read_json(log / names[2])
    offset_audit = read_json(log / "VALIDATION_OFFSET_AUDIT.json")
    meta = read_json(log / "EPISODE_META.json")
    summaries = read_json(log / "PAID_SUMMARIES.json")
    with np.load(log / "DATA.npz", allow_pickle=False) as source:
        role = source["role"]
        val_rows = np.flatnonzero(role == "validation")
        y = source["y"][val_rows]
        effect = source["effect"][val_rows]
        episode = source["episode"][val_rows]
        valid = source["valid_mask"][val_rows]
    master_map = {int(e["episode_id"]): e["cell"] for e in meta}
    master = np.array([master_map[int(e)] for e in episode])
    groups, seen = defaultdict(list), set()
    for summary in summaries:
        if summary["role"] != "train":
            continue
        key = tuple(summary["key"])
        if key in seen:
            raise ValueError("Duplicate training paid matrix")
        seen.add(key)
        if summary["mean_residual"] is not None:
            groups[tuple(summary["pair"])].append(summary["mean_residual"])
    pair_means = {"|".join(pair): float(np.mean(values)) for pair, values in groups.items()}
    offset_by_episode, missing = {}, []
    for e in meta:
        if e["role"] != "validation" or not e["valid"]:
            continue
        deviations = []
        for pair, residual in zip(e["query_pairs"], e["query_residual_means"]):
            pair = "|".join(pair)
            if residual is None:
                raise ValueError("Valid validation episode lacks paid residual")
            deviations.append(residual - pair_means.get(pair, 0.))
            if pair not in pair_means:
                missing.append([e["episode_id"], pair.split("|")])
        offset_by_episode[int(e["episode_id"])] = float(np.mean(deviations))
    offsets = np.array([offset_by_episode.get(int(e), np.nan) for e in episode])
    with np.load(log / "VALIDATION_PREDICTIONS.npz", allow_pickle=False) as source:
        prediction_names = set(source.files)
        predictions = {name: source[name][val_rows] for name in source.files}

    checks, differences, maxdiff, compared_numbers = [], [], 0., 0

    def check(name, passed, detail=None):
        checks.append({"name": name, "pass": bool(passed), "detail": detail})

    def compare(label, actual, expected):
        nonlocal maxdiff, compared_numbers
        if isinstance(expected, dict):
            if set(actual) != set(expected):
                differences.append({"path": label, "issue": "keys"})
                return
            for key in expected:
                compare(label + "." + key, actual[key], expected[key])
        elif isinstance(expected, list):
            if len(actual) != len(expected):
                differences.append({"path": label, "issue": "length"})
                return
            for i, v in enumerate(expected):
                compare(f"{label}[{i}]", actual[i], v)
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            compared_numbers += 1
            delta = abs(float(actual) - float(expected))
            maxdiff = max(maxdiff, delta)
            if not np.isfinite(delta) or delta > TOLERANCE:
                differences.append({"path": label, "actual": actual, "expected": expected, "absdiff": delta})
        elif actual != expected:
            differences.append({"path": label, "actual": actual, "expected": expected})

    expected_names = {f"{base}_{ci}" for base in BASES for ci in range(12)}
    check("48 prediction arrays exactly cover four fixed grids", prediction_names == expected_names)
    check("seven variant lists in frozen order", tuple(trials) == VARIANTS)
    compare("training_pair_means", pair_means, offset_audit["pair_means"])
    compare("training_unique_paid_matrices", sum(map(len, groups.values())), offset_audit["unique_reference_matrices"])
    stored_missing = [m for m in offset_audit["missing_historical_query_pairs"] if int(m[0]) in set(episode)]
    compare("validation_missing_prior_pairs", missing, stored_missing)

    recomputed = {}
    for variant in VARIANTS:
        base = variant.removesuffix("_offset")
        etas = ETAS if variant.endswith("_offset") else (0.,)
        expected = [(base, ci, eta) for ci in range(12) for eta in etas]
        actual = [(r["base"], r["config_index"], r["eta"]) for r in trials[variant]]
        check(f"{variant}: complete ordered config/eta grid", actual == expected, len(actual))
        recomputed[variant] = []
        for record in trials[variant]:
            prediction = predictions[f"{base}_{record['config_index']}"].copy()
            prediction[valid] += record["eta"] * offsets[valid]
            metrics = independently_score(y, prediction, effect, episode, master, valid)
            compare(f"trials.{variant}.{record['config_index']}.{record['eta']}", metrics, record["metrics"])
            recomputed[variant].append({**record, "metrics": metrics})

    selected, ties, mixtures = {}, {}, {}
    for endpoint in ENDPOINTS:
        selected[endpoint], ties[endpoint] = {}, {}
        policies = {}
        for variant in VARIANTS:
            chosen, tied = winner(trials[variant], endpoint)
            compare(f"choice.{endpoint}.{variant}", selection["policies"][endpoint][variant], chosen)
            independent, _ = winner(recomputed[variant], endpoint)
            check(f"{endpoint}.{variant}: independent winner agrees", independent == chosen)
            selected[endpoint][variant] = {k: chosen[k] for k in ("base", "config_index", "eta")}
            ties[endpoint][variant] = tied
            prediction = predictions[f"{chosen['base']}_{chosen['config_index']}"].copy()
            prediction[valid] += chosen["eta"] * offsets[valid]
            policies[variant] = prediction
            compare(f"selected_metrics.{endpoint}.{variant}", chosen["metrics"], selected_metrics[endpoint][variant])
        bliss = effect[:, 0] + effect[:, 1] - effect[:, 0] * effect[:, 1]
        compare(f"selected_metrics.{endpoint}.bliss", independently_score(y, bliss, effect, episode, master, valid), selected_metrics[endpoint]["bliss"])
        mixtures[endpoint] = []
        for weight in ETAS:
            prediction = weight * policies["effect"] + (1. - weight) * policies["direct_offset"]
            metrics = independently_score(y, prediction, effect, episode, master, valid)
            mixtures[endpoint].append({"weight": weight, "metrics": metrics})
        chosen, mixture_ties = winner(mixtures[endpoint], endpoint)
        compare(f"mixture.{endpoint}", chosen, selection["mixture"][endpoint])
        compare(f"selected_metrics.{endpoint}.mixture", chosen["metrics"], selected_metrics[endpoint]["mixture"])
        ties[endpoint]["mixture_weights"] = [ETAS[i] for i in mixture_ties]
        ordinary = [{"arm": arm, "metrics": selected_metrics[endpoint][arm]} for arm in ORDINARY]
        enumerator = [{"arm": arm, "metrics": metrics} for arm, metrics in selected_metrics[endpoint].items()]
        compare(f"ordinary.{endpoint}", winner(ordinary, endpoint)[0], selection["ordinary"][endpoint])
        compare(f"enumerator.{endpoint}", winner(enumerator, endpoint)[0], selection["enumerator"][endpoint])
        check(f"{endpoint}: policy metric enumeration order", tuple(selected_metrics[endpoint]) == ("bliss", "historical") + VARIANTS + ("mixture",))

    unique = sorted({(r["base"], r["config_index"]) for choices in selected.values() for r in choices.values()})
    check("unique selected base/config refits within 14", len(unique) <= 14, unique)
    check("five unique selected final refits", len(unique) == 5)
    after = {name: digest(log / name) for name in names}
    check("all read artifacts unchanged", before == after)
    check("all numerical/structural comparisons agree", not differences, {"compared_numbers": compared_numbers, "max_absdiff": maxdiff})
    result = {"utc": datetime.now(timezone.utc).isoformat(), "status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
              "verification_not_search": True, "model_fits": 0, "test_target_reads": 0,
              "script_sha256": digest(Path(__file__)), "input_sha256": before,
              "data_fields_read": ["validation y", "validation effect", "role", "validation episode", "validation valid_mask"],
              "metadata_fields_read": ["episode_id/cell", "role", "validation valid/query_pairs/query_residual_means", "train paid summaries"],
              "validation": {"rows": len(y), "episodes": len(set(episode)), "masters": len(set(master))},
              "base_prediction_arrays": len(predictions), "scored_candidate_records": sum(map(len, trials.values())),
              "checks": checks, "differences": differences, "max_absdiff": maxdiff, "numeric_comparisons": compared_numbers,
              "selected": selected, "exact_ties": ties, "mixtures": mixtures,
              "ordinary": {e: selection["ordinary"][e]["arm"] for e in ENDPOINTS},
              "enumerator": {e: selection["enumerator"][e]["arm"] for e in ENDPOINTS},
              "unique_final_refits": unique, "verification_seconds": time.perf_counter() - started,
              "limitation": "Historical predictions cannot be regenerated with this read contract; their stored metrics enter the comparator/enumerator selection check. Artifact completeness verifies 48 base predictions, not process-level fit receipts."}
    output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Independent validation selection audit", "", f"Status: **{result['status']}**. No fits, test-target reads, reselection or parameter changes.", "",
             f"Recomputed all {result['scored_candidate_records']} candidate score records from 48 saved base predictions, training-only paid priors and legal validation outcomes. Compared {compared_numbers} numerical fields; maximum absolute difference {maxdiff:.17g}.", "",
             "| Endpoint | Ordinary comparator | Enumerator | Mixture effect weight |", "|---|---|---|---|"]
    for endpoint in ENDPOINTS:
        lines.append(f"| {endpoint} | {result['ordinary'][endpoint]} | {result['enumerator'][endpoint]} | {selection['mixture'][endpoint]['weight']} |")
    lines += ["", f"Deduplication yields {len(unique)} base/config final refits, within the frozen maximum 14. Actual completion of refits is outside this validation-only audit.", "",
              "MAE and U have separately selected policies. The MAE-optimal and U-optimal settings must not be portrayed as one parameter choice that wins both endpoints. Offset eta ties in U retain the first candidate (eta=0); exact ties use stored order, never an approximate tolerance.", "",
              "All five mixture weights were independently scored per endpoint. The ordinary set excludes the effect candidate, its offset and the mixture; the enumerator includes all reported policies in fixed order.", "",
              "Historical prediction scores were only checked for consistent use in comparator/enumerator selection; regenerating them would require additional training outcomes/dose fields outside this audit contract.", "",
              "One pre-script schema inspection displayed a test-role paid-query summary value. It was already paid information, was not a test target, and was not used by this audit; the formal calculation filters training summaries before reading their values. Root confirmed this distinction. No protected target or forbidden feature arrays were read.", "",
              "Costs are independent verification compute, with zero experiment-search fits. All source inputs remained unchanged; details, tie indices, candidate mixtures and hashes are in SELECTION_INDEPENDENT_AUDIT.json."]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "max_absdiff", "numeric_comparisons", "ordinary", "enumerator", "unique_final_refits", "verification_seconds")}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", type=Path, default=Path(__file__).resolve().parents[2] / "log/20261022/az_paid_reference_gate")
    args = parser.parse_args()
    raise SystemExit(run(args.log_dir))
