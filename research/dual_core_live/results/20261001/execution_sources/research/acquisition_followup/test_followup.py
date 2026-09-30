"""Counterexamples for evidence conditioning and bounded contingent planning."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import two_step as S
from maestro.acquisition import OutcomeBranch, OutcomeForecast
from maestro.models import EvidenceScope
from maestro.outcome import EvidenceState, OutcomeClass, UpdateRecord


def forecast(key, *, correct=0.0, wrong=0.0, absent=0.0):
    branches = []
    for own, good, bad in (("H1", S.LABELS[0], S.LABELS[1]), ("H2", S.LABELS[1], S.LABELS[0])):
        branches.append(OutcomeBranch(own, {good: correct, bad: wrong, S.V.ABSENT: absent,
                                           S.V.UNRESOLVED: 1 - correct - wrong - absent}, 100))
    return OutcomeForecast(S.C.action_id(key), tuple(branches))


def test_probe_with_no_immediate_discrimination_can_buy_informative_followups():
    early, late, alternate = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0), ("A549", 72.0, 100.0)
    forecasts = {S.C.action_id(k): forecast(k, correct=0.4) for k in (late, alternate)}
    forecasts[S.C.action_id(early)] = forecast(early, absent=0.5)

    def conditional(first, label, second):
        useful = (label == S.V.ABSENT and second == late) or (label == S.V.UNRESOLVED and second == alternate)
        return forecast(second, correct=1.0 if useful else 0.0)

    chosen = S.plan_two_step((early, late, alternate), "H1", "H2", forecasts, conditional, budget=14)
    myopic = S.plan_two_step((early, late, alternate), "H1", "H2", forecasts, conditional, budget=14, horizon=1)
    assert chosen["first"] == early
    assert chosen["immediate_utility"] < 0
    assert chosen["followups"] == {S.V.ABSENT: late, S.V.UNRESOLVED: alternate}
    assert myopic["first"] in (late, alternate)
    assert chosen["utility"] > myopic["utility"]


def test_bad_or_unsupported_continuation_never_earns_credit():
    early, late = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0)
    forecasts = {S.C.action_id(k): forecast(k, absent=1) for k in (early, late)}
    for conditional in (lambda a, y, b: forecast(b, wrong=1),
                        lambda a, y, b: OutcomeForecast(S.C.action_id(b), refusal="no_paired_reference")):
        assert S.plan_two_step((early, late), "H1", "H2", forecasts, conditional) is None


def test_budget_and_time_order_bound_continuation():
    early, late = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0)
    forecasts = {S.C.action_id(k): forecast(k, absent=1) for k in (early, late)}
    conditional = lambda a, y, b: forecast(b, correct=1)
    assert S.plan_two_step((early, late), "H1", "H2", forecasts, conditional, budget=8) is None
    chosen = S.plan_two_step((early, late), "H1", "H2", forecasts, conditional, budget=14)
    assert chosen["first"] == early
    assert all(k == late for k in chosen["followups"].values())


def test_continuation_preserves_asymmetric_first_reading_likelihoods():
    early, late = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0)
    initial = OutcomeForecast(S.C.action_id(early), (
        OutcomeBranch("H1", {S.V.ABSENT: 0.8, S.V.UNRESOLVED: 0.2}, 100),
        OutcomeBranch("H2", {S.V.ABSENT: 0.2, S.V.UNRESOLVED: 0.8}, 100)))
    # After absence this reading mostly removes H2: its value depends on the
    # larger P(absent|H1), not on assuming equal weights a second time.
    tail = OutcomeForecast(S.C.action_id(late), (
        OutcomeBranch("H1", {S.LABELS[0]: 1.0}, 100),
        OutcomeBranch("H2", {S.LABELS[0]: 1.0}, 100)))
    plan = S.plan_two_step((early, late), "H1", "H2",
        {S.C.action_id(early): initial, S.C.action_id(late): forecast(late, absent=1)},
        lambda a, y, b: tail if y == S.V.ABSENT else OutcomeForecast(S.C.action_id(b), refusal="no_pair"))
    p1, p2 = S.probabilities(initial, "H1"), S.probabilities(initial, "H2")
    q1, q2 = S.probabilities(tail, "H1"), S.probabilities(tail, "H2")
    expected = (0.5 * (p1[S.LABELS[0]] + p2[S.LABELS[1]])
                + 0.5 * (p1[S.V.ABSENT] * q1[S.LABELS[0]] + p2[S.V.ABSENT] * q2[S.LABELS[1]]))
    assert abs(plan["p_correct"] - expected) < 1e-12
    assert plan["followups"] == {S.V.ABSENT: late}


def test_runtime_forecaster_conditions_on_valid_observation_without_mutating_belief(monkeypatch):
    first, second = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0)
    table = SimpleNamespace(names=["a", "b", "c", "d"], klass=["H1", "H1", "H2", "H2"])
    ft = SimpleNamespace(fold=0, tier="A", tables={first: table, second: table})
    outcomes = {first: {("a", "H2"): "undetected", ("b", "H2"): "ambiguous",
                        ("c", "H1"): "undetected", ("d", "H1"): "ambiguous"},
                second: {("a", "H2"): "eliminate_b", ("b", "H2"): "eliminate_a",
                         ("c", "H1"): "eliminate_b", ("d", "H1"): "eliminate_a"}}
    monkeypatch.setattr(S.C, "loo_outcomes", lambda ft, key, floor, margin: outcomes[key])
    action = S.E.make_action(second, "H1", "H2")
    contrast = S.E.contrast_for("H1", "H2", [action])
    forecaster = S.V.ReferenceCardForecaster(ft, {"floor": 0, "margin": 0, "eliminates": True})
    state = EvidenceState.open(contrast.hypotheses)
    update = UpdateRecord("r1", S.C.action_id(first), OutcomeClass.PREDICTED,
                          EvidenceScope.INTERVENTION_IMPLEMENTATION, (), "real no-response", S.V.ABSENT, ("H1", "H2"))
    observed = replace(state, updates=(update,))
    base = forecaster.forecast(contrast, [action], state)[action.identifier]
    conditioned = forecaster.forecast(contrast, [action], observed)[action.identifier]
    assert base.branch_for("H1").probabilities[S.LABELS[0]] == 0.5
    assert conditioned.branch_for("H1").probabilities[S.LABELS[0]] == 1
    assert conditioned.branch_for("H1").support == 1
    paired = S.conditional_forecast(ft, forecaster.params, first, S.V.ABSENT, second, "H1", "H2")
    assert paired.branch_for("H2").probabilities[S.LABELS[1]] == 1
    assert paired.branch_for("H2").probabilities[S.LABELS[0]] == 0
    assert observed.candidates == state.candidates
    for invalid in (OutcomeClass.QUALITY_FAILED, OutcomeClass.CONDITION_UNMATCHED, OutcomeClass.NON_MEASUREMENT):
        bad = replace(observed, updates=(replace(update, outcome_class=invalid),))
        assert forecaster.forecast(contrast, [action], bad)[action.identifier] == base
    migrated = replace(observed, updates=(replace(update, candidate_hypotheses=("H1", "H3")),))
    assert forecaster.forecast(contrast, [action], migrated)[action.identifier] == base

    # The same measured training compounds support each transition; no support
    # exists for a resolved first label, even though marginal references exist.
    missing = S.conditional_forecast(ft, forecaster.params, first, S.LABELS[0], second, "H1", "H2")
    assert missing.refusal.startswith("no_paired_reference_for_branch")


def test_evidence_update_keeps_the_registered_label_for_the_next_model_query():
    key = ("A549", 24.0, 10.0)
    action = S.E.make_action(key, "H1", "H2")
    contrast = S.E.contrast_for("H1", "H2", [action])
    state = EvidenceState.open(contrast.hypotheses)
    for reading in ("undetected", "ambiguous"):
        observed, _, _ = S.C.evidence_update(state, contrast, action, key, {"outcome": reading},
                                            "H1", "H2", qc=True, agreement=0.9, source="measured")
        assert observed.updates[-1].outcome_label == S.LABEL_OF[reading]
        assert observed.updates[-1].candidate_hypotheses == ("H1", "H2")
        assert observed.candidates == state.candidates
