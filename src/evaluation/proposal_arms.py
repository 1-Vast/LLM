"""Arms that propose a repair from the capability registry, and the controls that price it.

File summary
- Path: src/evaluation/proposal_arms.py
- Purpose: give the replay path policies that can do what selection cannot: name the premise
  a plan is missing and propose a registered capability to supply it. The rule arm is the
  framework's directed repair extended to the registry; the controls price what the proposal
  step is worth against the catalogue's content, against chance, and against removal.
- Core points:
  - Every arm proposes in the same operator language and is compiled by the same typed
    admission, so a difference between arms is which capability was proposed and when, never
    who was allowed to propose.
  - The rule arm is directed by the declaration: it prefers a missing premise whose declared
    template separates the hypotheses, because that is the premise whose measurement can
    change the decision. A gate premise is proposed only to unlock a readout that is already
    on the menu.
  - `RegistryExpandedSelectionPolicy` admits every compilable capability in advance and then
    selects once. If it matches the rule arm, the credit belongs to the catalogue rather than
    to the proposal step, and the record must say so.
  - A policy sees the registry as declarations and coverage counts. It never sees a value,
    and a compiled action's outcome model comes from the case, not from the proposal.
- Interfaces: `ProposalPolicy`, `RegistryRepairRulePolicy`, `RegistryExpandedSelectionPolicy`,
  `RegistryRandomProposalPolicy`, `LLMRegistryRepairPolicy`, `REPAIR_PROPOSAL_PROMPT`
- Depends on: evaluation.baselines, evaluation.cases
"""
from __future__ import annotations

import json
from random import Random
from typing import Any, Mapping, Protocol, Sequence

from .baselines import ExpertWorkflowPolicy, JSONCompleter, OutcomeAwareSelectionPolicy
from .cases import ReplayView

REPAIR_PROPOSAL_PROMPT = (
    "You are the repair operator of a scientific decision agent. You are given one case: two "
    "competing explanations of a discordance, the evidence already in hand, the measurements "
    "the menu can buy, the premises the menu cannot supply, and a registry of measurement "
    "capabilities with their declared types and coverage.\n\n"
    "The framework's rule, which you must respect: a decision that names a cause is licensed "
    "only when every explanation still compatible with the observations would take the same "
    "decision. A premise the menu cannot supply is what stops the case from deciding.\n\n"
    "Propose exactly one repair, as one JSON object and nothing else:\n"
    '  {"operator": "register_supplier", "capability": "<registry identifier>", '
    '"supplies": "<premise field>", "compound": "<compound>", "entity": "<gene symbol>", '
    '"rationale": "<one sentence>"}\n\n'
    "The capability must be one the registry lists, it must declare the premise you name, and "
    "its declared quantity, context and units must satisfy that premise's requirement. You do "
    "not choose what the result would mean: the case declares that."
)


class ProposalPolicy(Protocol):
    """A replay policy that can also propose repairs before it acquires evidence."""

    name: str

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]: ...


def _subject(view: ReplayView, premise: str) -> tuple[str, str] | None:
    """The gene and compound an engagement-style premise is declared to be about.

    The premise registry states the subject as ``GENE@compound``; that declaration is public,
    so a policy reads the subject from the case rather than guessing which compound a premise
    concerns.
    """

    requirement = (view.case.premise_registry or {}).get(premise)
    entity = getattr(requirement, "entity", None)
    if not entity or "@" not in entity:
        return None
    gene, compound = entity.split("@", 1)
    return gene, compound


def _separating(view: ReplayView, premise: str) -> bool:
    template = (view.case.repair_outcome_templates or {}).get(premise) or {}
    return len(set(template.values())) > 1


def _gated_menu_premises(view: ReplayView) -> set[str]:
    """Premises that make a registered menu action interpretable rather than legal."""

    return {
        item.action.interpretation_gate
        for item in view.case.actions
        if item.available and item.action.interpretation_gate is not None
    }


def _offers_for(view: ReplayView, premise: str) -> list[Mapping[str, object]]:
    offers = [entry for entry in view.capabilities if entry.get("supplies") == premise]
    return sorted(offers, key=lambda entry: (float(entry.get("cost", 0.0)), str(entry.get("identifier"))))


def _admissible_offers(view: ReplayView, premise: str) -> list[Mapping[str, object]]:
    """Offers whose *declaration* already matches what the premise requires.

    The comparison is the one the framework will make, on public fields: an estimate offered
    for a premise that requires a direct measurement, a different quantity, a different
    context or different units cannot discharge it, and a directed agent can see that before
    proposing. Offers that survive are proposed in price order; if the filter empties the
    list, the cheapest offer is proposed anyway so the refusal is recorded by name rather than
    the agent quietly proposing nothing.
    """

    requirement = (view.case.premise_registry or {}).get(premise)
    offers = _offers_for(view, premise)
    if requirement is None or not requirement.is_typed:
        return offers
    kept: list[Mapping[str, object]] = []
    for offer in offers:
        quantity = str(offer.get("quantity", ""))
        if requirement.quantity.value not in ("unspecified", quantity):
            continue
        if requirement.require_direct_measurement and bool(offer.get("is_estimate")):
            continue
        if requirement.context_identifier and offer.get("context_identifier") != requirement.context_identifier:
            continue
        if requirement.units and offer.get("units") not in (None, requirement.units):
            continue
        kept.append(offer)
    return kept or offers[:1]


class RegistryRepairRulePolicy(ExpertWorkflowPolicy):
    """Directed repair over the registry: name the missing premise, propose a capability.

    One proposal round per case. The premise is chosen by what its measurement could do, not
    by what is cheapest to buy: a premise whose declared template separates the explanations
    comes first, a premise that only unlocks a gated menu readout second.
    """

    name = "registry_repair_rule"

    def __init__(self) -> None:
        self._proposed: set[str] = set()

    def next_action(self, view: ReplayView) -> str | None:
        """Buy the premise the repair named, before spending the budget on anything else.

        Directed repair that proposes a premise and then lets a fixed acquisition order spend
        the budget elsewhere has not repaired anything. An admitted repair whose declared
        outcomes separate the explanations is therefore taken first; everything after that is
        the inherited order, so the arm differs from the expert baseline in the repair step
        alone.
        """

        pair = {item["identifier"] for item in view.case.hypotheses[:2]}
        admitted = [
            item
            for item in view.available_actions()
            if item.action.identifier.startswith("repair__")
            and pair.issubset(item.action.expected_outcomes)
            and len({item.action.expected_outcomes[name] for name in pair}) == 2
        ]
        if admitted:
            return min(admitted, key=lambda item: (item.action.cost, item.action.identifier)).action.identifier
        return super().next_action(view)

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        missing = list(view.case.missing_premises())
        gates = _gated_menu_premises(view)
        ordered = sorted(
            missing,
            key=lambda premise: (
                0 if _separating(view, premise) else (1 if premise in gates else 2),
                premise,
            ),
        )
        proposals: list[Mapping[str, object]] = []
        for premise in ordered:
            subject = _subject(view, premise)
            if subject is None:
                continue
            gene, compound = subject
            for offer in _admissible_offers(view, premise)[:2]:
                proposals.append(
                    {
                        "operator": "register_supplier",
                        "capability": offer["identifier"],
                        "supplies": premise,
                        "compound": compound,
                        "entity": gene,
                        "rationale": (
                            f"The plan cannot read its evidence without '{premise}', and this capability "
                            "declares that premise for this subject in this context."
                        ),
                    }
                )
        return tuple(proposals)


class RegistryExpandedSelectionPolicy(OutcomeAwareSelectionPolicy):
    """Control: admit every compilable capability first, then select once.

    This is the strongest honest alternative to proposing: it has the whole catalogue in the
    menu from the start and never checks a plan or edits it. A tie with the rule arm means
    the registry's content, not the proposal step, is what carries the difference.
    """

    name = "registry_expanded_selection"

    def __init__(self) -> None:
        self._proposed: set[str] = set()

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        proposals: list[Mapping[str, object]] = []
        for premise in view.case.missing_premises():
            subject = _subject(view, premise)
            if subject is None:
                continue
            gene, compound = subject
            for offer in _offers_for(view, premise):
                proposals.append(
                    {
                        "operator": "register_supplier",
                        "capability": offer["identifier"],
                        "supplies": premise,
                        "compound": compound,
                        "entity": gene,
                        "rationale": "Catalogue expansion control: every compilable capability is admitted.",
                    }
                )
        return tuple(proposals)


class RegistryRandomProposalPolicy(ExpertWorkflowPolicy):
    """Control: a seeded random proposal, so typed admission is what filters it.

    It draws a capability, a premise and a subject independently, which is exactly the
    behaviour a registry with no direction would produce. Its refusals are the measurement:
    a proposal that names the wrong quantity, context or compound is refused by name.
    """

    name = "registry_repair_random"

    def __init__(self, *, seed: int = 20260914, attempts: int = 1) -> None:
        self._seed = seed
        self._attempts = attempts
        self._proposed: set[str] = set()

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed or not view.capabilities:
            return ()
        self._proposed.add(view.case.identifier)
        random = Random(f"{self._seed}:{view.case.identifier}")
        premises = list(view.case.premise_registry or {}) or list(view.case.missing_premises())
        subjects: list[tuple[str, str]] = []
        for premise in view.case.premise_registry or {}:
            subject = _subject(view, premise)
            if subject is not None:
                subjects.append(subject)
        if not premises or not subjects:
            return ()
        proposals: list[Mapping[str, object]] = []
        for _ in range(self._attempts):
            offer = random.choice(sorted(view.capabilities, key=lambda entry: str(entry.get("identifier"))))
            premise = random.choice(sorted(premises))
            gene, compound = random.choice(sorted(subjects))
            proposals.append(
                {
                    "operator": "register_supplier",
                    "capability": offer["identifier"],
                    "supplies": premise,
                    "compound": compound,
                    "entity": gene,
                    "rationale": "Random control: the registry is sampled without direction.",
                }
            )
        return tuple(proposals)


class LLMRegistryRepairPolicy(ExpertWorkflowPolicy):
    """The configured model proposes one repair per case in the framework's operator language.

    The model chooses the capability, the premise and the subject. It never supplies an
    outcome model, a price or a reliability that scoring reads: those come from the case and
    the registry, so the measurement is the model's judgement and not its arithmetic.
    """

    name = "registry_repair_llm"

    def __init__(self, client: JSONCompleter, *, max_tokens: int = 1200) -> None:
        self._client = client
        self._max_tokens = max_tokens
        self._proposed: set[str] = set()
        self.transcripts: list[Mapping[str, object]] = []

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        statement = self._statement(view)
        try:
            payload, response = self._client.complete_json(
                [
                    {"role": "system", "content": REPAIR_PROPOSAL_PROMPT},
                    {"role": "user", "content": json.dumps(statement, ensure_ascii=False, sort_keys=True)},
                ],
                max_tokens=self._max_tokens,
            )
        except Exception as error:  # a provider failure is data, not a crash
            self.transcripts.append(
                {"case": view.case.identifier, "error": f"{type(error).__name__}: {str(error)[:200]}"}
            )
            return ()
        self.transcripts.append(
            {
                "case": view.case.identifier,
                "proposal": payload,
                "model": getattr(response, "model", ""),
                "usage": dict(getattr(response, "usage", {}) or {}),
                "finish_reason": getattr(response, "finish_reason", None),
            }
        )
        return (payload,) if isinstance(payload, dict) else ()

    def _statement(self, view: ReplayView) -> Mapping[str, Any]:
        return {
            "case": view.case.identifier,
            "context_identifier": view.case.context_identifier,
            "hypotheses": list(view.case.hypotheses),
            "initial_evidence": [
                {"identifier": item.identifier, "statement": item.statement, "source_id": item.source_id}
                for item in view.case.initial_evidence
            ],
            "menu": list(view.public_contract()),
            "missing_premises": list(view.case.missing_premises()),
            "premise_requirements": {
                name: {
                    "quantity": requirement.quantity.value,
                    "entity": requirement.entity,
                    "units": requirement.units,
                    "context_identifier": requirement.context_identifier,
                    "requires_direct_measurement": requirement.require_direct_measurement,
                }
                for name, requirement in (view.case.premise_registry or {}).items()
            },
            "declared_outcome_templates": {
                name: dict(template) for name, template in (view.case.repair_outcome_templates or {}).items()
            },
            "capability_registry": list(view.capabilities),
            "remaining_budget": view.remaining_budget,
            "case_limitations": list(view.case.limitations),
        }
