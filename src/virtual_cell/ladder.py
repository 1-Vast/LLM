"""The swappable world-model ladder, from linear baseline upward.

File summary
- Path: src/virtual_cell/ladder.py
- Purpose: provide the low rungs of the world-model ladder behind the same
  contract as a pretrained model, so a module swap attributes the gain.
- Core points:
  - `LinearPerturbationBaseline` is the rung that deep models must beat.
  - `HierarchicalDoseResponseModel` adds a Hill dose-response per context.
  - Both abstain outside their fitted domain and emit intervals, not points.
- Interfaces: `PerturbationTable`, `LinearPerturbationBaseline`,
  `HierarchicalDoseResponseModel`, `SHUFFLE_CONTROL`.
- Depends on: src/virtual_cell/interface.py, src/virtual_cell/applicability.py
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .applicability import SupportLevel, SupportRecord, SupportRegistry, receipt_level
from .artifacts import vector_sha256, write_shift_artifact
from .receipts import ValidationReceipt
from .interface import (
    Interval,
    IntervalKind,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
)

SHUFFLE_CONTROL = "shuffle_control"


@dataclass(frozen=True)
class PerturbationTable:
    """Aggregated real observations: one row per context x perturbation x dose.

    ``readouts`` names the observed variables globally; ``values`` holds one
    per-row sequence per readout, so a row is a complete observation rather than
    a single cell.
    """

    context_ids: tuple[str, ...]
    perturbations: tuple[str, ...]
    modes: tuple[str, ...]
    doses: tuple[float, ...]
    times: tuple[float, ...]
    readouts: tuple[str, ...]
    values: Mapping[str, Sequence[float]]
    source: str = "table"

    def rows(self) -> list[Mapping[str, object]]:
        """Row-level metadata for auditing and domain construction."""

        return [
            {
                "context_id": context,
                "perturbation": perturbation,
                "mode": mode,
                "dose": dose,
                "time_hours": time,
            }
            for context, perturbation, mode, dose, time in zip(
                self.context_ids,
                self.perturbations,
                self.modes,
                self.doses,
                self.times,
                strict=True,
            )
        ]

    def support(self, *, interpolate_over: Sequence[str] = ()) -> SupportRegistry:
        """Derive the fitted domain from the rows actually observed.

        ``interpolate_over`` carries the caller's declared interpolation claim. The
        dose-aware rungs declare the dose axis, because that is what they fit; a rung
        with no dose axis must leave it empty rather than inherit the claim.
        """

        registry = SupportRegistry.from_table(
            self.rows(), source=self.source, interpolate_over=interpolate_over
        )
        for record in registry.records:
            registry.register(
                SupportRecord(
                    context_id=record.context_id,
                    perturbations=record.perturbations,
                    modes=record.modes,
                    readouts=frozenset(self.readouts),
                    dose_range=record.dose_range,
                    time_range=record.time_range,
                    observations=record.observations,
                    source=record.source,
                )
            )
        return registry


def _design_matrix(
    table: PerturbationTable, contexts: Sequence[str], perturbations: Sequence[str]
) -> np.ndarray:
    log_dose = np.log1p(np.asarray(table.doses, dtype=float)).reshape(-1, 1)
    context_block = np.array(
        [[1.0 if context == name else 0.0 for name in contexts] for context in table.context_ids],
        dtype=float,
    )
    perturbation_block = np.array(
        [[1.0 if pert == name else 0.0 for name in perturbations] for pert in table.perturbations],
        dtype=float,
    )
    return np.hstack([context_block, perturbation_block, log_dose])


@dataclass
class LinearPerturbationBaseline:
    """Ridge regression on context, perturbation and log dose.

    This is deliberately the rung that a pretrained model must beat: if the
    pretrained model does not improve action ranking over this, it is withdrawn
    rather than reported as a contribution.

    Its fitted domain declares interpolation on the dose axis, because the rung fits a
    dose coefficient: a dose inside the range observed for that (context, perturbation)
    is a condition it is fitted for, while a dose outside the range, an unobserved
    perturbation or an unobserved context is refused by name.
    """

    table: PerturbationTable
    model_version: str = "linear_baseline"
    regularization: float = 1e-3
    interval_level: float = 0.9
    _support: SupportRegistry | None = field(default=None, init=False, repr=False)
    _coefficients: dict[str, np.ndarray] = field(default_factory=dict, init=False, repr=False)
    _residual_scale: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _contexts: tuple[str, ...] = field(default=(), init=False, repr=False)
    _perturbations: tuple[str, ...] = field(default=(), init=False, repr=False)

    def __post_init__(self) -> None:
        self.fit()

    @property
    def name(self) -> str:
        return self.model_version

    def fit(self) -> "LinearPerturbationBaseline":
        self._support = self.table.support(interpolate_over=("dose",))
        self._contexts = tuple(sorted(set(self.table.context_ids)))
        self._perturbations = tuple(sorted(set(self.table.perturbations)))
        design = _design_matrix(self.table, self._contexts, self._perturbations)
        penalty = self.regularization * np.eye(design.shape[1])
        for readout, values in self.table.values.items():
            target = np.asarray(values, dtype=float)
            solution = np.linalg.solve(design.T @ design + penalty, design.T @ target)
            self._coefficients[readout] = solution
            residual = target - design @ solution
            scale = float(np.std(residual)) if residual.size > 1 else 0.0
            self._residual_scale[readout] = scale if isfinite(scale) and scale > 0 else 1e-6
        return self

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="linear_perturbation_baseline",
            model_version=self.model_version,
            input_representation="context one-hot + perturbation one-hot + log1p(dose)",
            perturbation_representation="registered perturbation identifier",
            supported_modes=tuple(sorted(set(self.table.modes))) or ("drug",),
            requires_matched_control=True,
            supports_dose=True,
            supports_time=False,
            calibration_basis="residual scale on the fitted table",
        )

    def _row(self, request: PredictionRequest) -> np.ndarray | None:
        if self._support is None or not self._contexts:
            return None
        context = request.context.identifier
        perturbation = request.intervention.identifier
        if context not in self._contexts or perturbation not in self._perturbations:
            return None
        dose = float(request.intervention.dose or 0.0)
        row = [
            [1.0 if context == name else 0.0 for name in self._contexts]
            + [1.0 if perturbation == name else 0.0 for name in self._perturbations]
            + [float(np.log1p(dose))]
        ]
        return np.asarray(row, dtype=float)

    def _verdict(self, request: PredictionRequest):
        assert self._support is not None
        return self._support.assess(
            context_id=request.context.identifier,
            perturbation=request.intervention.identifier,
            mode=request.intervention.mode,
            dose=request.intervention.dose,
            time_hours=request.intervention.time_hours,
            readouts=tuple(request.readouts),
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        if self._support is None:
            return QueryAssessment(QuerySupport.UNSUPPORTED, ("model_not_fitted",), (), self.capabilities())
        verdict = self._verdict(request)
        if not verdict.in_distribution:
            return QueryAssessment(
                QuerySupport.UNSUPPORTED, (), (verdict.abstain_reason or "out_of_domain",), self.capabilities()
            )
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return _abstain(request, ", ".join(assessment.limitations) or "out_of_domain")
        row = self._row(request)
        if row is None:
            return _abstain(request, "prediction_row_unavailable")
        z = 1.645 if abs(self.interval_level - 0.9) < 1e-9 else 1.96
        state_change: dict[str, float] = {}
        intervals: dict[str, Interval] = {}
        for readout, coefficients in self._coefficients.items():
            value = float((row @ coefficients).item())
            scale = self._residual_scale.get(readout, 1e-6)
            state_change[readout] = value
            # The residual scale of a rung on its own training rows is a
            # dispersion, not a measured coverage. Labelling it CALIBRATED let
            # an unvalidated band carry the authority of a coverage claim, so
            # the band stays descriptive until a coverage receipt exists.
            intervals[readout] = Interval(
                value - z * scale,
                value + z * scale,
                kind=IntervalKind.DESCRIPTIVE,
                basis="residual scale of this rung on its own training rows; no held-out coverage has been measured",
            )
        spread = _spread(intervals)
        return StatePrediction(
            applicable=True,
            state_change=state_change,
            uncertainty=spread,
            limitations=(
                "Linear baseline prediction for planning only; it is not measured evidence and does not establish mechanism.",
            ),
            supported_variables=tuple(sorted(self._coefficients)),
            calibration_basis="residual scale on the fitted table",
            request_id=request.request_id,
            model_version=self.model_version,
            intervals=intervals,
            # No calibrated confidence exists here: the only width available is
            # the residual dispersion on the fit's own rows, and compressing it
            # into 1/(1+width) would hand an invented number the authority of a
            # calibrated one (F07). The contract path is an absent confidence
            # plus named unquantified sources.
            confidence=None,
            in_distribution=True,
            compute_cost=0.1,
            uncertainty_components={
                "predictor_randomness": "none: the ridge fit is deterministic given the table",
                "measurement_noise": "unquantified: residual scale on the fit's own rows is a dispersion, not a held-out coverage",
                "model_misspecification": "structural: linear features cannot express a nonlinear dose response",
            },
        )


@dataclass
class HierarchicalDoseResponseModel:
    """Per-context Hill curve with a residual-derived interval.

    Dose is the confounder that a purely linear model mishandles, and the reason
    a nominal dose is not a functional inhibition level.

    The fitted domain declares interpolation on the dose axis for the same reason: the
    rung exists to answer at a dose between the ones it was fitted on, and it refuses a
    (context, perturbation) pair whose curve could not be fitted at all.
    """

    table: PerturbationTable
    model_version: str = "hierarchical_dose_response"
    interval_level: float = 0.9
    minimum_points: int = 4
    _curves: dict[tuple[str, str, str], tuple[float, float, float, float]] = field(
        default_factory=dict, init=False, repr=False
    )
    _scales: dict[tuple[str, str, str], float] = field(default_factory=dict, init=False, repr=False)
    _support: SupportRegistry | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.fit()

    @property
    def name(self) -> str:
        return self.model_version

    def fit(self) -> "HierarchicalDoseResponseModel":
        self._support = self.table.support(interpolate_over=("dose",))
        grouped: dict[tuple[str, str, str], list[tuple[float, float]]] = {}
        for readout in self.table.readouts:
            values = self.table.values.get(readout)
            if values is None:
                continue
            for index in range(len(self.table.context_ids)):
                key = (self.table.context_ids[index], self.table.perturbations[index], readout)
                grouped.setdefault(key, []).append((float(self.table.doses[index]), float(values[index])))
        for key, points in grouped.items():
            if len(points) < self.minimum_points:
                continue
            points.sort()
            doses = np.array([item[0] for item in points], dtype=float)
            observed = np.array([item[1] for item in points], dtype=float)
            parameters, scale = _fit_hill(doses, observed)
            if parameters is None:
                continue
            self._curves[key] = parameters
            self._scales[key] = scale
        return self

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="hierarchical_dose_response",
            model_version=self.model_version,
            input_representation="context + perturbation + dose",
            perturbation_representation="registered perturbation identifier",
            supported_modes=tuple(sorted(set(self.table.modes))) or ("drug",),
            requires_matched_control=True,
            supports_dose=True,
            supports_time=False,
            calibration_basis="Hill curve residual scale per context and perturbation",
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        if self._support is None:
            return QueryAssessment(QuerySupport.UNSUPPORTED, (), ("model_not_fitted",), self.capabilities())
        verdict = self._support.assess(
            context_id=request.context.identifier,
            perturbation=request.intervention.identifier,
            mode=request.intervention.mode,
            dose=request.intervention.dose,
            time_hours=request.intervention.time_hours,
            readouts=tuple(request.readouts),
        )
        if not verdict.in_distribution:
            return QueryAssessment(
                QuerySupport.UNSUPPORTED, (), (verdict.abstain_reason or "out_of_domain",), self.capabilities()
            )
        missing = [
            readout
            for readout in request.readouts
            if (request.context.identifier, request.intervention.identifier, readout) not in self._curves
        ]
        if missing:
            return QueryAssessment(
                QuerySupport.UNSUPPORTED,
                (),
                (f"insufficient_dose_points:{','.join(sorted(missing))}",),
                self.capabilities(),
            )
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return _abstain(request, ", ".join(assessment.limitations) or "out_of_domain")
        z = 1.645 if abs(self.interval_level - 0.9) < 1e-9 else 1.96
        dose = float(request.intervention.dose or 0.0)
        state_change: dict[str, float] = {}
        intervals: dict[str, Interval] = {}
        for readout in request.readouts:
            key = (request.context.identifier, request.intervention.identifier, readout)
            baseline, top, log_ec50, hill = self._curves[key]
            value = _hill(baseline, top, log_ec50, hill, dose)
            scale = self._scales.get(key, 1e-6)
            state_change[readout] = value
            intervals[readout] = Interval(
                value - z * scale,
                value + z * scale,
                kind=IntervalKind.DESCRIPTIVE,
                basis="residual scale of the fitted curve for this group; no held-out coverage has been measured",
            )
        spread = _spread(intervals)
        return StatePrediction(
            applicable=True,
            state_change=state_change,
            uncertainty=spread,
            limitations=(
                "Hill dose-response prediction for planning only; it is not measured evidence and does not establish mechanism.",
            ),
            supported_variables=tuple(sorted(state_change)),
            calibration_basis="Hill curve residual scale per context and perturbation",
            request_id=request.request_id,
            model_version=self.model_version,
            intervals=intervals,
            # Same contract as the linear rung: a per-group residual dispersion
            # is not a calibrated confidence, so none is claimed (F07).
            confidence=None,
            in_distribution=True,
            compute_cost=0.2,
            uncertainty_components={
                "predictor_randomness": "none: the grid fit is deterministic given the table",
                "measurement_noise": "unquantified: per-group residual scale is a dispersion, not a held-out coverage",
                "model_misspecification": "structural: a four-parameter Hill curve is monotone by construction",
            },
        )


def shuffled(world_model, *, seed: int = 7) -> "ShuffledWorldModel":
    """Return the shuffled-prediction control for a module swap."""

    return ShuffledWorldModel(world_model, seed=seed)


class ShuffledWorldModel:
    """Same model, permuted outputs: measures whether the prediction carries signal."""

    def __init__(self, inner, *, seed: int = 7):
        self._inner = inner
        self._rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return f"{getattr(self._inner, 'name', type(self._inner).__name__)}:shuffled"

    def capabilities(self) -> ModelCapabilities:
        return self._inner.capabilities()

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        return self._inner.assess_query(request)

    def predict(self, request: PredictionRequest) -> StatePrediction:
        original = self._inner.predict(request)
        if not original.applicable or not original.state_change:
            return original
        values = np.array(list(original.state_change.values()), dtype=float)
        permuted = self._rng.permutation(values)
        state_change = dict(zip(original.state_change, (float(item) for item in permuted), strict=True))
        return StatePrediction(
            applicable=True,
            state_change=state_change,
            uncertainty=original.uncertainty,
            limitations=original.limitations + (SHUFFLE_CONTROL,),
            supported_variables=original.supported_variables,
            calibration_basis=None,
            request_id=original.request_id,
            model_version=original.model_version,
            intervals=original.intervals,
            confidence=original.confidence,
            in_distribution=original.in_distribution,
            compute_cost=original.compute_cost,
            # An absent confidence stays contract-valid only while the named
            # unquantified sources travel with the shuffled output.
            uncertainty_components=original.uncertainty_components,
        )


def _hill(baseline: float, top: float, log_ec50: float, hill: float, dose: float) -> float:
    if dose <= 0:
        return baseline
    ratio = (dose / np.exp(log_ec50)) ** hill
    return baseline + (top - baseline) * ratio / (1.0 + ratio)


def _fit_hill(doses: np.ndarray, observed: np.ndarray) -> tuple[tuple[float, float, float, float] | None, float]:
    """Grid-search a four-parameter Hill curve; returns parameters and residual scale.

    Non-finite observations are dropped before fitting. Leaving them in would
    turn every comparison against NaN false and silently discard the curve.
    """

    finite = np.isfinite(doses) & np.isfinite(observed)
    doses, observed = doses[finite], observed[finite]
    if doses.size < 4 or np.allclose(doses, doses[0]):
        return None, 0.0
    positive = doses[doses > 0]
    if positive.size == 0:
        return None, 0.0
    best = None
    baseline_guess = float(observed[doses == 0].mean()) if np.any(doses == 0) else float(observed.min())
    top_guess = float(observed.max())
    for log_ec50 in np.log(np.geomspace(max(positive.min(), 1e-6), max(positive.max(), 1e-5), num=12)):
        for hill in (0.5, 1.0, 2.0, 4.0):
            for top in (top_guess, baseline_guess - (top_guess - baseline_guess)):
                fitted = np.array([_hill(baseline_guess, top, log_ec50, hill, dose) for dose in doses])
                scale = float(np.std(observed - fitted))
                if best is None or scale < best[0]:
                    best = (scale, (baseline_guess, top, log_ec50, hill))
    if best is None:
        return None, 0.0
    scale, parameters = best
    return parameters, scale if isfinite(scale) and scale > 0 else 1e-6


def _spread(intervals: Mapping[str, Interval]) -> float:
    if not intervals:
        return 0.0
    return float(sum(interval.width for interval in intervals.values()) / len(intervals))


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
