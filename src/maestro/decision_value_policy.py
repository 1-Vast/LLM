"""Frozen external admission for decision-value planning, never measurement authority.

The receipt hash authenticates bytes and bindings. It does not establish calibration:
admission and calibration flags must come from an independent outcome-model evaluation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

from .acquisition import DecisionValuePlan, OutcomeForecast, outcome_consequences, select_decision_sensitive_action
from .composition import finite_number
from .handoff import json_dumps, json_loads, nonempty_string, object_fields
from .models import EvidenceAction, EvidenceKind, FunctionalInterventionProfile, MechanismHypothesis
from .outcome import OutcomeRule

_REVISIONS = ("calibration_id", "calibration_revision", "source_revision", "binding_sha256")
_ADMISSION_FIELDS = frozenset({
    "admission_status", "calibration_status", "model_version", "endpoint", "readout", "context",
    "reference_units", "in_distribution", "shift_flags", *_REVISIONS,
})


def decision_action_binding(action: EvidenceAction, profile: FunctionalInterventionProfile, endpoint: str) -> str:
    """Bind every registered action field and its operating conditions; facts stay outside."""
    data = asdict(action)
    data["kind"], data["quantity"] = action.kind.value, action.quantity.value
    # Strict JSON uses arrays; dataclass tuples are converted without changing their order.
    data = {key: list(value) if isinstance(value, tuple) else value for key, value in data.items()}
    identity = {"endpoint": endpoint, "action": data, "context": profile.context_identifier,
                "mode": profile.mode, "dose": profile.nominal_dose, "time_hours": profile.time_hours}
    return hashlib.sha256(json_dumps(identity).encode("utf-8")).hexdigest()


def decision_hypotheses_binding(hypotheses: Sequence[MechanismHypothesis]) -> str:
    """A label cannot reuse calibration under different scientific semantics."""
    if len(hypotheses) < 2 or any(not isinstance(item, MechanismHypothesis) for item in hypotheses):
        raise ValueError("registered_hypotheses_required")
    if len({item.identifier for item in hypotheses}) != len(hypotheses):
        raise ValueError("duplicate_registered_hypothesis")
    data = [{**asdict(item), "proposed_action": item.proposed_action.value if item.proposed_action else None}
            for item in sorted(hypotheses, key=lambda item: item.identifier)]
    return hashlib.sha256(json_dumps(data).encode("utf-8")).hexdigest()


def decision_interpretation_binding(rules: Sequence[OutcomeRule], *, time_tolerance_hours: float = 1.0,
                                    require_context_match: bool = True) -> str:
    """Bind the complete registered reading events, including table-level conditions."""
    if (not rules or any(not isinstance(rule, OutcomeRule) for rule in rules)
            or len({rule.identifier for rule in rules}) != len(rules)):
        raise ValueError("registered_interpretation_rules_required")
    if (not finite_number(time_tolerance_hours) or time_tolerance_hours < 0
            or type(require_context_match) is not bool):
        raise ValueError("invalid_interpretation_settings")
    def canonical(value):
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {key: canonical(item) for key, item in value.items()}
        if isinstance(value, (set, frozenset)):
            return sorted((canonical(item) for item in value), key=json_dumps)
        if isinstance(value, (tuple, list)):
            return [canonical(item) for item in value]
        return value
    data = {"rules": [asdict(rule) for rule in sorted(rules, key=lambda rule: rule.identifier)],
            "time_tolerance_hours": float(time_tolerance_hours), "require_context_match": require_context_match}
    return hashlib.sha256(json_dumps(canonical(data)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FrozenDecisionValuePolicy:
    """A snapshot of a caller-pinned independent evaluation receipt.

    Prices are terminal-loss units. ``EvidenceAction.cost`` remains the separate
    hard experimental budget. No omitted price is inferred from that budget cost.
    """

    receipt_sha256: str
    endpoint: str
    hypotheses_sha256: str
    interpretation_sha256: str
    wrong_decision_loss: float
    defer_loss: float
    minimum_reference_units: int
    minimum_branch_support: int
    measurement_costs: Mapping[str, float]
    admissions: Mapping[str, Mapping[str, object]]

    @classmethod
    def from_receipt(cls, path: Path, expected_sha256: str) -> "FrozenDecisionValuePolicy":
        raw = Path(path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_sha256:
            raise ValueError("decision_value_receipt_hash_mismatch")
        required = {"schema_version", "endpoint", "hypotheses_sha256", "interpretation_sha256", "wrong_decision_loss", "defer_loss",
                    "minimum_reference_units", "minimum_branch_support", "measurement_costs", "admissions"}
        data = object_fields(json_loads(raw.decode("utf-8")), required, set(), "decision_value_receipt")
        if data["schema_version"] != "1.0":
            raise ValueError("unsupported_decision_value_receipt")
        nonempty_string(data["endpoint"], "endpoint")
        nonempty_string(data["hypotheses_sha256"], "hypotheses_sha256")
        nonempty_string(data["interpretation_sha256"], "interpretation_sha256")
        for key in ("wrong_decision_loss", "defer_loss"):
            if not finite_number(data[key]) or data[key] < 0 or (key == "wrong_decision_loss" and data[key] == 0):
                raise ValueError(f"invalid_{key}")
        for key in ("minimum_reference_units", "minimum_branch_support"):
            if type(data[key]) is not int or data[key] < 1:
                raise ValueError(f"invalid_{key}")
        costs = data["measurement_costs"]
        if not isinstance(costs, dict) or any(not key.strip() or not finite_number(value) or value < 0
                                             for key, value in costs.items()):
            raise ValueError("invalid_utility_measurement_costs")
        admissions = data["admissions"]
        if not isinstance(admissions, dict):
            raise ValueError("invalid_decision_value_admissions")
        frozen = {}
        for identifier, admission in admissions.items():
            nonempty_string(identifier, "action_identifier")
            admission = object_fields(admission, set(_ADMISSION_FIELDS), set(), "admission")
            for key in _ADMISSION_FIELDS - {"reference_units", "in_distribution", "shift_flags"}:
                nonempty_string(admission[key], key)
            if type(admission["reference_units"]) is not int or admission["reference_units"] < 0:
                raise ValueError("invalid_calibration_reference_units")
            if type(admission["in_distribution"]) is not bool or not isinstance(admission["shift_flags"], list):
                raise ValueError("invalid_admission_domain")
            if any(not isinstance(flag, str) or not flag.strip() for flag in admission["shift_flags"]):
                raise ValueError("invalid_admission_shift_flags")
            frozen[identifier] = MappingProxyType({**admission, "shift_flags": tuple(admission["shift_flags"])})
        return cls(digest, data["endpoint"], data["hypotheses_sha256"], data["interpretation_sha256"], data["wrong_decision_loss"], data["defer_loss"],
                   data["minimum_reference_units"], data["minimum_branch_support"],
                   MappingProxyType(dict(costs)), MappingProxyType(frozen))

    def hypotheses_refusal_reason(self, hypotheses: Sequence[MechanismHypothesis]) -> str | None:
        try:
            bound = decision_hypotheses_binding(hypotheses)
        except (TypeError, ValueError):
            return "registered_hypotheses_required"
        return None if bound == self.hypotheses_sha256 else "decision_hypotheses_binding_mismatch"

    def interpretation_refusal_reason(self, rules: Sequence[OutcomeRule], *, time_tolerance_hours: float = 1.0,
                                      require_context_match: bool = True) -> str | None:
        try:
            bound = decision_interpretation_binding(rules, time_tolerance_hours=time_tolerance_hours,
                                                    require_context_match=require_context_match)
        except (TypeError, ValueError):
            return "registered_interpretation_rules_required"
        return None if bound == self.interpretation_sha256 else "decision_interpretation_binding_mismatch"

    def refusal_reason(self, action: EvidenceAction, profile: FunctionalInterventionProfile,
                       endpoint: str | None, forecast: OutcomeForecast | None) -> str | None:
        if endpoint != self.endpoint:
            return "decision_endpoint_mismatch"
        if action.identifier not in self.measurement_costs:
            return "utility_measurement_cost_missing"
        admission = self.admissions.get(action.identifier)
        if admission is None:
            return "external_admission_missing"
        if admission["admission_status"] != "admitted":
            return "external_admission_refused"
        if admission["calibration_status"] != "calibrated":
            return "outcome_distribution_uncalibrated"
        if not admission["in_distribution"] or admission["shift_flags"]:
            return "outcome_distribution_shifted"
        if admission["reference_units"] < self.minimum_reference_units:
            return "insufficient_calibration_reference_units"
        context = action.execution_context or (profile.context_identifier if action.context_bound else None)
        readout = action.readout or action.prediction_readout
        if (not context or not readout or action.time_hours is None
                or any(not action.expected_conditions.get(key) for key in ("dose", "assay", "platform"))):
            return "decision_domain_conditions_missing"
        if (admission["endpoint"], admission["readout"], admission["context"]) != (endpoint, readout, context):
            return "decision_domain_mismatch"
        if admission["binding_sha256"] != decision_action_binding(action, profile, self.endpoint):
            return "decision_action_binding_mismatch"
        if not isinstance(forecast, OutcomeForecast):
            return "no_outcome_forecast"
        if forecast.refusal:
            return str(forecast.refusal)
        if forecast.evidence_kind is not EvidenceKind.MODEL_PREDICTION:
            return "outcome_forecast_is_not_model_prediction"
        if forecast.model_version != admission["model_version"]:
            return "forecast_model_version_mismatch"
        if not isinstance(forecast.provenance, Mapping) or any(
                forecast.provenance.get(key) != admission[key] for key in _REVISIONS):
            return "forecast_calibration_binding_mismatch"
        if forecast.provenance.get("in_distribution") != "true" or forecast.provenance.get("shift_status") != "none":
            return "forecast_domain_unqualified"
        if any(type(branch.support) is not int or branch.support < self.minimum_branch_support
               for branch in forecast.branches):
            return "insufficient_forecast_branch_support"
        return None

    def select(self, candidates: frozenset[str], actions: Sequence[EvidenceAction],
               profile: FunctionalInterventionProfile, budget: float,
               forecasts: Mapping[str, OutcomeForecast], consequences: Mapping[str, frozenset[str]],
               *, endpoint: str | None, hypotheses: Sequence[MechanismHypothesis] = (),
               interpretation_rules: Sequence[OutcomeRule] = (), time_tolerance_hours: float = 1.0,
               require_context_match: bool = True) -> DecisionValuePlan:
        qualified = {}
        problem = self.hypotheses_refusal_reason(hypotheses) or self.interpretation_refusal_reason(
            interpretation_rules, time_tolerance_hours=time_tolerance_hours, require_context_match=require_context_match)
        if problem is None and consequences != outcome_consequences(interpretation_rules):
            problem = "decision_outcome_consequences_mismatch"
        for action in actions:
            forecast = forecasts.get(action.identifier)
            reason = problem or self.refusal_reason(action, profile, endpoint, forecast)
            qualified[action.identifier] = (
                replace(forecast, refusal=reason) if isinstance(forecast, OutcomeForecast)
                else OutcomeForecast(action.identifier, refusal=reason)
            )
        return select_decision_sensitive_action(
            candidates, actions, profile, budget, qualified, consequences,
            wrong_decision_loss=self.wrong_decision_loss, defer_loss=self.defer_loss,
            # A missing price belongs only to a refused action; zero is an audit placeholder.
            measurement_costs={action.identifier: self.measurement_costs.get(action.identifier, 0.0) for action in actions},
        )

    def payload(self) -> dict[str, object]:
        return {"receipt_sha256": self.receipt_sha256, "endpoint": self.endpoint, "hypotheses_sha256": self.hypotheses_sha256,
                "interpretation_sha256": self.interpretation_sha256,
                "wrong_decision_loss": self.wrong_decision_loss, "defer_loss": self.defer_loss,
                "minimum_reference_units": self.minimum_reference_units,
                "minimum_branch_support": self.minimum_branch_support,
                "measurement_costs": dict(self.measurement_costs),
                "utility_scope": "myopic hypothesis decision loss; does not license a development verdict",
                "authority": "external independent evaluation; hash verifies identity, not scientific validity"}
