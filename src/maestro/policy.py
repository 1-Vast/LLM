"""Typed, prediction-only input handed to an acquisition policy.

The policy boundary deliberately contains legal actions, visible evidence and
calibrated predictions only. Evaluator truth, future outcomes and mechanism
annotations are not fields on this object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .models import EvidenceAction


_HIDDEN_FIELDS = frozenset({
    "truth", "hidden_truth", "ground_truth", "groundtruth", "heldout", "held_out",
    "klass", "mechanism", "annotation", "annotations", "mechanism_annotation",
    "mechanism_class", "mechanism_label", "evaluator", "future_outcome",
    "future_action_outcome", "outcome_truth", "truth_label", "heldout_profile",
    "data", "conditions", "shift", "compounds", "index", "outcomes",
})


def _forbidden_fields(value, path: str = "$") -> list[str]:
    """Reject evaluator-only keys even when callers construct PolicyInput directly."""

    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            name = str(key).strip().lower()
            if name in _HIDDEN_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            problems.extend(_forbidden_fields(nested, f"{path}.{key}"))
    elif isinstance(value, (tuple, list)):
        for index, nested in enumerate(value):
            problems.extend(_forbidden_fields(nested, f"{path}[{index}]"))
    elif hasattr(value, "__dict__"):
        for key, nested in vars(value).items():
            if str(key).strip().lower() in _HIDDEN_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            if isinstance(nested, (Mapping, tuple, list)):
                problems.extend(_forbidden_fields(nested, f"{path}.{key}"))
    return problems


def _freeze_value(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(nested) for key, nested in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({key: _freeze_value(nested) for key, nested in value.items()})


@dataclass(frozen=True)
class PolicyInput:
    """The complete public state an acquisition policy is allowed to inspect."""

    visible_evidence: tuple[Any, ...] = ()
    legal_actions: tuple[EvidenceAction, ...] = ()
    budget: float = 0.0
    calibrated_action_distributions: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        evidence = ((self.visible_evidence,) if isinstance(self.visible_evidence, Mapping)
                    else tuple(self.visible_evidence))
        problems = _forbidden_fields(evidence, "$.visible_evidence")
        problems.extend(_forbidden_fields(self.calibrated_action_distributions, "$.calibrated"))
        problems.extend(_forbidden_fields(self.provenance, "$.provenance"))
        if problems:
            raise ValueError("; ".join(problems))
        if (isinstance(self.budget, bool) or not isinstance(self.budget, (int, float))
                or not math.isfinite(float(self.budget)) or self.budget < 0):
            raise ValueError("policy budget must be a finite nonnegative number")
        if not all(isinstance(action, EvidenceAction) for action in self.legal_actions):
            raise TypeError("legal_actions must contain EvidenceAction values")
        identifiers = {action.identifier for action in self.legal_actions}
        distributions = {
            str(identifier): _freeze_mapping(values)
            for identifier, values in self.calibrated_action_distributions.items()
        }
        unknown = set(distributions) - identifiers
        if unknown:
            raise ValueError(f"predictions supplied for non-legal actions: {sorted(unknown)}")
        for action_identifier, distribution in distributions.items():
            if any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(float(value)) or float(value) < 0
                   for value in distribution.values()):
                raise ValueError(f"invalid calibrated distribution: {action_identifier}")
        if any(not isinstance(key, str) or not key.strip() for key in self.provenance):
            raise ValueError("policy provenance keys must be nonempty strings")
        object.__setattr__(self, "visible_evidence", tuple(_freeze_value(item) for item in evidence))
        object.__setattr__(self, "legal_actions", tuple(self.legal_actions))
        object.__setattr__(self, "calibrated_action_distributions", MappingProxyType(distributions))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    @property
    def action_ids(self) -> tuple[str, ...]:
        return tuple(action.identifier for action in self.legal_actions)

    def distribution_for(self, action_identifier: str) -> Mapping[str, float] | None:
        return self.calibrated_action_distributions.get(action_identifier)


def make_policy_input(
    *,
    visible_evidence: Sequence[Any] = (),
    legal_actions: Sequence[EvidenceAction] = (),
    budget: float,
    calibrated_action_distributions: Mapping[str, Mapping[str, float]] | None = None,
    provenance: Mapping[str, str] | None = None,
) -> PolicyInput:
    """Build a policy input without accepting an evaluator or raw-data object."""

    return PolicyInput(
        visible_evidence=tuple(visible_evidence),
        legal_actions=tuple(legal_actions),
        budget=budget,
        calibrated_action_distributions=calibrated_action_distributions or {},
        provenance=provenance or {},
    )
