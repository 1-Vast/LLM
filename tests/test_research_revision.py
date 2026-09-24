"""Regression tests for provenance, structured planning and visibility boundaries."""
from dataclasses import replace
import json

import pytest

from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import MemoryStore
from maestro import EvidenceAction, FunctionalInterventionProfile
from maestro.acquisition import select_expected_coverage
from maestro.tool_analysis import evidence_bundle_optimize, multimodal_alignment
from agent.configuration import MAESTROSettings
from agent.llm import DeepSeekChatClient
from agent.planner import MechanismContrastPlanner


def test_duplicate_source_cannot_buy_independent_coverage():
    a = EvidenceAction("a", "First view", 1, ("h",), source_ids=("study",), detection_power=0.6)
    b = replace(a, identifier="b")
    c = replace(a, identifier="c", source_ids=("independent",), detection_power=0.5)
    answer = select_expected_coverage(frozenset({"h"}), (a, b, c), FunctionalInterventionProfile("drug"), 2)
    assert [item.identifier for item in answer.plan.actions] == ["a", "c"]
    assert answer.expected_coverage == pytest.approx(0.8)


def test_registered_tool_respects_declared_source_clusters(tmp_path):
    data = {"schema_version": "1.0", "budget": 2, "cost_unit": "retrieval", "context": "cells",
            "time_hours": 24, "required": ["h"],
            "sources": [{"id": s, "independence_group": g} for s, g in [("s1", "same"), ("s2", "same"), ("s3", "other")]],
            "actions": [{"id": a, "cost": 1, "cost_unit": "retrieval", "context": "cells", "time_hours": 24,
                         "distinguishes": ["h"], "source_ids": [s], "independent_unit": "well",
                         "quantity": "viability", "detection_power": p}
                        for a, s, p in [("a", "s1", 0.6), ("b", "s2", 0.6), ("c", "s3", 0.5)]]}
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = evidence_bundle_optimize({"dataset_path": str(path)})["payload"]
    assert result["selected_action_ids"] == ["a", "c"]
    assert result["expected_coverage"] == pytest.approx(0.8)


def test_planner_receives_structured_evidence_and_atomic_budget(tmp_path):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    payload = {"tool_payload": {"abstain_reason": "readout_not_served", "values": None},
               "receipt": {"input_sha256": "abc", "plan_version": "v1"}}
    record = ledger.add_evidence("EGFR prediction unavailable", source="tool:virtual_cell_query:input.json",
                                 context="Prediction only", status=EvidenceStatus.RETRIEVED, payload=payload)
    intent = TaskIntent("mechanism_diagnosis", "Review EGFR", ("EGFR",), (), "cells", "viability", (), (), (), False)
    memory = MemoryStore(tmp_path / "memory.sqlite")
    full = ContextBuilder(ledger, memory).build(intent)
    assert json.loads(full.rendered.split("STRUCTURED_DATA: ", 1)[1]) == payload
    assert record.identifier in full.included_record_ids
    small = ContextBuilder(ledger, memory, max_characters=len(full.rendered) - 1).build(intent)
    assert record.identifier in small.omitted_record_ids
    assert "EGFR prediction unavailable" not in small.rendered


def test_multimodal_visibility_never_releases_hidden_values(tmp_path):
    path = tmp_path / "paired.json"
    data = {"schema_version": "1.0", "sources": [], "records": [
        {"id": "hidden", "value": "DO_NOT_REVEAL"}],
        "visibility": {"stage": "pre_experiment", "available_record_ids": [],
                       "acquisition_cost": 0, "cost_unit": "record_retrieval"}}
    path.write_text(json.dumps(data), encoding="utf-8")
    result = multimodal_alignment({"dataset_path": str(path)})["payload"]
    assert "DO_NOT_REVEAL" not in json.dumps(result)
    assert result["records"] == []
    assert result["visibility"]["withheld_record_ids"] == ["hidden"]
    assert result["contradiction_candidates"] == []


@pytest.mark.parametrize("cost", [-1, True, float("nan")])
def test_multimodal_visibility_refuses_invalid_cost(tmp_path, cost):
    path = tmp_path / "paired.json"
    path.write_text(json.dumps({"schema_version": "1.0", "sources": [], "records": [{"id": "hidden"}],
                               "visibility": {"stage": "post_acquisition", "available_record_ids": [],
                                              "acquisition_cost": cost, "cost_unit": "retrieval"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        multimodal_alignment({"dataset_path": str(path)})


def test_source_overlap_is_transitive_and_permutation_invariant():
    actions = tuple(EvidenceAction(name, name, 1, ("h",), source_ids=refs, detection_power=0.6)
                    for name, refs in [("a", ("s1",)), ("b", ("s1", "s2")), ("c", ("s2",))])
    for order in (actions, actions[::-1]):
        result = select_expected_coverage(frozenset({"h"}), order, FunctionalInterventionProfile("drug"), 3)
        assert result.expected_coverage == pytest.approx(0.6)
        assert [a.identifier for a in result.plan.actions] == ["a"]
        assert len(set(result.dependence_groups.values())) == 1


@pytest.mark.parametrize("cost", [float("nan"), float("inf"), True, -1])
def test_core_selector_rejects_invalid_cost_before_search(cost):
    action = EvidenceAction("a", "assay", cost, ("h",))
    with pytest.raises(ValueError, match="invalid_action_cost"):
        select_expected_coverage(frozenset({"h"}), (action,), FunctionalInterventionProfile("drug"), 2)


def test_source_aliases_are_resolved_from_knowledge(tmp_path):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    for identifier in ("paper", "database"):
        ledger.register_source(identifier, url="https://example.org/study", locator="abstract", cluster="original-study",
                               access_level="public", hash="a" * 64)
    builder = ContextBuilder(ledger, MemoryStore(tmp_path / "memory.sqlite"))
    assert builder.source_groups(("paper", "database", "unknown")) == {
        "paper": "original-study", "database": "original-study", "unknown": "unknown"}


def test_planner_menu_is_complete_json(tmp_path):
    action = EvidenceAction("a", "Assay", 2, ("h1", "h2"), source_ids=("study",), detection_power=0.6,
                            expected_outcomes={"h1": "low", "h2": "high"})
    class Client:
        def complete_json(self, messages):
            menu = json.loads(messages[1]["content"].split("AVAILABLE_ACTIONS\n")[1])
            assert menu[0]["cost"] == 2 and menu[0]["detection_power"] == 0.6
            assert menu[0]["source_ids"] == ["study"]
            assert menu[0]["expected_outcomes"] == {"h1": "low", "h2": "high"}
            return {"hypotheses": [{"identifier": "h1"}, {"identifier": "h2"}], "action_identifier": "a"}, None
    builder = ContextBuilder(EvidenceLedger(tmp_path / "evidence.sqlite"), MemoryStore(tmp_path / "memory.sqlite"))
    intent = TaskIntent("mechanism_diagnosis", "Review EGFR", ("EGFR",), (), "cells", "viability", (), (), (), False)
    MechanismContrastPlanner(Client()).propose(builder.build(intent), (action,))


def test_provider_thinking_toggle_is_explicit_and_default_is_unchanged(tmp_path):
    client = DeepSeekChatClient(MAESTROSettings("test-key", "https://example.org", "model", "vision", tmp_path))
    requests = []
    def send(request):
        requests.append(json.loads(request.data))
        return {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}], "usage": {}}
    client._send = send
    client.complete([], thinking_enabled=False)
    client.complete([])
    assert requests[0]["thinking"] == {"type": "disabled"}
    assert "thinking" not in requests[1]
    with pytest.raises(ValueError, match="thinking_enabled"):
        client.complete([], thinking_enabled="false")
