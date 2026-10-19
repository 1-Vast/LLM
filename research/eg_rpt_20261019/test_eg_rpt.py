"""Local tests of the EG-RPT scaffolding (no data, no network, no LLM)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import experiences as X  # noqa: E402
import policy_memory as PM  # noqa: E402


def one():
    return copy.deepcopy(X.EXPERIENCES[0])


def test_all_repository_records_are_valid():
    for e in X.EXPERIENCES:
        assert PM.validate_experience(e) == [], e.exp_id


@pytest.mark.parametrize("mutate,needle", [
    (lambda e: setattr(e, "unit", "dollars"), "unit"),
    (lambda e: setattr(e, "validation_tier", "gold"), "validation_tier"),
    (lambda e: setattr(e, "failure_mode", ""), "failure mode"),
    (lambda e: setattr(e, "dependence_group", ""), "dependence_group"),
    (lambda e: setattr(e, "ci95", None), "ci_note"),
    (lambda e: setattr(e, "delta_u", 5.0), "outside its own interval"),
    (lambda e: (setattr(e, "validation_tier", "external_confirmation"), setattr(e, "outcome", "supported")), "hypothetical"),
])
def test_validator_refuses_unusable_records(mutate, needle):
    e = one()
    mutate(e)
    assert any(needle in p for p in PM.validate_experience(e)), PM.validate_experience(e)


def test_negative_results_are_first_class_records():
    neg = [e for e in X.EXPERIENCES if e.outcome in ("not_supported", "withdrawn")]
    assert len(neg) >= 5 and all(e.failure_mode for e in neg)


def test_independence_counts_groups_not_records_and_units_are_not_poolable():
    assert PM.independent_units(X.EXPERIENCES) < len(X.EXPERIENCES)
    assert not PM.poolable(X.EXPERIENCES)
    assert PM.poolable([e for e in X.EXPERIENCES if e.unit == "events_per_64_compounds"])


def test_leave_group_out_never_shares_a_group():
    seen = 0
    for g, train, test in PM.leave_group_out(X.EXPERIENCES):
        assert test and all(e.dependence_group == g for e in test) and all(e.dependence_group != g for e in train)
        seen += 1
    assert seen == PM.independent_units(X.EXPERIENCES)


def report(**kw):
    base = dict(prediction=0.3, interval=(0.1, 0.5), interval_is_calibrated=False, model_disagreement=0.1, in_scope=True,
                calibration_note="uncalibrated", domain_distance=0.5)
    base.update(kw)
    return PM.ReliabilityReport(**base)


TH = {"max_disagreement": 0.3, "max_distance": 1.0}


def test_refusal_removes_proceed_and_baseline_is_default():
    gain = {"proceed": 0.5, "acquire_information": 0.2, "test_model_assumption": 0.1}
    cost = {"acquire_information": 0.25, "test_model_assumption": 0.3}
    pen = {"proceed": 0.0}
    ok = PM.choose_under_uncertainty(report(), thresholds=TH, expected_gain=gain, cost=cost, misspec_penalty=pen)
    assert ok["choice"] == "proceed" and not ok["refused_point_claim"]
    out = PM.choose_under_uncertainty(report(in_scope=False), thresholds=TH, expected_gain=gain, cost=cost, misspec_penalty=pen)
    assert out["refused_point_claim"] and "proceed" not in out["values"] and out["choice"] == "baseline"
    far = PM.choose_under_uncertainty(report(domain_distance=3.0), thresholds=TH, expected_gain=gain, cost=cost, misspec_penalty=pen)
    assert far["refused_point_claim"]


def test_disagreement_alone_does_not_buy_information():
    r = report(model_disagreement=0.25)
    out = PM.choose_under_uncertainty(r, thresholds=TH, expected_gain={}, cost={"acquire_information": 0.1}, misspec_penalty={})
    assert out["choice"] == "baseline"  # no expected gain was supplied, so disagreement cannot create value


def test_misspecification_penalty_can_flip_a_choice():
    gain = {"proceed": 0.5}
    a = PM.choose_under_uncertainty(report(), thresholds=TH, expected_gain=gain, cost={}, misspec_penalty={})
    b = PM.choose_under_uncertainty(report(), thresholds=TH, expected_gain=gain, cost={}, misspec_penalty={"proceed": 0.6})
    assert a["choice"] == "proceed" and b["choice"] == "baseline"
