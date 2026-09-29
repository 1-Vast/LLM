"""Typed hypothesis and evidence graph for production scientific episodes.

File summary
- Path: src/maestro/hypothesis_graph.py
- Purpose: represent, for one user problem, the typed graph from intervention to observable with
  evidence classes on every edge, including higher-order relations that must not be flattened into
  independent pairwise links.
- Core points:
  - Node kinds follow the biological chain: intervention, target, engagement, proximal function,
    pathway, cell state, phenotype, observable, assay, context, time, dose.
  - Every edge carries relation type, direction, context, time, assay, evidence class, source,
    confidence, uncertainty and contradictory evidence. The seven evidence classes of
    `case_memory.EvidenceClass` stay distinct; only `QUALIFIED_EVIDENCE` may update an
    `EvidenceState`, and the graph enforces that by refusing to mark any other class promotable.
  - `HyperEdge` expresses higher-order claims - drug combinations, multi-biomarker rules,
    context-dependent mechanisms, dose-time interactions, prerequisite chains - as one object with
    named inputs, a condition and a target, never as a set of pairwise edges.
  - The graph assigns no probabilities and grants no evidence; it is a structure with a validator.
- Interfaces: `NodeKind`, `GraphNode`, `GraphEdge`, `HyperEdge`, `HypothesisGraph`,
  `PROMOTABLE_CLASSES`, `validate_graph`
- Depends on: maestro.case_memory (evidence classes, measurement status)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .case_memory import EvidenceClass, ScientificMeasurementStatus

PROMOTABLE_CLASSES = (EvidenceClass.QUALIFIED_EVIDENCE,)
"""Only qualified experimental evidence may update an `EvidenceState` (registered boundary)."""


class NodeKind(str, Enum):
    INTERVENTION = "intervention"
    TARGET = "target"
    ENGAGEMENT = "engagement"
    PROXIMAL_FUNCTION = "proximal_function"
    PATHWAY = "pathway"
    CELL_STATE = "cell_state"
    PHENOTYPE = "phenotype"
    OBSERVABLE = "observable"
    ASSAY = "assay"
    CONTEXT = "context"
    TIME = "time"
    DOSE = "dose"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: NodeKind
    label: str
    status: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation_type: str
    direction: int = 0
    """+1 activating, -1 suppressing, 0 unknown or unsigned."""
    context: str | None = None
    time_h: float | None = None
    assay: str | None = None
    evidence_class: EvidenceClass = EvidenceClass.SPECULATION
    source_ref: str = ""
    confidence: float | None = None
    uncertainty: str = ""
    contradictory_evidence: tuple[str, ...] = ()

    @property
    def promotable(self) -> bool:
        """Whether this edge may update an evidence state. Only qualified experimental evidence."""

        return self.evidence_class in PROMOTABLE_CLASSES


@dataclass(frozen=True)
class HyperEdge:
    """A higher-order relation: named inputs jointly imply the target under `condition`.

    Examples: a drug combination (two interventions jointly), a multi-biomarker rule (two markers
    jointly), a dose-time interaction (dose and time jointly condition a pathway effect), a
    prerequisite chain (engagement is a prerequisite of a functional claim).
    """

    inputs: tuple[str, ...]
    target: str
    relation_type: str
    condition: str
    evidence_class: EvidenceClass = EvidenceClass.SPECULATION
    source_ref: str = ""
    confidence: float | None = None
    uncertainty: str = ""
    contradictory_evidence: tuple[str, ...] = ()

    @property
    def promotable(self) -> bool:
        return self.evidence_class in PROMOTABLE_CLASSES


@dataclass(frozen=True)
class HypothesisGraph:
    """The typed graph of one problem. Immutable; a new fact makes a new graph value."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...] = ()
    hyperedges: tuple[HyperEdge, ...] = ()
    hypotheses: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    """hypothesis_id -> the node path the hypothesis claims; advisory ids are named separately."""
    advisory: tuple[str, ...] = ()

    def node(self, node_id: str) -> GraphNode | None:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def unmeasured_layers(self) -> tuple[str, ...]:
        """Node kinds every node of which is in a non-biological measurement state."""

        out = []
        for kind in NodeKind:
            nodes = [n for n in self.nodes if n.kind is kind]
            if nodes and all(not n.status.biological for n in nodes):
                out.append(kind.value)
        return tuple(out)

    def edges_from(self, node_id: str) -> tuple[GraphEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def promotable_edges(self) -> tuple[GraphEdge, ...]:
        return tuple(e for e in self.edges if e.promotable)


def validate_graph(graph: HypothesisGraph) -> tuple[str, ...]:
    """Named structural errors of a hypothesis graph."""

    errors: list[str] = []
    ids = [n.node_id for n in graph.nodes]
    if len(set(ids)) != len(ids):
        errors.append("duplicate:node_id")
    known = set(ids)
    for e in graph.edges:
        if e.source not in known or e.target not in known:
            errors.append(f"edge_to_unknown_node:{e.source}->{e.target}")
        if e.direction not in (-1, 0, 1):
            errors.append(f"invalid:edge_direction:{e.source}->{e.target}")
        if not isinstance(e.evidence_class, EvidenceClass):
            errors.append(f"invalid:edge_evidence_class:{e.source}->{e.target}")
        if e.confidence is not None and not 0.0 <= e.confidence <= 1.0:
            errors.append(f"invalid:edge_confidence:{e.source}->{e.target}")
    for h in graph.hyperedges:
        if len(h.inputs) < 2:
            errors.append(f"hyperedge_too_thin:{h.target}")
        unknown = [i for i in h.inputs if i not in known]
        if unknown or h.target not in known:
            errors.append(f"hyperedge_to_unknown_node:{h.target}")
    for hid, path in graph.hypotheses.items():
        if len(path) < 2:
            errors.append(f"hypothesis_path_too_short:{hid}")
        unknown = [n for n in path if n not in known]
        if unknown:
            errors.append(f"hypothesis_path_unknown_node:{hid}")
    registered = [h for h in graph.hypotheses if h not in graph.advisory]
    if len(registered) < 2:
        errors.append("missing:two_registered_hypotheses")
    return tuple(dict.fromkeys(errors))
