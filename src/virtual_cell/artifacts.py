"""Compact, hash-bound condition-level prediction artifacts.

File summary
- Path: src/virtual_cell/artifacts.py
- Purpose: write one backend's answer to one query as a small, self-describing
  record — the numbers, which coordinate each number is, what was asked, which
  model produced it from which inputs — so a planning step can cite it and an
  auditor can recompute its digest.
- Core points:
  - Coordinates are named where a verified identity exists and are listed as
    explicitly unresolved where it does not; no name is guessed.
  - Raw and calibrated values are stored side by side; a calibration never
    overwrites what the model returned.
  - Every artifact declares itself planning-only and not a measurement.
- Interfaces: `vector_sha256`, `write_shift_artifact`, `load_feature_names`
- Depends on: numpy
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

ARTIFACT_SCHEMA = "maestro.condition_shift.v1"


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
