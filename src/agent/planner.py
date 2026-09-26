"""LLM-assisted proposal of a constrained mechanism contrast for validation.

File summary
- Path: src/agent/planner.py
- Purpose: Let an LLM compose a scientific question while a deterministic layer enforces scope.
- Core points:
  - The LLM proposes hypotheses and a plan; the catalogue bounds what it may reference.
  - `propose_repair` returns one catalog-bounded candidate; deterministic code decides acceptance.
  - A reply that breaks the declared contract is named back to the model and asked once
    more (bounded by `contract_retries`); a second violation still raises.
  - A reply that parses but fails a deterministic critic only the planner can satisfy (an
    unregistered action, explanations that do not separate a decision) is back-prompted
    within the same budget, LLM-Modulo style; after the budget it is returned unchanged
    and the controller's own check reports the failure as before.
  - Catalogues are rendered compactly: undeclared (null or empty) fields are omitted and
    a contrast names its plan by identifier instead of repeating the action.
  - `propose` accepts an `extra_critique` hook so a caller's own critic (for example a typed
    decision model) can add findings to the same bounded back-prompt loop.
  - `propose_repair` accepts `advisory_findings`, rendered under their own heading as advice to
    weigh, never as facts and never as new actions.
  - `propose_repair` may receive a planning-only virtual-cell briefing; it is labelled as
    model output and never enters the catalogue, the contrast or the evidence ledger.
  - The planner may not invent assays, measurements, sources, results, or capabilities.
- Interfaces: `MechanismContrastPlanner`, `propose`, `propose_repair`, `contract_violations`, `critic_findings`, `render_catalogue`, `render_contrast`, `ContrastProposal`, `LLMRepairDraft`, `PlannerCompleter`, `PlannerContractError`
- Depends on: agent.context, maestro.models
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any, Callable, Mapping, Protocol, Sequence, TypeVar

from .context import ContextPacket
from maestro.models import (
    ContrastCheck,
    DevelopmentAction,
    EvidenceAction,
    MechanismContrast,
    MechanismHypothesis,
)


_Parsed = TypeVar("_Parsed")


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

    def __init__(self, client: PlannerCompleter, *, contract_retries: int = 1):
        if isinstance(contract_retries, bool) or not isinstance(contract_retries, int) or contract_retries < 0:
            raise ValueError("contract_retries must be a non-negative integer.")
        self._client = client
        self._contract_retries = contract_retries
        # Every violation and critic finding the model was asked to correct, in
        # order, so a run reports how often a turn needed a second answer.
        self.contract_violations: list[str] = []
        self.critic_findings: list[str] = []

    def _complete_within_contract(
        self,
        messages: list[dict[str, Any]],
        parse: Callable[[dict[str, Any]], _Parsed],
        critique: Callable[[_Parsed], tuple[str, ...]] | None = None,
    ) -> _Parsed:
        """Generate, test, and back-prompt a bounded number of times.

        The parser is the hard critic: a violation of the declared shape is
        echoed back with the parser's own message, and one still present when
        the budget is spent raises, as a single bad reply always did. ``critique``
        is the soft critic: it names failures the deterministic check would
        report and that only the planner can fix. They are fed back the same way,
        but a reply that still has them after the budget is returned, so the
        controller's check and repair handle it exactly as before. Transport
        failures are not retried here; the client owns that.
        """

        conversation = list(messages)
        for attempt in range(self._contract_retries + 1):
            data, _ = self._client.complete_json(conversation)
            last = attempt >= self._contract_retries
            try:
                result = parse(data)
            except PlannerContractError as error:
                self.contract_violations.append(str(error))
                if last:
                    raise
                heading, feedback = "CONTRACT_VIOLATION", str(error)
            else:
                findings = critique(result) if critique is not None else ()
                if not findings or last:
                    return result
                self.critic_findings.extend(findings)
                heading, feedback = "CRITIC_FEEDBACK", "\n".join(findings)
            conversation = conversation + [
                {"role": "assistant", "content": json.dumps(data, ensure_ascii=False, default=str)},
                {
                    "role": "user",
                    "content": (
                        f"{heading}\n{feedback}\nReturn one corrected JSON object with the same schema. Correct "
                        "only what is named; do not add facts, actions, hypotheses or capabilities."
                    ),
                },
            ]
        raise AssertionError("unreachable: the loop returns or raises")  # pragma: no cover

    def propose(
        self,
        context: ContextPacket,
        actions: Sequence[EvidenceAction],
        *,
        required_hypothesis_identifiers: Sequence[str] = (),
        expected_hypotheses: Sequence[MechanismHypothesis] = (),
        extra_critique: Callable[["ContrastProposal"], Sequence[str]] | None = None,
    ) -> ContrastProposal:
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
Conditioned biological relations are planning assertions, never case measurements.
Distinguish correlation, regulatory association and causal effects. Attention weights and
feature importance establish neither regulatory edges nor causal mechanisms. Preserve
unknown conditions and conflicting evidence; propose a discriminating measurement rather
than resolving conflicts by confidence. An RNA change does not establish protein activity.
Return {
  \"identifier\":\"...\",
  \"hypotheses\":[{\"identifier\":\"...\",\"description\":\"...\",\"proposed_action\":\"continue|revise_intervention|change_intervention_mode|preserve_multi_target_activity|remove_multi_target_activity|revise_attribution|defer|stop\",\"causal_factor\":\"incomplete_perturbation|mode_non_equivalence|multi_target_activity|pathway_compensation|context_dependence|unresolved\"},{...}],
  \"differing_assumptions\":[\"...\"], \"action_identifier\":\"...\",
  \"outcome_categories\":[\"...\"], \"interpretation_boundaries\":[\"...\"]
}."""
        def parse(data: dict[str, Any]) -> ContrastProposal:
            hypotheses = data.get("hypotheses")
            if not isinstance(hypotheses, list) or len(hypotheses) != 2:
                received = len(hypotheses) if isinstance(hypotheses, list) else type(hypotheses).__name__
                raise PlannerContractError(
                    f"Mechanism planner must return exactly two hypotheses; received {received}."
                )
            parsed_hypotheses = (_hypothesis(hypotheses[0]), _hypothesis(hypotheses[1]))
            returned = frozenset(item.identifier for item in parsed_hypotheses)
            if fixed_hypotheses and returned != frozenset(fixed_hypotheses):
                raise PlannerContractError(
                    "Mechanism planner did not preserve the registered hypothesis identifiers; "
                    f"expected {sorted(fixed_hypotheses)}, received {sorted(returned)}."
                )
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

        def critique(proposal: ContrastProposal) -> tuple[str, ...]:
            findings = list(_unregistered_action(proposal.action_identifier, actions, required=True))
            if not registered:
                # Registered definitions are the caller's; only model-authored ones are critiqued.
                decisions = [item.proposed_action for item in proposal.hypotheses]
                if None in decisions or decisions[0] == decisions[1]:
                    findings.append(
                        "The two hypotheses must propose two distinct development actions from the enum; "
                        f"received {[item.value if item else None for item in decisions]}."
                    )
            if extra_critique is not None:
                # A caller's critic sees a parsed proposal, so it can only add findings about
                # what the model actually returned; it cannot rewrite the proposal itself.
                findings.extend(str(item) for item in extra_critique(proposal) if str(item).strip())
            return tuple(findings)

        return self._complete_within_contract(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "CONTEXT\n" + context.rendered
                        + "\n\nHYPOTHESIS IDENTIFIER CONSTRAINT\n" + constraint
                        + "\n\nAVAILABLE_ACTIONS\n" + render_catalogue(actions)
                    ),
                },
            ],
            parse,
            critique,
        )

    def propose_repair(
        self,
        context: ContextPacket,
        contrast: MechanismContrast,
        check: ContrastCheck,
        actions: Sequence[EvidenceAction],
        *,
        world_model_briefing: str = "",
        action_topology: Mapping[str, Any] | None = None,
        advisory_findings: Sequence[str] = (),
    ) -> LLMRepairDraft:
        """Ask for one catalog-bounded scientific repair; deterministic code decides acceptance.

        ``world_model_briefing`` is the controller's rendering of this round's
        virtual-cell queries. It is shown under its own heading as planning-only
        model output: it may inform which registered action to propose, and it
        cannot supply a prerequisite, an observation or a new action.

        ``advisory_findings`` are a second opinion from a typed decision model. They are shown
        as advice to weigh against the catalogue, never as measurements, and they can never add
        an action: the contract still admits only a registered `action_identifier`.

        ``action_topology`` is the controller's deterministic dependency analysis of
        the menu (`ActionTopology.summary()`): which actions run now, how many
        supplier steps the others need, and which premises nothing registered
        supplies. It is structure computed from declarations, not model output.
        """

        prompt = """You are MAESTRO's directed contrast-repair planner. Return JSON only.
The contrast failed deterministic checks. Propose at most one replacement action from
AVAILABLE_ACTIONS that addresses one or more listed failures. Do not invent evidence,
measurements, costs, or capabilities. You may modify only plan.action_identifier.
State remaining limitations explicitly. This is a candidate repair, not validation.
Return {"action_identifier": string or null, "modified_fields": ["plan.action_identifier"],
"rationale": string, "remaining_limitations": [string]}."""
        briefing = world_model_briefing.strip()

        def parse(data: dict[str, Any]) -> LLMRepairDraft:
            fields = _texts(data.get("modified_fields"))
            outside = [field for field in fields if field != "plan.action_identifier"]
            if outside:
                raise PlannerContractError(
                    "Repair planner attempted to modify a field outside its contract: "
                    + ", ".join(sorted(set(outside))) + "; only plan.action_identifier may change."
                )
            return LLMRepairDraft(
                action_identifier=_optional_text(data.get("action_identifier")),
                modified_fields=fields,
                rationale=_text(data.get("rationale"), "No repair rationale supplied."),
                remaining_limitations=_texts(data.get("remaining_limitations")),
            )

        return self._complete_within_contract(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "CONTEXT\n" + context.rendered + "\n\nCONTRAST\n" + render_contrast(contrast)
                        + "\n\nCHECK_FAILURES\n" + json.dumps([reason.value for reason in check.reasons])
                        + "\n\nAVAILABLE_ACTIONS\n" + render_catalogue(actions)
                        + (_topology_section(action_topology) if action_topology else "")
                        + _advisory_section(advisory_findings)
                        + ("\n\n" + briefing if briefing else "")
                    ),
                },
            ],
            parse,
            lambda draft: _unregistered_action(draft.action_identifier, actions, required=False),
        )


def _declared(payload: dict[str, Any]) -> dict[str, Any]:
    """Omit fields that declare nothing: null, or an empty string, list or mapping.

    Booleans and numbers are kept even when they equal a default, because a
    ``False`` or a ``0.0`` can be a declaration (``context_bound`` defaults to
    true, so its false value is the informative one).
    """

    return {
        key: value
        for key, value in payload.items()
        if value is not None and not (isinstance(value, (str, list, tuple, dict)) and not value)
    }


def render_catalogue(actions: Sequence[EvidenceAction]) -> str:
    """The registered menu as compact JSON; an omitted field means "not declared"."""

    return json.dumps(
        [_declared(asdict(action)) for action in actions], allow_nan=False, separators=(",", ":")
    )


def render_contrast(contrast: MechanismContrast) -> str:
    """A contrast as compact JSON that names its plan instead of repeating the catalogue entry."""

    payload = _declared(asdict(contrast))
    payload["hypotheses"] = [_declared(item) for item in payload.get("hypotheses", ())]
    payload["plan"] = contrast.plan.identifier if contrast.plan is not None else None
    if contrast.additional_plans:
        payload["additional_plans"] = [action.identifier for action in contrast.additional_plans]
    return json.dumps(payload, allow_nan=False, separators=(",", ":"))


TOPOLOGY_HEADING = (
    "ACTION_TOPOLOGY (deterministic analysis of the registered menu under the current profile; "
    "steps_to_executable counts the actions in the shortest supplier chain, null means no registered "
    "chain exists; unsupplied_premises are premises no registered action supplies)"
)


ADVISORY_HEADING = (
    "TYPED_DECISION_ADVISORY (a separate calibrated model's judgement about this plan; advice to "
    "weigh, not measurement, and never a licence to name an action outside AVAILABLE_ACTIONS)"
)


def _advisory_section(findings: Sequence[str]) -> str:
    named = [str(item).strip() for item in findings if str(item).strip()]
    if not named:
        return ""
    return "\n\n" + ADVISORY_HEADING + "\n" + "\n".join(f"- {item}" for item in named)


def _topology_section(summary: Mapping[str, Any]) -> str:
    return "\n\n" + TOPOLOGY_HEADING + "\n" + json.dumps(dict(summary), allow_nan=False, separators=(",", ":"))


def _unregistered_action(
    identifier: str | None, actions: Sequence[EvidenceAction], *, required: bool
) -> tuple[str, ...]:
    """Name an action identifier that is absent from the registered menu."""

    if not actions:
        return ()
    registered = [action.identifier for action in actions]
    if identifier is None:
        if not required:
            return ()
        return (f"action_identifier is missing; choose one of {registered[:40]}.",)
    if identifier in registered:
        return ()
    return (f"action_identifier '{identifier}' is not in AVAILABLE_ACTIONS; choose one of {registered[:40]}.",)


def _hypothesis(value: Any) -> MechanismHypothesis:
    if not isinstance(value, dict):
        raise PlannerContractError(f"Each hypothesis must be an object; received {type(value).__name__}.")
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
