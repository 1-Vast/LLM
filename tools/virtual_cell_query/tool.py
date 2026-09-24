"""Expose the installed State checkpoint through the shared prediction contract."""
from dataclasses import asdict
import json
from pathlib import Path

from maestro.tool_contracts import TOOL_SCHEMA_VERSION, json_loads
from virtual_cell.interface import PredictionRequest, safe_predict
from virtual_cell.state_adapter import StateAdapterConfig, StateCapabilityAdapter


def run(parameters):
    request = PredictionRequest.from_dict(json_loads(Path(parameters["dataset_path"]).read_text(encoding="utf-8")))
    model = StateCapabilityAdapter(StateAdapterConfig.from_workspace(Path(__file__).resolve().parents[2]))
    assessment, prediction = safe_predict(model, request)
    structured = lambda value: json_loads(json.dumps(asdict(value), allow_nan=False))
    return {
        "schema_version": TOOL_SCHEMA_VERSION,
        "payload": {
            "request": request.to_dict(), "assessment": structured(assessment), "prediction": structured(prediction),
            "in_distribution": prediction.in_distribution is True,
            "rejected": [] if prediction.applicable else [{"request_id": request.request_id, "reason": prediction.abstain_reason}],
            "contradiction_flag": False,
        },
        "observations": ["Planning-only State query: " + (prediction.abstain_reason or "prediction_available")],
        "limitations": ["Predictions and refusals do not supply measured premises or eliminate hypotheses.",
                        "State paper performance does not qualify this checkpoint or a new biological endpoint."],
        "artifacts": [prediction.artifact_ref] if prediction.artifact_ref else [],
    }
