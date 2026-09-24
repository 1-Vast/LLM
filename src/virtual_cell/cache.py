"""Reuse a supported prediction for an identical biological query.

File summary
- Path: src/virtual_cell/cache.py
- Purpose: stop the agent loop from re-running the same inference every round. A
  multi-round case re-plans each round and re-queries each action; the biological
  query is unchanged, only its tracking metadata moves.
- Core points:
  - The key is every model input (intervention, context, readouts, model version) and
    the serving backend's name. Tracking metadata - request, case, contrast and plan
    version - is excluded, because the interface states it is not a model input.
  - Only an applicable, contract-valid prediction is stored. An abstention is cheap to
    reproduce and may reflect a transient failure, so it is always asked again.
  - A reused prediction is rebound to the new request id, carries zero compute cost and
    names the request whose inference it reuses, so its lineage stays auditable and the
    compute ledger does not bill one inference twice.
- Interfaces: `PredictionCache`, `PredictionCache.key_for`, `.lookup`, `.store`, `.stats`
- Depends on: interface.py
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace

from .interface import PredictionRequest, QueryAssessment, StatePrediction

# Fields of a request that identify *why* it was asked, not *what* was asked.
TRACKING_FIELDS = frozenset({"request_id", "case_id", "contrast_id", "plan_version"})
REUSE_NOTE_PREFIX = "reused_prediction_from_request:"


@dataclass(frozen=True)
class _Entry:
    assessment: QueryAssessment
    prediction: StatePrediction
    origin_request_id: str


class PredictionCache:
    """In-memory, per-controller store of supported predictions keyed by model inputs."""

    def __init__(self, *, max_entries: int = 512):
        if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be a positive integer.")
        self._max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key_for(request: PredictionRequest, backend: str) -> str | None:
        """A stable key over the query's model inputs, or ``None`` for an invalid request."""

        if not isinstance(request, PredictionRequest) or request.validation_errors():
            return None
        payload = {name: value for name, value in request.to_dict().items() if name not in TRACKING_FIELDS}
        payload["backend"] = backend
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def lookup(
        self, request: PredictionRequest, backend: str
    ) -> tuple[QueryAssessment, StatePrediction, str] | None:
        """Return ``(assessment, rebound prediction, origin request id)`` or ``None``."""

        key = self.key_for(request, backend)
        entry = self._entries.get(key) if key is not None else None
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        note = (
            f"{REUSE_NOTE_PREFIX}{entry.origin_request_id}; the identical query was already answered "
            "by this backend in this run, so no new inference was run."
        )
        prediction = replace(
            entry.prediction,
            request_id=request.request_id,
            compute_cost=0.0,
            limitations=tuple(entry.prediction.limitations) + (note,),
        )
        return entry.assessment, prediction, entry.origin_request_id

    def store(
        self,
        request: PredictionRequest,
        backend: str,
        assessment: QueryAssessment,
        prediction: StatePrediction,
    ) -> bool:
        """Keep a supported prediction for reuse; report whether it was stored."""

        if not prediction.applicable or not prediction.contract_valid:
            return False
        if prediction.request_id != getattr(request, "request_id", None):
            return False
        key = self.key_for(request, backend)
        if key is None:
            return False
        if key not in self._entries and len(self._entries) >= self._max_entries:
            # Oldest first: a long run keeps its recent queries, not its first ones.
            self._entries.pop(next(iter(self._entries)))
        self._entries[key] = _Entry(assessment, prediction, request.request_id)
        return True

    def stats(self) -> dict[str, int]:
        return {"entries": len(self._entries), "hits": self.hits, "misses": self.misses}
