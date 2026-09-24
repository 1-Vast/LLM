"""Validate local dataset-tool discovery, selection, and safe execution.

File summary
- Path: tests/test_local_tools.py
- Purpose: Validate local dataset-tool discovery, selection, and safe execution.
- Core points:
  - `ToolRouter` rejects unregistered tools and out-of-menu dataset paths.
  - Tool outputs keep their evidence kind; they are not real measurement results.
- Interfaces: `test_*` functions, `StubClient`
- Depends on: agent.context, agent.tool_runtime, maestro
"""
from pathlib import Path

from agent.context import ContextPacket, TaskIntent
from agent.tool_runtime import ToolRouter
from maestro import EvidenceKind

from tools.shared.stub_client import StubClient  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
def _context() -> ContextPacket:
    intent = TaskIntent(
        "analysis_planning",
        "Inspect an assay dataset.",
        (),
        (),
        None,
        None,
        (),
        (),
        (),
        False,
    )
    return ContextPacket(intent, (), (), "TASK\nInspect an assay dataset.")


def test_numeric_summary_tool_uses_only_the_selected_column(tmp_path: Path):
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,10\nB,20\nC,\n", encoding="utf-8")
    router = ToolRouter(
        StubClient(
            {
                "tool_id": "column_summary",
                "dataset_id": "dataset_1",
                "arguments": {"column": "ic50"},
                "rationale": "The requested endpoint is numeric.",
            }
        ),
        ROOT / "tools",
    )

    execution = router.select_and_execute(_context(), (dataset,))

    assert execution is not None
    assert execution.tool_id == "column_summary"
    assert execution.evidence_kind is EvidenceKind.DERIVED_ANALYSIS
    assert "mean=15" in execution.observations[1]
    assert execution.limitations


def test_table_filter_tool_applies_a_declarative_condition(tmp_path: Path):
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,10\nB,20\nC,30\n", encoding="utf-8")
    router = ToolRouter(
        StubClient(
            {
                "tool_id": "table_filter",
                "dataset_id": "dataset_1",
                "arguments": {"column": "ic50", "operator": "greater_than", "value": "15"},
                "rationale": "Identify records above the selected threshold.",
            }
        ),
        ROOT / "tools",
    )

    execution = router.select_and_execute(_context(), (dataset,))

    assert execution is not None
    assert execution.tool_id == "table_filter"
    assert "matched 2 rows" in execution.observations[0]
