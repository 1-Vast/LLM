"""Dataset-independent proposal review. Reports defects; owns no repair or execution tool."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite
from typing import Mapping


def _hash(value: object) -> str | None:
    try:
        text = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except (TypeError, ValueError, OverflowError, UnicodeError):
        return None


@dataclass(frozen=True)
class AuditFinding:
    code: str
    detail: str


@dataclass(frozen=True)
class ModelAuditReport:
    input_sha256: str | None
    proposal_sha256: str | None
    findings: tuple[AuditFinding, ...]

    def payload(self) -> dict[str, object]:
        return asdict(self)


class ModelAuditAgent:
    """Review a registered action card against a provider proposal without mutation.

    Qualified prerequisites are supplied by the evidence validator, never inferred
    from forecast text. This small contract is shared across task adapters. The
    caller may decline a defective proposal; this reviewer supplies no replacement
    action, biological verdict, evidence, or model correction.
    """

    def review(self, card: Mapping[str, object], proposal: object) -> ModelAuditReport:
        input_hash, proposal_hash = _hash(card), _hash(proposal)
        findings: list[AuditFinding] = []

        def report():
            return ModelAuditReport(input_hash, proposal_hash, tuple(findings))

        def number(value):
            if type(value) not in (int, float):
                return False
            try:
                return isfinite(value) and value >= 0
            except OverflowError:
                return False

        if input_hash is None or not isinstance(card, Mapping):
            findings.append(AuditFinding("invalid_task_contract", "Task card must be a finite JSON object; unavailable hash is null."))
            return report()
        budget, actions = card.get("remaining_budget"), card.get("actions")
        qualified, attempted = card.get("qualified_prerequisites", []), card.get("attempted_actions", [])
        if not number(budget) or not isinstance(actions, list) or not all(
            isinstance(items, (list, tuple)) and all(isinstance(x, str) for x in items)
            for items in (qualified, attempted)
        ) or not all(
            isinstance(a, Mapping) and isinstance(a.get("id"), str) and a["id"]
            and a["id"] != "defer" and number(a.get("cost"))
            and isinstance(a.get("prerequisites", []), (list, tuple))
            and all(isinstance(p, str) for p in a.get("prerequisites", []))
            for a in actions
        ) or len({a["id"] for a in actions}) != len(actions):
            findings.append(AuditFinding("invalid_task_contract", "Expected a unique registered menu, finite costs/budget and qualified prerequisite identifiers."))
            return report()
        if proposal_hash is None or not isinstance(proposal, Mapping) or not isinstance(proposal.get("action"), str) or type(proposal.get("terminal_authorized")) is not bool:
            findings.append(AuditFinding("malformed_proposal", "Expected action:string and terminal_authorized:boolean."))
            return report()
        if proposal["terminal_authorized"]:
            findings.append(AuditFinding("terminal_authority_claim", "A model proposal cannot authorize a terminal decision."))
        selected = proposal["action"]
        legal = {a["id"] for a in actions if a["cost"] <= budget and a["id"] not in attempted
                 and set(a.get("prerequisites", [])).issubset(qualified)}
        if selected != "defer" and selected not in legal:
            findings.append(AuditFinding("illegal_action", "Action is unregistered, attempted, unaffordable or missing qualified prerequisites."))
        return report()
