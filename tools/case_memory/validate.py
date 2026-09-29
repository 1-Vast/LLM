"""Development validation commands for case-memory forecasts and calibration.

Both workflows rebuild their reference artifacts inside the declared training split. They are
replay diagnostics and do not establish intervention causality, external validity or decision
value. Run ``python -m tools.case_memory.validate forecasts`` or ``... validate calibration``.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import sys

import numpy as np

from maestro.case_memory import EpisodeStore
from maestro.adaptive_retrieval import FeatureArm
from maestro.hypothesis_forecast import (
    CaseMemoryOutcomeForecaster,
    MODEL_VERSION,
    UserStateContext,
    dirichlet_forecast,
    fit_frequency_calibration,
)
from maestro.models import EvidenceAction, MechanismContrast, MechanismHypothesis
from tools.case_memory.build_cases import (
    _cosine,
    _reference_centroid_from_index,
    build_reference_episodes,
    build_reference_index,
    reference_norm_thresholds,
)
from tools.datasets.lincs_pack import ROOT, load_pack

def validate_forecasts() -> int:
    pack, arrays = load_pack()
    rng = np.random.default_rng(20260929)
    holdout = set()
    for klass in pack["pool"]:
        units = sorted(b for b, u in pack["units"].items() if not u["unseen"] and u["moa"] == klass)
        holdout.update(rng.permutation(units)[:max(1, len(units) // 5)])
    train = {b: u for b, u in pack["units"].items() if not u["unseen"] and b not in holdout}
    train_pack = {**pack, "units": train}
    # Only training raw vectors are passed to the builder. Frozen external test vectors stay unused.
    train_arrays = {k: v for k, v in arrays.items() if k.startswith("vec::") and k.split("::")[1] in train}
    reference_index = build_reference_index(train_pack, train_arrays)
    thresholds = reference_norm_thresholds(train_pack, train_arrays)
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    store = EpisodeStore()
    store.append_many(build_reference_episodes(train_pack, train_arrays, manifest))
    forecaster = CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR, research_mode=True)
    rows = []
    for block in sorted(holdout):
        unit = pack["units"][block]
        for cell in unit["conditions"]:
            vec = arrays[f"vec::{block}::{cell}"]  # evaluator view only
            threshold = thresholds[cell]
            own = f"class:{unit['moa']}"
            co = _reference_centroid_from_index(
                train_pack, train_arrays, unit["moa"], cell, index=reference_index
            )
            for decoy in pack["pool"]:
                if decoy == unit["moa"]:
                    continue
                other = f"class:{decoy}"
                contrast = MechanismContrast("development-pair", tuple(
                    MechanismHypothesis(h, h) for h in sorted((own, other))), (), None)
                action = EvidenceAction(f"lincs2020:{cell}:24h:10uM", "held-out proxy reading", 1,
                                        tuple(sorted((own, other))), readout="signature", time_hours=24)
                state = UserStateContext(cell_context=cell, time_h=24, dose_nM=10000,
                    assay="l1000_level5", biological_system="l1000", intervention_type="compound",
                    measurement_type="transcriptomic", control_design="plate_population")
                forecast = forecaster.forecast(contrast, (action,), None, state)[action.identifier]
                cd = _reference_centroid_from_index(
                    train_pack, train_arrays, decoy, cell, index=reference_index
                )
                if co is None or cd is None:
                    continue
                diff = _cosine(vec, co) - _cosine(vec, cd)
                label = ("absent" if np.linalg.norm(vec) < threshold else "unresolved" if abs(diff) < .02
                         else f"match_{own}" if diff > 0 else f"match_{other}")
                row = {"unit": block, "cell": cell, "own": own, "decoy": other,
                       "outcome": label, "refusal": forecast.refusal}
                if not forecast.refusal:
                    branch = forecast.branch_for(own)
                    counts = Counter()
                    for episode in store.latest():
                        m = forecaster._measurement_for_action(episode, action, state, (own, other))
                        if m is not None and m.conditioning_hypothesis == own:
                            mapped = forecaster._map_measurement_label(episode, m, own, other,
                                                                       f"match_{own}", f"match_{other}")
                            if mapped is not None:
                                counts[mapped] += 1
                    # Same declared outcome space and observed units for both estimators.
                    baseline = (counts[label] + .5) / (sum(counts.values()) + .5 * len(branch.probabilities))
                    row.update(probability=branch.probabilities[label], baseline_probability=baseline,
                               nll=-math.log(branch.probabilities[label]), baseline_nll=-math.log(baseline))
                rows.append(row)
    scored = [r for r in rows if not r["refusal"]]
    grouped = defaultdict(list)
    for row in scored:
        grouped[row["unit"]].append(row["nll"] - row["baseline_nll"])
    summary = {"evaluation_kind": "development_only_state_free_proxy_holdout", "model_version": MODEL_VERSION,
               "training_units": len(train), "holdout_units": len(holdout), "scored_units": len(grouped),
               "forecast_items": len(rows), "scored_items": len(scored),
               "production_nll": float(np.mean([r["nll"] for r in scored])) if scored else None,
               "jeffreys_baseline_nll": float(np.mean([r["baseline_nll"] for r in scored])) if scored else None,
               "unit_mean_nll_difference": float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None,
               "calibration_fitted": False, "external_test_used": False,
               "split_seed": 20260929,
               "source_inputs": manifest["inputs"],
               "training_blocks": sorted(train), "holdout_blocks": sorted(holdout),
               "store_snapshot": store.snapshot_digest(),
               "limitations": ["development diagnostic; no confirmatory or action-selection claim",
                               "curated annotations and derived readings are proxy labels",
                               "no user-state features or queried outcome signatures enter forecasting"]}
    # Preserve the previously inspected five-outcome experiment and its source artifacts.
    out = ROOT / "outputs/case_memory_integration/frequency_v3"
    out.mkdir(parents=True, exist_ok=True)
    (out / "development_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "development_items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    axes[0].bar(["Production candidate", "Jeffreys baseline"],
                [summary["production_nll"], summary["jeffreys_baseline_nll"]], color=["#446688", "#669977"])
    axes[0].set(ylabel="Mean NLL (lower is better)", title="156 proxy forecast items; 11 held-out units")
    values = sorted(float(np.mean(v)) for v in grouped.values())
    axes[1].bar(range(1, len(values) + 1), values, color=["#669977" if v < 0 else "#bb6655" for v in values])
    axes[1].axhline(0, color="black", linewidth=.8)
    axes[1].set(xlabel="Held-out unit (ordered by difference)", ylabel="Production minus baseline NLL",
                title="Independent-unit differences; positive is worse")
    fig.suptitle("Development diagnostic only: uncalibrated, no external-test or decision claim")
    fig.savefig(out / "development_diagnostic.png", dpi=150)
    plt.close(fig)
    print(json.dumps(summary, indent=2))
    return 0


def validate_calibration() -> int:
    pack, arrays = load_pack()
    previous_path = ROOT / "outputs/case_memory_integration/scientific_fix/development_summary.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    evaluation = set(previous["holdout_blocks"])
    available = set(previous["training_blocks"])
    rng = np.random.default_rng(20260930)
    calibration = set()
    for klass in pack["pool"]:
        members = sorted(b for b in available if pack["units"][b]["moa"] == klass)
        calibration.update(rng.permutation(members)[:2])
    training = available - calibration
    assert (len(training), len(calibration), len(evaluation)) == (44, 10, 11)
    assert not (training & calibration or training & evaluation or calibration & evaluation)
    assert all(not pack["units"][b]["unseen"] for b in training | calibration | evaluation)
    train_pack = {**pack, "units": {b: pack["units"][b] for b in sorted(training)}}
    train_arrays = {k: v for k, v in arrays.items() if k.startswith("vec::") and k.split("::")[1] in training}
    reference_index = build_reference_index(train_pack, train_arrays)
    thresholds = reference_norm_thresholds(train_pack, train_arrays)
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    store = EpisodeStore()
    store.append_many(build_reference_episodes(train_pack, train_arrays, manifest))
    baseline = CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR, research_mode=True)
    rows, requests = [], []
    for split, blocks in (("calibration", calibration), ("evaluation", evaluation)):
        for block in sorted(blocks):
            unit = pack["units"][block]
            for cell in unit["conditions"]:
                vec = arrays[f"vec::{block}::{cell}"]  # Evaluator-only future response.
                threshold = thresholds.get(cell)
                own = f"class:{unit['moa']}"
                for decoy in pack["pool"]:
                    if decoy == unit["moa"]:
                        continue
                    other = f"class:{decoy}"
                    contrast = MechanismContrast("development-pair", tuple(
                        MechanismHypothesis(h, h) for h in sorted((own, other))), (), None)
                    action = EvidenceAction(f"lincs2020:{cell}:24h:10uM", "development proxy", 1,
                                            tuple(sorted((own, other))), readout="signature", time_hours=24)
                    state = UserStateContext(cell_context=cell, time_h=24, dose_nM=10000,
                        assay="l1000_level5", biological_system="l1000", intervention_type="compound",
                        measurement_type="transcriptomic", control_design="plate_population")
                    context = baseline.calibration_context(action, state)
                    co = _reference_centroid_from_index(
                        train_pack, train_arrays, unit["moa"], cell, index=reference_index
                    )
                    counts = Counter({f"match_{own}": 0, f"match_{other}": 0, "unresolved": 0, "absent": 0})
                    for episode in store.latest():
                        m = baseline._measurement_for_action(episode, action, state, (own, other))
                        if m and m.conditioning_hypothesis == own:
                            label = baseline._map_measurement_label(episode, m, own, other,
                                                                   f"match_{own}", f"match_{other}")
                            if label in counts:
                                counts[label] += 1
                    cd = _reference_centroid_from_index(
                        train_pack, train_arrays, decoy, cell, index=reference_index
                    )
                    row = dict(split=split, unit=block, cell=cell, own=own, decoy=other,
                               context=context, counts=dict(counts), effective_support=sum(counts.values()))
                    if co is None or cd is None or threshold is None:
                        row["label_refusal"] = "missing_training_label_artifact"
                    else:
                        diff = _cosine(vec, co) - _cosine(vec, cd)
                        row["outcome"] = ("absent" if np.linalg.norm(vec) < threshold else "unresolved"
                                          if abs(diff) < .02 else f"match_{own}" if diff > 0 else f"match_{other}")
                    rows.append(row)
                    requests.append((contrast, action, state))
    cal_rows = [r for r in rows if r["split"] == "calibration" and "outcome" in r and r["effective_support"] > 0]
    profile = fit_frequency_calibration(cal_rows, training_units=training, source_snapshot=store.snapshot_digest(),
                                        outcome_mode="valid_readout", feature_arm=FeatureArm.SCALAR.value)
    fitted = CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR, research_mode=True, calibration=profile)
    assert set(profile.calibration_units) == calibration and set(profile.training_units) == training
    assert profile.source_snapshot == store.snapshot_digest() and profile.outcome_count == 4
    for row, (contrast, action, state) in zip(rows, requests):
        for name, model in (("baseline", baseline), ("fitted", fitted)):
            forecast = model.forecast(contrast, (action,), None, state)[action.identifier]
            row[f"{name}_refusal"] = forecast.refusal
            if forecast.refusal or "outcome" not in row:
                continue
            branch = forecast.branch_for(row["own"])
            alpha = .5 if name == "baseline" else profile.pseudocount
            expected, concentration = dirichlet_forecast(row["counts"], effective_support=row["effective_support"], pseudocount=alpha)
            assert all(math.isclose(branch.probabilities[k], p, abs_tol=1e-10) for k, p in expected.items())
            assert math.isclose(branch.posterior_concentration, concentration)
            if name == "fitted":
                assert profile.refusal(tuple(row["context"]), "valid_readout", "scalar", 4, store.snapshot_digest()) is None
            row[f"{name}_probabilities"] = dict(branch.probabilities)
            row[f"{name}_support"] = branch.support
            row[f"{name}_nll"] = -math.log(branch.probabilities[row["outcome"]])
            row[f"{name}_brier"] = sum((p - (label == row["outcome"])) ** 2 for label, p in branch.probabilities.items())
    summary = {"evaluation_kind": "development_only_previously_inspected_holdout", "model_version": MODEL_VERSION,
               "training_units": len(training), "calibration_units": len(calibration), "evaluation_units": len(evaluation),
               "pseudocount": profile.pseudocount, "external_test_used": False, "source_inputs": manifest["inputs"],
               "store_snapshot": store.snapshot_digest(), "metrics": {},
               "limitations": ["evaluation holdout already inspected; not confirmatory", "curated/derived proxy labels only",
                               "state-free valid-readout task; no action-selection or external-generalisation claim",
                               "unknown laboratory matches unknown only; this does not prove laboratory transfer"]}
    for split in ("calibration", "evaluation"):
        part = [r for r in rows if r["split"] == split]
        for name in ("baseline", "fitted"):
            scored = [r for r in part if f"{name}_nll" in r]
            grouped = defaultdict(list)
            for row in scored:
                grouped[row["unit"]].append(row)
            summary["metrics"][f"{split}_{name}"] = {"attempted_items": len(part), "scored_items": len(scored),
                "coverage": len(scored) / len(part), "scored_units": len(grouped),
                **{metric: float(np.mean([r[f"{name}_{metric}"] for r in scored])) for metric in ("nll", "brier")},
                "unit_mean_nll": float(np.mean([np.mean([r[f"{name}_nll"] for r in group]) for group in grouped.values()])),
                "support_range": [min(r[f"{name}_support"] for r in scored), max(r[f"{name}_support"] for r in scored)]}
    split = {"seed": 20260930, "training": sorted(training), "calibration": sorted(calibration), "evaluation": sorted(evaluation),
             "previous_split_sha256": hashlib.sha256(previous_path.read_bytes()).hexdigest()}
    summary["split_sha256"] = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()
    out = ROOT / "outputs/case_memory_integration/calibration_v3"
    out.mkdir(parents=True, exist_ok=True)
    for filename, value in (("summary.json", summary), ("profile.json", asdict(profile)), ("split.json", split)):
        (out / filename).write_text(json.dumps(value, indent=2), encoding="utf-8")
    (out / "items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = args[0] if args else "forecasts"
    if mode in {"calibration", "calibrate"}:
        return validate_calibration()
    if mode in {"forecasts", "forecast"}:
        return validate_forecasts()
    raise SystemExit(f"unknown validation mode: {mode}; choose forecasts or calibration")


if __name__ == "__main__":
    raise SystemExit(main())
