"""Exact metadata selection refuses incomplete, cross-context and malformed conditions."""
from dataclasses import asdict, replace
import json

import pytest

from tools.datasets.condition_sources import ConditionSource, resolve_condition_sources, run


def source(**changes):
    return replace(ConditionSource("line-A", "literal label", "Drug,A", 1.0, "uM",
                                   "plate-1", "census.json", "a" * 64), **changes)


def test_exact_scope_and_missing_conditions():
    rows = [source(), source(dose=2), source(source_group="plate-2"), source(context="line-B")]
    assert resolve_condition_sources(rows, context="line-A", drug="Drug,A").status == "clarify_requested_dose_and_unit"
    ambiguous = resolve_condition_sources(rows, context="line-A", drug="Drug,A", dose=1, unit="uM")
    assert ambiguous.status == "resolve_source_identity" and len(ambiguous.candidates) == 2
    exact = resolve_condition_sources(rows, context="line-A", drug="Drug,A", dose=1, unit="uM", source_group="plate-1")
    assert exact.status == "resolved" and exact.candidates == (rows[0],)
    for changes in ({"unit": "nM"}, {"drug": "drug,a"}, {"source_sha256": "b" * 64}):
        request = dict(context="line-A", drug="Drug,A", dose=1, unit="uM")
        request.update(changes)
        assert resolve_condition_sources(rows, **request).status == "no_registered_source"


@pytest.mark.parametrize("dose", [True, False, "1", -1, float("nan"), float("inf"), float("-inf")])
def test_invalid_dose_refused_in_record_and_request(dose):
    with pytest.raises(ValueError):
        source(dose=dose)
    with pytest.raises(ValueError):
        resolve_condition_sources([source()], context="line-A", drug="Drug,A", dose=dose)


def test_endpoint_retains_source_metadata_without_promoting_authority(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps([asdict(source())]), encoding="utf-8")
    result = run(dict(dataset_path=str(path), context="line-A", drug="Drug,A", dose=1, unit="uM"))
    assert result["payload"] == {"status": "resolved", "candidates": [asdict(source())]}
    assert "not authenticated" in result["limitations"][0]
    assert "No measured target state" in result["limitations"][1]


def test_duplicate_identity_is_ambiguous_and_invalid_hash_refused():
    result = resolve_condition_sources([source(), source()], context="line-A", drug="Drug,A", dose=1, unit="uM")
    assert result.status == "resolve_source_identity"
    with pytest.raises(ValueError):
        resolve_condition_sources([source()], context="line-A", drug="Drug,A", source_sha256="invalid")


def test_real_router_endpoint(tmp_path):
    from pathlib import Path
    from agent.context import ContextPacket, TaskIntent
    from agent.tool_runtime import ToolRouter
    from maestro.models import EvidenceKind
    from tests.fixtures.stub_client import StubClient

    path = tmp_path / "sources.json"
    path.write_text(json.dumps([asdict(source())]), encoding="utf-8")
    client = StubClient({"tool_id": "condition_sources", "dataset_id": "dataset_1",
                         "arguments": {"context": "line-A", "drug": "Drug,A", "dose": 1, "unit": "uM"},
                         "rationale": "Resolve the literal source metadata."})
    context = ContextPacket(TaskIntent("analysis_planning", "Resolve source.", (), (), None, None, (), (), (), False), (), (), "Resolve source.")
    execution = ToolRouter(client, Path(__file__).resolve().parents[1] / "tools").select_and_execute(context, (path,))
    assert execution is not None
    assert execution.evidence_kind is EvidenceKind.DERIVED_ANALYSIS
    assert execution.payload["status"] == "resolved"
    assert execution.payload["candidates"] == [asdict(source())]


def test_zero_budget_accepts_distinct_sources_and_stops_exact_repeat(tmp_path):
    from pathlib import Path
    from agent.context import ContextPacket, TaskIntent
    from agent.tool_runtime import ToolBudget, ToolRouter
    from tests.fixtures.stub_client import StubClient

    path = tmp_path / "sources.json"
    rows = [source(), source(source_group="plate-2")]
    path.write_text(json.dumps([asdict(row) for row in rows]), encoding="utf-8")
    def selection(group):
        return {"tool_id": "condition_sources", "dataset_id": "dataset_1", "arguments": {
            "context": "line-A", "drug": "Drug,A", "dose": 1, "unit": "uM", "source_group": group,
        }, "rationale": "Resolve a distinct declared source."}
    client = StubClient([selection("plate-1"), selection("plate-2"), selection("plate-2")])
    context = ContextPacket(TaskIntent("analysis_planning", "Resolve sources.", (), (), None, None, (), (), (), False),
                            (), (), "Resolve sources.")
    budget = ToolBudget(0.)
    executions = ToolRouter(client, Path(__file__).resolve().parents[1] / "tools", budget=budget).select_and_execute_many(
        context, (path,), max_steps=3)
    assert [item.payload["candidates"][0]["source_group"] for item in executions] == ["plate-1", "plate-2"]
    assert all(item.receipt.parameters["dataset_path"] == str(path.resolve()) for item in executions)
    assert budget.snapshot() == {"limit": 0., "spent": 0., "remaining": 0.}
