"""Compile user measurements into a scoped problem and an evidence-typed hypothesis graph."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .adaptive_retrieval import DirectionalState, directional_state_from_shift
from .case_memory import CandidateAction, EvidenceClass, ScientificMeasurementStatus


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


_TIME_UNITS = {"h": 1.0, "hr": 1.0, "hour": 1.0, "hours": 1.0, "d": 24.0, "day": 24.0, "days": 24.0}
_DOSE_UNITS = {"nm": 1.0, "um": 1e3, "µm": 1e3, "mm": 1e6, "ng/ml": None, "ug/ml": None}
_GENE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,19}$")
_EFFECT_KINDS = {"signed_effect", "log_fold_change", "differential_z_score"}


@dataclass(frozen=True)
class MeasurementRecord:
    """One measurement row; legacy values are declared signed effects, not expression.

    Raw counts/normalized expression require upstream control matching and differential
    analysis. ``replicate_group`` groups related rows; only explicitly identified biological
    replicates count as independent support. Technical replicates must be aggregated upstream.
    """

    record_id: str
    feature: str
    value: float | None
    condition: str
    status: ScientificMeasurementStatus = ScientificMeasurementStatus.QUALIFIED
    cell_line: str | None = None
    time_value: float | None = None
    time_unit: str | None = None
    dose_value: float | None = None
    dose_unit: str | None = None
    replicate_group: str | None = None
    is_control: bool = False
    value_kind: str = "signed_effect"
    biological_replicate_id: str | None = None


@dataclass(frozen=True)
class CompilerDiagnostic:
    code: str
    severity: str
    detail: str


@dataclass(frozen=True)
class CompiledProblem:
    """The compiler output: diagnostics first, then the typed problem."""

    problem_id: str
    user_question: str
    diagnostics: tuple[CompilerDiagnostic, ...]
    assay: str | None
    control_design: str | None
    time_h: float | None
    dose_nM: float | None
    replicates: int | None
    measurement_status: Mapping[str, ScientificMeasurementStatus]
    directional_state: DirectionalState
    context: Mapping[str, object]
    ood_risks: tuple[str, ...]
    hypothesis_graph: HypothesisGraph | None
    candidate_actions: tuple[CandidateAction, ...]

    @property
    def usable(self) -> bool:
        return not any(d.severity == "fatal" for d in self.diagnostics)


def _normalise_time(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    factor = _TIME_UNITS.get((unit or "").strip().lower())
    return value * factor if factor else None


def _normalise_dose(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    factor = _DOSE_UNITS.get((unit or "").strip().lower())
    return value * factor if factor else None


class ProblemCompiler:
    """Validate, diagnose and compile user data into a typed open problem."""

    def __init__(self, *, reference_genes: Sequence[str] | None = None,
                 gene_sets: Mapping[str, Sequence[str]] | None = None,
                 known_cell_lines: Sequence[str] | None = None):
        self.reference_genes = set(reference_genes or ())
        self.gene_sets = dict(gene_sets or {})
        self.known_cell_lines = set(known_cell_lines or ())

    def compile(self, problem_id: str, question: str,
                records: Sequence[MeasurementRecord], *,
                intervention: str = "", nominal_target: str | None = None,
                assay_hint: str | None = None,
                condition: str | None = None) -> CompiledProblem:
        diagnostics: list[CompilerDiagnostic] = []
        if not question.strip():
            diagnostics.append(CompilerDiagnostic("missing:question", "fatal", "the user question is empty"))
        if not records:
            diagnostics.append(CompilerDiagnostic("missing:records", "fatal", "no measurement records supplied"))
        supplied_conditions = {r.condition for r in records if not r.is_control}
        if condition is not None:
            if condition not in supplied_conditions:
                diagnostics.append(CompilerDiagnostic(
                    "invalid:condition", "fatal", f"no treated records for {condition!r}"))
            records = tuple(r for r in records if r.is_control or r.condition == condition)
        elif len(supplied_conditions) > 1:
            diagnostics.append(CompilerDiagnostic(
                "ambiguous:condition", "fatal", "select one treated condition explicitly; conditions cannot be pooled"))
        status_by_condition: dict[str, ScientificMeasurementStatus] = {}
        delta: dict[str, float] = {}
        controls, treated = set(), set()
        times, doses = set(), set()
        feature_values: dict[str, dict[str | None, float]] = {}
        contexts: set[tuple] = set()
        effect_kinds: set[str] = set()
        record_ids: set[str] = set()
        for record in records:
            if record.record_id in record_ids:
                diagnostics.append(CompilerDiagnostic(
                    "duplicate:record_id", "fatal", f"duplicate record ID {record.record_id!r}"))
            record_ids.add(record.record_id)
            if not isinstance(record.status, ScientificMeasurementStatus):
                diagnostics.append(CompilerDiagnostic(
                    "invalid:status", "fatal", f"{record.record_id}: status {record.status!r} is not registered"))
                continue
            status_by_condition.setdefault(record.condition, record.status)
            if record.status is ScientificMeasurementStatus.QC_FAILED:
                diagnostics.append(CompilerDiagnostic(
                    "qc:failed", "warning", f"{record.condition}: measurement failed its quality rule"))
            if not record.status.biological and record.value is not None:
                diagnostics.append(CompilerDiagnostic(
                    "missing_as_zero", "fatal",
                    f"{record.record_id}: a {record.status.value} measurement carries a value; "
                    "missingness must stay a status, never a zero"))
            (controls if record.is_control else treated).add(record.condition)
            time_h = _normalise_time(record.time_value, record.time_unit)
            dose_nm = _normalise_dose(record.dose_value, record.dose_unit)
            if record.time_value is not None and time_h is None:
                diagnostics.append(CompilerDiagnostic(
                    "invalid:time_unit", "fatal", f"{record.record_id}: unsupported time unit {record.time_unit!r}"))
            if record.dose_value is not None and dose_nm is None:
                diagnostics.append(CompilerDiagnostic(
                    "invalid:dose_unit", "fatal", f"{record.record_id}: unsupported dose unit {record.dose_unit!r}"))
            if any(v is not None and (not math.isfinite(v) or v < 0) for v in (time_h, dose_nm)):
                diagnostics.append(CompilerDiagnostic(
                    "invalid:condition_value", "fatal", f"{record.record_id}: time and dose must be finite and nonnegative"))
                continue
            if not record.is_control:
                contexts.add((record.condition, record.cell_line, time_h, dose_nm))
            if time_h is not None and not record.is_control:
                times.add(time_h)
            if dose_nm is not None and not record.is_control:
                doses.add(dose_nm)
            if record.status.biological and record.value is not None and not record.is_control:
                if record.value_kind not in _EFFECT_KINDS:
                    diagnostics.append(CompilerDiagnostic(
                        "unsupported:value_kind", "fatal",
                        f"{record.record_id}: {record.value_kind!r} is not a signed contrast; "
                        "perform matched-control differential analysis upstream"))
                    continue
                effect_kinds.add(record.value_kind)
                if not isinstance(record.value, (int, float)) or not math.isfinite(record.value):
                    diagnostics.append(CompilerDiagnostic(
                        "invalid:measurement_value", "fatal", f"{record.record_id}: effect must be finite numeric data"))
                    continue
                gene = record.feature.strip().upper()
                if not _GENE_PATTERN.match(gene):
                    diagnostics.append(CompilerDiagnostic(
                        "invalid:gene_identifier", "error",
                        f"{record.record_id}: {record.feature!r} is not a valid gene symbol"))
                else:
                    if self.reference_genes and gene not in self.reference_genes:
                        diagnostics.append(CompilerDiagnostic(
                            "ood:gene", "warning", f"{gene}: not in the reference feature space"))
                    values = feature_values.setdefault(gene, {})
                    replicate = record.biological_replicate_id
                    if replicate in values or (values and (replicate is None or None in values)):
                        diagnostics.append(CompilerDiagnostic(
                            "ambiguous:feature_replicate", "fatal",
                            f"{gene}: repeated feature requires distinct biological replicate IDs"))
                    else:
                        values[replicate] = float(record.value)
        if len(contexts) > 1:
            diagnostics.append(CompilerDiagnostic(
                "ambiguous:experimental_context", "fatal",
                "one condition must have a single cell context, time and dose; split the upload"))
        if len(effect_kinds) > 1:
            diagnostics.append(CompilerDiagnostic(
                "mixed:effect_scales", "fatal", "effect scales cannot be pooled into one state"))
        for gene, values in feature_values.items():
            delta[gene] = math.fsum(values.values()) / len(values)
        if treated and not controls:
            diagnostics.append(CompilerDiagnostic(
                "missing:control", "error", "treated conditions have no control condition in the upload"))
        assay = assay_hint or self._identify_assay(records)
        if assay is None:
            diagnostics.append(CompilerDiagnostic("unidentified:assay", "error", "the assay could not be identified"))
        replicate_counts = {gene: sum(key is not None for key in values)
                            for gene, values in feature_values.items()}
        replicates = min(replicate_counts.values()) if replicate_counts and all(replicate_counts.values()) else None
        if replicates is None or replicates < 2:
            diagnostics.append(CompilerDiagnostic(
                "thin:replicates", "warning", "fewer than two replicates per condition were identified"))
        invalid = any(d.severity == "fatal" for d in diagnostics)
        state = directional_state_from_shift(delta, self.gene_sets) if delta and not invalid else DirectionalState()
        ood = tuple(sorted({d.detail.split(":")[0] for d in diagnostics if d.code == "ood:gene"}))
        graph = self._hypothesis_graph(intervention, nominal_target, assay, state)
        actions = self._actions(assay, sorted(times) or [None], sorted(doses) or [None],
                                sorted(status_by_condition)) if not invalid else ()
        return CompiledProblem(
            problem_id=problem_id, user_question=question, diagnostics=tuple(diagnostics),
            assay=assay, control_design=("vehicle_control" if controls else "none_identified"),
            time_h=next(iter(times)) if len(times) == 1 else None,
            dose_nM=next(iter(doses)) if len(doses) == 1 else None,
            replicates=replicates, measurement_status=status_by_condition, directional_state=state,
            context={"cell_lines": sorted({r.cell_line for r in records if r.cell_line and not r.is_control}),
                     "intervention": intervention, "nominal_target": nominal_target,
                     "conditions": sorted(status_by_condition),
                     "effect_kind": next(iter(effect_kinds)) if len(effect_kinds) == 1 else None,
                     "replicates_per_feature": replicate_counts,
                     "replicate_aggregation": "unweighted_biological_mean"},
            ood_risks=ood, hypothesis_graph=graph, candidate_actions=actions)

    def _identify_assay(self, records: Sequence[MeasurementRecord]) -> str | None:
        genes = {r.feature for r in records if not r.is_control and r.status.biological}
        if len(genes) >= 50:
            return "transcriptomic_profile"
        if genes:
            return "targeted_molecular_readout"
        return None

    def _hypothesis_graph(self, intervention: str, target: str | None,
                          assay: str | None, state: DirectionalState) -> HypothesisGraph | None:
        if not intervention:
            return None
        target = target or "unspecified_target"
        nodes = [
            GraphNode("intervention", NodeKind.INTERVENTION, intervention,
                      ScientificMeasurementStatus.QUALIFIED),
            GraphNode("target", NodeKind.TARGET, target),
            GraphNode("pathway", NodeKind.PATHWAY, "pathway_state",
                      ScientificMeasurementStatus.AMBIGUOUS if state.pathway_direction
                      else ScientificMeasurementStatus.NOT_PLANNED),
            GraphNode("observable", NodeKind.OBSERVABLE, assay or "unidentified_assay",
                      ScientificMeasurementStatus.QUALIFIED if assay
                      else ScientificMeasurementStatus.NOT_PLANNED),
        ]
        hypotheses = {
            "H_on_target": ("intervention", "target", "pathway", "observable"),
            "H_off_target": ("intervention", "pathway", "observable"),
        }
        graph = HypothesisGraph(tuple(nodes), (), (), hypotheses, advisory=("H_artifact",))
        return graph if not validate_graph(graph) else graph  # advisory graphs are still returned

    def _actions(self, assay: str | None, times: Sequence, doses: Sequence,
                 conditions: Sequence[str]) -> tuple[CandidateAction, ...]:
        if assay is None:
            return ()
        actions = []
        for time_h in times:
            for dose in doses:
                aid = f"measure:{assay}:t{time_h if time_h is not None else 'planned'}:d{dose if dose is not None else 'planned'}"
                actions.append(CandidateAction(
                    aid, f"repeat {assay} at time {time_h} dose {dose}", assay, 8.0, 2.0,
                    "signed_state_change", time_h=time_h, dose_nM=dose,
                    controls=("vehicle",), detection_power=None,
                    available=bool(conditions)))
        actions.append(CandidateAction(
            "orthogonal:phenotype", "orthogonal phenotypic assay", "phenotypic", 24.0, 4.0,
            "phenotype", prerequisites=tuple(a.action_id for a in actions[:1]), available=True))
        return tuple(actions)


def compile_problem(problem_id: str, question: str, records: Sequence[MeasurementRecord], **kwargs) -> CompiledProblem:
    """Convenience wrapper around `ProblemCompiler` with no reference resources."""

    return ProblemCompiler().compile(problem_id, question, records, **kwargs)


# ---------------------------------------------------------------------------------------- compounds
def canonicalize_smiles(smiles: str) -> str | None:
    """The canonical isomeric SMILES of a structure, or None when it cannot be parsed.

    RDKit is imported lazily so the compiler stays importable without it; a structure that does
    not parse is reported, never guessed. Salt and hydrate suffixes stay in the structure - the
    connectivity block, not the parent, is what identifies a chemical unit.
    """

    try:
        from rdkit import Chem, RDLogger

        RDLogger.DisableLog("rdApp.*")
    except ImportError:  # pragma: no cover - environment dependent
        return None
    mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles.strip() else None
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, isomericSmiles=True)


def connectivity_block(inchi_key: str) -> str | None:
    """The InChIKey connectivity block (first 14 characters): the chemical-unit identity."""

    if not isinstance(inchi_key, str) or len(inchi_key) < 14:
        return None
    return inchi_key[:14]


def unseen_unit_split(blocks: Sequence[str], reference_blocks: Sequence[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split `blocks` into (unseen, seen) against the reference study's block list.

    The independent unit is the connectivity block; a unit absent from the reference study is
    unseen. Used by the external evaluation's study-level split and tested here so the split
    rule cannot silently change.
    """

    reference = set(reference_blocks)
    unseen = tuple(sorted(b for b in set(blocks) if b not in reference))
    seen = tuple(sorted(b for b in set(blocks) if b in reference))
    return unseen, seen
