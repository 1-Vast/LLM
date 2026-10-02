"""Synthetic world-model fixture for orchestration contracts."""
from virtual_cell.interface import Interval, IntervalKind, ModelCapabilities, QueryAssessment, QuerySupport, StatePrediction


class ApplicableWorldModel:
    def __init__(self):
        self.requests = []

    def capabilities(self):
        return ModelCapabilities("test", "model-1", "embedding", "condition", ("drug",), True, False, False, None)

    def assess_query(self, request):
        self.requests.append(request)
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request):
        return StatePrediction(
            True, {"embedding_delta_l2": 1.0}, None, (),
            intervals={
                "embedding_delta_l2": Interval(
                    0.5, 1.5, kind=IntervalKind.CALIBRATED, level=0.9,
                    basis="held-out residuals for the declared test split",
                )
            },
            request_id=request.request_id, model_version=request.model_version,
            confidence=None, in_distribution=True,
            uncertainty_components={"fixture": "not independently calibrated"},
        )
