"""Decision scoring: licensed decisions, error taxonomy, waste, and reachability.

File summary
- Path: src/evaluation/scoring.py
- Purpose: Score a submitted development decision against evidence-licensing rules rather than a single expected answer.
- Core points:
  - A case may license several decisions; every licensed decision counts as correct.
  - Deferral is scored against what the policy could still have licensed within its budget, so over-deferral is an error.
  - Cost is reported as three separate quantities: the cheapest legal certificate in the case, the redundancy inside the policy's own acquisition, and the hindsight regret against the cheapest route.
  - Laboratory cost (wells and turnaround days) and the always-hidden final-test verdict are reported beside the licensing verdict and never change it.
- Interfaces: `DecisionVerdict`, `FinalTestVerdict`, `score_submission`, `final_test_verdict`, `licensed_decisions`, `reachable_decisions`, `minimum_certificate`
- Depends on: evaluation.cases, evaluation.lab_cost, maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from maestro.models import DevelopmentAction

from .cases import DecisionRule, ReplayCase, RevealedEvidence
from .feasibility import (
    enumerate_executed_sequences,
    licensing_certificates,
    sequence_cost,
)
from .lab_cost import SequenceLabCost


class FinalTestVerdict(str, Enum):
    """How a terminal decision fares against results no policy could ever read.

    The verdict sits beside the licensing verdict and never replaces it: licensing asks
    whether the acquired evidence supports the decision, the final test asks whether data
    held back from every strategy agree with it. ``partition_absent`` is the honest value
    for a case package that carries no held-back results.
    """

    PARTITION_ABSENT = "partition_absent"
    NO_DECISION = "no_decision"
    UNTESTED = "untested"
    INADMISSIBLE = "inadmissible"
    CONSISTENT = "consistent"
    CONTRADICTED = "contradicted"
    MIXED = "mixed"

# Deferral is never scored as an advance or an abandonment: it is a refusal to act,
# and section 9.4 requires it to be counted separately so that refusing everything
# cannot win.
_ADVANCING = frozenset({DevelopmentAction.CONTINUE, DevelopmentAction.PRESERVE_MULTI_TARGET_ACTIVITY})
_ABANDONING = frozenset({DevelopmentAction.STOP, DevelopmentAction.REMOVE_MULTI_TARGET_ACTIVITY})


class DecisionVerdict(str, Enum):
    """How a submitted decision relates to what the acquired evidence licenses."""

    CORRECT = "correct"
    OVER_DEFERRAL = "over_deferral"
    WRONG_ADVANCE = "wrong_advance"
    WRONG_ABANDON = "wrong_abandon"
    WRONG_DIRECTION = "wrong_direction"
    NO_DECISION = "no_decision"
    INVALID_SUBMISSION = "invalid_submission"


@dataclass(frozen=True)
class DecisionScore:
    """The scored outcome of one policy submission on one case."""

    verdict: DecisionVerdict
    licensed: tuple[str, ...]
    reachable: tuple[str, ...]
    decisive_evidence_acquired: bool
    required_cost: float
    waste_cost: float
    cited_evidence_valid: bool
    reason: str
    redundant_cost: float = 0.0
    hindsight_regret: float = 0.0
    certificate: tuple[str, ...] = ()
    lab_cost_spent: SequenceLabCost | None = None
    final_test: str = FinalTestVerdict.PARTITION_ABSENT.value
    final_test_records: tuple[str, ...] = ()

    @property
    def correct(self) -> bool:
        return self.verdict is DecisionVerdict.CORRECT


def licensed_decisions(
    case: ReplayCase, observed: Mapping[str, RevealedEvidence]
) -> tuple[DevelopmentAction, ...]:
    """Return every decision the currently revealed evidence licenses."""

    return tuple(
        dict.fromkeys(rule.decision for rule in case.scoring.decision_rules if rule.matches(observed))
    )


def minimum_certificate(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    decision: DevelopmentAction | None = None,
    restricted_to: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], float] | None:
    """Cheapest legally executable acquisition whose records license a decision.

    This replaces the earlier prerequisite-closure arithmetic. The closure
    could skip a prerequisite that no registered action supplies and still
    report a cost, so the scorer could call a decision reachable that the
    replay environment refuses to execute. Here the search runs over the same
    transition semantics execution uses, so the two cannot disagree.

    A prerequisite's own cost is inside the certificate: the sequence is legal,
    which means every premise was actually bought.
    """

    def matches(observed: Mapping[str, RevealedEvidence]) -> bool:
        for rule in case.scoring.decision_rules:
            if decision is not None and rule.decision is not decision:
                continue
            if rule.matches(observed):
                return True
        return False

    certificates = licensing_certificates(
        case.public, outcomes, matches, restricted_to=restricted_to
    )
    return certificates[0] if certificates else None


def reachable_decisions(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    budget: float,
) -> tuple[DevelopmentAction, ...]:
    """Return the decisions a policy could still have licensed inside the case budget.

    Evaluator-side knowledge used only for scoring: it asks whether evidence
    that licenses a decision was *executably* purchasable in this hidden world.
    A decision whose licensing evidence is unavailable, unaffordable, or blocked
    by a premise no action supplies is not reachable, so declining to reach it
    is not an error.
    """

    reachable: list[DevelopmentAction] = []
    for rule in case.scoring.decision_rules:
        if not rule.required_outcomes:
            reachable.append(rule.decision)
            continue
        for sequence in enumerate_executed_sequences(case.public, outcomes):
            if sequence_cost(case.public, sequence) > budget + 1e-9:
                continue
            observed = {name: outcomes[name] for name in sequence if name in outcomes}
            if rule.matches(observed):
                reachable.append(rule.decision)
                break
    return tuple(dict.fromkeys(reachable))


def score_submission(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    decision: DevelopmentAction | None,
    observed: Mapping[str, RevealedEvidence],
    evidence_ids: Sequence[str],
    spent: float,
    submission_valid: bool,
) -> DecisionScore:
    """Score one submission against the licensing rules, not against one expected answer."""

    licensed = licensed_decisions(case, observed)
    reachable = reachable_decisions(case, outcomes, budget=case.public.budget)
    decisive = _decisive_evidence_acquired(case, observed)

    # The cheapest legal certificate available anywhere in this case, and the
    # cheapest one contained in what this policy actually acquired. Three costs
    # are reported separately because they answer different questions:
    #   required_cost     - what a supported decision costs at best in this case
    #   redundant_cost    - what this policy bought beyond its own certificate
    #   hindsight_regret  - what a cheaper legal route would have saved
    # A valid alternative route is therefore not scored as waste; only
    # acquisition outside the policy's own licensing certificate is.
    cheapest = minimum_certificate(case, outcomes)
    required_cost = cheapest[1] if cheapest is not None else 0.0
    own = minimum_certificate(
        case, outcomes, decision=decision, restricted_to=tuple(observed)
    )
    if own is None:
        own = minimum_certificate(case, outcomes, restricted_to=tuple(observed))
    certificate = own[0] if own is not None else ()
    certificate_cost = own[1] if own is not None else 0.0
    redundant = max(0.0, spent - certificate_cost) if own is not None else spent
    regret = max(0.0, spent - required_cost) if own is not None else 0.0

    public_ids = {item.identifier for item in case.public.initial_evidence}
    cited_valid = set(evidence_ids).issubset(set(observed) | public_ids)

    verdict, reason = _verdict(decision, licensed, reachable, submission_valid)
    tested, tested_records = final_test_verdict(case, decision if submission_valid else None)
    return DecisionScore(
        verdict=verdict,
        licensed=tuple(item.value for item in licensed),
        reachable=tuple(item.value for item in reachable),
        decisive_evidence_acquired=decisive,
        required_cost=required_cost,
        waste_cost=redundant,
        redundant_cost=redundant,
        hindsight_regret=regret,
        certificate=certificate,
        cited_evidence_valid=cited_valid,
        reason=reason,
        lab_cost_spent=case.public.sequence_lab_cost(tuple(observed)),
        final_test=tested.value,
        final_test_records=tested_records,
    )


def final_test_verdict(
    case: ReplayCase, decision: DevelopmentAction | None
) -> tuple[FinalTestVerdict, tuple[str, ...]]:
    """Check a terminal decision against the always-hidden partition, if the case has one.

    Only admissible records count, and a record that bears on neither the submitted
    decision's confirmation nor its contradiction leaves it untested rather than passed.
    """

    records = case.scoring.final_test
    if not records:
        return FinalTestVerdict.PARTITION_ABSENT, ()
    if decision is None:
        return FinalTestVerdict.NO_DECISION, ()
    bearing = [record for record in records if decision in record.confirms or decision in record.contradicts]
    if not bearing:
        return FinalTestVerdict.UNTESTED, ()
    admissible = [record for record in bearing if record.admissible]
    if not admissible:
        return FinalTestVerdict.INADMISSIBLE, tuple(record.identifier for record in bearing)
    identifiers = tuple(record.identifier for record in admissible)
    confirmed = any(decision in record.confirms for record in admissible)
    contradicted = any(decision in record.contradicts for record in admissible)
    if confirmed and contradicted:
        return FinalTestVerdict.MIXED, identifiers
    if contradicted:
        return FinalTestVerdict.CONTRADICTED, identifiers
    return FinalTestVerdict.CONSISTENT, identifiers


def _verdict(
    decision: DevelopmentAction | None,
    licensed: Sequence[DevelopmentAction],
    reachable: Sequence[DevelopmentAction],
    submission_valid: bool,
) -> tuple[DecisionVerdict, str]:
    if not submission_valid:
        return DecisionVerdict.INVALID_SUBMISSION, "the submission did not satisfy the terminal decision contract"
    if decision is None:
        return DecisionVerdict.NO_DECISION, "no terminal decision was submitted"
    if decision in licensed:
        return DecisionVerdict.CORRECT, "the acquired evidence licenses the submitted decision"
    if decision is DevelopmentAction.DEFER:
        decisive = [item for item in reachable if item is not DevelopmentAction.DEFER]
        if decisive:
            return (
                DecisionVerdict.OVER_DEFERRAL,
                "deferral was submitted while "
                + ", ".join(sorted(item.value for item in decisive))
                + " remained licensable within the case budget",
            )
        # Nothing else was licensable within the budget, so refusing to act is
        # the correct response rather than a failure to find an answer.
        return DecisionVerdict.CORRECT, "no decision other than deferral was licensable within the case budget"
    if decision in _ADVANCING:
        return DecisionVerdict.WRONG_ADVANCE, "the programme was advanced without licensing evidence"
    if decision in _ABANDONING:
        return DecisionVerdict.WRONG_ABANDON, "the programme was abandoned without licensing evidence"
    return DecisionVerdict.WRONG_DIRECTION, "a revision was submitted that the acquired evidence does not license"


def _decisive_evidence_acquired(case: ReplayCase, observed: Mapping[str, RevealedEvidence]) -> bool:
    """Whether the policy acquired the evidence some licensing rule actually needs."""

    rules: Sequence[DecisionRule] = case.scoring.decision_rules
    informative = [rule for rule in rules if rule.required_outcomes]
    if not informative:
        return True
    return any(rule.matches(observed) for rule in informative)
