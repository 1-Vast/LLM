"""Post-hoc explanation of the fixed development run; no fitting, selection or external test use.

Reconstruct the same class/condition/contrast counts and vary only the two already-declared
smoothing operations to attribute their losses. Outputs are diagnostics, not validation of a
newly selected model.
"""
from collections import Counter, defaultdict
import json
import math

import numpy as np

from maestro.case_memory import EpisodeStore
from maestro.hypothesis_forecast import support_aware_shrinkage
from tools.datasets.lincs_pack import ROOT, load_pack
from tools.case_memory.build_cases import build_reference_episodes


def main():
    out = ROOT / "outputs/case_memory_integration/scientific_fix"
    summary = json.loads((out / "development_summary.json").read_text())
    original = [json.loads(line) for line in (out / "development_items.jsonl").read_text().splitlines()]
    pack, arrays = load_pack()
    train = set(summary["training_blocks"])
    train_pack = {**pack, "units": {b: u for b, u in pack["units"].items() if b in train}}
    train_arrays = {k: v for k, v in arrays.items() if k.startswith("vec::") and k.split("::")[1] in train}
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    store = EpisodeStore()
    store.append_many(build_reference_episodes(train_pack, train_arrays, manifest))
    assert store.snapshot_digest() == summary["store_snapshot"]
    frequencies = defaultdict(Counter)
    for episode in store.latest():
        for m in episode.real_measurements:
            h1, h2 = m.contrast
            label = {"match_h1": "own", "match_h2": "other"}.get(m.outcome_label, m.outcome_label)
            frequencies[(m.action_id, h1, h2)][label] += 1
    labels = ("own", "other", "unresolved", "absent", "qc_failed")
    prior = {label: .2 for label in labels}
    rows = []
    for r in original:
        if r["refusal"]:
            continue
        counts = frequencies[(f"lincs2020:{r['cell']}:24h:10uM", r["own"], r["decoy"])]
        n = sum(counts.values())
        truth = "own" if r["outcome"] == f"match_{r['own']}" else "other" if r["outcome"] == f"match_{r['decoy']}" else r["outcome"]
        distributions = {}
        for name, strength, temperature in (("baseline", 2.5, 1.), ("temperature_only", 2.5, 1.5),
                                             ("strong_prior_only", 8., 1.), ("full", 8., 1.5)):
            distributions[name] = support_aware_shrinkage(counts, effective_support=n, domain_shift=0,
                base_prior=prior, prior_strength=strength, temperature=temperature)
        assert abs(distributions["full"][truth] - r["probability"]) < 1e-12
        assert abs(distributions["baseline"][truth] - r["baseline_probability"]) < 1e-12
        loss = {name: -math.log(p[truth]) for name, p in distributions.items()}
        row = {"unit": r["unit"], "class": r["own"], "cell": r["cell"], "outcome": truth,
               "support": n, "counts": dict(counts), "nll": loss,
               "difference": loss["full"] - loss["baseline"],
               "uniform_mass": 8 / (n + 8),
               "qc_mass_full": distributions["full"]["qc_failed"],
               "qc_mass_baseline": distributions["baseline"]["qc_failed"],
               "qc_reservation_penalty_difference": math.log1p(-distributions["baseline"]["qc_failed"])
                   - math.log1p(-distributions["full"]["qc_failed"]),
               "temperature_shapley": .5 * (loss["temperature_only"] - loss["baseline"]
                                              + loss["full"] - loss["strong_prior_only"]),
               "prior_shapley": .5 * (loss["strong_prior_only"] - loss["baseline"]
                                        + loss["full"] - loss["temperature_only"]),
               "correct": {k: max(p, key=p.get) == truth for k, p in distributions.items()},
               "brier": {k: sum((v - (label == truth)) ** 2 for label, v in p.items())
                         for k, p in distributions.items()}}
        rows.append(row)

    def grouped(key):
        buckets = defaultdict(list)
        for row in rows:
            buckets[row[key]].append(row)
        return {str(k): {"items": len(v), "units": len({x["unit"] for x in v}),
                        "difference": float(np.mean([x["difference"] for x in v])),
                        "nll_full": float(np.mean([x["nll"]["full"] for x in v])),
                        "nll_baseline": float(np.mean([x["nll"]["baseline"] for x in v])),
                        "sum_difference": sum(x["difference"] for x in v)} for k, v in sorted(buckets.items())}

    unit_diffs = np.array([v["difference"] for v in grouped("unit").values()])
    rng = np.random.default_rng(20260929)
    boots = rng.choice(unit_diffs, size=(10000, len(unit_diffs)), replace=True).mean(axis=1)
    result = {"kind": "posthoc_diagnostic_not_model_selection", "reconstruction_error_below": 1e-12,
              "original_training_snapshot": store.snapshot_digest(),
              "nll": {name: float(np.mean([r["nll"][name] for r in rows])) for name in distributions},
              "accuracy": {name: float(np.mean([r["correct"][name] for r in rows])) for name in distributions},
              "brier": {name: float(np.mean([r["brier"][name] for r in rows])) for name in distributions},
              "means": {k: float(np.mean([r[k] for r in rows])) for k in (
                  "uniform_mass", "qc_mass_full", "qc_mass_baseline", "qc_reservation_penalty_difference",
                  "temperature_shapley", "prior_shapley")},
              "support_range": [min(r["support"] for r in rows), max(r["support"] for r in rows)],
              "unit_mean_difference": float(unit_diffs.mean()),
              "unit_bootstrap_descriptive_interval": np.quantile(boots, [.025, .975]).tolist(),
              "units_better": int((unit_diffs < 0).sum()), "units_worse": int((unit_diffs > 0).sum()),
              "by_outcome": grouped("outcome"), "by_class": grouped("class"), "by_cell": grouped("cell"),
              "by_unit": grouped("unit"), "by_support": grouped("support")}
    (out / "shrinkage_diagnosis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "shrinkage_diagnosis_items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
