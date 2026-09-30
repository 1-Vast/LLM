"""Prediction artifacts, feature identities and cell-context marker checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence
import numpy as np
from dataclasses import dataclass, field


ARTIFACT_SCHEMA = "maestro.condition_shift.v1"
_DIGESTS: dict[tuple[str, int, int], str] = {}


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file's bytes."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def cached_file_sha256(path: Path) -> str:
    """Reuse an asset digest while its path, size and modification time are unchanged."""

    path = Path(path)
    metadata = path.stat()
    key = (str(path.resolve()), metadata.st_size, metadata.st_mtime_ns)
    if key not in _DIGESTS:
        _DIGESTS[key] = file_sha256(path)
    return _DIGESTS[key]


def vector_sha256(values: Sequence[float] | np.ndarray) -> str:
    """Digest of the float64 little-endian bytes, independent of file formatting."""

    array = np.ascontiguousarray(np.asarray(values, dtype="<f8"))
    return hashlib.sha256(array.tobytes()).hexdigest()


def load_feature_names(path: Path | None, feature_count: int) -> tuple[tuple[str | None, ...], str | None]:
    """Per-coordinate names from a verified identity file, or all unresolved.

    The file must list exactly one entry per coordinate, ``null`` where the
    coordinate could not be identified. Anything else is refused rather than
    aligned by position, because a shifted name list silently mislabels every
    coordinate after the shift.
    """

    if path is None or not Path(path).is_file():
        return tuple([None] * feature_count), None
    raw = Path(path).read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    names = payload.get("names") if isinstance(payload, dict) else None
    if not isinstance(names, list) or len(names) != feature_count:
        raise ValueError(
            f"Feature identity file {path} does not list exactly {feature_count} coordinates."
        )
    return tuple(str(name) if isinstance(name, str) and name else None for name in names), hashlib.sha256(raw).hexdigest()


def write_shift_artifact(
    path: Path,
    *,
    request_id: str,
    backend: str,
    model_version: str,
    endpoint: str,
    context_identifier: str,
    perturbation: str,
    control_label: str | None,
    raw_vector: Sequence[float] | np.ndarray,
    calibrated_vector: Sequence[float] | np.ndarray | None,
    feature_names: Sequence[str | None],
    feature_identity_sha256: str | None,
    provenance: Mapping[str, object],
    limitations: Sequence[str],
) -> str:
    """Write the artifact and return the SHA-256 of the file bytes."""

    raw = np.asarray(raw_vector, dtype=float)
    if raw.ndim != 1 or raw.shape[0] != len(feature_names):
        raise ValueError("The shift vector and the feature list must have the same length.")
    calibrated = None if calibrated_vector is None else np.asarray(calibrated_vector, dtype=float)
    if calibrated is not None and calibrated.shape != raw.shape:
        raise ValueError("Raw and calibrated vectors must have the same shape.")
    unresolved = [index for index, name in enumerate(feature_names) if name is None]
    payload = {
        "schema": ARTIFACT_SCHEMA,
        "planning_only": True,
        "is_measurement": False,
        "request_id": request_id,
        "backend": backend,
        "model_version": model_version,
        "endpoint": endpoint,
        "context_identifier": context_identifier,
        "perturbation": perturbation,
        "control_label": control_label,
        "coordinates": len(feature_names),
        "feature_names": list(feature_names),
        "unresolved_coordinates": unresolved,
        "feature_identity_sha256": feature_identity_sha256,
        "raw": {
            "values": [float(value) for value in raw],
            "sha256_float64": vector_sha256(raw),
            "l2_norm": float(np.linalg.norm(raw)),
            "mean_absolute": float(np.abs(raw).mean()) if raw.size else 0.0,
        },
        "calibrated": None
        if calibrated is None
        else {
            "values": [float(value) for value in calibrated],
            "sha256_float64": vector_sha256(calibrated),
            "l2_norm": float(np.linalg.norm(calibrated)),
            "mean_absolute": float(np.abs(calibrated).mean()) if calibrated.size else 0.0,
        },
        "provenance": dict(provenance),
        "limitations": list(limitations),
    }
    encoded = (json.dumps(payload, indent=1, sort_keys=False, allow_nan=False) + "\n").encode("utf-8")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Written as bytes: text mode would translate line endings on Windows, and
    # the recorded digest would then describe bytes that are not on disk.
    Path(path).write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()




# Context -> genes expressed there far above the other two contexts. K562 is an erythroleukemia
# line expressing embryonic and fetal globins with GATA1; MCF7 is a luminal, estrogen-receptor
# positive breast line; A549 carries a KEAP1 loss that keeps NRF2 targets constitutively high.
IDENTITY_MARKERS: Mapping[str, tuple[str, ...]] = {
    "K562": ("HBG1", "HBG2", "HBZ", "GATA1"),
    "MCF7": ("TFF1", "KRT19", "GATA3", "ESR1"),
    "A549": ("AKR1C1", "AKR1B10", "NQO1", "ALDH3A1"),
}


@dataclass(frozen=True)
class MarkerCheck:
    """How many declared markers peak in their expected context under one label offset."""

    offset: int
    tested: int
    peaked_in_expected_context: int
    untestable: tuple[str, ...]
    peaks: Mapping[str, str] = field(default_factory=dict)

    @property
    def fraction(self) -> float:
        return self.peaked_in_expected_context / self.tested if self.tested else 0.0

    def passed(self, *, minimum_fraction: float = 0.9, minimum_tested: int = 6) -> bool:
        return self.tested >= minimum_tested and self.fraction >= minimum_fraction

    def payload(self) -> dict[str, object]:
        return {"offset": self.offset, "tested": self.tested,
                "peaked_in_expected_context": self.peaked_in_expected_context,
                "untestable": list(self.untestable), "peaks": dict(self.peaks)}


def shift_labels(labels: Sequence[str | None], offset: int, columns: int) -> list[str | None]:
    """The label of each column under an offset: column j takes label row j + offset.

    A column whose label row falls outside the table is unlabelled (None), never borrowed.
    """

    return [labels[j + offset] if 0 <= j + offset < len(labels) else None for j in range(columns)]


def check_markers(
    means: Mapping[str, np.ndarray],
    labels: Sequence[str | None],
    *,
    offset: int = 0,
    markers: Mapping[str, Sequence[str]] = IDENTITY_MARKERS,
) -> MarkerCheck:
    """Test one offset: a marker passes when its column is highest in the marker's context.

    ``means`` maps a context to per-column mean expression; ``labels`` is the label table as
    published. A marker is untestable when its label is absent, when its column falls outside
    the matrix, when its context has no means, or when its column is zero everywhere.
    """

    contexts = [c for c in means]
    if not contexts:
        raise ValueError("marker_check_needs_context_means")
    columns = {len(np.asarray(v)) for v in means.values()}
    if len(columns) != 1:
        raise ValueError("marker_check_context_means_differ_in_length")
    width = columns.pop()
    row = {}
    for index, label in enumerate(labels):
        if label is not None:
            row.setdefault(label, index)
    tested = passed = 0
    untestable: list[str] = []
    peaks: dict[str, str] = {}
    for context, genes in markers.items():
        for gene in genes:
            column = row.get(gene, -1) - offset if gene in row else -1
            if context not in means or not 0 <= column < width:
                untestable.append(gene)
                continue
            values = {c: float(np.asarray(means[c])[column]) for c in contexts}
            if max(values.values()) <= 0.0:
                untestable.append(gene)
                continue
            winner = max(values, key=lambda c: (values[c], c))
            peaks[gene] = winner
            tested += 1
            passed += int(winner == context)
    return MarkerCheck(offset, tested, passed, tuple(untestable), peaks)


def resolve_label_offset(
    means: Mapping[str, np.ndarray],
    labels: Sequence[str | None],
    *,
    offsets: Sequence[int] = (-1, 0, 1),
    markers: Mapping[str, Sequence[str]] = IDENTITY_MARKERS,
    minimum_fraction: float = 0.9,
    minimum_tested: int = 6,
) -> tuple[int | None, tuple[MarkerCheck, ...], str | None]:
    """Choose the offset the markers support, or refuse by name.

    Returns ``(offset, checks, refusal)``. Exactly one passing offset is required: none means the
    labels cannot be trusted at any tested alignment, several means the markers cannot decide.
    """

    checks = tuple(check_markers(means, labels, offset=o, markers=markers) for o in offsets)
    passing = [c for c in checks if c.passed(minimum_fraction=minimum_fraction, minimum_tested=minimum_tested)]
    if not passing:
        return None, checks, "feature_labels_fail_identity_markers"
    if len(passing) > 1:
        return None, checks, "feature_label_offset_ambiguous"
    return passing[0].offset, checks, None
