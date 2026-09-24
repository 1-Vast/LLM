"""State adapter rejects unmapped perturbations and unmatched controls.

File summary
- Path: tests/test_state_adapter.py
- Purpose: State adapter rejects unmapped perturbations and unmatched controls.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_state_adapter_rejects_unknown_perturbation_before_any_control_fallback()`
- Depends on: virtual_cell
"""
from pathlib import Path

from virtual_cell import (
    Intervention,
    PredictionRequest,
    QuerySupport,
    StateAdapterConfig,
    StateCapabilityAdapter,
    SystemContext,
)


def test_state_adapter_rejects_unknown_perturbation_before_any_control_fallback(tmp_path: Path):
    checkpoint = tmp_path / "model.ckpt"
    config = tmp_path / "config.yaml"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    config.write_text("config", encoding="utf-8")
    adapter = StateCapabilityAdapter(
        StateAdapterConfig(checkpoint, config, "state-x-hvg", frozenset({"known_drug"}))
    )
    request = PredictionRequest(
        "request-1",
        "case-1",
        "contrast-1",
        1,
        Intervention("unknown_drug", "drug", ("TARGET",)),
        SystemContext("cell-a", "context", dataset_id="treated", control_dataset_id="control"),
        ("signature-a",),
        "state-x-hvg",
    )

    assessment = adapter.assess_query(request)
    prediction = adapter.predict(request)

    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "fallback-to-control" in " ".join(assessment.limitations)
    assert not prediction.applicable
