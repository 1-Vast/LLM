"""A typed capability registry, and the compilation of an agent's repair proposal.

File summary
- Path: src/evaluation/capabilities.py
- Purpose: give the repair operator something real to propose. A registry publishes what
  each local release *could* supply - the quantity, the entity, the context, the price and
  the coverage - without publishing any value, and a policy proposes one capability for the
  premise its plan is missing. The framework compiles the proposal into a typed action or
  refuses it by name.
- Core points:
  - The registry is public: every arm sees the same offers, so a difference between arms is
    which offer was proposed and when, never who was allowed to see the catalogue.
  - Compilation never takes an outcome model from the proposal. Outcomes come from the
    case's declared template for that premise field, so a model can choose a capability but
    cannot invent what its result would mean.
  - Typed admission is the framework's own: the declared grant of the offer is compared
    against the case's premise requirement, so a lysate estimate or a foreign context is
    refused with the same reasons the executor would give.
  - Coverage is a property of the release, not of a result: a compound the release never
    assayed and a protein it never quantified are refused, and a missing value is never
    read as a negative measurement.
- Interfaces: `CapabilityOffer`, `CapabilityRegistry`, `CompiledRepair`, `ProposalRefusal`,
  `load_capability_registry`, `compile_proposal`, `canonical_repair_identifier`,
  `CAPABILITY_SCHEMA`
- Depends on: evaluation.cases (public case shape), evaluation.lab_cost, maestro.models
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from maestro.models import (
    BiologicalQuantity,
    EvidenceAction,
    EvidenceActionKind,
    PremiseGrant,
    PremiseRequirement,
)

from .lab_cost import LabCost, lab_cost_from_payload

CAPABILITY_SCHEMA = "maestro.capabilities.v1"
_SAFE = re.compile(r"[^A-Za-z0-9]+")


def _fold(name: str) -> str:
    """Folded compound identity: the same rule the source loaders use."""

    stripped = re.sub(r"\(.*?\)", " ", name)
    return re.sub(r"[^a-z0-9]", "", stripped.lower())


def canonical_repair_identifier(capability: str, compound: str, entity: str) -> str:
    """The identifier a compiled proposal always gets, so two arms proposing the same
    capability for the same compound and entity produce the same action.

    The compound is folded by the same rule the release readers use, so a policy that names
    `AZD-5438`, `AZD5438` or `azd 5438` reaches the identifier the licensing rules were
    written against. Without that, a pre-registered rule would silently fail to match an
    action that is in every other respect the one it names.
    """

    parts = [
        _SAFE.sub("_", capability).strip("_").lower(),
        _fold(compound),
        _SAFE.sub("_", entity).strip("_").lower(),
    ]
    return "repair__" + "__".join(part for part in parts if part)


@dataclass(frozen=True)
class ProposalRefusal(ValueError):
    """A refused proposal, carrying the machine-readable reason and its detail."""

    code: str
    detail: str = ""

    def __str__(self) -> str:  # pragma: no cover - message formatting only
        return f"{self.code}:{self.detail}" if self.detail else self.code


@dataclass(frozen=True)
class CapabilityOffer:
    """One registered measurement capability: what it would supply, and what it covers."""

    identifier: str
    description: str
    supplies: str
    quantity: BiologicalQuantity
    kind: EvidenceActionKind
    cost: float
    lab_cost: LabCost | None
    source: str
    source_sha256: str
    units: str | None = None
    context_identifier: str | None = None
    time_hours: float | None = None
    is_estimate: bool = False
    readout: str | None = None
    compounds: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    entity_is_proteome: bool = False
    note: str = ""

    def covers_compound(self, compound: str) -> bool:
        return _fold(compound) in {_fold(name) for name in self.compounds}

    def covers_entity(self, entity: str) -> bool:
        return self.entity_is_proteome or entity in set(self.entities)

    def grant(self, field: str, entity: str) -> PremiseGrant:
        """The typed grant this offer declares, for admission against a requirement.

        Quality is declared and passing, because a proposal is a bet that the record
        qualifies; what the declaration may not be optimistic about is meaning, and that is
        exactly what the typed comparison checks.
        """

        return PremiseGrant(
            field=field,
            source_action=self.identifier,
            quantity=self.quantity,
            is_estimate=self.is_estimate,
            entity=None if self.entity_is_proteome else entity,
            site=None,
            units=self.units,
            context_identifier=self.context_identifier,
            time_hours=self.time_hours,
            quality="declared",
            quality_passed=True,
            provenance=self.source,
        )

    def public_payload(self) -> Mapping[str, object]:
        """What a policy is shown: the declaration and the coverage, never a value."""

        return {
            "identifier": self.identifier,
            "description": self.description,
            "supplies": self.supplies,
            "quantity": self.quantity.value,
            "kind": self.kind.value,
            "units": self.units,
            "context_identifier": self.context_identifier,
            "time_hours": self.time_hours,
            "is_estimate": self.is_estimate,
            "cost": self.cost,
            "lab_cost": dict(self.lab_cost.to_payload()) if self.lab_cost is not None else None,
            "readout": self.readout,
            "covers_compounds": len(self.compounds),
            "covers_entities": "proteome" if self.entity_is_proteome else len(self.entities),
            "source": self.source,
            "source_sha256": self.source_sha256,
            "note": self.note,
        }


@dataclass(frozen=True)
class CapabilityRegistry:
    """The public catalogue of offers, with the digest of the file it was read from."""

    schema: str
    identifier: str
    offers: Mapping[str, CapabilityOffer]
    sha256: str
    path: str = ""

    def offer(self, identifier: str) -> CapabilityOffer | None:
        return self.offers.get(identifier)

    def public_payload(self) -> tuple[Mapping[str, object], ...]:
        return tuple(offer.public_payload() for offer in self.offers.values())

    def offers_for(self, premise: str) -> tuple[CapabilityOffer, ...]:
        return tuple(offer for offer in self.offers.values() if offer.supplies == premise)


def load_capability_registry(path: Path) -> CapabilityRegistry:
    """Read a capability registry, refusing a file that declares another schema."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    schema = str(payload.get("schema", ""))
    if schema != CAPABILITY_SCHEMA:
        raise ValueError(f"capability_registry_schema_unsupported:{schema or 'missing'}")
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        raise ValueError("capability_registry_identifier_missing")
    offers: dict[str, CapabilityOffer] = {}
    for entry in payload.get("capabilities", ()):
        offer = _offer(entry)
        if offer.identifier in offers:
            raise ValueError(f"capability_identifier_repeated:{offer.identifier}")
        offers[offer.identifier] = offer
    if not offers:
        raise ValueError("capability_registry_declares_no_capability")
    return CapabilityRegistry(
        schema=schema,
        identifier=identifier,
        offers=offers,
        sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        path=str(path),
    )


def _offer(entry: Any) -> CapabilityOffer:
    if not isinstance(entry, dict):
        raise ValueError("capability_entry_malformed")
    identifier = str(entry["identifier"]).strip()
    entities = tuple(str(item) for item in entry.get("entities", ()))
    return CapabilityOffer(
        identifier=identifier,
        description=str(entry.get("description", "")),
        supplies=str(entry["supplies"]),
        quantity=BiologicalQuantity(str(entry.get("quantity", BiologicalQuantity.UNSPECIFIED.value))),
        kind=EvidenceActionKind(str(entry.get("kind", EvidenceActionKind.READOUT_MEASUREMENT.value))),
        cost=float(entry.get("cost", 1.0)),
        lab_cost=(
            lab_cost_from_payload(entry["lab_cost"], where=identifier)
            if entry.get("lab_cost") is not None
            else None
        ),
        source=str(entry.get("source", "")),
        source_sha256=str(entry.get("source_sha256", "")),
        units=entry.get("units"),
        context_identifier=entry.get("context_identifier"),
        time_hours=float(entry["time_hours"]) if entry.get("time_hours") is not None else None,
        is_estimate=bool(entry.get("is_estimate", False)),
        readout=entry.get("readout"),
        compounds=tuple(str(item) for item in entry.get("compounds", ())),
        entities=entities,
        entity_is_proteome=bool(entry.get("entity_is_proteome", False)),
        note=str(entry.get("note", "")),
    )


@dataclass(frozen=True)
class CompiledRepair:
    """One admitted proposal: the typed action it became, and the claim it was made with."""

    identifier: str
    capability: str
    compound: str
    entity: str
    premise: str
    action: EvidenceAction
    lab_cost: LabCost | None
    claimed: Mapping[str, object]

    def payload(self) -> Mapping[str, object]:
        return {
            "identifier": self.identifier,
            "capability": self.capability,
            "compound": self.compound,
            "entity": self.entity,
            "premise": self.premise,
            "cost": self.action.cost,
            "lab_cost": dict(self.lab_cost.to_payload()) if self.lab_cost is not None else None,
            "expected_outcomes": dict(self.action.expected_outcomes),
            "claimed": dict(self.claimed),
        }


def compile_proposal(
    case,
    registry: CapabilityRegistry,
    proposal: Mapping[str, object],
    *,
    missing: Sequence[str] | None = None,
) -> CompiledRepair:
    """Compile one proposal into a typed action, or raise `ProposalRefusal` by name.

    ``case`` is a `PublicCase`. The premise must be one the case actually misses, the
    capability must be registered, must declare that premise, must cover the compound and
    the entity, and its declared grant must satisfy the case's typed requirement. Outcomes
    are read from the case's declared template for the premise, never from the proposal.
    """

    operator = str(proposal.get("operator", "")).strip()
    if operator != "register_supplier":
        raise ProposalRefusal("unknown_operator", operator or "missing")
    capability_id = str(proposal.get("capability", "")).strip()
    offer = registry.offer(capability_id)
    if offer is None:
        raise ProposalRefusal("capability_not_registered", capability_id or "missing")
    premise = str(proposal.get("supplies", "")).strip() or offer.supplies
    outstanding = set(missing if missing is not None else case.missing_premises())
    if premise not in outstanding:
        raise ProposalRefusal("premise_not_missing", premise)
    if offer.supplies != premise:
        raise ProposalRefusal("capability_does_not_supply_premise", f"{capability_id}:{premise}")
    compound = str(proposal.get("compound", "")).strip()
    if not compound:
        raise ProposalRefusal("proposal_names_no_compound", capability_id)
    if not offer.covers_compound(compound):
        raise ProposalRefusal("capability_does_not_cover_compound", f"{capability_id}:{compound}")
    entity = str(proposal.get("entity", "")).strip()
    if not entity:
        raise ProposalRefusal("proposal_names_no_entity", capability_id)
    if not offer.covers_entity(entity):
        raise ProposalRefusal("entity_not_quantified_in_capability", f"{capability_id}:{entity}")
    # The premise is about one entity *under one compound*, so the subject carries both. A
    # proposal that measures the right gene under the wrong compound is then refused by the
    # framework's own entity check rather than passing as the premise it does not answer.
    subject = entity if offer.entity_is_proteome else f"{entity}@{_fold(compound)}"
    requirement: PremiseRequirement | None = (case.premise_registry or {}).get(premise)
    if requirement is not None and requirement.is_typed:
        unmet = requirement.unmet_reasons(offer.grant(premise, subject))
        if unmet:
            raise ProposalRefusal(unmet[0].split(":")[0], ", ".join(unmet))
    template = (getattr(case, "repair_outcome_templates", {}) or {}).get(premise)
    if not template:
        raise ProposalRefusal("no_declared_outcome_template", premise)
    hypotheses = {item["identifier"] for item in case.hypotheses}
    if set(template) != hypotheses:
        raise ProposalRefusal("outcome_template_incomplete", premise)
    identifier = canonical_repair_identifier(offer.identifier, compound, entity)
    action = EvidenceAction(
        identifier=identifier,
        description=(
            f"{offer.description} Proposed repair: supply '{premise}' for {entity} under "
            f"{compound} from {offer.identifier}."
        ),
        cost=offer.cost,
        distinguishes=tuple(sorted(hypotheses)),
        kind=offer.kind,
        readout=offer.readout,
        time_hours=offer.time_hours,
        # One planned condition, and it is the package's folded compound identity rather than
        # one release's spelling, because the executor compares a planned condition against
        # the record's. The entity is not repeated here: it is already enforced, more strictly,
        # by the typed premise admission above, which compares the declared subject rather
        # than a free-text condition key.
        expected_conditions={"compound": _fold(compound)},
        expected_outcomes={name: str(value) for name, value in template.items()},
        supplies=(premise,),
        execution_context=offer.context_identifier,
        context_bound=offer.context_identifier is not None,
        quantity=offer.quantity,
        quantity_is_estimated=offer.is_estimate,
        entity=None if offer.entity_is_proteome else subject,
        units=offer.units,
    )
    return CompiledRepair(
        identifier=identifier,
        capability=offer.identifier,
        compound=compound,
        entity=entity,
        premise=premise,
        action=action,
        lab_cost=offer.lab_cost,
        claimed={
            key: proposal[key]
            for key in ("cost", "reliability", "rationale", "expected_outcomes", "predicts_licensed")
            if key in proposal
        },
    )
