"""Contracts of the Scientific Decision Review (maestro.decision_review)."""
import pytest

from maestro.campaign_budget import CampaignBudget
from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.decision_review import (APPROVAL_MISMATCH, APPROVAL_MISSING, RANKING_NOT_PROBABILITY, SELF_APPROVAL,
                                     DiscriminatingExperiment, EvidenceItem, Explanation, ExperimentRequest, Prediction,
                                     ReviewStatus, admit, approve, authorize_execution, decision_digest,
                                     discriminating_experiments, exploration_tournament, review)
from maestro.models import EvidenceKind as K

CTX = "PRISM:barcode:120h:8dose:pooled"
SHA = "a" * 64
SECONDARY = DiscriminatingExperiment("prism_secondary", "secondary_z", cost=1)
ORTHOGONAL = DiscriminatingExperiment("orthogonal_curve", "orthogonal_z", cost=3)


def _explanations():
    return (Explanation("SELECTIVE", "coherent sensitive subpopulation", (Prediction("secondary_z", "<=", -2.0),
                                                                        Prediction("breadth", ">=", 2.0)), progression=True),
            Explanation("NOISE", "isolated single-dose outlier", (Prediction("secondary_z", ">", -1.0), Prediction("breadth", "<=", 1.0))),
            Explanation("GENERIC", "broad cytotoxicity", (Prediction("generic_fraction", ">=", 0.3),)))


def _item(observable, value, kind=K.REAL_MEASUREMENT, status=S.QUALIFIED, context=CTX):
    return EvidenceItem(observable, value, kind, status, context, "features.npz", SHA)


def test_only_qualified_real_measurements_in_the_same_context_decide():
    assert admit(_item("secondary_z", -3.0), CTX) == (True, "admitted")
    assert admit(_item("secondary_z", -3.0, kind=K.MODEL_PREDICTION), CTX)[0] is False
    assert admit(_item("secondary_z", -3.0, kind=K.RETRIEVED_SOURCE), CTX)[0] is False
    assert admit(_item("secondary_z", -3.0, status=S.PLANNED_MISSING), CTX)[0] is False
    assert admit(_item("secondary_z", -3.0, status=S.QC_FAILED), CTX)[0] is False
    assert admit(_item("secondary_z", -3.0, context="CTRP:atp:72h:16dose:arrayed"), CTX)[1].startswith("context_mismatch")


def test_a_model_prediction_can_neither_falsify_nor_progress_a_candidate():
    predicted_failure = [_item("secondary_z", 0.5, kind=K.MODEL_PREDICTION), _item("breadth", 4.0, kind=K.DERIVED_ANALYSIS)]
    d = review("c1", _explanations(), predicted_failure, context=CTX, funded=True, menu=(SECONDARY,))
    assert d.status == ReviewStatus.GO                                # supported by admitted breadth only
    assert any("model_prediction_not_admitted" in x for x in d.limitations)
    only_prediction = [_item("secondary_z", -4.0, kind=K.MODEL_PREDICTION)]
    d = review("c2", _explanations(), only_prediction, context=CTX, funded=True, menu=(SECONDARY,))
    assert d.status == ReviewStatus.NEED_MORE_EVIDENCE and d.experiment == SECONDARY


def test_measured_contradiction_is_a_named_no_go():
    d = review("c3", _explanations(), [_item("secondary_z", 0.2), _item("breadth", 5.0, kind=K.DERIVED_ANALYSIS)],
               context=CTX, funded=True, menu=(SECONDARY,))
    assert d.status == ReviewStatus.NO_GO
    assert d.reasons == ("CONTRADICTED:secondary_z <= -2",)
    assert d.evidence_sha256 == (SHA,)


def test_unfunded_or_unsupported_candidates_need_a_discriminating_experiment():
    d = review("c4", _explanations(), [_item("breadth", 5.0, kind=K.DERIVED_ANALYSIS)], context=CTX, funded=False,
               menu=(ORTHOGONAL, SECONDARY))
    assert d.status == ReviewStatus.NEED_MORE_EVIDENCE and d.reasons == ("NOT_FUNDED",)
    assert d.experiment == SECONDARY                                  # the orthogonal assay predicts nothing that differs
    with pytest.raises(ValueError, match="discriminating experiment"):
        review("c5", _explanations(), [], context=CTX, funded=True, menu=(ORTHOGONAL,))


def test_no_signal_is_a_no_go_and_explanations_must_compete():
    assert review("c6", _explanations(), [], context=CTX, funded=True, no_signal=True).status == ReviewStatus.NO_GO
    with pytest.raises(ValueError, match="two competing"):
        review("c7", _explanations()[:1], [], context=CTX, funded=True)
    with pytest.raises(ValueError, match="not falsifiable"):
        Explanation("VAGUE", "it works somehow", ())
    two_progression = (_explanations()[0], Explanation("ALT", "alt", (Prediction("x", "<=", 0.0),), progression=True))
    with pytest.raises(ValueError, match="exactly one"):
        review("c8", two_progression, [], context=CTX, funded=True)


def test_discriminating_experiments_need_incompatible_predictions_from_different_explanations():
    one_sided = (Explanation("A", "a", (Prediction("secondary_z", "<=", -2.0), Prediction("secondary_z", ">=", -5.0)), progression=True),
                 Explanation("B", "b", (Prediction("breadth", ">=", 1.0),)))
    assert discriminating_experiments(one_sided, (SECONDARY,)) == ()
    assert discriminating_experiments(_explanations(), (ORTHOGONAL, SECONDARY)) == (SECONDARY,)


def test_tournament_ranks_exploration_only_and_is_reproducible():
    judge = lambda a, b: min(a, b)                                    # deterministic preference
    first = exploration_tournament(["d", "b", "a", "c"], judge, rounds=3)
    second = exploration_tournament(["d", "b", "a", "c"], judge, rounds=3)
    assert first == second and first.order[0] == "a"
    with pytest.raises(TypeError, match=RANKING_NOT_PROBABILITY):
        first.as_probability()
    with pytest.raises(TypeError, match=RANKING_NOT_PROBABILITY):
        float(first)
    with pytest.raises(TypeError, match=RANKING_NOT_PROBABILITY):
        EvidenceItem("priority", first, K.DERIVED_ANALYSIS, S.QUALIFIED, CTX, "x", SHA)
    forfeits = exploration_tournament(["a", "b"], lambda a, b: "neither", rounds=2)
    assert forfeits.wins == {"a": 0.0, "b": 0.0} and forfeits.matches == 1


def test_consequential_experiments_need_a_matching_human_approval_within_budget():
    budget = CampaignBudget(total=4, measurement_cost=1, turnaround_cost=0, unit="dose-response")
    request = ExperimentRequest("c1", SECONDARY, requested_by="maestro", rationale="discriminates SELECTIVE from NOISE")
    with pytest.raises(PermissionError, match=APPROVAL_MISSING):
        authorize_execution(request, None, budget, spent_measurements=0, spent_turnarounds=0)
    with pytest.raises(PermissionError, match=SELF_APPROVAL):
        approve(request, "agent")
    approval = approve(request, "dr.reviewer")
    other = ExperimentRequest("c2", SECONDARY, requested_by="maestro", rationale="x")
    with pytest.raises(PermissionError, match=APPROVAL_MISMATCH):
        authorize_execution(other, approval, budget, spent_measurements=0, spent_turnarounds=0)
    assert authorize_execution(request, approval, budget, spent_measurements=3, spent_turnarounds=0) == 4
    with pytest.raises(ValueError, match="exceeds"):
        authorize_execution(request, approval, budget, spent_measurements=4, spent_turnarounds=0)


def test_decision_digest_is_stable_and_sensitive():
    ev = [_item("secondary_z", -3.0), _item("breadth", 4.0, kind=K.DERIVED_ANALYSIS)]
    a = review("c1", _explanations(), ev, context=CTX, funded=True, menu=(SECONDARY,), provenance={"code": "x"})
    b = review("c1", _explanations(), ev, context=CTX, funded=True, menu=(SECONDARY,), provenance={"code": "x"})
    c = review("c1", _explanations(), ev, context=CTX, funded=False, menu=(SECONDARY,), provenance={"code": "x"})
    assert a.status == ReviewStatus.GO and decision_digest(a) == decision_digest(b) != decision_digest(c)
