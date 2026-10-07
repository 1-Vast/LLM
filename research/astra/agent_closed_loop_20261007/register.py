"""Freeze a bounded exposed-development engineering study using metadata only."""
from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / "research/astra/zeroshot_context_20261007"
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def register():
    files = {"PANC-1": "c20.h5ad", "HepG2/C3A": "c27.h5ad"}
    menus = {}
    for context, file in files.items():
        by = {}
        for label, plate, count in json.loads((PRIOR / "census" / f"{file}.json").read_text())["condition_plate_counts"]:
            if "DMSO" not in label and count >= 100:
                by.setdefault(label, set()).add(plate)
        menus[context] = {label: plates for label, plates in by.items() if len(plates) >= 2}
    common = set.intersection(*(set(m) for m in menus.values()))
    drugs = {}
    for label in common:
        (drug, dose, unit), = ast.literal_eval(label)
        drugs.setdefault(drug, []).append((dose, unit, label))
    eligible = {drug: sorted(rows) for drug, rows in drugs.items() if len(rows) >= 2}
    selected = sorted(eligible, key=lambda drug: hashlib.sha256(("agent-source-case:" + drug).encode()).hexdigest())[:2]
    sources, cases = [], []
    runtime = json.loads((PRIOR / "state_forecasts/runtime.json").read_text())
    for context, file in files.items():
        state_path = CACHE / "state_forecasts" / f"{file}.npz"
        state_hash = digest(state_path)
        receipt = json.loads((PRIOR / "state_forecasts" / f"{file}.receipt.json").read_text())
        if state_hash != receipt["sha256"]:
            raise ValueError("Prior STATE forecast receipt hash mismatch")
        for drug in selected:
            for dose, unit, label in eligible[drug]:
                for plate in sorted(menus[context][label]):
                    sources.append(dict(context=context, label=label, drug=drug, dose=float(dose), unit=unit,
                                        source_group=plate, source_reference=state_path.relative_to(ROOT).as_posix(),
                                        source_sha256=state_hash))
            dose, unit, label = eligible[drug][0]
            plates = sorted(menus[context][label], key=lambda plate: hashlib.sha256(("well-role:" + label + ":" + plate).encode()).hexdigest())
            cases.append(dict(context=context, file=file, drug=drug, dose=float(dose), unit=unit, label=label,
                              first_plate=plates[0], independent_plate=plates[1]))
    write(HERE / "SOURCES.json", sources)
    protocol = dict(
        schema="agent_state_closed_loop_v1", created_utc=datetime.now(timezone.utc).isoformat(),
        status="exposed-development operational replay; no independent biological efficacy claim",
        historical_exposure="Prior reports, development tables and cached forecast metadata were inspected before registration. This freeze protects this task's execution and analysis, not previously untouched outcomes.",
        cases=cases, selection="Two SHA256-ordered drugs with >=2 replicated doses on both development contexts, lowest qualifying dose, well order hashed from metadata only",
        arms=["deterministic_exact_source", "live_llm_exact_source"],
        world="Cached native STATE paired RNA delta from final.ckpt; no new inference/adaptation; common exact outputs in both arms",
        checkpoint=runtime["checkpoint"], original_runtime="research/astra/zeroshot_context_20261007/state_forecasts/runtime.json",
        native_axis="2000 X_hvg coordinates; unidentified coordinates stay unnamed", exposure_hours=24.0,
        readout="RNA_delta_rms = sqrt(mean(delta_X_hvg**2)); diagnostic full-vector squared error also logged",
        observation="24-hour Tahoe existing drug-treated mean minus disjoint same-plate DMSO reference mean; one well is one source unit, sampled cells are not independent wells",
        budget=dict(measurement_limit=2.0, cost_per_purchased_profile=1.0, declared_metadata_tool_cost=0.0,
                    api_max_completions=8, api_max_output_tokens_per_call=800, api_timeout_seconds=25.0,
                    api_transport_attempt_limit=4, api_transport_retry_billing="unknown when no decoded response"),
        decision_rule="After qualified first-well profile, request independent-well verification iff full-vector STATE error exceeds estimated observation sampling noise; otherwise stop. This heuristic is an operational rule, not calibrated biological risk or proof of utility.",
        matching="Same initial source menu, tools, source selectors, forecast, feedback, measurement cap and rule. Invalid LLM requests fail closed and are reported separately; no silent deterministic fallback.",
        primary_endpoints=["exact_source_resolution", "legal_prediction_binding", "feedback_conditioned_next_request", "idempotent_budget", "case_evidence_after_restart", "original_prediction_after_old_retry"],
        secondary_endpoints=["api_usage_and_runtime", "two-well_descriptive_error", "live_vs_deterministic_choices"],
        restart="Reconstruct CaseStore/ContextBuilder/Orchestrator after first result; restore persisted prediction reliability only. A newly registered source-qualification analysis never claims restoration of prior mechanism hypotheses.",
        unavailable_claims=["agent biological benefit", "new STATE inference", "mechanism elimination", "causal RNA-to-ATP bridge", "independent generalization of decision utility"],
    )
    write(HERE / "PROTOCOL.json", protocol)
    write(HERE / "PROTOCOL_FREEZE.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=digest(HERE / "PROTOCOL.json"), sources_sha256=digest(HERE / "SOURCES.json"),
        registration_code_sha256=digest(Path(__file__)), treatment_outcomes_read_by_registration=False))
    print(json.dumps(dict(cases=len(cases), source_records=len(sources), freeze=digest(HERE / "PROTOCOL.json"))))


if __name__ == "__main__":
    register()
