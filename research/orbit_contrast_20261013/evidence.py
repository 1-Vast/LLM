"""Domain-general evidence interface (study prototype; see INTERFACE.md).

File summary
- Path: research/orbit_contrast_20261013/evidence.py
- Purpose: typed entities, evidence records, queries and orbit declarations, with named refusals,
  so that routes read evidence without merging observational with interventional records, without
  treating missing evidence as negative, and without aliasing knockdown, inhibition, engagement and
  efficacy.
- Interfaces: `Entity`, `EvidenceRecord`, `Query`, `OrbitSpec`, `Absent`, `EvidenceStore`,
  `EvidenceRefused`, `transport`, `PREDICATES`.
- Depends on: the standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

OBSERVATIONS = ("curated_annotation", "assay_measurement", "interventional_response",
                "observational_association", "computed_similarity", "transported")
INTERVENTIONAL = {"interventional_response"}
OBSERVATIONAL = {"observational_association", "computed_similarity"}
INTERVENTIONS = ("genetic_knockdown", "genetic_knockout", "genetic_overexpression", "chemical_perturbation",
                 "inhibition", "activation", "binding", "engagement", "efficacy")
# predicate -> (subject kind, object kind or None for a vector-valued record)
PREDICATES = {
    "targets": ("compound", "gene"),             # curated or assay compound-gene relation; sign and intervention type it
    "has_moa": ("compound", "moa"),
    "response": ("perturbation", None),          # measured response vector in a context (value_ref)
    "is_readout": ("gene", "readout"),           # the gene is measured directly by the assay's readout
    "sequence_embedding": ("gene", None),        # computed protein-sequence representation
}
# Declared transports: (from intervention, to intervention) -> name. Nothing else may alias.
TRANSPORTS = {("genetic_knockdown", "inhibition"): "knockdown_as_inhibition_proxy",
              ("chemical_perturbation", "genetic_knockdown"): "compound_as_knockdown_proxy"}


class EvidenceRefused(ValueError):
    """A named refusal; `code` is one of the INTERFACE.md refusal codes."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


@dataclass(frozen=True)
class Entity:
    kind: str
    namespace: str
    id: str

    def key(self) -> str:
        return f"{self.kind}:{self.namespace}:{self.id}"


@dataclass(frozen=True)
class EvidenceRecord:
    subject: Entity
    predicate: str
    obj: Entity | None
    sign: int
    observation: str
    intervention: str | None
    context: str | None
    source: str
    available_from: str
    reliability: str
    depends_on: tuple[str, ...] = ()
    value_ref: str | None = None
    provenance: tuple[str, ...] = ()

    def __post_init__(self):
        if self.predicate not in PREDICATES:
            raise EvidenceRefused("PREDICATE_UNKNOWN", self.predicate)
        if self.observation not in OBSERVATIONS:
            raise EvidenceRefused("OBSERVATION_UNKNOWN", self.observation)
        if self.intervention is not None and self.intervention not in INTERVENTIONS:
            raise EvidenceRefused("INTERVENTION_UNKNOWN", self.intervention)
        if self.sign not in (-1, 0, 1):
            raise EvidenceRefused("SIGN_INVALID", str(self.sign))
        subject_kind, object_kind = PREDICATES[self.predicate]
        if subject_kind != "perturbation" and self.subject.kind != subject_kind:
            raise EvidenceRefused("SUBJECT_KIND_MISMATCH", f"{self.predicate} needs {subject_kind}")
        if object_kind is not None and (self.obj is None or self.obj.kind != object_kind):
            raise EvidenceRefused("OBJECT_KIND_MISMATCH", f"{self.predicate} needs {object_kind}")


@dataclass(frozen=True)
class Absent:
    """Missing evidence. Never a zero, never a negative."""

    reason: str

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True)
class Query:
    entity: Entity
    context: str | None
    outcome_type: str
    as_of: str = "9999-12-31"
    excluded_sources: frozenset[str] = frozenset()


@dataclass(frozen=True)
class OrbitSpec:
    route: str
    acts_on: str
    strata: tuple[str, ...]
    destroys: str


def transport(record: EvidenceRecord, to: str, sign: int) -> EvidenceRecord:
    """Re-type an interventional record as another intervention, only through a declared transport."""
    name = TRANSPORTS.get((record.intervention, to))
    if name is None:
        raise EvidenceRefused("TRANSPORT_UNDECLARED", f"{record.intervention} -> {to}")
    return replace(record, observation="transported", intervention=to, sign=sign,
                   provenance=record.provenance + (name,))


@dataclass
class EvidenceStore:
    records: list[EvidenceRecord] = field(default_factory=list)
    _by_subject: dict = field(default_factory=dict, repr=False)

    def add(self, record: EvidenceRecord) -> None:
        self.records.append(record)
        self._by_subject.setdefault((record.subject, record.predicate), []).append(record)

    def select(self, query: Query, subject: Entity, predicate: str, *, observation=None, intervention=None,
               context=None, strict: bool = False):
        """Records about `subject` admissible for `query`, or Absent.

        Records newer than `query.as_of` are dropped (or refused with `strict=True`); records from an
        excluded source are dropped (or refused). Mixed observational/interventional results refuse.
        """
        found = []
        for r in self._by_subject.get((subject, predicate), ()):
            if observation is not None and r.observation not in (observation if isinstance(observation, tuple) else (observation,)):
                continue
            if intervention is not None and r.intervention not in (intervention if isinstance(intervention, tuple) else (intervention,)):
                continue
            if context is not None and r.context not in (context, None):
                continue
            if r.available_from > query.as_of:
                if strict:
                    raise EvidenceRefused("AVAILABLE_AFTER_QUERY", r.source)
                continue
            if r.source in query.excluded_sources:
                if strict:
                    raise EvidenceRefused("EXCLUDED_SOURCE", r.source)
                continue
            found.append(r)
        if not found:
            return Absent(f"no {predicate} evidence for {subject.key()}")
        check_poolable(found)
        return found


def check_poolable(records) -> None:
    """Refuse pooling observational with interventional records, or two untransported intervention types."""
    kinds = {r.observation for r in records}
    if kinds & INTERVENTIONAL and kinds & OBSERVATIONAL:
        raise EvidenceRefused("MERGE_REFUSED", "observational with interventional")
    measured = {r.intervention for r in records if r.observation == "interventional_response"}
    if len(measured) > 1:
        raise EvidenceRefused("MERGE_REFUSED", f"intervention types {sorted(measured)} without transport")


def require_orbit(route: str, specs: dict) -> OrbitSpec:
    if route not in specs:
        raise EvidenceRefused("ORBIT_UNDECLARED", route)
    return specs[route]


def require_signed(record: EvidenceRecord, sign_rule: str | None = None) -> int:
    if record.sign == 0 and sign_rule is None:
        raise EvidenceRefused("UNSIGNED_IN_SIGNED_ROUTE", record.subject.key())
    return record.sign if record.sign != 0 else 1
