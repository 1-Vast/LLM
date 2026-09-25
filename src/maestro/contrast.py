"""Deterministic control layer that constructs, checks, and repairs a decision-relevant mechanism contrast.

File summary
- Path: src/maestro/contrast.py
- Purpose: Bounds LLM proposals by the registered action catalogue and explicit evidence fields.
- Core points:
  - `check_contrast` validates execution, premise, and decision separation without inferring biology.
  - `repair_contrast` returns a catalog-bounded repair, or an explicit deferral when none exists.
  - `observation_scope` limits an observation's update target when its interpretation premise failed.
  - Supplier-chain search is pruned by the menu's topology (`maestro.topology`) without changing its result.
- Interfaces: `MAESTROAgent`, `decide`, `construct_contrast`, `check_contrast`, `repair_contrast`, `next_executable_action`, `executable_chain`, `observation_scope`
- Depends on: maestro.models, maestro.selection, maestro.topology, virtual_cell.interface (typing only)
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from .models import (
    CompositionRule,
    ContrastCheck,
    DecisionStatus,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MechanismContrast,
    MechanismDecision,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    RepairKind,
    RepairProposal,
)
from .composition import PlanComposer, rank_plans
from .selection import BudgetedEvidencePlan, BudgetedEvidenceSelector
from .topology import ActionTopology

if TYPE_CHECKING:
    from virtual_cell.interface import StatePrediction


class MAESTROAgent:
    """Construct, audit, and repair a decision-relevant mechanism contrast."""

    # A subclass that overrides __init__ without calling it must still answer
    # "is a composer registered?" rather than raising on attribute access.
    _composer: PlanComposer | None = None

    def __init__(self, *, composition_rule: CompositionRule | None = None):
        """Create a controller, optionally able to compose gated evidence plans.

        Composition is a switch rather than a default so that the ablation
        "repair with and without the composed action space" is a property of the
        same controller, not a comparison between two code paths that differ in
        more than the operator under test.
        """

        self._composer = PlanComposer(composition_rule) if composition_rule is not None else None

    @property
    def composer(self) -> PlanComposer | None:
        return self._composer

    def decide(
        self,
        hypotheses: Sequence[MechanismHypothesis],
        actions: Sequence[EvidenceAction],
        prediction: "StatePrediction | None" = None,
    ) -> MechanismDecision:
        """Preserve the small action-selection interface for callers without a profile."""

        unresolved = {hypothesis.identifier for hypothesis in hypotheses}
        if len(unresolved) < 2:
            return MechanismDecision(
                status=DecisionStatus.DEFERRED,
                selected_action=None,
                rationale="At least two competing mechanism hypotheses are required.",
            )

        action = self.select_evidence_action(unresolved, actions)
        if action is None:
            return MechanismDecision(
                status=DecisionStatus.DEFERRED,
                selected_action=None,
                rationale="No available evidence action distinguishes the competing hypotheses.",
            )

        model_note = ""
        if prediction is not None and not prediction.applicable:
            model_note = " The virtual-cell model is outside its applicability range."
        return MechanismDecision(
            status=DecisionStatus.NEEDS_EVIDENCE,
            selected_action=action,
            rationale=(
                "Additional measured evidence is required before a mechanism claim. "
                f"Selected '{action.identifier}' as the lowest-cost discriminating action."
                f"{model_note}"
            ),
        )

    @staticmethod
    def select_evidence_action(
        unresolved: set[str] | frozenset[str], actions: Sequence[EvidenceAction]
    ) -> EvidenceAction | None:
        """Choose the cheapest executable action that covers the complete contrast."""

        candidates = [
            action
            for action in actions
            if action.cost >= 0 and unresolved.issubset(action.distinguishes)
        ]
        return min(candidates, key=lambda action: (action.cost, action.identifier), default=None)

    @staticmethod
    def select_budgeted_evidence(
        unresolved: frozenset[str],
        actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        budget: float,
        *,
        action_priorities: Mapping[str, float] | None = None,
    ) -> BudgetedEvidencePlan:
        """Return a small executable action set while keeping blocked actions visible."""

        return BudgetedEvidenceSelector().select(
            unresolved, actions, profile, budget, action_priorities=action_priorities
        )

    def construct_contrast(
        self,
        identifier: str,
        hypotheses: Sequence[MechanismHypothesis],
        differing_assumptions: Sequence[str],
        actions: Sequence[EvidenceAction],
        *,
        outcome_categories: Sequence[str] = (),
        interpretation_boundaries: Sequence[str] = (),
    ) -> MechanismContrast | None:
        """Build one pairwise contrast; other explanations remain outside this pair."""

        unique = tuple({hypothesis.identifier: hypothesis for hypothesis in hypotheses}.values())
        if len(unique) < 2:
            return None
        pair = (unique[0], unique[1])
        identifiers = frozenset(hypothesis.identifier for hypothesis in pair)
        # Selection and checking read the same declarations. Choosing a plan on
        # label coverage alone, when the check then demands a declared
        # observation difference, guarantees a first plan that fails for a
        # reason already visible at selection time. A separating action is
        # therefore preferred; the cheapest covering action remains the
        # fallback when nothing declares a difference, so the check can still
        # report that the contrast is not separable.
        action = self._separating_action_for(identifiers, actions) or self.select_evidence_action(
            identifiers, actions
        )
        return MechanismContrast(
            identifier=identifier,
            hypotheses=pair,
            differing_assumptions=tuple(differing_assumptions),
            plan=action,
            outcome_categories=tuple(outcome_categories),
            interpretation_boundaries=tuple(interpretation_boundaries),
        )

    def check_contrast(
        self,
        contrast: MechanismContrast,
        profile: FunctionalInterventionProfile,
        prediction: "StatePrediction | None" = None,
    ) -> ContrastCheck:
        """Check execution, premise, and decision separation without inferring biology."""

        actions = contrast.actions()
        reasons: list[NonDiscriminabilityReason] = []
        missing: list[str] = []
        executable = bool(actions) and all(candidate.cost >= 0 for candidate in actions)
        if not executable:
            reasons.append(NonDiscriminabilityReason.INVALID_ACTION)

        if not actions:
            prerequisites_satisfied = False
            discriminable = False
            outcome_separated = False
        else:
            # An interpretation gate is a premise in the only sense that matters
            # here: without it the measurement runs, passes its own quality
            # control, and moves no belief. Leaving it out of this list let a
            # gated readout pass the check as though it were interpretable, which
            # is the failure the gate field was added to make expressible. The
            # named field is the same one the typed premise admission compares, so
            # the repair that follows is directed at a field rather than a class.
            missing = [name for candidate in actions for name in profile.unmeasured(candidate.required_premises)]
            if any(
                candidate.kind is EvidenceActionKind.MODE_MATCHED_COMPARATOR for candidate in actions
            ) and not profile.mode:
                reasons.append(NonDiscriminabilityReason.UNMATCHED_INTERVENTION_MODE)
            if missing:
                reasons.append(NonDiscriminabilityReason.MISSING_PREREQUISITE)
                if any(name.startswith("functional:") for name in missing):
                    reasons.append(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT)
            prerequisites_satisfied = not missing and (
                NonDiscriminabilityReason.UNMATCHED_INTERVENTION_MODE not in reasons
            )
            covered = frozenset().union(*(candidate.distinguishes for candidate in actions))
            discriminable = contrast.identifiers().issubset(covered)
            if not discriminable:
                reasons.append(NonDiscriminabilityReason.NO_DISCRIMINATING_ACTION)
            if any(candidate.requires_virtual_prediction for candidate in actions) and (
                prediction is None or not prediction.applicable
            ):
                reasons.append(NonDiscriminabilityReason.MODEL_UNSUPPORTED)
            outcome_separated, outcome_reason = _outcome_separation(contrast, actions, prediction)
            if outcome_reason is not None:
                reasons.append(outcome_reason)

        requested_actions = {
            hypothesis.proposed_action
            for hypothesis in contrast.hypotheses
            if hypothesis.proposed_action is not None
        }
        decision_separating = len(requested_actions) == 2
        if not decision_separating:
            reasons.append(NonDiscriminabilityReason.DECISION_NOT_SEPARATED)

        return ContrastCheck(
            executable=executable,
            prerequisites_satisfied=prerequisites_satisfied,
            discriminable=discriminable,
            decision_separating=decision_separating,
            reasons=tuple(dict.fromkeys(reasons)),
            missing_prerequisites=tuple(missing),
            outcome_separated=outcome_separated,
        )

    def next_executable_action(
        self,
        candidates: Sequence[EvidenceAction | None],
        profile: FunctionalInterventionProfile,
        available_actions: Sequence[EvidenceAction],
        *,
        max_chain_depth: int = 4,
    ) -> EvidenceAction | None:
        """Return the action to execute now for the first candidate plan that can run.

        A repaired plan is not always executable yet: the edit that makes a
        contrast separable can itself introduce an interpretation prerequisite.
        Readiness for a *mechanism update* and executability of the *next step*
        are different questions, and conflating them makes the loop propose an
        assay whose premise is not yet measured. When a candidate is blocked,
        the step becomes the first action of a bounded backward chain over the
        registered ``supplies``/``prerequisites`` declarations: the supplier of
        a missing field may itself carry prerequisites, and those are resolved
        the same way, one level at a time. This is the task-and-motion-planning
        move of expanding a high-level step into the feasible sub-steps its
        preconditions require, instead of declaring no path whenever the only
        supplier is not immediately runnable.
        """

        # One topological analysis serves every candidate: they share the menu and profile.
        topology = ActionTopology.build(available_actions, profile)
        for candidate in candidates:
            if candidate is None:
                continue
            chain = self.executable_chain(
                candidate, profile, available_actions, max_depth=max_chain_depth, topology=topology
            )
            if chain:
                return chain[0]
        return None

    def executable_chain(
        self,
        action: EvidenceAction,
        profile: FunctionalInterventionProfile,
        available_actions: Sequence[EvidenceAction],
        *,
        max_depth: int = 4,
        topology: ActionTopology | None = None,
    ) -> tuple[EvidenceAction, ...] | None:
        """Plan a bounded supplier chain that makes ``action`` runnable.

        The chain is ordered execution-first: element 0 is the step that can
        run now, and the last element is ``action`` itself. Suppliers are
        tried cheapest-first with backtracking, and a supplier already on the
        chain is never re-entered, so a cyclic ``supplies`` declaration cannot
        loop the planner. ``None`` means no chain within the depth bound, which
        is reported as unexecutable rather than silently truncated.

        A supplier is skipped when the menu's topology shows that even an
        unrestricted chain from it is longer than the remaining depth. That
        bound can only be optimistic for the search, so the result is exactly
        the one the unpruned search returns; only hopeless branches are cut.
        ``topology`` must describe the same menu and profile when supplied.
        """

        if max_depth < 1:
            return None
        actions = tuple(available_actions)
        return self._chain_for(
            action,
            profile,
            actions,
            max_depth,
            frozenset({action.identifier}),
            topology if topology is not None else ActionTopology.build(actions, profile),
        )

    def _chain_for(
        self,
        action: EvidenceAction,
        profile: FunctionalInterventionProfile,
        available_actions: tuple[EvidenceAction, ...],
        depth: int,
        visited: frozenset[str],
        topology: ActionTopology,
    ) -> tuple[EvidenceAction, ...] | None:
        # The chain exists to make a step runnable, and an unmeasured
        # interpretation gate is the same obstacle a prerequisite is: without it
        # the step runs and decides nothing. Both are resolved by a registered
        # supplier, so both belong in the same backward chain.
        missing = profile.unmeasured(action.required_premises)
        if not missing:
            return (action,)
        if depth <= 1:
            return None
        outstanding = frozenset(missing)
        suppliers = sorted(
            (
                candidate
                for candidate in available_actions
                if candidate.cost >= 0
                and candidate.identifier not in visited
                and frozenset(candidate.supplies) & outstanding
                and topology.within(candidate.identifier, depth - 1)
            ),
            key=lambda candidate: (candidate.cost, candidate.identifier),
        )
        for supplier in suppliers:
            subchain = self._chain_for(
                supplier,
                profile,
                available_actions,
                depth - 1,
                visited | {supplier.identifier},
                topology,
            )
            if subchain is not None:
                return subchain + (action,)
        return None

    def repair_contrast(
        self,
        contrast: MechanismContrast,
        check: ContrastCheck,
        available_actions: Sequence[EvidenceAction],
    ) -> RepairProposal:
        """Return a catalog-bounded repair, or an explicit deferral when none exists.

        Repair is directed by the *named* failure first: when the check reports
        specific missing prerequisites and the catalogue declares which fields
        each action supplies, the repair selects the registered capability that
        covers those exact fields at least cost. Only when no action declares a
        covering capability does it fall back to the action-kind table below,
        which matches a failure class rather than a named prerequisite.
        """

        reasons = check.reasons
        gated = self._gated_plan_repair(contrast, check, available_actions)
        if gated is not None:
            return gated
        directed = self._directed_prerequisite_repair(check, available_actions)
        if directed is not None:
            return directed
        if NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in reasons:
            action = self._lowest_cost_of_kind(
                available_actions, EvidenceActionKind.FUNCTIONAL_MEASUREMENT
            )
            return self._proposal_or_defer(
                action,
                RepairKind.ADD_FUNCTIONAL_MEASUREMENT,
                ("plan.prerequisites", "intervention.functional_states"),
                reasons,
                "A failed functional measurement updates intervention implementation, not the target mechanism.",
            )

        if NonDiscriminabilityReason.MISSING_PREREQUISITE in reasons:
            action = self._lowest_cost_of_kind(
                available_actions, EvidenceActionKind.PROTEIN_ABUNDANCE_MEASUREMENT
            )
            return self._proposal_or_defer(
                action,
                RepairKind.ADD_PREREQUISITE_MEASUREMENT,
                ("plan.prerequisites",),
                reasons,
                "An unmet prerequisite limits interpretation until it is measured in the relevant condition.",
            )

        if NonDiscriminabilityReason.NO_DISCRIMINATING_ACTION in reasons:
            action = self.select_evidence_action(contrast.identifiers(), available_actions)
            return self._proposal_or_defer(
                action,
                RepairKind.CHANGE_READOUT_OR_TIME,
                ("plan.readout", "plan.time_hours"),
                reasons,
                "The replacement must be a registered readout that distinguishes this contrast; it is not a new biological claim.",
            )

        if NonDiscriminabilityReason.UNMATCHED_INTERVENTION_MODE in reasons:
            action = self._lowest_cost_of_kind(
                available_actions, EvidenceActionKind.MODE_MATCHED_COMPARATOR
            )
            return self._proposal_or_defer(
                action,
                RepairKind.MATCH_INTERVENTION_MODE,
                ("intervention.mode", "plan.time_hours"),
                reasons,
                "Matching a target name alone does not establish functional equivalence between intervention modes.",
            )

        if NonDiscriminabilityReason.MODEL_UNSUPPORTED in reasons:
            action = self.select_evidence_action(
                contrast.identifiers(),
                [candidate for candidate in available_actions if not candidate.requires_virtual_prediction],
            )
            return self._proposal_or_defer(
                action,
                RepairKind.REMOVE_MODEL_DEPENDENCE,
                ("plan.requires_virtual_prediction",),
                reasons,
                "The virtual-cell prediction is removed from planning; no model output is entered as measured evidence.",
            )

        if _OUTCOME_FAILURES & set(reasons):
            action = self._separating_action(contrast, available_actions)
            return self._proposal_or_defer(
                action,
                RepairKind.CHANGE_READOUT_OR_TIME,
                ("plan.action_identifier", "plan.readout"),
                reasons,
                (
                    "The replacement is a registered action that declares a different expected "
                    "observation under each hypothesis. The declaration is the case author's "
                    "claim about what the readout can separate; only a qualified real result "
                    "can confirm it."
                ),
                promised_fields=("outcome_separation",),
            )

        return RepairProposal(
            kind=RepairKind.DEFER,
            replacement_action=None,
            modified_fields=(),
            triggered_by=reasons,
            interpretation_boundary="No registered repair can make the current action difference testable.",
        )

    def _gated_plan_repair(
        self,
        contrast: MechanismContrast,
        check: ContrastCheck,
        available_actions: Sequence[EvidenceAction],
    ) -> RepairProposal | None:
        """Keep the contrast's own readout and buy the premise that makes it interpretable.

        The single-action repair below *replaces* the readout with a premise
        measurement: it makes the contrast interpretable by changing the
        question. This branch does the opposite — it holds the question fixed
        and composes a plan whose first stage is the missing premise and whose
        second stage is the readout the contrast already wanted. It fires only
        when the check named the missing fields and a registered gate supplies
        them, so the repair stays directed by the failure rather than by the
        availability of an interesting-looking pair.
        """

        if self._composer is None:
            return None
        missing = tuple(dict.fromkeys(check.missing_prerequisites))
        if not missing:
            return None
        named = {action.identifier: missing for action in contrast.actions()}
        plans = self._composer.compose(contrast, available_actions, named)
        if not plans:
            return None
        ranked = rank_plans(plans, contrast)
        intended = contrast.plan.identifier if contrast.plan is not None else None
        preferred = tuple(item for item in ranked if item.plan.readout.identifier == intended) or ranked
        plan = preferred[0].plan
        promised = tuple(sorted(set(plan.gate.supplies) & set(missing)))
        if not promised:
            return None
        functional = any(name.startswith("functional:") for name in promised)
        kind = RepairKind.ADD_FUNCTIONAL_MEASUREMENT if functional else RepairKind.ADD_PREREQUISITE_MEASUREMENT
        return RepairProposal(
            kind=kind,
            replacement_action=None,
            modified_fields=("plan.action_identifier", "plan.prerequisites", "plan.composed_from"),
            triggered_by=check.reasons,
            interpretation_boundary=(
                f"'{plan.gate.identifier}' measures "
                + ", ".join(promised)
                + f" so that '{plan.readout.identifier}' becomes interpretable; the readout is "
                "bought only if the gate returns a passing outcome, and a failing gate routes to "
                f"'{plan.fallback.value}' without buying it."
            ),
            promised_fields=promised,
            composed_plan=plan,
        )

    @staticmethod
    def observation_scope(check: ContrastCheck) -> EvidenceScope:
        """Limit an observation's update target when its interpretation premise failed.

        The raw result can still be retained by an evidence adapter.  This method
        only prevents it from being used as a mechanism-level update prematurely.
        """

        if NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in check.reasons:
            return EvidenceScope.INTERVENTION_IMPLEMENTATION
        if not check.executable or not check.prerequisites_satisfied:
            return EvidenceScope.MEASUREMENT_FEASIBILITY
        if not check.discriminable or not check.decision_separating or not check.outcome_separated:
            return EvidenceScope.PLAN_LIMITATION
        return EvidenceScope.MECHANISM_CONTRAST

    @staticmethod
    def _separating_action_for(
        identifiers: frozenset[str], available_actions: Sequence[EvidenceAction]
    ) -> EvidenceAction | None:
        """Cheapest registered action declaring a different outcome for each identifier."""

        candidates = [
            action
            for action in available_actions
            if action.cost >= 0
            and identifiers.issubset(action.expected_outcomes)
            and len({action.expected_outcomes[name] for name in identifiers}) == 2
        ]
        return min(candidates, key=lambda action: (action.cost, action.identifier), default=None)

    def _separating_action(
        self, contrast: MechanismContrast, available_actions: Sequence[EvidenceAction]
    ) -> EvidenceAction | None:
        """Return the cheapest registered action whose declared outcomes separate the pair.

        The check can report that a plan's observation-to-decision mapping is
        undeclared, incomplete, or identical under both hypotheses (audit F03).
        Without this repair those failures have no registered edit and the loop
        can only defer, which would make a *checkable* failure permanently
        unrepairable even when the catalogue already contains a readout that
        declares a difference.
        """

        return self._separating_action_for(contrast.identifiers(), available_actions)

    @staticmethod
    def _directed_prerequisite_repair(
        check: ContrastCheck, available_actions: Sequence[EvidenceAction]
    ) -> RepairProposal | None:
        """Select the cheapest registered action that supplies the named missing fields.

        Returns ``None`` when nothing in the catalogue declares a covering
        capability, so the caller keeps its existing failure-class behaviour.
        A declared capability is still only a claim: the proposal records the
        promised fields so a later real result can falsify it.
        """

        missing = tuple(dict.fromkeys(check.missing_prerequisites))
        if not missing:
            return None
        outstanding = frozenset(missing)
        candidates = [
            (action, frozenset(action.supplies) & outstanding)
            for action in available_actions
            if action.cost >= 0 and action.supplies
        ]
        covering = [(action, covered) for action, covered in candidates if covered]
        if not covering:
            return None
        action, covered = min(
            covering,
            key=lambda item: (-len(item[1]), item[0].cost, item[0].identifier),
        )
        functional = any(name.startswith("functional:") for name in covered)
        kind = (
            RepairKind.ADD_FUNCTIONAL_MEASUREMENT
            if functional
            else RepairKind.ADD_PREREQUISITE_MEASUREMENT
        )
        remaining = tuple(sorted(outstanding - covered))
        boundary = (
            "The replacement supplies "
            + ", ".join(sorted(covered))
            + "; it constrains that prerequisite only, not the target mechanism."
        )
        if remaining:
            boundary += " Still unmeasured after this repair: " + ", ".join(remaining) + "."
        return RepairProposal(
            kind=kind,
            replacement_action=action,
            modified_fields=("plan.action_identifier", "plan.prerequisites"),
            triggered_by=check.reasons,
            interpretation_boundary=boundary,
            promised_fields=tuple(sorted(covered)),
        )

    @staticmethod
    def _lowest_cost_of_kind(
        actions: Sequence[EvidenceAction], kind: EvidenceActionKind
    ) -> EvidenceAction | None:
        return min(
            (action for action in actions if action.kind is kind and action.cost >= 0),
            key=lambda action: (action.cost, action.identifier),
            default=None,
        )

    @staticmethod
    def _proposal_or_defer(
        action: EvidenceAction | None,
        kind: RepairKind,
        modified_fields: tuple[str, ...],
        reasons: tuple[NonDiscriminabilityReason, ...],
        boundary: str,
        *,
        promised_fields: tuple[str, ...] = (),
    ) -> RepairProposal:
        if action is None:
            return RepairProposal(
                kind=RepairKind.DEFER,
                replacement_action=None,
                modified_fields=(),
                triggered_by=reasons,
                interpretation_boundary="No registered capability can perform the required repair. " + boundary,
            )
        return RepairProposal(
            kind=kind,
            replacement_action=action,
            modified_fields=modified_fields,
            triggered_by=reasons,
            interpretation_boundary=boundary,
            promised_fields=promised_fields or tuple(action.supplies),
        )


_OUTCOME_FAILURES = frozenset(
    {
        NonDiscriminabilityReason.OUTCOME_MAPPING_UNDECLARED,
        NonDiscriminabilityReason.OUTCOME_MAPPING_INCOMPLETE,
        NonDiscriminabilityReason.OUTCOME_NOT_SEPARATED,
    }
)


def _outcome_separation(
    contrast: MechanismContrast,
    actions: tuple[EvidenceAction, ...],
    prediction: "StatePrediction | None",
) -> tuple[bool, NonDiscriminabilityReason | None]:
    """Check the declared observation-to-decision mapping, beyond label coverage.

    An action separates the pair only when it declares a different expected
    observable outcome for each hypothesis; identical declared outcomes reject
    distinguishability, and an undeclared mapping leaves the premise unstated.
    Labels from different actions are never pooled into a joint outcome: that
    would mistake two incomplete assays for one comparable observation. A
    future joint specification must model its shared observation coordinate
    explicitly. A model-dependent action counts only with a
    coverage-claiming interval for its readout: a descriptive spread cannot
    certify discrimination (F03).
    """

    pair = {hypothesis.identifier for hypothesis in contrast.hypotheses}
    uncalibrated = False
    identical = False
    single = [candidate for candidate in actions if pair.issubset(candidate.expected_outcomes)]
    for candidate in single:
        if len({candidate.expected_outcomes[identifier] for identifier in pair}) < 2:
            identical = True
            continue
        if candidate.requires_virtual_prediction and not _calibrated_model_support(candidate, prediction):
            uncalibrated = True
            continue
        return True, None
    has_partial_mapping = any(
        bool(set(candidate.expected_outcomes) & pair)
        for candidate in actions
    )
    if uncalibrated:
        return False, NonDiscriminabilityReason.MODEL_DISCRIMINATION_UNCALIBRATED
    if identical:
        return False, NonDiscriminabilityReason.OUTCOME_NOT_SEPARATED
    if has_partial_mapping:
        return False, NonDiscriminabilityReason.OUTCOME_MAPPING_INCOMPLETE
    return False, NonDiscriminabilityReason.OUTCOME_MAPPING_UNDECLARED


def _calibrated_model_support(action: EvidenceAction, prediction: "StatePrediction | None") -> bool:
    """A model-dependent separation needs a coverage-claiming interval for its readout."""

    if prediction is None or not prediction.applicable:
        return False
    readout = action.prediction_readout or action.readout
    if not readout:
        return False
    band = prediction.interval_for(readout)
    return band is not None and band.claims_coverage
