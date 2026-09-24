"""Directed repair, execution context, clarification scope, and decision licensing.

File summary
- Path: tests/test_directed_repair_and_licensing.py
- Purpose: Pin the behaviours introduced when the real-data licensing benchmark exposed them.
- Core points: each test fixes one boundary that a counterexample moved; none of them reports a biological result.
- Interfaces: repair direction, outcome-separation repair, promise scoring, context planning, clarification scope, decision verdicts.
- Depends on: maestro, agent.context, evaluation
"""
from pathlib import Path

from agent.context import TaskInterpreter
from maestro import (
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    FunctionalInterventionProfile,
    MAESTROAgent,
    MeasurementStatus,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    RepairController,
    RepairKind,
    RepairLedger,
)
from evaluation.cases import CaseRepository, ReplayEnvironment
from evaluation.runner import EvaluationRunner, _planned_context
from evaluation.scoring import score_submission

HYPOTHESES = (
    MechanismHypothesis("h_gap", "Insufficient perturbation.", DevelopmentAction.REVISE_INTERVENTION),
    MechanismHypothesis("h_mode", "Mode non-equivalence.", DevelopmentAction.CHANGE_INTERVENTION_MODE),
)

SEPARATING = EvidenceAction(
    identifier="comparator",
    description="A second registered inhibitor of the same target.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.MODE_MATCHED_COMPARATOR,
    prerequisites=("abundance:target",),
    supplies=("functional:mode_comparator",),
    expected_outcomes={"h_gap": "comparator_active", "h_mode": "comparator_inactive"},
)

FLAT = EvidenceAction(
    identifier="a_panel_summary",
    description="A panel-wide summary that cannot separate these two explanations.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.EVIDENCE_REVIEW,
    supplies=("attribution:selectivity",),
    expected_outcomes={"h_gap": "selective", "h_mode": "selective"},
    context_bound=False,
)

SUPPLIER = EvidenceAction(
    identifier="abundance",
    description="Target abundance in this context.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.PROTEIN_ABUNDANCE_MEASUREMENT,
    supplies=("abundance:target",),
    expected_outcomes={"h_gap": "present", "h_mode": "present"},
)

DECOY = EvidenceAction(
    identifier="another_abundance_assay",
    description="A same-kind assay that supplies a different field.",
    cost=0.5,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.PROTEIN_ABUNDANCE_MEASUREMENT,
    supplies=("abundance:unrelated_protein",),
)

MENU = (FLAT, SEPARATING, SUPPLIER, DECOY)
EMPTY_PROFILE = FunctionalInterventionProfile(mode="drug", context_identifier="ctx")
MEASURED_PROFILE = FunctionalInterventionProfile(
    mode="drug",
    context_identifier="ctx",
    measured_fields={"abundance:target": MeasurementStatus.MEASURED},
)

REAGENT = EvidenceAction(
    identifier="imaging_reagent",
    description="A target-abundance assay that itself requires a baseline scan.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.PROTEIN_ABUNDANCE_MEASUREMENT,
    prerequisites=("imaging:baseline",),
    supplies=("abundance:target",),
)

BASELINE_SCAN = EvidenceAction(
    identifier="baseline_scan",
    description="The baseline scan the reagent assay requires.",
    cost=0.5,
    distinguishes=("h_gap", "h_mode"),
    kind=EvidenceActionKind.READOUT_MEASUREMENT,
    supplies=("imaging:baseline",),
)

CYCLE_A = EvidenceAction(
    identifier="cycle_a",
    description="Supplies the field cycle_b requires.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    prerequisites=("cycle:b",),
    supplies=("cycle:a",),
)

CYCLE_B = EvidenceAction(
    identifier="cycle_b",
    description="Supplies the field cycle_a requires.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    prerequisites=("cycle:a",),
    supplies=("cycle:b",),
)


def _contrast(agent: MAESTROAgent, actions=MENU):
    contrast = agent.construct_contrast("c", HYPOTHESES, (), actions)
    assert contrast is not None
    return contrast


def test_constructor_prefers_a_declared_separating_action_over_a_cheaper_flat_one():
    """Selection reads the same declaration the check will demand."""

    agent = MAESTROAgent()
    contrast = _contrast(agent)
    assert contrast.plan is not None
    assert contrast.plan.identifier == "comparator"


def test_repair_is_directed_by_the_named_missing_prerequisite():
    """The repair picks the action that supplies the missing field, not the matching kind.

    ``DECOY`` is the same action kind and costs less, so a kind-matching rule
    would choose it. Only the field it supplies distinguishes the two.
    """

    agent = MAESTROAgent()
    contrast = _contrast(agent)
    check = agent.check_contrast(contrast, EMPTY_PROFILE)
    assert NonDiscriminabilityReason.MISSING_PREREQUISITE in check.reasons

    proposal = agent.repair_contrast(contrast, check, MENU)
    assert proposal.kind is RepairKind.ADD_PREREQUISITE_MEASUREMENT
    assert proposal.replacement_action is not None
    assert proposal.replacement_action.identifier == "abundance"
    assert proposal.promised_fields == ("abundance:target",)


def test_an_outcome_separation_failure_has_a_registered_repair():
    """A checkable failure must have a registered edit, not only a deferral.

    The check can report that a plan declares the same observation under both
    explanations. Before this repair existed, that failure fell through to
    ``DEFER`` even when the catalogue already held a separating readout.
    """

    agent = MAESTROAgent()
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (FLAT,))
    assert contrast is not None and contrast.plan is FLAT
    check = agent.check_contrast(contrast, MEASURED_PROFILE)
    assert NonDiscriminabilityReason.OUTCOME_NOT_SEPARATED in check.reasons

    proposal = agent.repair_contrast(contrast, check, MENU)
    assert proposal.kind is RepairKind.CHANGE_READOUT_OR_TIME
    assert proposal.replacement_action is not None
    assert proposal.replacement_action.identifier == "comparator"


def test_no_registered_separating_action_still_defers():
    """The repair does not invent a separation that the catalogue cannot declare."""

    agent = MAESTROAgent()
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (FLAT,))
    assert contrast is not None
    check = agent.check_contrast(contrast, MEASURED_PROFILE)
    proposal = agent.repair_contrast(contrast, check, (FLAT,))
    assert proposal.kind is RepairKind.DEFER
    assert proposal.replacement_action is None


def test_the_executable_step_supplies_a_blocked_plans_premise():
    """A separating plan whose premise is unmeasured yields the supplying action."""

    agent = MAESTROAgent()
    step = agent.next_executable_action((SEPARATING,), EMPTY_PROFILE, MENU)
    assert step is not None and step.identifier == "abundance"

    step = agent.next_executable_action((SEPARATING,), MEASURED_PROFILE, MENU)
    assert step is not None and step.identifier == "comparator"


def test_a_blocked_plan_chains_through_a_suppliers_own_prerequisite():
    """A supplier that is not immediately runnable expands into its own sub-steps.

    The depth-one substitution could not see this path at all: ``REAGENT``
    supplies the plan's premise but carries a prerequisite of its own, so it
    was invisible as a supplier and the plan reported no executable step.
    """

    agent = MAESTROAgent()
    chain = agent.executable_chain(SEPARATING, EMPTY_PROFILE, (REAGENT, BASELINE_SCAN))
    assert chain is not None
    assert tuple(action.identifier for action in chain) == ("baseline_scan", "imaging_reagent", "comparator")

    step = agent.next_executable_action((SEPARATING,), EMPTY_PROFILE, MENU + (REAGENT, BASELINE_SCAN))
    assert step is not None and step.identifier == "abundance"

    step = agent.next_executable_action((SEPARATING,), EMPTY_PROFILE, (FLAT, SEPARATING, REAGENT, BASELINE_SCAN))
    assert step is not None and step.identifier == "baseline_scan"


def test_a_supplier_cycle_cannot_loop_the_chain():
    """Cyclic supplies declarations are reported as unplannable, not traversed forever."""

    agent = MAESTROAgent()
    needs_a = EvidenceAction(
        identifier="needs_cycle_a",
        description="A plan whose premise sits on a cyclic supplier pair.",
        cost=1.0,
        distinguishes=("h_gap", "h_mode"),
        prerequisites=("cycle:a",),
    )
    assert agent.executable_chain(needs_a, EMPTY_PROFILE, (CYCLE_A, CYCLE_B)) is None


def test_the_chain_respects_its_depth_bound_and_backtracks():
    """A chain deeper than the bound is refused, and a failed supplier is backtracked over."""

    agent = MAESTROAgent()
    assert agent.executable_chain(SEPARATING, EMPTY_PROFILE, (REAGENT, BASELINE_SCAN), max_depth=2) is None
    assert agent.executable_chain(SEPARATING, EMPTY_PROFILE, (REAGENT, BASELINE_SCAN), max_depth=3) is not None

    # The cheaper supplier sorts first, but its own prerequisite has no
    # registered supplier, so the planner must backtrack to the runnable one.
    cheap_blocked = EvidenceAction(
        identifier="cheap_blocked",
        description="Cheapest supplier of the plan's premise, itself unsuppliable.",
        cost=0.1,
        distinguishes=("h_gap", "h_mode"),
        prerequisites=("never:measured",),
        supplies=("abundance:target",),
    )
    chain = agent.executable_chain(SEPARATING, EMPTY_PROFILE, (cheap_blocked, SUPPLIER))
    assert chain is not None
    assert tuple(action.identifier for action in chain) == ("abundance", "comparator")


def test_repeating_an_edit_after_new_evidence_is_not_a_repair_cycle():
    """Cycle detection identifies a repair by evidence state as well as by edit.

    The same edit proposed again *after* a measurement arrived is the next
    step, not a loop; treating it as a loop stalled the sequential case.
    """

    agent = MAESTROAgent()
    controller = RepairController(agent, max_attempts=3)
    ledger = RepairLedger()
    contrast = _contrast(agent)

    first = controller.run(contrast, agent.check_contrast(contrast, EMPTY_PROFILE), MENU, EMPTY_PROFILE, ledger=ledger)
    assert first.records

    second = controller.run(
        contrast, agent.check_contrast(contrast, MEASURED_PROFILE), MENU, MEASURED_PROFILE, ledger=ledger
    )
    assert second.stop_reason != "repair_cycle_detected"
    assert second.check.ready_for_mechanism_update


def test_a_cross_context_review_is_planned_without_the_case_context():
    """A panel review and an orthogonal control declare where they run.

    Planning every action in the case's own context made the store reject a
    valid cross-context record, so the declaration is read instead.
    """

    cases = CaseRepository(
        Path("data/evaluation/cases/real/public"), Path("data/evaluation/cases/real/private")
    ).load()
    case = next(item for item, _ in cases if item.public.action("dependency_selectivity_profile"))
    review = case.public.action("dependency_selectivity_profile").action
    assert _planned_context(review, case) is None

    abundance = case.public.action("target_abundance_rna").action
    assert _planned_context(abundance, case) == case.public.context_identifier


def test_only_a_named_task_field_blocks_planning():
    """A missing measurement is an evidence gap, not missing task information.

    The boundary used to rest on prompt wording, so a model that listed the
    measurements the evidence menu exists to acquire stopped the whole loop.
    """

    class Stub:
        def complete_json(self, messages, **kwargs):
            return (
                {
                    "task_type": "mechanism_diagnosis",
                    "research_question": "Why does the compound not reproduce the genetic phenotype?",
                    "target_or_targets": ["EGFR"],
                    "interventions": ["compound"],
                    "biological_context": "one model",
                    "phenotype_endpoint": "viability",
                    "supplied_evidence": ["a dependency score"],
                    "constraints": [],
                    "missing_information": [
                        "Condition-matched target engagement measurement",
                        "phenotype_endpoint",
                    ],
                    "needs_visual_review": False,
                },
                None,
            )

    intent = TaskInterpreter(Stub()).interpret("anything")
    assert intent.missing_information == ("phenotype_endpoint",)
    assert intent.evidence_gaps == ("Condition-matched target engagement measurement",)
    assert intent.requires_clarification


def test_an_evidence_gap_alone_does_not_require_clarification():
    class Stub:
        def complete_json(self, messages, **kwargs):
            return (
                {
                    "task_type": "mechanism_diagnosis",
                    "research_question": "Question.",
                    "target_or_targets": ["EGFR"],
                    "interventions": ["compound"],
                    "biological_context": "one model",
                    "phenotype_endpoint": "viability",
                    "supplied_evidence": ["a dependency score"],
                    "constraints": [],
                    "missing_information": ["Residual target activity after inhibition"],
                    "needs_visual_review": False,
                },
                None,
            )

    intent = TaskInterpreter(Stub()).interpret("anything")
    assert not intent.requires_clarification
    assert intent.evidence_gaps


def _real_case(identifier_fragment: str):
    cases = CaseRepository(
        Path("data/evaluation/cases/real/public"), Path("data/evaluation/cases/real/private")
    ).load()
    return next(item for item in cases if identifier_fragment in item[0].public.identifier)


def test_deferral_is_correct_only_when_nothing_else_is_licensable():
    """Refusing to act is right when nothing is licensable and wrong when something is."""

    case, outcomes = next(
        item
        for item in CaseRepository(
            Path("data/evaluation/cases/real/public"), Path("data/evaluation/cases/real/private")
        ).load()
        if any(rule.required_outcomes for rule in item[0].scoring.decision_rules)
    )
    environment = ReplayEnvironment(case, outcomes)

    before = score_submission(
        case,
        outcomes,
        decision=DevelopmentAction.DEFER,
        observed=environment.view().observed,
        evidence_ids=(),
        spent=0.0,
        submission_valid=True,
    )
    assert before.verdict.value == "over_deferral"
    assert before.reachable

    empty = score_submission(
        case,
        {},
        decision=DevelopmentAction.DEFER,
        observed={},
        evidence_ids=(),
        spent=0.0,
        submission_valid=True,
    )
    assert empty.verdict.value == "correct"


def test_a_quality_failed_measurement_licenses_nothing():
    """An uninterpretable record cannot license a development action.

    A rule resting on a measurement requires that measurement to have passed
    its declared quality check, so marking the record failed withdraws the
    licence even though the record stays valid and keeps its outcome label.
    """

    from dataclasses import replace as dataclass_replace

    case, outcomes = next(
        item
        for item in CaseRepository(
            Path("data/evaluation/cases/real/public"), Path("data/evaluation/cases/real/private")
        ).load()
        if any(
            rule.required_outcomes and rule.require_biological_quality
            for rule in item[0].scoring.decision_rules
        )
    )
    rule = next(
        item
        for item in case.scoring.decision_rules
        if item.required_outcomes and item.require_biological_quality
    )
    observed = {name: outcomes[name] for name in rule.required_outcomes}
    assert rule.matches(observed)

    failed = {
        name: dataclass_replace(outcome, biological_quality="failed")
        for name, outcome in observed.items()
    }
    assert not rule.matches(failed)


def test_a_terminal_decision_may_cite_public_premise_evidence(tmp_path: Path):
    """A decision licensed by the public premise has no revealed record to cite.

    Requiring one forced every policy to buy something before it could submit
    anything, which is a spending bias rather than an evidence contract.
    """

    case, outcomes = next(
        item
        for item in CaseRepository(
            Path("data/evaluation/cases/real/public"), Path("data/evaluation/cases/real/private")
        ).load()
        if not any(rule.required_outcomes for rule in item[0].scoring.decision_rules)
    )
    public_id = case.public.initial_evidence[0].identifier
    score = score_submission(
        case,
        outcomes,
        decision=case.scoring.decision_rules[0].decision,
        observed={},
        evidence_ids=(public_id,),
        spent=0.0,
        submission_valid=True,
    )
    assert score.cited_evidence_valid
    assert score.verdict.value == "correct"


def test_public_case_files_never_carry_the_archetype_or_licensed_answer():
    """The public package must not contain the evaluator's classification."""

    import json

    banned = {"archetype", "licensed_decisions", "split", "scoring", "decision_rules"}
    for path in sorted(Path("data/evaluation/cases/real/public").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert banned.isdisjoint(payload), path.name
        text = path.read_text(encoding="utf-8")
        assert "critical_actions" not in text, path.name


def test_a_provider_failure_is_recorded_as_one_lost_case_not_a_lost_run(tmp_path: Path):
    """One transport failure must not discard an entire multi-case comparison."""

    from agent.llm import LLMError

    case, outcomes = _real_case("")

    class Failing:
        name = "failing_provider"

        def next_action(self, view):
            raise LLMError("LLM request could not reach the configured endpoint.")

        def decide(self, view):
            raise LLMError("LLM request could not reach the configured endpoint.")

    result = EvaluationRunner(run_id="provider", state_root=tmp_path, mode="decision").run_case(
        Failing(), case, outcomes
    )
    assert result.stop_reason == "provider_error"
    assert result.decision_origin == "provider_error"
    assert not result.submission_valid
