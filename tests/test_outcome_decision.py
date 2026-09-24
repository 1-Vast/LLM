"""Outcome interpretation rules (rho), set-based updates, and the decision layer.

File summary
- Path: tests/test_outcome_decision.py
- Purpose: Test outcome interpretation, set-based evidence updates, and the decision layer.
- Core points:
  - Asserts only a real measurement can constrain a mechanism contrast.
  - A condition-matched rule, not budget exhaustion, licenses a development decision.
- Interfaces: `test_*` functions
- Depends on: agent.cases, maestro
"""
from dataclasses import replace

from agent.cases import MeasurementResult
from maestro.models import BiologicalQuantity
from maestro import (
    DEFAULT_REQUIREMENTS,
    INCOMPLETE_PERTURBATION_FACTOR,
    MODE_COMPARATOR_FIELD,
    MODE_DIFFERENCE_FIELD,
    REALISATION_FIELD,
    SUFFICIENT_FUNCTION_FIELD,
    DecisionEngine,
    DecisionStatus,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceRequirement,
    EvidenceScope,
    FunctionalInterventionProfile,
    InterpretationTable,
    MeasurementStatus,
    MechanismContrast,
    MechanismHypothesis,
    OutcomeClass,
    OutcomeRule,
    default_rules_for,
)
from maestro.outcome import EvidenceState, admit_evidence


def _result(**overrides) -> MeasurementResult:
    payload = {
        "action_identifier": "functional",
        "statement": "Target activity measured.",
        "source_id": "source-a",
        "context_identifier": "cell-a",
        "time_hours": 24.0,
        "independent_units": 3,
        "quality_passed": True,
        "interpretation_fields": ("functional:target_activity:insufficient",),
        "result_id": "result-1",
    }
    payload.update(overrides)
    return MeasurementResult(**payload)


def _contrast() -> MechanismContrast:
    return MechanismContrast(
        identifier="contrast-1",
        hypotheses=(
            MechanismHypothesis(
                "incomplete_perturbation",
                "Perturbation was incomplete.",
                DevelopmentAction.REVISE_INTERVENTION,
                causal_factor=INCOMPLETE_PERTURBATION_FACTOR,
            ),
            MechanismHypothesis("mode_non_equivalence", "Modes are not equivalent.", DevelopmentAction.CHANGE_INTERVENTION_MODE),
        ),
        differing_assumptions=("functional implementation",),
        plan=EvidenceAction(
            "functional",
            "Measure proximal target activity.",
            2.0,
            ("incomplete_perturbation",),
            kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
            quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
            time_hours=24.0,
        ),
    )


def _complete_mode_evidence() -> tuple[str, ...]:
    """The field set a mode decision has to rest on: function, phenotype, comparison."""

    return (
        "phenotype:viability:unaffected",
        MODE_COMPARATOR_FIELD,
        MODE_DIFFERENCE_FIELD,
    )


def _table(contrast: MechanismContrast) -> InterpretationTable:
    return InterpretationTable(default_rules_for(contrast))


def test_quality_failure_is_retained_but_cannot_update_the_contrast():
    contrast = _contrast()
    interpretation = _table(contrast).interpret(
        _result(quality_passed=False),
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.QUALITY_FAILED
    assert interpretation.scope is EvidenceScope.MEASUREMENT_FEASIBILITY
    assert interpretation.eliminates == frozenset()
    assert not interpretation.can_update_mechanism

    state = EvidenceState.open(contrast.hypotheses).apply(interpretation, _result(quality_passed=False))
    assert state.candidates == frozenset({"incomplete_perturbation", "mode_non_equivalence"})
    assert len(state.updates) == 1
    assert len(state.mechanism_updates()) == 0


def test_insufficient_perturbation_constrains_implementation_only():
    contrast = _contrast()
    interpretation = _table(contrast).interpret(
        _result(),
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.PREDICTED
    assert interpretation.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION
    assert interpretation.eliminates == frozenset()

    state = EvidenceState.open(contrast.hypotheses).apply(interpretation, _result())
    assert state.still_ambiguous
    assert state.mechanism_updates() == ()


def test_sufficient_function_alone_cannot_retire_the_realisation_explanation():
    """A proximal measurement unlocks a comparator but cannot replace its result."""

    contrast = _contrast()
    profile = FunctionalInterventionProfile(mode="drug", context_identifier="cell-a")
    alone = _result(interpretation_fields=(SUFFICIENT_FUNCTION_FIELD,))
    interpretation = _table(contrast).interpret(alone, contrast, profile, contrast.plan)
    assert interpretation.outcome_class is OutcomeClass.PREDICTED
    assert interpretation.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION
    assert interpretation.eliminates == frozenset()
    assert not interpretation.can_update_mechanism

    state = EvidenceState.open(contrast.hypotheses).apply(interpretation, alone)
    assert state.still_ambiguous
    prior = admit_evidence(interpretation, alone, action=contrast.plan).measured_premises
    comparator = replace(contrast.plan, identifier="comparator", kind=EvidenceActionKind.MODE_MATCHED_COMPARATOR,
                         quantity=BiologicalQuantity.VIABILITY)
    complete = _result(action_identifier="comparator", result_id="result-2", interpretation_fields=_complete_mode_evidence())
    complete_interpretation = _table(contrast).interpret(
        complete, contrast, profile, comparator, prior_evidence=prior
    )
    assert complete_interpretation.can_update_mechanism
    assert complete_interpretation.eliminates == frozenset({"incomplete_perturbation"})

    resolved = state.apply(complete_interpretation, complete)
    assert resolved.resolved
    assert resolved.candidates == frozenset({"mode_non_equivalence"})


def test_an_unregistered_causal_factor_retires_nothing():
    """A plan label is not a causal factor, so a case cannot eliminate by accident."""

    implicit = MechanismContrast(
        identifier="contrast-implicit",
        hypotheses=(
            MechanismHypothesis("a", "A.", DevelopmentAction.REVISE_INTERVENTION),
            MechanismHypothesis("b", "B.", DevelopmentAction.CHANGE_INTERVENTION_MODE),
        ),
        differing_assumptions=("functional implementation",),
        plan=_contrast().plan,
    )
    observation = _result(interpretation_fields=_complete_mode_evidence())
    interpretation = _table(implicit).interpret(
        observation,
        implicit,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        implicit.plan,
    )
    assert interpretation.eliminates == frozenset()
    state = EvidenceState.open(implicit.hypotheses).apply(interpretation, observation)
    assert state.candidates == frozenset({"a", "b"})


def test_time_mismatch_blocks_the_mechanism_update():
    contrast = _contrast()
    observation = _result(
        interpretation_fields=(
            SUFFICIENT_FUNCTION_FIELD,
            "phenotype:viability:unaffected",
            MODE_COMPARATOR_FIELD,
            MODE_DIFFERENCE_FIELD,
        ),
        time_hours=2.0,
    )
    interpretation = _table(contrast).interpret(
        observation,
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.CONDITION_UNMATCHED
    assert interpretation.eliminates == frozenset()
    state = EvidenceState.open(contrast.hypotheses).apply(interpretation, observation)
    assert state.still_ambiguous


def test_qualified_result_outside_the_registered_categories_is_not_forced_into_a_hypothesis():
    contrast = _contrast()
    observation = _result(interpretation_fields=("mechanism:unexpected_feedback_loop",))
    interpretation = _table(contrast).interpret(
        observation,
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.OUT_OF_PREDICTION
    assert not interpretation.can_update_mechanism


def test_prediction_derived_records_never_update_the_contrast():
    contrast = _contrast()
    observation = _result(
        evidence_kind=EvidenceKind.PREDICTION_DERIVED_ANALYSIS,
        interpretation_fields=("functional:target_activity:sufficient",),
    )
    interpretation = _table(contrast).interpret(
        observation,
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.NON_MEASUREMENT
    assert interpretation.scope is EvidenceScope.PLAN_LIMITATION


def test_exhausted_evidence_state_is_reported_as_contradiction_not_as_a_label():
    contrast = _contrast()
    state = EvidenceState(candidates=frozenset())
    decision = DecisionEngine(DEFAULT_REQUIREMENTS).decide(state, contrast)
    assert decision.status is DecisionStatus.CONTRADICTED
    assert decision.action is DevelopmentAction.REVISE_ATTRIBUTION
    assert "exhausted" in decision.unmet_requirements[0]


def test_measured_insufficient_perturbation_licenses_an_implementation_repair():
    contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    decision = DecisionEngine(DEFAULT_REQUIREMENTS).decide(
        state,
        contrast,
        admitted_scopes={REALISATION_FIELD: EvidenceScope.INTERVENTION_IMPLEMENTATION},
        observed_units={REALISATION_FIELD: 3},
        evidence_ids=("result-1",),
    )
    assert decision.status is DecisionStatus.DECIDED
    assert decision.action is DevelopmentAction.REVISE_INTERVENTION


def test_a_model_prediction_cannot_license_a_development_decision():
    """The admission verdict, not the field spelling, grants a licence (audit F01)."""

    contrast = _contrast()
    predicted = _result(
        evidence_kind=EvidenceKind.MODEL_PREDICTION,
        interpretation_fields=(REALISATION_FIELD,),
    )
    interpretation = _table(contrast).interpret(
        predicted,
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    admission = admit_evidence(interpretation, predicted)
    assert admission.readable and admission.qc_passed
    assert not admission.conditions_matched
    assert not admission.admissible
    assert admission.admitted_fields == ()

    decision = DecisionEngine(DEFAULT_REQUIREMENTS).decide(
        EvidenceState.open(contrast.hypotheses),
        contrast,
        admitted_scopes={},
    )
    assert decision.status is not DecisionStatus.DECIDED


def test_a_condition_unmatched_result_cannot_license_a_decision():
    """A rule whose measurement conditions did not hold cannot grant a licence."""

    contrast = _contrast()
    observation = _result(interpretation_fields=(REALISATION_FIELD,), context_identifier="cell-b")
    interpretation = _table(contrast).interpret(
        observation,
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.CONDITION_UNMATCHED
    admission = admit_evidence(interpretation, observation)
    assert not admission.admissible

    decision = DecisionEngine(DEFAULT_REQUIREMENTS).decide(
        EvidenceState.open(contrast.hypotheses),
        contrast,
        admitted_scopes={field: admission.scope for field in admission.admitted_fields},
        executable_actions=(contrast.plan,),
        remaining_budget=5.0,
    )
    assert decision.status is DecisionStatus.NEEDS_EVIDENCE


def test_resolved_contrast_decides_only_when_its_requirement_is_met():
    contrast = _contrast()
    state = EvidenceState(
        candidates=frozenset({"mode_non_equivalence"}),
        eliminated=frozenset({"incomplete_perturbation"}),
    )
    engine = DecisionEngine(DEFAULT_REQUIREMENTS)
    pending = engine.decide(state, contrast, admitted_scopes={})
    assert pending.status is DecisionStatus.NEEDS_EVIDENCE
    assert f"field:{SUFFICIENT_FUNCTION_FIELD}" in pending.unmet_requirements

    # Sufficient function admitted at the implementation layer cannot change the mode.
    partial = engine.decide(
        state,
        contrast,
        admitted_scopes={SUFFICIENT_FUNCTION_FIELD: EvidenceScope.INTERVENTION_IMPLEMENTATION},
        observed_units={SUFFICIENT_FUNCTION_FIELD: 4},
    )
    assert partial.status is DecisionStatus.NEEDS_EVIDENCE
    assert f"field:{MODE_COMPARATOR_FIELD}" in partial.unmet_requirements

    ready = engine.decide(
        state,
        contrast,
        admitted_scopes={
            SUFFICIENT_FUNCTION_FIELD: EvidenceScope.MECHANISM_CONTRAST,
            MODE_COMPARATOR_FIELD: EvidenceScope.MECHANISM_CONTRAST,
            MODE_DIFFERENCE_FIELD: EvidenceScope.MECHANISM_CONTRAST,
        },
        observed_units={SUFFICIENT_FUNCTION_FIELD: 4, MODE_COMPARATOR_FIELD: 4, MODE_DIFFERENCE_FIELD: 4},
        evidence_ids=("result-2",),
    )
    assert ready.status is DecisionStatus.DECIDED
    assert ready.action is DevelopmentAction.CHANGE_INTERVENTION_MODE


def test_shared_stage_action_allows_an_early_decision_without_buying_resolution():
    contrast = MechanismContrast(
        identifier="shared",
        hypotheses=(
            MechanismHypothesis("a", "Explanation A.", DevelopmentAction.CONTINUE),
            MechanismHypothesis("b", "Explanation B.", DevelopmentAction.CONTINUE),
        ),
        differing_assumptions=("attribution",),
        plan=None,
    )
    requirement = (EvidenceRequirement(DevelopmentAction.CONTINUE, requires_resolved_contrast=False),)
    state = EvidenceState.open(contrast.hypotheses)
    decision = DecisionEngine(requirement).decide(state, contrast)
    assert decision.status is DecisionStatus.DECIDED
    assert decision.action is DevelopmentAction.CONTINUE
    assert "not bought" in decision.rationale


def test_budget_exhaustion_is_not_evidence_and_defers():
    contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    decision = DecisionEngine(DEFAULT_REQUIREMENTS).decide(
        state, contrast, remaining_budget=0.0, executable_actions=()
    )
    assert decision.status is DecisionStatus.DEFERRED
    assert decision.action is DevelopmentAction.DEFER
    assert decision.unmet_requirements == ("no_executable_evidence_path",)


def test_source_clusters_are_recorded_once_per_original_experiment():
    contrast = _contrast()
    interpretation = _table(contrast).interpret(
        _result(),
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    state = EvidenceState.open(contrast.hypotheses)
    first = state.apply(interpretation, _result(source_id="paper-a"), source_cluster="experiment-1")
    second = first.apply(interpretation, _result(source_id="paper-b"), source_cluster="experiment-1")
    third = second.apply(interpretation, _result(source_id="paper-c"), source_cluster="experiment-2")
    assert third.independent_source_clusters == frozenset({"experiment-1", "experiment-2"})


def test_custom_rule_can_require_an_explicit_condition():
    contrast = _contrast()
    rule = OutcomeRule(
        identifier="mode_matched",
        outcome_label="mode_matched_phenotype_absent",
        matched_fields=frozenset({"mechanism:mode_matched:absent"}),
        eliminates=frozenset({"mode_non_equivalence"}),
        required_conditions=frozenset({"degrader_control"}),
    )
    table = InterpretationTable((rule,))
    without = table.interpret(
        _result(interpretation_fields=("mechanism:mode_matched:absent",)),
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert without.outcome_class is OutcomeClass.CONDITION_UNMATCHED
    with_condition = table.interpret(
        _result(
            interpretation_fields=("mechanism:mode_matched:absent",),
            conditions={"degrader_control": "present"},
        ),
        contrast,
        FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        contrast.plan,
    )
    assert with_condition.can_update_mechanism
    assert with_condition.eliminates == frozenset({"mode_non_equivalence"})


def test_context_mismatch_is_reported_as_an_unmatched_condition():
    contrast = _contrast()
    interpretation = _table(contrast).interpret(
        _result(context_identifier="cell-b"),
        contrast,
        FunctionalInterventionProfile(
            mode="drug",
            context_identifier="cell-a",
            functional_states={"target_activity": MeasurementStatus.MEASURED},
        ),
        contrast.plan,
    )
    assert interpretation.outcome_class is OutcomeClass.CONDITION_UNMATCHED
    assert any(item.startswith("context:") for item in interpretation.unmatched_conditions)
