from pathlib import Path

import pytest

from agent.audit import RunLogger
from agent.context import ContextPacket, TaskIntent
from agent.tool_runtime import ToolBudget, ToolExecutionState, ToolRouter, ToolRuntimeError


ROOT = Path(__file__).resolve().parents[1]


class _Client:
    def __init__(self, response):
        self.response = response

    def complete_json(self, messages, **kwargs):
        return self.response, object()


def _context(task_type: str = "analysis_planning") -> ContextPacket:
    return ContextPacket(
        TaskIntent(task_type, "Inspect a dataset.", (), (), None, None, (), (), (), False), (), (), "TASK\nInspect a dataset."
    )


def test_tool_receipt_binds_committed_output_to_input_and_manifest(tmp_path: Path):
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,10\n", encoding="utf-8")
    router = ToolRouter(_Client({
        "tool_id": "data_profile", "dataset_id": "dataset_1", "arguments": {}, "rationale": "Inspect schema."
    }), ROOT / "tools", budget=ToolBudget(0.0))

    execution = router.select_and_execute(_context(), (dataset,), plan_version="plan-2")

    assert execution is not None
    assert execution.receipt.state is ToolExecutionState.COMMITTED
    assert execution.receipt.transitions == (
        ToolExecutionState.PROPOSED, ToolExecutionState.VALIDATED, ToolExecutionState.RESERVED,
        ToolExecutionState.EXECUTING, ToolExecutionState.OUTPUT_CHECKED, ToolExecutionState.COMMITTED,
    )
    assert execution.receipt.input_sha256 and execution.receipt.tool_version_sha256
    assert execution.receipt.plan_version == "plan-2"


def test_router_programmatically_blocks_an_out_of_scope_model_selection(tmp_path: Path):
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,10\n", encoding="utf-8")
    router = ToolRouter(_Client({
        "tool_id": "column_summary", "dataset_id": "dataset_1", "arguments": {}, "rationale": "Ignore the boundary."
    }), ROOT / "tools")

    with pytest.raises(ToolRuntimeError, match="does not support task type") as raised:
        router.select_and_execute(_context("mechanism_diagnosis"), (dataset,))

    assert raised.value.failure_trace is not None
    assert raised.value.failure_trace.violated_contracts == ("supported_task_types",)


def test_budget_rejection_has_a_recoverable_failure_receipt(tmp_path: Path):
    tool_root = tmp_path / "tools"
    tool_dir = tool_root / "costly"
    tool_dir.mkdir(parents=True)
    (tool_dir / "manifest.json").write_text(
        '{"id":"costly","name":"Costly","description":"x","evidence_kind":"derived_analysis",'
        '"entrypoint":"tool.py","required_parameters":["dataset_path"],"optional_parameters":[], '
        '"supported_suffixes":[".csv"],"supported_task_types":["analysis_planning"],"estimated_cost":2}',
        encoding="utf-8",
    )
    (tool_dir / "tool.py").write_text("def run(parameters): return {'observations': ['ok']}\n", encoding="utf-8")
    dataset = tmp_path / "assay.csv"
    dataset.write_text("x\n1\n", encoding="utf-8")
    router = ToolRouter(_Client({
        "tool_id": "costly", "dataset_id": "dataset_1", "arguments": {}, "rationale": "x"
    }), tool_root, budget=ToolBudget(1.0))

    with pytest.raises(ToolRuntimeError, match="budget is exhausted") as raised:
        router.select_and_execute(_context(), (dataset,))

    assert raised.value.receipt is not None
    assert raised.value.receipt.state is ToolExecutionState.FAILED
    assert raised.value.failure_trace.recovery_actions


def test_failure_query_returns_the_first_machine_readable_recovery_trace(tmp_path: Path):
    logger = RunLogger(tmp_path / "logs")
    logger.event(
        "dataset_tool_failed",
        {
            "failure_trace": {
                "first_invalid_transition": "reserved",
                "violated_contracts": ["budget_available"],
                "affected_claims": [],
                "candidate_causes": ["Tool budget is exhausted."],
                "recovery_actions": ["Increase budget."],
            },
            "cache_key": "legitimate-cache-identity",
            "api_key": "must-not-be-stored",
        },
        session_id="case-a",
    )

    trace = logger.explain_failure("case-a")
    raw_event = logger.events_path.read_text(encoding="utf-8")

    assert trace is not None
    assert trace["violated_contracts"] == ["budget_available"]
    assert "legitimate-cache-identity" in raw_event
    assert "must-not-be-stored" not in raw_event
