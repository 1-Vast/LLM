"""Conditional valid readings must not masquerade as complete attempted-experiment forecasts."""
from dataclasses import replace

from maestro.case_memory import EpisodeStore, ScientificMeasurementStatus
from maestro.hypothesis_forecast import CaseMemoryOutcomeForecaster, UserStateContext
from maestro.acquisition import _forecast_problem
from maestro.acquisition import expected_terminal_decision_value
import pytest
from tests.fixtures.case_memory_forecasting import _episode, _store, _contrast, _actions, H1, H2


def test_valid_readout_has_four_labels_and_cannot_drive_unconditional_planning():
    f = CaseMemoryOutcomeForecaster(_store([_episode("reference", 1)]), research_mode=True)
    action = _actions()[0]
    prediction = f.forecast(_contrast(), (action,), None)[action.identifier]
    assert prediction.outcome_mode == "valid_readout"
    assert all("qc_failed" not in b.probabilities and len(b.probabilities) == 4 for b in prediction.branches)
    assert _forecast_problem(prediction, action.identifier, frozenset((H1, H2))) == "experiment_validity_probability_required"
    with pytest.raises(ValueError, match="experiment_validity_probability_required"):
        expected_terminal_decision_value((H1, H2), prediction, {})


def test_all_attempts_is_explicit_and_missing_denominator_is_not_guessed():
    store = EpisodeStore()
    for e in _store([_episode("reference", 1)]).latest():
        store.append(replace(e, real_measurements=tuple(replace(m, sampling_frame="valid_only")
                                                       for m in e.real_measurements)))
    action = _actions()[0]
    f = CaseMemoryOutcomeForecaster(store, research_mode=True, outcome_mode="attempted_experiment")
    assert f.forecast(_contrast(), (action,), None)[action.identifier].refusal == "insufficient_outcome_support"


def test_known_qc_failures_are_counted_only_in_attempted_experiment_mode():
    store = EpisodeStore()
    for e in _store([_episode("pass", 1), _episode("fail", 1)]).latest():
        if e.case_id.startswith("fail"):
            e = replace(e, real_measurements=tuple(replace(m, status=ScientificMeasurementStatus.QC_FAILED,
                                                           outcome_label=None) for m in e.real_measurements))
        store.append(e)
    action = _actions()[0]
    f = CaseMemoryOutcomeForecaster(store, research_mode=True)
    for mode, n in (("valid_readout", 1), ("attempted_experiment", 2)):
        state = UserStateContext(outcome_mode=mode)
        prediction = f.forecast_detailed(_contrast(), action, None, state)
        assert all(r["independent_units"] == n for r in prediction["support"].values())
        assert prediction["decision_applicable"] == (mode == "attempted_experiment")
        if mode == "attempted_experiment":
            assert all(b["probabilities"]["qc_failed"] > 0 for b in prediction["branches"])


def test_unknown_attempt_outcome_is_refused_instead_of_silently_dropped():
    store = EpisodeStore()
    for e in _store([_episode("reference", 1)]).latest():
        store.append(replace(e, real_measurements=tuple(replace(m, status=ScientificMeasurementStatus.PLANNED_MISSING,
                                                               outcome_label=None) for m in e.real_measurements)))
    action = _actions()[0]
    f = CaseMemoryOutcomeForecaster(store, research_mode=True, outcome_mode="attempted_experiment")
    assert f.forecast(_contrast(), (action,), None)[action.identifier].refusal == "incomplete_attempt_outcomes"


def test_unmapped_attempt_label_cannot_disappear_from_the_denominator():
    store = EpisodeStore()
    for e in _store([_episode("known", 1), _episode("unknown", 1)]).latest():
        if e.case_id.startswith("unknown"):
            e = replace(e, real_measurements=tuple(replace(m, outcome_label="unregistered_reading")
                                                   for m in e.real_measurements))
        store.append(e)
    f = CaseMemoryOutcomeForecaster(store, research_mode=True, outcome_mode="attempted_experiment")
    receipt = f.forecast_detailed(_contrast(), _actions()[0], None)
    assert receipt["abstain_reason"] == "incomplete_attempt_outcomes"
    assert not receipt["decision_applicable"]


def test_missing_outcome_in_another_laboratory_does_not_block_the_requested_lab():
    store = EpisodeStore()
    for e in _store([_episode("known", 1), _episode("unknown", 1)]).latest():
        missing = e.case_id.startswith("unknown")
        e = replace(e, context_fingerprint={**e.context_fingerprint, "laboratory": "B" if missing else "A"})
        if missing:
            e = replace(e, real_measurements=tuple(replace(m, status=ScientificMeasurementStatus.PLANNED_MISSING,
                                                           outcome_label=None) for m in e.real_measurements))
        store.append(e)
    f = CaseMemoryOutcomeForecaster(store, research_mode=True)
    receipt = f.forecast_detailed(_contrast(), _actions()[0], None,
                                 UserStateContext(laboratory="A", outcome_mode="attempted_experiment"))
    assert receipt["decision_applicable"]
    assert all(row["independent_units"] == 1 for row in receipt["support"].values())
