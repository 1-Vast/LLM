"""Registered operational LLM + cached-native-STATE feedback replay.

All execution accounting and result projection use production implementations.
The driver defines this research task and never restores mechanism hypotheses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from agent.case_store import CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskIntent, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.llm import DeepSeekChatClient, MAESTROSettings, VisualInspector
import agent.llm as llm_transport
from agent.memory import MemoryScope, MemoryStore, RunLogger
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.prediction import PredictionCoordinator
from agent.tool_runtime import LocalToolCatalog, ToolBudget, ToolRouter
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
from tools.datasets.condition_sources import ConditionSource, resolve_condition_sources
from virtual_cell.interface import (
    Intervention, ModelCapabilities, PredictionCache, PredictionRequest,
    QueryAssessment, QuerySupport, StatePrediction, SystemContext, safe_predict,
)


PRIOR = ROOT / "research/astra/zeroshot_context_20261007"
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"
READOUT = "RNA_delta_rms"
MODEL = "STATE-final-2c9b2e74f59c-paired-replay-v1"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def append(path, value):
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def checked_protocol():
    frozen = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    if (digest(HERE / "PROTOCOL.json") != frozen["protocol_sha256"]
            or digest(HERE / "SOURCES.json") != frozen["sources_sha256"]):
        raise ValueError("Study inputs changed after registration")
    return json.loads((HERE / "PROTOCOL.json").read_text())


def should_verify(metrics):
    """Registered operational heuristic; this is not a calibrated error threshold."""
    error = float(metrics["profile_mse"])
    noise = float(metrics["sampling_noise_estimate"])
    if not np.isfinite(error) or not np.isfinite(noise) or error < 0 or noise < 0:
        raise ValueError("Nonfinite/negative feedback diagnostic")
    return error > noise


class FixedSourcePolicy:
    """Competent same-tool baseline: literal exact source selectors."""

    def __init__(self, selectors):
        self.selectors = selectors

    def complete_json(self, messages, **kwargs):
        return dict(tool_id="condition_sources", dataset_id="dataset_1", arguments=self.selectors,
                    rationale="Resolve the explicit dose and independent source identity without inferring missing conditions."), None


class LoggedClient:
    def __init__(self, client, path, limit=8):
        self.client, self.path, self.limit = client, path, limit
        self.calls = 0

    def complete_json(self, messages, **kwargs):
        if self.calls >= self.limit:
            raise ValueError("Registered LLM completion limit reached")
        self.calls += 1
        started = time.perf_counter()
        record = dict(call=self.calls, request=messages, max_tokens=min(kwargs.get("max_tokens", 800), 800),
                      start_monotonic=started)
        try:
            answer, response = self.client.complete_json(messages, max_tokens=record["max_tokens"])
            record.update(status="completed", answer=answer, model=response.model, usage=dict(response.usage),
                          finish_reason=response.finish_reason)
            return answer, response
        except Exception as error:
            record.update(status="failed", error_type=type(error).__name__,
                          error="Provider failure; no secret-bearing transport/request text retained.")
            raise
        finally:
            record["elapsed_seconds"] = time.perf_counter() - started
            append(self.path, record)


class CountedTransportClient(DeepSeekChatClient):
    """Observe the production retry boundary without reimplementing its policy."""

    def __init__(self, settings, path):
        super().__init__(settings)
        self.transport_path = path
        self.transport_attempts = 0

    def _send(self, request):
        original = llm_transport.urlopen

        def observed(request, **kwargs):
            self.transport_attempts += 1
            started = time.perf_counter()
            receipt = {"attempt": self.transport_attempts}
            try:
                response = original(request, **kwargs)
                receipt["status"] = "connection_opened"
                return response
            except Exception as error:
                receipt.update(status="failed", error_type=type(error).__name__)
                raise
            finally:
                receipt["connection_seconds"] = time.perf_counter() - started
                append(self.transport_path, receipt)

        # All provider requests in this study are sequential; the patch is scoped
        # to the production transport call and restores its original on exit.
        with patch("agent.llm.urlopen", observed):
            return super()._send(request)


class SourceCatalog(LocalToolCatalog):
    """Both policies receive the same one-tool catalogue, using real validation."""

    def discover(self):
        return tuple(item for item in super().discover() if item.identifier == "condition_sources")


class CachedNativeSTATE:
    name = "cached_native_STATE_replay"

    def __init__(self, sources, protocol):
        self.sources = tuple(sources)
        self.protocol = protocol
        self.arrays = {}
        self.original_receipts = {}
        self.calls = 0
        for source in self.sources:
            path = ROOT / source.source_reference
            if source.source_reference not in self.arrays:
                if digest(path) != source.source_sha256:
                    raise ValueError("STATE artifact does not match registered source hash")
                self.arrays[source.source_reference] = dict(np.load(path, allow_pickle=False))
                receipt = json.loads((PRIOR / "state_forecasts" / path.name.replace(".npz", ".receipt.json")).read_text())
                if receipt["sha256"] != source.source_sha256 or receipt["treated_rows_read"] is not False:
                    raise ValueError("Native STATE receipt lineage mismatch")
                self.original_receipts[source.source_reference] = receipt

    def capabilities(self):
        return ModelCapabilities("Arc STATE final.ckpt paired native RNA replay", MODEL,
                                 "native 2000-coordinate X_hvg, 256 basal DMSO cells per plate",
                                 "registered categorical drug-dose label", ("drug",), True, True, False, None)

    def resolve(self, request):
        conditions = request.observation_context or {}
        return resolve_condition_sources(
            self.sources, context=request.context.identifier, drug=request.intervention.identifier,
            dose=request.intervention.dose, unit=request.intervention.dose_unit,
            label=conditions.get("label"), source_group=conditions.get("plate"),
            source_reference=request.context.dataset_id, source_sha256=conditions.get("source_sha256"))

    def assess_query(self, request):
        missing = []
        conditions = request.observation_context or {}
        for field in ("label", "plate", "source_sha256", "tool_evidence_id"):
            if not isinstance(conditions.get(field), str) or not conditions[field].strip():
                missing.append("missing_source_binding:" + field)
        if request.intervention.time_hours != 24.0:
            missing.append("registered_24h_exposure")
        if request.readouts != (READOUT,):
            missing.append("native_RNA_readout")
        result = self.resolve(request)
        if result.status != "resolved":
            missing.append(result.status)
        else:
            source = result.candidates[0]
            expected = self.original_receipts[source.source_reference]["basal"][source.source_group]["sha256"]
            if request.context.control_dataset_id != expected or (request.observation_context or {}).get("basal_input_sha256") != expected:
                missing.append("exact_basal_control")
        if (request.observation_context or {}).get("checkpoint_sha256") != self.protocol["checkpoint"]["sha256"]:
            missing.append("original_checkpoint_identity")
        if (request.observation_context or {}).get("native_axis") != "X_hvg:2000":
            missing.append("original_input_axis")
        return QueryAssessment(QuerySupport.UNSUPPORTED if missing else QuerySupport.SUPPORTED, tuple(missing),
                               ("Saved native STATE output replay; no new inference, fitted bridge or calibrated uncertainty.",),
                               self.capabilities())

    def profile(self, request):
        result = self.resolve(request)
        if result.status != "resolved":
            raise ValueError("An exact registered source is required")
        source = result.candidates[0]
        arrays = self.arrays[source.source_reference]
        match = np.flatnonzero((arrays["label"] == source.label) & (arrays["plate"] == source.source_group))
        if len(match) != 1:
            raise ValueError("Ambiguous cached STATE row")
        return arrays["paired_delta"][match[0]].astype(np.float64)

    def predict(self, request):
        self.calls += 1
        source = self.resolve(request).candidates[0]
        profile = self.profile(request)
        return StatePrediction(True, {READOUT: float(np.sqrt(np.mean(profile ** 2)))}, None,
                               ("Native checkpoint output replay, not fresh inference.",
                                "A profile norm is not viability, efficacy or mechanism probability."),
                               supported_variables=(READOUT,), request_id=request.request_id,
                               model_version=MODEL, artifact_ref=str(ROOT / source.source_reference),
                               artifact_sha256=source.source_sha256, confidence=None, in_distribution=None,
                               compute_cost=0.0,
                               uncertainty_components={"prediction_error": "Uncalibrated for this RMS summary.",
                                                       "replay": "Finite original basal-cell set and native checkpoint sampling."})


def task_intent(case, phase, expected_plate, restored=None):
    question = (
        f"Resolve the exact registered native-RNA source for context {case['context']}, drug {case['drug']}, "
        f"dose {case['dose']} {case['unit']}, label {case['label']}, source_group {expected_plate}. "
        "Use condition_sources on dataset_1 with the literal context,drug,dose,unit,label,source_group. "
        "The query will be rejected if any identity differs. Metadata is derived analysis, not a biological measurement. "
        "Omit dataset_path in tool arguments: ToolRouter injects the approved file path. "
        "SOURCES.json is the full 20-row registered menu, including the requested source_group; "
        "earlier tool evidence lists the previous query result only, not all available rows. "
        "The condition_sources declared cost is zero, so a zero remaining ToolBudget permits this lookup. "
        "Public RNA purchases have a separate CaseStore budget of two credits; these are distinct resources. "
    )
    if phase == 2:
        question += (
            "This is a new registered source-qualification analysis after restart. Read the accepted first-well "
            "result in case evidence. If profile_mse exceeds sampling_noise_estimate, select the independent "
            "well above; otherwise stop by returning tool_id=null. This heuristic is not calibrated biological risk. "
        )
    return TaskIntent("analysis_planning", question, (), (case["drug"],), case["context"], "native RNA delta",
                      (), ("24-hour exposure, exact native axis and original basal control required.",), (), False)


def runtime(out, backend):
    evidence = EvidenceLedger(out / "evidence.sqlite")
    memory = MemoryStore(out / "memory.sqlite")
    builder = ContextBuilder(evidence, memory, max_characters=22000)
    store = CaseStore(out / "cases.sqlite")
    logger = RunLogger(out / "logs")
    unused = FixedSourcePolicy({})
    orchestrator = MAESTROOrchestrator(
        interpreter=TaskInterpreter(unused), context_builder=builder,
        planner=MechanismContrastPlanner(unused), visual_inspector=VisualInspector(unused, "unused"),
        memory=memory, logger=logger, case_store=store, virtual_cell=backend,
        selection_strategy="budgeted_coverage")
    coordinator = PredictionCoordinator(backend, logger, cache=PredictionCache())
    return store, builder, orchestrator, coordinator


def build_request(case, source, case_id, version, request_id, evidence_id):
    prior_receipt = json.loads((PRIOR / "state_forecasts" / f"{case['file']}.receipt.json").read_text())
    basal_hash = prior_receipt["basal"][source.source_group]["sha256"]
    return PredictionRequest(request_id, case_id, "registered_source_qualification", version,
        Intervention(source.drug, "drug", (), source.dose, source.unit, 24.0),
        SystemContext(source.context, "Saved native STATE basal-context query",
                      source.source_reference, basal_hash, "human", "well"),
        (READOUT,), MODEL, observation_context={
            "label": source.label, "plate": source.source_group, "source_sha256": source.source_sha256,
            "basal_input_sha256": basal_hash, "tool_evidence_id": evidence_id,
            "checkpoint_sha256": "2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3",
            "native_axis": "X_hvg:2000", "assay": "24h single-cell RNA"})


def purchased_result(case, request, action, result_id, backend, out, ledger):
    """Only called after an authoritative start_action receipt exists."""
    path = CACHE / "observations" / f"{case['file']}.npz"
    obs = np.load(path, allow_pickle=False)
    plate = request.observation_context["plate"]
    matches = np.flatnonzero((obs["label"] == case["label"]) & (obs["plate"] == plate))
    controls = np.flatnonzero(obs["ctrl_plate"] == plate)
    if len(matches) != 1 or len(controls) != 1:
        raise ValueError("Ambiguous or absent real observation/control")
    i, c = int(matches[0]), int(controls[0])
    observed = obs["mean"][i].astype(np.float64) - obs["ctrl_mean"][c].astype(np.float64)
    predicted = backend.profile(request)
    count, ctrl_count = int(obs["n"][i]), int(obs["ctrl_n"][c])
    metrics = {READOUT: str(float(np.sqrt(np.mean(observed ** 2)))),
               "profile_mse": str(float(np.mean((predicted - observed) ** 2))),
               "sampling_noise_estimate": str(float(np.mean(obs["var"][i]) / count + np.mean(obs["ctrl_var"][c]) / ctrl_count)),
               "treated_cells": str(count), "reference_cells": str(ctrl_count)}
    destination = out / "profiles" / f"{result_id}.npz"
    destination.parent.mkdir(exist_ok=True)
    np.savez(destination, observed_delta=observed, predicted_delta=predicted)
    append(ledger, dict(event="paid_reveal", case_id=request.case_id, result_id=result_id,
        plan_version=request.plan_version, action_id=action.identifier, request_id=request.request_id,
        source_reference=path.relative_to(ROOT).as_posix(), label=case["label"], plate=plate,
        observation_row=i, control_row=c, cost=action.cost, metrics=metrics,
        profile=str(destination.relative_to(out)), profile_sha256=digest(destination),
        evidence_kind="retrieved_source", checkpoint_sha256=request.observation_context["checkpoint_sha256"]))
    return MeasurementResult(action.identifier,
        f"Published {case['context']} {case['drug']} {case['dose']} {case['unit']} native RNA profile from {plate}; paid replay reveal.",
        f"tahoe:{case['file']}:{case['label']}:{plate}", case["context"], 24.0, 1, True,
        conditions=action.expected_conditions, metrics=metrics, record_count=count,
        evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
        limitations=("Previously exposed development data; no new laboratory experiment.",
                     "Sampled cells are within one well, not independent biological replicates.",
                     "Public-source replay is not granted runtime physical-measurement calibration authority."),
        result_id=result_id, plan_version=request.plan_version)


def run(out, live=False):
    protocol = checked_protocol()
    out = Path(out).resolve()
    if out.exists():
        raise ValueError("Refusing to overwrite a prior run; use a new output directory")
    out.mkdir(parents=True)
    started = time.perf_counter()
    sources = [ConditionSource(**row) for row in json.loads((HERE / "SOURCES.json").read_text())]
    backend = CachedNativeSTATE(sources, protocol)
    provider = None
    if live:
        settings = MAESTROSettings.from_workspace(ROOT)
        settings = replace(settings, timeout_seconds=25.0, max_tokens=800, log_directory=out / "logs")
        provider = LoggedClient(CountedTransportClient(settings, out / "transport.jsonl"), out / "api.jsonl", limit=8)
    store, builder, orchestrator, coordinator = runtime(out, backend)
    actions_path = out / "actions.jsonl"
    results = []
    for number, case in enumerate(protocol["cases"]):
        case_id = f"{'llm' if live else 'det'}.case{number}"
        store.open_case(case_id, budget=2.0)
        accepted_ids, original_prediction, first_metrics = [], None, None
        case_record = dict(case_id=case_id, case=case, phases=[], failures=[])
        for phase, plate in enumerate((case["first_plate"], case["independent_plate"]), 1):
            # Rebuild all production views after phase one; no LLM is used for recovery.
            if phase == 2:
                store, builder, orchestrator, coordinator = runtime(out, backend)
                restored = store.measurement(case_id, accepted_ids[0])
                visible = builder.build(task_intent(case, phase, plate), memory_scope=MemoryScope(case_id=case_id))
                case_record["restored_evidence_ids"] = [e.identifier for e in visible.evidence]
                case_record["facts_restored"] = any(e.payload.get("result_id") == accepted_ids[0] for e in visible.evidence)
                case_record["restored_decision"] = should_verify(restored.metrics)
                case_record["runtime_calibration_records"] = len(orchestrator._reliability.records)
                case_record["recovery_capabilities"] = dict(orchestrator.recovery_capabilities(case_id))
                if not should_verify(restored.metrics):
                    case_record["stopped"] = "registered_diagnostic_did_not_request_independent_profile"
                    break
            intent = task_intent(case, phase, plate)
            packet = builder.build(intent, memory_scope=MemoryScope(case_id=case_id))
            selectors = dict(context=case["context"], drug=case["drug"], dose=case["dose"], unit=case["unit"],
                             label=case["label"], source_group=plate)
            anticipated = resolve_condition_sources(sources, **selectors).candidates[0]
            unqualified = build_request(case, anticipated, case_id, store.snapshot(case_id).plan_version + 1,
                                        f"{case_id}.unqualified{phase}", "not_acquired")
            unqualified = replace(unqualified, observation_context={key: value for key, value in unqualified.observation_context.items()
                                    if key not in ("source_sha256", "tool_evidence_id")})
            before_assessment, before_prediction = safe_predict(backend, unqualified)
            if before_prediction.applicable:
                raise ValueError("Forecast became legal before source qualification")
            append(actions_path, dict(event="pre_acquisition_refusal", case_id=case_id, phase=phase,
                                      reason=before_prediction.abstain_reason,
                                      missing_inputs=list(before_assessment.missing_inputs)))
            client = provider if live else FixedSourcePolicy(selectors)
            tool_budget = ToolBudget(0.0)
            router = ToolRouter(client, ROOT / "tools", budget=tool_budget)
            router._catalog = SourceCatalog(ROOT / "tools")
            try:
                execution = router.select_and_execute(packet, [HERE / "SOURCES.json"], plan_version=f"{case_id}.{phase}")
                if execution is None:
                    raise ValueError("Policy stopped before required source qualification")
                if execution.payload.get("status") != "resolved":
                    raise ValueError("Tool did not return one exact source")
                (candidate,) = execution.payload["candidates"]
                source = ConditionSource(**candidate)
                if any(getattr(source, key) != value for key, value in selectors.items()):
                    raise ValueError("Policy resolved a different condition than registered")
            except Exception as error:
                case_record["failures"].append(dict(phase=phase, error_type=type(error).__name__,
                                                   reason="Source action rejected; no automatic fallback or purchase."))
                append(actions_path, dict(event="rejected_source_action", case_id=case_id, phase=phase,
                                          error_type=type(error).__name__,
                                          reason=str(error) if isinstance(error, ValueError) else "Runtime source action validation refused; inspect selected action in API receipt."))
                break
            packet = builder.add_tool_execution(packet, execution, case_id=case_id)
            evidence_id = packet.evidence[0].identifier
            # Re-project the same immutable receipt; identity must remain stable.
            builder.add_tool_execution(packet, execution, case_id=case_id)
            append(actions_path, dict(event="source_resolved", case_id=case_id, phase=phase,
                                      execution=execution.to_dict(), evidence_id=evidence_id,
                                      declared_tool_budget=tool_budget.snapshot()))
            action = EvidenceAction("native_profile", "Purchase the qualified public native-RNA profile", 1.0, (),
                kind=EvidenceActionKind.EVIDENCE_REVIEW, readout=READOUT, prediction_readout=READOUT, time_hours=24.0,
                expected_conditions={"intervention": source.drug, "dose": str(source.dose), "dose_unit": source.unit,
                                     "context_identifier": source.context, "time_hours": "24.0", "readout": READOUT})
            version = store.snapshot(case_id).plan_version + 1
            request = build_request(case, source, case_id, version, f"{case_id}.phase{phase}", evidence_id)
            if request.intervention.for_action(action, request.context, request.readouts) != request.intervention:
                raise ValueError("Action/request condition mismatch")
            assessment, prediction = coordinator.predict(request, request.request_id)
            if not prediction.applicable:
                raise ValueError("Qualified replay prediction refused: " + str(prediction.abstain_reason))
            plan = store.record_plan(case_id, [action], ready_to_measure=True, context_identifier=case["context"])
            if plan.plan_version != request.plan_version:
                raise ValueError("Prediction and committed plan version differ")
            envelope = dict(schema="state_response_pair_v1", request=asdict(request), prediction=asdict(prediction),
                            action=asdict(action), biological_context=case["context"],
                            checkpoint=protocol["checkpoint"], source=asdict(source), evidence_id=evidence_id)
            store.record_prediction(case_id, version, action.identifier, request.request_id, envelope)
            append(actions_path, dict(event="plan_committed", case_id=case_id, phase=phase,
                                      plan_version=version, request=asdict(request), prediction=asdict(prediction),
                                      budget=store.budget_status(case_id)))
            store.start_action(case_id, version, action.identifier, attempt_id=f"{case_id}.attempt{phase}", source="registered_public_replay")
            append(actions_path, dict(event="profile_purchase_started", case_id=case_id, phase=phase, plan_version=version))
            result_id = f"{case_id}.result{phase}"
            measurement = purchased_result(case, request, action, result_id, backend, out, actions_path)
            imported = orchestrator.import_measurement(case_id, measurement)
            retry = orchestrator.import_measurement(case_id, measurement)
            if not imported.created or retry.created or retry.snapshot.spent != phase:
                raise ValueError("Result retry charged twice or did not preserve identity")
            accepted_ids.append(result_id)
            persisted = store.measurement(case_id, result_id)
            visible = builder.build(intent, memory_scope=MemoryScope(case_id=case_id))
            foreign = builder.build(intent, memory_scope=MemoryScope(case_id="different_case"))
            if not any(e.payload.get("result_id") == result_id for e in visible.evidence):
                raise ValueError("Accepted result absent from same-case context")
            if any(e.payload.get("result_id") == result_id for e in foreign.evidence):
                raise ValueError("Result crossed case boundary")
            pair = store.prediction_for_result(case_id, result_id)
            if pair["request_id"] != request.request_id:
                raise ValueError("Accepted result linked to wrong prediction")
            if phase == 1:
                original_prediction = pair
                first_metrics = dict(measurement.metrics)
            else:
                old = store.measurement(case_id, accepted_ids[0])
                old_retry = orchestrator.import_measurement(case_id, old)
                if old_retry.created or store.prediction_for_result(case_id, old.result_id) != original_prediction:
                    raise ValueError("Old retry linked to the latest same-name action")
                if store.snapshot(case_id).spent != 2.0:
                    raise ValueError("Old retry changed budget")
            case_record["phases"].append(dict(phase=phase, source=asdict(source), request_id=request.request_id,
                plan_version=version, result_id=result_id, metrics=dict(persisted.metrics), budget=store.budget_status(case_id),
                idempotent_retry=True, same_case_visible=True, foreign_case_hidden=True,
                original_prediction_binding=True, tool_receipt_id=execution.receipt.request_id))
            append(actions_path, dict(event="result_imported", case_id=case_id, phase=phase, result_id=result_id,
                                      created=imported.created, retry_created=retry.created,
                                      accepted_plan_version=persisted.plan_version, budget=store.budget_status(case_id)))
        if len(case_record["phases"]) == 2 or case_record.get("stopped"):
            store.record_decision(case_id, status="decided")
            case_record["operational_decision"] = "registered_public_profile_review_complete; no mechanism verdict"
        elif case_record["failures"]:
            store.record_decision(case_id, status="deferred")
            case_record["operational_decision"] = "source_action_rejected; no silent fallback"
        case_record["final_state"] = store.snapshot(case_id).state.value
        case_record["final_budget"] = store.budget_status(case_id)
        case_record["first_feedback"] = first_metrics
        results.append(case_record)
        print(json.dumps(dict(case_id=case_id, phases=len(case_record["phases"]), failures=len(case_record["failures"])), ensure_ascii=False), flush=True)
    write(out / "SUMMARY.json", dict(arm="live_llm_exact_source" if live else "deterministic_exact_source", cases=results,
        completed_cases=sum(len(case["phases"]) == 2 for case in results),
        purchases=sum(len(case["phases"]) for case in results),
        spent=sum(case["final_budget"]["recorded_use"] for case in results),
        failures=sum(len(case["failures"]) for case in results),
        api_completions=provider.calls if provider else 0,
        provider_usage=provider.client.provider_usage if provider else {},
        transport_attempts=provider.client.transport_attempts if provider else 0,
        billed_api_amount=None if live else 0.0,
        billing_note="Provider response token counters; no price schedule or invoice was assumed. Retry responses lost in transport may still be billed.",
        state_backend_calls=backend.calls, fresh_state_inference_calls=0, elapsed_seconds=time.perf_counter() - started,
        calibrated_runtime_scores=len(store.prediction_scores()), protocol_sha256=digest(HERE / "PROTOCOL.json")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    run(args.out, args.live)
