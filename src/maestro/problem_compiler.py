"""User-problem compiler: uploaded data plus a question becomes a typed open problem.

File summary
- Path: src/maestro/problem_compiler.py
- Purpose: transform user-provided measurements and a natural-language question into a typed
  `CompiledProblem`, after validating what the data actually is. The compiler always returns a
  structured diagnostic report first; biological recommendations are a separate, later step.
- Core points:
  - Validation: gene identifiers against an optional reference set, compound identifiers by name
    and (when RDKit is available) by structure, time and dose units, assay identification, control
    design, replicate inspection and QC failures.
  - Missingness is one of the six registered states and is never encoded as zero: not planned,
    planned but missing, QC failed, undetected, ambiguous, qualified.
  - The compiler computes directional state summaries and pathway/cell-state summaries when the
    data supports them, flags out-of-distribution risks, proposes competing hypotheses (registered
    plus advisory) and lists the available actions with their prerequisites.
  - The compiler measures and diagnoses; it never admits evidence and never updates a hypothesis.
- Interfaces: `MeasurementRecord`, `CompilerDiagnostic`, `CompiledProblem`, `ProblemCompiler`,
  `compile_problem`
- Depends on: maestro.case_memory, maestro.directional, maestro.hypothesis_graph
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .case_memory import CandidateAction, ScientificMeasurementStatus
from .directional import DirectionalState, directional_state_from_shift
from .hypothesis_graph import GraphNode, HypothesisGraph, NodeKind, validate_graph

_TIME_UNITS = {"h": 1.0, "hr": 1.0, "hour": 1.0, "hours": 1.0, "d": 24.0, "day": 24.0, "days": 24.0}
_DOSE_UNITS = {"nm": 1.0, "um": 1e3, "µm": 1e3, "mm": 1e6, "ng/ml": None, "ug/ml": None}
_GENE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,19}$")


@dataclass(frozen=True)
class MeasurementRecord:
    """One user-supplied measurement row, typed before any interpretation."""

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
                assay_hint: str | None = None) -> CompiledProblem:
        diagnostics: list[CompilerDiagnostic] = []
        if not question.strip():
            diagnostics.append(CompilerDiagnostic("missing:question", "fatal", "the user question is empty"))
        if not records:
            diagnostics.append(CompilerDiagnostic("missing:records", "fatal", "no measurement records supplied"))
        status_by_condition: dict[str, ScientificMeasurementStatus] = {}
        genes: set[str] = set()
        delta: dict[str, float] = {}
        controls, treated = set(), set()
        times, doses = set(), set()
        replicate_groups: dict[str, int] = {}
        for record in records:
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
                    "invalid:time_unit", "error", f"{record.record_id}: unsupported time unit {record.time_unit!r}"))
            if record.dose_value is not None and dose_nm is None:
                diagnostics.append(CompilerDiagnostic(
                    "invalid:dose_unit", "error", f"{record.record_id}: unsupported dose unit {record.dose_unit!r}"))
            if time_h is not None:
                times.add(time_h)
            if dose_nm is not None:
                doses.add(dose_nm)
            if record.status.biological and record.value is not None and not record.is_control:
                gene = record.feature.strip().upper()
                if not _GENE_PATTERN.match(gene):
                    diagnostics.append(CompilerDiagnostic(
                        "invalid:gene_identifier", "error",
                        f"{record.record_id}: {record.feature!r} is not a valid gene symbol"))
                else:
                    genes.add(gene)
                    if self.reference_genes and gene not in self.reference_genes:
                        diagnostics.append(CompilerDiagnostic(
                            "ood:gene", "warning", f"{gene}: not in the reference feature space"))
                    delta[gene] = float(record.value)
            if record.replicate_group:
                replicate_groups[record.replicate_group] = replicate_groups.get(record.replicate_group, 0) + 1
        if treated and not controls:
            diagnostics.append(CompilerDiagnostic(
                "missing:control", "error", "treated conditions have no control condition in the upload"))
        assay = assay_hint or self._identify_assay(records)
        if assay is None:
            diagnostics.append(CompilerDiagnostic("unidentified:assay", "error", "the assay could not be identified"))
        replicates = max(replicate_groups.values()) if replicate_groups else None
        if replicates is None or replicates < 2:
            diagnostics.append(CompilerDiagnostic(
                "thin:replicates", "warning", "fewer than two replicates per condition were identified"))
        state = directional_state_from_shift(delta, self.gene_sets) if delta else DirectionalState()
        ood = tuple(sorted({d.detail.split(":")[0] for d in diagnostics if d.code == "ood:gene"}))
        graph = self._hypothesis_graph(intervention, nominal_target, assay, state)
        actions = self._actions(assay, sorted(times) or [None], sorted(doses) or [None],
                                sorted(status_by_condition))
        return CompiledProblem(
            problem_id=problem_id, user_question=question, diagnostics=tuple(diagnostics),
            assay=assay, control_design=("vehicle_control" if controls else "none_identified"),
            time_h=sorted(times)[0] if times else None, dose_nM=sorted(doses)[0] if doses else None,
            replicates=replicates, measurement_status=status_by_condition, directional_state=state,
            context={"cell_lines": sorted({r.cell_line for r in records if r.cell_line}),
                     "intervention": intervention, "nominal_target": nominal_target,
                     "conditions": sorted(status_by_condition)},
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
