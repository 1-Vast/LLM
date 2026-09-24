"""Section 37 row 4: the same model, required to keep an explicit hypothesis posterior.

File summary
- Path: src/evaluation/llm_rows.py
- Purpose: fill the row that asks whether making the hypothesis bookkeeping explicit changes
  what a language model does. Row 3 is the existing single-agent arm and needs no new code;
  this arm differs from it in exactly one way - it must state a posterior over the registered
  explanations and the value of information of each action it could buy, and it must select
  the action it says is worth most.
- Core points:
  - The contract is enforced, not requested: a posterior that does not cover the registered
    explanations or does not sum to one is a named refusal, and so is an action the menu does
    not allow right now. A refused turn acquires nothing and is recorded.
  - The decision step reuses the shared submission parser, so the terminal contract is
    identical to the other provider-backed arms and the comparison is about selection.
  - Every call is priced into a spend ledger before and after it is made, so provider spend
    is reported separately from laboratory cost.
- Interfaces: `EXPLICIT_HYPOTHESES_PROMPT`, `ExplicitHypothesesLLMPolicy`
- Depends on: evaluation.baselines, evaluation.cases, evaluation.provider_spend
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from .baselines import DecisionSubmission, JSONCompleter, _prerequisites_met, _request_submission
from .cases import ReplayView
from .provider_spend import SpendLedger

EXPLICIT_HYPOTHESES_PROMPT = (
    "You are deciding one experimental case, and you must show your hypothesis bookkeeping.\n\n"
    "Return one JSON object and nothing else:\n"
    '  {"posterior": {"<explanation identifier>": <probability>, ...}, '
    '"value_of_information": {"<action identifier>": <expected reduction in decision loss>, ...}, '
    '"action": "<action identifier or null>", "rationale": "<one sentence>"}\n\n'
    "The posterior must cover exactly the registered explanations and sum to 1. The value of "
    "information must cover every action you were offered. Set \"action\" to the identifier you "
    "would buy now, or to null if no action is worth its cost, in which case the case will be "
    "decided on what you already have. A decision that names a cause is supported only when "
    "every explanation still compatible with the evidence would accept it."
)


class ExplicitHypothesesLLMPolicy:
    """Row 4: the same model as row 3, with the posterior and the value of information enforced."""

    name = "explicit_hypotheses_llm"

    def __init__(
        self,
        client: JSONCompleter,
        *,
        ledger: SpendLedger | None = None,
        # The configured model reasons before it answers, and reasoning counts against this
        # budget: a trivial object cost 437 completion tokens in the reachability probe, and
        # this row's object at 4000 returned `finish_reason=length` with no content. The budget
        # is a cap, not a charge; only tokens actually produced are paid for.
        max_tokens: int = 16000,
        estimate_usd: float = 0.016,
    ) -> None:
        self._client = client
        self._ledger = ledger
        self._max_tokens = max_tokens
        self._estimate = estimate_usd
        self.turns: list[Mapping[str, Any]] = []

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        if not candidates:
            return None
        allowed = {item.action.identifier for item in candidates}
        registered = {str(entry["identifier"]) for entry in view.case.hypotheses}
        statement = self._statement(view, candidates)
        label = f"row4:{view.case.identifier}:{len(view.revealed)}"
        if self._ledger is not None:
            self._ledger.reserve(label, self._estimate)
        try:
            payload, response = self._client.complete_json(
                [
                    {"role": "system", "content": EXPLICIT_HYPOTHESES_PROMPT},
                    {"role": "user", "content": json.dumps(statement, ensure_ascii=False, sort_keys=True, default=str)},
                ],
                max_tokens=self._max_tokens,
            )
        except Exception as error:  # a provider failure is data, not a crash
            detail = str(error)[:300]
            if self._ledger is not None:
                self._ledger.charge(
                    label,
                    None,
                    status="failed",
                    reserved_usd=self._estimate,
                    note=f"{type(error).__name__}: {detail}; charged at reservation",
                )
            self.turns.append(
                {
                    "case": view.case.identifier,
                    "refusal": f"provider_failure:{type(error).__name__}",
                    "detail": detail,
                }
            )
            return None
        if self._ledger is not None:
            self._ledger.charge(label, dict(response.usage), status="ok", reserved_usd=self._estimate)
        refusal = self._contract_refusal(payload, registered, allowed)
        self.turns.append(
            {
                "case": view.case.identifier,
                "posterior": payload.get("posterior"),
                "value_of_information": payload.get("value_of_information"),
                "action": payload.get("action"),
                "refusal": refusal,
            }
        )
        if refusal is not None:
            return None
        action = payload.get("action")
        return str(action) if isinstance(action, str) and action in allowed else None

    def decide(self, view: ReplayView) -> DecisionSubmission | None:
        if not view.revealed:
            return None
        return _request_submission(self._client, view)

    @staticmethod
    def _statement(view: ReplayView, candidates) -> Mapping[str, Any]:
        """What this row's turn actually needs, and nothing else.

        The full public contract, the unavailable actions and every record's metrics and
        limitations are what a decision step reads; a selection step needs the explanations,
        what has already been observed, and what each purchasable action is declared to show
        under each explanation. Sending the rest made the model reason past a twelve-thousand
        token budget and return no content at all, which is a failure of the prompt rather
        than of the row.
        """

        return {
            "case": view.case.identifier,
            "registered_explanations": [
                {"identifier": str(item["identifier"]), "description": str(item["description"])[:200]}
                for item in view.case.hypotheses
            ],
            "observed_so_far": [
                {"action": record.action_identifier, "outcome": record.outcome, "statement": record.statement[:240]}
                for record in view.revealed
            ],
            "purchasable_actions": [
                {
                    "identifier": item.action.identifier,
                    "cost": item.action.cost,
                    "declared_outcome_by_explanation": dict(item.action.expected_outcomes),
                }
                for item in candidates
            ],
            "remaining_budget": view.remaining_budget,
        }

    @staticmethod
    def _contract_refusal(
        payload: Mapping[str, Any], registered: set[str], allowed: set[str]
    ) -> str | None:
        """Name the contract violation rather than silently treating the turn as a pass."""

        posterior = payload.get("posterior")
        if not isinstance(posterior, dict) or set(posterior) != registered:
            return "posterior_does_not_cover_the_registered_explanations"
        try:
            total = sum(float(value) for value in posterior.values())
        except (TypeError, ValueError):
            return "posterior_is_not_numeric"
        if abs(total - 1.0) > 1e-6:
            return f"posterior_not_normalised:{total:.6f}"
        values = payload.get("value_of_information")
        if not isinstance(values, dict) or not allowed.issubset(set(values)):
            return "value_of_information_does_not_cover_the_offered_actions"
        action = payload.get("action")
        if action is not None and (not isinstance(action, str) or action not in allowed):
            return f"action_not_executable:{action}"
        return None
