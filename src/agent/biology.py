"""Conditioned biological assertions for retrieval, never case measurements."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Mapping


@dataclass(frozen=True)
class BiologicalConditions:
    species: str | None = None
    tissue: str | None = None
    cell_type: str | None = None
    context: str | None = None
    perturbation: str | None = None
    time_hours: float | None = None

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if value is None:
                continue
            if key == "time_hours":
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError("time_hours must be finite and nonnegative.")
            elif not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"Biological condition {key} must be canonical text or null.")

    def compare(self, requested: BiologicalConditions) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Unknown is not a match; unspecified query fields impose no restriction."""
        mismatches, unknown = [], []
        for key, value in asdict(requested).items():
            if value is None:
                continue
            actual = getattr(self, key)
            if actual is None:
                unknown.append(key)
            elif actual != value:
                mismatches.append(key)
        return tuple(mismatches), tuple(unknown)


@dataclass(frozen=True)
class BiologicalRelation:
    subject: str
    relation_type: str
    object: str
    evidence_type: str
    claim_level: str
    method: str
    conditions: BiologicalConditions = field(default_factory=BiologicalConditions)
    database: str | None = None
    database_version: str | None = None
    publication: str | None = None
    subject_scale: str | None = None
    object_scale: str | None = None
    controls: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("subject", "object"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"Biological relation requires {name}.")
        if self.relation_type not in {"coexpression", "physical_binding", "activation", "inhibition",
                                      "complex_membership", "pathway_membership", "state_transition",
                                      "measured_intervention_effect"}:
            raise ValueError("Unknown biological relation type.")
        if self.evidence_type not in {"experimental", "computational", "hypothesis"}:
            raise ValueError("Unknown biological evidence type.")
        if self.claim_level not in {"correlation", "regulatory_association", "causal_effect"}:
            raise ValueError("Unknown biological claim level.")
        if self.relation_type == "coexpression" and self.claim_level != "correlation":
            raise ValueError("Coexpression is a correlation, not a regulatory or causal effect.")
        if self.method not in {"observational", "physical_assay", "perturbation", "attention",
                                "feature_importance", "computational_prediction", "hypothesis"}:
            raise ValueError("Unknown biological evidence method.")
        if not isinstance(self.conditions, BiologicalConditions):
            raise ValueError("Biological conditions must be structured.")
        if self.method in {"attention", "feature_importance"} and (
            self.evidence_type != "computational" or self.claim_level != "correlation" or self.relation_type != "coexpression"
        ):
            raise ValueError("Attention and feature importance establish neither regulation nor causality.")
        if self.evidence_type == "experimental" and self.method not in {"observational", "physical_assay", "perturbation"}:
            raise ValueError("Experimental support requires an experimental method.")
        if self.claim_level == "causal_effect" and (
            self.evidence_type != "experimental" or self.method != "perturbation" or not self.controls
        ):
            raise ValueError("A causal effect requires experimental perturbation and declared controls.")
        for name in ("database", "database_version", "publication", "subject_scale", "object_scale"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be text or null.")
        for name in ("controls", "limitations"):
            values = getattr(self, name)
            if not isinstance(values, (tuple, list)) or any(not isinstance(v, str) or not v.strip() for v in values):
                raise ValueError(f"{name} must contain nonempty text.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BiologicalRelation:
        data = dict(data)
        data["conditions"] = BiologicalConditions(**data.get("conditions", {}))
        return cls(**data)


def relation_conflicts(records: Mapping[str, BiologicalRelation]) -> dict[str, list[dict[str, str]]]:
    """Opposite signs are review candidates, not adjudicated biological contradictions."""
    result: dict[str, list[dict[str, str]]] = {}
    items = list(records.items())
    for index, (left_id, left) in enumerate(items):
        for right_id, right in items[index + 1:]:
            if (left.subject, left.object) != (right.subject, right.object):
                continue
            if {left.relation_type, right.relation_type} != {"activation", "inhibition"}:
                continue
            mismatches, _ = left.conditions.compare(right.conditions)
            if mismatches:
                continue
            complete = all(value is not None for value in asdict(left.conditions).values()) and all(
                value is not None for value in asdict(right.conditions).values())
            reason = "opposite_sign_same_conditions" if complete else "opposite_sign_unresolved_conditions"
            result.setdefault(left_id, []).append({"evidence_id": right_id, "reason": reason})
            result.setdefault(right_id, []).append({"evidence_id": left_id, "reason": reason})
    return result
