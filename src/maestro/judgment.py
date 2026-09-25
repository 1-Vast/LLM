"""A calibrated model judgment, and the ledger that decides whether it may still influence planning.

File summary
- Path: src/maestro/judgment.py
- Purpose: give a typed decision-model answer the same standing MAESTRO already gives a
  virtual-cell prediction: it may rank, warn and advise, and it may never become evidence.
- Core points:
  - A `TypedJudgment` is `model_prediction` by construction. `satisfies_premise`,
    `eliminates_hypothesis` and `is_measurement` are properties that return ``False`` and take
    no arguments, so there is no call site that could make one of them true.
  - `JudgmentScope` names the only things a judgment may touch. `MECHANISM_CONTRAST` is
    deliberately absent: removing an explanation stays the job of a qualified real result read
    through an interpretation rule.
  - `JudgmentLedger` scores probability forecasts against later measured outcomes with a Brier
    score, down-weights a poorly calibrated scope and revokes it. A model that says 0.9 and is
    wrong repeatedly stops steering the plan, which is the same revocation the prediction
    reliability ledger applies to interval misses.
  - A score answer is recorded but never graded: an ordered scale is not a probability forecast,
    and grading it as one would invent a calibration claim the answer never made.
- Interfaces: `JudgmentScope`, `TypedJudgment`, `ScoredJudgment`, `JudgmentSummary`,
  `JudgmentLedger`
- Depends on: maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .models import EvidenceKind

# The Brier score of a forecaster that always answers 0.5. A scope no better than this carries
# no information about the outcome, whatever confidence it reported.
UNINFORMATIVE_BRIER = 0.25


class JudgmentScope(str, Enum):
    """What a judgment is allowed to influence. Nothing here updates an evidence state."""

    PLAN_CRITIQUE = "plan_critique"
    ACTION_RANKING = "action_ranking"
    APPLICABILITY_ADVISORY = "applicability_advisory"
    HYPOTHESIS_ADVISORY = "hypothesis_advisory"


@dataclass(frozen=True)
class TypedJudgment:
    """One typed, calibrated answer bound to the exact state it judged.

    ``state_digest`` is the digest of the text that was sent. It exists so a judgment cannot be
    re-attached to a different plan later and read as though the model had seen it.
    """

    question_id: str
    scope: JudgmentScope
    kind: str
    value: str | int | bool
    model_version: str
    state_digest: str
    probability: float | None = None
    confidence: float | None = None
    limitations: tuple[str, ...] = ()
    context_identifier: str | None = None

    def __post_init__(self) -> None:
        if not str(self.question_id).strip() or not str(self.model_version).strip():
            raise ValueError("invalid_judgment:question_id_and_model_version_required")
        if not isinstance(self.scope, JudgmentScope):
            raise ValueError("invalid_judgment:unknown_scope")
        for name in ("probability", "confidence"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not isfinite(value) or not 0.0 <= value <= 1.0
            ):
                raise ValueError(f"invalid_judgment:{name}_must_be_a_probability")

    @property
    def evidence_kind(self) -> EvidenceKind:
        return EvidenceKind.MODEL_PREDICTION

    @property
    def satisfies_premise(self) -> bool:
        """A judgment never measures anything, so it never satisfies a prerequisite."""

        return False

    @property
    def eliminates_hypothesis(self) -> bool:
        """Only a qualified real result read through an interpretation rule removes an explanation."""

        return False

    @property
    def is_measurement(self) -> bool:
        return False

    @property
    def graded(self) -> bool:
        """Whether this judgment made a probability forecast that a later outcome can score."""

        return self.kind in {"noul", "choice"} and self.probability is not None

    def as_payload(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "scope": self.scope.value,
            "kind": self.kind,
            "value": self.value,
            "probability": self.probability,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "state_digest": self.state_digest,
            "context_identifier": self.context_identifier,
            "evidence_kind": self.evidence_kind.value,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ScoredJudgment:
    """A judgment paired with the measured outcome that later became available."""

    judgment: TypedJudgment
    outcome: bool
    result_id: str
    source_cluster: str | None = None

    @property
    def brier(self) -> float | None:
        if not self.judgment.graded:
            return None
        probability = float(self.judgment.probability or 0.0)
        return (probability - (1.0 if self.outcome else 0.0)) ** 2

    @property
    def confident_miss(self) -> bool:
        """A confident answer that the outcome contradicted."""

        if not self.judgment.graded:
            return False
        probability = float(self.judgment.probability or 0.0)
        return (probability >= 0.75 and not self.outcome) or (probability <= 0.25 and self.outcome)


@dataclass(frozen=True)
class JudgmentSummary:
    scope: str
    records: int
    graded: int
    brier: float | None
    consecutive_misses: int
    weight: float
    revoked: bool
    provisional: bool


class JudgmentLedger:
    """Score a decision model's probability forecasts, and revoke a scope that stops calibrating."""

    def __init__(
        self,
        *,
        minimum_records: int = 5,
        maximum_brier: float = UNINFORMATIVE_BRIER,
        revoke_after: int = 3,
    ):
        if minimum_records < 1 or revoke_after < 1:
            raise ValueError("invalid_ledger_configuration")
        if not isfinite(maximum_brier) or not 0.0 < maximum_brier <= 1.0:
            raise ValueError("invalid_maximum_brier")
        self._minimum_records = minimum_records
        self._maximum_brier = maximum_brier
        self._revoke_after = revoke_after
        self._records: list[ScoredJudgment] = []
        self._seen: set[tuple[str, str, str]] = set()

    @property
    def records(self) -> tuple[ScoredJudgment, ...]:
        return tuple(self._records)

    def record_outcome(
        self,
        judgment: TypedJudgment,
        *,
        outcome: bool,
        result_id: str,
        source_cluster: str | None = None,
    ) -> ScoredJudgment | None:
        """Pair a judgment with a measured outcome once; a repeat is ignored, not counted twice."""

        if not isinstance(outcome, bool):
            raise ValueError("invalid_outcome:a_measured_outcome_must_be_boolean")
        key = (judgment.question_id, judgment.state_digest, source_cluster or result_id)
        if key in self._seen:
            return None
        self._seen.add(key)
        scored = ScoredJudgment(judgment, outcome, result_id, source_cluster)
        self._records.append(scored)
        return scored

    def _scope(self, scope: JudgmentScope, model_version: str, context_identifier: str | None):
        return tuple(
            record
            for record in self._records
            if record.judgment.scope is scope
            and record.judgment.model_version == model_version
            and (context_identifier is None or record.judgment.context_identifier == context_identifier)
        )

    def summarize(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> JudgmentSummary:
        entries = self._scope(scope, model_version, context_identifier)
        graded = [record for record in entries if record.brier is not None]
        brier = sum(record.brier or 0.0 for record in graded) / len(graded) if graded else None

        consecutive = 0
        for record in reversed(graded):
            if record.confident_miss:
                consecutive += 1
            else:
                break

        name = f"{model_version}:{scope.value}"
        if context_identifier:
            name = f"{name}@{context_identifier}"
        common = {
            "scope": name,
            "records": len(entries),
            "graded": len(graded),
            "brier": brier,
            "consecutive_misses": consecutive,
        }
        if len(graded) < self._minimum_records:
            return JudgmentSummary(**common, weight=1.0, revoked=False, provisional=True)
        if consecutive >= self._revoke_after or (brier is not None and brier >= UNINFORMATIVE_BRIER):
            return JudgmentSummary(**common, weight=0.0, revoked=True, provisional=False)
        if brier is not None and brier > self._maximum_brier:
            span = max(1e-9, UNINFORMATIVE_BRIER - self._maximum_brier)
            weight = max(0.0, 1.0 - (brier - self._maximum_brier) / span)
            return JudgmentSummary(**common, weight=weight, revoked=False, provisional=False)
        return JudgmentSummary(**common, weight=1.0, revoked=False, provisional=False)

    def weight(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> float:
        """How much influence this scope still has; 0.0 means the judgments are ignored."""

        return self.summarize(scope, model_version, context_identifier).weight

    def is_revoked(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> bool:
        return self.summarize(scope, model_version, context_identifier).revoked

    def summaries(self) -> tuple[JudgmentSummary, ...]:
        scopes = {
            (record.judgment.scope, record.judgment.model_version, record.judgment.context_identifier)
            for record in self._records
        }
        return tuple(self.summarize(scope, model, context) for scope, model, context in sorted(scopes, key=str))
