"""Invariants of the measurement-choice harness: refusal, evidence boundary, and reproducibility.

File summary
- Path: research/dynamic_world_model/test_validator.py
- Purpose: pin the behaviours the study's conclusions rest on, so a later edit cannot quietly
  change them: an undetected response eliminates nothing; a model prediction routed through the
  evidence path cannot eliminate a hypothesis; a failed measurement is a named non-success;
  the leave-one-out Gram similarity equals the direct computation; a card refuses by name below its
  reference minimum; and a rerun of one fold reproduces the recorded episodes exactly.
- Run: python -m pytest -q research/dynamic_world_model/test_validator.py
  (outside the repository suite: `testpaths = ["tests"]`; the last test needs the prepared data)
- Depends on: common.py, episodes.py, maestro.models, maestro.outcome
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402
import episodes as E  # noqa: E402

from maestro.models import EvidenceKind  # noqa: E402
from maestro.outcome import EvidenceState  # noqa: E402


def _table(n=12, g=40, seed=0):
    rng = np.random.default_rng(seed)
    Y = rng.normal(size=(n, g))
    klass = np.array(["a"] * 4 + ["b"] * 4 + ["c"] * 4, dtype=object)
    detected = np.array([True, True, False, True, True, True, True, False, False, True, True, True])
    G = Y @ Y.T
    return C.ConditionTable(("L", 24.0, 10.0), [f"x{i}" for i in range(n)], klass, detected, Y, G, G.sum(1),
                            float(G.sum()), Y.sum(0))


def test_undetected_response_never_eliminates_even_with_perfect_scores():
    scores = np.array([0.99, -0.5])
    outcome = C.decide(False, scores, 0, 1, np.array([5, 5]), np.array([5, 5]), floor=0.1, margin=0.0)
    assert outcome == "undetected"


def test_absence_of_templates_eliminates_only_when_two_references_were_measured():
    scores = np.array([0.8, -np.inf])
    assert C.decide(True, scores, 0, 1, np.array([3, 2]), np.array([3, 0]), 0.2, 0.1) == "eliminate_b"
    assert C.decide(True, scores, 0, 1, np.array([3, 1]), np.array([3, 0]), 0.2, 0.1) == "ambiguous"


def test_leave_one_out_gram_similarity_equals_direct_computation():
    t = _table()
    fast = C._loo_class_scores(t, ("a", "b", "c"))

    def perp(v, u):
        u = u / np.linalg.norm(u)
        return v - (v @ u) * u

    for c in range(len(t.names)):
        axis = t.S - t.Y[c]
        for j, k in enumerate(("a", "b", "c")):
            members = [i for i in range(len(t.names)) if t.klass[i] == k and t.detected[i] and i != c]
            if not members:
                assert not np.isfinite(fast[c, j])
                continue
            pc = perp(t.Y[c], axis)
            direct = max(float(pc @ perp(t.Y[i], axis) / np.linalg.norm(pc) / np.linalg.norm(perp(t.Y[i], axis)))
                         for i in members)
            assert math.isclose(fast[c, j], direct, abs_tol=1e-10)


def _contrast(h1="A", h2="B"):
    key = ("A549", 24.0, 10000.0)
    action = E.make_action(key, h1, h2)
    return key, action, E.contrast_for(h1, h2, [action])


def test_qualified_matching_profile_eliminates_the_other_hypothesis_through_the_repository_rules():
    key, action, contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    state, interpretation, outcome = C.evidence_update(state, contrast, action, key, {"outcome": "eliminate_b"},
                                                       "A", "B", qc=True, agreement=0.5, source="test")
    assert outcome == "eliminate_b"
    assert state.candidates == frozenset({"A"})
    assert interpretation.can_update_mechanism


def test_undetected_result_is_retained_at_implementation_scope_without_elimination():
    key, action, contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    state, interpretation, outcome = C.evidence_update(state, contrast, action, key, {"outcome": "undetected"},
                                                       "A", "B", qc=True, agreement=0.02, source="test")
    assert state.candidates == frozenset({"A", "B"})
    assert interpretation.scope.value == "intervention_implementation"
    assert not interpretation.can_update_mechanism


def test_failed_measurement_is_a_named_non_success_and_eliminates_nothing():
    key, action, contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    state, interpretation, outcome = C.evidence_update(state, contrast, action, key, {"outcome": "eliminate_b"},
                                                       "A", "B", qc=False, agreement=float("nan"), source="test")
    assert outcome == "quality_failed"
    assert interpretation.outcome_class.value == "quality_failed"
    assert state.candidates == frozenset({"A", "B"})


def test_a_prediction_routed_through_the_evidence_path_cannot_eliminate():
    from agent.cases import MeasurementResult
    from maestro.models import FunctionalInterventionProfile
    from maestro.outcome import InterpretationTable, OutcomeRule
    key, action, contrast = _contrast()
    forecast = MeasurementResult(action_identifier=action.identifier, statement="forecast", source_id="model",
                                 context_identifier="A549", time_hours=24.0, independent_units=2, quality_passed=True,
                                 conditions={"dose_nM": "10000"}, evidence_kind=EvidenceKind.MODEL_PREDICTION,
                                 interpretation_fields=("response_detected", "profile_matches:H1"))
    rule = OutcomeRule("matches_h1", "profile_matches_h1", frozenset({"response_detected", "profile_matches:H1"}),
                       eliminates=frozenset({"B"}), requires_time_match=True, minimum_independent_units=2)
    interpretation = InterpretationTable((rule,)).interpret(
        forecast, contrast, FunctionalInterventionProfile(mode="small_molecule"), action)
    state = EvidenceState.open(contrast.hypotheses).apply(interpretation, forecast)
    assert interpretation.outcome_class.value == "non_measurement"
    assert state.candidates == frozenset({"A", "B"})


def test_card_refuses_by_name_below_its_reference_minimum():
    t = _table()
    ft = C.FoldTables(0, "T", {t.key: t}, ("a", "b", "c"))
    ft.loo_scores[t.key] = C._loo_class_scores(t, ft.classes)
    card = C.card(ft, t.key, "a", "b", {"floor": 0.1, "margin": 0.0, "eliminates": True}, minimum_references=5)
    assert card == {"served": False, "reason": "too_few_references_at_condition:a:4"}


@pytest.mark.skipif(not (C.OUTPUTS / "episodes" / "episodes.jsonl").is_file(), reason="needs the recorded run")
def test_a_rerun_of_one_fold_reproduces_the_recorded_episodes():
    recorded = [json.loads(line) for line in (C.OUTPUTS / "episodes" / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    recorded = [r for r in recorded if r["tier"] == "A" and r["fold"] == 1]
    rerun, _ = E.run_fold(("A", 1))
    assert len(rerun) == len(recorded)
    strip = lambda r: json.dumps(C.clean(r), default=C._default, sort_keys=True)  # noqa: E731
    assert [strip(r) for r in rerun] == [strip(r) for r in recorded]
