"""Revocable dependence on a virtual-cell prediction, scored against later real measurement results.

File summary
- Path: src/maestro/reliability.py
- Purpose: Track per-readout prediction calibration and revoke it when it fails.
- Core points:
  - `PredictionReliabilityLedger` scores predictions against realised values for the same readout.
  - A prediction is only a tie-breaker; revocation never edits the evidence ledger.
  - Consecutive misses revoke the readout; too few records keep the default weight.
- Interfaces: `PredictionReliabilityLedger`, `record_pair`, `summarize`, `weight`, `ScoredPrediction`, `ReliabilitySummary`
- Depends on: (standard library only)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


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
        entries = self._scope(model_version, readout, context_identifier)
        scored = [entry for entry in entries if entry.scored]
        graded = [entry for entry in scored if entry.interval_hit is not None]
        hits = sum(1 for entry in graded if entry.interval_hit)
        misses = len(graded) - hits
        miss_rate = (misses / len(graded)) if graded else None

        consecutive = 0
        for entry in reversed(graded):
            if entry.interval_hit is False:
                consecutive += 1
            else:
                break

        scope = f"{model_version}:{readout}"
        if context_identifier:
            scope = f"{scope}@{context_identifier}"
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
