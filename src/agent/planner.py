"""LLM-assisted proposal of a constrained mechanism contrast for validation.

File summary
- Path: src/agent/planner.py
- Purpose: Let an LLM compose a scientific question while a deterministic layer enforces scope.
- Core points:
  - The LLM proposes hypotheses and a plan; the catalogue bounds what it may reference.
  - `propose_repair` returns one catalog-bounded candidate; deterministic code decides acceptance.
  - The planner may not invent assays, measurements, sources, results, or capabilities.
- Interfaces: `MechanismContrastPlanner`, `propose`, `propose_repair`, `ContrastProposal`, `LLMRepairDraft`, `PlannerCompleter`, `PlannerContractError`
- Depends on: agent.context, maestro.models
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any, Protocol, Sequence

from .context import ContextPacket
from maestro.models import (
    ContrastCheck,
    DevelopmentAction,
    EvidenceAction,
    MechanismContrast,
    MechanismHypothesis,
)


class PlannerContractError(ValueError):
    """The model returned a proposal outside the planner's declared contract.

    It is a distinct type so a caller can treat one bad model response as a
    failed turn without also swallowing a genuine defect in the surrounding
    code, which a bare ``ValueError`` guard would do.
    """


class PlannerCompleter(Protocol):
    def complete_json(self, messages: list[dict[str, Any]], **kwargs: Any) -> tuple[dict[str, Any], Any]: ...


@dataclass(frozen=True)
class ContrastProposal:
    """A parsed, catalog-bounded contrast draft before it becomes a MechanismContrast."""

    identifier: str
    hypotheses: tuple[MechanismHypothesis, MechanismHypothesis]
    differing_assumptions: tuple[str, ...]
    action_identifier: str | None
    outcome_categories: tuple[str, ...]
    interpretation_boundaries: tuple[str, ...]

    def to_contrast(self, actions: Sequence[EvidenceAction]) -> MechanismContrast:
        """Materialise the draft into a contrast using a registered action identifier."""

        action = next((item for item in actions if item.identifier == self.action_identifier), None)
        return MechanismContrast(
            identifier=self.identifier,
            hypotheses=self.hypotheses,
            differing_assumptions=self.differing_assumptions,
            plan=action,
            outcome_categories=self.outcome_categories,
            interpretation_boundaries=self.interpretation_boundaries,
        )


@dataclass(frozen=True)
class LLMRepairDraft:
    """A proposal to alter one registered plan field, pending deterministic re-checking."""

    action_identifier: str | None
    modified_fields: tuple[str, ...]
    rationale: str
    remaining_limitations: tuple[str, ...]

    def apply(
        self, contrast: MechanismContrast, actions: Sequence[EvidenceAction]
    ) -> MechanismContrast | None:
        if self.action_identifier is None:
            return None
        action = next((item for item in actions if item.identifier == self.action_identifier), None)
        if action is None:
            return None
        return replace(contrast, plan=action)


class MechanismContrastPlanner:
    """Lets an LLM compose a scientific question while a deterministic layer enforces scope."""

    def __init__(self, client: PlannerCompleter):
        self._client = client

    def propose(
        self,
        context: ContextPacket,
        actions: Sequence[EvidenceAction],
        *,
        required_hypothesis_identifiers: Sequence[str] = (),
        expected_hypotheses: Sequence[MechanismHypothesis] = (),
    ) -> ContrastProposal:
        catalogue = [asdict(action) for action in actions]
        fixed_hypotheses = tuple(required_hypothesis_identifiers)
        registered = {item.identifier: item for item in expected_hypotheses}
        if registered and set(registered) != set(fixed_hypotheses):
            raise PlannerContractError("Registered hypothesis definitions and identifiers must agree.")
        constraint = (
            "Use exactly these two hypothesis identifiers, preserving their spelling: "
            + ", ".join(fixed_hypotheses)
            if fixed_hypotheses
            else "Generate two concise, stable hypothesis identifiers."
        )
        prompt = """You are MAESTRO's mechanism-contrast planner. Return JSON only.
Construct exactly two condition-specific, competing explanations that would lead to
        different development actions. Use only an action_identifier from AVAILABLE_ACTIONS;
do not invent assays, measurements, sources, results, or capabilities. Include at least
one interpretation boundary stating what the planned result cannot establish.
Name each hypothesis's causal factor explicitly: a plan preference is not a causal claim,
and no downstream rule may infer the factor from proposed_action.
The hypotheses' proposed_action fields are development decisions from the enum below,
not evidence-tool identifiers. Never copy action_identifier into proposed_action.
Use distinct development decisions for the competing explanations. A withheld observation
must remain hypothetical; dataset availability is not an observed response value.
Return {
  \"identifier\":\"...\",
  \"hypotheses\":[{\"identifier\":\"...\",\"description\":\"...\",\"proposed_action\":\"continue|revise_intervention|change_intervention_mode|preserve_multi_target_activity|remove_multi_target_activity|revise_attribution|defer|stop\",\"causal_factor\":\"incomplete_perturbation|mode_non_equivalence|multi_target_activity|pathway_compensation|context_dependence|unresolved\"},{...}],
  \"differing_assumptions\":[\"...\"], \"action_identifier\":\"...\",
  \"outcome_categories\":[\"...\"], \"interpretation_boundaries\":[\"...\"]
}."""
        data, _ = self._client.complete_json(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "CONTEXT\n" + context.rendered
                        + "\n\nHYPOTHESIS IDENTIFIER CONSTRAINT\n" + constraint
                        + "\n\nAVAILABLE_ACTIONS\n" + json.dumps(catalogue, allow_nan=False)
                    ),
                },
            ]
        )
        hypotheses = data.get("hypotheses")
        if not isinstance(hypotheses, list) or len(hypotheses) != 2:
            raise PlannerContractError("Mechanism planner must return exactly two hypotheses.")
        parsed_hypotheses = (_hypothesis(hypotheses[0]), _hypothesis(hypotheses[1]))
        if fixed_hypotheses and frozenset(item.identifier for item in parsed_hypotheses) != frozenset(fixed_hypotheses):
            raise PlannerContractError("Mechanism planner did not preserve the registered hypothesis identifiers.")
        if registered:
            parsed_hypotheses = tuple(registered[item.identifier] for item in parsed_hypotheses)
        return ContrastProposal(
            identifier=_text(data.get("identifier"), "mechanism-contrast"),
            hypotheses=parsed_hypotheses,
            differing_assumptions=_texts(data.get("differing_assumptions")),
            action_identifier=_optional_text(data.get("action_identifier")),
            outcome_categories=_texts(data.get("outcome_categories")),
            interpretation_boundaries=_texts(data.get("interpretation_boundaries")),
        )

    def propose_repair(
        self,
        context: ContextPacket,
        contrast: MechanismContrast,
        check: ContrastCheck,
        actions: Sequence[EvidenceAction],
    ) -> LLMRepairDraft:
        """Ask for one catalog-bounded scientific repair; deterministic code decides acceptance."""

        catalogue = [asdict(action) for action in actions]
        prompt = """You are MAESTRO's directed contrast-repair planner. Return JSON only.
The contrast failed deterministic checks. Propose at most one replacement action from
AVAILABLE_ACTIONS that addresses one or more listed failures. Do not invent evidence,
measurements, costs, or capabilities. You may modify only plan.action_identifier.
State remaining limitations explicitly. This is a candidate repair, not validation.
Return {"action_identifier": string or null, "modified_fields": ["plan.action_identifier"],
"rationale": string, "remaining_limitations": [string]}."""
        data, _ = self._client.complete_json(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "CONTEXT\n" + context.rendered + "\n\nCONTRAST\n" + json.dumps(asdict(contrast), allow_nan=False)
                        + "\n\nCHECK_FAILURES\n" + json.dumps([reason.value for reason in check.reasons])
                        + "\n\nAVAILABLE_ACTIONS\n" + json.dumps(catalogue, allow_nan=False)
                    ),
                },
            ]
        )
        fields = _texts(data.get("modified_fields"))
        if any(field != "plan.action_identifier" for field in fields):
            raise PlannerContractError("Repair planner attempted to modify a field outside its contract.")
        return LLMRepairDraft(
            action_identifier=_optional_text(data.get("action_identifier")),
            modified_fields=fields,
            rationale=_text(data.get("rationale"), "No repair rationale supplied."),
            remaining_limitations=_texts(data.get("remaining_limitations")),
        )


def _hypothesis(value: Any) -> MechanismHypothesis:
    if not isinstance(value, dict):
        raise PlannerContractError("Hypothesis must be an object.")
    action = _development_action(value.get("proposed_action"))
    return MechanismHypothesis(
        identifier=_text(value.get("identifier"), "hypothesis"),
        description=_text(value.get("description"), "No description supplied."),
        proposed_action=action,
        causal_factor=_optional_text(value.get("causal_factor")),
    )


def _development_action(value: Any) -> DevelopmentAction | None:
    """Parse a registered development action, or record its absence.

    An unregistered label becomes ``None`` rather than an exception. ``None`` is
    the type's own representation of "no registered action was supplied", and
    the deterministic check then reports ``decision_not_separated``, which is
    the designed handling of a proposal that cannot change a decision. Raising
    here instead would let one malformed field end a whole evaluation run, and
    when the caller registers the hypothesis definitions this field is
    discarded a few lines later anyway.
    """

    label = _optional_text(value)
    if not label:
        return None
    try:
        return DevelopmentAction(label)
    except ValueError:
        return None


def _texts(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip()) if isinstance(value, list) else ()


def _text(value: Any, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
