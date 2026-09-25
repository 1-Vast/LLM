"""Close a registered evidence menu under gated, shared-control composition.

File summary
- Path: src/maestro/composition.py
- Purpose: give the repair step something the menu does not contain — a *plan* — without letting it invent capability.
- Core points:
  - A composed plan is a new registered object, not a sequence of the parts: only a new object can carry the shared-control saving that makes a plan affordable inside a binding budget.
  - Composition requires an interpretation gate. The gate measures the premise without which the readout is uninterpretable, and the readout is bought only after the gate passes.
  - The planner reads only public declarations, ranks plans by worst-declared-case residual plus weighted cost, and reports every plan it rejected with the reason.
  - Nothing here claims a probability. A declared comparison is not a measured one, and a composed plan is confirmed only by a real qualified result from both stages.
- Interfaces: `PlanComposer`, `PlanEvaluation`, `rank_plans`, `composition_is_legal`, `unmet_prerequisites`
- Depends on: maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .models import (
    CompositionRule,
    EvidenceAction,
    FunctionalInterventionProfile,
    GatedEvidencePlan,
    MechanismContrast,
)


@dataclass(frozen=True)
class PlanEvaluation:
    """One composed plan with the declared quantities that placed it.

    ``worst_case_residual`` is the number of hypotheses that would still be
    compatible under the readout's least favourable declared outcome. It is a
    worst-declared-case count, not an expected value: the declarations carry no
    probabilities, and inventing them here is exactly the failure the outcome
    layer exists to prevent.

    ``gate_detection_power`` is the gate's *declared* chance of returning a
    qualified, interpretable result. It is the only declared quantity that
    distinguishes two gates which answer the same question at different prices,
    and when it is undeclared the ordering falls back to cost rather than
    guessing.
    """

    plan: GatedEvidencePlan
    worst_case_residual: int
    objective: float
    gate_outcomes: tuple[str, ...]
    readout_outcomes: tuple[str, ...]
    gate_detection_power: float | None = None


def composition_is_legal(plan: GatedEvidencePlan) -> tuple[str, ...]:
    """Every reason this composition is not admissible, named individually.

    A composition is admissible only when the gate is the thing that makes the
    readout interpretable. A pair where the readout's premise is already
    measured, or where the gate supplies nothing the readout needs, is a
    substitution or a discount and is refused by name rather than admitted as a
    plan.
    """

    problems: list[str] = []
    if plan.gate.identifier == plan.readout.identifier:
        problems.append("gate_and_readout_are_the_same_action")
    authorization = plan.authorization()
    discharged = set(plan.gate.supplies)
    if not authorization.premise:
        problems.append("plan_declares_no_premise_to_repair")
    elif authorization.premise not in discharged:
        # An authorization the gate cannot grant is the failure this record
        # exists to make visible: the plan would be composed on a coincidence.
        problems.append("gate_does_not_grant_the_authorized_premise")
    if not discharged:
        problems.append("gate_supplies_nothing")
    if plan.outstanding_prerequisites():
        problems.append(
            "readout_prerequisite_not_discharged_by_gate:" + ",".join(plan.outstanding_prerequisites())
        )
    if not plan.readout.expected_outcomes:
        problems.append("readout_declares_no_expected_outcomes")
    if plan.readout.cost < 0 or plan.gate.cost < 0:
        problems.append("negative_component_cost")
    return tuple(problems)


def unmet_prerequisites(
    actions: Sequence[EvidenceAction], profile: FunctionalInterventionProfile
) -> dict[str, tuple[str, ...]]:
    """Which declared prerequisites each action still lacks, by the profile alone.

    This is the same question :meth:`ContrastCheck` answers, asked here so the
    caller can pass either source. The repair path passes the check's own named
    failures, because a repair directed at anything else is not directed.
    """

    return {
        action.identifier: profile.unmeasured(action.prerequisites)
        for action in actions
    }


class PlanComposer:
    """Compose registered actions into gated plans a menu-only policy cannot reach.

    The composer is a capability of the controller, not a solver: it enumerates
    a bounded, declared closure and hands the result to the same check the menu
    path uses. It never edits an action, never supplies a field it was not
    declared to supply, and never composes a plan whose readout could be bought
    without its gate.
    """

    def __init__(self, rule: CompositionRule):
        if rule.max_components != 2:
            raise ValueError("Only two-component compositions are registered.")
        self._rule = rule

    @property
    def rule(self) -> CompositionRule:
        return self._rule

    def compose(
        self,
        contrast: MechanismContrast,
        actions: Sequence[EvidenceAction],
        missing: Mapping[str, Iterable[str]],
        *,
        identifiers: frozenset[str] | None = None,
    ) -> tuple[GatedEvidencePlan, ...]:
        """Every admissible gated plan over the catalogue for this contrast.

        ``missing`` names, per action identifier, the prerequisites that action
        still lacks. ``identifiers`` restricts composition to the hypotheses
        still open, so a repair cannot reintroduce an explanation the evidence
        already removed.
        """

        wanted = identifiers if identifiers is not None else contrast.identifiers()
        plans: list[GatedEvidencePlan] = []
        for readout in actions:
            if readout.cost < 0 or not readout.expected_outcomes:
                continue
            if not wanted.issubset(readout.distinguishes):
                continue
            gate_field = readout.interpretation_gate
            if gate_field is None:
                # Composition exists to restore interpretability. A readout with
                # no declared gate has nothing for a plan to restore, and an
                # unmet prerequisite remains the existing single-action repair.
                continue
            outstanding = tuple(dict.fromkeys((gate_field,) + tuple(missing.get(readout.identifier, ()))))
            for gate in actions:
                if gate.identifier == readout.identifier or gate.cost < 0:
                    continue
                if tuple(missing.get(gate.identifier, ())):
                    # The gate must be runnable now; a plan whose first step is
                    # blocked is not a plan, it is an aspiration. Chaining over
                    # the gate's own suppliers is the executable-chain step.
                    continue
                if not set(gate.supplies) & set(outstanding):
                    continue
                plan = GatedEvidencePlan(
                    identifier=f"plan[{gate.identifier}|{readout.identifier}]",
                    gate=gate,
                    readout=readout,
                    rule=self._rule,
                    note=(
                        f"{gate.identifier} measures the interpretation premise; "
                        f"{readout.identifier} is bought only if it passes."
                    ),
                )
                if composition_is_legal(plan):
                    continue
                plans.append(plan)
        return tuple(sorted(plans, key=lambda item: (item.cost, item.identifier)))


def rank_plans(
    plans: Sequence[GatedEvidencePlan],
    contrast: MechanismContrast,
    *,
    cost_weight: float = 0.25,
) -> tuple[PlanEvaluation, ...]:
    """Order composed plans by declared worst case plus weighted cost.

    The ordering is the same robust criterion the evidence planner already uses,
    so a composed plan competes with a menu plan on one scale instead of being
    promoted by a separate rule written for it. Two plans that resolve the same
    residual are separated by the gate's declared detection power before price,
    because an assay that answers the question one time in two is not cheaper
    than one that answers it, it is a different purchase.
    """

    pair = tuple(hypothesis.identifier for hypothesis in contrast.hypotheses)
    order = {identifier: index for index, identifier in enumerate(pair)}
    evaluations: list[PlanEvaluation] = []
    for plan in plans:
        declared = plan.readout.expected_outcomes
        if not set(pair).issubset(declared):
            continue
        outcomes = tuple(dict.fromkeys(declared[name] for name in pair))
        surviving = 1
        for outcome in outcomes:
            count = sum(1 for name in pair if declared[name] == outcome)
            if count == 1:
                # One declared outcome would leave exactly one hypothesis; a
                # plan is scored by the worst branch, so the branch that
                # separates cannot be the one that sets the score.
                continue
            surviving = max(surviving, count)
        evaluations.append(
            PlanEvaluation(
                plan=plan,
                worst_case_residual=surviving,
                objective=surviving + cost_weight * plan.cost,
                gate_outcomes=tuple(sorted(set(plan.gate.expected_outcomes.values()))),
                readout_outcomes=tuple(sorted(set(outcomes))),
                gate_detection_power=plan.gate.detection_power,
            )
        )
    return tuple(
        sorted(
            evaluations,
            key=lambda item: (
                item.worst_case_residual,
                -(item.gate_detection_power if item.gate_detection_power is not None else 0.0),
                item.objective,
                tuple(order.get(name, len(order)) for name in item.plan.readout.distinguishes),
                item.plan.identifier,
            ),
        )
    )

