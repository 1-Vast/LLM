"""Strict decision review (policy `strict-review-1`): authenticated receipts, required predictions, human approval.

Every required prediction needs authenticated measured support; progression also requires measured competitor exclusion and evidence-bound human approval."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from maestro.decision_review import (APPROVAL_MISMATCH, AUTOMATED_APPROVERS, SELF_APPROVAL, Approval,
                                     DiscriminatingExperiment, Explanation, Prediction, discriminating_experiments)
from maestro.evidence_registry import RELATIONS, EvidenceLedger, canonical_value, holds

POLICY_VERSION = "strict-review-1"
NO_SIGNAL_REFUSED = "NO_SIGNAL_REFUSED"
NO_DISCRIMINATING_EXPERIMENT = "NO_DISCRIMINATING_EXPERIMENT_AVAILABLE"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class Role(str, Enum):
    REQUIRED = "required"
    SUPPORTIVE = "supportive"


class StrictStatus(str, Enum):
    GO = "GO"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    NO_GO = "NO_GO"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"


class Outcome(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    CONFLICTED = "conflicted"
    UNTESTED = "untested"


@dataclass(frozen=True)
class StrictPrediction:
    key: str
    observable: str
    relation: str
    threshold: float
    unit: str
    role: Role = Role.REQUIRED

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.observable.strip() or self.relation not in RELATIONS:
            raise ValueError("prediction needs a key, an observable and a relation in <=, >=, <, >")
        canonical_value(self.threshold, self.unit)


@dataclass(frozen=True)
class StrictExplanation:
    identifier: str
    statement: str
    predictions: tuple[StrictPrediction, ...]
    progression: bool = False

    def __post_init__(self) -> None:
        if not self.identifier.strip() or not self.statement.strip() or not self.predictions:
            raise ValueError("explanation needs an identifier, a statement and at least one prediction")


@dataclass(frozen=True)
class NoSignalRule:
    """Signal is absent exactly when ``observable relation threshold`` holds for the receipt's value."""

    rule_id: str
    observable: str
    relation: str
    threshold: float
    unit: str

    def __post_init__(self) -> None:
        if self.relation not in RELATIONS:
            raise ValueError("no-signal rule needs a relation in <=, >=, <, >")
        canonical_value(self.threshold, self.unit)


@dataclass(frozen=True)
class Limitation:
    identifier: str
    statement: str
    critical: bool = False
    resolved_by: str | None = None


@dataclass(frozen=True)
class StrictPolicy:
    protocol_version: str
    min_independent_groups: int = 1
    exclude_alternatives: bool = True
    no_signal_rules: tuple[NoSignalRule, ...] = ()
    version: str = POLICY_VERSION

    def __post_init__(self) -> None:
        if not self.protocol_version.strip() or type(self.min_independent_groups) is not int or self.min_independent_groups < 1:
            raise ValueError("policy needs a protocol version and min_independent_groups >= 1")


@dataclass(frozen=True)
class StrictDecision:
    candidate: str
    status: StrictStatus
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    results: Mapping[str, Mapping[str, str]]
    experiment: DiscriminatingExperiment | None
    binding: Mapping[str, str]
    basis_sha256: str
    policy_version: str
    approver: str = ""


def _outcome(prediction: StrictPrediction, ledger: EvidenceLedger, context: str, policy: StrictPolicy) -> tuple[Outcome, tuple[str, ...], list[str]]:
    """Per independent upstream group, all admitted values must hold; groups then vote."""

    dimension, threshold = canonical_value(prediction.threshold, prediction.unit)
    by_group: dict[str, list[bool]] = {}
    used, refusals = [], []
    for receipt_id in ledger.receipt_ids():
        receipt = ledger.receipt(receipt_id)
        if receipt.observable != prediction.observable:
            continue
        ok, why = ledger.admit(receipt_id, context, policy.protocol_version)
        if ok and receipt.rule_id != prediction.key:
            ok, why = False, f"RULE_MISMATCH:{receipt.rule_id}"
        if not ok:
            refusals.append(f"not_admitted:{receipt.observable}:{receipt_id}:{why}")
            continue
        value_dimension, value = canonical_value(receipt.value, receipt.unit)
        if value_dimension != dimension:
            refusals.append(f"not_admitted:{receipt.observable}:{receipt_id}:UNIT_DIMENSION_MISMATCH")
            continue
        used.append(receipt_id)
        for group in ledger.lineage(receipt_id)[0]:
            by_group.setdefault(group, []).append(holds(value, prediction.relation, threshold))
    if not by_group:
        return Outcome.UNTESTED, (), refusals
    group_holds = [all(v) for v in by_group.values()]
    if all(group_holds):
        outcome = Outcome.SUPPORTED if len(group_holds) >= policy.min_independent_groups else Outcome.UNTESTED
        if outcome is Outcome.UNTESTED:
            refusals.append(f"insufficient_independent_groups:{prediction.key}:{len(group_holds)}<{policy.min_independent_groups}")
    elif not any(group_holds):
        outcome = Outcome.CONTRADICTED
    else:
        outcome = Outcome.CONFLICTED
    return outcome, tuple(used), refusals


def _no_signal(ledger: EvidenceLedger, receipt_id: str | None, rule_id: str | None, context: str, policy: StrictPolicy) -> tuple[bool, str, tuple[str, ...]]:
    if receipt_id is None or rule_id is None:
        return False, "", ()
    rule = next((r for r in policy.no_signal_rules if r.rule_id == rule_id), None)
    if rule is None:
        return False, f"{NO_SIGNAL_REFUSED}:RULE_NOT_REGISTERED:{rule_id}", ()
    if receipt_id not in ledger.receipt_ids():
        return False, f"{NO_SIGNAL_REFUSED}:RECEIPT_UNKNOWN:{receipt_id}", ()
    receipt = ledger.receipt(receipt_id)
    ok, why = ledger.admit(receipt_id, context, policy.protocol_version, allow_undetected=True)
    if not ok:
        return False, f"{NO_SIGNAL_REFUSED}:{why}", ()
    if receipt.observable != rule.observable or receipt.rule_id != rule.rule_id:
        return False, f"{NO_SIGNAL_REFUSED}:RULE_OBSERVABLE_MISMATCH", ()
    dimension, threshold = canonical_value(rule.threshold, rule.unit)
    value_dimension, value = canonical_value(receipt.value, receipt.unit)
    if value_dimension != dimension:
        return False, f"{NO_SIGNAL_REFUSED}:UNIT_DIMENSION_MISMATCH", ()
    if not holds(value, rule.relation, threshold):
        return False, f"{NO_SIGNAL_REFUSED}:SIGNAL_PRESENT", ()
    return True, f"NO_SELECTIVE_SIGNAL:{rule.rule_id}", (receipt_id,)


def _basis(candidate: str, policy: StrictPolicy, status: str, reasons: Sequence[str], binding: Mapping[str, str]) -> str:
    payload = {"candidate": candidate, "policy": policy.version, "protocol": policy.protocol_version,
               "min_groups": policy.min_independent_groups, "exclude_alternatives": policy.exclude_alternatives, "status": status, "reasons": sorted(reasons),
               "binding": dict(sorted(binding.items()))}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def approve_basis(basis_sha256: str, approver: str, note: str = "") -> Approval:
    if approver.strip().lower() in AUTOMATED_APPROVERS:
        raise PermissionError(SELF_APPROVAL)
    return Approval(basis_sha256, approver.strip(), note)


def strict_review(candidate: str, explanations: Sequence[StrictExplanation], ledger: EvidenceLedger, policy: StrictPolicy, *,
                  context: str, funded: bool, limitations: Sequence[Limitation] = (),
                  menu: Sequence[DiscriminatingExperiment] = (), no_signal_receipt: str | None = None,
                  no_signal_rule: str | None = None, approval: Approval | None = None) -> StrictDecision:
    if len(explanations) < 2 or len({e.identifier for e in explanations}) != len(explanations):
        raise ValueError("a review needs at least two uniquely identified competing explanations")
    progression = [e for e in explanations if e.progression]
    if len(progression) != 1:
        raise ValueError("exactly one explanation must be the progression explanation")
    if not any(p.role is Role.REQUIRED for p in progression[0].predictions):
        raise ValueError("the progression explanation must declare at least one REQUIRED prediction")
    keys = [p.key for e in explanations for p in e.predictions]
    if len(keys) != len(set(keys)):
        raise ValueError("prediction keys must be unique")

    results: dict[str, dict[str, str]] = {}
    used: set[str] = set()
    notes: list[str] = []
    outcomes: dict[str, Outcome] = {}
    for e in explanations:
        results[e.identifier] = {}
        for p in e.predictions:
            outcome, receipts, refusals = _outcome(p, ledger, context, policy)
            outcomes[p.key] = outcome
            results[e.identifier][f"{p.key}[{p.role.value}] {p.observable} {p.relation} {p.threshold:g} {p.unit}"] = outcome.value
            used.update(receipts)
            notes.extend(refusals)

    prog_required = [p for p in progression[0].predictions if p.role is Role.REQUIRED]
    prog_supportive = [p for p in progression[0].predictions if p.role is Role.SUPPORTIVE]
    flags = [f"supportive_{outcomes[p.key].value}:{p.key}" for p in prog_supportive if outcomes[p.key] is not Outcome.SUPPORTED]
    unresolved = []
    for lim in limitations:
        resolved = False
        if lim.resolved_by is not None and lim.resolved_by in ledger.receipt_ids():
            resolved = ledger.admit(lim.resolved_by, context, policy.protocol_version)[0]
            if resolved:
                used.add(lim.resolved_by)
        if not resolved:
            (unresolved if lim.critical else flags).append(lim.identifier if lim.critical else f"limitation:{lim.identifier}")
    flags += sorted(set(notes))

    signal, signal_reason, signal_receipts = _no_signal(ledger, no_signal_receipt, no_signal_rule, context, policy)
    if signal_reason.startswith(NO_SIGNAL_REFUSED):
        flags.append(signal_reason)
    used.update(signal_receipts)

    contradicted = [p for p in prog_required if outcomes[p.key] is Outcome.CONTRADICTED]
    gaps = [p for p in prog_required if outcomes[p.key] in (Outcome.UNTESTED, Outcome.CONFLICTED)]
    competitors_open = []
    if policy.exclude_alternatives:
        for e in explanations:
            if e.progression:
                continue
            required = [p for p in e.predictions if p.role is Role.REQUIRED] or list(e.predictions)
            if not any(outcomes[p.key] is Outcome.CONTRADICTED for p in required):
                competitors_open.append(e.identifier)

    experiment = None
    if signal:
        status, reasons = StrictStatus.NO_GO, (signal_reason,)
    elif contradicted:
        status, reasons = StrictStatus.NO_GO, tuple(f"CONTRADICTED:{p.key}" for p in contradicted)
    else:
        blockers = [f"{outcomes[p.key].value.upper()}:{p.key}" for p in gaps]
        blockers += [f"CRITICAL_LIMITATION:{x}" for x in unresolved]
        blockers += [f"ALTERNATIVE_NOT_EXCLUDED:{x}" for x in competitors_open]
        if not funded:
            blockers.append("NOT_FUNDED")
        if blockers:
            status, reasons = StrictStatus.NEED_MORE_EVIDENCE, tuple(blockers)
            options = discriminating_experiments([Explanation(e.identifier, e.statement, tuple(Prediction(p.observable, p.relation, p.threshold) for p in e.predictions), e.progression) for e in explanations], menu)
            if options:
                experiment = options[0]
            else:
                reasons += (NO_DISCRIMINATING_EXPERIMENT,)
        else:
            status, reasons = StrictStatus.AWAITING_APPROVAL, tuple(f"SUPPORTED:{p.key}" for p in prog_required) + (APPROVAL_REQUIRED,)
    binding = ledger.binding(used)
    basis = _basis(candidate, policy, StrictStatus.GO.value if status is StrictStatus.AWAITING_APPROVAL else status.value, reasons[:-1] if status is StrictStatus.AWAITING_APPROVAL else reasons, binding)
    approver = ""
    if status is StrictStatus.AWAITING_APPROVAL and approval is not None:
        if approval.request_sha256 != basis:
            flags.append(APPROVAL_MISMATCH)
        elif approval.approver.strip().lower() in AUTOMATED_APPROVERS:
            flags.append(SELF_APPROVAL)
        else:
            status, reasons, approver = StrictStatus.GO, reasons[:-1] + (f"APPROVED_BY:{approval.approver}",), approval.approver
    return StrictDecision(candidate, status, reasons, tuple(flags), results, experiment, binding, basis, policy.version, approver)


def certificate_problems(decision: StrictDecision, ledger: EvidenceLedger) -> list[str]:
    """Why a GO certificate no longer holds: a receipt it rests on was withdrawn, altered or lost."""

    if decision.status is not StrictStatus.GO:
        return [f"NOT_A_GO:{decision.status.value}"]
    return ledger.binding_problems(decision.binding)
