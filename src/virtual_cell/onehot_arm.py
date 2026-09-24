"""The zero-information arm: entity identity only, with the informative axis removed.

File summary
- Path: src/virtual_cell/onehot_arm.py
- Purpose: supply the one-hot ablation the combination-prediction literature made
  mandatory. Until this arm exists beside the ladder, a ladder result cannot be read,
  because nothing separates "the model learned a dose response" from "the model learned
  which entities were involved".
- Core points:
  - This repository's ladder is *already* identity-one-hot: `_design_matrix` encodes
    context and perturbation as indicator columns and carries no molecular or
    cell-line featurisation. So the arm that answers the published question here is
    not "replace features with one-hot" -- there are no features to replace -- but
    "remove the one informative axis the rungs do carry", which is dose.
  - Two behaviours on an unseen entity are offered and reported separately: abstain,
    which is this framework's contract, and fall back to the training mean, which is
    what the published models did under leave-drug-out. Reporting one and not the
    other would either flatter the contract or misdescribe the literature.
  - It is a control, never a candidate. Its intervals stay descriptive, and it
    declares no calibration basis it does not have.
- Interfaces: `OneHotIdentityBaseline`
- Depends on: virtual_cell.ladder (the table, the abstention and spread helpers),
  virtual_cell.applicability, virtual_cell.interface
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

import numpy as np

from .applicability import SupportRegistry
from .interface import (
    Interval,
    IntervalKind,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
)
from .ladder import PerturbationTable, _abstain, _spread

ONE_HOT_ARM = "one_hot_identity_baseline"


@dataclass
class OneHotIdentityBaseline:
    """Ridge on context and perturbation indicators only: no dose, no features.

    ``fall_back_to_training_mean`` selects what happens to an entity the fit never
    saw. With it False the rung abstains, which is the behaviour the rest of this
    framework requires of a model outside its domain. With it True the rung answers
    the training mean, which is what the published one-hot models did under
    leave-drug-out and is therefore the arm that reproduces the published finding.
    """

    table: PerturbationTable
    model_version: str = ONE_HOT_ARM
    regularization: float = 1e-3
    interval_level: float = 0.9
    fall_back_to_training_mean: bool = False
    _support: SupportRegistry | None = field(default=None, init=False, repr=False)
    _coefficients: dict[str, np.ndarray] = field(default_factory=dict, init=False, repr=False)
    _residual_scale: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _training_mean: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _training_spread: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _contexts: tuple[str, ...] = field(default=(), init=False, repr=False)
    _perturbations: tuple[str, ...] = field(default=(), init=False, repr=False)

    def __post_init__(self) -> None:
        self.fit()

    @property
    def name(self) -> str:
        return self.model_version if not self.fall_back_to_training_mean else f"{self.model_version}:mean_fallback"

    def _design(self, contexts, perturbations) -> np.ndarray:
        """Indicator columns only. The absence of a dose column is the ablation."""

        context_block = np.array(
            [[1.0 if item == name else 0.0 for name in contexts] for item in self.table.context_ids],
            dtype=float,
        )
        perturbation_block = np.array(
            [[1.0 if item == name else 0.0 for name in perturbations] for item in self.table.perturbations],
            dtype=float,
        )
        return np.hstack([context_block, perturbation_block])

    def fit(self) -> "OneHotIdentityBaseline":
        self._support = self.table.support()
        self._contexts = tuple(sorted(set(self.table.context_ids)))
        self._perturbations = tuple(sorted(set(self.table.perturbations)))
        design = self._design(self._contexts, self._perturbations)
        penalty = self.regularization * np.eye(design.shape[1])
        for readout, values in self.table.values.items():
            target = np.asarray(values, dtype=float)
            solution = np.linalg.solve(design.T @ design + penalty, design.T @ target)
            self._coefficients[readout] = solution
            residual = target - design @ solution
            scale = float(np.std(residual)) if residual.size > 1 else 0.0
            self._residual_scale[readout] = scale if isfinite(scale) and scale > 0 else 1e-6
            mean = float(np.mean(target)) if target.size else 0.0
            spread = float(np.std(target)) if target.size > 1 else 0.0
            self._training_mean[readout] = mean
            self._training_spread[readout] = spread if isfinite(spread) and spread > 0 else 1e-6
        return self

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="one_hot_identity_baseline",
            model_version=self.model_version,
            input_representation="context one-hot + perturbation one-hot; the dose axis is removed",
            perturbation_representation="zero-information indicator of the registered identifier",
            supported_modes=tuple(sorted(set(self.table.modes))) or ("drug",),
            requires_matched_control=True,
            supports_dose=False,
            supports_time=False,
            calibration_basis="residual scale on the fitted table",
        )

    def _known(self, request: PredictionRequest) -> bool:
        return (
            request.context.identifier in self._contexts
            and request.intervention.identifier in self._perturbations
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        if self._support is None or not self._contexts:
            return QueryAssessment(
                QuerySupport.UNSUPPORTED, ("model_not_fitted",), (), self.capabilities()
            )
        if self._known(request):
            return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())
        if self.fall_back_to_training_mean:
            # The published behaviour: answer anyway, from the training mean. It is
            # supported only because the arm declares that it will do this.
            return QueryAssessment(
                QuerySupport.SUPPORTED,
                (),
                ("answered_from_the_training_mean:entity_not_in_the_fit",),
                self.capabilities(),
            )
        return QueryAssessment(
            QuerySupport.UNSUPPORTED, (), ("entity_not_in_the_fit",), self.capabilities()
        )

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return _abstain(request, ", ".join(assessment.limitations) or "out_of_domain")
        z = 1.645 if abs(self.interval_level - 0.9) < 1e-9 else 1.96
        known = self._known(request)
        state_change: dict[str, float] = {}
        intervals: dict[str, Interval] = {}
        for readout, coefficients in self._coefficients.items():
            if known:
                row = np.asarray(
                    [
                        [1.0 if request.context.identifier == name else 0.0 for name in self._contexts]
                        + [
                            1.0 if request.intervention.identifier == name else 0.0
                            for name in self._perturbations
                        ]
                    ],
                    dtype=float,
                )
                value = float((row @ coefficients).item())
                scale = self._residual_scale.get(readout, 1e-6)
                basis = "residual scale of this arm on its own training rows; no held-out coverage measured"
            else:
                value = self._training_mean.get(readout, 0.0)
                scale = self._training_spread.get(readout, 1e-6)
                basis = "training-mean fallback for an entity absent from the fit; dispersion of the training rows"
            state_change[readout] = value
            intervals[readout] = Interval(
                value - z * scale, value + z * scale, kind=IntervalKind.DESCRIPTIVE, basis=basis
            )
        limitations = [
            "Zero-information control arm: entity identity only, with the dose axis removed. "
            "It is a control for reading the ladder, never a candidate predictor.",
        ]
        if not known:
            limitations.append("answered_from_the_training_mean:entity_not_in_the_fit")
        return StatePrediction(
            applicable=True,
            state_change=state_change,
            uncertainty=_spread(intervals),
            limitations=tuple(limitations),
            supported_variables=tuple(sorted(self._coefficients)),
            calibration_basis="residual scale on the fitted table",
            request_id=request.request_id,
            model_version=self.model_version,
            intervals=intervals,
            confidence=None,
            in_distribution=known,
            compute_cost=0.05,
            uncertainty_components={
                "predictor_randomness": "none: the ridge fit is deterministic given the table",
                "measurement_noise": "unquantified: residual scale on the fit's own rows is a dispersion, not a held-out coverage",
                "model_misspecification": (
                    "structural and deliberate: the arm cannot express any dose dependence, "
                    "because removing that axis is the ablation"
                ),
            },
        )
