"""Layered hypothesis graph: intervention to observed assay, with typed edges and higher-order relations.

File summary
- Path: research/scientific_case_memory/hypothesis_graph.py
- Purpose: represent a non-trivial problem as a graph whose layers are intervention, target
  engagement, proximal function, pathway state, cellular state, phenotype and observed assay, and
  whose competing hypotheses are explicit testable claims over that graph.
- Core points:
  - Every edge carries a relation type, direction, context, time, assay, evidence sources,
    evidence strength, uncertainty and contradictory evidence. An edge with none of these is not
    an edge, it is a wish; `validate` names each missing field.
  - A `HyperEdge` states a relation that holds only for a combination (several biomarkers, several
    compounds, a dose-time pair, a prerequisite measurement), so a multi-component statement is not
    forced into independent pairwise edges.
  - Hypotheses are claims, not posteriors. A hypothesis is either registered (a member of the
    candidate set the evidence rules can eliminate from) or advisory (kept in the graph and the
    report but never eliminated by a rule). The graph never assigns a probability to a hypothesis.
  - Layer order is enforced (`LAYERS`): an edge may only run forward, so a graph that reads
    "phenotype causes engagement" is rejected instead of drawn.
  - `distinguishing_actions` lists, per pair of hypotheses, the actions whose predicted reading
    differs, and `undistinguishable_pairs` names the pairs no action in the menu can separate.
  - `template_for` builds the five standard competing hypotheses of an engagement-type problem
    (direct engagement, compensatory stress response, off-target effect, artifact, real but
    functionally irrelevant) from a problem's measurement statuses, so no hypothesis is built from
    a measurement that was never made.
- Interfaces: `LAYERS`, `Node`, `Edge`, `HyperEdge`, `Hypothesis`, `HypothesisGraph`, `template_for`
- Depends on: case_schema.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from . import case_schema as S

LAYERS = ("intervention", "target_engagement", "proximal_function", "pathway_state", "cellular_state", "phenotype",
          "observed_assay")
STRENGTHS = ("measured", "qualified", "retrieved", "predicted", "speculative")
RELATIONS = ("engages", "inhibits", "activates", "modulates", "causes", "correlates_with", "reports", "confounds")
DIRECTIONS = ("positive", "negative", "signed_unknown", "none")


@dataclass(frozen=True)
class Node:
    node_id: str
    layer: str
    label: str
    status: S.MeasurementStatus = S.MeasurementStatus.NOT_PLANNED


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation_type: str
    direction: str
    context: str
    time: str
    assay: str
    evidence_sources: tuple[str, ...]
    evidence_strength: str
    uncertainty: str
    contradictory_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class HyperEdge:
    """A relation that holds only for the joint state of several inputs."""

    inputs: tuple[str, ...]
    target: str
    relation_type: str
    condition: str
    evidence_sources: tuple[str, ...]
    evidence_strength: str
    uncertainty: str


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    claim: str
    path: tuple[str, ...]
    """Node identifiers the claim says carry the effect, in layer order."""
    assumptions: tuple[str, ...] = ()
    predicted: Mapping[str, str] = field(default_factory=dict)
    advisory: bool = False
    supporting: tuple[str, ...] = ()
    contradicting: tuple[str, ...] = ()
    next_test: str | None = None

    def as_claim(self) -> S.HypothesisClaim:
        return S.HypothesisClaim(self.hypothesis_id, self.claim, self.assumptions, dict(self.predicted), self.advisory)


class HypothesisGraph:
    def __init__(self, nodes: Sequence[Node], edges: Sequence[Edge] = (), hyperedges: Sequence[HyperEdge] = (),
                 hypotheses: Sequence[Hypothesis] = ()):
        self.nodes = {n.node_id: n for n in nodes}
        if len(self.nodes) != len(nodes):
            raise ValueError("duplicate_node_id")
        self.edges = tuple(edges)
        self.hyperedges = tuple(hyperedges)
        self.hypotheses = tuple(hypotheses)

    # ------------------------------------------------------------------ queries
    def layer_of(self, node_id: str) -> int:
        return LAYERS.index(self.nodes[node_id].layer)

    def registered(self) -> tuple[Hypothesis, ...]:
        return tuple(h for h in self.hypotheses if not h.advisory)

    def edges_from(self, node_id: str) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def unmeasured_layers(self) -> tuple[str, ...]:
        """Layers with no node whose status is a biological measurement: what the data cannot speak to."""
        measured = {n.layer for n in self.nodes.values() if n.status.biological}
        return tuple(layer for layer in LAYERS if layer not in measured)

    def distinguishing_actions(self, a: str, b: str) -> tuple[str, ...]:
        ha = next(h for h in self.hypotheses if h.hypothesis_id == a)
        hb = next(h for h in self.hypotheses if h.hypothesis_id == b)
        return tuple(sorted(k for k in set(ha.predicted) & set(hb.predicted) if ha.predicted[k] != hb.predicted[k]))

    def undistinguishable_pairs(self) -> tuple[tuple[str, str], ...]:
        ids = [h.hypothesis_id for h in self.hypotheses]
        return tuple((a, b) for i, a in enumerate(ids) for b in ids[i + 1:] if not self.distinguishing_actions(a, b))

    # ------------------------------------------------------------------ validation
    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for n in self.nodes.values():
            if n.layer not in LAYERS:
                errors.append(f"invalid:node_layer:{n.node_id}")
        for e in self.edges:
            tag = f"{e.source}->{e.target}"
            if e.source not in self.nodes or e.target not in self.nodes:
                errors.append(f"dangling_edge:{tag}")
                continue
            if self.layer_of(e.source) >= self.layer_of(e.target):
                errors.append(f"edge_not_forward:{tag}")
            if e.relation_type not in RELATIONS:
                errors.append(f"invalid:relation_type:{tag}")
            if e.direction not in DIRECTIONS:
                errors.append(f"invalid:direction:{tag}")
            if e.evidence_strength not in STRENGTHS:
                errors.append(f"invalid:evidence_strength:{tag}")
            for name in ("context", "time", "assay", "uncertainty"):
                if not str(getattr(e, name)).strip():
                    errors.append(f"missing:{name}:{tag}")
            if not e.evidence_sources:
                errors.append(f"missing:evidence_sources:{tag}")
            if e.evidence_strength in ("measured", "qualified") and self.nodes[e.target].status is S.MeasurementStatus.NOT_PLANNED:
                errors.append(f"measured_edge_to_unmeasured_node:{tag}")
        for h in self.hyperedges:
            if len(h.inputs) < 2:
                errors.append(f"hyperedge_needs_two_inputs:{h.target}")
            if any(i not in self.nodes for i in h.inputs) or h.target not in self.nodes:
                errors.append(f"dangling_hyperedge:{h.target}")
            if h.evidence_strength not in STRENGTHS:
                errors.append(f"invalid:evidence_strength:hyper:{h.target}")
        seen = set()
        for hyp in self.hypotheses:
            if hyp.hypothesis_id in seen:
                errors.append(f"duplicate_hypothesis:{hyp.hypothesis_id}")
            seen.add(hyp.hypothesis_id)
            if not hyp.claim.strip():
                errors.append(f"missing:claim:{hyp.hypothesis_id}")
            missing = [p for p in hyp.path if p not in self.nodes]
            if missing:
                errors.append(f"hypothesis_path_unknown_node:{hyp.hypothesis_id}:{missing[0]}")
            elif [self.layer_of(p) for p in hyp.path] != sorted(self.layer_of(p) for p in hyp.path):
                errors.append(f"hypothesis_path_not_layer_ordered:{hyp.hypothesis_id}")
            if any(k == hyp.hypothesis_id for k in hyp.contradicting) and hyp.hypothesis_id in hyp.supporting:
                errors.append(f"hypothesis_supports_and_contradicts_itself:{hyp.hypothesis_id}")
        if len(self.registered()) < 2 and self.hypotheses:
            errors.append("fewer_than_two_registered_hypotheses")
        return tuple(dict.fromkeys(errors))

    # ------------------------------------------------------------------ export
    def payload(self) -> dict:
        return S.to_dict({"nodes": list(self.nodes.values()), "edges": list(self.edges),
                          "hyperedges": list(self.hyperedges), "hypotheses": list(self.hypotheses),
                          "unmeasured_layers": self.unmeasured_layers(),
                          "undistinguishable_pairs": self.undistinguishable_pairs()})


# ---------------------------------------------------------------------------------------- template
def template_for(problem_id: str, intervention: str, target: str | None, context: str, assay: str,
                 statuses: Mapping[str, S.MeasurementStatus], *, action_ids: Sequence[str] = (),
                 sources: Sequence[str] = ("user_data",)) -> HypothesisGraph:
    """The five standard competing explanations of an engagement-type problem.

    `statuses` maps `engagement`, `function`, `pathway`, `cell_state`, `phenotype` and `assay` to the
    measurement status of that layer. A layer that was never measured stays `not_planned` and any
    edge into it is at most `predicted` or `speculative`; the validator refuses a stronger claim.
    """

    def status(name: str) -> S.MeasurementStatus:
        return statuses.get(name, S.MeasurementStatus.NOT_PLANNED)

    tgt = target or "unspecified_target"
    nodes = [
        Node("intervention", "intervention", intervention, S.MeasurementStatus.QUALIFIED),
        Node("engagement", "target_engagement", f"engagement of {tgt}", status("engagement")),
        Node("function", "proximal_function", f"activity of {tgt}", status("function")),
        Node("pathway", "pathway_state", "pathway state", status("pathway")),
        Node("cell_state", "cellular_state", "cellular state", status("cell_state")),
        Node("phenotype", "phenotype", "phenotype", status("phenotype")),
        Node("assay", "observed_assay", f"observed {assay}", status("assay")),
    ]

    def edge(src: str, dst: str, relation: str, strength: str) -> Edge:
        measured = status(dst).biological
        strength = strength if measured or strength in ("predicted", "speculative", "retrieved") else "predicted"
        return Edge(src, dst, relation, "signed_unknown", context, "unspecified", assay, tuple(sources), strength,
                    "not quantified" if strength in ("predicted", "speculative") else "replicate-limited")

    chain = [("intervention", "engagement", "engages", "predicted"),
             ("engagement", "function", "inhibits", "predicted"),
             ("function", "pathway", "modulates", "predicted"),
             ("pathway", "cell_state", "causes", "predicted"),
             ("cell_state", "phenotype", "causes", "predicted"),
             ("phenotype", "assay", "reports", "retrieved")]
    edges = [edge(*c) for c in chain]

    def prediction(h: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for a in action_ids:
            lowered = a.lower()
            if "engagement" in lowered or "occupancy" in lowered:
                out[a] = {"H1": "engaged", "H2": "engaged_or_unengaged", "H3": "not_engaged", "H4": "not_engaged",
                          "H5": "engaged"}[h]
            elif "control" in lowered or "orthogonal" in lowered:
                out[a] = {"H1": "control_resistant", "H2": "control_resistant", "H3": "control_sensitive",
                          "H4": "control_variable", "H5": "control_resistant"}[h]
            elif "replicate" in lowered or "qc" in lowered:
                out[a] = {"H1": "reproducible", "H2": "reproducible", "H3": "reproducible", "H4": "not_reproducible",
                          "H5": "reproducible"}[h]
            elif "phenotype" in lowered or "viability" in lowered:
                out[a] = {"H1": "phenotype_present", "H2": "phenotype_present", "H3": "phenotype_present",
                          "H4": "phenotype_variable", "H5": "phenotype_absent"}[h]
        return out

    path = ("intervention", "engagement", "function", "pathway", "cell_state", "phenotype", "assay")
    hyps = [
        Hypothesis("H1", f"The observed effect is caused by direct engagement of {tgt} by {intervention}.", path,
                   ("engagement is dose- and time-matched to the observed effect",), prediction("H1")),
        Hypothesis("H2", "The observed pathway activation is a compensatory stress response downstream of a real "
                   "but different primary effect.", ("intervention", "function", "pathway", "cell_state", "assay"),
                   ("the primary effect precedes the compensation in time",), prediction("H2"), advisory=True),
        Hypothesis("H3", f"{tgt} is not engaged and the effect is off-target.",
                   ("intervention", "function", "pathway", "cell_state", "phenotype", "assay"),
                   ("an off-target activity exists at this dose",), prediction("H3")),
        Hypothesis("H4", "The effect is a batch or assay artifact.", ("intervention", "assay"),
                   ("the control design cannot absorb the batch",), prediction("H4"), advisory=True),
        Hypothesis("H5", "The molecular response is real but functionally irrelevant to the phenotype.",
                   ("intervention", "engagement", "function", "pathway", "assay"),
                   ("the phenotype readout is sensitive and was measured in the same context",), prediction("H5"),
                   advisory=True),
    ]
    return HypothesisGraph(nodes, edges, (), hyps)
