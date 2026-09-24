"""Regression tests written directly from the strict-research-audit counterexamples.

File summary
- Path: tests/test_audit_regressions.py
- Purpose: Pin the audit findings F01, F02, F04, F05, F06 as executable expectations.
- Core points:
  - Each test corresponds to one probe of the 2026-09-11 strict review that used to
    reproduce a defect.  The probe recorded the defect; these tests assert the corrected
    semantics, so the same defect cannot return silently.
  - No test asserts a biological conclusion, and none calls an LLM or a virtual-cell model.
- Interfaces: `test_*` functions
- Depends on: agent.orchestrator, agent.cases, maestro, tests.test_case_decision_loop (helpers)
"""
from pathlib import Path

import pytest

import runpy

from agent.orchestrator import MAESTROOrchestrator
from maestro import (
    MODE_COMPARATOR_FIELD,
    REALISATION_FIELD,
    SUFFICIENT_FUNCTION_FIELD,
    DecisionStatus,
    EvidenceAction,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    InterpretationTable,
    MechanismContrast,
    MechanismHypothesis,
    OutcomeClass,
    OutcomeRule,
    BudgetedEvidenceSelector,
)
from maestro.outcome import admit_evidence
from maestro.repair import RepairLedger, RepairRecord
from maestro.models import RepairKind
from virtual_cell import (
    Interval,
    IntervalKind,
    Intervention,
    PredictionRequest,
    StatePrediction,
    SystemContext,
)


ROOT = Path(__file__).resolve().parents[1]
_helpers = runpy.run_path(str(ROOT / "tests" / "test_case_decision_loop.py"))
TASK = _helpers["TASK"]
PLAN = _helpers["PLAN"]
_actions = _helpers["_actions"]
_profile = _helpers["_profile"]
_orchestrator = _helpers["_orchestrator"]
_result = _helpers["_result"]


# --------------------------------------------------------------------------------------
# F01: one admission verdict for every consumer
# --------------------------------------------------------------------------------------


def test_f01_model_prediction_neither_licenses_a_decision_nor_marks_a_prerequisite(tmp_path: Path):
    """A prediction is readable and QC-passing, and still grants nothing."""

    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: _result(
            "functional",
            (REALISATION_FIELD,),
            evidence_kind=EvidenceKind.MODEL_PREDICTION,
        ),
        case_id="audit-f01-live",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED
    assert loop.evidence_state is not None
    assert loop.evidence_state.mechanism_updates() == ()
    assert not controller._profile_after_result(
        _profile(), _result("functional", (REALISATION_FIELD,)), None
    ).has_measured_function()


def test_f01_functional_field_is_measured_only_through_an_admitted_result():
    contrast = MechanismContrast(
        identifier="audit-f01",
        hypotheses=(
            MechanismHypothesis("incomplete_perturbation", "A."),
            MechanismHypothesis("mode_non_equivalence", "B."),
        ),
        differing_assumptions=("functional implementation",),
        plan=EvidenceAction("functional", "Measure activity.", 2.0, ("incomplete_perturbation",)),
    )
    table = InterpretationTable(
        [
            OutcomeRule(
                identifier="implementation",
                outcome_label="implementation",
                matched_fields=frozenset({REALISATION_FIELD}),
                scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
            )
        ]
    )
    profile = FunctionalInterventionProfile(mode="drug", context_identifier="cell-a")

    for kind in (
        EvidenceKind.MODEL_PREDICTION,
        EvidenceKind.DERIVED_ANALYSIS,
        EvidenceKind.RETRIEVED_SOURCE,
    ):
        observation = _result("functional", (REALISATION_FIELD,), evidence_kind=kind)
        interpretation = table.interpret(observation, contrast, profile, contrast.plan)
        admission = admit_evidence(interpretation, observation)
        assert admission.readable and admission.qc_passed
        assert not admission.admissible, kind
        assert admission.admitted_fields == (), kind

    measured = _result("functional", (REALISATION_FIELD,))
    admission = admit_evidence(
        table.interpret(measured, contrast, profile, contrast.plan), measured
    )
    assert admission.admissible
    assert admission.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION


def test_f01_a_rule_whose_conditions_did_not_hold_is_admitted_nowhere(tmp_path: Path):
    """A rule matched by field name, but a declared condition was absent.

    This is the audit's second F01 counterexample: the interpretation is
    ``condition_unmatched``, so nothing may be admitted and nothing may be decided.
    """

    controller = _orchestrator(tmp_path, [TASK, PLAN])
    controller._interpretation_table = InterpretationTable(
        [
            OutcomeRule(
                identifier="guarded",
                outcome_label="guarded",
                matched_fields=frozenset({REALISATION_FIELD}),
                required_conditions=frozenset({"matched_exposure"}),
                scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
            )
        ]
    )
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: _result("functional", (REALISATION_FIELD,)),
        case_id="audit-f01-unmatched",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.evidence_state is not None
    assert loop.evidence_state.updates[0].outcome_class is OutcomeClass.CONDITION_UNMATCHED
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED


def test_f01_a_context_mismatch_is_refused_before_interpretation(tmp_path: Path):
    """The store refuses a result whose context is not the planned one."""

    controller = _orchestrator(tmp_path, [TASK, PLAN])
    with pytest.raises(ValueError, match="context"):
        controller.run_case_loop(
            "Resolve the discrepancy.",
            available_actions=_actions(),
            intervention_profile=_profile(),
            result_provider=lambda action, turn: _result(
                "functional", (REALISATION_FIELD,), context_identifier="cell-b"
            ),
            case_id="audit-f01-context",
            budget=5.0,
            max_rounds=1,
        )


# --------------------------------------------------------------------------------------
# F02: a sufficient-function label is not a mode change
# --------------------------------------------------------------------------------------


def test_f02_a_mode_decision_needs_a_declared_comparison_not_just_sufficient_function(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result("functional", (SUFFICIENT_FUNCTION_FIELD, "phenotype:viability:unaffected"))
            if action.identifier == "functional"
            else None
        ),
        case_id="audit-f02",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED
    assert loop.evidence_state is not None
    assert loop.evidence_state.still_ambiguous


# --------------------------------------------------------------------------------------
# F04: one observation, one transition, one terminal state
# --------------------------------------------------------------------------------------


def test_f04_terminal_decision_stops_the_loop_after_one_observation(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN, TASK, PLAN, TASK, PLAN])
    calls: list[str] = []

    def provider(action, turn):
        calls.append(action.identifier)
        return _result("functional", (REALISATION_FIELD,))

    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=provider,
        case_id="audit-f04",
        budget=10.0,
        max_rounds=3,
    )
    assert calls == ["functional"], "A decided case must not run the same action again."
    assert len(loop.turns) == 1
    assert loop.stop_reason == "decision:decided"
    assert loop.decision is not None and loop.decision.status is DecisionStatus.DECIDED
    assert len(loop.evidence_state.updates) == 1
    snapshot = controller._case_store.snapshot("audit-f04")
    assert snapshot.state.value == "completed"
    assert snapshot.stop_reason == "decision:decided"


def test_f04_a_repeated_result_identifier_is_not_a_second_observation(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN, TASK, PLAN, TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        # Neither sufficient-function set is admissible, so the case keeps asking for the
        # same planned action and the provider keeps returning the same result identifier.
        result_provider=lambda action, turn: (
            _result("functional", (SUFFICIENT_FUNCTION_FIELD,))
            if action.identifier == "functional"
            else None
        ),
        case_id="audit-f04-duplicate",
        budget=10.0,
        max_rounds=3,
    )
    assert len(loop.evidence_state.updates) == 1, "A repeated result must not update twice."
    assert len(loop.reflections) == 1


# --------------------------------------------------------------------------------------
# F05: identity and version binding
# --------------------------------------------------------------------------------------


def test_f05_renaming_hypotheses_is_a_migration_not_a_silent_inheritance(tmp_path: Path):
    renamed = {
        **PLAN,
        "hypotheses": [
            {"identifier": "new_a", "description": "new", "proposed_action": "revise_intervention"},
            {"identifier": "new_b", "description": "new", "proposed_action": "change_intervention_mode"},
        ],
    }
    controller = _orchestrator(tmp_path, [TASK, PLAN, TASK, renamed])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result("functional", (SUFFICIENT_FUNCTION_FIELD, "phenotype:viability:unaffected"))
            if action.identifier == "functional"
            else None
        ),
        case_id="audit-f05-drift",
        budget=10.0,
        max_rounds=2,
    )
    assert loop.evidence_state is not None
    assert loop.evidence_state.candidates == frozenset({"new_a", "new_b"})
    assert loop.evidence_state.eliminated == frozenset()
    assert loop.turns[-1].contrast is not None
    assert loop.turns[-1].contrast.identifiers() == loop.evidence_state.candidates


def test_f05_a_bundle_result_is_read_against_its_own_action(tmp_path: Path):
    six_hours = EvidenceAction("a", "Early readout.", 1.0, ("h1", "h2"), time_hours=6.0)
    twenty_four_hours = EvidenceAction("b", "Late readout.", 1.0, ("h1", "h2"), time_hours=24.0)
    contrast = MechanismContrast(
        identifier="audit-f05-bundle",
        hypotheses=(MechanismHypothesis("h1", "H1."), MechanismHypothesis("h2", "H2.")),
        differing_assumptions=("timing",),
        plan=six_hours,
        additional_plans=(twenty_four_hours,),
    )
    table = InterpretationTable(
        [
            OutcomeRule(
                identifier="late",
                outcome_label="late",
                matched_fields=frozenset({"found"}),
                action_identifier="b",
                requires_time_match=True,
                eliminates=frozenset({"h1"}),
            )
        ]
    )
    observation = _result("b", ("found",))
    assert observation.time_hours == 24.0

    bound = table.interpret(
        observation,
        contrast,
        _profile(),
        MAESTROOrchestrator._action_for_result(contrast, observation, twenty_four_hours),
    )
    assert bound.outcome_class is OutcomeClass.PREDICTED

    primary = table.interpret(observation, contrast, _profile(), six_hours)
    assert primary.outcome_class is OutcomeClass.CONDITION_UNMATCHED


# --------------------------------------------------------------------------------------
# F06: prediction value is per-action and never buys cost
# --------------------------------------------------------------------------------------


def test_f06_prediction_priority_follows_each_action_own_readout():
    controller = object.__new__(MAESTROOrchestrator)
    from maestro.reliability import PredictionReliabilityLedger

    controller._reliability = PredictionReliabilityLedger()
    actions = (
        EvidenceAction("a", "a", 1, ("h1", "h2"), prediction_readout="r1", prediction_relevance=1),
        EvidenceAction("b", "b", 1, ("h1", "h2"), prediction_readout="r2", prediction_relevance=1),
        EvidenceAction(
            "missing", "missing", 1, ("h1", "h2"), prediction_readout="absent", prediction_relevance=1
        ),
    )
    request = PredictionRequest(
        "r", "c", "k", 1, Intervention("D", "drug", ()), SystemContext("C", "C"),
        ("r1", "r2", "absent"), "m",
    )
    prediction = StatePrediction(
        True, {"r1": 1.0, "r2": 100.0}, 0.0, (), model_version="m",
        request_id="r", confidence=0.5, in_distribution=True,
    )
    original = controller._prediction_action_priorities(prediction, request, actions)
    swapped = controller._prediction_action_priorities(
        StatePrediction(True, {"r1": 100.0, "r2": 1.0}, 0.0, (), model_version="m",
                        request_id="r", confidence=0.5, in_distribution=True),
        request,
        actions,
    )
    assert original == {"a": 1.0, "b": 100.0}
    assert swapped == {"a": 100.0, "b": 1.0}
    assert "missing" not in original, "A readout absent from the prediction carries no weight."


def test_f06_a_prediction_cannot_buy_a_redundant_or_costlier_action():
    actions = tuple(
        EvidenceAction(identifier, identifier, cost, ("h1", "h2"))
        for identifier, cost in (("cheap", 1.0), ("expensive", 9.0))
    )
    profile = FunctionalInterventionProfile(mode="drug")
    plain = BudgetedEvidenceSelector().select(frozenset({"h1", "h2"}), actions, profile, 10.0)
    ranked = BudgetedEvidenceSelector().select(
        frozenset({"h1", "h2"}), actions, profile, 10.0,
        action_priorities={"cheap": 1.0, "expensive": 1.0},
    )
    assert [action.identifier for action in plain.actions] == ["cheap"]
    assert [action.identifier for action in ranked.actions] == ["cheap"]
    assert ranked.total_cost == plain.total_cost == 1.0


def test_f06_equal_coverage_and_cost_prefers_fewer_actions():
    one_arm = EvidenceAction("one", "One arm.", 2.0, ("h1", "h2"))
    cheap_pair = (
        EvidenceAction("left", "Left.", 1.0, ("h1",)),
        EvidenceAction("right", "Right.", 1.0, ("h2",)),
    )
    plan = BudgetedEvidenceSelector().select(
        frozenset({"h1", "h2"}), (one_arm, *cheap_pair), FunctionalInterventionProfile(mode="drug"), 2.0
    )
    assert [action.identifier for action in plan.actions] == ["one"]


# --------------------------------------------------------------------------------------
# F10: repair credit follows the edit, not a reused attempt number
# --------------------------------------------------------------------------------------


def test_f10_repair_credit_is_scored_by_edit_fingerprint():
    ledger = RepairLedger()
    for fingerprint, action in (("first", "alpha"), ("second", "beta")):
        ledger.register(
            RepairRecord(
                attempt=1,
                fingerprint=fingerprint,
                kind=RepairKind.CHANGE_READOUT_OR_TIME,
                action_identifier=action,
                triggered_by=(),
                modified_fields=(),
                expected_gain="",
                adopted=True,
                resolved_reasons=(),
                remaining_reasons=(),
            )
        )
    scored = ledger.resolve_fingerprint("second", True)
    assert scored is not None and scored.action_identifier == "beta"
    first = next(record for record in ledger.records if record.fingerprint == "first")
    assert first.gap_resolved is None, "An earlier attempt must not be scored instead."


@pytest.mark.parametrize("field", [REALISATION_FIELD, SUFFICIENT_FUNCTION_FIELD, MODE_COMPARATOR_FIELD])
def test_audit_field_constant_is_a_declared_interpretation_field(field: str):
    """The decision layer depends on these names; keep them visible and stable."""

    assert field and ":" in field


# --------------------------------------------------------------------------------------
# F07: a descriptive spread is not a calibrated predictive interval
# --------------------------------------------------------------------------------------


def test_f07_a_descriptive_band_cannot_claim_a_coverage_level():
    def prediction(interval: Interval) -> StatePrediction:
        return StatePrediction(
            applicable=True,
            state_change={"a": 0.5},
            uncertainty=0.1,
            limitations=(),
            intervals={"a": interval},
            confidence=0.3,
            in_distribution=True,
        )

    claims_a_level = Interval(0.0, 1.0, kind=IntervalKind.DESCRIPTIVE, level=0.9)
    assert "descriptive_interval_claims_a_level:a" in prediction(claims_a_level).contract_errors()

    unbased_claim = Interval(0.0, 1.0, kind=IntervalKind.CALIBRATED, level=0.9)
    assert "calibrated_interval_without_basis:a" in prediction(unbased_claim).contract_errors()

    honest_spread = Interval(
        0.0, 1.0, basis="spread of the statistic across its own dimensions"
    )
    assert honest_spread.claims_coverage is False
    assert prediction(honest_spread).contract_errors() == ()

    calibrated = Interval(
        0.0, 1.0, kind=IntervalKind.CALIBRATED, level=0.9, basis="held-out residuals, split leave_dose_out"
    )
    assert calibrated.claims_coverage is True
    assert prediction(calibrated).contract_errors() == ()
