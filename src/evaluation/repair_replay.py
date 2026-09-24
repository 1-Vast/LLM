"""The proposal round: compile what a policy proposes, admit it, and record every refusal.

File summary
- Path: src/evaluation/repair_replay.py
- Purpose: one place where a policy's repair proposals meet the framework's typed admission,
  so the replay runner gains the step without gaining the rules. It also holds the
  evaluator-side view of what the registry makes reachable, which is what decides whether a
  deferral was informed or premature.
- Core points:
  - A proposal is compiled, not trusted: the capability must be registered, must declare the
    premise, must cover the subject, and its declared grant must satisfy the case's typed
    requirement. Every failure is recorded with its name instead of being dropped.
  - An admitted repair is an action on that run's menu only. Its result is still hidden: the
    policy has to spend budget to see it, exactly like a menu action.
  - `registry_extended_case` is evaluator-only. It is how "a decision was reachable through a
    repair" becomes a scoring fact rather than a claim, and it is never handed to a policy.
- Interfaces: `ProposalRecord`, `run_proposal_round`, `compilable_repairs`,
  `registry_extended_case`
- Depends on: evaluation.capabilities, evaluation.cases
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from .capabilities import CapabilityRegistry, CompiledRepair, ProposalRefusal, compile_proposal
from .cases import EvidenceMenuItem, ReplayCase, ReplayEnvironment, RevealRefusal, RevealedEvidence

DEFAULT_PROPOSAL_LIMIT = 6


@dataclass(frozen=True)
class ProposalRecord:
    """One proposal, what it compiled to, and why it did not."""

    case_id: str
    policy: str
    proposal: Mapping[str, object]
    compiled: bool
    admitted: bool
    identifier: str | None = None
    refusal: str | None = None
    detail: str = ""

    def payload(self) -> Mapping[str, object]:
        return {
            "case_id": self.case_id,
            "policy": self.policy,
            "proposal": dict(self.proposal),
            "compiled": self.compiled,
            "admitted": self.admitted,
            "identifier": self.identifier,
            "refusal": self.refusal,
            "detail": self.detail,
        }


def run_proposal_round(
    policy,
    environment: ReplayEnvironment,
    registry: CapabilityRegistry | None,
    *,
    limit: int = DEFAULT_PROPOSAL_LIMIT,
) -> tuple[ProposalRecord, ...]:
    """Ask a policy for repairs, compile them, and admit the ones that pass admission.

    A policy without a ``propose_repairs`` method, or a run without a registry, produces no
    records and no change, which is how every existing package keeps its exact behaviour.
    """

    propose = getattr(policy, "propose_repairs", None)
    if registry is None or not callable(propose):
        return ()
    proposals = tuple(propose(environment.view()))[:limit]
    records: list[ProposalRecord] = []
    for proposal in proposals:
        if not isinstance(proposal, Mapping):
            records.append(
                ProposalRecord(
                    case_id=environment.case.public.identifier,
                    policy=getattr(policy, "name", "unknown"),
                    proposal={"payload_type": type(proposal).__name__},
                    compiled=False,
                    admitted=False,
                    refusal="proposal_not_an_object",
                )
            )
            continue
        try:
            compiled = compile_proposal(environment.case.public, registry, proposal)
        except ProposalRefusal as refusal:
            records.append(
                ProposalRecord(
                    case_id=environment.case.public.identifier,
                    policy=getattr(policy, "name", "unknown"),
                    proposal=dict(proposal),
                    compiled=False,
                    admitted=False,
                    refusal=refusal.code,
                    detail=refusal.detail,
                )
            )
            continue
        try:
            environment.admit(EvidenceMenuItem(action=compiled.action, lab_cost=compiled.lab_cost))
        except RevealRefusal as refusal:
            records.append(
                ProposalRecord(
                    case_id=environment.case.public.identifier,
                    policy=getattr(policy, "name", "unknown"),
                    proposal=dict(proposal),
                    compiled=True,
                    admitted=False,
                    identifier=compiled.identifier,
                    refusal=refusal.code,
                    detail=str(refusal),
                )
            )
            continue
        records.append(
            ProposalRecord(
                case_id=environment.case.public.identifier,
                policy=getattr(policy, "name", "unknown"),
                proposal=dict(proposal),
                compiled=True,
                admitted=True,
                identifier=compiled.identifier,
            )
        )
    return tuple(records)


def compilable_repairs(case: ReplayCase, registry: CapabilityRegistry | None) -> tuple[CompiledRepair, ...]:
    """Every repair the registry could supply for this case, by the same compiler policies use.

    The subjects come from the case's own premise declarations, so this enumerates what any
    policy could have proposed, not what one policy happened to propose.
    """

    if registry is None:
        return ()
    compiled: dict[str, CompiledRepair] = {}
    for premise in case.public.missing_premises():
        requirement = (case.public.premise_registry or {}).get(premise)
        entity = getattr(requirement, "entity", None)
        if not entity or "@" not in entity:
            continue
        gene, compound = entity.split("@", 1)
        for offer in registry.offers_for(premise):
            try:
                candidate = compile_proposal(
                    case.public,
                    registry,
                    {
                        "operator": "register_supplier",
                        "capability": offer.identifier,
                        "supplies": premise,
                        "compound": compound,
                        "entity": gene,
                    },
                )
            except ProposalRefusal:
                continue
            compiled.setdefault(candidate.identifier, candidate)
    return tuple(compiled.values())


def registry_extended_case(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    registry: CapabilityRegistry | None,
) -> tuple[ReplayCase, Mapping[str, RevealedEvidence]]:
    """The case as the evaluator sees it: the menu plus every compilable repair.

    Used only for reachability, so that "the policy deferred while a repair could have
    licensed a decision" is a measured statement. A repair with no registered hidden result
    is left out: nothing could have been learned from it.
    """

    repairs = compilable_repairs(case, registry)
    if not repairs:
        return case, outcomes
    items = list(case.public.actions)
    extended_outcomes = dict(outcomes)
    for repair in repairs:
        outcome = case.scoring.repair_outcomes.get(repair.identifier)
        if outcome is None:
            continue
        items.append(EvidenceMenuItem(action=repair.action, lab_cost=repair.lab_cost))
        extended_outcomes[repair.identifier] = outcome
    if len(items) == len(case.public.actions):
        return case, outcomes
    public = replace(case.public, actions=tuple(items))
    return replace(case, public=public), extended_outcomes
