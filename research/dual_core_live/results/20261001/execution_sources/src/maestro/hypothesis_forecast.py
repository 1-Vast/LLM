"""Hypothesis-conditional forecasts and scoped categorical calibration for the production planner."""
from __future__ import annotations

import hashlib
import math
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .acquisition import OutcomeBranch, OutcomeForecast
from .adaptive_retrieval import AdaptiveRetriever, RetrievalProblem
from .case_memory import EpisodeStore, case_memory_enabled, digest
from .adaptive_retrieval import ContextFeatures, DirectionalState, FeatureArm
from .models import EvidenceAction, MechanismContrast
from .outcome import EvidenceState

SHRINKAGE_VERSION = "support-aware-shrinkage-1"
FREQUENCY_VERSION = "conditional-dirichlet-1"


def dirichlet_forecast(counts: Mapping[str, float], *, effective_support: float,
                       pseudocount: float = 0.5) -> tuple[dict[str, float], float]:
    """One smoothing step. Weighted frequencies carry Kish support, not total arbitrary weights.

    Return the posterior predictive mean and total concentration for the planner. No temperature
    transformation persists at infinite support. This approximation is not a calibration claim.
    """
    if (not counts or not math.isfinite(effective_support) or effective_support <= 0
            or not math.isfinite(pseudocount) or pseudocount <= 0):
        raise ValueError("invalid_dirichlet_support")
    frequencies = _normalise(counts, tuple(counts))
    if sum(counts.values()) <= 0:
        raise ValueError("missing_observed_outcomes")
    concentration = effective_support + len(counts) * pseudocount
    return ({label: (effective_support * value + pseudocount) / concentration
             for label, value in frequencies.items()}, concentration)


@dataclass(frozen=True)
class FrequencyCalibration:
    """A scoped development fit; exact context/estimand matching is required before use.

    This is categorical outcome calibration, separate from continuous prediction intervals.
    Fitting does not establish external validity. Tuples keep scope and identity immutable.
    """
    pseudocount: float
    outcome_mode: str
    feature_arm: str
    outcome_count: int
    contexts: tuple[tuple[str, ...], ...]
    training_units: tuple[str, ...]
    calibration_units: tuple[str, ...]
    source_snapshot: str
    model_version: str = FREQUENCY_VERSION

    def __post_init__(self):
        if (not math.isfinite(self.pseudocount) or self.pseudocount <= 0
                or self.outcome_mode not in ("valid_readout", "attempted_experiment")
                or self.outcome_count < 1 or not self.contexts or not self.source_snapshot
                or not self.training_units or len(set(self.calibration_units)) < 2):
            raise ValueError("invalid_frequency_calibration")
        if set(self.training_units) & set(self.calibration_units):
            raise ValueError("calibration_training_overlap")
        if any(len(c) != 6 for c in self.contexts):
            raise ValueError("invalid_calibration_context")

    def refusal(self, context: tuple[str, ...], outcome_mode: str, feature_arm: str,
                outcome_count: int, source_snapshot: str) -> str | None:
        if self.model_version != FREQUENCY_VERSION or self.source_snapshot != source_snapshot:
            return "calibration_source_mismatch"
        if (self.outcome_mode != outcome_mode or self.feature_arm != feature_arm
                or self.outcome_count != outcome_count):
            return "calibration_estimand_mismatch"
        if context not in self.contexts:
            return "outside_calibration_context"
        return None


def fit_frequency_calibration(rows, *, training_units, source_snapshot: str,
                              outcome_mode: str, feature_arm: str) -> FrequencyCalibration:
    """Fit just one positive pseudocount on independent development outcomes.

    Each compound receives equal loss weight, irrespective of its number of conditions. Counts
    must have been built without calibration units. The caller must rebuild fitted preprocessing
    within the training split; disjoint IDs alone cannot prove that provenance.
    """
    import numpy as np
    from scipy.optimize import minimize_scalar

    if not rows:
        raise ValueError("empty_calibration_set")
    training = set(training_units)
    calibration = {str(r["unit"]) for r in rows}
    if training & calibration:
        raise ValueError("calibration_training_overlap")
    if not training or not source_snapshot or len(calibration) < 2:
        raise ValueError("insufficient_calibration_provenance")
    sizes = {len(r["counts"]) for r in rows}
    if len(sizes) != 1:
        raise ValueError("mixed_calibration_outcome_spaces")
    unit_rows = {}
    for row in rows:
        if row["outcome"] not in row["counts"]:
            raise ValueError("unregistered_calibration_outcome")
        unit_rows.setdefault(str(row["unit"]), []).append(row)

    def objective(log_alpha):
        alpha = math.exp(log_alpha)
        losses = []
        for group in unit_rows.values():
            losses.append(np.mean([-math.log(dirichlet_forecast(r["counts"],
                effective_support=r["effective_support"], pseudocount=alpha)[0][r["outcome"]])
                for r in group]))
        return float(np.mean(losses))

    result = minimize_scalar(objective, bounds=(math.log(.01), math.log(20.)), method="bounded")
    if not result.success or not math.isfinite(result.fun):
        raise ValueError("calibration_fit_failed")
    return FrequencyCalibration(math.exp(result.x), outcome_mode, feature_arm, next(iter(sizes)),
                                tuple(sorted({tuple(r["context"]) for r in rows})),
                                tuple(sorted(training)), tuple(sorted(calibration)), source_snapshot)


def _normalise(values: Mapping[str, float], labels: tuple[str, ...]) -> dict[str, float]:
    clean = {label: float(values.get(label, 0.0)) for label in labels}
    if any(not math.isfinite(v) or v < 0 for v in clean.values()):
        raise ValueError("invalid_probability_mass")
    total = sum(clean.values())
    if not math.isfinite(total):
        raise ValueError("invalid_probability_mass")
    if total <= 0.0:
        return {label: 1.0 / len(labels) for label in labels}
    return {label: value / total for label, value in clean.items()}


def support_aware_shrinkage(
    raw: Mapping[str, float],
    *,
    effective_support: float,
    domain_shift: float,
    base_prior: Mapping[str, float],
    prior_strength: float = 8.0,
    temperature: float = 1.5,
    domain_shift_penalty: float = 0.75,
) -> dict[str, float]:
    """Return a normalised, explicitly support-aware forecast distribution.

    ``effective_support`` is the Kish effective number of independent precedents.  ``domain_shift``
    is in [0, 1], where 1 means the retrieved state is maximally unlike the reference cases.
    All constants are declared arguments so a future development calibration can replace them
    without silently changing the contract.
    """

    if (not math.isfinite(effective_support) or effective_support < 0
            or not math.isfinite(domain_shift) or not 0 <= domain_shift <= 1
            or not math.isfinite(prior_strength) or prior_strength <= 0
            or not math.isfinite(temperature) or temperature < 1
            or not math.isfinite(domain_shift_penalty) or not 0 <= domain_shift_penalty <= 1):
        raise ValueError("invalid_shrinkage_parameters")
    labels = tuple(dict.fromkeys([*base_prior, *raw]))
    if not labels:
        return {}
    prior = _normalise(base_prior, labels)
    empirical = _normalise(raw, labels)
    temp = max(1.0, float(temperature))
    tempered = _normalise({label: empirical[label] ** (1.0 / temp) for label in labels}, labels)
    support = max(0.0, float(effective_support))
    strength = support / (support + max(1e-9, float(prior_strength)))
    shift = min(1.0, max(0.0, float(domain_shift)))
    trust = strength * max(0.0, 1.0 - float(domain_shift_penalty) * shift)
    result = {label: trust * tempered[label] + (1.0 - trust) * prior[label] for label in labels}
    return _normalise(result, labels)


MODEL_VERSION = "case-memory-production-3"
MIN_SUPPORT = 6
"""Registered minimum: a branch resting on fewer independent precedents is flagged low-support."""
CALIBRATION_STATUS = "uncalibrated"
"""Neither a default prior nor a development fit establishes external calibration."""
CALIBRATION_DATASET: str | None = None
"""Default has no fitted profile; detailed receipts identify any supplied development fit."""

READING_LABELS = ("match_h1", "match_h2", "unresolved", "absent", "qc_failed")
OUTCOME_MODES = ("valid_readout", "attempted_experiment")


@dataclass(frozen=True)
class UserStateContext:
    """The user's actual biological state, compiled before forecasting. No truth field."""

    directional_state: DirectionalState = field(default_factory=DirectionalState)
    cell_state_summaries: Mapping[str, float] = field(default_factory=dict)
    intervention_identity: str = ""
    chemical_structure: str | None = None
    cell_context: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    assay: str = ""
    hypothesis_graph: Mapping[str, Any] = field(default_factory=dict)
    evidence_history: tuple[str, ...] = ()
    biological_system: str = ""
    intervention_type: str = ""
    measurement_type: str = ""
    control_design: str = ""
    laboratory: str = ""
    outcome_mode: str = "valid_readout"

    def identity(self) -> str:
        """Digest of the state; part of the forecast cache identity, so two states never share one."""

        def clean(value):
            if isinstance(value, Mapping):
                return {str(k): clean(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
            if isinstance(value, (tuple, list)):
                return [clean(v) for v in value]
            return value

        payload = {
            "delta": clean(dict(self.directional_state.signed_feature_delta)),
            "pathway": clean(dict(self.directional_state.pathway_direction)),
            "cell_state": clean(dict(self.cell_state_summaries)),
            "intervention": self.intervention_identity,
            "structure": self.chemical_structure,
            "cell_context": self.cell_context,
            "time_h": self.time_h,
            "dose_nM": self.dose_nM,
            "assay": self.assay,
            "history": list(self.evidence_history),
            "biological_system": self.biological_system,
            "intervention_type": self.intervention_type,
            "measurement_type": self.measurement_type,
            "control_design": self.control_design,
            "laboratory": self.laboratory, "outcome_mode": self.outcome_mode,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class CaseMemoryOutcomeForecaster:
    """Hypothesis-conditional outcome forecasts served from a case memory."""

    name = "case_memory"

    def __init__(self, store: EpisodeStore, retriever: AdaptiveRetriever | None = None, *,
                 feature_arm: FeatureArm = FeatureArm.COMBINED, research_mode: bool = False,
                 calibration: FrequencyCalibration | None = None,
                 outcome_mode: str = "valid_readout"):
        self.store = store
        self.retriever = retriever or AdaptiveRetriever(store)
        self.feature_arm = feature_arm
        self.research_mode = research_mode
        self.calibration = calibration
        if outcome_mode not in OUTCOME_MODES:
            raise ValueError("unsupported_outcome_mode")
        self.outcome_mode = outcome_mode
        self._cache: dict[str, OutcomeForecast] = {}
        self._support: dict[str, dict] = {}

    # ------------------------------------------------------------------ protocol
    def forecast(self, contrast: MechanismContrast, actions: Sequence[EvidenceAction],
                 evidence: EvidenceState | None,
                 user_state: UserStateContext | None = None) -> Mapping[str, OutcomeForecast]:
        """Forecasts per action. `user_state` is optional; the three-argument call is unchanged."""

        out: dict[str, OutcomeForecast] = {}
        hypotheses = tuple(sorted(contrast.identifiers()))
        for action in actions:
            key = self._cache_key(contrast, action, evidence, user_state)
            if key not in self._cache:
                self._cache[key] = self._forecast_one(hypotheses, action, evidence, user_state)
            out[action.identifier] = self._cache[key]
        return out

    def support_report(self, contrast: MechanismContrast, action: EvidenceAction,
                       evidence: EvidenceState | None = None,
                       user_state: UserStateContext | None = None) -> Mapping[str, Mapping[str, Any]]:
        """Support actually used for this action and state, grouped by independent source unit."""

        self.forecast(contrast, (action,), evidence, user_state)
        report = self._support.get(self._cache_key(contrast, action, evidence, user_state), {})
        return {h: report.get(h, {"independent_units": 0, "effective_support": 0.0,
                                  "low_support": True}) for h in sorted(contrast.identifiers())}

    # ------------------------------------------------------------------ detailed receipt
    def forecast_detailed(self, contrast: MechanismContrast, action: EvidenceAction,
                          evidence: EvidenceState | None,
                          user_state: UserStateContext | None = None) -> Mapping[str, Any]:
        """The full forecast receipt: distribution, support, calibration status and provenance.

        The multi-label distribution is reported whole for log-score evaluation; it is never
        collapsed into a binary qualified/not-qualified score.
        """

        forecast = self.forecast(contrast, (action,), evidence, user_state)[action.identifier]
        return {
            "action_identifier": action.identifier,
            "applicable": forecast.refusal is None and bool(forecast.branches),
            "abstain_reason": forecast.refusal,
            "branches": [
                {"hypothesis": branch.hypothesis, "probabilities": dict(branch.probabilities),
                 "support": branch.support, "low_support": branch.support < MIN_SUPPORT,
                 "posterior_concentration": branch.posterior_concentration}
                for branch in forecast.branches
            ],
            "support": self.support_report(contrast, action, evidence, user_state),
            "regularisation": {"pseudocount_per_label": self.calibration.pseudocount if self.calibration else .5,
                               "temperature": 1.0, "smoothing_owner": "forecaster",
                               "fitted": self.calibration is not None},
            "outcome_mode": user_state.outcome_mode if user_state else self.outcome_mode,
            "decision_applicable": (forecast.refusal is None and bool(forecast.branches)
                                    and forecast.outcome_mode == "attempted_experiment"),
            "calibration_status": CALIBRATION_STATUS,
            "calibration_fit": "development_only" if self.calibration else "not_fitted",
            "calibration_dataset": digest(self.calibration.calibration_units) if self.calibration else None,
            "calibration_method": FREQUENCY_VERSION,
            "model_version": MODEL_VERSION,
            "feature_arm": self.feature_arm.value,
            "provenance": {
                "builder": "CaseMemoryOutcomeForecaster",
                "store_snapshot": self.store.snapshot_digest(),
                "basis": forecast.basis,
                "evidence_kind": forecast.evidence_kind.value,
            },
        }

    # ------------------------------------------------------------------ internals
    def _cache_key(self, contrast: MechanismContrast, action: EvidenceAction,
                   evidence: EvidenceState | None, user_state: UserStateContext | None) -> str:
        return self._cache_key_from_hypotheses(sorted(contrast.identifiers()), action, evidence, user_state)

    def _cache_key_from_hypotheses(self, hypotheses, action, evidence, user_state):
        identity = {
            "contrast": sorted(hypotheses),
            "action": digest(action),
            "enabled": self.research_mode or case_memory_enabled(),
            "research_mode": self.research_mode,
            "history": [u.action_identifier for u in evidence.updates] if evidence is not None else [],
            "user_state": user_state.identity() if user_state is not None else None,
            "arm": self.feature_arm.value,
            "model": MODEL_VERSION,
            "calibration": digest(self.calibration) if self.calibration else None,
            "outcome_mode": self.outcome_mode,
            "snapshot": self.store.snapshot_digest(),
        }
        return hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()

    def _forecast_one(self, hypotheses: Sequence[str], action: EvidenceAction,
                      evidence: EvidenceState | None,
                      user_state: UserStateContext | None) -> OutcomeForecast:
        if not self.research_mode and not case_memory_enabled():
            return OutcomeForecast(action.identifier, refusal="case_memory_disabled",
                                   basis="hypothesis_forecast", model_version=MODEL_VERSION)
        if len(hypotheses) != 2:
            return OutcomeForecast(action.identifier, refusal="contrast_without_two_hypotheses",
                                   basis="hypothesis_forecast", model_version=MODEL_VERSION)
        mode = user_state.outcome_mode if user_state else self.outcome_mode
        if mode not in OUTCOME_MODES:
            return OutcomeForecast(action.identifier, refusal="unsupported_outcome_mode", model_version=MODEL_VERSION)
        h1, h2 = hypotheses[0], hypotheses[1]
        context_features = ContextFeatures(
            cell_line=(action.execution_context or (user_state.cell_context if user_state else None)),
            time_h=(action.time_hours if action.time_hours is not None else user_state.time_h if user_state else None),
            dose_nM=(user_state.dose_nM if user_state else None),
        )
        state = user_state.directional_state if user_state else DirectionalState()
        assay = (user_state.assay if user_state and user_state.assay
                 else action.kind.value if hasattr(action.kind, "value") else str(action.kind))
        problem = RetrievalProblem(
            problem_id=action.identifier,
            biological_system=user_state.biological_system if user_state else "",
            assay=assay,
            intervention_type=user_state.intervention_type if user_state else "",
            measurement_type=user_state.measurement_type if user_state else "",
            control_design=user_state.control_design if user_state else "",
            context=context_features,
            hypotheses=(h1, h2),
            state=state,
            feature_arm=self.feature_arm,
            state_context=ContextFeatures(cell_line=user_state.cell_context, time_h=user_state.time_h,
                                          dose_nM=user_state.dose_nM, assay=user_state.assay or None) if user_state else None,
        )
        result = self.retriever.retrieve(problem, top_k=max(1, len(self.store.latest())), research_mode=True)
        expected = dict(getattr(action, "expected_outcomes", None) or {})
        branches: list[OutcomeBranch] = []
        report = {}
        for own, other in ((h1, h2), (h2, h1)):
            match_own = expected.get(own) or f"match_{own}"
            match_other = expected.get(other) or f"match_{other}"
            labels = tuple(dict.fromkeys((match_own, match_other, "unresolved", "absent") +
                                        (("qc_failed",) if mode == "attempted_experiment" else ())))
            if self.calibration:
                refusal = self.calibration.refusal(self.calibration_context(action, user_state), mode,
                                                   self.feature_arm.value, len(labels), self.store.snapshot_digest())
                if refusal:
                    return OutcomeForecast(action.identifier, refusal=refusal, model_version=MODEL_VERSION)
            # Each independent unit contributes once, regardless of episode/replicate count.
            units = {}
            missing_attempt = False
            for precedent in result.precedents.get(own, ()):
                case = self.store.get(precedent.case_id)
                if case is None:
                    continue
                measurement = self._measurement_for_action(case, action, user_state, (own, other))
                if measurement is None or measurement.conditioning_hypothesis != own:
                    continue
                if user_state and user_state.laboratory and case.context_fingerprint.get("laboratory") != user_state.laboratory:
                    continue
                proxy = (measurement.label_kind != "measured_outcome" or
                         case.provenance.get("label_kind") == "curated_annotation_proxy")
                if proxy and not self.research_mode:
                    continue
                if mode == "attempted_experiment" and measurement.sampling_frame != "all_attempts":
                    continue
                if mode == "attempted_experiment" and measurement.status.value in ("planned_missing", "not_planned"):
                    missing_attempt = True
                    continue
                if mode == "valid_readout" and measurement.status.value == "qc_failed":
                    continue
                label = self._map_measurement_label(case, measurement, own, other, match_own, match_other)
                if label not in labels:
                    if mode == "attempted_experiment":
                        missing_attempt = True
                    continue
                weight = max(precedent.components["state_similarity"], 0.0) * max(
                    precedent.components["historical_reliability"], 0.0)
                if weight <= 0:
                    continue
                unit = str(case.provenance.get("independent_unit") or case.case_id)
                row = (weight, label, precedent.components["domain_shift"], proxy)
                if unit not in units or weight > units[unit][0]:
                    units[unit] = row
            if missing_attempt:
                return OutcomeForecast(action.identifier, refusal="incomplete_attempt_outcomes",
                                       model_version=MODEL_VERSION, outcome_mode=mode)
            if not units:
                report[own] = {"independent_units": 0, "effective_support": 0.0, "low_support": True}
                continue
            weights = [row[0] for row in units.values()]
            total = sum(weights)
            effective = total ** 2 / sum(w * w for w in weights)
            counts = {label: 0.0 for label in labels}
            for weight, label, _, _ in units.values():
                counts[label] += weight
            shift = sum(w * d for w, _, d, _ in units.values()) / total
            dist, concentration = dirichlet_forecast(
                counts, effective_support=effective,
                pseudocount=self.calibration.pseudocount if self.calibration else .5)
            report[own] = {"independent_units": len(units), "effective_support": effective,
                           "low_support": effective < MIN_SUPPORT,
                           "proxy_units": sum(row[3] for row in units.values()),
                           "domain_shift": shift,
                           "domain_shift_assessment": "state_similarity_proxy" if (
                               state.signed_feature_delta or state.pathway_direction
                           ) and self.feature_arm is not FeatureArm.SCALAR else "not_assessed_state_free"}
            # The planner preserves this mean and uses concentration only for uncertainty.
            branches.append(OutcomeBranch(own, dist, max(1, int(effective + 1e-9)),
                                          posterior_concentration=concentration))
        key = self._cache_key_from_hypotheses(hypotheses, action, evidence, user_state)
        self._support[key] = report
        if len(branches) != 2:
            return OutcomeForecast(action.identifier, refusal="insufficient_outcome_support",
                                   basis="no_fabricated_hypothesis_branch", model_version=MODEL_VERSION)
        basis = (f"hypothesis_forecast[arm={self.feature_arm.value},calibration={CALIBRATION_STATUS},"
                 f"estimator={FREQUENCY_VERSION},outcome_mode={mode},outcome_basis=observed_label_frequencies,"
                 f"research_proxy_units={sum(r.get('proxy_units', 0) for r in report.values())}]")
        return OutcomeForecast(action.identifier, tuple(branches), basis=basis, model_version=MODEL_VERSION,
                               outcome_mode=mode)

    @staticmethod
    def calibration_context(action: EvidenceAction, state: UserStateContext | None) -> tuple[str, ...]:
        """Exact supported assay/readout/cell/lab/exposure domain, including explicit unknowns."""
        state = state or UserStateContext()
        def number(value):
            return "unknown" if value is None else format(float(value), ".12g")
        return (state.assay or action.kind.value, action.readout or "unknown",
                action.execution_context or state.cell_context or "unknown", state.laboratory or "unknown",
                number(action.time_hours if action.time_hours is not None else state.time_h), number(state.dose_nM))

    @staticmethod
    def _measurement_for_action(case, action, user_state=None, contrast=None):
        candidates = {c.action_id: c for c in case.candidate_actions}
        matches = []
        assay = user_state.assay if user_state and user_state.assay else action.kind.value
        for measurement in case.real_measurements:
            if contrast is not None and (measurement.contrast is None or
                                         set(measurement.contrast) != set(contrast)):
                continue
            candidate = candidates.get(measurement.action_id)
            if candidate is None or candidate.assay != assay:
                continue
            if action.readout and candidate.readout != action.readout:
                continue
            time = action.time_hours if action.time_hours is not None else user_state.time_h if user_state else None
            cell = action.execution_context or (user_state.cell_context if user_state else None)
            dose = user_state.dose_nM if user_state else None
            if any(want is not None and got != want for want, got in (
                    (time, candidate.time_h), (cell, candidate.cell_line), (dose, candidate.dose_nM))):
                continue
            matches.append(measurement)
        direct = [m for m in matches if m.action_id == action.identifier]
        # Multiple compatible actions are ambiguous, not permission to select the last row.
        return direct[0] if len(direct) == 1 else matches[0] if len(matches) == 1 else None

    @staticmethod
    def _map_measurement_label(case, measurement, own, other, match_own, match_other):
        if measurement is None or measurement.status.value in ("not_planned", "planned_missing"):
            return None
        if measurement.contrast is None or set(measurement.contrast) != {own, other}:
            return None
        if measurement.status.value == "qc_failed":
            return "qc_failed"
        if measurement.status.value == "undetected":
            return "absent"
        if measurement.status.value == "ambiguous":
            return "unresolved"
        label = measurement.outcome_label
        if label == "match_h1":
            return match_own if measurement.contrast[0] == own else match_other
        if label == "match_h2":
            return match_own if measurement.contrast[1] == own else match_other
        return label if label in (match_own, match_other, "unresolved", "absent", "qc_failed") else None
