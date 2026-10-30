"""The case-memory path serves hypothesis outcomes, not STATE or history forecasts."""
from dataclasses import replace

import pytest

from maestro import case_update as path
from maestro.models import EvidenceScope
from maestro.outcome import EvidenceState, OutcomeClass, UpdateRecord
from tests.fixtures.case_memory_forecasting import H1, H2, _actions, _contrast, _episode, _store
from tests.fixtures.case_memory_forecasting import _compiled_problem


def _history_state():
    record = UpdateRecord("previous_result", "previous_action", OutcomeClass.AMBIGUOUS,
                          EvidenceScope.PLAN_LIMITATION, (), "synthetic measured history",
                          "unresolved", (H1, H2))
    return replace(EvidenceState.open(_contrast().hypotheses), updates=(record,))


@pytest.mark.parametrize("mode", ("state", "history_aware", "hypothesis_conditional_history", "unknown"))
@pytest.mark.parametrize("research", (False, True))
def test_unserved_modes_cannot_activate_case_memory(mode, research, monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "0" if research else "1")
    store = _store([_episode(f"unit-{i}", +1) for i in range(6)])
    evidence = _history_state()
    result = path.run_case_memory_path(_compiled_problem(), store, _contrast(), _actions(), evidence,
                                       forecast_mode=mode, research_mode=research)
    assert not result.activated
    assert result.refusal == f"unsupported_forecast_mode:{mode}"
    assert result.gate_failures == (path.PathGateFailure("forecast_mode", f"unsupported:{mode}"),)
    assert not result.forecasts and not result.retrieval and not result.rankings
    assert evidence == _history_state()


@pytest.mark.parametrize("mode", ("state", "history_aware", "hypothesis_conditional_history", "unknown"))
def test_mode_refusal_precedes_forecasting(mode, monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    monkeypatch.setattr(path, "CaseMemoryOutcomeForecaster",
                        lambda *a, **kw: pytest.fail("unserved mode constructed a forecaster"))
    result = path.run_case_memory_path(_compiled_problem(), _store([]), _contrast(), _actions(),
                                       _history_state(), forecast_mode=mode)
    assert result.refusal == f"unsupported_forecast_mode:{mode}"


@pytest.mark.parametrize("research", (False, True))
def test_hypothesis_conditional_still_serves_observed_outcome_branches(research, monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "0" if research else "1")
    store = _store([_episode(f"unit-{i}", +1) for i in range(6)])
    evidence = _history_state()
    result = path.run_case_memory_path(_compiled_problem(), store, _contrast(), _actions(), evidence,
                                       forecast_mode="hypothesis_conditional", research_mode=research)
    assert result.activated and not result.gate_failures
    for forecast in result.forecasts.values():
        assert forecast["decision_applicable"]
        assert {branch["hypothesis"] for branch in forecast["branches"]} == {H1, H2}
        assert forecast["provenance"]["evidence_kind"] == "model_prediction"
        assert all("qc_failed" in branch["probabilities"] for branch in forecast["branches"])
    assert evidence == _history_state()
