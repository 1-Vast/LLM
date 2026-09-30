"""No-training denominator audit on frozen LINCS2020 proxy cases and queries."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

from maestro.acquisition import select_discriminating_action
from maestro.adaptive_retrieval import FeatureArm
from maestro.case_memory import EpisodeStore, digest, episode_to_dict
from maestro.hypothesis_forecast import CaseMemoryOutcomeForecaster, UserStateContext
from maestro.models import EvidenceAction, FunctionalInterventionProfile, MechanismContrast, MechanismHypothesis
from maestro.outcome import EvidenceState

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "outputs/dual_core_followup_20261001/denominator_run"
PACK = "data/processed/case_memory_integration/pack.json"
ARRAYS = "data/processed/case_memory_integration/pack_arrays.npz"
STORE = "outputs/case_memory_integration/episodes/proxy_reference_cases_v3.jsonl.gz"
ITEMS = "outputs/case_memory_integration/forecast_items.jsonl"
# Inspected before the new intervention; these historical files are never rebuilt.
FROZEN_SHA256 = {
    PACK: "5e4100852551e8945f88dda92cc60fcf21960e1034320ea90ca8a714b178c120",
    ARRAYS: "c603e70e7f8bf6264d0d469bdf9210f4c605e54383423be4855764100a5f0a4b",
    "data/processed/case_memory_integration/pack_manifest.json": "f566614aa27031cd947675ee057d4615f029d84926552d767159d0313d9e9780",
    STORE: "20951fde2d1871b3c083f1c75f54bb9cbc517bf04d08ea754dd961132e611de3",
    ITEMS: "f3d697a6a89e4471094d74ded01936a6cfe2aea029c0b879409c45222d4ff0e8",
    "outputs/case_memory_integration/results.json": "87428d7995362dde50df0756e59142d572ba823af539d67c336c792cfc75d212",
    "outputs/case_memory_integration/calibration_v3/profile.json": "42c848bbd596efc1a765bbf781af2b4188b22eba8bf48904dc20f37f59f7e8e1",
    "outputs/case_memory_integration/calibration_v3/split.json": "e2b9328f3f799e3515e983205b9c6a1117099eb5aaaeabda1396e23ecfc25fa8",
    "outputs/case_memory_integration/calibration_v3/items.jsonl": "a649f92861b100c39e38dd8d54b192a95e8637ef08453e823192d53309e48ea0",
    "outputs/case_memory_integration/calibration_v3/summary.json": "3436779a898e34e1e5faf794a56916228b196701a4549d6038b394620b02b72e",
    "outputs/case_memory_integration/frequency_v3/development_summary.json": "5ae3ad7f16f373bf719835ab4e7f1586d6f23029461c463320bd895d7deb0066",
    "research/case_memory_integration/PROTOCOL.md": "3758bf2e40a5f67d962fb645b673c875d178b12011cd6dccbbe164e3e7730231",
    "research/case_memory_integration/freeze_protocol.json": "fc5a14cf987c881e6aca4db2e0188420937af91a858292f819aade80e1c7cba8",
}
CODE_PATHS = (
    "research/dual_core_followup/denominator.py", "src/maestro/hypothesis_forecast.py",
    "src/maestro/acquisition.py", "src/maestro/adaptive_retrieval.py",
    "src/maestro/case_memory.py", "src/maestro/models.py", "src/maestro/outcome.py", "src/maestro/composition.py",
    "research/case_memory_integration/external_replay.py", "tools/case_memory/build_cases.py",
)
READING_NAMES = ("match_own", "match_decoy", "unresolved", "undetected")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_records(root: Path) -> dict:
    records = {}
    for path, expected in FROZEN_SHA256.items():
        actual = file_sha(root / path)
        if actual != expected:
            raise ValueError(f"frozen_source_hash_mismatch:{path}")
        records[path] = {"sha256": actual, "size_bytes": (root / path).stat().st_size}
    return records


def write_json(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(episode_to_dict(value), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def load_frozen(root: Path):
    pack = json.loads((root / PACK).read_text(encoding="utf-8"))
    manifest = json.loads((root / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    for name, expected in manifest["outputs"].items():
        if file_sha(root / "data/processed/case_memory_integration" / name) != expected:
            raise ValueError(f"pack_manifest_mismatch:{name}")
    rows = [json.loads(line) for line in (root / ITEMS).read_text().splitlines() if line.strip()]
    key = lambda row: tuple(row[name] for name in ("unit", "cell", "own", "decoy"))
    queries = {}
    for row in rows:
        if row["arm"] == "scalar":
            if key(row) in queries and queries[key(row)]["code"] != row["code"]:
                raise ValueError("conflicting_scalar_labels")
            queries[key(row)] = {name: row[name] for name in ("unit", "cell", "own", "decoy", "code")}
    for row in rows:
        if key(row) not in queries or row["code"] != queries[key(row)]["code"]:
            raise ValueError("cross_arm_label_mismatch")
    expected_queries = {(unit, cell, info["moa"], decoy)
                        for unit, info in pack["units"].items() if info["unseen"]
                        for cell in info["conditions"] for decoy in pack["pool"] if decoy != info["moa"]}
    if set(queries) != expected_queries:
        raise ValueError("historical_query_population_mismatch")
    store = EpisodeStore(root / STORE)
    reference = {str(case.provenance["independent_unit"]) for case in store.latest()}
    expected_reference = {unit for unit, info in pack["units"].items() if not info["unseen"]}
    test = {row["unit"] for row in queries.values()}
    if reference != expected_reference or reference & test:
        raise ValueError("reference_test_unit_boundary_failure")
    readings = {}
    with np.load(root / ARRAYS, allow_pickle=False) as arrays:
        for unit, cell, _, _ in queries:
            name = f"vec::{unit}::{cell}"
            vector = arrays[name]
            if not np.isfinite(vector).all() or not np.any(vector):
                raise ValueError(f"invalid_frozen_reading:{name}")
            readings[(unit, cell)] = {
                "array_key": name, "shape": list(vector.shape), "dtype": str(vector.dtype),
                "content_sha256": digest({"shape": vector.shape, "dtype": str(vector.dtype), "values": vector.tolist()}),
            }
    return pack, store, [queries[name] for name in sorted(queries)], readings


def run(out: Path, *, root: Path = ROOT, command: list[str] | None = None) -> dict:
    sources = source_records(root)
    code = {path: file_sha(root / path) for path in CODE_PATHS}
    out.mkdir(parents=True, exist_ok=False)
    environment = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                   "packages": {name: importlib.metadata.version(name) for name in ("maestro", "numpy", "scipy")}}
    declaration = {
        "schema": "maestro.denominator.predeclared.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "command_argv": command if command is not None else [sys.executable, *sys.argv],
        "environment": environment, "environment_sha256": digest(environment),
        "sources": sources, "source_manifest_sha256": digest(sources), "code_sha256": code,
        "population": {"selection": "unique scalar-arm unit/cell/own/decoy keys in frozen forecast_items",
                       "independent_units": 26, "unit_cell_readings": 28, "queries": 112},
        "intervention": {"outcome_modes": ["valid_readout", "attempted_experiment"], "feature_arm": "scalar",
                         "research_mode": True, "calibration": None, "action_cost": 8.0, "budget": 8.0,
                         "user_state": "same state-free public context; only outcome_mode changes",
                         "selector": "production select_discriminating_action; one legal action per historical query"},
        "historical_calibration": "frozen metadata only; no profile loaded, recalibration or fitted-artifact rebuild",
        "exposure": "all reference/test signatures and proxy labels previously inspected in September 2026; descriptive software contract audit",
        "report": ["three denominators separately", "support/refusal", "selector reasons/actions", "reading/evidence fingerprints"],
        "excluded_claims": ["QC success probability", "terminal benefit", "biological evidence", "state gain", "external generalisation"],
        "stop_on": ["source/code hash change", "pack manifest mismatch", "reference/test overlap",
                    "query population mismatch", "cross-arm label conflict", "missing/invalid real vector", "evidence mutation"],
        "no_valid_forecasts": "report the frozen population's refusals; do not select another population",
    }
    # Persist this before constructing or calling either prediction target or selector.
    write_json(out / "predeclared.json", declaration)
    pack, store, queries, readings = load_frozen(root)
    if (len({row["unit"] for row in queries}), len(readings), len(queries)) != (26, 28, 112):
        raise ValueError("predeclared_population_count_mismatch")
    models = {mode: CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR,
              research_mode=True, outcome_mode=mode) for mode in ("valid_readout", "attempted_experiment")}
    results = []
    for query in queries:
        unit = pack["units"][query["unit"]]
        hypotheses = tuple(sorted((f"class:{query['own']}", f"class:{query['decoy']}")))
        contrast = MechanismContrast("frozen-denominator-pair", tuple(MechanismHypothesis(h, h) for h in hypotheses), (), None)
        action = EvidenceAction(f"lincs2020:{query['cell']}:24h:10uM", "frozen Level 5 signature", 8.0,
                                hypotheses, readout="signature", time_hours=24, execution_context=query["cell"])
        state = UserStateContext(intervention_identity=unit["pert_id"], cell_context=query["cell"],
            time_h=24, dose_nM=10000, assay="l1000_level5", biological_system="l1000", intervention_type="compound",
            measurement_type="transcriptomic", control_design="plate_population")
        evidence = EvidenceState.open(contrast.hypotheses)
        evidence_before = digest(evidence)
        consequences = {f"match_{hypotheses[0]}": frozenset((hypotheses[1],)),
                        f"match_{hypotheses[1]}": frozenset((hypotheses[0],)),
                        "unresolved": frozenset(), "absent": frozenset(), "qc_failed": frozenset()}
        query_input = {"contrast": contrast, "action": action, "state": state, "evidence": evidence}
        row = {**query, "compound": unit["pert_id"], "fold": "historical_unseen_stratum_already_exposed",
               "independent_unit": query["unit"], "reading": readings[(query["unit"], query["cell"])],
               "reading_code_name": READING_NAMES[query["code"]], "label_kind": "derived_annotation_proxy",
               "query_sha256": digest(query_input), "evidence_before_sha256": evidence_before, "targets": {}}
        for mode, model in models.items():
            current_state = replace(state, outcome_mode=mode)
            forecasts = model.forecast(contrast, (action,), evidence, current_state)
            forecast = forecasts[action.identifier]
            support = model.support_report(contrast, action, evidence, current_state)
            plan = select_discriminating_action(evidence.candidates, (action,),
                FunctionalInterventionProfile("compound"), 8.0, forecasts, consequences)
            row["targets"][mode] = {
                "input_sha256": digest({**query_input, "state": current_state}), "output_sha256": digest(forecast),
                "requested_outcome_mode": mode, "returned_outcome_mode": forecast.outcome_mode,
                "model_version": forecast.model_version, "forecast": episode_to_dict(forecast), "support": support,
                "available": forecast.refusal is None and bool(forecast.branches), "refusal": forecast.refusal,
                "selector_status": plan.status, "selector_reasons": [item.reason for item in plan.evaluations],
                "selected_actions": [item.identifier for item in plan.plan.actions], "selector_sha256": digest(plan),
            }
        row["evidence_after_sha256"] = digest(evidence)
        row["observations_unchanged"] = row["evidence_after_sha256"] == evidence_before and not evidence.updates
        if not row["observations_unchanged"]:
            raise ValueError("evidence_mutated_by_forecast_or_selector")
        results.append(row)
    if sources != source_records(root) or code != {path: file_sha(root / path) for path in CODE_PATHS}:
        raise ValueError("source_or_code_changed_during_run")
    with (out / "query_paths.jsonl").open("x", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    measurements = [m for case in store.latest() for m in case.real_measurements]
    summary = {
        "schema": "maestro.denominator.summary.v1", "predeclared_sha256": file_sha(out / "predeclared.json"),
        "population": {"test_independent_units": len({r["unit"] for r in results}), "test_unit_cell_readings": len(readings),
                       "contrast_queries": len(results), "reference_independent_units": len(store.latest()),
                       "reference_proxy_labels": len(measurements)},
        "reference_sampling_frames": dict(Counter(m.sampling_frame for m in measurements)),
        "reference_statuses": dict(Counter(m.status.value for m in measurements)),
        "store_snapshot": store.snapshot_digest(), "targets": {},
        "observations_unchanged": all(row["observations_unchanged"] for row in results),
        "frozen_inputs_unchanged": True, "code_unchanged_during_run": True,
        "qc_success_probability": None, "terminal_benefit": None, "confidence_intervals": None,
        "interpretation": "qualification of two forecast targets and selector contract; no complete attempted-experiment denominator",
        "exposure": declaration["exposure"], "calibration_loaded_or_fitted": False,
    }
    for mode in models:
        entries = [row["targets"][mode] for row in results]
        summary["targets"][mode] = {
            "queried": len(entries), "available": sum(item["available"] for item in entries),
            "available_units": len({row["unit"] for row in results if row["targets"][mode]["available"]}),
            "refusals": dict(Counter(item["refusal"] for item in entries if item["refusal"])),
            "selector_reasons": dict(Counter(reason for item in entries for reason in item["selector_reasons"])),
            "queries_with_selected_action": sum(bool(item["selected_actions"]) for item in entries),
        }
    write_json(out / "summary.json", summary)
    write_json(out / "ledger.json", {"sources": sources, "code_sha256": code,
        "outputs": {path.name: file_sha(path) for path in (out / "predeclared.json", out / "query_paths.jsonl", out / "summary.json")}})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.out.resolve()), indent=2, sort_keys=True))
