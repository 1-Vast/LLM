"""Scientific regressions: support, leakage, conditioning, provenance and cache invalidation."""
from dataclasses import replace

import numpy as np
import pytest

from maestro import case_memory as CM
from maestro.case_update import qualify_result
from maestro.hypothesis_forecast import CaseMemoryOutcomeForecaster
from maestro.hypothesis_forecast import support_aware_shrinkage
from tests.fixtures.case_memory_forecasting import _episode, _store, _contrast, _actions, H1, H2
from tools.case_memory.build_cases import _reference_centroid


def _run(store, **kwargs):
    forecaster = CaseMemoryOutcomeForecaster(store, research_mode=True, **kwargs)
    action = _actions()[0]
    return forecaster, forecaster.forecast(_contrast(), (action,), None)[action.identifier]


def test_hypotheses_without_conditioned_outcomes_never_fabricate_a_forecast():
    store = CM.EpisodeStore()
    store.append(_episode("legacy", +1))
    _, result = _run(store)
    assert result.refusal == "insufficient_outcome_support" and not result.branches


def test_duplicate_episodes_do_not_inflate_independent_support():
    original = _store([_episode("a", +1)])
    duplicated = CM.EpisodeStore()
    for episode in original.latest():
        for i in range(8):
            duplicated.append(replace(episode, case_id=f"{episode.case_id}-{i}",
                provenance={**episode.provenance, "independent_unit": episode.case_id}))
    f, result = _run(duplicated)
    assert all(b.support == 1 for b in result.branches)
    report = f.support_report(_contrast(), _actions()[0])
    assert all(r["independent_units"] == 1 and r["effective_support"] == 1 for r in report.values())


def test_one_labelled_stratum_cannot_supply_both_hypothesis_branches():
    paired = _store([_episode("a", +1)])
    store = CM.EpisodeStore()
    store.append(next(e for e in paired.latest() if e.real_measurements[0].conditioning_hypothesis == H1))
    _, result = _run(store)
    assert result.refusal and not result.branches


def test_no_discrimination_is_invented_when_observed_distributions_are_identical():
    store = _store([_episode("same-ambiguity", -1)])
    _, result = _run(store)
    assert result.branches[0].probabilities == result.branches[1].probabilities


def test_same_identifier_with_changed_action_or_revoked_flag_does_not_reuse_forecast(monkeypatch):
    store = _store([_episode("a", +1)])
    f = CaseMemoryOutcomeForecaster(store)
    action = _actions()[0]
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    first = f.forecast(_contrast(), (action,), None)[action.identifier]
    assert not first.refusal
    changed = replace(action, time_hours=72)
    assert f.forecast(_contrast(), (changed,), None)[action.identifier].refusal
    renamed = replace(action, expected_outcomes={H1: "positive", H2: "negative"})
    assert "positive" in f.forecast(_contrast(), (renamed,), None)[action.identifier].branches[0].probabilities
    monkeypatch.delenv("MAESTRO_CASE_MEMORY_ENABLED")
    assert f.forecast(_contrast(), (action,), None)[action.identifier].refusal == "case_memory_disabled"


def test_proxy_labels_are_research_only_and_cannot_be_qualified(monkeypatch):
    store = CM.EpisodeStore()
    for e in _store([_episode("a", +1)]).latest():
        store.append(replace(e, real_measurements=tuple(replace(m, label_kind="derived_annotation_proxy")
                                                       for m in e.real_measurements)))
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    action = _actions()[0]
    assert CaseMemoryOutcomeForecaster(store).forecast(_contrast(), (action,), None)[action.identifier].refusal
    _, research = _run(store)
    assert not research.refusal
    with pytest.raises(ValueError, match="proxy_label_is_not_experimental_evidence"):
        qualify_result(store.latest()[0].real_measurements[0], qc_passed=True, detected=True, eliminated=(H2,))


def test_unplanned_rows_and_different_contrasts_do_not_become_support():
    for replacement in ({"status": CM.ScientificMeasurementStatus.PLANNED_MISSING},
                        {"contrast": (H1, "unrelated")}):
        store = CM.EpisodeStore()
        for e in _store([_episode("a", +1)]).latest():
            store.append(replace(e, real_measurements=tuple(replace(m, **replacement) for m in e.real_measurements)))
        assert _run(store)[1].refusal


def test_legacy_measurement_serialisation_preserves_digest():
    legacy = {"action_id": "a", "status": "qualified", "outcome_label": "match_h1",
              "independent_units": 1, "source": "legacy"}
    measurement = CM.RealMeasurement("a", CM.ScientificMeasurementStatus.QUALIFIED, "match_h1", 1, "legacy")
    assert CM.digest(measurement) == CM.digest(legacy)


def test_centroid_excludes_self_and_all_test_signatures():
    pack = {"units": {"self": {"moa": "A", "unseen": False},
                      "ref": {"moa": "A", "unseen": False}, "test": {"moa": "A", "unseen": True}}}
    arrays = {"vec::self::cell": np.array([1000., 0.]), "vec::ref::cell": np.array([0., 2.]),
              "vec::test::cell": np.array([-1000., 0.])}
    np.testing.assert_array_equal(_reference_centroid(pack, arrays, "A", "cell", "self"), [0., 2.])


@pytest.mark.parametrize("raw", [{"a": float("nan")}, {"a": float("inf")}, {"a": -1}])
def test_invalid_masses_are_rejected_instead_of_silently_normalised(raw):
    with pytest.raises(ValueError, match="invalid_probability_mass"):
        support_aware_shrinkage(raw, effective_support=1, domain_shift=0, base_prior={"a": 1})
