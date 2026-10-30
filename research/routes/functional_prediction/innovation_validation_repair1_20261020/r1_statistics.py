"""Read-only audit of saved results; no fitting, outcome generation, or API calls."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).resolve().parents[1] / "innovation_validation_20261020"
SEED = 20261020
BOOT = 20000
FAMILIES = ("alias", "compose")
ARMS = ("inh_kg", "lat_aopt", "rst_kg", "inh_pol", "fix_pol", "fix_kg")


def stratified_ci(values: dict, level: float) -> list[float]:
    """Preserve the fixed 24:24 family allocation and paired stream contrasts."""
    rng = np.random.default_rng(SEED)
    means = np.zeros(BOOT)
    for family in FAMILIES:
        x = np.asarray(values[family], dtype=float)
        indices = rng.integers(0, len(x), size=(BOOT, len(x)))
        means += 0.5 * x[indices].mean(axis=1)
    alpha = (1 - level) / 2
    return np.quantile(means, [alpha, 1 - alpha]).tolist()


def resource_totals(streams: list[dict]) -> dict:
    arms = sorted(streams[0]["resources"]["candidate_evals"])
    return {
        "n_streams": len(streams),
        "candidate_evaluations": {
            arm: sum(s["resources"]["candidate_evals"][arm] for s in streams)
            for arm in arms
        },
        "validation_replays": {
            arm: sum(s["resources"]["validation_replays"][arm] for s in streams)
            for arm in arms
        },
        "sum_stream_elapsed_seconds": round(
            sum(s["resources"]["wall_seconds"] for s in streams), 6
        ),
        "measured_process_cpu_seconds": None,
    }


def audit() -> dict:
    streams, hashes = [], {}
    files = sorted((SOURCE / "RUN/eval/streams").glob("*.json.gz"))
    for path in files:
        raw = path.read_bytes()
        hashes[str(path.relative_to(SOURCE)).replace("\\", "/")] = hashlib.sha256(raw).hexdigest()
        streams.append(json.loads(gzip.decompress(raw)))
    expected = {f"{k}_{s}" for k in ("null", "lowrank", *FAMILIES) for s in range(1, 25)}
    expected |= {f"{k}_{s}_dec" for k in FAMILIES for s in range(1, 25)}
    if len(streams) != 144 or {s["sid"] for s in streams} != expected:
        raise ValueError("The original 144 unique saved evaluation streams are required.")

    tables = {family: [] for family in FAMILIES}
    for stream in streams:
        if stream["decoupled"] or stream["kind"] not in FAMILIES:
            continue
        table = {}
        for arm in ARMS:
            selected = [r for r in stream["rows"] if r["arm"] == arm
                        and r["contract"] == "E" and r["role"] == "task" and r["gen"] >= 2]
            if len(selected) != 12 or len({(r["gen"], r["cell"]) for r in selected}) != 12:
                raise ValueError(f"Incomplete or duplicated task rows: {stream['sid']}/{arm}")
            table[arm] = float(np.mean([r["utility"] for r in selected]))
        tables[stream["kind"]].append(table)

    primary = {}
    for label, a, b in (("H1", "inh_kg", "lat_aopt"),
                        ("H2", "inh_kg", "rst_kg"),
                        ("H3", "inh_pol", "inh_kg")):
        values = {k: [r[a] - r[b] for r in tables[k]] for k in FAMILIES}
        ci = stratified_ci(values, 1 - 0.05 / 3)
        primary[label] = {
            "contrast": f"{a} - {b}",
            "mean": float(np.mean([x for k in FAMILIES for x in values[k]])),
            "family_means": {k: float(np.mean(values[k])) for k in FAMILIES},
            "stratified_ci": ci,
            "ci_level": 1 - 0.05 / 3,
            "all_upper_bounds_below_original_margin": ci[1] < 0.01,
            "purpose": "Sensitivity analysis; does not replace the registered pooled analysis.",
        }
    interactions = {
        k: [(r["inh_pol"] - r["inh_kg"]) - (r["fix_pol"] - r["fix_kg"])
            for r in tables[k]] for k in FAMILIES
    }
    summary = json.loads((SOURCE / "SUMMARY.json").read_text(encoding="utf-8"))
    launcher = json.loads((SOURCE / "RUN/RESOURCES.json").read_text(encoding="utf-8"))
    for name in ("SUMMARY.json", "CONFIG.json", "RUN/RESOURCES.json", "iv_run.py",
                 "iv_search.py", "iv_worlds.py", "iv_post.py"):
        hashes[name] = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
    return {
        "label": "SAVED_OUTPUT_STATISTICAL_AUDIT_NOT_A_NEW_EXPERIMENT",
        "source_package": str(SOURCE),
        "input_sha256": hashes,
        "method": {"seed": SEED, "bootstrap_resamples": BOOT,
                   "ordering": "sorted stream filenames; family order alias, compose",
                   "strata": {k: len(tables[k]) for k in FAMILIES},
                   "unit": "paired mean over contract E task rows in generations 2-4, within one stream",
                   "weights": {k: 0.5 for k in FAMILIES},
                   "original_margin": 0.01},
        "original_registered_primary_results": [
            r for r in summary["primary_E"] if r["group"] == "mechanism(alias+compose)"
        ],
        "stratified_sensitivity": primary,
        "factorial_interaction": {
            "label": "POST_HOC_DESCRIPTIVE_NOT_CONFIRMATORY",
            "formula": "(inh_pol - inh_kg) - (fix_pol - fix_kg)",
            "mean": float(np.mean([x for k in FAMILIES for x in interactions[k]])),
            "family_means": {k: float(np.mean(interactions[k])) for k in FAMILIES},
            "stratified_ci95": stratified_ci(interactions, 0.95),
            "arm_means": {a: float(np.mean([r[a] for k in FAMILIES for r in tables[k]]))
                          for a in ("inh_pol", "inh_kg", "fix_pol", "fix_kg")},
        },
        "resources": {
            "normal_96": resource_totals([s for s in streams if not s["decoupled"]]),
            "decoupled_48": resource_totals([s for s in streams if s["decoupled"]]),
            "all_144": resource_totals(streams),
            "reported_launcher_wall_minutes": launcher["comparative_wall_minutes"],
            "reported_worker_processes": launcher["processes"],
            "worker_capacity_hours_not_measured_cpu":
                launcher["processes"] * launcher["comparative_wall_minutes"] / 60,
            "timing_limit": "perf_counter elapsed time; process CPU was not measured; arm cost attribution is incomplete.",
        },
        "interpretation": {
            "H1_original_implementation": "NO_SUPPORT at the original margin in the registered synthetic world family.",
            "H1_repaired_implementation": "NOT_TESTED by these saved outputs.",
            "H2_registered_expanded_restart": "NO_SUPPORT against the expanded-budget restart comparator.",
            "H2_equal_resources": "NOT_TESTED: candidate caps total 48 versus 120 over four generations.",
            "H3_registered": "NO_SUPPORT for adding policy adaptation when structure evolution is enabled; not a factorial interaction.",
            "H4_measured_utility": "NOT_TESTED; no independent measured effectiveness evidence.",
            "decoupled_specificity": "NOT_IDENTIFIED: compose activation marginals and temporal structure also change.",
            "proposed_12_background_design": "WITHDRAW: unsupported sample-size prescription; no new wet experiment proposed.",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved read-only statistical audit: {args.out}")
