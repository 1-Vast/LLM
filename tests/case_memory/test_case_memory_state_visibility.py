"""Regression checks for pre-action state visibility and condition-safe retrieval."""
from dataclasses import replace

import pytest

from maestro.adaptive_retrieval import AdaptiveRetriever, RetrievalProblem
from maestro.case_memory import EpisodeObservation, EpisodeStore, ScientificMeasurementStatus
from maestro.adaptive_retrieval import ContextFeatures, DirectionalState, FeatureArm
from tests.fixtures.case_memory_integration import _episode


def _observation(condition="before", **kwargs):
    return EpisodeObservation(
        condition, ScientificMeasurementStatus.QUALIFIED, "l1000",
        cell_line="A549", time_h=6.0, dose_nM=10000.0,
        pathway_direction={"P": 1.0}, **kwargs)


def _problem(**kwargs):
    problem = RetrievalProblem(
        "p", "l1000", "l1000", "compound", "transcriptomic", "vehicle",
        ContextFeatures(cell_line="A549", time_h=24.0, dose_nM=10000.0),
        ("H_on", "H_off"), DirectionalState(pathway_direction={"P": 1.0}),
        FeatureArm.PATHWAY_DIRECTION,
        state_context=ContextFeatures(cell_line="A549", time_h=6.0, dose_nM=10000.0))
    return replace(problem, **kwargs)


def _retriever(observations):
    store = EpisodeStore()
    store.append(_episode(observations=tuple(observations)))
    return AdaptiveRetriever(store)


def test_outcome_signature_cannot_supply_directional_retrieval_state():
    retriever = _retriever([_observation(availability="outcome_only")])
    result = retriever.retrieve(_problem(), research_mode=True)
    assert not result.precedents["H_on"]
    assert not result.usable["H_on"]


@pytest.mark.parametrize("problem", [
    _problem(feature_arm=FeatureArm.SCALAR),
    _problem(state=DirectionalState()),
])
def test_state_free_baseline_can_retrieve_outcome_only_cases(problem):
    retriever = _retriever([_observation(availability="outcome_only")])
    result = retriever.retrieve(problem, research_mode=True)
    assert result.precedents["H_on"][0].components["state_similarity"] == 1.0


def test_pre_action_context_is_distinct_from_future_action_context():
    before = _observation()
    future = replace(before, condition_id="after", time_h=24.0,
                     pathway_direction={"P": -1.0}, availability="outcome_only")
    retriever = _retriever([before, future])
    result = retriever.retrieve(_problem(), research_mode=True)
    assert result.precedents["H_on"][0].components["state_similarity"] == 1.0
    # Altering or reordering future measurements must not change retrieval.
    altered = _retriever([replace(future, pathway_direction={"P": 999.0}), before])
    assert altered.retrieve(_problem(), research_mode=True) == result


@pytest.mark.parametrize("field,value", [
    ("cell_line", "MCF7"), ("time_h", 12.0), ("dose_nM", 1000.0), ("assay", "scRNA"),
])
def test_only_pre_action_observations_matching_state_context_are_used(field, value):
    matching = _observation()
    other = replace(matching, condition_id="other", pathway_direction={"P": -1.0},
                    **{field: value})
    retriever = _retriever([matching, other])
    context = replace(_problem().state_context, assay="l1000")
    state = retriever._case_state(retriever.store.latest()[0], context)
    assert state.pathway_direction == {"P": 1.0}


def test_ambiguous_conditions_or_conflicting_replicates_do_not_use_last_row():
    first = _observation()
    for second in (replace(first, condition_id="different"),
                   replace(first, pathway_direction={"P": -1.0})):
        for rows in ([first, second], [second, first]):
            retriever = _retriever(rows)
            result = retriever.retrieve(_problem(), research_mode=True)
            assert not result.precedents["H_on"]


def test_failed_measurement_pathway_values_are_not_pre_action_state():
    failed = replace(_observation(), status=ScientificMeasurementStatus.QC_FAILED)
    retriever = _retriever([failed])
    assert not retriever.retrieve(_problem(), research_mode=True).precedents["H_on"]


@pytest.mark.parametrize("version", [None, "loo-proxy-2"])
def test_old_proxy_archive_defaults_do_not_make_future_signatures_visible(version):
    episode = _episode(observations=(_observation(),))
    provenance = {**episode.provenance, "builder": "tools.case_memory.build_cases"}
    if version is not None:
        provenance["builder_version"] = version
    store = EpisodeStore()
    store.append(replace(episode, provenance=provenance))
    retriever = AdaptiveRetriever(store)
    assert not retriever.retrieve(_problem(), research_mode=True).precedents["H_on"]
    baseline = _problem(feature_arm=FeatureArm.SCALAR)
    assert retriever.retrieve(baseline, research_mode=True).precedents["H_on"]
