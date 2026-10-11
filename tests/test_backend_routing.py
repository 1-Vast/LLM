"""Routing cannot gain scientific authority from backend registration order."""
from dataclasses import asdict, replace
import hashlib
import json

import pytest

from virtual_cell.interface import (Intervention, ModelCapabilities, PredictionRequest,
                                    QueryAssessment, QuerySupport, StatePrediction, SystemContext, safe_predict)
from virtual_cell.routing import BackendPreference, BackendRoutingPolicy
from virtual_cell.world_model import CompositeWorldModel


def request():
    return PredictionRequest("q", "case", "contrast", 1,
                             Intervention("drug", "drug", (), 1.0, "uM", 24.0),
                             SystemContext("cell", "cell", dataset_id="platform"), ("rna",), "v1")


class Rung:
    def __init__(self, name, value, *, supported=True, broken=False):
        self.name, self.value, self.supported, self.broken = name, value, supported, broken
        self.calls = 0

    def capabilities(self):
        return ModelCapabilities(self.name, "v1", "state", "drug", ("drug",), False, True, True, "reference")

    def assess_query(self, query):
        return QueryAssessment(QuerySupport.SUPPORTED if self.supported else QuerySupport.UNSUPPORTED,
                               (), (), self.capabilities())

    def predict(self, query):
        self.calls += 1
        if self.broken:
            raise ValueError("broken backend")
        return StatePrediction(True, {"rna": self.value}, 0.1, (), request_id=query.request_id,
                               model_version=query.model_version, confidence=0.9, in_distribution=True)


def preference(name, units=20, cost=1.0):
    return BackendPreference(name, "v1", "cell", "platform", ("rna",), "drug", 1.0, "uM", 24.0,
                             "reference-v1", units, cost)


def policy(*preferences):
    return BackendRoutingPolicy("frozen", "1" * 64, preferences)


def test_multiple_supported_models_refuse_without_reference_policy_in_both_orders():
    a, b = Rung("a", 1.0), Rung("b", -1.0)
    for order in ((a, b), (b, a)):
        composite = CompositeWorldModel(order)
        assessment, prediction = safe_predict(composite, request())
        assert assessment.support is QuerySupport.UNSUPPORTED
        assert "ambiguous_backend_routing" in prediction.limitations
        assert not prediction.applicable
        assert composite.routing_report(request())["selected"] is None
        assert composite.ledger.total_cost() == 0.0
        composite.predict(request())
        assert composite.ledger.total_cost() == 0.0
    assert a.calls == b.calls == 0


def test_reference_support_and_cost_choose_same_prediction_in_both_registration_orders():
    a, b, c = Rung("a", 1.0), Rung("b", -1.0), Rung("c", 2.0)
    declared = policy(preference("a", 40, 0.1), preference("b", 50, 2.0), preference("c", 50, 0.5))
    identities = []
    for order in ((a, b, c), (c, a, b)):
        composite = CompositeWorldModel(order, routing_policy=declared)
        _, prediction = safe_predict(composite, request())
        assert prediction.applicable and prediction.state_change == {"rna": 2.0}
        report = composite.routing_report(request())
        assert report["selected"] == composite.last_rung == "c"
        assert report["selected_calibration_id"] == "reference-v1"
        assert report["selected_reference_units"] == 50
        identities.append(composite.name)
    assert len(set(identities)) == 1
    assert a.calls == b.calls == 0 and c.calls == 2


def test_composite_assessment_cannot_claim_an_undeclared_model():
    class Impostor(CompositeWorldModel):
        def assess_query(self, query):
            assessment = super().assess_query(query)
            return replace(assessment, capabilities=replace(assessment.capabilities, model_identifier="foreign"))

    rung = Rung("a", 1.0)
    _, prediction = safe_predict(Impostor((rung,)), request())
    assert prediction.abstain_reason == "assessment_model_mismatch"
    assert rung.calls == 0


@pytest.mark.parametrize("changed", [
    {"context": SystemContext("cell", "cell", dataset_id="shifted")},
    {"context": SystemContext("other", "cell", dataset_id="platform")},
    {"intervention": Intervention("drug", "drug", (), 2.0, "uM", 24.0)},
    {"intervention": Intervention("drug", "drug", (), 1.0, "uM", 48.0)},
    {"readouts": ("viability",)},
])
def test_scope_shift_refuses_even_when_backend_declares_support(changed):
    rung = Rung("a", 1.0)
    composite = CompositeWorldModel((rung,), routing_policy=policy(preference("a")))
    prediction = composite.predict(replace(request(), **changed))
    assert prediction.abstain_reason == "routing_policy_out_of_scope"
    assert rung.calls == 0 and composite.last_rung is None


def test_ineligible_high_support_backend_cannot_win_and_unique_model_remains_usable():
    a, b = Rung("a", 1.0), Rung("b", 2.0, supported=False)
    composite = CompositeWorldModel((b, a), routing_policy=policy(preference("a"), preference("b", 100)))
    assert composite.predict(request()).state_change == {"rna": 1.0}
    assert b.calls == 0
    assert CompositeWorldModel((b, a)).predict(request()).state_change == {"rna": 1.0}


def test_failed_selected_backend_does_not_silently_fall_back():
    a, b = Rung("a", 1.0, broken=True), Rung("b", 2.0)
    composite = CompositeWorldModel((a, b), routing_policy=policy(preference("a", 30), preference("b")))
    assert not composite.predict(request()).applicable
    assert a.calls == 1 and b.calls == 0


def test_cache_identity_tracks_source_and_policy_but_not_registration_order():
    a, b = Rung("a", 1.0), Rung("b", 2.0)
    first = policy(preference("a"), preference("b", 30))
    names = {CompositeWorldModel((a, b), routing_policy=p).name for p in (
        first, replace(first, source_sha256="2" * 64),
        policy(preference("a", 40), preference("b", 30)))}
    assert len(names) == 3
    reversed_policy = replace(first, preferences=tuple(reversed(first.preferences)))
    assert CompositeWorldModel((b, a), routing_policy=reversed_policy).name in names


def test_hash_bound_receipt_rejects_tampering(tmp_path):
    path = tmp_path / "routing.json"
    raw = json.dumps({"identifier": "frozen", "preferences": [asdict(preference("a"))]}).encode()
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    declared = BackendRoutingPolicy.from_receipt(path, digest)
    assert declared.ranked(request(), {"a"})[0].backend == "a"
    path.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="hash_mismatch"):
        BackendRoutingPolicy.from_receipt(path, digest)


@pytest.mark.parametrize("changed", [{"reference_units": True}, {"reference_units": 0},
                                    {"compute_cost": float("nan")}, {"dose": -1.0},
                                    {"dose_unit": None}, {"readouts": ("rna", "rna")}])
def test_invalid_scientific_routing_inputs_are_not_coerced(changed):
    with pytest.raises(ValueError):
        replace(preference("a"), **changed)


def test_unknown_registered_name_is_rejected_at_configuration():
    with pytest.raises(ValueError, match="unregistered"):
        CompositeWorldModel((Rung("a", 1.0),), routing_policy=policy(preference("missing")))
