"""Reproducibility of a judgment source, measured without waiting for a biological outcome.

File summary
- Path: src/maestro/stability.py
- Purpose: the judgment ledger grades a decision model by Brier score against measured
  outcomes, which are the scarcest and most expensive thing in the system. A source can be
  irreproducible long before any outcome arrives: the live run of 2026-09-25 saw a ranking
  question move between two of five options across two identical calls. This module measures
  that directly, from repeated calls on one unchanged state, and gates influence on it.
- Core points:
  - Agreement is computed on the value that can change a decision - the decided boolean, the
    selected option, the integer level - never on a raw float, because two calls differing in
    the eighth decimal place have not disagreed about anything.
  - The estimator is the unbiased collision probability, sum_v c_v (c_v - 1) / (n (n - 1)):
    the chance that asking again returns the same answer. It is therefore also the weight,
    with no tuning constant standing in for it.
  - Ranking is held to a stricter rule than commentary. A scope that can move which action is
    bought must show reproducibility before it may break a tie; a scope that only produces
    advisory text may speak while unmeasured, carrying its verdict.
  - Below `RELIABLE_REPEATS` the estimate cannot separate a stable source from an unstable one,
    so the verdict is `insufficient` rather than a number presented as if it were settled.
- Interfaces: `RepeatedJudgment`, `StabilityVerdict`, `StabilitySummary`, `StabilityLedger`,
  `canonical_value`, `effective_weight`
- Depends on: maestro.judgment (scopes only)

Derivations and the Monte Carlo that fixed the constants:
`research/analysis/judgment_stability.py`.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Mapping, Sequence

from .judgment import JudgmentScope, TypedJudgment

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
