"""Virtual-cell request, capability and prediction contract.

File summary
- Path: tests/test_virtual_cell_contract.py
- Purpose: Virtual-cell request, capability and prediction contract.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_unavailable_world_model_does_not_invent_a_state_prediction()`
- Depends on: virtual_cell
"""
from virtual_cell import (
    Intervention,
    PredictionRequest,
    SystemContext,
    UnavailableVirtualCellWorldModel,
)


def test_unavailable_world_model_does_not_invent_a_state_prediction():
    prediction = UnavailableVirtualCellWorldModel().predict(
        PredictionRequest(
            "request-1",
            "case-1",
            "contrast-1",
            1,
            Intervention("compound_a", "drug", ("target_a",), dose=1.0, dose_unit="uM"),
            SystemContext("cell_a", "Defined cell context.", control_dataset_id="control-1"),
            (),
            "none",
        )
    )

    assert not prediction.applicable
    assert prediction.state_change is None
    assert prediction.uncertainty is None
    assert prediction.limitations
