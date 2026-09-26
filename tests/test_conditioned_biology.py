"""Biological assertions must retain conditions, provenance and epistemic limits."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.biology import BiologicalConditions, BiologicalRelation
from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import MemoryScope, MemoryStore
from maestro.models import EvidenceKind
from maestro.tool_analysis import evidence_bundle_optimize, multimodal_alignment


def ledger_at(tmp_path):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    for name in ("paper", "replication"):
        ledger.register_source(name, url=f"https://example.org/{name}", locator="Figure 1",
                               cluster=name, access_level="public", hash=hashlib.sha256(name.encode()).hexdigest())
    return ledger


def relation(**changes):
    return replace(BiologicalRelation(
        "A", "activation", "B", "experimental", "regulatory_association", "perturbation",
        BiologicalConditions(species="human", tissue="lung", cell_type="epithelial", context="cells",
                             perturbation="knockdown", time_hours=24),
        publication="doi:fixture", controls=("matched vehicle",), limitations=("Synthetic contract fixture.",),
    ), **changes)


def add(ledger, item, **kwargs):
    return ledger.add_biological_relation(item, source_ids=("paper",), statement="A regulates B", **kwargs)


def test_conditions_filter_actual_agent_context_without_erasing_unknowns(tmp_path):
    ledger = ledger_at(tmp_path)
    matched = add(ledger, relation())
    other = add(ledger, relation(conditions=BiologicalConditions(context="other", time_hours=24)))
    unknown = add(ledger, relation(conditions=BiologicalConditions(context="cells")))
    intent = TaskIntent("mechanism_diagnosis", "Review A", ("A",), (), "cells", "viability", (), (), (), False)
    packet = ContextBuilder(ledger, MemoryStore(tmp_path / "memory.sqlite")).build(
        intent, biological_conditions=BiologicalConditions(context="cells", time_hours=24))
    records = {item.identifier: item for item in packet.evidence}
    assert other.identifier not in records
    assert records[matched.identifier].payload["condition_match"] == "matched"
    assert records[unknown.identifier].payload["unknown_conditions"] == ["time_hours"]
    assert '"decision_use":"hypothesis_and_measurement_planning_only"' in packet.rendered
    assert all(item.evidence_kind is EvidenceKind.RETRIEVED_SOURCE for item in records.values())


def test_opposite_signs_keep_their_contexts_and_retraction_removes_conflict(tmp_path):
    ledger = ledger_at(tmp_path)
    first = add(ledger, relation())
    second = ledger.add_biological_relation(relation(relation_type="inhibition"),
                                          source_ids=("replication",), statement="A inhibits B")
    other = add(ledger, relation(relation_type="inhibition", conditions=BiologicalConditions(context="other")))
    records = {r.identifier: r for r in ledger.retrieve("A", entities=("A",))}
    assert len(records) == 3
    conflicts = records[first.identifier].payload["conflict_candidates"]
    assert conflicts == [{"evidence_id": second.identifier, "reason": "opposite_sign_same_conditions"}]
    assert records[other.identifier].payload["conflict_candidates"] == []
    ledger.retract_source("replication")
    records = {r.identifier: r for r in ledger.retrieve("A", entities=("A",))}
    assert second.identifier not in records
    assert records[first.identifier].payload["conflict_candidates"] == []


@pytest.mark.parametrize("method", ["attention", "feature_importance"])
@pytest.mark.parametrize("level", ["correlation", "regulatory_association", "causal_effect"])
def test_feature_attribution_cannot_be_registered_as_regulation(method, level):
    with pytest.raises(ValueError, match="neither regulation nor causality"):
        relation(method=method, evidence_type="computational", claim_level=level)


def test_causality_requires_controls_and_prediction_lineage_cannot_be_experimental(tmp_path):
    with pytest.raises(ValueError, match="declared controls"):
        relation(claim_level="causal_effect", controls=())
    ledger = ledger_at(tmp_path)
    prediction = ledger.add_evidence("Predicted B", source="model", context="cells", status=EvidenceStatus.PREDICTED)
    with pytest.raises(ValueError, match="lineage"):
        add(ledger, relation(), lineage_ids=(prediction.identifier,))
    with pytest.raises(ValueError, match="not a case measurement"):
        add(ledger, relation(), evidence_kind=EvidenceKind.REAL_MEASUREMENT)
    with pytest.raises(ValueError, match="registered source lineage"):
        ledger.add_evidence("A activates B", source="paper", context="cells", status=EvidenceStatus.RETRIEVED,
                            payload={"biology": asdict(relation())})


def test_context_controls_graph_expansion_and_unknown_time_does_not_match(tmp_path):
    ledger = ledger_at(tmp_path)
    edge = add(ledger, relation())
    neighbor = ledger.add_evidence("Downstream observation", source="paper", context="review",
                                   status=EvidenceStatus.RETRIEVED, entities=("B",))
    for conditions, expected in [(BiologicalConditions(context="cells", time_hours=24), True),
                                 (BiologicalConditions(context="other"), False),
                                 (BiologicalConditions(context="cells", time_hours=48), False)]:
        ids = {r.identifier for r in ledger.retrieve("no-lexical-match", entities=("A",), biological_conditions=conditions)}
        assert (neighbor.identifier in ids) is expected
    ledger.retract_evidence(edge.identifier)
    add(ledger, relation(conditions=BiologicalConditions(context="cells")))
    ids = {r.identifier for r in ledger.retrieve("no-lexical-match", entities=("A",),
                                               biological_conditions=BiologicalConditions(time_hours=24))}
    assert neighbor.identifier not in ids


def test_prediction_trace_is_bidirectional_and_case_isolated(tmp_path):
    ledger = ledger_at(tmp_path)
    assertion = add(ledger, relation(), partition="knowledge")
    predicted = ledger.add_evidence("Predicted B", source="model", context="cells", status=EvidenceStatus.PREDICTED,
                                    lineage_ids=(assertion.identifier,), case_id="one")
    scope = MemoryScope(case_id="one")
    forward = ledger.trace_evidence(predicted.identifier, scope=scope)
    assert forward["ancestor_ids"] == [assertion.identifier]
    assert forward["sources"][0]["locator"] == "Figure 1"
    assert ledger.trace_evidence(assertion.identifier, scope=scope)["descendant_ids"] == [predicted.identifier]
    assert ledger.trace_evidence(assertion.identifier, scope=MemoryScope(case_id="two"))["descendant_ids"] == []
    assert ledger.trace_evidence(predicted.identifier, scope=MemoryScope(case_id="two")) == {}
    ledger.retract_evidence(assertion.identifier)
    assert ledger.trace_evidence(predicted.identifier, scope=scope) == {}


def test_package_import_validates_biology_atomically_and_is_idempotent(tmp_path):
    ledger = ledger_at(tmp_path)
    package = {"schema_version": "1.0", "package_id": "fixture-v1",
               "sources": [asdict(ledger.get_source("paper"))], "constraints": [
                   {"id": "edge", "statement": "A activates B", "source_ids": ["paper"],
                    "limitations": "Fixture only", "biology": asdict(relation())}]}
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")
    first = ledger.load_knowledge_package(path)
    assert ledger.load_knowledge_package(path) == first
    assert first[0].entities == ("A", "B")
    package["package_id"] = "invalid-v2"
    package["constraints"].append({**package["constraints"][0], "id": "invalid",
                                   "biology": {**asdict(relation()), "method": "attention"}})
    path.write_text(json.dumps(package), encoding="utf-8")
    with pytest.raises(ValueError):
        ledger.load_knowledge_package(path)
    assert len(ledger.retrieve("A", entities=("A",))) == 1


def test_retained_literature_hashes_and_import_are_reproducible(tmp_path):
    path = Path(__file__).resolve().parents[1] / "research/knowledge/framework_constraints.json"
    package = json.loads(path.read_text(encoding="utf-8"))
    for source, constraint in zip(package["sources"], package["constraints"]):
        assert source["hash"] == hashlib.sha256(constraint["source_abstract"].encode()).hexdigest()
    records = ledger_at(tmp_path).load_knowledge_package(path)
    assert len(records) == 2
    assert all(r.partition == "knowledge" and r.status is EvidenceStatus.RETRIEVED for r in records)


def test_cli_prediction_artifacts_follow_run_isolation_unless_overridden(tmp_path, monkeypatch):
    from agent import cli
    captured = []
    monkeypatch.setattr(cli, "build_backend", lambda name, **kwargs: captured.append(kwargs))
    args = SimpleNamespace(virtual_cell="state", workspace=tmp_path, dataset_id="dataset",
                           development_partition=None, artifact_directory=None, state_directory=tmp_path / "run")
    cli._virtual_cell(args)
    assert captured[-1]["artifact_directory"] == tmp_path / "run" / "artifacts"
    args.artifact_directory = tmp_path / "explicit"
    cli._virtual_cell(args)
    assert captured[-1]["artifact_directory"] == tmp_path / "explicit"


def bundle():
    return {"schema_version": "1.0", "budget": 4, "cost_unit": "USD", "context": "cells", "time_hours": 24,
            "required": ["transcription", "activity"],
            "sources": [{"id": "rna", "independence_group": "study-rna"},
                        {"id": "activity", "independence_group": "study-activity"}],
            "actions": [{"id": name, "cost": 2, "cost_unit": "USD", "distinguishes": [premise],
                         "source_ids": [source], "context": "cells", "time_hours": 24, "independent_unit": name,
                         "quantity": quantity, "detection_power": 0.8,
                         "data_origin": "existing_public" if source == "rna" else "new_experiment",
                         "cost_breakdown": {"access": 0, "preprocessing": 1, "compute": 1, "new_measurement": 0}
                         if source == "rna" else {"access": 0, "preprocessing": 0, "compute": 0, "new_measurement": 2}}
                        for name, premise, source, quantity in [("rna", "transcription", "rna", "rna_abundance"),
                                                              ("rna_copy", "transcription", "rna", "rna_abundance"),
                                                              ("activity", "activity", "activity", "proximal_activity")]]}


def optimize(tmp_path, data):
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return evidence_bundle_optimize({"dataset_path": str(path)})["payload"]


def test_public_data_has_processing_cost_and_complementary_quantities_beat_copies(tmp_path):
    data = bundle()
    result = optimize(tmp_path, data)
    assert result["selected_action_ids"] == ["activity", "rna"]
    assert result["total_cost"] == 4
    assert all(row["conditional_coverage_gain"] == pytest.approx(0.8) for row in result["quantity_contributions"])
    assert result["cost_breakdowns"]["rna"]["new_measurement"] == 0
    data["required"] = ["transcription"]
    data["actions"] = data["actions"][:2]
    assert optimize(tmp_path, data)["selected_action_ids"] == ["rna"]


@pytest.mark.parametrize("change", [{"compute": -1}, {"compute": True}, {"compute": 5},
                                    {"new_measurement": 1, "compute": 0}])
def test_cost_breakdown_cannot_hide_or_relabel_measurement_cost(tmp_path, change):
    data = bundle()
    data["actions"][0]["cost_breakdown"].update(change)
    with pytest.raises(ValueError):
        optimize(tmp_path, data)


def test_batch_mismatch_is_reported_without_correction_or_directional_inference(tmp_path):
    common = {"pair_id": "p", "source_id": "s", "context": "cells", "time_hours": 24,
              "independent_unit": "sample", "replicate": "r", "entity": "A", "contrast_id": "treated",
              "feature": "A", "unit": "relative", "reference_value": 1}
    records = [{**common, "id": "rna", "modality": "transcript", "quantity": "rna_abundance", "value": 2, "batch_id": "one"},
               {**common, "id": "protein", "modality": "protein", "quantity": "protein_abundance", "value": 0, "batch_id": "two"}]
    path = tmp_path / "modalities.json"
    path.write_text(json.dumps({"schema_version": "1.0", "sources": [{"id": "s", "independence_group": "study"}],
                                "records": records}), encoding="utf-8")
    result = multimodal_alignment({"dataset_path": str(path)})["payload"]
    assert result["contradiction_candidates"] == []
    assert result["alignment_qc"]["batch_reviews"] == [
        {"record_ids": ["rna", "protein"], "reason": "batch_mismatch", "correction_applied": False}]
