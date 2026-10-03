"""Typed model advice with calibration, prediction reliability, and repeatability ledgers.

Model advice can influence planning; only qualified measurements update evidence."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Mapping, Sequence

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


@dataclass(frozen=True)
class ScoredPrediction:
    """One prediction paired with the real value that later became available.

    ``interval`` is reserved for bands that claim coverage (a calibrated
    interval with a declared level and basis); only those are graded by
    ``interval_hit``.  ``descriptive_interval`` keeps a descriptive spread or a
    point-plus-minus-scalar band visible without letting it acquire coverage
    semantics it never earned (audit F07 residual).
    """

    model_version: str
    readout: str
    context_identifier: str | None
    predicted_value: float | None
    interval: tuple[float, float] | None
    realized_value: float | None
    request_id: str | None = None
    action_identifier: str | None = None
    descriptive_interval: tuple[float, float] | None = None
    source_cluster: str | None = None
    result_id: str | None = None
    time_hours: float | None = None
    condition_fingerprint: str | None = None

    @property
    def scored(self) -> bool:
        return all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
            for value in (self.predicted_value, self.realized_value)
        )

    @property
    def interval_hit(self) -> bool | None:
        """``True`` when the real value fell inside the declared interval."""

        if self.interval is None or not self.scored:
            return None
        low, high = self.interval
        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
            for value in (low, high)
        ) or low > high:
            return None
        return low <= self.realized_value <= high


@dataclass(frozen=True)
class ReliabilitySummary:
    scope: str
    records: int
    scored: int
    interval_hits: int
    miss_rate: float | None
    consecutive_misses: int
    weight: float
    revoked: bool
    provisional: bool


class PredictionReliabilityLedger:
    """Track calibration per model version and readout, and revoke when it fails."""

    def __init__(
        self,
        *,
        minimum_records: int = 3,
        maximum_miss_rate: float = 0.5,
        revoke_after_consecutive_misses: int = 3,
    ):
        if minimum_records < 1:
            raise ValueError("minimum_records must be positive.")
        if not 0.0 <= maximum_miss_rate <= 1.0:
            raise ValueError("maximum_miss_rate must lie in [0, 1].")
        self._minimum_records = minimum_records
        self._maximum_miss_rate = maximum_miss_rate
        self._revoke_after = revoke_after_consecutive_misses
        self._records: list[ScoredPrediction] = []

    @property
    def records(self) -> tuple[ScoredPrediction, ...]:
        return tuple(self._records)

    @property
    def policy(self) -> Mapping[str, object]:
        """Version the deterministic aggregation rule used for persisted scores."""
        return {"version": "prediction_reliability_v1", "minimum_records": self._minimum_records,
                "maximum_miss_rate": self._maximum_miss_rate,
                "revoke_after_consecutive_misses": self._revoke_after}

    def record(self, entry: ScoredPrediction) -> ScoredPrediction:
        for existing in self._records:
            if existing.model_version != entry.model_version or existing.readout != entry.readout:
                continue
            if entry.result_id is not None and existing.result_id == entry.result_id:
                return existing
            if entry.source_cluster and (
                existing.context_identifier,
                existing.source_cluster,
                existing.time_hours,
                existing.condition_fingerprint,
            ) == (
                entry.context_identifier,
                entry.source_cluster,
                entry.time_hours,
                entry.condition_fingerprint,
            ):
                return existing
        self._records.append(entry)
        return entry

    def record_pair(
        self,
        *,
        model_version: str,
        readout: str,
        predicted_value: float | None,
        realized_value: float | None,
        interval: tuple[float, float] | None = None,
        descriptive_interval: tuple[float, float] | None = None,
        context_identifier: str | None = None,
        request_id: str | None = None,
        action_identifier: str | None = None,
        source_cluster: str | None = None,
        result_id: str | None = None,
        time_hours: float | None = None,
        condition_fingerprint: str | None = None,
    ) -> ScoredPrediction:
        return self.record(
            ScoredPrediction(
                model_version=model_version,
                readout=readout,
                context_identifier=context_identifier,
                predicted_value=predicted_value,
                interval=interval,
                realized_value=realized_value,
                request_id=request_id,
                action_identifier=action_identifier,
                descriptive_interval=descriptive_interval,
                source_cluster=source_cluster,
                result_id=result_id,
                time_hours=time_hours,
                condition_fingerprint=condition_fingerprint,
            )
        )

    def _scope(self, model_version: str, readout: str, context_identifier: str | None):
        return tuple(
            entry
            for entry in self._records
            if entry.model_version == model_version
            and entry.readout == readout
            and (context_identifier is None or entry.context_identifier == context_identifier)
        )

    def weight(
        self, model_version: str, readout: str, context_identifier: str | None = None
    ) -> float:
        """How much planning influence this readout's prediction still has."""

        return self.summarize(model_version, readout, context_identifier).weight

    def is_revoked(self, model_version: str, readout: str, context_identifier: str | None = None) -> bool:
        """Return whether this readout's prediction has been revoked for the scope."""

        return self.summarize(model_version, readout, context_identifier).revoked

    def summarize(
        self, model_version: str, readout: str, context_identifier: str | None = None
    ) -> ReliabilitySummary:
        """Summarise the graded record for one scope.

        Scope behaviour, stated exactly. With a ``context_identifier``, only
        that context's records count. With ``None``, the records of *every*
        context (and of no context) are pooled under one summary, and the scope
        string says so (``model:readout@all-contexts``). Two consequences of
        pooling, both deliberate but neither silent:

        - A revocation in any one context revokes the pooled scope. For a gate
          this is the conservative direction: it fails closed.
        - The pooled miss rate can *hide* a local failure -- one context missing
          every prediction and another covering everything averages to 0.5,
          which crosses no threshold. The consecutive-miss rule does not have
          this blind spot: it is evaluated per context within the scope and
          fires when any single context's run reaches the revocation length.
        """

        entries = self._scope(model_version, readout, context_identifier)
        scored = [entry for entry in entries if entry.scored]
        graded = [entry for entry in scored if entry.interval_hit is not None]
        hits = sum(1 for entry in graded if entry.interval_hit)
        misses = len(graded) - hits
        miss_rate = (misses / len(graded)) if graded else None

        # Longest current miss run, counted per context inside the scope. One
        # pooled sequence would let another context's hits break a failing
        # context's run and hide a local failure.
        streaks: dict[str | None, int] = {}
        for entry in graded:
            key = entry.context_identifier
            streaks[key] = streaks.get(key, 0) + 1 if entry.interval_hit is False else 0
        consecutive = max(streaks.values(), default=0)

        scope = f"{model_version}:{readout}"
        if context_identifier:
            scope = f"{scope}@{context_identifier}"
        else:
            scope = f"{scope}@all-contexts"
        if len(graded) < self._minimum_records:
            return ReliabilitySummary(
                scope=scope,
                records=len(entries),
                scored=len(scored),
                interval_hits=hits,
                miss_rate=miss_rate,
                consecutive_misses=consecutive,
                weight=1.0,
                revoked=False,
                provisional=True,
            )
        if consecutive >= self._revoke_after:
            return ReliabilitySummary(
                scope=scope,
                records=len(entries),
                scored=len(scored),
                interval_hits=hits,
                miss_rate=miss_rate,
                consecutive_misses=consecutive,
                weight=0.0,
                revoked=True,
                provisional=False,
            )
        if miss_rate is not None and miss_rate > self._maximum_miss_rate:
            span = max(1e-9, 1.0 - self._maximum_miss_rate)
            weight = max(0.0, 1.0 - (miss_rate - self._maximum_miss_rate) / span)
            return ReliabilitySummary(
                scope=scope,
                records=len(entries),
                scored=len(scored),
                interval_hits=hits,
                miss_rate=miss_rate,
                consecutive_misses=consecutive,
                weight=weight,
                revoked=False,
                provisional=False,
            )
        return ReliabilitySummary(
            scope=scope,
            records=len(entries),
            scored=len(scored),
            interval_hits=hits,
            miss_rate=miss_rate,
            consecutive_misses=consecutive,
            weight=1.0,
            revoked=False,
            provisional=False,
        )

    def summaries(self) -> tuple[ReliabilitySummary, ...]:
        scopes = {(entry.model_version, entry.readout, entry.context_identifier) for entry in self._records}
        return tuple(
            self.summarize(model, readout, context) for model, readout, context in sorted(scopes, key=str)
        )


# Two calls are enough to notice a disagreement and not enough to measure a rate.
MINIMUM_REPEATS = 2
# Below this, a gate at STABLE_AGREEMENT catches under half of a uniformly random source while
# a 0.95-stable source is essentially never revoked: the test has no power, not no risk.
RELIABLE_REPEATS = 8
# Verified in research/analysis/judgment_stability.py: at eight repeats this threshold revokes
# a 0.95-stable source in 0.000 of runs and catches a three-way random source in 0.737.
STABLE_AGREEMENT = 0.6
# The scopes that can change which action is bought, rather than only what is said about it.
DECIDING_SCOPES = frozenset({JudgmentScope.ACTION_RANKING})


class StabilityVerdict(str, Enum):
    """What repetition has established about a scope so far."""

    UNMEASURED = "unmeasured"          # one observation: nothing was asked twice
    INSUFFICIENT = "insufficient"      # repeated, but too few to separate stable from unstable
    STABLE = "stable"
    UNSTABLE = "unstable"


def canonical_value(kind: str, value: object) -> str:
    """The part of an answer that can change a decision, as a comparable string.

    A noul answer decides by its boolean, not by the probability behind it, so two calls at
    0.94 and 0.77 agree. A score decides by its integer level. A choice decides by the option
    named. Comparing raw floats instead would report every source as unstable.
    """

    if value is None:
        return "<none>"
    if kind == "noul":
        return "true" if bool(value) else "false"
    if kind == "score":
        return str(int(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
    return str(value)


@dataclass(frozen=True)
class RepeatedJudgment:
    """One question asked several times against one unchanged state."""

    question_id: str
    scope: JudgmentScope
    kind: str
    model_version: str
    state_digest: str
    values: tuple[str, ...]
    probabilities: tuple[float, ...] = ()
    context_identifier: str | None = None

    def __post_init__(self) -> None:
        if not self.question_id.strip() or not self.state_digest.strip():
            raise ValueError("invalid_repeat:question_and_state_digest_required")
        if not self.values:
            raise ValueError("invalid_repeat:no_observations")
        if any(not isfinite(p) for p in self.probabilities):
            raise ValueError("invalid_repeat:probability_must_be_finite")

    @property
    def repeats(self) -> int:
        return len(self.values)

    @property
    def counts(self) -> Mapping[str, int]:
        return dict(Counter(self.values))

    @property
    def modal_value(self) -> str:
        """The most frequent answer; ties break on the value itself so this is deterministic."""

        counts = self.counts
        return max(sorted(counts), key=lambda name: counts[name])

    @property
    def agreement(self) -> float | None:
        """The chance that asking once more returns the same answer.

        The unbiased estimator of the collision probability sum_v p_v^2 for a multinomial
        sample, verified in the analysis script. `None` when nothing was asked twice.
        """

        n = self.repeats
        if n < MINIMUM_REPEATS:
            return None
        return sum(c * (c - 1) for c in self.counts.values()) / (n * (n - 1))

    @property
    def flip_rate(self) -> float | None:
        """How often two identical calls disagree: the share of decisions that would not repeat."""

        agreement = self.agreement
        return None if agreement is None else 1.0 - agreement

    @property
    def probability_variance(self) -> float | None:
        """Sample variance of the reported probability, which is the Brier penalty for instability.

        `E[Brier] = q(1-q) + (mu - q)^2 + sigma^2`, so this term is charged to the source and
        needs no outcome to compute.
        """

        values = [p for p in self.probabilities]
        if len(values) < 2:
            return None
        mean = sum(values) / len(values)
        return sum((p - mean) ** 2 for p in values) / (len(values) - 1)

    def averaging_gain(self, repeats: int | None = None) -> float | None:
        """Brier saved by answering with the mean of n calls instead of one: sigma^2 (1 - 1/n)."""

        variance = self.probability_variance
        n = repeats or self.repeats
        return None if variance is None or n < 1 else variance * (1.0 - 1.0 / n)

    @property
    def verdict(self) -> StabilityVerdict:
        agreement = self.agreement
        if agreement is None:
            return StabilityVerdict.UNMEASURED
        if agreement < STABLE_AGREEMENT:
            return StabilityVerdict.UNSTABLE
        if self.repeats < RELIABLE_REPEATS:
            return StabilityVerdict.INSUFFICIENT
        return StabilityVerdict.STABLE

    def as_payload(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "scope": self.scope.value,
            "kind": self.kind,
            "model_version": self.model_version,
            "state_digest": self.state_digest,
            "context_identifier": self.context_identifier,
            "repeats": self.repeats,
            "distinct_values": sorted(self.counts),
            # The empirical selection frequencies. These are not the distribution the model
            # reports for itself: measured over 12 identical calls the two differed by half
            # again, so the reported vector cannot stand in for reproducibility.
            "value_counts": dict(sorted(self.counts.items())),
            "modal_value": self.modal_value,
            "agreement": self.agreement,
            "flip_rate": self.flip_rate,
            "probability_variance": self.probability_variance,
            "verdict": self.verdict.value,
        }


@dataclass(frozen=True)
class StabilitySummary:
    """What repetition has established about one scope of one model version."""

    scope: str
    observations: int
    repeats: int
    agreement: float | None
    flip_rate: float | None
    verdict: StabilityVerdict
    weight: float
    revoked: bool
    may_decide: bool

    def as_payload(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "observations": self.observations,
            "repeats": self.repeats,
            "agreement": self.agreement,
            "flip_rate": self.flip_rate,
            "verdict": self.verdict.value,
            "weight": self.weight,
            "revoked": self.revoked,
            "may_decide": self.may_decide,
        }


class StabilityLedger:
    """Hold repeated judgments and say what influence reproducibility has earned each scope."""

    def __init__(self, *, stable_agreement: float = STABLE_AGREEMENT, reliable_repeats: int = RELIABLE_REPEATS):
        if not 0.0 < stable_agreement <= 1.0:
            raise ValueError("invalid_stability_configuration:stable_agreement")
        if reliable_repeats < MINIMUM_REPEATS:
            raise ValueError("invalid_stability_configuration:reliable_repeats")
        self._stable_agreement = stable_agreement
        self._reliable_repeats = reliable_repeats
        self._records: list[RepeatedJudgment] = []

    @property
    def records(self) -> tuple[RepeatedJudgment, ...]:
        return tuple(self._records)

    def record(self, repeated: RepeatedJudgment) -> RepeatedJudgment:
        self._records.append(repeated)
        return repeated

    def _scope(self, scope: JudgmentScope, model_version: str, context_identifier: str | None):
        return tuple(
            record
            for record in self._records
            if record.scope is scope
            and record.model_version == model_version
            and (context_identifier is None or record.context_identifier == context_identifier)
        )

    def summarize(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> StabilitySummary:
        entries = self._scope(scope, model_version, context_identifier)
        name = f"{model_version}:{scope.value}"
        if context_identifier:
            name = f"{name}@{context_identifier}"
        measured = [record for record in entries if record.agreement is not None]
        repeats = sum(record.repeats for record in measured)
        if not measured:
            # Nothing was asked twice. An advisory scope may still speak; a scope that can move
            # which action is bought may not, because no influence has been earned.
            return StabilitySummary(
                name, len(entries), repeats, None, None, StabilityVerdict.UNMEASURED,
                weight=1.0, revoked=False, may_decide=scope not in DECIDING_SCOPES,
            )
        # Pool the pairs rather than average the rates, so a long run is not outvoted by a short one.
        agreeing = sum((record.agreement or 0.0) * record.repeats * (record.repeats - 1) for record in measured)
        pairs = sum(record.repeats * (record.repeats - 1) for record in measured)
        agreement = agreeing / pairs if pairs else None
        if agreement is None:
            verdict = StabilityVerdict.UNMEASURED
        elif agreement < self._stable_agreement:
            verdict = StabilityVerdict.UNSTABLE
        elif repeats < self._reliable_repeats:
            verdict = StabilityVerdict.INSUFFICIENT
        else:
            verdict = StabilityVerdict.STABLE
        revoked = verdict is StabilityVerdict.UNSTABLE
        return StabilitySummary(
            name,
            len(entries),
            repeats,
            agreement,
            None if agreement is None else 1.0 - agreement,
            verdict,
            # The weight is the measured chance the advice survives being asked again. There is
            # no tuning constant here: a source that reproduces 0.7 of the time counts 0.7.
            weight=0.0 if revoked else float(agreement or 1.0),
            revoked=revoked,
            may_decide=verdict is StabilityVerdict.STABLE or (
                verdict is not StabilityVerdict.UNSTABLE and scope not in DECIDING_SCOPES
            ),
        )

    def weight(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> float:
        return self.summarize(scope, model_version, context_identifier).weight

    def is_revoked(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> bool:
        return self.summarize(scope, model_version, context_identifier).revoked

    def may_decide(
        self, scope: JudgmentScope, model_version: str, context_identifier: str | None = None
    ) -> bool:
        """Whether this scope has earned the right to change which action is selected."""

        return self.summarize(scope, model_version, context_identifier).may_decide

    def summaries(self) -> tuple[StabilitySummary, ...]:
        scopes = {(r.scope, r.model_version, r.context_identifier) for r in self._records}
        return tuple(self.summarize(scope, model, context) for scope, model, context in sorted(scopes, key=str))


def effective_weight(calibration: float, stability: float) -> float:
    """Influence a scope retains under both tests, which is the weaker of the two.

    Calibration and reproducibility fail independently: a source can be well calibrated on
    average while answering differently each time, and can be perfectly repeatable while
    being repeatably wrong. Neither excuses the other, so the smaller weight governs.
    """

    for value in (calibration, stability):
        if not isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("invalid_weight:must_be_a_finite_fraction")
    return min(calibration, stability)


def group_judgments(judgments: Sequence[TypedJudgment]) -> dict[str, list[TypedJudgment]]:
    """Group answers to the same question about the same state, which is what repeats are."""

    grouped: dict[str, list[TypedJudgment]] = {}
    for judgment in judgments:
        grouped.setdefault(f"{judgment.question_id}@{judgment.state_digest}", []).append(judgment)
    return grouped
