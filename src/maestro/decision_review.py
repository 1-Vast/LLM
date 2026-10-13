"""Scientific Decision Review: competing explanations, admitted evidence, discriminating experiments, GO / NO-GO.

File summary
- Path: src/maestro/decision_review.py
- Purpose: turn a candidate's competing explanations and its evidence into one auditable progression
  decision: GO, NO_GO or NEED_MORE_EVIDENCE. Each decision carries explicit reasons, evidential
  limitations and the digest of everything it rests on.
- Core points:
  - An `Explanation` is falsifiable: it states `Prediction`s about named observables. A
    candidate needs at least two explanations, and exactly one is the progression explanation
    (the one a GO relies on).
  - `EvidenceItem` records origin (`EvidenceKind`), measurement status
    (`ScientificMeasurementStatus` values), assay context and a source digest. `admit` decides
    what an item may do:
    - qualified real measurements, and analyses derived from them, may support or contradict a
      prediction;
    - model predictions, retrieved sources and unqualified items are kept as context only. They
      can never falsify, rescue or progress a candidate. A virtual-cell or LLM claim therefore
      cannot overwrite a measurement.
  - `review` applies the rule:
    - NO_GO needs the progression explanation contradicted by admitted evidence, or an admitted
      no-signal finding;
    - GO needs admitted support, no admitted contradiction and funding;
    - everything else is NEED_MORE_EVIDENCE and must name an experiment that discriminates
      between at least two explanations (`discriminating_experiments`).
  - `exploration_tournament` ranks candidates for exploration only. Its `ExplorationRanking`
    refuses to be read as a probability (`as_probability` raises `RANKING_NOT_PROBABILITY`), and
    `EvidenceItem` refuses a ranking as a value.
  - `ExperimentRequest` / `approve` / `authorize_execution` keep consequential experiments behind
    a named human approval that is bound to the request digest and checked against the budget.
- Interfaces: `Prediction`, `Explanation`, `EvidenceItem`, `admit`, `evaluate_prediction`,
  `DiscriminatingExperiment`, `discriminating_experiments`, `ReviewDecision`, `review`,
  `ExplorationRanking`, `exploration_tournament`, `ExperimentRequest`, `Approval`, `approve`,
  `authorize_execution`, `decision_digest`.
- Depends on: maestro.models, maestro.case_memory, maestro.campaign_budget.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Mapping, Sequence

from maestro.campaign_budget import CampaignBudget
from maestro.case_memory import ScientificMeasurementStatus
from maestro.models import EvidenceKind

RANKING_NOT_PROBABILITY = "RANKING_NOT_PROBABILITY"
APPROVAL_MISSING, APPROVAL_MISMATCH, SELF_APPROVAL = "APPROVAL_MISSING", "APPROVAL_MISMATCH", "SELF_APPROVAL"
AUTOMATED_APPROVERS = frozenset({"", "agent", "llm", "maestro", "system", "automated"})
DECIDING_KINDS = frozenset({EvidenceKind.REAL_MEASUREMENT, EvidenceKind.DERIVED_ANALYSIS})
DECIDING_STATUSES = frozenset({ScientificMeasurementStatus.QUALIFIED, ScientificMeasurementStatus.UNDETECTED})
RELATIONS = {"<=": lambda v, t: v <= t, ">=": lambda v, t: v >= t, "<": lambda v, t: v < t, ">": lambda v, t: v > t}


class ReviewStatus(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"


class PredictionResult(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNTESTED = "untested"


@dataclass(frozen=True)
class Prediction:
    """What an explanation says one observable must show, e.g. ``secondary_selectivity_z <= -2``."""

    observable: str
    relation: str
    threshold: float

    def __post_init__(self) -> None:
        if not self.observable.strip() or self.relation not in RELATIONS or not math.isfinite(self.threshold):
            raise ValueError("prediction needs an observable, a relation in <=, >=, <, > and a finite threshold")

    def holds(self, value: float) -> bool:
        return RELATIONS[self.relation](value, self.threshold)


@dataclass(frozen=True)
class Explanation:
    identifier: str
    statement: str
    predictions: tuple[Prediction, ...]
    progression: bool = False

    def __post_init__(self) -> None:
        if not self.identifier.strip() or not self.statement.strip():
            raise ValueError("explanation needs an identifier and a statement")
        if not self.predictions:
            raise ValueError(f"explanation {self.identifier} is not falsifiable: it states no prediction")


@dataclass(frozen=True)
class EvidenceItem:
    """One value about one observable, with its origin, status, assay context and source digest."""

    observable: str
    value: float
    kind: EvidenceKind
    status: ScientificMeasurementStatus
    context: str
    source: str
    source_sha256: str
    independent: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.value, ExplorationRanking):
            raise TypeError(RANKING_NOT_PROBABILITY)
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError("evidence value must be a number")
        if not isinstance(self.kind, EvidenceKind) or not isinstance(self.status, ScientificMeasurementStatus):
            raise TypeError("evidence kind and status must be the registered enums")
        if not self.context.strip() or not self.source.strip() or len(self.source_sha256) != 64:
            raise ValueError("evidence needs an assay context, a source and a sha256 digest")


def admit(item: EvidenceItem, context: str) -> tuple[bool, str]:
    """Whether ``item`` may decide a prediction made in assay ``context``, and why not if it may not."""

    if item.kind not in DECIDING_KINDS:
        return False, f"{item.kind.value}_not_admitted_as_decision_evidence"
    if item.status not in DECIDING_STATUSES:
        return False, f"measurement_status_{item.status.value}"
    if not math.isfinite(float(item.value)):
        return False, "non_finite_value"
    if item.context != context:
        return False, f"context_mismatch:{item.context}"
    return True, "admitted"


def evaluate_prediction(prediction: Prediction, evidence: Sequence[EvidenceItem], context: str) -> tuple[PredictionResult, tuple[EvidenceItem, ...]]:
    used = tuple(e for e in evidence if e.observable == prediction.observable and admit(e, context)[0])
    if not used:
        return PredictionResult.UNTESTED, ()
    if all(prediction.holds(float(e.value)) for e in used):
        return PredictionResult.SUPPORTED, used
    return PredictionResult.CONTRADICTED, used


@dataclass(frozen=True)
class DiscriminatingExperiment:
    identifier: str
    observable: str
    cost: int
    turnarounds: int = 1

    def __post_init__(self) -> None:
        if type(self.cost) is not int or self.cost < 1 or type(self.turnarounds) is not int or self.turnarounds < 0:
            raise ValueError("experiment cost must be a positive integer of measurement units")


def discriminating_experiments(explanations: Sequence[Explanation], menu: Sequence[DiscriminatingExperiment]) -> tuple[DiscriminatingExperiment, ...]:
    """Experiments whose observable at least two explanations predict incompatibly, cheapest first."""

    out = []
    for exp in menu:
        below = {e.identifier: p.threshold for e in explanations for p in e.predictions
                 if p.observable == exp.observable and p.relation in ("<=", "<")}
        above = {e.identifier: p.threshold for e in explanations for p in e.predictions
                 if p.observable == exp.observable and p.relation in (">=", ">")}
        if any(a < b for i, a in below.items() for j, b in above.items() if i != j):
            out.append(exp)
    return tuple(sorted(out, key=lambda e: (e.cost, e.turnarounds, e.identifier)))


@dataclass(frozen=True)
class ReviewDecision:
    candidate: str
    status: ReviewStatus
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    results: Mapping[str, Mapping[str, str]]
    experiment: DiscriminatingExperiment | None
    evidence_sha256: tuple[str, ...]
    provenance: Mapping[str, str] = field(default_factory=dict)


def review(candidate: str, explanations: Sequence[Explanation], evidence: Sequence[EvidenceItem], *, context: str,
           funded: bool, menu: Sequence[DiscriminatingExperiment] = (), no_signal: bool = False,
           scope_limitations: Sequence[str] = (), provenance: Mapping[str, str] | None = None) -> ReviewDecision:
    """One progression decision. ``no_signal`` must itself come from admitted evidence (the caller's screen rule)."""

    if len(explanations) < 2:
        raise ValueError("a decision review needs at least two competing explanations")
    if len({e.identifier for e in explanations}) != len(explanations):
        raise ValueError("explanation identifiers must be unique")
    progression = [e for e in explanations if e.progression]
    if len(progression) != 1:
        raise ValueError("exactly one explanation must be the progression explanation")
    results: dict = {}
    for e in explanations:
        results[e.identifier] = {f"{p.observable} {p.relation} {p.threshold:g}": evaluate_prediction(p, evidence, context)[0].value
                                 for p in e.predictions}
    prog = results[progression[0].identifier]
    limitations = [f"untested:{k}" for k, v in prog.items() if v == PredictionResult.UNTESTED.value]
    limitations += sorted({f"not_admitted:{e.observable}:{admit(e, context)[1]}" for e in evidence if not admit(e, context)[0]})
    limitations += list(scope_limitations)
    experiment = None
    if no_signal:
        status, reasons = ReviewStatus.NO_GO, ("NO_SELECTIVE_SIGNAL",)
    elif PredictionResult.CONTRADICTED.value in prog.values():
        status = ReviewStatus.NO_GO
        reasons = tuple(f"CONTRADICTED:{k}" for k, v in prog.items() if v == PredictionResult.CONTRADICTED.value)
    elif funded and PredictionResult.SUPPORTED.value in prog.values():
        status = ReviewStatus.GO
        reasons = tuple(f"SUPPORTED:{k}" for k, v in prog.items() if v == PredictionResult.SUPPORTED.value)
    else:
        status = ReviewStatus.NEED_MORE_EVIDENCE
        options = discriminating_experiments(explanations, menu)
        if not options:
            raise ValueError("NEED_MORE_EVIDENCE must name a discriminating experiment; none in the menu discriminates")
        experiment = options[0]
        reasons = ("NOT_FUNDED" if not funded else "NO_ADMITTED_SUPPORT",)
    used = sorted({e.source_sha256 for e in evidence if admit(e, context)[0]})
    return ReviewDecision(candidate, status, reasons, tuple(limitations), results, experiment, tuple(used), dict(provenance or {}))


def decision_digest(decision: ReviewDecision) -> str:
    payload = asdict(decision)
    payload["status"] = decision.status.value
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExplorationRanking:
    """Order in which to explore candidates. It is a priority, never a probability of validity."""

    order: tuple[str, ...]
    wins: Mapping[str, float]
    matches: int
    method: str

    def as_probability(self):
        raise TypeError(RANKING_NOT_PROBABILITY)

    def __float__(self):
        raise TypeError(RANKING_NOT_PROBABILITY)


def exploration_tournament(candidates: Sequence[str], judge: Callable[[str, str], str], *, rounds: int = 3,
                           seed_order: Sequence[str] | None = None) -> ExplorationRanking:
    """Swiss tournament: each round pairs neighbours by current wins; ``judge(a, b)`` returns the one to explore first.

    A judge that answers with neither candidate forfeits the match for both (no win recorded).
    Ties break by ``seed_order`` (default: the candidates' given order), so the ranking is
    reproducible.
    """

    names = list(dict.fromkeys(candidates))
    seed = list(seed_order) if seed_order is not None else names
    position = {c: seed.index(c) if c in seed else len(seed) + k for k, c in enumerate(names)}
    wins = {c: 0.0 for c in names}
    played: set = set()
    matches = 0
    for _ in range(max(0, rounds)):
        order = sorted(names, key=lambda c: (-wins[c], position[c]))
        free = list(order)
        while len(free) >= 2:
            a = free.pop(0)
            b = next((x for x in free if frozenset((a, x)) not in played), None)
            if b is None:
                continue
            free.remove(b)
            played.add(frozenset((a, b)))
            matches += 1
            winner = judge(a, b)
            if winner in (a, b):
                wins[winner] += 1.0
    order = tuple(sorted(names, key=lambda c: (-wins[c], position[c])))
    return ExplorationRanking(order, dict(wins), matches, f"swiss_{rounds}_rounds")


@dataclass(frozen=True)
class ExperimentRequest:
    candidate: str
    experiment: DiscriminatingExperiment
    requested_by: str
    rationale: str

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Approval:
    request_sha256: str
    approver: str
    note: str = ""


def approve(request: ExperimentRequest, approver: str, note: str = "") -> Approval:
    if approver.strip().lower() in AUTOMATED_APPROVERS:
        raise PermissionError(SELF_APPROVAL)
    return Approval(request.digest(), approver.strip(), note)


def authorize_execution(request: ExperimentRequest, approval: Approval | None, budget: CampaignBudget, *,
                        spent_measurements: int, spent_turnarounds: int) -> float:
    """Cumulative cost after this experiment, or a named refusal; nothing runs without a matching human approval."""

    if approval is None:
        raise PermissionError(APPROVAL_MISSING)
    if approval.request_sha256 != request.digest():
        raise PermissionError(APPROVAL_MISMATCH)
    if approval.approver.strip().lower() in AUTOMATED_APPROVERS or approval.approver == request.requested_by:
        raise PermissionError(SELF_APPROVAL)
    return budget.require_feasible(spent_measurements + request.experiment.cost, spent_turnarounds + request.experiment.turnarounds)
