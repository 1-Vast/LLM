"""Frozen, condition-bound backend preferences; file identity is not scientific certification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
import re

from virtual_cell.interface import PredictionRequest


@dataclass(frozen=True)
class BackendPreference:
    backend: str
    model_version: str
    context_identifier: str
    dataset_id: str | None
    readouts: tuple[str, ...]
    mode: str
    dose: float | None
    dose_unit: str | None
    time_hours: float | None
    calibration_id: str
    reference_units: int
    compute_cost: float

    def __post_init__(self) -> None:
        for value in (self.backend, self.model_version, self.context_identifier, self.mode, self.calibration_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("routing preference requires named identity and calibration")
        if (not isinstance(self.readouts, tuple) or not self.readouts
                or any(not isinstance(x, str) or not x.strip() for x in self.readouts)
                or len(set(self.readouts)) != len(self.readouts)):
            raise ValueError("routing readouts must be a nonempty tuple of unique names")
        if type(self.reference_units) is not int or self.reference_units < 1:
            raise ValueError("routing support must count positive independent reference units")
        for value in (self.compute_cost, self.dose, self.time_hours):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or not isfinite(value) or value < 0):
                raise ValueError("routing costs and conditions must be finite and nonnegative")
        if self.compute_cost is None:
            raise ValueError("routing compute cost must be declared")
        if (self.dose is None) != (self.dose_unit is None):
            raise ValueError("routing dose and unit must be declared together")
        for value in (self.dataset_id, self.dose_unit):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError("invalid routing dataset or dose unit")

    def matches(self, request: PredictionRequest) -> bool:
        """Exact declared scope; an unknown condition never stands for all conditions."""
        intervention = request.intervention
        return (
            request.model_version == self.model_version
            and request.context.identifier == self.context_identifier
            and request.context.dataset_id == self.dataset_id
            and set(request.readouts) == set(self.readouts)
            and intervention.mode == self.mode
            and intervention.dose == self.dose and intervention.dose_unit == self.dose_unit
            and intervention.time_hours == self.time_hours
        )


@dataclass(frozen=True)
class BackendRoutingPolicy:
    """Reference preferences supplied outside the LLM, applied after backend eligibility.

    Independent-unit support, then declared compute cost, then backend name break
    ties. The receipt must be prepared from qualifying reference evaluations;
    verifying its bytes and scope does not establish calibration or model benefit.
    """

    identifier: str
    source_sha256: str
    preferences: tuple[BackendPreference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError("routing policy requires an identifier")
        if not isinstance(self.source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("routing policy requires a SHA256 source identity")
        if not isinstance(self.preferences, tuple) or not self.preferences:
            raise ValueError("routing policy requires frozen preferences")
        if any(not isinstance(p, BackendPreference) for p in self.preferences):
            raise ValueError("invalid routing preference")

    @classmethod
    def from_receipt(cls, path: Path, expected_sha256: str) -> BackendRoutingPolicy:
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError("routing_receipt_hash_mismatch")
        document = json.loads(raw)
        preferences = tuple(BackendPreference(**{**item, "readouts": tuple(item["readouts"])})
                            for item in document["preferences"])
        return cls(document["identifier"], expected_sha256, preferences)

    @property
    def identity(self) -> str:
        """All routing inputs enter cache identity, including declared support and cost."""
        payload = asdict(self)
        payload["preferences"] = sorted(payload["preferences"], key=lambda x: json.dumps(x, sort_keys=True))
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def ranked(self, request: PredictionRequest, eligible: set[str]) -> tuple[BackendPreference, ...]:
        return tuple(sorted((p for p in self.preferences if p.backend in eligible and p.matches(request)),
                            key=lambda p: (-p.reference_units, p.compute_cost, p.backend, p.calibration_id)))
