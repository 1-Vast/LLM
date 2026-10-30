from maestro.research_loop import (ActionCandidate, Forecast, HypothesisPair,
                                    Observation, ResearchLoop)
import pytest


class Executor:
    def execute(self, action):
        return Observation(action.identifier, action.payload["outcome"], source_id="simulated", context_identifier="toy", independent_units=1)


def test_loop_selects_information_per_cost_and_records_replay_digest():
    pair = HypothesisPair("on_target", "artifact")
    actions = (ActionCandidate("cheap", 1, 0.4, {"outcome": "on_target"}),
               ActionCandidate("expensive", 2, 0.7, {"outcome": "artifact"}))
    forecasts = {a.identifier: Forecast(a.identifier, {"on_target": .5, "artifact": .5}) for a in actions}
    loop = ResearchLoop(pair, actions, forecasts, Executor(), budget=1)
    state = loop.run()
    assert state.selected_actions == ("cheap",)
    assert state.observations[0].outcome == "on_target"
    assert state.stop_reason == "budget_exhausted"
    assert loop.digest() == loop.digest()


def test_refused_forecast_does_not_spend_budget():
    pair = HypothesisPair("a", "b")
    action = ActionCandidate("unknown", 1, 10)
    loop = ResearchLoop(pair, (action,), {"unknown": Forecast("unknown", {}, refusal="outside_scope")}, Executor(), budget=1)
    state = loop.step()
    assert state.stop_reason == "no_admissible_action"
    assert state.remaining_budget == 1


def test_executor_cannot_change_action_identity():
    class Bad:
        def execute(self, action):
            return Observation("other", "a", source_id="simulated", context_identifier="toy", independent_units=1)
    loop = ResearchLoop(HypothesisPair("a", "b"), (ActionCandidate("x", 1, 1),),
                        {"x": Forecast("x", {"a": 1})}, Bad(), budget=1)
    try:
        loop.step()
    except ValueError as exc:
        assert str(exc) == "executor_returned_wrong_action"
    else:
        raise AssertionError("expected identity guard")


def test_unknown_outcome_is_retained_but_cannot_steer():
    class Unknown:
        def execute(self, action):
            return Observation(action.identifier, "new_readout")
    loop = ResearchLoop(HypothesisPair("a", "b"), (ActionCandidate("x", 1, 1),),
                        {"x": Forecast("x", {"a": .5, "b": .5})}, Unknown(), budget=1)
    state = loop.step()
    assert state.stop_reason == "invalid_observation"
    assert state.observations[0].success is False
    assert state.observations[0].detail["validation"] == "unknown_outcome"


def test_failed_or_qc_observations_are_retained_without_updating_support():
    pair = HypothesisPair("a", "b")
    action = ActionCandidate("x", 1, 1, {"outcome": "a"})
    class Failing:
        def execute(self, action):
            return Observation(action.identifier, "a", success=False, evidence_kind="execution_failure", detail={"reason": "timeout"})
    loop = ResearchLoop(pair, (action,), {"x": Forecast("x", {"a": .5, "b": .5})}, Failing(), budget=1)
    state = loop.run()
    assert len(state.observations) == 1 and not state.observations[0].admissible
    assert state.stop_reason == "budget_exhausted"


def test_qualified_measurement_requires_source_context_and_independent_units():
    pair = HypothesisPair("a", "b")
    action = ActionCandidate("x", 1, 1, {"outcome": "a"})
    class MissingEvidence:
        def execute(self, action):
            return Observation(action.identifier, "a")
    loop = ResearchLoop(pair, (action,), {"x": Forecast("x", {"a": .5, "b": .5})}, MissingEvidence(), budget=1)
    state = loop.run()
    assert state.observations[0].admissible is False
    assert state.stop_reason == "budget_exhausted"


def test_unknown_outcome_is_recorded_as_invalid_without_updating_support():
    class Wrong:
        def execute(self, action):
            return Observation(action.identifier, "invented", source_id="s", context_identifier="c", independent_units=1)
    loop = ResearchLoop(HypothesisPair("a", "b"), (ActionCandidate("x", 1, 1),),
                        {"x": Forecast("x", {"a": .5, "b": .5})}, Wrong(), budget=1)
    state = loop.step()
    assert state.stop_reason == "invalid_observation"
    assert state.observations[0].success is False
    assert state.observations[0].detail["validation"] == "unknown_outcome"
    assert state.observations[0].source_id == "s"
    assert state.observations[0].context_identifier == "c"
    assert state.observations[0].independent_units == 1


@pytest.mark.parametrize("forecast", [
    Forecast("other", {"a": 1}, support=2, scope="cell", basis="references"),
    Forecast("x", {"a": 1}, support=0, scope="cell", basis="references"),
    Forecast("x", {"a": 1}, support=2, scope="other", basis="references"),
    Forecast("x", {"a": 1}, scope="cell", basis="references"),
    Forecast("x", {"a": 1}, support=2, scope="cell"),
])
def test_scoped_action_refuses_unbound_or_unsupported_forecast_without_spending(forecast):
    class NeverExecute:
        def execute(self, action):
            raise AssertionError("refused forecast spent budget")
    action = ActionCandidate("x", 1, 1, scope="cell")
    loop = ResearchLoop(HypothesisPair("a", "b"), (action,), {"x": forecast},
                        NeverExecute(), budget=1)
    state = loop.step()
    assert state.stop_reason == "no_admissible_action"
    assert state.remaining_budget == 1


def test_supported_scoped_action_can_execute():
    action = ActionCandidate("x", 1, 1, {"outcome": "a"}, scope="cell")
    forecast = Forecast("x", {"a": 1}, support=2, scope="cell", basis="references")
    loop = ResearchLoop(HypothesisPair("a", "b"), (action,), {"x": forecast}, Executor(), budget=1)
    assert loop.run().selected_actions == ("x",)


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_acquisition_inputs_are_refused(value):
    with pytest.raises(ValueError):
        ActionCandidate("x", value, 1)
    with pytest.raises(ValueError):
        ActionCandidate("x", 1, value)
    with pytest.raises(ValueError):
        Forecast("x", {"a": value})
    with pytest.raises(ValueError):
        Forecast("x", {"a": 1}, information_gain=value)
    with pytest.raises(ValueError):
        ResearchLoop(HypothesisPair("a", "b"), (), {}, Executor(), budget=value)


def test_duplicate_actions_cannot_silently_replace_menu_entries():
    with pytest.raises(ValueError, match="duplicate_action_identifier"):
        ResearchLoop(HypothesisPair("a", "b"), (ActionCandidate("x", 1, 1),
                                               ActionCandidate("x", 2, 2)), {}, Executor(), budget=2)


@pytest.mark.parametrize("support", [float("nan"), float("inf"), .5, True])
def test_support_counts_require_integers(support):
    with pytest.raises(ValueError):
        Forecast("x", {"a": 1}, support=support)
    with pytest.raises(ValueError):
        Observation("x", "a", independent_units=support)
