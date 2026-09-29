"""Development-only transcript baseline fitted from registered matched controls."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
import numpy as np
from .applicability import SupportLevel, receipt_level, ValidationReceipt
from .artifacts import vector_sha256, write_shift_artifact, load_feature_names
from .interface import ModelCapabilities, PredictionRequest, QueryAssessment, QuerySupport, StatePrediction
from .state_adapter import DatasetRegistration, file_sha256


def _abstain(request: PredictionRequest, reason: str) -> StatePrediction:
    return StatePrediction(
        applicable=False,
        state_change=None,
        uncertainty=None,
        limitations=(reason,),
        request_id=request.request_id,
        model_version=request.model_version,
        confidence=None,
        in_distribution=False,
        abstain_reason=reason,
        compute_cost=0.0,
    )


SHIFT_ENDPOINT = "x_hvg_perturbation_shift"
SHIFT_SUMMARIES = ("embedding_delta_l2", "mean_absolute_embedding_delta")


@dataclass(frozen=True)
class DevelopmentMeanShiftBaseline:
    """A computed backend: the mean observed shift over development conditions only.

    It returns the same vector for every held-out condition, so it carries the
    response conditions share and nothing about the requested perturbation.
    That is what makes it the rung a pretrained model has to beat on the shift
    endpoint, and what makes a substitution test meaningful: it is fitted from
    real measurements through a declared partition, not a fixture under a
    different name. It refuses the conditions it was fitted on, so none of its
    answers is in-sample.
    """

    mean_shift: tuple[float, ...]
    feature_names: tuple[str | None, ...]
    development_conditions: frozenset[str]
    context_identifier: str
    dataset_id: str
    fitted_on: str
    endpoint: str = SHIFT_ENDPOINT
    model_version: str = "development_mean_shift_v1"
    fitted_vector_sha256: str = ""
    development_partition_sha256: str = ""
    artifact_directory: Path | None = None
    validation_receipts: tuple[ValidationReceipt, ...] = ()

    @classmethod
    def fit(
        cls,
        shifts: Mapping[str, Sequence[float]],
        *,
        development_conditions: Sequence[str],
        feature_names: Sequence[str | None],
        context_identifier: str,
        dataset_id: str,
        fitted_on: str,
        endpoint: str = SHIFT_ENDPOINT,
        model_version: str = "development_mean_shift_v1",
        artifact_directory: Path | None = None,
        validation_receipts: Sequence[ValidationReceipt] = (),
    ) -> "DevelopmentMeanShiftBaseline":
        development = tuple(dict.fromkeys(str(item) for item in development_conditions))
        if not development:
            raise ValueError("A development mean needs at least one development condition.")
        absent = [item for item in development if item not in shifts]
        if absent:
            raise ValueError(f"Development conditions without an observed shift: {absent[:5]}")
        names = tuple(feature_names)
        matrix = np.asarray([np.asarray(shifts[item], dtype=float) for item in development], dtype=float)
        if matrix.ndim != 2 or matrix.shape[1] != len(names):
            raise ValueError("Every development shift must have one value per declared feature.")
        mean = matrix.mean(axis=0)
        partition = hashlib.sha256("\n".join(sorted(development)).encode("utf-8")).hexdigest()
        return cls(
            mean_shift=tuple(float(value) for value in mean),
            feature_names=names,
            development_conditions=frozenset(development),
            context_identifier=context_identifier,
            dataset_id=dataset_id,
            fitted_on=f"{fitted_on} ({len(development)} development conditions)",
            endpoint=endpoint,
            model_version=model_version,
            fitted_vector_sha256=vector_sha256(mean),
            development_partition_sha256=partition,
            artifact_directory=artifact_directory,
            validation_receipts=tuple(validation_receipts),
        )

    @property
    def name(self) -> str:
        return self.model_version

    @property
    def served_readouts(self) -> tuple[str, ...]:
        return (self.endpoint, *SHIFT_SUMMARIES)

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="development_mean_shift_baseline",
            model_version=self.model_version,
            input_representation="none: the fitted vector does not read the query's cells",
            perturbation_representation="ignored: every held-out condition receives the same vector",
            supported_modes=("drug",),
            requires_matched_control=True,
            supports_dose=False,
            supports_time=False,
            calibration_basis=None,
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        missing: list[str] = []
        limitations: list[str] = []
        if request.model_version != self.model_version:
            missing.append("matching model_version")
        if request.intervention.mode != "drug":
            limitations.append(f"modality_unsupported:{request.intervention.mode}")
        if not request.readouts:
            limitations.append("no_readout_requested")
        limitations.extend(
            f"readout_not_served:{readout}" for readout in request.readouts if readout not in self.served_readouts
        )
        if request.context.identifier != self.context_identifier:
            limitations.append(f"context_not_registered_for_dataset:{request.context.identifier}")
        if request.context.dataset_id != self.dataset_id:
            limitations.append(f"dataset_not_fitted:{request.context.dataset_id}")
        if request.context.control_dataset_id != self.dataset_id:
            limitations.append(f"control_dataset_not_matched_to_input:{request.context.control_dataset_id}")
        if request.intervention.identifier in self.development_conditions:
            limitations.append("query_condition_in_fitting_partition")
        supported = not missing and not limitations
        status, notes = SupportLevel.UNKNOWN, ()
        if supported and self.validation_receipts:
            level, notes = receipt_level(
                self.validation_receipts,
                endpoints=tuple(request.readouts),
                context_identifier=request.context.identifier,
                model_version=self.model_version,
            )
            status = SupportLevel.UNKNOWN if level is SupportLevel.OBSERVED_SUPPORT else level
        return QueryAssessment(
            QuerySupport.SUPPORTED if supported else QuerySupport.UNSUPPORTED,
            tuple(missing),
            tuple(limitations),
            self.capabilities(),
            status,
            tuple(notes),
        )

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return _abstain(request, "; ".join((*assessment.limitations, *assessment.missing_inputs)) or "out_of_domain")
        vector = np.asarray(self.mean_shift, dtype=float)
        limitations = (
            "Planning-only computed baseline: the mean observed shift over the declared development conditions. "
            "It is not a measurement of the requested condition and ignores the perturbation's identity.",
        )
        artifact_ref: str | None = None
        artifact_sha: str | None = None
        if self.artifact_directory is not None:
            path = self.artifact_directory / f"{request.request_id}.{self.model_version}.shift.json"
            artifact_sha = write_shift_artifact(
                path,
                request_id=request.request_id,
                backend=self.name,
                model_version=self.model_version,
                endpoint=self.endpoint,
                context_identifier=request.context.identifier,
                perturbation=request.intervention.identifier,
                control_label=None,
                raw_vector=vector,
                calibrated_vector=None,
                feature_names=self.feature_names,
                feature_identity_sha256=None,
                provenance={
                    "fitted_on": self.fitted_on,
                    "development_partition_sha256": self.development_partition_sha256,
                    "fitted_vector_sha256": self.fitted_vector_sha256,
                    "dataset_id": self.dataset_id,
                },
                limitations=limitations,
            )
            artifact_ref = str(path)
        return StatePrediction(
            applicable=True,
            state_change={
                "embedding_delta_l2": float(np.linalg.norm(vector)),
                "mean_absolute_embedding_delta": float(np.abs(vector).mean()) if vector.size else 0.0,
            },
            uncertainty=None,
            limitations=limitations,
            supported_variables=self.served_readouts,
            calibration_basis=None,
            request_id=request.request_id,
            model_version=self.model_version,
            artifact_ref=artifact_ref,
            intervals={},
            confidence=None,
            in_distribution=assessment.validation_status is not SupportLevel.UNKNOWN,
            compute_cost=0.001,
            artifact_sha256=artifact_sha,
            uncertainty_components={
                "predictor_randomness": "none: the fitted vector is deterministic",
                "measurement_noise": "unquantified: development condition means carry cell-sampling and well noise",
                "batch_effects": "unquantified: plate composition of the development partition is not modelled",
                "model_misspecification": "structural: the vector ignores which perturbation was requested",
                "training_overlap": "none for served conditions: conditions in the fitting partition are refused",
            },
        )




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
    control_mean = matrix[np.searchsorted(rows, control_rows)].mean(axis=0)
    members_by_condition: dict[str, list[int]] = {}
    for position, condition in zip(np.searchsorted(rows, selected), labels[selected], strict=True):
        members_by_condition.setdefault(str(condition), []).append(int(position))
    shifts: dict[str, np.ndarray] = {}
    counts: dict[str, int] = {}
    for condition in conditions:
        members = members_by_condition.get(condition, ())
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
