"""Observed condition shifts from a registered asset, and the backend fitted on them.

File summary
- Path: src/virtual_cell/transcript_baselines.py
- Purpose: compute measured perturbation shifts of named conditions directly from a registered data asset, bound to its digest, and fit the development-mean backend on a declared development partition only.
- Core points:
  - A partition is a declared object with its own digest; the baseline is fitted on exactly the conditions it names and refuses the rest of them at query time.
  - Shifts are computed inside the declared context against the exact control label; there is no substring matching.
  - These observations fit a planning backend; this module never produces evidence for a case.
- Interfaces: `DevelopmentPartition`, `load_partition`, `observed_condition_shifts`, `fit_development_mean_baseline`
- Depends on: h5py, numpy, virtual_cell.state_adapter, virtual_cell.ladder, virtual_cell.artifacts
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .artifacts import load_feature_names
from .ladder import DevelopmentMeanShiftBaseline
from .state_adapter import DatasetRegistration, file_sha256


@dataclass(frozen=True)
class DevelopmentPartition:
    """Which conditions a fitted component may learn from, and by what rule."""

    dataset_id: str
    context_identifier: str
    unit: str
    rule: str
    development_conditions: tuple[str, ...]
    held_out_conditions: tuple[str, ...] = ()
    source: str = ""

    @property
    def sha256(self) -> str:
        return hashlib.sha256("\n".join(sorted(self.development_conditions)).encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, object]:
        return {
            "schema": "maestro.development_partition.v1",
            "dataset_id": self.dataset_id,
            "context_identifier": self.context_identifier,
            "unit": self.unit,
            "rule": self.rule,
            "development_conditions": list(self.development_conditions),
            "held_out_conditions": list(self.held_out_conditions),
            "development_partition_sha256": self.sha256,
            "source": self.source,
        }


def load_partition(path: Path) -> DevelopmentPartition:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    partition = DevelopmentPartition(
        dataset_id=str(data["dataset_id"]),
        context_identifier=str(data["context_identifier"]),
        unit=str(data["unit"]),
        rule=str(data["rule"]),
        development_conditions=tuple(str(item) for item in data["development_conditions"]),
        held_out_conditions=tuple(str(item) for item in data.get("held_out_conditions", ())),
        source=str(data.get("source", "")),
    )
    declared = data.get("development_partition_sha256")
    if declared and declared != partition.sha256:
        raise ValueError("The partition file's declared digest does not match its development conditions.")
    overlap = set(partition.development_conditions) & set(partition.held_out_conditions)
    if overlap:
        raise ValueError(f"Conditions are both development and held out: {sorted(overlap)[:5]}")
    return partition


def _strings(item) -> np.ndarray:
    import h5py

    if isinstance(item, h5py.Group) and "categories" in item:
        return np.asarray(item["categories"].asstr()[:])[item["codes"][:]]
    return np.asarray(item.asstr()[:]) if item.dtype.kind in "OS" else item[:].astype(str)


def observed_condition_shifts(
    registration: DatasetRegistration,
    conditions: Sequence[str],
    *,
    context_identifier: str,
) -> tuple[Mapping[str, np.ndarray], Mapping[str, int]]:
    """Measured mean shift of each named condition against the context's controls."""

    import h5py

    if not registration.sha256 or file_sha256(registration.path) != registration.sha256:
        raise ValueError(f"Dataset '{registration.identifier}' does not match its registered digest.")
    if registration.contexts and context_identifier not in registration.contexts:
        raise ValueError(f"Context '{context_identifier}' is not registered for '{registration.identifier}'.")
    with h5py.File(registration.path, "r") as handle:
        labels = _strings(handle["obs"][registration.perturbation_column])
        contexts = _strings(handle["obs"][registration.context_column])
        in_context = contexts == context_identifier
        control_rows = np.flatnonzero(in_context & (labels == registration.control_label))
        if control_rows.size == 0:
            raise ValueError("The declared context has no rows with the exact control label.")
        wanted = set(conditions)
        selected = np.flatnonzero(in_context & np.isin(labels, sorted(wanted)))
        rows = np.union1d(control_rows, selected)
        matrix = np.asarray(handle["obsm"][registration.embedding_key][rows], dtype=np.float64)
    position = {row: index for index, row in enumerate(rows)}
    control_mean = matrix[[position[row] for row in control_rows]].mean(axis=0)
    shifts: dict[str, np.ndarray] = {}
    counts: dict[str, int] = {}
    for condition in conditions:
        members = [position[row] for row in selected if labels[row] == condition]
        if not members:
            continue
        shifts[condition] = matrix[members].mean(axis=0) - control_mean
        counts[condition] = len(members)
    return shifts, counts


def fit_development_mean_baseline(
    registration: DatasetRegistration,
    partition: DevelopmentPartition,
    *,
    artifact_directory: Path | None = None,
    model_version: str = "development_mean_shift_v1",
) -> DevelopmentMeanShiftBaseline:
    """Fit the development-mean backend from measured shifts of the partition's conditions."""

    if partition.dataset_id != registration.identifier:
        raise ValueError("The partition names a different dataset than the registration.")
    shifts, _ = observed_condition_shifts(
        registration, partition.development_conditions, context_identifier=partition.context_identifier
    )
    missing = [item for item in partition.development_conditions if item not in shifts]
    if missing:
        raise ValueError(f"Development conditions absent from the asset: {missing[:5]}")
    feature_count = len(next(iter(shifts.values())))
    names, _ = load_feature_names(registration.feature_names_path, feature_count)
    return DevelopmentMeanShiftBaseline.fit(
        shifts,
        development_conditions=partition.development_conditions,
        feature_names=names,
        context_identifier=partition.context_identifier,
        dataset_id=registration.identifier,
        fitted_on=(
            f"measured shifts in {registration.identifier} (sha256 {registration.sha256[:12]}), "
            f"partition {partition.sha256[:12]}: {partition.rule}"
        ),
        model_version=model_version,
        artifact_directory=artifact_directory,
    )
