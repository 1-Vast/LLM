"""Regression tests for the PredictionRequest extension and conditional cache identity.

File summary
- Path: tests/test_conditional_forecast_interface.py
- Purpose: pin the backward compatibility of `PredictionRequest` after the optional
  hypotheses/history/observation_context/forecast_mode extension: state-only requests behave
  exactly as before (construction, validation, serialization, deserialization, cache identity),
  and the conditional modes validate their requirements with named errors.
- Depends on: src/virtual_cell/{interface,conditional_forecast,cache}.py
"""
from __future__ import annotations

from virtual_cell import conditional_forecast as CF
from virtual_cell import interface as VC
from virtual_cell.cache import PredictionCache


def _state_request(**kwargs) -> VC.PredictionRequest:
    base = dict(
        request_id="r1", case_id="c1", contrast_id="k1", plan_version=1,
        intervention=VC.Intervention("drug", "compound", ("TARGET_A",), dose=5.0, dose_unit="uM",
                                     time_hours=24.0),
        context=VC.SystemContext("NCI-H596", "fixture", dataset_id="tiny", control_dataset_id="tiny"),
        readouts=("embedding_delta_l2",), model_version="stub-1",
    )
    base.update(kwargs)
    return VC.PredictionRequest(**base)


# ------------------------------------------------------------------ backward compatibility
def test_state_only_request_is_valid_exactly_as_before():
    request = _state_request()
    assert request.hypotheses == () and request.history == ()
    assert request.observation_context is None and request.forecast_mode is None
    assert request.validation_errors() == ()


def test_legacy_construction_serialization_and_deserialization_are_unchanged():
    request = _state_request()
    payload = request.to_dict()
    assert "hypotheses" in payload and payload["hypotheses"] == []
    decoded = VC.PredictionRequest.from_dict(payload)
    assert decoded == request
    assert VC.PredictionRequest.from_json(request.to_json()) == request


def test_legacy_payload_without_the_new_fields_still_decodes():
    request = _state_request()
    payload = request.to_dict()
    for name in ("hypotheses", "history", "observation_context", "forecast_mode"):
        payload.pop(name)
    assert VC.PredictionRequest.from_dict(payload) == request


def test_plain_prediction_cache_identity_is_unchanged_by_tracking_fields():
    cache = PredictionCache()
    a = _state_request()
    b = _state_request(request_id="other", case_id="other-case")
    assert cache.key_for(a, "backend") == cache.key_for(b, "backend")


# ------------------------------------------------------------------ conditional validation
def test_state_mode_allows_empty_hypotheses_and_history():
    assert _state_request(forecast_mode="state").validation_errors() == ()


def test_hypothesis_conditional_mode_requires_two_hypotheses():
    request = _state_request(forecast_mode="hypothesis_conditional")
    assert "hypothesis_conditional_requires_two_hypotheses" in request.validation_errors()
    one = _state_request(forecast_mode="hypothesis_conditional", hypotheses=("H1",))
    assert "hypothesis_conditional_requires_two_hypotheses" in one.validation_errors()
    two = _state_request(forecast_mode="hypothesis_conditional", hypotheses=("H1", "H2"))
    assert two.validation_errors() == ()


def test_history_aware_mode_requires_structurally_valid_history():
    missing = _state_request(forecast_mode="history_aware")
    assert "history_aware_requires_history" in missing.validation_errors()
    malformed = _state_request(forecast_mode="history_aware", history=({"action": "a"},))
    assert "invalid_history_entry" in malformed.validation_errors()
    valid = _state_request(forecast_mode="history_aware",
                           history=({"action": "a", "outcome": "o"},))
    assert valid.validation_errors() == ()


def test_invalid_mode_and_invalid_combinations_return_named_errors():
    bogus = _state_request(forecast_mode="prophecy")
    assert "invalid_forecast_mode" in bogus.validation_errors()
    combined = _state_request(forecast_mode="hypothesis_conditional_history")
    errors = combined.validation_errors()
    assert "hypothesis_conditional_requires_two_hypotheses" in errors
    assert "history_aware_requires_history" in errors


def test_extended_request_round_trips_through_strict_json():
    request = _state_request(
        forecast_mode="hypothesis_conditional_history", hypotheses=("H1", "H2"),
        history=({"action": "a", "outcome": "o"},), observation_context={"cell_line": "A549"})
    assert request.validation_errors() == ()
    assert VC.PredictionRequest.from_json(request.to_json()) == request


# ------------------------------------------------------------------ conditional cache identity
def test_conditional_cache_identity_includes_hypotheses_history_context_and_mode():
    base = _state_request()
    variants = [
        _state_request(hypotheses=("H1", "H2")),
        _state_request(history=({"action": "a", "outcome": "o"},)),
        _state_request(observation_context={"cell_line": "A549"}),
        _state_request(forecast_mode="hypothesis_conditional", hypotheses=("H1", "H2")),
    ]
    keys = {CF.conditional_cache_key(v, "backend") for v in [base, *variants]}
    assert len(keys) == 1 + len(variants)
    assert CF.conditional_cache_key(base, "backend") != CF.conditional_cache_key(base, "other-backend")


def test_conditional_cache_identity_excludes_only_tracking_fields():
    a = _state_request(hypotheses=("H1", "H2"))
    b = _state_request(request_id="r2", case_id="c2", contrast_id="k2", plan_version=2,
                       hypotheses=("H1", "H2"))
    assert CF.conditional_cache_key(a, "backend") == CF.conditional_cache_key(b, "backend")
    invalid = _state_request(request_id="")
    assert CF.conditional_cache_key(invalid, "backend") is None
