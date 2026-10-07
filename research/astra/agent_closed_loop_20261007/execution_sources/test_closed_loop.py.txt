"""Scientific-authority and conditions boundaries of the registered replay task."""
from __future__ import annotations

import importlib.util
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pytest

from agent.case_store import CaseStore, MeasurementResult
from agent.context import ContextBuilder
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryScope, MemoryStore
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
from tools.datasets.condition_sources import ConditionSource
from virtual_cell.interface import QuerySupport, safe_predict

spec = importlib.util.spec_from_file_location("agent_closed_loop_run", Path(__file__).with_name("run.py"))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def fake_world(tmp_path):
    """Small synthetic artifact for contracts; never a biological performance result."""
    artifact = tmp_path / "source.npz"
    label = "[('A', 0.5, 'uM')]"
    np.savez(artifact, label=np.array([label]), plate=np.array(["p1"]), paired_delta=np.array([[.1, .2]]))
    source = ConditionSource("L", label, "A", .5, "uM", "p1", str(artifact), study.digest(artifact))
    backend = object.__new__(study.CachedNativeSTATE)
    backend.sources = (source,)
    backend.protocol = {"checkpoint": {"sha256": "c" * 64}}
    backend.arrays = {str(artifact): dict(np.load(artifact))}
    backend.original_receipts = {str(artifact): {"basal": {"p1": {"sha256": "b" * 64}}}}
    backend.calls = 0
    from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
    request = PredictionRequest("test.req", "case", "source", 1, Intervention("A", "drug", (), .5, "uM", 24.),
        SystemContext("L", "test", str(artifact), "b" * 64), (study.READOUT,), study.MODEL,
        observation_context={"label": label, "plate": "p1", "source_sha256": source.source_sha256,
                             "basal_input_sha256": "b" * 64, "checkpoint_sha256": "c" * 64,
                             "native_axis": "X_hvg:2000", "tool_evidence_id": "tool:qualified"})
    return backend, request


@pytest.mark.parametrize("error,reason", [
    ("time", "registered_24h_exposure"),
    ("readout", "native_RNA_readout"),
    ("control", "exact_basal_control"),
    ("checkpoint", "original_checkpoint_identity"),
    ("axis", "original_input_axis"),
    ("source", "no_registered_source"),
])
def test_metadata_resolution_cannot_grant_other_native_conditions(tmp_path, error, reason):
    backend, request = fake_world(tmp_path)
    if error == "time":
        request = replace(request, intervention=replace(request.intervention, time_hours=72.))
    elif error == "readout":
        request = replace(request, readouts=("ATP",))
    elif error == "control":
        request = replace(request, context=replace(request.context, control_dataset_id="wrong"))
    else:
        key = {"checkpoint": "checkpoint_sha256", "axis": "native_axis", "source": "source_sha256"}[error]
        request = replace(request, observation_context={**request.observation_context, key: "d" * 64})
    assessment, prediction = safe_predict(backend, request)
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert reason in assessment.missing_inputs
    assert not prediction.applicable
    assert backend.calls == 0


def test_qualified_cached_forecast_retains_unknown_confidence(tmp_path):
    backend, request = fake_world(tmp_path)
    assessment, prediction = safe_predict(backend, request)
    assert assessment.support is QuerySupport.SUPPORTED
    assert prediction.applicable and prediction.request_id == request.request_id
    assert prediction.artifact_sha256 == backend.sources[0].source_sha256
    assert prediction.confidence is None and prediction.in_distribution is None
    assert prediction.calibration_basis is None
    assert prediction.state_change[study.READOUT] == pytest.approx(np.sqrt(.025))


def test_preacquisition_source_identity_is_not_assumed(tmp_path):
    backend, request = fake_world(tmp_path)
    request = replace(request, observation_context={key: value for key, value in request.observation_context.items()
                                                   if key not in ("source_sha256", "tool_evidence_id")})
    assessment, prediction = safe_predict(backend, request)
    assert not prediction.applicable and backend.calls == 0
    assert "missing_source_binding:source_sha256" in assessment.missing_inputs


@pytest.mark.parametrize("error,noise", [("nan", ".1"), ("inf", ".1"), (".1", "nan"), ("-.1", ".1")])
def test_nonfinite_feedback_cannot_choose_second_profile(error, noise):
    with pytest.raises(ValueError):
        study.should_verify({"profile_mse": error, "sampling_noise_estimate": noise})


def test_registered_feedback_changes_next_request_with_fixed_conditions():
    assert study.should_verify({"profile_mse": ".2", "sampling_noise_estimate": ".1"})
    assert not study.should_verify({"profile_mse": ".05", "sampling_noise_estimate": ".1"})


def test_public_result_restart_retry_does_not_become_real_measurement(tmp_path):
    backend, request = fake_world(tmp_path)
    store = CaseStore(tmp_path / "facts.sqlite")
    store.open_case("case", budget=2.)
    action = EvidenceAction("native_profile", "public profile", 1., (), kind=EvidenceActionKind.EVIDENCE_REVIEW)
    store.record_plan("case", [action], ready_to_measure=True, context_identifier="L")
    store.record_prediction("case", 1, action.identifier, request.request_id, {"prediction": asdict(backend.predict(request))})
    result = MeasurementResult(action.identifier, "A native profile", "public:well1", "L", 24., 1, True,
                               metrics={"profile_mse": ".2", "sampling_noise_estimate": ".1"},
                               evidence_kind=EvidenceKind.RETRIEVED_SOURCE, result_id="first", plan_version=1)
    assert store.import_measurement("case", result).created
    # Simulate crash between authoritative fact write and evidence projection.
    store = CaseStore(tmp_path / "facts.sqlite")
    imported = store.import_measurement("case", result)
    assert not imported.created and imported.snapshot.spent == 1.
    builder = ContextBuilder(EvidenceLedger(tmp_path / "evidence.sqlite"), MemoryStore(tmp_path / "memory.sqlite"))
    first = builder.record_result(store.measurement("case", "first"), case_id="case")
    assert builder.record_result(store.measurement("case", "first"), case_id="case").identifier == first.identifier
    case = {"context": "L", "drug": "A", "dose": .5, "unit": "uM", "label": backend.sources[0].label}
    intent = study.task_intent(case, 2, "p2")
    assert any(e.identifier == first.identifier for e in builder.build(intent, memory_scope=MemoryScope(case_id="case")).evidence)
    assert not builder.build(intent, memory_scope=MemoryScope(case_id="other")).evidence
    store.record_plan("case", [action], ready_to_measure=True, context_identifier="L")
    store.record_prediction("case", 2, action.identifier, "second.req", {"unscored": "second"})
    old = store.import_measurement("case", result)
    assert not old.created and old.snapshot.spent == 1.
    assert store.prediction_for_result("case", "first")["request_id"] == request.request_id
    with pytest.raises(ValueError, match="qualified real measurement"):
        store.record_prediction_score("case", "first", request.request_id, {"error": .2}, conditions_matched=True)
