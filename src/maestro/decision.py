"""The development-decision layer of a mechanism contrast.

File summary
- Path: src/maestro/decision.py
- Purpose: Map an evidence state and contrast to one bounded development action.
- Core points:
  - A decision is emitted only when the compatible explanation set supports it.
  - Exhausting the budget is never evidence; deferral must not be the cheapest policy.
  - No registered explanation surviving routes to CONTRADICTED, not a new mechanism label.
- Interfaces: `DecisionEngine`, `decide`, `EvidenceRequirement`, `DevelopmentDecision`, `DEFAULT_REQUIREMENTS`
- Depends on: maestro.models, maestro.outcome
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .models import (
    DecisionStatus,
    DevelopmentAction,
    EvidenceAction,
    EvidenceScope,
    MechanismContrast,
    MechanismHypothesis,
)
from .outcome import (
    MODE_COMPARATOR_FIELD,
    MODE_DIFFERENCE_FIELD,
    REALISATION_FIELD,
    SUFFICIENT_FUNCTION_FIELD,
    EvidenceState,
    scope_rank,
)


@dataclass(frozen=True)
class EvidenceRequirement:
    """The minimum measured support a named development action must have.

    ``required_scope`` states which layer the licensing fields must have been
    admitted under.  A field carried by a model prediction or by a
    condition-unmatched record is never admitted at any layer, so it cannot
    satisfy a requirement by name.
    """

    action: DevelopmentAction
    satisfied_by: frozenset[str] = frozenset()
    requires_resolved_contrast: bool = True
    minimum_units: int = 1
    required_scope: EvidenceScope = EvidenceScope.MECHANISM_CONTRAST
    note: str = ""
    field_scopes: Mapping[str, EvidenceScope] = field(default_factory=dict)

    def _admitted(self, field: str, admitted_scopes: Mapping[str, EvidenceScope]) -> bool:
        scope = admitted_scopes.get(field)
        required = self.field_scopes.get(field, self.required_scope)
        return scope is not None and scope_rank(scope) >= scope_rank(required)

    def unmet(
        self,
        admitted_scopes: Mapping[str, EvidenceScope],
        state: EvidenceState,
        observed_units: Mapping[str, int],
    ) -> tuple[str, ...]:
        unmet = [
            f"field:{field}"
            for field in sorted(self.satisfied_by)
            if not self._admitted(field, admitted_scopes)
        ]
        if self.requires_resolved_contrast and not state.resolved:
            unmet.append("contrast:not_resolved")
        for field in sorted(self.satisfied_by):
            if self._admitted(field, admitted_scopes) and observed_units.get(field, 0) < self.minimum_units:
                unmet.append(f"units:{field}<{self.minimum_units}")
        return tuple(unmet)


@dataclass(frozen=True)
class DevelopmentDecision:
    """A stage action with the evidence that licenses it, or an explicit non-decision."""

    status: DecisionStatus
    action: DevelopmentAction | None
    evidence_ids: tuple[str, ...]
    unmet_requirements: tuple[str, ...]
    rationale: str
    boundary: str

    @property
    def is_terminal(self) -> bool:
        return self.status in (DecisionStatus.DECIDED, DecisionStatus.DEFERRED, DecisionStatus.CONTRADICTED)


DEFAULT_REQUIREMENTS: tuple[EvidenceRequirement, ...] = (
    EvidenceRequirement(
        DevelopmentAction.REVISE_INTERVENTION,
        satisfied_by=frozenset({REALISATION_FIELD}),
        requires_resolved_contrast=False,
        required_scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
        note=(
            "Insufficient implementation licenses an implementation repair without waiting for the "
            "mechanism contrast to resolve; it never licenses stopping the programme."
        ),
    ),
    EvidenceRequirement(
        DevelopmentAction.CHANGE_INTERVENTION_MODE,
        satisfied_by=frozenset({SUFFICIENT_FUNCTION_FIELD, MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD}),
        required_scope=EvidenceScope.MECHANISM_CONTRAST,
        field_scopes={SUFFICIENT_FUNCTION_FIELD: EvidenceScope.INTERVENTION_IMPLEMENTATION},
        note=(
            "Reconsidering the intervention mode requires sufficient perturbation, an observed "
            "phenotype, and a measured mode-matched comparator. A sufficient-function measurement "
            "alone proposes a mode comparison; it does not license changing the mode."
        ),
    ),
)
# Deferral is deliberately not a licensable requirement: an action that is always licensed would
# make over-deferral the cheapest policy, which section 9.4 scores as a failure mode.


class DecisionEngine:
    """Map an evidence state and a contrast to one bounded development action."""

    def __init__(self, requirements: Sequence[EvidenceRequirement] = DEFAULT_REQUIREMENTS):
        self._requirements = tuple(requirements)
        self._by_action = {item.action: item for item in self._requirements}

    @property
    def requirements(self) -> tuple[EvidenceRequirement, ...]:
        return self._requirements

    def decide(
        self,
        state: EvidenceState,
        contrast: MechanismContrast,
        *,
        admitted_scopes: Mapping[str, EvidenceScope] | None = None,
        observed_units: Mapping[str, int] | None = None,
        evidence_ids: Sequence[str] = (),
        remaining_budget: float | None = None,
        executable_actions: Sequence[EvidenceAction] = (),
    ) -> DevelopmentDecision:
        units = observed_units or {}
        admitted = admitted_scopes or {}
        if state.exhausted:
            return DevelopmentDecision(
                status=DecisionStatus.CONTRADICTED,
                action=DevelopmentAction.REVISE_ATTRIBUTION,
                evidence_ids=tuple(evidence_ids),
                unmet_requirements=("explanation_set:exhausted",),
                rationale="No registered explanation remains compatible with the qualified results.",
                boundary=(
                    "The explanation set must be revised from this version onward; existing predictions are not rewritten "
                    "and no new mechanism label is inferred from the contradiction itself."
                ),
            )

        # A licence has to be granted by an admitted measured field; a name alone is not a licence.
        licensed = tuple(
            requirement
            for requirement in self._requirements
            if requirement.action is not DevelopmentAction.DEFER
            and requirement.satisfied_by
            and not requirement.unmet(admitted, state, units)
        )
        if len(licensed) == 1:
            return DevelopmentDecision(
                status=DecisionStatus.DECIDED,
                action=licensed[0].action,
                evidence_ids=tuple(evidence_ids),
                unmet_requirements=(),
                rationale=(
                    f"A qualified measurement satisfies the registered minimum evidence for "
                    f"'{licensed[0].action.value}': {licensed[0].note or 'no note registered.'}"
                ),
                boundary="The licence comes from the measured field only; it does not settle which mechanism is correct.",
            )

        surviving = tuple(
            hypothesis for hypothesis in contrast.hypotheses if hypothesis.identifier in state.candidates
        )
        shared = _shared_action(surviving)
        if shared is not None and len(surviving) > 1:
            requirement = self._by_action.get(shared)
            unmet = (
                requirement.unmet(admitted, state, units)
                if requirement is not None
                else ("requirement:unregistered",)
            )
            if requirement is not None and not unmet:
                return DevelopmentDecision(
                    status=DecisionStatus.DECIDED,
                    action=shared,
                    evidence_ids=tuple(evidence_ids),
                    unmet_requirements=(),
                    rationale=(
                        "Every explanation still compatible with the evidence supports the same stage action, "
                        f"so finer discrimination was not bought: {shared.value}."
                    ),
                    boundary="The competing explanations remain open; only the stage action is shared.",
                )

        if state.resolved:
            hypothesis = next(
                item for item in contrast.hypotheses if item.identifier in state.candidates
            )
            proposed = hypothesis.proposed_action
            if proposed is None:
                return DevelopmentDecision(
                    status=DecisionStatus.NEEDS_EVIDENCE,
                    action=None,
                    evidence_ids=tuple(evidence_ids),
                    unmet_requirements=("hypothesis:no_proposed_action",),
                    rationale=f"Explanation '{hypothesis.identifier}' survived but declares no development action.",
                    boundary="A hypothesis without a registered action cannot produce a stage decision.",
                )
            requirement = self._by_action.get(proposed)
            if requirement is None:
                return DevelopmentDecision(
                    status=DecisionStatus.NEEDS_EVIDENCE,
                    action=None,
                    evidence_ids=tuple(evidence_ids),
                    unmet_requirements=("requirement:unregistered",),
                    rationale=f"No minimum-evidence requirement is registered for '{proposed.value}'.",
                    boundary="Unregistered actions are not emitted as decisions.",
                )
            unmet = requirement.unmet(admitted, state, units)
            if unmet:
                return DevelopmentDecision(
                    status=DecisionStatus.NEEDS_EVIDENCE,
                    action=None,
                    evidence_ids=tuple(evidence_ids),
                    unmet_requirements=unmet,
                    rationale=f"Explanation '{hypothesis.identifier}' survived but its action lacks the required support.",
                    boundary="The surviving explanation is not yet sufficient for the action it implies.",
                )
            return DevelopmentDecision(
                status=DecisionStatus.DECIDED,
                action=proposed,
                evidence_ids=tuple(evidence_ids),
                unmet_requirements=(),
                rationale=(
                    f"Only '{hypothesis.identifier}' remains compatible and its action "
                    f"'{proposed.value}' meets the registered minimum evidence."
                ),
                boundary="The decision is scoped to this context, condition, and endpoint; it is not a permanent target label.",
            )

        if executable_actions and (remaining_budget is None or remaining_budget > 0):
            unmet = ["contrast:not_resolved"]
            if len(licensed) > 1:
                unmet.append(
                    "multiple_licensed_actions:"
                    + ",".join(sorted(item.action.value for item in licensed))
                )
            return DevelopmentDecision(
                status=DecisionStatus.NEEDS_EVIDENCE,
                action=None,
                evidence_ids=tuple(evidence_ids),
                unmet_requirements=tuple(unmet),
                rationale="More than one explanation is still compatible and executable evidence remains.",
                boundary="Continue with the selected evidence action; no stage decision is licensed yet.",
            )
        return DevelopmentDecision(
            status=DecisionStatus.DEFERRED,
            action=DevelopmentAction.DEFER,
            evidence_ids=tuple(evidence_ids),
            unmet_requirements=("no_executable_evidence_path",),
            rationale="No executable evidence path can separate the surviving explanations within the remaining budget.",
            boundary="Exhausting the budget is not evidence; deferred cases must state what would restore a decision.",
        )


def _shared_action(hypotheses: Sequence[MechanismHypothesis]) -> DevelopmentAction | None:
    actions = {item.proposed_action for item in hypotheses if item.proposed_action is not None}
    if len(actions) != 1 or not hypotheses:
        return None
    if any(item.proposed_action is None for item in hypotheses):
        return None
    return next(iter(actions))
