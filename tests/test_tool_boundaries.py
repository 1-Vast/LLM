"""Tool manifests must carry an applicability boundary into selection.

File summary
- Path: tests/test_tool_boundaries.py
- Purpose: Pin the tool-manifest applicability contract (use_when / do_not_use_when).
- Core points:
  - Registered manifests parse their declared boundaries into the descriptor.
  - The router's selection prompt exposes the boundaries to the selecting model.
- Interfaces: `test_*` functions
- Depends on: agent.tool_runtime
"""
from pathlib import Path

import pytest

from agent.context import ContextPacket, TaskIntent
from agent.tool_runtime import LocalToolCatalog, ToolRouter, ToolRuntimeError


ROOT = Path(__file__).resolve().parents[1]


class _RefusingClient:
    def __init__(self):
        self.messages = []

    def complete_json(self, messages, **kwargs):
        self.messages.append(messages)
        return {"tool_id": None, "dataset_id": None, "arguments": {}, "rationale": "Out of scope."}, object()


def test_registered_manifests_expose_their_applicability_boundaries():
    descriptors = LocalToolCatalog(ROOT / "tools").discover()
    assert descriptors, "The registered tool set must not be empty."
    for descriptor in descriptors:
        assert descriptor.use_when, descriptor.identifier
        assert descriptor.do_not_use_when, descriptor.identifier


def test_the_catalog_discovers_only_manifested_tools():
    """Discovery globs `tools/*/manifest.json`, so support code is never offered.

    `tools/shared/` holds the fixture and client stand-ins the tests and offline
    runners use. It carries no manifest on purpose: if it did, the router would
    offer it to the selecting model as a dataset tool, and a fixture builder is not
    one. This pins both halves of that statement.
    """

    identifiers = {descriptor.identifier for descriptor in LocalToolCatalog(ROOT / "tools").discover()}
    assert identifiers == {"column_summary", "data_profile", "table_filter", "evidence_bundle_optimize", "multimodal_alignment", "typed_decision_review", "virtual_cell_query",
                           "signature_retrieval"}
    assert (ROOT / "tools" / "shared").is_dir()
    assert not (ROOT / "tools" / "shared" / "manifest.json").exists()


def test_selection_prompt_carries_the_boundaries_to_the_model(tmp_path: Path):
    client = _RefusingClient()
    router = ToolRouter(client, ROOT / "tools")
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,12.5\n", encoding="utf-8")
    intent = TaskIntent("analysis_planning", "Profile.", (), (), None, None, (), (), (), False)
    result = router.select_and_execute(ContextPacket(intent, (), (), "context"), (dataset,))
    assert result is None
    prompt = client.messages[0][1]["content"]
    assert "use_when" in prompt and "do_not_use_when" in prompt


def test_model_may_echo_the_approved_path_but_never_a_foreign_one(tmp_path: Path):
    descriptors = LocalToolCatalog(ROOT / "tools").discover()
    descriptor = next(item for item in descriptors if item.identifier == "data_profile")
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,12.5\n", encoding="utf-8")

    validated = ToolRouter._validate_arguments(
        descriptor, {"dataset_path": str(dataset.resolve())}, dataset.resolve()
    )
    assert validated["dataset_path"] == str(dataset.resolve())

    echoed_name = ToolRouter._validate_arguments(
        descriptor, {"dataset_path": "assay.csv"}, dataset.resolve()
    )
    assert echoed_name["dataset_path"] == str(dataset.resolve())

    with pytest.raises(ToolRuntimeError, match="outside the approved dataset list"):
        ToolRouter._validate_arguments(
            descriptor, {"dataset_path": "C:/elsewhere/secret.csv"}, dataset.resolve()
        )
