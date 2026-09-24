"""Leakage-bounded public cases, private outcomes, and internal scoring contracts.

File summary
- Path: src/evaluation/cases.py
- Purpose: Define frozen public cases, hidden outcomes, and evaluator-only scoring.
- Core points:
  - `ReplayView` exposes only policy-allowed state; scoring answers stay hidden.
  - `CaseRepository` loads public cases plus evaluator-only result and scoring files.
  - A revealed record is a real measurement result gated by validation and context.
- Interfaces: `CaseRepository`, `ReplayEnvironment`, `ReplayView`, `PublicCase`, `EvidenceMenuItem`, `InitialEvidence`, `RevealedEvidence`, `ScoringSpec`, `ReplayCase`, `DecisionRule`, `measurement_result_from_reveal`
- Depends on: maestro.models
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from maestro.models import (
    BiologicalQuantity,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    PremiseRequirement,
)

from agent.cases import MeasurementResult

from .feasibility import (
    effective_fields,
    granted_premises,
    legal_actions,
    purchasable_actions,
    unmet_premises,
)
from .lab_cost import (
    CostingProfile,
    LabCost,
    SequenceLabCost,
    SharedControl,
    lab_cost_from_payload,
    sequence_lab_cost,
    shared_control_from_payload,
)


class RevealRefusal(ValueError):
    """A refused query, with a machine-readable reason code beside the message.

    It stays a ``ValueError`` with the message it always had, so every caller that
    handled a refused query keeps working; ``code`` is what a report counts.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class EvidenceMenuItem:
    """A public-case action with its declared prediction value, availability and lab price.

    ``lab_cost`` is None when nothing declares the action's price in wells and days; the
    ledger then refuses to price a sequence containing it rather than calling it free.
    """

    action: EvidenceAction
    prediction_value: float = 0.0
    available: bool = True
    lab_cost: LabCost | None = None


@dataclass(frozen=True)
class InitialEvidence:
    """A supplied public evidence statement with its source and limitations."""

    identifier: str
    statement: str
    source_id: str
    conditions: Mapping[str, str] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    evidence_kind: EvidenceKind = EvidenceKind.RETRIEVED_SOURCE


@dataclass(frozen=True)
class PublicCase:
    """Only material a policy may receive before choosing a registered query."""

    identifier: str
    provenance: str
    evaluation_status: str
    initial_evidence: tuple[InitialEvidence, ...]
    hypotheses: tuple[dict[str, str], ...]
    actions: tuple[EvidenceMenuItem, ...]
    budget: float
    context_identifier: str
    limitations: tuple[str, ...] = ()
    premise_registry: Mapping[str, PremiseRequirement] = field(default_factory=dict)
    shared_controls: Mapping[str, SharedControl] = field(default_factory=dict)
    # Declared, per premise field, what a record supplying that field would be expected to
    # show under each hypothesis. It is prior annotation in the same sense as an action's
    # `expected_outcomes`: public, author-declared, and the only place a compiled repair may
    # take its outcome model from, so a proposal can choose a capability but cannot invent
    # what its result would mean.
    repair_outcome_templates: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    def action(self, identifier: str) -> EvidenceMenuItem | None:
        return next((item for item in self.actions if item.action.identifier == identifier), None)

    def missing_premises(self) -> tuple[str, ...]:
        """Premise fields the case needs and no available registered action supplies.

        A field is needed when the premise registry declares it, when an action requires it,
        or when an action names it as its interpretation gate. Only available actions count
        as suppliers: an action the package cannot serve supplies nothing. These are the
        fields a repair proposal may target, and nothing else.
        """

        needed = set(self.premise_registry)
        for item in self.actions:
            needed.update(item.action.prerequisites)
            if item.action.interpretation_gate is not None:
                needed.add(item.action.interpretation_gate)
        supplied = {name for item in self.actions if item.available for name in item.action.supplies}
        return tuple(sorted(needed - supplied))

    def lab_costs(self) -> Mapping[str, LabCost | None]:
        """Every registered action's declared laboratory price, None where undeclared."""

        return {item.action.identifier: item.lab_cost for item in self.actions}

    def sequence_lab_cost(self, sequence: Sequence[str]) -> SequenceLabCost:
        """Wells and turnaround days of an executed sequence, shared controls charged once."""

        return sequence_lab_cost(self.lab_costs(), self.shared_controls, sequence)

    def untyped_premises(self) -> tuple[str, ...]:
        """Prerequisite fields no registry entry constrains beyond their name.

        These are the fields where admission is still a string comparison. They
        are reported rather than forbidden, so a legacy catalogue stays usable
        while being visibly untyped.
        """

        required = {name for item in self.actions for name in item.action.prerequisites}
        typed = {
            name
            for name, requirement in self.premise_registry.items()
            if requirement.is_typed
        }
        return tuple(sorted(required - typed))


@dataclass(frozen=True)
class DecisionRule:
    """Private evaluator criterion, never exposed through :class:`ReplayView`."""

    decision: DevelopmentAction
    required_outcomes: Mapping[str, str]
    required_interpretation_fields: tuple[str, ...] = ()
    require_record_validated: bool = True
    require_biological_quality: bool = False

    def matches(self, observed: Mapping[str, "RevealedEvidence"]) -> bool:
        required = tuple(self.required_outcomes.items())
        if not all(action_id in observed and observed[action_id].outcome == outcome for action_id, outcome in required):
            return False
        results = tuple(observed[action_id] for action_id, _ in required)
        if self.require_record_validated and not all(item.record_validated for item in results):
            return False
        if self.require_biological_quality and not all(item.biological_quality == "passed" for item in results):
            return False
        fields = {field for item in results for field in item.interpretation_fields}
        return set(self.required_interpretation_fields).issubset(fields)


@dataclass(frozen=True)
class FinalTestRecord:
    """An evaluator-only result that no policy can query, kept to test a terminal decision.

    This is the always-hidden partition of report sections 26 and 36: discovery data are
    revealed by budget, and a separate set of results is never readable by any strategy,
    so a stop or advance decision can be checked against data that did not shape it. A
    record names the development actions it would confirm and the ones it would
    contradict; it never names an answer the policy was meant to find.
    """

    identifier: str
    statement: str
    source_id: str
    outcome: str
    confirms: tuple[DevelopmentAction, ...]
    contradicts: tuple[DevelopmentAction, ...]
    record_validated: bool
    biological_quality: str
    evidence_kind: EvidenceKind
    limitations: tuple[str, ...] = ()

    @property
    def admissible(self) -> bool:
        """A final test counts only when it would have been admitted as a measurement."""

        return (
            self.record_validated
            and self.biological_quality == "passed"
            and self.evidence_kind is EvidenceKind.REAL_MEASUREMENT
        )


@dataclass(frozen=True)
class ScoringSpec:
    """The evaluator-only decision rules, critical actions and always-hidden results for one case."""

    decision_rules: tuple[DecisionRule, ...]
    critical_actions: frozenset[str]
    final_test: tuple[FinalTestRecord, ...] = ()
    # Hidden results for actions that exist only once a policy's repair proposal compiles,
    # keyed by the canonical repair identifier. They are evaluator-owned like every other
    # result: the environment receives one only when a compiled proposal is admitted.
    repair_outcomes: Mapping[str, "RevealedEvidence"] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayCase:
    """Evaluator-owned combination of a public case and private scoring specification."""

    public: PublicCase
    scoring: ScoringSpec


@dataclass(frozen=True)
class RevealedEvidence:
    action_identifier: str
    outcome: str
    statement: str
    source_id: str
    context_identifier: str | None
    time_hours: float | None
    conditions: Mapping[str, str]
    metrics: Mapping[str, str]
    record_count: int
    biological_replicates: int | None
    record_validated: bool
    biological_quality: str
    interpretation_fields: tuple[str, ...]
    limitations: tuple[str, ...]
    evidence_kind: EvidenceKind
    independent_units: int | None = None

    @property
    def usable_for_mechanism(self) -> bool:
        return self.record_validated and self.biological_quality == "passed"

    @property
    def admits_biological_fields(self) -> bool:
        """Whether this record's interpretation fields may satisfy a biological premise.

        Schema validity (``record_validated``) is not biological quality, and a
        retrieved or derived record is not a current-case measurement, so all
        three gates apply before a field can unlock a prerequisite (audit F08).
        """

        return (
            self.record_validated
            and self.biological_quality == "passed"
            and self.evidence_kind is EvidenceKind.REAL_MEASUREMENT
        )


def measurement_result_from_reveal(outcome: RevealedEvidence, *, result_id: str | None) -> MeasurementResult:
    """The single conversion from an authorized reveal to a measurement result.

    Every replay path uses this one admission mapping, so the same record is
    admitted identically in production and in every replay policy:

    - ``quality_passed`` requires both a validated record and a passed
      biological quality check; an unknown check is not a pass.
    - ``independent_units`` preserves the declared independent-unit metadata
      (falling back to declared biological replicates) and stays ``None`` when
      unknown; the record count is never substituted for it.
    """

    units = outcome.independent_units if outcome.independent_units is not None else outcome.biological_replicates
    return MeasurementResult(
        action_identifier=outcome.action_identifier,
        statement=outcome.statement,
        source_id=outcome.source_id,
        context_identifier=outcome.context_identifier,
        time_hours=outcome.time_hours,
        independent_units=units,
        quality_passed=outcome.record_validated and outcome.biological_quality == "passed",
        conditions=outcome.conditions,
        metrics=outcome.metrics,
        record_count=outcome.record_count,
        biological_replicates=outcome.biological_replicates,
        evidence_kind=outcome.evidence_kind,
        interpretation_fields=outcome.interpretation_fields,
        limitations=outcome.limitations,
        result_id=result_id,
    )


def _requirement_payload(requirement: PremiseRequirement | None) -> Mapping[str, object]:
    """The public half of a premise requirement, or an explicit untyped marker.

    A policy is entitled to know what a prerequisite field is required to mean.
    Saying "untyped" out loud is part of that: it tells the reader that the
    field is admitted on its name alone.
    """

    if requirement is None or not requirement.is_typed:
        return {"typed": False}
    return {
        "typed": True,
        "quantity": requirement.quantity.value,
        "entity": requirement.entity,
        "site": requirement.site,
        "units": requirement.units,
        "context_identifier": requirement.context_identifier,
        "time_hours": requirement.time_hours,
        "requires_direct_measurement": requirement.require_direct_measurement,
    }


@dataclass(frozen=True)
class ReplayView:
    """The policy-facing state; it deliberately omits scoring answers and critical actions."""

    case: PublicCase
    remaining_budget: float
    revealed: tuple[RevealedEvidence, ...]
    queried_actions: tuple[str, ...]
    # The public capability registry, when the run offers one: declarations and coverage
    # only, never a value. Empty for every package evaluated without a registry.
    capabilities: tuple[Mapping[str, object], ...] = ()

    @property
    def observed(self) -> Mapping[str, RevealedEvidence]:
        return {item.action_identifier: item for item in self.revealed}

    @property
    def spent(self) -> float:
        return self.case.budget - self.remaining_budget

    def available_actions(self) -> tuple[EvidenceMenuItem, ...]:
        """The shrinking purchasable menu, decided by the shared feasibility rule.

        An action whose premise is not yet measured stays visible here; whether
        it may run *now* is :meth:`executable_actions`.
        """

        return purchasable_actions(self.case, self.queried_actions, self.spent)

    def executable_actions(self) -> tuple[EvidenceMenuItem, ...]:
        """Actions that would be accepted if queried in this exact state."""

        return legal_actions(
            self.case,
            self.queried_actions,
            self.spent,
            effective_fields(self.observed),
            observed=self.observed,
        )

    def blocked_actions(self) -> Mapping[str, tuple[str, ...]]:
        """Purchasable actions whose premises are unmet, and which premise failed.

        This is the signal directed repair acts on. An action that is visible
        but not runnable names the premise standing between the policy and the
        measurement it wants, so the next step can be to supply that premise
        rather than to guess.
        """

        grants = granted_premises(self.case, self.observed)
        supplied = effective_fields(self.observed)
        blocked: dict[str, tuple[str, ...]] = {}
        for item in self.available_actions():
            problems = unmet_premises(self.case, item.action, supplied, grants)
            if problems:
                blocked[item.action.identifier] = problems
        return blocked

    def decision_state(self, *, required_premises: Sequence[str] = ()) -> Mapping[str, object]:
        """Separate "this decision's requirements are met" from "more evidence exists".

        Readiness is relative to *declared* requirements. With none declared
        there is nothing to be ready for, so the state is unresolved rather than
        ready: an empty argument list is not a decision criterion, and an
        exhausted menu is not a biological conclusion either. Where the case
        types a premise, the check is against the typed grant a record actually
        delivers, not against the spelling of the field.
        """

        from .planning import hypothesis_compatibility

        grants = granted_premises(self.case, self.observed)
        supplied = effective_fields(self.observed)
        registry = self.case.premise_registry or {}
        missing: list[str] = []
        for name in required_premises:
            requirement = registry.get(name)
            if requirement is None or not requirement.is_typed:
                if name not in supplied:
                    missing.append(f"{name}:not_supplied")
                continue
            candidates = grants.get(name, ())
            if not candidates:
                missing.append(f"{name}:not_supplied")
                continue
            failures = [requirement.unmet_reasons(grant) for grant in candidates]
            if all(failures):
                closest = min(failures, key=len)
                missing.append(f"{name}:{','.join(closest)}")

        reasons: list[str] = []
        if not required_premises:
            reasons.append("no_decision_requirements_declared")
        reasons.extend(missing)
        ready = bool(required_premises) and not missing
        observed_outcomes = {name: record.outcome for name, record in self.observed.items()}
        evidence_status = (
            hypothesis_compatibility(self.case, observed_outcomes).status.value
            if observed_outcomes
            else "no_observations"
        )
        return {
            "decision_ready": ready,
            "readiness": "ready" if ready else "unresolved",
            "readiness_reasons": tuple(reasons),
            "required_missing_premises": tuple(missing),
            "additional_evidence_available": bool(self.available_actions()),
            "evidence_status": evidence_status,
            "executable_now": tuple(item.action.identifier for item in self.executable_actions()),
            "blocked_on_premises": dict(self.blocked_actions()),
            "remaining_budget": self.remaining_budget,
        }

    def public_contract(self) -> tuple[Mapping[str, object], ...]:
        """Every registered action's public declaration, with its current status.

        This is the immutable half of the task state. It does not shrink when
        the budget is exhausted, so a terminal policy can still read what its
        own acquired outcome labels were declared to mean. Only public material
        appears here: no hidden outcome, no decision rule, no evaluator label.
        """

        executable = {item.action.identifier for item in self.executable_actions()}
        acquired = set(self.queried_actions)
        contract: list[Mapping[str, object]] = []
        for item in self.case.actions:
            action = item.action
            entry: dict[str, object] = {
                "identifier": action.identifier,
                "description": action.description,
                "cost": action.cost,
                "kind": action.kind.value,
                "quantity": action.quantity.value,
                "quantity_is_estimated": action.quantity_is_estimated,
                "readout": action.readout,
                "entity": action.entity,
                "site": action.site,
                "units": action.units,
                "prerequisites": list(action.prerequisites),
                "prerequisite_requirements": {
                    name: _requirement_payload(self.case.premise_registry.get(name))
                    for name in action.prerequisites
                },
                "supplies": list(action.supplies),
                "expected_outcome_by_hypothesis": dict(action.expected_outcomes),
                "registered_available": item.available,
                "acquired": action.identifier in acquired,
                "executable_now": action.identifier in executable,
            }
            # A laboratory price is public, like the abstract cost: section 36 puts wells and
            # turnaround on the menu a policy reads. It is added only where declared, so a
            # package without a costing declaration presents exactly the contract it had.
            if item.lab_cost is not None:
                entry["lab_cost"] = dict(item.lab_cost.to_payload())
            contract.append(entry)
        return tuple(contract)


class CaseRepository:
    """Load frozen public cases, evaluator-only outcomes and scoring, and the hidden partition.

    ``costing`` is an optional overlay of laboratory prices kept outside the frozen case
    files, so a package can be priced in wells and days without being edited. An overlay
    entry that prices no action in the package is refused, because a misspelt identifier
    would otherwise leave that action silently unpriced.
    """

    def __init__(self, public_directory: Path, private_directory: Path, *, costing: CostingProfile | None = None):
        self.public_directory = public_directory
        self.private_directory = private_directory
        self.costing = costing

    def load(self) -> tuple[tuple[ReplayCase, Mapping[str, RevealedEvidence]], ...]:
        loaded: list[tuple[ReplayCase, Mapping[str, RevealedEvidence]]] = []
        matched: set[str] = set()
        for public_path in sorted(self.public_directory.glob("*.json")):
            public = _public_case(_read_json(public_path))
            if self.costing is not None:
                public = apply_costing(public, self.costing)
                matched.update(name for name in self.costing.actions if public.action(name) is not None)
            private_path = self.private_directory / f"{public.identifier}.results.json"
            if not private_path.is_file():
                raise ValueError(f"Missing private result file for case '{public.identifier}'.")
            private = _read_json(private_path)
            scoring = replace(
                _scoring(private, public.identifier),
                final_test=_final_tests(private, public),
                repair_outcomes=_repair_outcomes(private, public),
            )
            loaded.append((ReplayCase(public, scoring), _outcomes(private, public)))
        if self.costing is not None:
            unmatched = sorted(set(self.costing.actions) - matched)
            if unmatched:
                raise ValueError("costing_entry_matches_no_action:" + ",".join(unmatched))
        return tuple(loaded)


def apply_costing(public: PublicCase, profile: CostingProfile) -> PublicCase:
    """Attach an overlay's prices to one case, refusing any disagreement with the case file."""

    items: list[EvidenceMenuItem] = []
    for item in public.actions:
        declared = profile.actions.get(item.action.identifier)
        if declared is None:
            items.append(item)
            continue
        if item.lab_cost is not None:
            if item.lab_cost.price_key() != declared.price_key():
                raise ValueError(f"costing_conflict:{public.identifier}:{item.action.identifier}")
            items.append(item)
            continue
        items.append(replace(item, lab_cost=declared))
    controls = dict(public.shared_controls)
    for name, control in profile.shared_controls.items():
        existing = controls.get(name)
        if existing is not None and (existing.wells, existing.turnaround_days) != (control.wells, control.turnaround_days):
            raise ValueError(f"costing_conflict:{public.identifier}:shared_control:{name}")
        controls.setdefault(name, control)
    for item in items:
        group = item.lab_cost.shared_control if item.lab_cost is not None else None
        if group is not None and group not in controls:
            raise ValueError(f"costing_shared_control_undeclared:{public.identifier}:{group}")
    return replace(public, actions=tuple(items), shared_controls=controls)


class ReplayEnvironment:
    """Budgeted query oracle. State is restored only from the active run's CaseStore."""

    def __init__(
        self,
        case: ReplayCase,
        outcomes: Mapping[str, RevealedEvidence],
        *,
        restored_action_ids: tuple[str, ...] = (),
        restored_spent: float = 0.0,
        capabilities: tuple[Mapping[str, object], ...] = (),
    ):
        self.case = case
        self._outcomes = dict(outcomes)
        self._capabilities = tuple(capabilities)
        self._admitted: list[str] = []
        unknown = [action_id for action_id in restored_action_ids if action_id not in self._outcomes]
        if unknown:
            # A restored ledger naming an action this environment holds no result for can only
            # come from a run that admitted a repair. Resuming it would silently drop the
            # admitted action, so the resume is refused by name instead.
            raise RevealRefusal(
                "resume_with_admitted_repairs_unsupported",
                "Restored actions without a registered result: " + ", ".join(unknown),
            )
        self._revealed = {action_id: self._outcomes[action_id] for action_id in restored_action_ids}
        self._spent = restored_spent
        expected_spent = sum(case.public.action(action_id).action.cost for action_id in restored_action_ids if case.public.action(action_id))
        if abs(expected_spent - restored_spent) > 1e-9:
            raise ValueError("Replay state and CaseStore budget do not agree.")

    @property
    def spent(self) -> float:
        return self._spent

    @property
    def admitted_repairs(self) -> tuple[str, ...]:
        return tuple(self._admitted)

    @property
    def outcomes(self) -> Mapping[str, RevealedEvidence]:
        """Every hidden result this environment holds, including admitted repairs.

        Evaluator-side only: it is what the scorer needs to ask whether a decision was
        reachable, and it is never reachable from a :class:`ReplayView`.
        """

        return dict(self._outcomes)

    def view(self) -> ReplayView:
        return ReplayView(
            case=self.case.public,
            remaining_budget=self.case.public.budget - self._spent,
            revealed=tuple(self._revealed.values()),
            queried_actions=tuple(self._revealed),
            capabilities=self._capabilities,
        )

    def admit(self, item: EvidenceMenuItem) -> None:
        """Add a compiled repair action to this run's menu, with its evaluator-held result.

        The action exists only for the policy whose proposal compiled, and only from this
        point on. Its hidden result comes from the evaluator-only repair store; a compiled
        action with no registered result stays on the menu and is refused on query with
        `no_registered_result`, exactly as a menu action without a result would be.
        """

        identifier = item.action.identifier
        if self.case.public.action(identifier) is not None:
            raise RevealRefusal("repair_shadows_registered_action", f"Action '{identifier}' is already on the menu.")
        public = replace(self.case.public, actions=self.case.public.actions + (item,))
        self.case = replace(self.case, public=public)
        outcome = self.case.scoring.repair_outcomes.get(identifier)
        if outcome is not None:
            self._outcomes[identifier] = outcome
        self._admitted.append(identifier)

    def query(self, action_identifier: str) -> RevealedEvidence:
        item = self.case.public.action(action_identifier)
        if item is None:
            raise RevealRefusal("action_not_in_menu", f"Action '{action_identifier}' is absent from the case menu.")
        if not item.available:
            raise RevealRefusal(
                "action_unavailable_in_package", f"Action '{action_identifier}' is unavailable in this case package."
            )
        if action_identifier in self._revealed:
            raise RevealRefusal("action_already_revealed", f"Action '{action_identifier}' was already queried.")
        if item.action.cost > self.view().remaining_budget:
            raise RevealRefusal("exceeds_remaining_budget", "Action exceeds the remaining evaluation budget.")
        missing = [name for name in item.action.prerequisites if name not in effective_fields(self.view().observed)]
        if missing:
            raise RevealRefusal("unmet_prerequisites", "Action has unmet prerequisites: " + ", ".join(missing))
        # The specific messages above stay for diagnosis; the shared rule is the
        # authority, so execution and scoring cannot drift apart.
        legal = {candidate.action.identifier for candidate in self.view().executable_actions()}
        if action_identifier not in legal:
            raise RevealRefusal(
                "not_legal_in_current_state", f"Action '{action_identifier}' is not legal in the current state."
            )
        outcome = self._outcomes.get(action_identifier)
        if outcome is None:
            raise RevealRefusal(
                "no_registered_result", f"No hidden result is registered for action '{action_identifier}'."
            )
        self._spent += item.action.cost
        self._revealed[action_identifier] = outcome
        return outcome


def _public_case(data: Any) -> PublicCase:
    if not isinstance(data, dict):
        raise ValueError("Case definition must be a JSON object.")
    actions = tuple(_item(value) for value in _list(data, "actions"))
    identifiers = [item.action.identifier for item in actions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Evidence-menu action identifiers must be unique.")
    budget = float(data["budget"])
    if budget < 0:
        raise ValueError("Case budget must be nonnegative.")
    return PublicCase(
        identifier=_text(data, "identifier"),
        provenance=_text(data, "provenance"),
        evaluation_status=_text(data, "evaluation_status"),
        initial_evidence=tuple(_initial(value) for value in _list(data, "initial_evidence")),
        hypotheses=tuple(_hypothesis(value) for value in _list(data, "hypotheses")),
        actions=actions,
        budget=budget,
        context_identifier=_text(data, "context_identifier"),
        limitations=tuple(str(item) for item in data.get("limitations", ())),
        premise_registry={
            str(name): _premise_requirement(str(name), value)
            for name, value in dict(data.get("premise_registry", {})).items()
        },
        shared_controls={
            str(name): shared_control_from_payload(str(name), value, where=f"{data.get('identifier')}:{name}")
            for name, value in dict(data.get("shared_controls", {})).items()
        },
        repair_outcome_templates={
            str(field_name): {str(hypothesis): str(outcome) for hypothesis, outcome in dict(template).items()}
            for field_name, template in dict(data.get("repair_outcome_templates", {})).items()
        },
    )


def _premise_requirement(name: str, data: Any) -> PremiseRequirement:
    """Read one field's declared meaning from a case file.

    A case that declares nothing keeps the pre-typing behaviour, which is how
    the frozen packages stay loadable.
    """

    if not isinstance(data, dict):
        raise ValueError(f"Premise requirement for '{name}' must be an object.")
    return PremiseRequirement(
        field=name,
        quantity=BiologicalQuantity(data.get("quantity", BiologicalQuantity.UNSPECIFIED.value)),
        entity=data.get("entity"),
        site=data.get("site"),
        units=data.get("units"),
        context_identifier=_optional_context(data.get("context_identifier")),
        time_hours=_optional_number(data.get("time_hours")),
        time_tolerance_hours=_optional_number(data.get("time_tolerance_hours")),
        require_direct_measurement=bool(data.get("require_direct_measurement", True)),
        note=str(data.get("note", "")),
    )


def _item(data: Any) -> EvidenceMenuItem:
    if not isinstance(data, dict):
        raise ValueError("Each action must be an object.")
    return EvidenceMenuItem(
        action=EvidenceAction(
            identifier=_text(data, "identifier"),
            description=_text(data, "description"),
            cost=float(data["cost"]),
            distinguishes=tuple(str(item) for item in _list(data, "distinguishes")),
            kind=EvidenceActionKind(data.get("kind", EvidenceActionKind.READOUT_MEASUREMENT.value)),
            prerequisites=tuple(str(item) for item in data.get("prerequisites", ())),
            readout=data.get("readout"),
            time_hours=_optional_number(data.get("time_hours")),
            expected_conditions={str(key): str(value) for key, value in dict(data.get("expected_conditions", {})).items()},
            expected_outcomes={str(key): str(value) for key, value in dict(data.get("expected_outcomes", {})).items()},
            supplies=tuple(str(item) for item in data.get("supplies", ())),
            execution_context=_optional_context(data.get("execution_context")),
            context_bound=bool(data.get("context_bound", True)),
            quantity=BiologicalQuantity(data.get("quantity", BiologicalQuantity.UNSPECIFIED.value)),
            quantity_is_estimated=bool(data.get("quantity_is_estimated", False)),
            entity=data.get("entity"),
            site=data.get("site"),
            units=data.get("units"),
            interpretation_gate=_optional_text(data.get("interpretation_gate")),
        ),
        prediction_value=float(data.get("prediction_value", 0.0)),
        available=bool(data.get("available", True)),
        lab_cost=(
            lab_cost_from_payload(data["lab_cost"], where=str(data.get("identifier")))
            if data.get("lab_cost") is not None
            else None
        ),
    )


def _final_tests(data: Any, public: PublicCase) -> tuple[FinalTestRecord, ...]:
    """Read the always-hidden partition, refusing any record a policy could reach.

    A held-back record that shares an identifier with a menu action or a revealable result
    would be one query away from a policy, which is exactly the leak the partition exists
    to prevent, so the overlap is refused by name rather than resolved.
    """

    values = data.get("final_test", []) if isinstance(data, dict) else []
    if not isinstance(values, list):
        raise ValueError(f"final_test_malformed:{public.identifier}: 'final_test' must be a JSON list.")
    menu = {item.action.identifier for item in public.actions}
    revealable = {
        str(value.get("action_identifier"))
        for key in ("results", "repair_results")
        for value in data.get(key, ())
        if isinstance(value, dict)
    }
    records: list[FinalTestRecord] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            raise ValueError(f"final_test_malformed:{public.identifier}: each record must be an object.")
        identifier = _text(value, "identifier")
        if identifier in menu or identifier in revealable:
            raise ValueError(f"final_test_record_shadows_public_action:{public.identifier}:{identifier}")
        if identifier in seen:
            raise ValueError(f"final_test_record_repeated:{public.identifier}:{identifier}")
        seen.add(identifier)
        confirms = tuple(DevelopmentAction(str(item)) for item in value.get("confirms", ()))
        contradicts = tuple(DevelopmentAction(str(item)) for item in value.get("contradicts", ()))
        if not confirms and not contradicts:
            raise ValueError(f"final_test_record_bears_on_no_decision:{public.identifier}:{identifier}")
        if set(confirms) & set(contradicts):
            raise ValueError(f"final_test_record_confirms_and_contradicts:{public.identifier}:{identifier}")
        records.append(
            FinalTestRecord(
                identifier=identifier,
                statement=_text(value, "statement"),
                source_id=_text(value, "source_id"),
                outcome=_text(value, "outcome"),
                confirms=confirms,
                contradicts=contradicts,
                record_validated=bool(value.get("record_validated", False)),
                biological_quality=_quality(value.get("biological_quality", "unknown")),
                evidence_kind=EvidenceKind(value.get("evidence_kind", EvidenceKind.REAL_MEASUREMENT.value)),
                limitations=tuple(str(item) for item in value.get("limitations", ())),
            )
        )
    return tuple(records)


def _initial(data: Any) -> InitialEvidence:
    if not isinstance(data, dict):
        raise ValueError("Each initial evidence item must be an object with a source identifier.")
    return InitialEvidence(
        identifier=_text(data, "identifier"), statement=_text(data, "statement"), source_id=_text(data, "source_id"),
        conditions={str(key): str(value) for key, value in dict(data.get("conditions", {})).items()},
        limitations=tuple(str(item) for item in data.get("limitations", ())),
        evidence_kind=EvidenceKind(data.get("evidence_kind", EvidenceKind.RETRIEVED_SOURCE.value)),
    )


def _outcomes(data: Any, case: PublicCase) -> Mapping[str, RevealedEvidence]:
    if not isinstance(data, dict) or data.get("case_id") != case.identifier:
        raise ValueError(f"Private results must identify case '{case.identifier}'.")
    registered = {item.action.identifier for item in case.actions}
    outcomes: dict[str, RevealedEvidence] = {}
    for value in _list(data, "results"):
        if not isinstance(value, dict):
            raise ValueError("Each private result must be an object.")
        action_id = _text(value, "action_identifier")
        if action_id not in registered:
            raise ValueError(f"Private results name action '{action_id}' outside the public menu.")
        if action_id in outcomes:
            raise ValueError(f"Private results repeat action '{action_id}'.")
        outcomes[action_id] = RevealedEvidence(
            action_identifier=action_id, outcome=_text(value, "outcome"), statement=_text(value, "statement"),
            source_id=_text(value, "source_id"), context_identifier=_optional_text(value.get("context_identifier")),
            time_hours=_optional_number(value.get("time_hours")),
            conditions={str(key): str(item) for key, item in dict(value.get("conditions", {})).items()},
            metrics={str(key): str(item) for key, item in dict(value.get("metrics", {})).items()},
            record_count=int(value.get("record_count", 1)),
            biological_replicates=_optional_integer(value.get("biological_replicates")),
            record_validated=bool(value.get("record_validated", False)),
            biological_quality=_quality(value.get("biological_quality", "unknown")),
            interpretation_fields=tuple(str(item) for item in value.get("interpretation_fields", ())),
            limitations=tuple(str(item) for item in value.get("limitations", ())),
            evidence_kind=EvidenceKind(value.get("evidence_kind", EvidenceKind.REAL_MEASUREMENT.value)),
            independent_units=_optional_integer(value.get("independent_units")),
        )
    return outcomes


def _repair_outcomes(data: Any, case: PublicCase) -> Mapping[str, RevealedEvidence]:
    """Evaluator-held results for actions that exist only once a repair proposal compiles.

    An entry must carry a canonical repair identifier, must not shadow a registered menu
    action and must not repeat. Each violation is refused by name, because a result that a
    menu query could reach would leak outside the repair route it belongs to.
    """

    values = data.get("repair_results", []) if isinstance(data, dict) else []
    if not isinstance(values, list):
        raise ValueError(f"repair_results_malformed:{case.identifier}")
    registered = {item.action.identifier for item in case.actions}
    outcomes: dict[str, RevealedEvidence] = {}
    for value in values:
        if not isinstance(value, dict):
            raise ValueError(f"repair_results_malformed:{case.identifier}")
        action_id = _text(value, "action_identifier")
        if not action_id.startswith("repair__"):
            raise ValueError(f"repair_result_identifier_not_canonical:{case.identifier}:{action_id}")
        if action_id in registered:
            raise ValueError(f"repair_result_shadows_menu_action:{case.identifier}:{action_id}")
        if action_id in outcomes:
            raise ValueError(f"repair_result_repeated:{case.identifier}:{action_id}")
        outcomes[action_id] = RevealedEvidence(
            action_identifier=action_id, outcome=_text(value, "outcome"), statement=_text(value, "statement"),
            source_id=_text(value, "source_id"), context_identifier=_optional_text(value.get("context_identifier")),
            time_hours=_optional_number(value.get("time_hours")),
            conditions={str(key): str(item) for key, item in dict(value.get("conditions", {})).items()},
            metrics={str(key): str(item) for key, item in dict(value.get("metrics", {})).items()},
            record_count=int(value.get("record_count", 1)),
            biological_replicates=_optional_integer(value.get("biological_replicates")),
            record_validated=bool(value.get("record_validated", False)),
            biological_quality=_quality(value.get("biological_quality", "unknown")),
            interpretation_fields=tuple(str(item) for item in value.get("interpretation_fields", ())),
            limitations=tuple(str(item) for item in value.get("limitations", ())),
            evidence_kind=EvidenceKind(value.get("evidence_kind", EvidenceKind.REAL_MEASUREMENT.value)),
            independent_units=_optional_integer(value.get("independent_units")),
        )
    return outcomes


def _scoring(data: Any, case_id: str) -> ScoringSpec:
    if not isinstance(data, dict) or data.get("case_id") != case_id:
        raise ValueError(f"Private scoring must identify case '{case_id}'.")
    scoring = data.get("scoring")
    if not isinstance(scoring, dict):
        raise ValueError("Private results require evaluator-only 'scoring'.")
    return ScoringSpec(
        decision_rules=tuple(_rule(value) for value in _list(scoring, "decision_rules")),
        critical_actions=frozenset(str(item) for item in _list(scoring, "critical_actions")),
    )


def _hypothesis(data: Any) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ValueError("Each hypothesis must be an object.")
    return {"identifier": _text(data, "identifier"), "description": _text(data, "description"), "development_action": _text(data, "development_action")}


def _rule(data: Any) -> DecisionRule:
    if not isinstance(data, dict) or not isinstance(data.get("required_outcomes"), dict):
        raise ValueError("Each decision rule requires an outcome map.")
    return DecisionRule(
        decision=DevelopmentAction(_text(data, "decision")),
        required_outcomes={str(key): str(value) for key, value in data["required_outcomes"].items()},
        required_interpretation_fields=tuple(str(item) for item in data.get("required_interpretation_fields", ())),
        require_record_validated=bool(data.get("require_record_validated", True)),
        require_biological_quality=bool(data.get("require_biological_quality", False)),
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _list(data: Mapping[str, Any], name: str) -> list[Any]:
    value = data.get(name)
    if not isinstance(value, list):
        raise ValueError(f"'{name}' must be a JSON list.")
    return value


def _text(data: Mapping[str, Any], name: str) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{name}' must be nonempty text.")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _optional_integer(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and value >= 0 else None


def _quality(value: Any) -> str:
    if value not in {"passed", "failed", "unknown"}:
        raise ValueError("biological_quality must be 'passed', 'failed', or 'unknown'.")
    return str(value)


def _optional_context(value: object) -> str | None:
    """An action's declared execution context; absent means the case's own context."""

    return value.strip() if isinstance(value, str) and value.strip() else None
