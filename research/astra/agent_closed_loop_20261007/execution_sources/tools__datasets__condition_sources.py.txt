"""Exact declared condition/source metadata lookup; no biological state inference."""
from dataclasses import asdict, dataclass
import json
import math
from numbers import Real
from pathlib import Path


def _dose(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
        raise ValueError("dose must be a finite nonnegative non-boolean number")


def _hash(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("source_sha256 must be a lowercase SHA-256 hex digest")


@dataclass(frozen=True)
class ConditionSource:
    context: str
    label: str
    drug: str
    dose: float
    unit: str
    source_group: str
    source_reference: str
    source_sha256: str

    def __post_init__(self):
        _dose(self.dose)
        for name in ("context", "label", "drug", "unit", "source_group", "source_reference"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonempty string")
        _hash(self.source_sha256)


@dataclass(frozen=True)
class SourceResolution:
    candidates: tuple[ConditionSource, ...]
    status: str


def resolve_condition_sources(sources, *, context, drug, dose=None, unit=None,
                              label=None, source_group=None, source_reference=None,
                              source_sha256=None):
    """Match literal identities; never choose the first source or infer missing dose/unit."""
    if dose is not None:
        _dose(dose)
    if source_sha256 is not None:
        _hash(source_sha256)
    selectors = dict(context=context, drug=drug, unit=unit, label=label,
                     source_group=source_group, source_reference=source_reference,
                     source_sha256=source_sha256)
    for name, value in selectors.items():
        if (name in ("context", "drug") or value is not None) and (
                not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be a nonempty string")
    candidates = tuple(s for s in sources if (dose is None or s.dose == dose)
                       and all(value is None or getattr(s, name) == value
                               for name, value in selectors.items()))
    if not candidates:
        status = "no_registered_source"
    elif dose is None or unit is None:
        status = "clarify_requested_dose_and_unit"
    elif len(candidates) > 1:
        status = "resolve_source_identity"
    else:
        status = "resolved"
    return SourceResolution(candidates, status)


def run(parameters):
    """Read a JSON list of declared source records, preserving each supplied source identity."""
    parameters = dict(parameters)
    path = Path(parameters.pop("dataset_path"))
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("dataset must be a JSON list of source records")
    result = resolve_condition_sources(tuple(ConditionSource(**row) for row in rows), **parameters)
    return {"schema_version": "1.0", "payload": {
        "status": result.status, "candidates": [asdict(s) for s in result.candidates]},
        "observations": [f"Exact declared-source lookup: {result.status}; {len(result.candidates)} candidates."],
        "limitations": ["Declared metadata only; source hashes are retained, not authenticated against raw bytes.",
                        "No measured target state, response, prediction, or biological decision benefit is established."],
        "artifacts": []}
