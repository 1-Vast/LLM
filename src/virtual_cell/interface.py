"""Virtual-cell contracts with explicit applicability and prediction lineage.

File summary
- Path: src/virtual_cell/interface.py
- Purpose: declare the world-model contract between MAESTRO's controller and a
  swappable virtual-cell predictor.
- Core points:
  - A prediction is planning-only; it never becomes measured evidence.
  - Three contract fields are mandatory: ``confidence``, ``in_distribution``,
    ``abstain_reason``.
  - Predictions carry intervals, not point estimates, so they can enter costs.
- Interfaces: `PredictionRequest`, `QueryAssessment`, `StatePrediction`,
  `Interval`, `VirtualCellWorldModel`, `UnavailableVirtualCellWorldModel`.
- Depends on: maestro.models
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, fields, replace
from enum import Enum
from math import isfinite
from typing import Mapping, Protocol

from maestro.models import FunctionalInterventionProfile, MeasurementStatus

from .applicability import SupportLevel


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _names(value: object, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, (tuple, list))
        and (allow_empty or bool(value))
        and all(_text(item) for item in value)
        and len(set(value)) == len(value)
    )


def _notes(value: object) -> bool:
    return isinstance(value, (tuple, list)) and all(_text(item) for item in value)


def _components(value: object) -> bool:
    return isinstance(value, Mapping) and all(_text(k) and _text(v) for k, v in value.items())


@dataclass(frozen=True)
class Intervention:
    """A stated intervention, including rather than assuming its functional effect."""

    identifier: str
    mode: str
    intended_targets: tuple[str, ...]
    dose: float | None = None
    dose_unit: str | None = None
    time_hours: float | None = None
    functional_profile: FunctionalInterventionProfile | None = None


@dataclass(frozen=True)
class SystemContext:
    """Observed biological context for a conditional prediction."""

    identifier: str
    description: str
    dataset_id: str | None = None
    control_dataset_id: str | None = None
    species: str | None = None
    replicate_unit: str | None = None


class QuerySupport(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ModelCapabilities:
    """Checkpoint-specific capabilities, never generic claims about a model family."""

    model_identifier: str
    model_version: str
    input_representation: str
    perturbation_representation: str
    supported_modes: tuple[str, ...]
    requires_matched_control: bool
    supports_dose: bool
    supports_time: bool
    calibration_basis: str | None


@dataclass(frozen=True)
class PredictionRequest:
    """A traceable query whose model inputs are distinct from the mechanism narrative."""

    request_id: str
    case_id: str
    contrast_id: str
    plan_version: int
    intervention: Intervention
    context: SystemContext
    readouts: tuple[str, ...]
    model_version: str

    def validation_errors(self) -> tuple[str, ...]:
        """Return structural errors without coercing identities or numeric values."""

        errors: list[str] = []
        for name in ("request_id", "case_id", "contrast_id", "model_version"):
            if not _text(getattr(self, name)):
                errors.append(f"invalid_{name}")
        if _text(self.request_id) and (
            not re.fullmatch(r"[A-Za-z0-9_.-]+", self.request_id) or self.request_id in (".", "..")
        ):
            errors.append("invalid_request_id")
        if type(self.plan_version) is not int or self.plan_version < 1:
            errors.append("invalid_plan_version")
        if not _names(self.readouts, allow_empty=False):
            errors.append("invalid_readouts")
        if not isinstance(self.context, SystemContext):
            errors.append("invalid_context")
        else:
            if not _text(self.context.identifier):
                errors.append("invalid_context_identifier")
            if not isinstance(self.context.description, str):
                errors.append("invalid_context_description")
            for name in ("dataset_id", "control_dataset_id", "species", "replicate_unit"):
                value = getattr(self.context, name)
                if value is not None and not _text(value):
                    errors.append(f"invalid_context_{name}")
        if not isinstance(self.intervention, Intervention):
            errors.append("invalid_intervention")
            return tuple(errors)
        intervention = self.intervention
        for name in ("identifier", "mode"):
            if not _text(getattr(intervention, name)):
                errors.append(f"invalid_intervention_{name}")
        if not _names(intervention.intended_targets):
            errors.append("invalid_intended_targets")
        for name in ("dose", "time_hours"):
            value = getattr(intervention, name)
            if value is not None and (not _finite(value) or value < 0):
                errors.append(f"invalid_{name}")
        if intervention.dose_unit is not None and not _text(intervention.dose_unit):
            errors.append("invalid_dose_unit")
        if (intervention.dose is None) != (intervention.dose_unit is None):
            errors.append("dose_unit_pair_required")
        profile = intervention.functional_profile
        if profile is not None:
            if not isinstance(profile, FunctionalInterventionProfile):
                errors.append("invalid_functional_profile")
            else:
                if not _text(profile.mode) or profile.mode != intervention.mode:
                    errors.append("functional_profile_mode_mismatch")
                if profile.context_identifier is not None and (
                    not _text(profile.context_identifier)
                    or not isinstance(self.context, SystemContext)
                    or profile.context_identifier != self.context.identifier
                ):
                    errors.append("functional_profile_context_mismatch")
                for name, stated in (("nominal_dose", intervention.dose), ("time_hours", intervention.time_hours)):
                    value = getattr(profile, name)
                    if value is not None and (not _finite(value) or value < 0):
                        errors.append(f"invalid_functional_profile_{name}")
                    elif value is not None and stated is not None and value != stated:
                        errors.append(f"functional_profile_{name}_mismatch")
                for name in ("activity_spectrum", "source_ids"):
                    if not _names(getattr(profile, name)):
                        errors.append(f"invalid_functional_profile_{name}")
                if not isinstance(profile.protein_abundance, MeasurementStatus):
                    errors.append("invalid_functional_profile_protein_abundance")
                for name in ("functional_states", "measured_fields"):
                    value = getattr(profile, name)
                    if not isinstance(value, Mapping) or not all(
                        _text(k) and isinstance(v, MeasurementStatus) for k, v in value.items()
                    ):
                        errors.append(f"invalid_functional_profile_{name}")
        return tuple(dict.fromkeys(errors))

    def validate(self) -> None:
        """Raise ValueError for an invalid request; construction remains compatible."""

        errors = self.validation_errors()
        if errors:
            raise ValueError("invalid_prediction_request:" + ",".join(errors))

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible structure, including profile provenance."""

        self.validate()
        return json.loads(json.dumps(asdict(self), allow_nan=False))

    def to_json(self) -> str:
        """Serialize a validated request as strict JSON, never NaN or Infinity."""

        return json.dumps(self.to_dict(), allow_nan=False, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> PredictionRequest:
        """Decode nested objects and enums; reject unknown fields and wrong shapes."""

        def object_fields(value, kind):
            if not isinstance(value, Mapping) or any(k not in {f.name for f in fields(kind)} for k in value):
                raise ValueError(f"invalid_{kind.__name__}_object")
            return dict(value)

        def sequence(value):
            if not isinstance(value, (tuple, list)):
                raise ValueError("invalid_sequence")
            return tuple(value)

        try:
            data = object_fields(payload, cls)
            context = SystemContext(**object_fields(data["context"], SystemContext))
            intervention = object_fields(data["intervention"], Intervention)
            intervention["intended_targets"] = sequence(intervention["intended_targets"])
            raw_profile = intervention.get("functional_profile")
            if raw_profile is not None:
                profile = object_fields(raw_profile, FunctionalInterventionProfile)
                for name in ("activity_spectrum", "source_ids"):
                    if name in profile:
                        profile[name] = sequence(profile[name])
                for name in ("functional_states", "measured_fields"):
                    if name in profile:
                        if not isinstance(profile[name], Mapping):
                            raise ValueError(f"invalid_{name}")
                        profile[name] = {k: MeasurementStatus(v) for k, v in profile[name].items()}
                if "protein_abundance" in profile:
                    profile["protein_abundance"] = MeasurementStatus(profile["protein_abundance"])
                intervention["functional_profile"] = FunctionalInterventionProfile(**profile)
            data["intervention"] = Intervention(**intervention)
            data["context"] = context
            data["readouts"] = sequence(data["readouts"])
            result = cls(**data)
            result.validate()
            return result
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"invalid_prediction_request:{error}") from error

    @classmethod
    def from_json(cls, payload: str) -> PredictionRequest:
        """Decode strict JSON; duplicate keys cannot silently replace query identity."""

        def reject_constant(value):
            raise ValueError(f"nonfinite_json_number:{value}")

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate_json_key:{key}")
                result[key] = value
            return result

        if not isinstance(payload, str):
            raise ValueError("prediction_request_json_must_be_text")
        return cls.from_dict(json.loads(payload, parse_constant=reject_constant, object_pairs_hook=unique_object))


@dataclass(frozen=True)
class VirtualCellQueryTemplate:
    """Registered model inputs from which the controller may construct a request.

    Exact perturbation labels and dataset identifiers are supplied by the caller;
    the controller only binds them to the current case, contrast, and targets.
    """

    intervention_identifier: str
    intervention_mode: str
    context: SystemContext
    readouts: tuple[str, ...]
    model_version: str
    # Optional per-action exact labels. When present, the controller queries
    # the model once per registered action, so each action is ranked by the
    # prediction for its own condition rather than by one shared number.
    action_interventions: Mapping[str, str] = field(default_factory=dict)
    # The declared dose and exposure of the planned condition. A backend that
    # needs them refuses by name when they are absent; none is inferred.
    dose: float | None = None
    dose_unit: str | None = None
    time_hours: float | None = None

    def build(
        self,
        *,
        request_id: str,
        case_id: str,
        contrast_id: str,
        plan_version: int,
        intended_targets: tuple[str, ...],
        intervention_identifier: str | None = None,
        time_hours: float | None = None,
    ) -> PredictionRequest:
        """Bind the template to one case; ``time_hours`` states a planned action's own exposure."""

        return PredictionRequest(
            request_id=request_id,
            case_id=case_id,
            contrast_id=contrast_id,
            plan_version=plan_version,
            intervention=Intervention(
                identifier=intervention_identifier or self.intervention_identifier,
                mode=self.intervention_mode,
                intended_targets=intended_targets,
                dose=self.dose,
                dose_unit=self.dose_unit,
                time_hours=self.time_hours if time_hours is None else time_hours,
            ),
            context=self.context,
            readouts=self.readouts,
            model_version=self.model_version,
        )


@dataclass(frozen=True)
class QueryAssessment:
    """Whether the query can run, kept apart from what is known about its accuracy.

    ``support`` answers executability. ``validation_status`` answers a different
    question — whether anything has been *evaluated* for this endpoint, context
    and model version — and its default is ``UNKNOWN``, because a query the
    backend can run is not thereby a query whose answer has been checked.
    """

    support: QuerySupport
    missing_inputs: tuple[str, ...]
    limitations: tuple[str, ...]
    capabilities: ModelCapabilities
    validation_status: SupportLevel = SupportLevel.UNKNOWN
    validation_notes: tuple[str, ...] = ()


class IntervalKind(str, Enum):
    """Whether a band claims coverage, or is only a descriptive spread.

    A band built from the dispersion of a statistic is not a predictive interval:
    the spread of embedding dimensions is not the error distribution of the
    prediction.  Conflating them is how an uncalibrated number acquires the
    authority of a coverage claim (audit F07).
    """

    DESCRIPTIVE = "descriptive"
    CALIBRATED = "calibrated"


@dataclass(frozen=True)
class Interval:
    """A band for one declared readout, with its coverage claim made explicit.

    ``DESCRIPTIVE`` bands carry no ``level``: they state a spread and nothing
    more.  ``CALIBRATED`` bands carry a ``level`` and must name the ``basis``
    whose residuals were used, so the claim can be audited.
    """

    low: float
    high: float
    kind: IntervalKind = IntervalKind.DESCRIPTIVE
    level: float | None = None
    basis: str | None = None

    @property
    def width(self) -> float:
        return self.high - self.low

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high

    @property
    def claims_coverage(self) -> bool:
        return self.kind is IntervalKind.CALIBRATED and self.level is not None


@dataclass(frozen=True)
class StatePrediction:
    """A planning-only prediction with calibration and applicability boundaries.

    ``confidence``, ``in_distribution`` and ``abstain_reason`` are mandatory
    contract fields: without them the controller has no basis for deciding
    whether to trust a simulation, and a silently wrong simulation is worse than
    an admitted abstention.
    """

    applicable: bool
    state_change: Mapping[str, float] | None
    uncertainty: float | None
    limitations: tuple[str, ...]
    supported_variables: tuple[str, ...] = ()
    calibration_basis: str | None = None
    request_id: str | None = None
    model_version: str | None = None
    artifact_ref: str | None = None
    intervals: Mapping[str, Interval] = field(default_factory=dict)
    confidence: float | None = None
    in_distribution: bool | None = None
    abstain_reason: str | None = None
    compute_cost: float = 1.0
    artifact_sha256: str | None = None
    # Named uncertainty sources and what is known about each. A backend that
    # cannot state a calibrated confidence must say which sources remain
    # unquantified instead of compressing them into an invented number.
    uncertainty_components: Mapping[str, str] = field(default_factory=dict)

    def interval_for(self, readout: str) -> Interval | None:
        return self.intervals.get(readout)

    def contract_errors(self) -> tuple[str, ...]:
        """Return structural violations without raising on malformed field values.

        Unknown confidence and distribution stay unknown when uncertainty sources
        are named. Optional lineage remains compatible for standalone objects;
        safe_predict requires it to match the actual request and serving model.
        """

        errors: list[str] = []
        if type(self.applicable) is not bool:
            errors.append("invalid_applicable")
        if not _notes(self.limitations):
            errors.append("invalid_limitations")
        if not _names(self.supported_variables):
            errors.append("invalid_supported_variables")
        components_valid = _components(self.uncertainty_components)
        if not components_valid:
            errors.append("invalid_uncertainty_components")
        explained_unknown = components_valid and bool(self.uncertainty_components)
        if self.confidence is not None and (not _finite(self.confidence) or not 0 <= self.confidence <= 1):
            errors.append("invalid_confidence")
        if self.in_distribution is not None and type(self.in_distribution) is not bool:
            errors.append("invalid_in_distribution")
        for name in ("uncertainty", "compute_cost"):
            value = getattr(self, name)
            if (value is not None or name == "compute_cost") and (not _finite(value) or value < 0):
                errors.append(f"invalid_{name}")
        for name in ("request_id", "model_version", "artifact_ref", "calibration_basis", "abstain_reason"):
            value = getattr(self, name)
            if value is not None and not _text(value):
                errors.append(f"invalid_{name}")
        if self.artifact_sha256 is not None:
            if not isinstance(self.artifact_sha256, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", self.artifact_sha256):
                errors.append("invalid_artifact_sha256")
            if not _text(self.artifact_ref):
                errors.append("artifact_sha256_without_ref")
        if self.state_change is not None:
            if not isinstance(self.state_change, Mapping):
                errors.append("invalid_state_change")
            else:
                for name, value in self.state_change.items():
                    if not _text(name):
                        errors.append("invalid_state_change_readout")
                    if not _finite(value):
                        errors.append(f"invalid_state_change:{name}")
        if self.applicable is True:
            if self.confidence is None and not explained_unknown:
                errors.append("applicable_confidence_missing")
            if self.in_distribution is None and not explained_unknown:
                errors.append("in_distribution_missing")
            if not self.state_change and not _text(self.artifact_ref):
                errors.append("state_change_missing")
            if self.abstain_reason is not None:
                errors.append("applicable_with_abstain_reason")
        elif self.applicable is False:
            if not _text(self.abstain_reason):
                errors.append("abstain_reason_missing")
            if self.state_change is not None or self.intervals or self.artifact_ref is not None:
                errors.append("abstention_contains_prediction")
            if self.confidence is not None or self.uncertainty is not None:
                errors.append("abstention_contains_estimate")
        if not isinstance(self.intervals, Mapping):
            errors.append("invalid_intervals")
            return tuple(dict.fromkeys(errors))
        for name, interval in self.intervals.items():
            if not _text(name):
                errors.append("invalid_interval_readout")
            if not isinstance(interval, Interval):
                errors.append(f"invalid_interval:{name}")
                continue
            if not _finite(interval.low) or not _finite(interval.high) or interval.low > interval.high:
                errors.append(f"invalid_interval:{name}")
            if not isinstance(interval.kind, IntervalKind):
                errors.append(f"invalid_interval_kind:{name}")
            elif interval.kind is IntervalKind.CALIBRATED:
                if not _finite(interval.level) or not 0.0 < interval.level < 1.0:
                    errors.append(f"invalid_interval_level:{name}")
                if not _text(interval.basis):
                    errors.append(f"calibrated_interval_without_basis:{name}")
            elif interval.level is not None:
                errors.append(f"descriptive_interval_claims_a_level:{name}")
            if interval.basis is not None and not _text(interval.basis):
                errors.append(f"invalid_interval_basis:{name}")
            if isinstance(self.state_change, Mapping) and name not in self.state_change:
                errors.append(f"interval_without_state_change:{name}")
        return tuple(dict.fromkeys(errors))

    @property
    def contract_valid(self) -> bool:
        return not self.contract_errors()


class VirtualCellWorldModel(Protocol):
    """A calibrated model of intervention-conditioned state change, where supported.

    ``name`` is part of the contract because routing, cost accounting and every
    receipt identify a backend by it. A backend without one cannot be routed to
    or billed, which is how a composite came to raise ``AttributeError`` in the
    middle of a routing report.
    """

    name: str

    def capabilities(self) -> ModelCapabilities:
        """Return the concrete checkpoint capability declaration."""

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        """Reject missing, unsupported, or unsafe conditions before inference."""

    def predict(self, request: PredictionRequest) -> StatePrediction:
        """Return a planning-only prediction or an explicit unsupported result."""


def _capability_errors(value: object) -> tuple[str, ...]:
    if not isinstance(value, ModelCapabilities):
        return ("invalid_capabilities",)
    errors = []
    for name in ("model_identifier", "model_version", "input_representation", "perturbation_representation"):
        if not _text(getattr(value, name)):
            errors.append(f"invalid_capabilities_{name}")
    if not _names(value.supported_modes):
        errors.append("invalid_supported_modes")
    for name in ("requires_matched_control", "supports_dose", "supports_time"):
        if type(getattr(value, name)) is not bool:
            errors.append(f"invalid_capabilities_{name}")
    if value.calibration_basis is not None and not _text(value.calibration_basis):
        errors.append("invalid_capabilities_calibration_basis")
    return tuple(errors)


def _abstention(
    request: PredictionRequest,
    reason: str,
    limitations: tuple[str, ...],
    *,
    model_version: str | None = None,
    prediction: StatePrediction | None = None,
) -> StatePrediction:
    """Discard unusable outputs while retaining valid cost and uncertainty metadata."""

    return StatePrediction(
        applicable=False,
        state_change=None,
        uncertainty=None,
        limitations=limitations,
        request_id=request.request_id if isinstance(request, PredictionRequest) and _text(request.request_id) else None,
        model_version=model_version,
        confidence=None,
        in_distribution=(
            prediction.in_distribution
            if prediction is not None and type(prediction.in_distribution) is bool else None
        ),
        abstain_reason=reason,
        compute_cost=(
            prediction.compute_cost
            if prediction is not None and _finite(prediction.compute_cost) and prediction.compute_cost >= 0 else 0.0
        ),
        uncertainty_components=(
            dict(prediction.uncertainty_components)
            if prediction is not None and _components(prediction.uncertainty_components) else {}
        ),
    )


def safe_predict(
    model: VirtualCellWorldModel, request: PredictionRequest
) -> tuple[QueryAssessment, StatePrediction]:
    """Assess then predict once, failing closed on invalid input, output or lineage.

    Executability, validation and distribution membership are separate claims.
    Unknown confidence/distribution are never promoted. Ordinary backend errors
    and SystemExit become abstentions; user interrupts are not swallowed. This
    boundary does not authenticate artifacts or impose a process timeout.
    """

    capabilities = UnavailableVirtualCellWorldModel().capabilities()

    def reject(reason, details=(), assessment=None, prediction=None):
        limitations = tuple(details) + (reason,)
        if assessment is None:
            assessment = QueryAssessment(QuerySupport.UNSUPPORTED, (), limitations, capabilities)
        if prediction is not None and _notes(prediction.limitations):
            limitations = tuple(prediction.limitations) + limitations
        return assessment, _abstention(
            request, reason, limitations, model_version=capabilities.model_version, prediction=prediction
        )

    if not isinstance(request, PredictionRequest):
        return reject("invalid_request", ("expected_PredictionRequest",))
    errors = request.validation_errors()
    if errors:
        return reject("invalid_request", errors)
    try:
        declared = model.capabilities()
        if callable(getattr(model, "catalog", None)):
            declared = next((item for item in model.catalog() if item.model_version == request.model_version), declared)
        errors = _capability_errors(declared)
        if errors:
            return reject("invalid_capabilities", errors)
        capabilities = declared
        if request.model_version != capabilities.model_version:
            return reject("model_version_mismatch")
    except (Exception, SystemExit) as error:
        return reject(f"capabilities_exception:{type(error).__name__}")
    try:
        assessment = model.assess_query(request)
        if not isinstance(assessment, QueryAssessment) or (
            not isinstance(assessment.support, QuerySupport)
            or not isinstance(assessment.validation_status, SupportLevel)
            or not _notes(assessment.missing_inputs)
            or not _notes(assessment.limitations)
            or not _notes(assessment.validation_notes)
            or _capability_errors(assessment.capabilities)
        ):
            return reject("invalid_assessment")
        if assessment.capabilities != capabilities:
            return reject("assessment_model_mismatch")
        if assessment.support is not QuerySupport.SUPPORTED:
            return reject(
                f"query_{assessment.support.value}",
                tuple(assessment.limitations) + tuple(f"missing_input:{item}" for item in assessment.missing_inputs),
                assessment,
            )
        if assessment.missing_inputs:
            return reject("invalid_assessment", ("supported_with_missing_inputs",))
    except (Exception, SystemExit) as error:
        return reject(f"assessment_exception:{type(error).__name__}")
    try:
        prediction = model.predict(request)
        if not isinstance(prediction, StatePrediction):
            return reject("invalid_prediction_type", assessment=assessment)
        errors = prediction.contract_errors()
        if errors:
            return reject("contract_violation", errors, assessment, prediction)
        if prediction.request_id != request.request_id:
            return reject("request_id_mismatch", assessment=assessment, prediction=prediction)
        if prediction.model_version != capabilities.model_version:
            return reject("prediction_model_mismatch", assessment=assessment, prediction=prediction)
        if prediction.applicable:
            values = prediction.state_change or {}
            declared_readouts = prediction.supported_variables
            missing = tuple(
                name for name in request.readouts
                if name not in values and not (
                    name in declared_readouts and _text(prediction.artifact_ref)
                )
            )
            if missing:
                return reject("readout_mismatch", missing, assessment, prediction)
            if declared_readouts and any(name not in declared_readouts for name in request.readouts):
                return reject("readout_mismatch", ("requested_readout_not_declared",), assessment, prediction)
        return assessment, prediction
    except (Exception, SystemExit) as error:
        return reject(f"prediction_exception:{type(error).__name__}", assessment=assessment)


class UnavailableVirtualCellWorldModel:
    """Safe default used until a calibrated model is supplied."""

    name = "unavailable"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="unavailable",
            model_version="none",
            input_representation="none",
            perturbation_representation="none",
            supported_modes=(),
            requires_matched_control=True,
            supports_dose=False,
            supports_time=False,
            calibration_basis=None,
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        del request
        return QueryAssessment(
            support=QuerySupport.UNSUPPORTED,
            missing_inputs=(),
            limitations=("No calibrated virtual-cell model is available for this query.",),
            capabilities=self.capabilities(),
        )

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        return StatePrediction(
            applicable=False,
            state_change=None,
            uncertainty=None,
            limitations=assessment.limitations,
            request_id=request.request_id,
            model_version=self.capabilities().model_version,
            confidence=None,
            in_distribution=None,
            abstain_reason="model_unavailable",
            compute_cost=0.0,
        )
