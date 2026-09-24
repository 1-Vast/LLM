"""A licence certificate for a repair-produced measurement, and the rates it makes reportable.

File summary
- Path: src/maestro/licence.py
- Purpose: turn the update rules the framework already enforces into one auditable object, so
  "this result may update the mechanism contrast" is a certificate a reader can check rather
  than an implicit consequence of field overlap.
- Core points:
  - Four gates, named and recorded per certificate: input validity (does the record carry the
    typed quantity the premise declares), outcome support (does a licensed result exist for the
    declared outcome classes and is the observed value one of them), identifiability (is the
    comparison inside one context and time window) and incremental utility (does the repair
    beat the exact optimum over the visible menu).
  - Two decisions, deliberately separate. `updates_licensed` is governed by the first three
    gates, because a qualified result may update the contrast whether or not the repair that
    produced it was worth buying. `repair_credited` needs all four, which is the gate that
    would have caught the recorded tie between directed repair and reactive selection.
  - Nothing here is a probability model and nothing here is biological evidence. The rates are
    counts over recorded events, so a better predictor cannot inflate them.
- Interfaces: `GateVerdict`, `LicenceCertificate`, `LicenceAudit`, `GATES`, `input_validity`,
  `outcome_support`, `identifiability`, `incremental_utility`, `issue_licence`, `audit_licences`
- Depends on: maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .models import EvidenceScope, PremiseGrant, PremiseRequirement

GATES = ("input_validity", "outcome_support", "identifiability", "incremental_utility")
UTILITY_TOLERANCE = 1e-9


@dataclass(frozen=True)
class GateVerdict:
    """One gate, its verdict, and the observation that decided it."""

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if self.name not in GATES:
            raise ValueError(f"Unregistered licence gate '{self.name}'.")


@dataclass(frozen=True)
class LicenceCertificate:
    """What one repair-produced measurement is allowed to do, and whether it earns credit.

    ``authorized_fields`` and ``refused_fields`` are the premise fields the record does and
    does not discharge. The scope narrows with the first three gates: a failed input-validity
    gate limits the update to measurement feasibility, a failed support or identifiability gate
    limits it to the plan, and only a record that passes all three may update the mechanism
    contrast.
    """

    contrast_identifier: str
    action_identifier: str
    gates: tuple[GateVerdict, ...]
    authorized_fields: tuple[str, ...] = ()
    refused_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        names = tuple(gate.name for gate in self.gates)
        if names != GATES:
            raise ValueError("A certificate must record the four gates in order: " + ", ".join(GATES))

    def gate(self, name: str) -> GateVerdict:
        return next(gate for gate in self.gates if gate.name == name)

    @property
    def updates_licensed(self) -> bool:
        """Whether a qualified result may update the mechanism contrast."""

        return all(self.gate(name).passed for name in GATES[:3])

    @property
    def repair_credited(self) -> bool:
        """Whether the *repair* that produced the record earns credit over the visible menu."""

        return all(gate.passed for gate in self.gates)

    @property
    def scope(self) -> EvidenceScope:
        """The strongest update this record licenses, narrowed by the gate that failed."""

        if not self.gate("input_validity").passed:
            return EvidenceScope.MEASUREMENT_FEASIBILITY
        if not self.gate("outcome_support").passed or not self.gate("identifiability").passed:
            return EvidenceScope.PLAN_LIMITATION
        return EvidenceScope.MECHANISM_CONTRAST

    def as_row(self) -> Mapping[str, object]:
        return {
            "contrast": self.contrast_identifier,
            "action": self.action_identifier,
            "updates_licensed": self.updates_licensed,
            "repair_credited": self.repair_credited,
            "scope": self.scope.value,
            "gates": {gate.name: gate.passed for gate in self.gates},
            "authorized_fields": list(self.authorized_fields),
            "refused_fields": list(self.refused_fields),
        }


def input_validity(requirement: PremiseRequirement | None, grant: PremiseGrant | None) -> GateVerdict:
    """Does the record carry the quantity, entity, site, units, context and time the premise declares?

    An untyped premise passes by declaration: the field name is then the only claim, which is
    recorded in the verdict rather than hidden. This is the framework's own typed admission,
    called rather than re-derived.
    """

    if requirement is None:
        return GateVerdict("input_validity", True, "no typed requirement is declared for this premise")
    if grant is None:
        return GateVerdict("input_validity", False, "no grant was declared by the supplying record")
    unmet = requirement.unmet_reasons(grant)
    if unmet:
        return GateVerdict("input_validity", False, "typed admission refused: " + "; ".join(unmet))
    return GateVerdict("input_validity", True, "the declared grant satisfies the typed requirement")


def outcome_support(
    *,
    declared_outcomes: Mapping[str, str],
    hypotheses: Sequence[str],
    observed_outcome: str | None,
) -> GateVerdict:
    """Does a licensed result exist for the declared classes, and is the observed value one?

    An undeclared observation is not support and not refutation: the declaration says nothing
    about that value, so it cannot eliminate anything and cannot license an update either.
    """

    missing = [hypothesis for hypothesis in hypotheses if hypothesis not in declared_outcomes]
    if missing:
        return GateVerdict(
            "outcome_support",
            False,
            "no declared outcome for: " + ", ".join(missing),
        )
    if observed_outcome is None:
        return GateVerdict("outcome_support", True, "declared classes cover every hypothesis; no value observed yet")
    if observed_outcome not in set(declared_outcomes.values()):
        return GateVerdict(
            "outcome_support",
            False,
            f"observed value '{observed_outcome}' is not among the declared outcomes",
        )
    return GateVerdict("outcome_support", True, f"observed value '{observed_outcome}' is declared")


def identifiability(
    *,
    planned_context: str | None,
    observed_context: str | None,
    planned_time_hours: float | None = None,
    observed_time_hours: float | None = None,
    time_tolerance_hours: float | None = None,
) -> GateVerdict:
    """Is the comparison inside one context and one time window?

    A missing value on either side is reported as a refusal rather than assumed equal: an
    unmatchable condition is exactly what makes two results incomparable, which is the failure
    this certificate exists to name.
    """

    if planned_context is None or observed_context is None:
        return GateVerdict("identifiability", False, "context is missing on one side of the comparison")
    if planned_context != observed_context:
        return GateVerdict(
            "identifiability", False, f"context mismatch: planned '{planned_context}', observed '{observed_context}'"
        )
    if planned_time_hours is None or observed_time_hours is None:
        return GateVerdict("identifiability", True, "contexts match; no time window was declared to compare")
    tolerance = time_tolerance_hours if time_tolerance_hours is not None else 0.0
    if abs(planned_time_hours - observed_time_hours) > tolerance:
        return GateVerdict(
            "identifiability",
            False,
            f"time mismatch: planned {planned_time_hours}h, observed {observed_time_hours}h, tolerance {tolerance}h",
        )
    return GateVerdict("identifiability", True, "context and time window match")


def incremental_utility(value_over_the_menu_only_optimum: float | None, *, tolerance: float = UTILITY_TOLERANCE) -> GateVerdict:
    """Does the repair beat the exact optimum over the visible menu?

    The comparison is against a bound, not against another heuristic: the menu-only optimum is
    the best any contingent policy restricted to the unrepaired declarations can do, at any
    search depth. A repair whose certified value is not strictly positive therefore earns no
    credit, however plausible its rationale reads. ``None`` means no exact bound was computed,
    which is refused rather than assumed favourable.
    """

    if value_over_the_menu_only_optimum is None:
        return GateVerdict("incremental_utility", False, "no exact menu-only bound was computed")
    if value_over_the_menu_only_optimum > tolerance:
        return GateVerdict(
            "incremental_utility",
            True,
            f"certified value {value_over_the_menu_only_optimum:.6f} is strictly above the menu-only optimum",
        )
    return GateVerdict(
        "incremental_utility",
        False,
        f"certified value {value_over_the_menu_only_optimum:.6f} does not beat the menu-only optimum",
    )


def issue_licence(
    *,
    contrast_identifier: str,
    action_identifier: str,
    requirement: PremiseRequirement | None = None,
    grant: PremiseGrant | None = None,
    authorized_fields: Sequence[str] = (),
    refused_fields: Sequence[str] = (),
    declared_outcomes: Mapping[str, str] | None = None,
    hypotheses: Sequence[str] = (),
    observed_outcome: str | None = None,
    planned_context: str | None = None,
    observed_context: str | None = None,
    planned_time_hours: float | None = None,
    observed_time_hours: float | None = None,
    time_tolerance_hours: float | None = None,
    certified_value: float | None = None,
) -> LicenceCertificate:
    """Record all four gates for one repair-produced measurement."""

    return LicenceCertificate(
        contrast_identifier=contrast_identifier,
        action_identifier=action_identifier,
        gates=(
            input_validity(requirement, grant),
            outcome_support(
                declared_outcomes=declared_outcomes or {},
                hypotheses=hypotheses,
                observed_outcome=observed_outcome,
            ),
            identifiability(
                planned_context=planned_context,
                observed_context=observed_context,
                planned_time_hours=planned_time_hours,
                observed_time_hours=observed_time_hours,
                time_tolerance_hours=time_tolerance_hours,
            ),
            incremental_utility(certified_value),
        ),
        authorized_fields=tuple(dict.fromkeys(authorized_fields)),
        refused_fields=tuple(dict.fromkeys(refused_fields)),
    )


@dataclass(frozen=True)
class LicenceAudit:
    """Counts over recorded events: the two rates that cannot be inflated by a better model."""

    certificates: int
    updates_licensed: int
    repairs_credited: int
    updates_applied: int
    updates_applied_beyond_the_licence: int
    readouts_bought: int
    readouts_bought_without_a_passing_gate: int

    @property
    def unlicensed_update_rate(self) -> float | None:
        if self.updates_applied == 0:
            return None
        return self.updates_applied_beyond_the_licence / self.updates_applied

    @property
    def gate_bypass_rate(self) -> float | None:
        if self.readouts_bought == 0:
            return None
        return self.readouts_bought_without_a_passing_gate / self.readouts_bought

    def as_row(self) -> Mapping[str, object]:
        return {
            "certificates": self.certificates,
            "updates_licensed": self.updates_licensed,
            "repairs_credited": self.repairs_credited,
            "updates_applied": self.updates_applied,
            "unlicensed_update_rate": self.unlicensed_update_rate,
            "readouts_bought": self.readouts_bought,
            "gate_bypass_rate": self.gate_bypass_rate,
        }


def audit_licences(
    certificates: Sequence[LicenceCertificate],
    *,
    applied_updates: Sequence[tuple[str, EvidenceScope]] = (),
    gate_events: Sequence[tuple[str, bool, bool]] = (),
) -> LicenceAudit:
    """Count applied updates that exceeded their licence, and readouts bought without a gate.

    ``applied_updates`` pairs an action identifier with the scope the update was actually
    applied at; an update is beyond its licence when no certificate for that action licenses a
    scope at least as strong. ``gate_events`` pairs a readout identifier with whether its gate
    passed and whether the readout was bought.
    """

    by_action: dict[str, list[LicenceCertificate]] = {}
    for certificate in certificates:
        by_action.setdefault(certificate.action_identifier, []).append(certificate)
    rank = {
        EvidenceScope.MEASUREMENT_FEASIBILITY: 0,
        EvidenceScope.INTERVENTION_IMPLEMENTATION: 1,
        EvidenceScope.PLAN_LIMITATION: 2,
        EvidenceScope.MECHANISM_CONTRAST: 3,
    }
    beyond = 0
    for action, applied_scope in applied_updates:
        licensed = [certificate for certificate in by_action.get(action, ()) if certificate.updates_licensed]
        if not licensed or max(rank[certificate.scope] for certificate in licensed) < rank[applied_scope]:
            beyond += 1
    readouts = [event for event in gate_events if event[2]]
    return LicenceAudit(
        certificates=len(certificates),
        updates_licensed=sum(1 for certificate in certificates if certificate.updates_licensed),
        repairs_credited=sum(1 for certificate in certificates if certificate.repair_credited),
        updates_applied=len(applied_updates),
        updates_applied_beyond_the_licence=beyond,
        readouts_bought=len(readouts),
        readouts_bought_without_a_passing_gate=sum(1 for _, passed, bought in readouts if not passed),
    )
