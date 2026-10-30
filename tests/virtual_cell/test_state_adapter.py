"""State adapter rejects unmapped perturbations and unmatched controls."""
from pathlib import Path

from virtual_cell.interface import Intervention, QuerySupport, SystemContext
from virtual_cell import PredictionRequest
from virtual_cell.state_adapter import StateAdapterConfig, StateCapabilityAdapter


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
