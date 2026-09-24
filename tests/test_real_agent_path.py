"""The public agent entry point drives a real backend without a language model.

File summary
- Path: tests/test_real_agent_path.py
- Purpose: Pin the vertical path task -> typed contrast -> per-action query -> computed backend -> hashed artifact -> planning use -> real result import -> decision record, exercised through the CLI rather than by constructing data classes.
- Core points:
  - The reviewed template completer answers only the components it names and refuses any other call.
  - Per-action queries rank each action by the prediction for its own condition, only as a tie-break, and never discharge a premise.
  - The CLI run uses a registered asset, a declared development partition and a computed backend; its trace carries artifact digests, the imported measurement and the decision.
- Interfaces: pytest test functions
- Depends on: agent.cli, agent.orchestrator, agent.template_client, virtual_cell
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]

from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.template_client import TemplateCompleter, TemplateCompleterError
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.models import MeasurementStatus
from virtual_cell import (
    ModelCapabilities,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
)

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
LOW = "[('drugA', 0.5, 'uM')]"
HIGH = "[('drugA', 5.0, 'uM')]"
DEV_B = "[('drugB', 0.5, 'uM')]"
DEV_C = "[('drugC', 0.5, 'uM')]"
HAVE_RUNTIME = all(importlib.util.find_spec(name) for name in ("anndata", "h5py"))

TRIAGE = {
    "task_type": "mechanism_diagnosis",
    "research_question": "Is the transcriptional response of drugA realised in NCI-H596 at the tested exposure?",
    "target_or_targets": ["TARGET_A"],
    "interventions": ["drugA"],
    "biological_context": "NCI-H596",
    "phenotype_endpoint": "transcriptome shift",
    "supplied_evidence": [],
    "constraints": [],
    "missing_information": [],
    "evidence_gaps": ["proximal target activity"],
    "needs_visual_review": False,
}
PLAN = {
    "identifier": "realisation-contrast",
    "hypotheses": [
        {"identifier": "response_realised", "description": "The exposure perturbs the transcriptome.",
         "proposed_action": "continue", "causal_factor": "unresolved"},
        {"identifier": "response_not_realised", "description": "The exposure does not perturb the transcriptome.",
         "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
    ],
    "differing_assumptions": ["whether the exposure changes RNA abundance"],
    "action_identifier": "measure_low",
    "outcome_categories": ["response_detected", "no_detectable_response"],
    "interpretation_boundaries": ["An RNA-level response does not establish target engagement or viability."],
}
NO_REPAIR = {"action_identifier": None, "modified_fields": [], "rationale": "No catalog repair is needed.", "remaining_limitations": []}


def _actions() -> tuple[EvidenceAction, ...]:
    common = dict(
        cost=1.0, distinguishes=("response_realised", "response_not_realised"), time_hours=24.0,
        supplies=("realization:transcript_response",), prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
        expected_outcomes={"response_realised": "response_detected", "response_not_realised": "no_detectable_response"},
    )
    return (
        EvidenceAction("measure_low", "Measure the transcriptome shift at 0.5 uM.", **common),
        EvidenceAction("measure_high", "Measure the transcriptome shift at 5 uM.", **common),
        EvidenceAction("followup", "An assay that needs a realised response first.", 1.0,
                       ("response_realised", "response_not_realised"), prerequisites=("realization:transcript_response",)),
    )


def test_the_template_completer_answers_only_named_components():
    completer = TemplateCompleter({"task_triage": TRIAGE})
    data, response = completer.complete_json([
        {"role": "system", "content": "You are MAESTRO's scientific task triage component. Return JSON only."},
        {"role": "user", "content": "question"},
    ])
    assert data["task_type"] == "mechanism_diagnosis"
    assert response.usage["total_tokens"] == 0
    assert completer.calls[0]["component"] == "task_triage"
    with pytest.raises(TemplateCompleterError):
        completer.complete_json([{"role": "system", "content": "You are MAESTRO's mechanism-contrast planner."}])
    with pytest.raises(TemplateCompleterError):
        completer.complete_json([{"role": "system", "content": "You are an unregistered helper."}])


class LabelWorldModel:
    name = "label_stub"

    def __init__(self, values):
        self.values = values
        self.requests = []

    def capabilities(self):
        return ModelCapabilities("label_stub", "stub-1", "none", "label", ("drug",), True, False, False, None)

    def assess_query(self, request):
        self.requests.append(request)
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request):
        return StatePrediction(
            True, {"embedding_delta_l2": self.values[request.intervention.identifier]}, None, ("planning only",),
            request_id=request.request_id, model_version="stub-1", confidence=None, in_distribution=True,
            uncertainty_components={"all_sources": "unquantified in this fixture"},
        )


def _orchestrator(tmp_path: Path, world_model) -> MAESTROOrchestrator:
    client = TemplateCompleter({"task_triage": TRIAGE, "contrast_planner": PLAN, "repair_planner": NO_REPAIR})
    root = tmp_path / "state"
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "unused"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=world_model,
    )


def _template() -> VirtualCellQueryTemplate:
    return VirtualCellQueryTemplate(
        LOW, "drug", SystemContext("NCI-H596", "fixture", dataset_id="tiny", control_dataset_id="tiny"),
        ("embedding_delta_l2",), "stub-1", action_interventions={"measure_low": LOW, "measure_high": HIGH},
    )


@pytest.mark.parametrize("values, expected", [({LOW: 5.0, HIGH: 1.0}, "measure_low"), ({LOW: 1.0, HIGH: 5.0}, "measure_high")])
def test_each_action_is_ranked_by_the_prediction_for_its_own_condition(tmp_path, values, expected):
    world_model = LabelWorldModel(values)
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    turn = _orchestrator(tmp_path, world_model).run(
        "Which exposure should be measured first?", available_actions=_actions(), intervention_profile=profile,
        case_id="per-action", budget=1.0, virtual_cell_template=_template(),
    )
    assert tuple(action.identifier for action in turn.selected_actions) == (expected,)
    assert set(turn.action_predictions) == {"measure_low", "measure_high"}
    assert {request.intervention.identifier for request in world_model.requests} == {LOW, HIGH}
    assert len({request.request_id for request in world_model.requests}) == 2


def test_a_prediction_never_discharges_the_premise_it_is_about(tmp_path):
    world_model = LabelWorldModel({LOW: 9.0, HIGH: 9.0})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    turn = _orchestrator(tmp_path, world_model).run(
        "Which exposure should be measured first?", available_actions=_actions(), intervention_profile=profile,
        case_id="premise", budget=3.0, virtual_cell_template=_template(),
    )
    assert "followup" not in {action.identifier for action in turn.selected_actions}
    assert profile.measurement_status("realization:transcript_response") is MeasurementStatus.UNKNOWN


# --------------------------------------------------------------------------
# The CLI, end to end, with a registered asset and a computed backend.
# --------------------------------------------------------------------------


def _write_workspace(root: Path) -> dict[str, Path]:
    import anndata as ad
    import pandas as pd

    rng = np.random.default_rng(1)
    labels = [CONTROL] * 12 + [LOW] * 10 + [HIGH] * 10 + [DEV_B] * 10 + [DEV_C] * 10
    obs = pd.DataFrame(
        {"cell_name": ["NCI-H596"] * len(labels), "drugname_drugconc": labels, "plate": ["plate1", "plate2"] * (len(labels) // 2)},
        index=[f"cell{i}" for i in range(len(labels))],
    )
    data = ad.AnnData(obs=obs)
    data.obsm["X_hvg"] = rng.normal(size=(len(labels), 8)).astype(np.float32)
    asset = root / "data" / "tiny.h5ad"
    asset.parent.mkdir(parents=True)
    data.write_h5ad(asset)
    (root / ".env").write_text(
        "DEEPSEEK_API_KEY=unused-by-template\nDEEPSEEK_BASE_URL=http://127.0.0.1:9\nDEEPSEEK_MODEL=none\nDEEPSEEK_VISION_MODEL=none\n",
        encoding="utf-8",
    )
    registry = {
        "datasets": {"tiny": {
            "path": "data/tiny.h5ad", "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
            "size_bytes": asset.stat().st_size, "contexts": ["NCI-H596"], "context_column": "cell_name",
            "perturbation_column": "drugname_drugconc", "control_label": CONTROL, "batch_column": "plate",
            "embedding_key": "X_hvg", "feature_count": 8,
        }},
        "models": {},
    }
    (root / "data" / "virtual_cell").mkdir(parents=True)
    (root / "data" / "virtual_cell" / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
    files = {name: root / "inputs" / f"{name}.json" for name in ("actions", "profile", "template", "state", "rules", "results", "partition")}
    files["actions"].parent.mkdir(parents=True)
    files["actions"].write_text(json.dumps([
        {"identifier": identifier, "description": description, "cost": 1.0, "distinguishes": ["response_realised", "response_not_realised"],
         "kind": "rna_abundance_measurement", "quantity": "rna_abundance", "entity": "transcriptome_hvg_8", "units": "log1p_normalized_counts",
         "time_hours": 24.0, "supplies": ["realization:transcript_response"], "prediction_readout": "embedding_delta_l2",
         "prediction_relevance": 1.0, "expected_outcomes": {"response_realised": "response_detected", "response_not_realised": "no_detectable_response"}}
        for identifier, description in (("measure_low", "Transcriptome shift at 0.5 uM."), ("measure_high", "Transcriptome shift at 5 uM."))
    ]), encoding="utf-8")
    files["profile"].write_text(json.dumps({"mode": "inhibition", "context_identifier": "NCI-H596", "time_hours": 24.0}), encoding="utf-8")
    files["template"].write_text(json.dumps({"responses": {"task_triage": TRIAGE, "contrast_planner": PLAN, "repair_planner": NO_REPAIR}}), encoding="utf-8")
    files["state"].write_text(json.dumps({
        "intervention_identifier": LOW, "intervention_mode": "drug",
        "context": {"identifier": "NCI-H596", "description": "fixture", "dataset_id": "tiny", "control_dataset_id": "tiny"},
        "readouts": ["embedding_delta_l2"], "model_version": "development_mean_shift_v1",
        "action_interventions": {"measure_low": LOW, "measure_high": HIGH},
    }), encoding="utf-8")
    files["rules"].write_text(json.dumps([{
        "identifier": "transcript_response_detected", "outcome_label": "rna_level_response_detected",
        "matched_fields": ["realization:transcript_response:detected"], "scope": "intervention_implementation",
        "boundary": "An RNA-level response constrains realisation only; it is not target engagement or viability.",
    }]), encoding="utf-8")
    files["results"].write_text(json.dumps({
        identifier: {"statement": f"Observed shift for {identifier} exceeds the declared vehicle null.", "source_id": f"tiny:{identifier}",
                     "context_identifier": "NCI-H596", "time_hours": 24.0, "independent_units": 1, "quality_passed": True,
                     "evidence_kind": "real_measurement", "result_id": f"result-{identifier}",
                     "interpretation_fields": ["realization:transcript_response", "realization:transcript_response:detected"]}
        for identifier in ("measure_low", "measure_high")
    }), encoding="utf-8")
    files["partition"].write_text(json.dumps({
        "dataset_id": "tiny", "context_identifier": "NCI-H596", "unit": "drug", "rule": "fixture: drugB and drugC develop, drugA is held out",
        "development_conditions": [DEV_B, DEV_C], "held_out_conditions": [LOW, HIGH],
    }), encoding="utf-8")
    return files


@pytest.mark.skipif(not HAVE_RUNTIME, reason="anndata and h5py are required to build the asset")
def test_the_cli_runs_the_whole_path_with_a_computed_backend_and_no_language_model(tmp_path, monkeypatch):
    from agent import cli

    files = _write_workspace(tmp_path)
    trace = tmp_path / "trace.json"
    monkeypatch.setattr(sys, "argv", [
        "maestro", "Is the transcriptional response of drugA realised in NCI-H596?",
        "--workspace", str(tmp_path), "--actions", str(files["actions"]), "--profile", str(files["profile"]),
        "--planner-template", str(files["template"]), "--virtual-cell", "development_mean",
        "--development-partition", str(files["partition"]), "--dataset-id", "tiny",
        "--state-template", str(files["state"]), "--rules", str(files["rules"]), "--results", str(files["results"]),
        "--case-id", "cli-path", "--budget", "1", "--max-rounds", "2",
        "--state-directory", str(tmp_path / "state"), "--artifact-directory", str(tmp_path / "artifacts"),
        "--trace", str(trace),
    ])
    assert cli.main() == 0
    payload = json.loads(trace.read_text(encoding="utf-8"))
    assert payload["planner"] == "reviewed_template"
    first = payload["record"]["turns"][0]
    predictions = first["action_predictions"]
    assert set(predictions) == {"measure_low", "measure_high"}
    for prediction in predictions.values():
        artifact = Path(prediction["artifact_ref"])
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == prediction["artifact_sha256"]
        content = json.loads(artifact.read_text(encoding="utf-8"))
        assert content["planning_only"] is True and content["is_measurement"] is False
    # The computed baseline gives both held-out conditions the same vector, so
    # the prediction cannot break the tie and the deterministic order decides.
    assert predictions["measure_low"]["state_change"] == predictions["measure_high"]["state_change"]
    selected = [action["identifier"] for action in first["selected_actions"]]
    assert selected == ["measure_high"]
    assert payload["record"]["reflections"], "the real result must have been imported"
    assert payload["record"]["stop_reason"].startswith("decision:")
    assert payload["record"]["decision"]["status"] in {"deferred", "needs_evidence"}
