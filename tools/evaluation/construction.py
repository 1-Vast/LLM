"""Evaluation construction: consolidated module responsibilities."""
from __future__ import annotations

from tools.evaluation.engagement_sources import _number

import csv
import hashlib
import json
import sys
import argparse
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

# PRISM ran several screens over overlapping compound sets. MTS010 is the technical
# redo the release readme recommends when present; HTS002 is retained as a separate
# source record and never merged into MTS010 as a biological replicate.
SCREEN_PREFERENCE: tuple[str, ...] = ("MTS010", "MTS006", "MTS005", "HTS002")

DEPENDENCY_THRESHOLD = -0.5
"""Gene-effect value used only to describe how widely a gene scores as a dependency."""


@dataclass(frozen=True)
class SourceRelease:
    """One local release file with its recorded provenance, used verbatim in case records."""

    release: str
    file_name: str
    path: Path
    declared_md5: str
    doi: str

    @property
    def citation(self) -> str:
        return f"{self.release}:{self.file_name} (DOI {self.doi}, MD5 {self.declared_md5})"

    @classmethod
    def from_provenance(cls, path: Path) -> "SourceRelease":
        """Read the sidecar provenance file written when the release was downloaded."""

        sidecar = path.with_suffix(path.suffix + ".provenance.json")
        if not sidecar.is_file():
            raise FileNotFoundError(f"Release '{path.name}' has no recorded provenance sidecar.")
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        if not data.get("md5_match", False):
            raise ValueError(f"Release '{path.name}' has an unverified checksum; refusing to build cases from it.")
        declared = str(data["declared_md5"]).strip().lower()
        actual = _file_md5(path)
        if actual != declared:
            # The sidecar flag records what was true when the file was fetched.
            # A file edited afterwards keeps that flag, so the digest of the
            # bytes on disk is recomputed at every registration.
            raise ValueError(
                f"Release '{path.name}' does not match its recorded digest: "
                f"declared {declared}, actual {actual}."
            )
        return cls(
            release=str(data["release"]),
            file_name=str(data["file_name"]),
            path=path,
            declared_md5=str(data["declared_md5"]),
            doi=str(data.get("figshare_doi", "unknown")),
        )


def _file_md5(path: Path, *, chunk_size: int = 1 << 20) -> str:
    """Digest the bytes actually on disk, streamed so a wide release fits in memory."""

    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class DependencyRecord:
    """One processed CRISPR gene-effect value for one model and gene."""

    model_id: str
    gene: str
    gene_effect: float


@dataclass(frozen=True)
class ExpressionRecord:
    """One processed RNA abundance value (log2(TPM+1)) for one model and gene."""

    model_id: str
    gene: str
    log2_tpm1: float


@dataclass(frozen=True)
class ExposureRecord:
    """One fitted PRISM dose-response curve for one compound, model, and screen."""

    model_id: str
    ccle_name: str
    gene: str
    compound: str
    broad_id: str
    screen_id: str
    auc: float
    ic50: float | None
    ec50: float | None
    curve_r2: float
    moa: str
    phase: str

    @property
    def source_id(self) -> str:
        return (
            "PRISM-19Q4:secondary-screen-dose-response-curve-parameters.csv:"
            f"{self.model_id}:{self.broad_id}:{self.screen_id}"
        )


@dataclass(frozen=True)
class ModelRecord:
    """Identity fields for one DepMap model, used for context naming only."""

    model_id: str
    cell_line_name: str
    lineage: str
    primary_disease: str


@dataclass(frozen=True)
class EvidenceBase:
    """Joined, provenance-carrying real records plus explicitly derived summaries."""

    dependencies: Mapping[tuple[str, str], DependencyRecord]
    expression: Mapping[tuple[str, str], ExpressionRecord]
    exposures: tuple[ExposureRecord, ...]
    models: Mapping[str, ModelRecord]
    dependent_fraction: Mapping[str, float]
    releases: tuple[SourceRelease, ...]
    panel: tuple[str, ...] = ()
    exposure_index: Mapping[tuple[str, str], tuple[ExposureRecord, ...]] = field(default_factory=dict)
    compound_index: Mapping[tuple[str, str], tuple[ExposureRecord, ...]] = field(default_factory=dict)

    def gene_effect(self, model_id: str, gene: str) -> float | None:
        record = self.dependencies.get((model_id, gene))
        return record.gene_effect if record else None

    def abundance(self, model_id: str, gene: str) -> float | None:
        record = self.expression.get((model_id, gene))
        return record.log2_tpm1 if record else None

    def exposures_for(self, model_id: str, gene: str) -> tuple[ExposureRecord, ...]:
        return self.exposure_index.get((model_id, gene), ())

    def exposures_of_compound(self, gene: str, compound: str) -> tuple[ExposureRecord, ...]:
        """Every model in which one registered compound was screened against one gene."""

        return self.compound_index.get((gene, compound), ())

    def context_identifier(self, model_id: str) -> str:
        model = self.models.get(model_id)
        return f"{model_id}:{model.cell_line_name}" if model else model_id

    def release_manifest(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {
                "release": item.release,
                "file_name": item.file_name,
                "declared_md5": item.declared_md5,
                "doi": item.doi,
            }
            for item in self.releases
        )


def _wide_release_rows(path: Path, panel: Sequence[str]) -> tuple[dict[str, dict[str, float]], tuple[str, ...]]:
    """Stream a wide `model x gene` release file and keep only the panel columns."""

    wanted = set(panel)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        columns: dict[str, int] = {}
        for position, column in enumerate(header):
            symbol = column.split(" (")[0].strip()
            if symbol in wanted and symbol not in columns:
                columns[symbol] = position
        values: dict[str, dict[str, float]] = {}
        for row in reader:
            if not row or not row[0]:
                continue
            model_values: dict[str, float] = {}
            for symbol, position in columns.items():
                raw = row[position] if position < len(row) else ""
                if raw not in ("", "NA", "NaN"):
                    try:
                        model_values[symbol] = float(raw)
                    except ValueError:
                        continue
            if model_values:
                values[row[0]] = model_values
    return values, tuple(sorted(columns))


def _models(path: Path) -> Mapping[str, ModelRecord]:
    records: dict[str, ModelRecord] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            model_id = (row.get("ModelID") or "").strip()
            if not model_id:
                continue
            records[model_id] = ModelRecord(
                model_id=model_id,
                cell_line_name=(row.get("StrippedCellLineName") or row.get("CellLineName") or model_id).strip(),
                lineage=(row.get("OncotreeLineage") or "unknown").strip(),
                primary_disease=(row.get("OncotreePrimaryDisease") or "unknown").strip(),
            )
    return records


def _exposures(path: Path, panel: Sequence[str] | None) -> tuple[ExposureRecord, ...]:
    """Read PRISM fitted curves, keeping only single-annotated-target compounds.

    ``panel`` of ``None`` keeps every single-target compound, so the gene panel
    can be derived from the compound annotations themselves rather than from a
    hand-written list. A compound with several annotated targets is excluded:
    its phenotype cannot be attributed to one gene without further evidence.
    """

    wanted = set(panel) if panel is not None else None
    records: list[ExposureRecord] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            target = (row.get("target") or "").strip()
            if not target or "," in target or (wanted is not None and target not in wanted):
                continue
            model_id = (row.get("depmap_id") or "").strip()
            compound = (row.get("name") or "").strip()
            if not model_id or not compound:
                continue
            auc = _number(row.get("auc"))
            curve_r2 = _number(row.get("r2"))
            if auc is None or curve_r2 is None:
                continue
            records.append(
                ExposureRecord(
                    model_id=model_id,
                    ccle_name=(row.get("ccle_name") or "").strip(),
                    gene=target,
                    compound=compound,
                    broad_id=(row.get("broad_id") or "").strip(),
                    screen_id=(row.get("screen_id") or "").strip(),
                    auc=auc,
                    ic50=_number(row.get("ic50")),
                    ec50=_number(row.get("ec50")),
                    curve_r2=curve_r2,
                    moa=(row.get("moa") or "unknown").strip(),
                    phase=(row.get("phase") or "unknown").strip(),
                )
            )
    return tuple(records)


def _preferred_exposures(records: Iterable[ExposureRecord]) -> tuple[ExposureRecord, ...]:
    """Keep one screen per compound/model, following the release's own screen preference."""

    order = {screen: rank for rank, screen in enumerate(SCREEN_PREFERENCE)}
    best: dict[tuple[str, str, str], ExposureRecord] = {}
    for record in records:
        key = (record.model_id, record.gene, record.compound)
        current = best.get(key)
        if current is None or order.get(record.screen_id, 99) < order.get(current.screen_id, 99):
            best[key] = record
    return tuple(sorted(best.values(), key=lambda item: (item.model_id, item.gene, item.compound)))


def build_evidence_base(
    workspace: Path,
    *,
    panel: Sequence[str] | None = None,
) -> EvidenceBase:
    """Extract the real evidence base from the local release files.

    With ``panel=None`` the gene panel is derived from PRISM's own
    single-target compound annotations and then intersected with the genes the
    CRISPR release actually scores. A gene therefore enters the panel because a
    registered compound declares it as its only annotated target, not because
    it produced a result of interest.
    """

    depmap = workspace / "data" / "raw" / "depmap"
    prism = workspace / "data" / "raw" / "prism"
    crispr_release = SourceRelease.from_provenance(depmap / "CRISPRGeneEffect.csv")
    expression_release = SourceRelease.from_provenance(depmap / "OmicsExpressionProteinCodingGenesTPMLogp1.csv")
    model_release = SourceRelease.from_provenance(depmap / "Model.csv")
    prism_release = SourceRelease.from_provenance(prism / "secondary-screen-dose-response-curve-parameters.csv")

    annotated = _preferred_exposures(_exposures(prism_release.path, panel))
    candidate_genes = sorted({record.gene for record in annotated})

    effects, effect_genes = _wide_release_rows(crispr_release.path, candidate_genes)
    abundances, _ = _wide_release_rows(expression_release.path, candidate_genes)
    scored = set(effect_genes)
    exposures = tuple(record for record in annotated if record.gene in scored)
    dependencies = {
        (model_id, gene): DependencyRecord(model_id, gene, value)
        for model_id, values in effects.items()
        for gene, value in values.items()
    }
    expression = {
        (model_id, gene): ExpressionRecord(model_id, gene, value)
        for model_id, values in abundances.items()
        for gene, value in values.items()
    }

    dependent_fraction: dict[str, float] = {}
    for gene in effect_genes:
        scored = [values[gene] for values in effects.values() if gene in values]
        if scored:
            dependent_fraction[gene] = sum(value <= DEPENDENCY_THRESHOLD for value in scored) / len(scored)

    index: dict[tuple[str, str], list[ExposureRecord]] = {}
    compounds: dict[tuple[str, str], list[ExposureRecord]] = {}
    for record in exposures:
        index.setdefault((record.model_id, record.gene), []).append(record)
        compounds.setdefault((record.gene, record.compound), []).append(record)

    return EvidenceBase(
        dependencies=dependencies,
        expression=expression,
        exposures=exposures,
        models=_models(model_release.path),
        dependent_fraction=dependent_fraction,
        releases=(crispr_release, expression_release, model_release, prism_release),
        panel=tuple(effect_genes),
        exposure_index={key: tuple(value) for key, value in index.items()},
        compound_index={key: tuple(value) for key, value in compounds.items()},
    )




# Every threshold below is a declared case-construction setting, frozen before any
# policy runs. None of them is a validated biological cut-off: they select which
# joint evidence pattern a case represents, and the case then states its own limits.
ARCHETYPE_THRESHOLDS: Mapping[str, float] = {
    "strong_dependency": -0.7,
    "absent_dependency": -0.2,
    "selective_gene_fraction": 0.30,
    "pan_essential_gene_fraction": 0.90,
    "active_auc": 0.60,
    "comparator_active_auc": 0.75,
    "inactive_auc": 0.85,
    "expressed_log2_tpm1": 2.0,
    "unexpressed_log2_tpm1": 1.0,
    "minimum_curve_r2": 0.50,
    "confident_curve_r2": 0.70,
}

ACTION_COST = 1.0
CASE_BUDGET = 2.0
ENGAGEMENT_COST = 3.0


class CaseArchetype(str, Enum):
    """The joint evidence pattern a case represents, recorded outside the public file."""

    CONCORDANT_PROGRAM_SUPPORT = "concordant_program_support"
    UNATTRIBUTED_PHARMACOLOGY = "unattributed_pharmacology"
    IMPLEMENTATION_GAP = "implementation_gap"
    MODE_NON_EQUIVALENCE = "mode_non_equivalence"
    PAN_ESSENTIAL_ATTRIBUTION = "pan_essential_attribution"
    NO_DISCRIMINATING_EVIDENCE = "no_discriminating_evidence"


# Two competing explanations per case. The pair depends on what the public premise
# already shows, so it is public; which one the evidence supports is not.
TARGET_MEDIATED = "target_mediated_pharmacology"
ATTRIBUTION_ERROR = "phenotype_not_target_attributable"
IMPLEMENTATION_GAP = "insufficient_functional_perturbation"
MODE_NON_EQUIVALENCE = "genetic_pharmacological_mode_non_equivalence"

_PAIRS: Mapping[CaseArchetype, tuple[str, str]] = {
    CaseArchetype.CONCORDANT_PROGRAM_SUPPORT: (TARGET_MEDIATED, ATTRIBUTION_ERROR),
    CaseArchetype.UNATTRIBUTED_PHARMACOLOGY: (TARGET_MEDIATED, ATTRIBUTION_ERROR),
    CaseArchetype.IMPLEMENTATION_GAP: (IMPLEMENTATION_GAP, MODE_NON_EQUIVALENCE),
    CaseArchetype.MODE_NON_EQUIVALENCE: (IMPLEMENTATION_GAP, MODE_NON_EQUIVALENCE),
    CaseArchetype.PAN_ESSENTIAL_ATTRIBUTION: (ATTRIBUTION_ERROR, MODE_NON_EQUIVALENCE),
    CaseArchetype.NO_DISCRIMINATING_EVIDENCE: (IMPLEMENTATION_GAP, MODE_NON_EQUIVALENCE),
}

_DEVELOPMENT_ACTIONS: Mapping[str, str] = {
    TARGET_MEDIATED: "continue",
    ATTRIBUTION_ERROR: "revise_attribution",
    IMPLEMENTATION_GAP: "revise_intervention",
    MODE_NON_EQUIVALENCE: "change_intervention_mode",
}

_CAUSAL_FACTORS: Mapping[str, str] = {
    TARGET_MEDIATED: "target_mediated",
    ATTRIBUTION_ERROR: "attribution_error",
    IMPLEMENTATION_GAP: "incomplete_perturbation",
    MODE_NON_EQUIVALENCE: "mode_non_equivalence",
}


@dataclass(frozen=True)
class ClassifiedCase:
    """One classified real evidence pattern with the records that produced it."""

    archetype: CaseArchetype
    model_id: str
    gene: str
    index: ExposureRecord
    comparator: ExposureRecord | None
    control: ExposureRecord | None
    control_model_id: str | None
    gene_effect: float
    abundance: float
    dependent_fraction: float
    control_gene_effect: float | None

    @property
    def identifier(self) -> str:
        return f"mc-{_slug(self.gene)}-{_slug(self.index.compound)}-{self.model_id.replace('ACH-', 'ach')}"


def _slug(value: str) -> str:
    keep = [character if character.isalnum() else "-" for character in value.lower()]
    return "".join(keep).strip("-").replace("--", "-")[:28]


def select_comparator(candidates: Sequence[ExposureRecord]) -> ExposureRecord | None:
    """Choose the offered comparator without reading the response it will return.

    The previous rule took the lowest observed AUC, so the environment ranked
    the comparator by the very measurement the agent is supposed to buy, and
    the archetype then followed from that hidden value. Selection now uses
    release metadata only -- compound identity, then screen and batch
    identifiers -- which is fixed before any response is inspected.

    Curve fit quality is deliberately *not* a filter here. A poorly fitted
    comparator curve is a real, recoverable measurement failure and belongs in
    the revealed record, not in the menu construction.
    """

    if not candidates:
        return None
    return min(candidates, key=lambda record: (record.compound, record.screen_id, record.broad_id))


def classify(base: EvidenceBase, model_id: str, gene: str, index: ExposureRecord) -> ClassifiedCase | None:
    """Assign one real (model, gene, compound) triple to an archetype, or reject it.

    Classification reads only measured values and their release-declared fit
    quality. A triple that matches no declared pattern is rejected rather than
    forced into the nearest one.
    """

    thresholds = ARCHETYPE_THRESHOLDS
    if index.curve_r2 < thresholds["minimum_curve_r2"]:
        return None
    gene_effect = base.gene_effect(model_id, gene)
    abundance = base.abundance(model_id, gene)
    fraction = base.dependent_fraction.get(gene)
    if gene_effect is None or abundance is None or fraction is None:
        return None

    selective = fraction <= thresholds["selective_gene_fraction"]
    pan_essential = fraction >= thresholds["pan_essential_gene_fraction"]
    others = [
        record
        for record in base.exposures_for(model_id, gene)
        if record.compound != index.compound
    ]
    comparator = select_comparator(others)
    control_model_id, control, control_effect = _context_control(base, gene, index)

    archetype: CaseArchetype | None = None
    if (
        selective
        and gene_effect <= thresholds["strong_dependency"]
        and index.auc <= thresholds["active_auc"]
        and index.curve_r2 >= thresholds["confident_curve_r2"]
        and abundance >= thresholds["expressed_log2_tpm1"]
        and control is not None
        and control.auc > thresholds["comparator_active_auc"]
    ):
        archetype = CaseArchetype.CONCORDANT_PROGRAM_SUPPORT
    elif (
        gene_effect > thresholds["absent_dependency"]
        and index.auc <= thresholds["comparator_active_auc"]
        and abundance < thresholds["unexpressed_log2_tpm1"]
        and control is not None
        and control.auc <= thresholds["comparator_active_auc"]
    ):
        archetype = CaseArchetype.UNATTRIBUTED_PHARMACOLOGY
    elif selective and gene_effect <= thresholds["strong_dependency"] and index.auc >= thresholds["inactive_auc"]:
        # A comparator whose curve does not fit is offered on the menu but
        # cannot classify the case: an uninterpretable measurement is exactly
        # the situation in which no registered evidence discriminates, and the
        # agent has to discover that by acquiring it.
        interpretable = comparator is not None and comparator.curve_r2 >= thresholds["minimum_curve_r2"]
        if comparator is None or not interpretable:
            archetype = CaseArchetype.NO_DISCRIMINATING_EVIDENCE
        elif abundance < thresholds["expressed_log2_tpm1"]:
            archetype = None
        elif comparator.auc <= thresholds["comparator_active_auc"]:
            archetype = CaseArchetype.IMPLEMENTATION_GAP
        elif comparator.auc >= thresholds["inactive_auc"]:
            archetype = CaseArchetype.MODE_NON_EQUIVALENCE
    elif (
        pan_essential
        and gene_effect <= thresholds["strong_dependency"]
        and index.auc >= thresholds["inactive_auc"]
        and abundance >= thresholds["expressed_log2_tpm1"]
    ):
        archetype = CaseArchetype.PAN_ESSENTIAL_ATTRIBUTION

    if archetype is None:
        return None
    if archetype in (CaseArchetype.CONCORDANT_PROGRAM_SUPPORT, CaseArchetype.UNATTRIBUTED_PHARMACOLOGY):
        comparator = None
    else:
        control, control_model_id, control_effect = None, None, None
    return ClassifiedCase(
        archetype=archetype,
        model_id=model_id,
        gene=gene,
        index=index,
        comparator=comparator,
        control=control,
        control_model_id=control_model_id,
        gene_effect=gene_effect,
        abundance=abundance,
        dependent_fraction=fraction,
        control_gene_effect=control_effect,
    )


def _context_control(
    base: EvidenceBase, gene: str, index: ExposureRecord
) -> tuple[str | None, ExposureRecord | None, float | None]:
    """Find the same compound screened in a model that does not depend on the gene.

    The control is a real screened record, chosen deterministically as the
    non-dependent model with the lowest gene effect magnitude. It is an
    orthogonal context, not an isogenic control: the two models differ in every
    other respect as well, which the case records as a limitation.
    """

    best: tuple[str, ExposureRecord, float] | None = None
    for match in base.exposures_of_compound(gene, index.compound):
        if match.model_id == index.model_id or match.curve_r2 < ARCHETYPE_THRESHOLDS["minimum_curve_r2"]:
            continue
        effect = base.gene_effect(match.model_id, gene)
        if effect is None or effect <= ARCHETYPE_THRESHOLDS["absent_dependency"]:
            continue
        if best is None or (abs(effect), match.model_id) < (abs(best[2]), best[0]):
            best = (match.model_id, match, effect)
    return best if best is not None else (None, None, None)


def enumerate_candidates(base: EvidenceBase) -> tuple[ClassifiedCase, ...]:
    """Classify every registered (model, gene, compound) triple in the evidence base."""

    found: list[ClassifiedCase] = []
    for (model_id, gene), records in sorted(base.exposure_index.items()):
        for index in sorted(records, key=lambda record: record.compound):
            candidate = classify(base, model_id, gene, index)
            if candidate is not None:
                found.append(candidate)
    return tuple(found)


def select_cases(
    candidates: Sequence[ClassifiedCase],
    *,
    per_archetype: int = 12,
    per_gene: int = 3,
) -> tuple[ClassifiedCase, ...]:
    """Take a deterministic, gene-capped sample so no single target dominates an archetype."""

    selected: list[ClassifiedCase] = []
    for archetype in CaseArchetype:
        pool = sorted(
            (item for item in candidates if item.archetype is archetype),
            key=lambda item: (item.gene, item.index.compound, item.model_id),
        )
        by_gene: dict[str, list[ClassifiedCase]] = {}
        for item in pool:
            by_gene.setdefault(item.gene, []).append(item)
        taken: list[ClassifiedCase] = []
        # Round-robin over genes so a gene with many instances cannot fill the archetype.
        for round_index in range(per_gene):
            for gene in sorted(by_gene):
                if len(taken) >= per_archetype:
                    break
                items = by_gene[gene]
                if round_index < len(items):
                    taken.append(items[round_index])
            if len(taken) >= per_archetype:
                break
        selected.extend(taken)
    return tuple(selected)


def assign_split(gene: str, gene_order: Sequence[str]) -> str:
    """Assign one independent biological group to exactly one partition.

    The group is the target gene, and the assignment is made once over the
    *global* gene order. The previous version indexed a gene inside its own
    archetype's gene list, so a gene appearing in two archetypes could take
    both labels; BRAF and EGFR did exactly that in the frozen package.
    Balancing now happens after allocation and cannot move a group.
    """

    order = sorted(set(gene_order))
    if gene not in order:
        raise ValueError(f"Gene '{gene}' is not in the declared grouping axis.")
    return "development" if order.index(gene) % 2 == 0 else "test"


def _hypotheses(candidate: ClassifiedCase) -> tuple[dict[str, str], ...]:
    first, second = _PAIRS[candidate.archetype]
    return tuple(
        {
            "identifier": identifier,
            "description": _description(identifier, candidate),
            "development_action": _DEVELOPMENT_ACTIONS[identifier],
            "causal_factor": _CAUSAL_FACTORS[identifier],
        }
        for identifier in (first, second)
    )


def _description(identifier: str, candidate: ClassifiedCase) -> str:
    gene, compound = candidate.gene, candidate.index.compound
    line = candidate.index.ccle_name or candidate.model_id
    if identifier == TARGET_MEDIATED:
        return (
            f"The viability phenotype of {compound} in {line} is mediated by its annotated "
            f"target {gene} in this context."
        )
    if identifier == ATTRIBUTION_ERROR:
        return (
            f"The observed phenotype in {line} is not attributable to {gene} in this context, "
            "so the target-program interpretation of the existing records is unsupported."
        )
    if identifier == IMPLEMENTATION_GAP:
        return (
            f"{compound} does not achieve sufficient functional perturbation of {gene} in {line} "
            "at the screened exposure, so the absent phenotype reflects the intervention, not the target."
        )
    return (
        f"Genetic removal of {gene} and pharmacological inhibition by {compound} are not "
        f"functionally equivalent in {line}, so the absent phenotype reflects the intervention mode."
    )


def _initial_evidence(candidate: ClassifiedCase, base: EvidenceBase) -> list[dict[str, Any]]:
    """Public premise: the genetic score and the index compound's own fitted curve."""

    context = base.context_identifier(candidate.model_id)
    index = candidate.index
    conditions = {
        "model_id": candidate.model_id,
        "context_identifier": context,
        "gene": candidate.gene,
    }
    return [
        {
            "identifier": "crispr-gene-effect",
            "statement": (
                f"DepMap 24Q2 reports a CRISPR gene-effect score of {candidate.gene_effect:.4f} for "
                f"{candidate.gene} in {candidate.model_id} ({index.ccle_name})."
            ),
            "source_id": f"DepMap-24Q2:CRISPRGeneEffect.csv:{candidate.model_id}:{candidate.gene}",
            "conditions": dict(conditions, assay="processed CRISPR gene-effect score"),
            "evidence_kind": "retrieved_source",
            "limitations": [
                "A processed cross-study dependency score is not a condition-matched target-engagement measurement.",
                "The CRISPR perturbation removes the protein over days; it is not dose-matched or time-matched to a compound exposure.",
            ],
        },
        {
            "identifier": "prism-index-curve",
            "statement": (
                f"PRISM Repurposing 19Q4 {index.screen_id} reports {index.compound} "
                f"(annotated target {candidate.gene}, mechanism '{index.moa}', clinical phase '{index.phase}') "
                f"in {candidate.model_id} with fitted AUC {index.auc:.4f} and curve R2 {index.curve_r2:.4f}."
            ),
            "source_id": index.source_id,
            "conditions": dict(
                conditions,
                compound=index.compound,
                broad_id=index.broad_id,
                screen=index.screen_id,
                assay="PRISM secondary screen fitted dose-response",
            ),
            "evidence_kind": "derived_analysis",
            "limitations": [
                "A fitted screening curve is one retrospective record, not an independently designed biological replicate set.",
                "The screen measures pooled viability; it measures neither target engagement nor pathway activity.",
                "The compound-target annotation comes from the release metadata and was not re-verified experimentally.",
            ],
        },
    ]


def _abundance_action(candidate: ClassifiedCase) -> dict[str, Any]:
    pair = _PAIRS[candidate.archetype]
    separates = pair == (TARGET_MEDIATED, ATTRIBUTION_ERROR)
    outcomes = (
        {TARGET_MEDIATED: "target_expressed", ATTRIBUTION_ERROR: "target_not_expressed"}
        if separates
        # Abundance does not distinguish an implementation gap from mode non-equivalence,
        # and it does not distinguish either from an attribution error once the target is
        # present, so the same observation is declared under both explanations.
        else {identifier: "target_expressed" for identifier in pair}
    )
    return {
        "identifier": "target_abundance_rna",
        "description": (
            f"Retrieve the DepMap 24Q2 RNA abundance (log2(TPM+1)) of {candidate.gene} in "
            f"{candidate.model_id}, establishing whether the annotated target is present in this context."
        ),
        "cost": ACTION_COST,
        "distinguishes": list(pair),
        # The record is bulk RNA abundance. Typing it as a protein measurement
        # let an RNA value discharge a protein premise, which is the one
        # substitution the evidence contract must never make.
        "kind": "rna_abundance_measurement",
        "quantity": "rna_abundance",
        "entity": candidate.gene,
        "units": "log2_tpm_plus_1",
        "supplies": ["abundance:target_rna"],
        "readout": "rna_abundance_log2_tpm1",
        "expected_conditions": {"model_id": candidate.model_id, "gene": candidate.gene},
        "expected_outcomes": outcomes,
        "prediction_value": 0.4,
    }


def _comparator_action(candidate: ClassifiedCase) -> dict[str, Any]:
    pair = _PAIRS[candidate.archetype]
    return {
        "identifier": "mode_matched_comparator",
        "description": (
            f"Retrieve the PRISM fitted response of a second registered {candidate.gene} inhibitor in "
            f"{candidate.model_id}, testing whether any compound against this target produces the phenotype."
        ),
        "cost": ACTION_COST,
        "distinguishes": list(pair),
        "kind": "mode_matched_comparator",
        "quantity": "viability",
        "entity": "cell_population",
        "units": "fitted_auc",
        "supplies": ["functional:mode_comparator"],
        "prerequisites": ["abundance:target_rna"],
        "readout": "viability_auc",
        "expected_conditions": {"model_id": candidate.model_id, "gene": candidate.gene},
        "expected_outcomes": {IMPLEMENTATION_GAP: "comparator_active", MODE_NON_EQUIVALENCE: "comparator_inactive"},
        "prediction_value": 0.7,
    }


def _selectivity_action(candidate: ClassifiedCase) -> dict[str, Any]:
    pair = _PAIRS[candidate.archetype]
    separates = pair == (ATTRIBUTION_ERROR, MODE_NON_EQUIVALENCE)
    outcomes = (
        {ATTRIBUTION_ERROR: "dependency_pan_essential", MODE_NON_EQUIVALENCE: "dependency_selective"}
        if separates
        # A panel-wide selectivity summary says nothing about which of two
        # context-specific explanations holds in this model.
        else {identifier: "dependency_selective" for identifier in pair}
    )
    return {
        "identifier": "dependency_selectivity_profile",
        "description": (
            f"Compute the fraction of DepMap 24Q2 models scoring {candidate.gene} as a dependency, "
            "establishing whether the genetic phenotype is selective or panel-wide."
        ),
        "cost": ACTION_COST,
        "distinguishes": list(pair),
        "kind": "evidence_review",
        "quantity": "selectivity",
        "entity": candidate.gene,
        "units": "dependent_model_fraction",
        "supplies": ["attribution:dependency_selectivity"],
        "readout": "dependent_model_fraction",
        "context_bound": False,
        "expected_conditions": {"gene": candidate.gene},
        "expected_outcomes": outcomes,
        "prediction_value": 0.3,
    }


def _control_context(candidate: ClassifiedCase) -> str:
    """The orthogonal control runs in another model, so it declares that context."""

    control = candidate.control
    assert control is not None and candidate.control_model_id is not None
    return f"{candidate.control_model_id}:{control.ccle_name}" if control.ccle_name else str(candidate.control_model_id)


def _control_action(candidate: ClassifiedCase) -> dict[str, Any]:
    pair = _PAIRS[candidate.archetype]
    return {
        "identifier": "orthogonal_context_control",
        "description": (
            f"Retrieve the PRISM fitted response of {candidate.index.compound} in "
            f"{candidate.control_model_id}, a model that does not score {candidate.gene} as a dependency."
        ),
        "cost": ACTION_COST,
        "distinguishes": list(pair),
        "kind": "orthogonal_control",
        "quantity": "viability",
        "entity": "cell_population",
        "units": "fitted_auc",
        "supplies": ["functional:context_control"],
        "readout": "viability_auc",
        "execution_context": _control_context(candidate),
        "expected_conditions": {"model_id": str(candidate.control_model_id), "gene": candidate.gene},
        "expected_outcomes": {
            TARGET_MEDIATED: "control_context_resistant",
            ATTRIBUTION_ERROR: "control_context_sensitive",
        },
        "prediction_value": 0.6,
    }


def _engagement_action(candidate: ClassifiedCase) -> dict[str, Any]:
    return {
        "identifier": "matched_target_engagement",
        "description": (
            f"Measure condition-matched engagement and residual activity of {candidate.gene} under the "
            f"exact {candidate.index.compound} exposure used in the screen. Not available in this "
            "retrospective package."
        ),
        "cost": ENGAGEMENT_COST,
        "distinguishes": list(_PAIRS[candidate.archetype]),
        "kind": "functional_measurement",
        "quantity": "target_occupancy",
        "entity": candidate.gene,
        "units": "fraction_occupied",
        "supplies": ["functional:target_activity"],
        "available": False,
        "prediction_value": 0.0,
    }


def _premise_registry(candidate: ClassifiedCase, base: "EvidenceBase") -> dict[str, Any]:
    """What each prerequisite field in this package is required to mean.

    Only one field is a prerequisite here: the comparator action needs the
    target's RNA abundance in this model before its result can be read as a
    mode comparison. Declaring the requirement makes the check a measurement
    comparison instead of a string comparison, so retyping the supplying action
    would make the comparator unreachable rather than silently substituting a
    different quantity.

    The requirement is RNA abundance because that is what the release contains.
    It is deliberately not protein abundance: naming the stronger requirement
    the package cannot meet would make every case unsolvable, and naming it
    while accepting an RNA record is the substitution this registry exists to
    prevent.
    """

    return {
        "abundance:target_rna": {
            "quantity": "rna_abundance",
            "entity": candidate.gene,
            "units": "log2_tpm_plus_1",
            "context_identifier": base.context_identifier(candidate.model_id),
            "require_direct_measurement": True,
            "note": (
                "Bulk RNA abundance in this model. It does not establish protein presence, "
                "isoform usage, or residual catalytic activity."
            ),
        }
    }


def _actions(candidate: ClassifiedCase) -> list[dict[str, Any]]:
    actions = [_abundance_action(candidate), _selectivity_action(candidate)]
    if candidate.comparator is not None:
        actions.append(_comparator_action(candidate))
    if candidate.control is not None:
        actions.append(_control_action(candidate))
    actions.append(_engagement_action(candidate))
    return sorted(actions, key=lambda item: item["identifier"])


def _abundance_result(candidate: ClassifiedCase, base: EvidenceBase) -> dict[str, Any]:
    expressed = candidate.abundance >= ARCHETYPE_THRESHOLDS["unexpressed_log2_tpm1"]
    outcome = "target_expressed" if expressed else "target_not_expressed"
    state = "expressed" if expressed else "not_expressed"
    return {
        "action_identifier": "target_abundance_rna",
        "outcome": outcome,
        "statement": (
            f"DepMap 24Q2 reports {candidate.gene} RNA abundance of {candidate.abundance:.4f} "
            f"log2(TPM+1) in {candidate.model_id}."
        ),
        "source_id": f"DepMap-24Q2:OmicsExpressionProteinCodingGenesTPMLogp1.csv:{candidate.model_id}:{candidate.gene}",
        "context_identifier": base.context_identifier(candidate.model_id),
        "conditions": {
            "model_id": candidate.model_id,
            "gene": candidate.gene,
            "assay": "bulk RNA abundance, log2(TPM+1)",
        },
        "metrics": {"log2_tpm1": f"{candidate.abundance:.6f}"},
        "record_count": 1,
        "independent_units": 1,
        "record_validated": True,
        "biological_quality": "passed",
        "evidence_kind": "real_measurement",
        "interpretation_fields": ["abundance:target_rna", f"abundance:target_rna:{state}"],
        "limitations": [
            "RNA abundance is not protein abundance, and neither is target activity or engagement.",
            "The measurement comes from the untreated model profile, not from the treated screen condition.",
        ],
    }


def _comparator_result(candidate: ClassifiedCase, base: EvidenceBase) -> dict[str, Any]:
    comparator = candidate.comparator
    assert comparator is not None
    active = comparator.auc <= ARCHETYPE_THRESHOLDS["comparator_active_auc"]
    outcome = "comparator_active" if active else "comparator_inactive"
    state = "active" if active else "inactive"
    quality = "passed" if comparator.curve_r2 >= ARCHETYPE_THRESHOLDS["minimum_curve_r2"] else "failed"
    return {
        "action_identifier": "mode_matched_comparator",
        "outcome": outcome,
        "statement": (
            f"PRISM Repurposing 19Q4 {comparator.screen_id} reports {comparator.compound} "
            f"(annotated target {candidate.gene}, mechanism '{comparator.moa}') in {candidate.model_id} "
            f"with fitted AUC {comparator.auc:.4f} and curve R2 {comparator.curve_r2:.4f}."
        ),
        "source_id": comparator.source_id,
        "context_identifier": base.context_identifier(candidate.model_id),
        "conditions": {
            "model_id": candidate.model_id,
            "gene": candidate.gene,
            "compound": comparator.compound,
            "broad_id": comparator.broad_id,
            "screen": comparator.screen_id,
            "assay": "PRISM secondary screen fitted dose-response",
        },
        "metrics": {"auc": f"{comparator.auc:.6f}", "curve_r2": f"{comparator.curve_r2:.6f}"},
        "record_count": 1,
        "independent_units": 1,
        "record_validated": True,
        "biological_quality": quality,
        "evidence_kind": "real_measurement",
        "interpretation_fields": ["functional:mode_comparator", f"functional:mode_comparator:{state}"],
        "limitations": [
            "The comparator shares an annotated target, not a measured intracellular exposure or residual activity.",
            "Two compounds inactive in one screen do not establish that the target cannot be inhibited in this model.",
            "The comparison is between fitted screening curves, not between matched engagement measurements.",
        ],
    }


def _selectivity_result(candidate: ClassifiedCase) -> dict[str, Any]:
    pan_essential = candidate.dependent_fraction >= ARCHETYPE_THRESHOLDS["pan_essential_gene_fraction"]
    outcome = "dependency_pan_essential" if pan_essential else "dependency_selective"
    state = "pan_essential" if pan_essential else "selective"
    return {
        "action_identifier": "dependency_selectivity_profile",
        "outcome": outcome,
        "statement": (
            f"Across DepMap 24Q2 models, {candidate.dependent_fraction * 100:.1f} percent score "
            f"{candidate.gene} at or below a gene effect of "
            f"{ARCHETYPE_THRESHOLDS['strong_dependency'] + 0.2:.1f}, which classifies the genetic "
            f"phenotype as {state.replace('_', ' ')}."
        ),
        "source_id": f"DepMap-24Q2:CRISPRGeneEffect.csv:panel-summary:{candidate.gene}",
        "context_identifier": None,
        "conditions": {"gene": candidate.gene, "assay": "panel summary over processed gene-effect scores"},
        "metrics": {"dependent_model_fraction": f"{candidate.dependent_fraction:.6f}"},
        "record_count": 1,
        "record_validated": True,
        "biological_quality": "unknown",
        "evidence_kind": "derived_analysis",
        "interpretation_fields": ["attribution:dependency_selectivity", f"attribution:dependency_selectivity:{state}"],
        "limitations": [
            "This is a derived summary over already-processed scores, not a new measurement, and it cannot satisfy a biological premise.",
            "A panel-wide dependency does not establish that a compound's absent phenotype has the same cause.",
            "The threshold is a declared construction setting, not a validated biological cut-off.",
        ],
    }


def _control_result(candidate: ClassifiedCase, base: EvidenceBase) -> dict[str, Any]:
    control = candidate.control
    assert control is not None and candidate.control_model_id is not None
    sensitive = control.auc <= ARCHETYPE_THRESHOLDS["comparator_active_auc"]
    outcome = "control_context_sensitive" if sensitive else "control_context_resistant"
    state = "sensitive" if sensitive else "resistant"
    effect = candidate.control_gene_effect if candidate.control_gene_effect is not None else float("nan")
    return {
        "action_identifier": "orthogonal_context_control",
        "outcome": outcome,
        "statement": (
            f"PRISM Repurposing 19Q4 {control.screen_id} reports {control.compound} in "
            f"{candidate.control_model_id} with fitted AUC {control.auc:.4f} and curve R2 "
            f"{control.curve_r2:.4f}; that model scores {candidate.gene} at gene effect {effect:.4f}, "
            "so it is not a genetic dependency there."
        ),
        "source_id": control.source_id,
        "context_identifier": _control_context(candidate),
        "conditions": {
            "model_id": str(candidate.control_model_id),
            "gene": candidate.gene,
            "compound": control.compound,
            "screen": control.screen_id,
            "assay": "PRISM secondary screen fitted dose-response",
        },
        "metrics": {"auc": f"{control.auc:.6f}", "curve_r2": f"{control.curve_r2:.6f}", "gene_effect": f"{effect:.6f}"},
        "record_count": 1,
        "independent_units": 1,
        "record_validated": True,
        "biological_quality": "passed",
        "evidence_kind": "real_measurement",
        "interpretation_fields": ["functional:context_control", f"functional:context_control:{state}"],
        "limitations": [
            "The control model differs from the index model in every genomic and lineage respect, not only in the dependency; it is not an isogenic control.",
            "Comparable sensitivity in a non-dependent model is consistent with target-independent activity but does not identify the responsible target.",
        ],
    }


def _results(candidate: ClassifiedCase, base: EvidenceBase) -> list[dict[str, Any]]:
    results = [_abundance_result(candidate, base), _selectivity_result(candidate)]
    if candidate.comparator is not None:
        results.append(_comparator_result(candidate, base))
    if candidate.control is not None:
        results.append(_control_result(candidate, base))
    return sorted(results, key=lambda item: item["action_identifier"])


def _licensing_rules(candidate: ClassifiedCase, results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """State which decision the revealed evidence licenses, and under which observation.

    A rule resting on a measurement requires that measurement to have passed its
    declared quality check: an uninterpretable record cannot license an action.
    The panel selectivity summary is the exception, because a derived analysis
    over published scores has no biological quality check of its own; it
    constrains how existing measurements are read rather than adding one.

    These are evidence-sufficiency rules, not biological ground truth: each one
    says that a named development action is supported by a specific revealed
    observation in this context. A rule with no required outcome states that the
    public premise already licenses the action, so acquiring more evidence
    cannot change it within this package.
    """

    observed = {item["action_identifier"]: item["outcome"] for item in results}
    rules: list[dict[str, Any]] = []
    if candidate.archetype is CaseArchetype.CONCORDANT_PROGRAM_SUPPORT:
        rules.append(
            {
                "decision": "continue",
                "required_outcomes": {},
                "note": (
                    "A strong selective genetic dependency and a potent fitted response for a "
                    "compound annotated to that target are concordant in this context; no menu "
                    "action in this package can change that within the declared limits."
                ),
            }
        )
    if candidate.archetype is CaseArchetype.UNATTRIBUTED_PHARMACOLOGY:
        if observed.get("target_abundance_rna") == "target_not_expressed":
            rules.append(
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {"target_abundance_rna": "target_not_expressed"},
                    "required_interpretation_fields": ["abundance:target_rna:not_expressed"],
                    "require_biological_quality": True,
                    "note": "A compound cannot act through a target the context does not express.",
                }
            )
        if observed.get("orthogonal_context_control") == "control_context_sensitive":
            rules.append(
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {"orthogonal_context_control": "control_context_sensitive"},
                    "required_interpretation_fields": ["functional:context_control:sensitive"],
                    "require_biological_quality": True,
                    "note": "Comparable potency in a model without the dependency is not target-attributable activity.",
                }
            )
    if candidate.archetype is CaseArchetype.IMPLEMENTATION_GAP:
        rules.append(
            {
                "decision": "revise_intervention",
                "required_outcomes": {
                    "mode_matched_comparator": "comparator_active",
                    "target_abundance_rna": "target_expressed",
                },
                "required_interpretation_fields": [
                    "functional:mode_comparator:active",
                    "abundance:target_rna:expressed",
                ],
                "require_biological_quality": True,
                "note": (
                    "The target is present and a second registered inhibitor does produce the "
                    "phenotype, so the index compound's realisation is the failing element."
                ),
            }
        )
    if candidate.archetype is CaseArchetype.MODE_NON_EQUIVALENCE:
        rules.append(
            {
                "decision": "change_intervention_mode",
                "required_outcomes": {
                    "mode_matched_comparator": "comparator_inactive",
                    "target_abundance_rna": "target_expressed",
                },
                "required_interpretation_fields": [
                    "functional:mode_comparator:inactive",
                    "abundance:target_rna:expressed",
                ],
                "require_biological_quality": True,
                "note": (
                    "The target is present and two structurally distinct inhibitors both fail, "
                    "while removal of the gene does not, which supports reconsidering the mode."
                ),
            }
        )
        rules.append(
            {
                "decision": "defer",
                "required_outcomes": {
                    "mode_matched_comparator": "comparator_inactive",
                    "target_abundance_rna": "target_expressed",
                },
                "require_biological_quality": True,
                "note": (
                    "Informed deferral is equally licensed here, because no condition-matched "
                    "engagement measurement exists to separate insufficient inhibition from mode "
                    "non-equivalence. Deferral before acquiring this evidence is not licensed."
                ),
            }
        )
    if candidate.archetype is CaseArchetype.PAN_ESSENTIAL_ATTRIBUTION:
        rules.append(
            {
                "decision": "revise_attribution",
                "required_outcomes": {"dependency_selectivity_profile": "dependency_pan_essential"},
                "required_interpretation_fields": ["attribution:dependency_selectivity:pan_essential"],
                "note": (
                    "A panel-wide dependency is not evidence for a selective target programme in "
                    "this model, so the attribution of the genetic phenotype must be revised "
                    "before any mode conclusion."
                ),
            }
        )
    if candidate.archetype is CaseArchetype.NO_DISCRIMINATING_EVIDENCE:
        rules.append(
            {
                "decision": "defer",
                "required_outcomes": {},
                "note": (
                    "No registered menu action declares a different observation under the two "
                    "explanations, and the engagement measurement that would is unavailable."
                ),
            }
        )
    return rules


_CRITICAL_ACTIONS: Mapping[CaseArchetype, tuple[str, ...]] = {
    CaseArchetype.CONCORDANT_PROGRAM_SUPPORT: (),
    CaseArchetype.UNATTRIBUTED_PHARMACOLOGY: ("target_abundance_rna",),
    CaseArchetype.IMPLEMENTATION_GAP: ("target_abundance_rna", "mode_matched_comparator"),
    CaseArchetype.MODE_NON_EQUIVALENCE: ("target_abundance_rna", "mode_matched_comparator"),
    CaseArchetype.PAN_ESSENTIAL_ATTRIBUTION: ("dependency_selectivity_profile",),
    CaseArchetype.NO_DISCRIMINATING_EVIDENCE: (),
}


def _case_limitations(candidate: ClassifiedCase) -> list[str]:
    return [
        "This is a retrospective package built from public processed records; it contains no new experiment.",
        "The CRISPR and PRISM records are not matched for perturbation method, dose, exposure duration, assay, or replicate structure.",
        "No condition-matched target engagement or residual-activity measurement is available for any condition in this package.",
        "Compound-target annotations are release metadata; a single annotated target does not establish pharmacological selectivity.",
        "RNA abundance, protein abundance, target occupancy, proximal activity, viability and "
        "selectivity are distinct quantities in this package; no action substitutes one for another.",
        f"Every registered menu action returns an existing public record for {candidate.gene}; none commissions a new measurement.",
    ]


def build_case_payloads(
    candidate: ClassifiedCase, base: EvidenceBase
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return the public case, the evaluator-only results and scoring, and the metadata."""

    results = _results(candidate, base)
    rules = _licensing_rules(candidate, results)
    if not rules:
        raise ValueError(f"Case '{candidate.identifier}' produced no licensing rule.")
    releases = ", ".join(item.citation for item in base.releases)
    public = {
        "identifier": candidate.identifier,
        "provenance": f"retrospective_real_public_records; {releases}",
        "evaluation_status": "retrospective_real_licensing_case",
        "initial_evidence": _initial_evidence(candidate, base),
        "context_identifier": base.context_identifier(candidate.model_id),
        "budget": CASE_BUDGET,
        "hypotheses": [
            {key: value for key, value in item.items() if key != "causal_factor"}
            for item in _hypotheses(candidate)
        ],
        "actions": _actions(candidate),
        "premise_registry": _premise_registry(candidate, base),
        "limitations": _case_limitations(candidate),
    }
    private = {
        "case_id": candidate.identifier,
        "results": results,
        "scoring": {
            "decision_rules": rules,
            "critical_actions": list(_CRITICAL_ACTIONS[candidate.archetype]),
        },
    }
    metadata = {
        "case_id": candidate.identifier,
        "archetype": candidate.archetype.value,
        "gene": candidate.gene,
        "model_id": candidate.model_id,
        "cell_line": candidate.index.ccle_name,
        "index_compound": candidate.index.compound,
        "comparator_compound": candidate.comparator.compound if candidate.comparator else None,
        "control_model_id": candidate.control_model_id,
        "gene_effect": candidate.gene_effect,
        "index_auc": candidate.index.auc,
        "index_curve_r2": candidate.index.curve_r2,
        "abundance_log2_tpm1": candidate.abundance,
        "dependent_model_fraction": candidate.dependent_fraction,
        "licensed_decisions": sorted({rule["decision"] for rule in rules}),
        "critical_actions": list(_CRITICAL_ACTIONS[candidate.archetype]),
        "source_cluster": candidate.gene,
    }
    return public, private, metadata


def build_cases(
    base: EvidenceBase, *, per_archetype: int = 12, per_gene: int = 3
) -> tuple[tuple[dict[str, Any], dict[str, Any], dict[str, Any]], ...]:
    """Classify, sample, and materialise the frozen case package."""

    selected = select_cases(enumerate_candidates(base), per_archetype=per_archetype, per_gene=per_gene)
    # One global grouping assignment over every gene the package uses, made
    # before any per-archetype balancing, so a gene cannot cross partitions.
    gene_order = sorted({candidate.gene for candidate in selected})
    payloads = []
    for candidate in selected:
        public, private, metadata = build_case_payloads(candidate, base)
        metadata["split"] = assign_split(candidate.gene, gene_order)
        payloads.append((public, private, metadata))
    return tuple(payloads)


def write_cases(
    payloads: Iterable[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    *,
    public_directory: Path,
    private_directory: Path,
    manifest_path: Path,
    releases: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Write the public cases, the evaluator-only files, and the evaluator manifest."""

    public_directory.mkdir(parents=True, exist_ok=True)
    private_directory.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for public, private, metadata in payloads:
        identifier = public["identifier"]
        (public_directory / f"{identifier}.json").write_text(
            json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (private_directory / f"{identifier}.results.json").write_text(
            json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        entries.append(metadata)
    manifest = {
        "construction_settings": dict(ARCHETYPE_THRESHOLDS),
        "action_cost": ACTION_COST,
        "case_budget": CASE_BUDGET,
        "releases": [dict(item) for item in releases],
        "cases": entries,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


@dataclass(frozen=True)
class CandidateCase:
    """Source-screening record, not an evaluation case or a scientific verdict."""

    identifier: str
    source_clusters: tuple[str, ...]
    biological_context: str
    category: str
    status: str
    action_identifiers: tuple[str, ...]
    hidden_result_actions: tuple[str, ...]
    decision_branch_actions: tuple[str, ...]
    provenance_complete: bool
    conditions_complete: bool
    selection_blinded_to_policy: bool
    independent_review_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class CandidateAssessment:
    """Eligibility verdict for one candidate case, with its blocking reasons."""

    identifier: str
    eligible_for_development: bool
    blocking_reasons: tuple[str, ...]


def load_candidate_registry(path: Path) -> tuple[CandidateCase, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("candidates"), list):
        raise ValueError("Candidate registry requires a 'candidates' list.")
    candidates = tuple(_candidate(value) for value in data["candidates"])
    identifiers = [candidate.identifier for candidate in candidates]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Candidate identifiers must be unique.")
    return candidates


def assess_candidate(candidate: CandidateCase) -> CandidateAssessment:
    """Apply G2 eligibility criteria without reading hidden outcome values."""

    blockers: list[str] = []
    if candidate.status != "screened":
        blockers.append("candidate_not_screened")
    if len(candidate.source_clusters) < 1 or not candidate.provenance_complete:
        blockers.append("incomplete_provenance")
    if not candidate.conditions_complete:
        blockers.append("incomplete_condition_metadata")
    if len(candidate.action_identifiers) < 2:
        blockers.append("fewer_than_two_real_action_paths")
    if len(candidate.hidden_result_actions) < 2:
        blockers.append("insufficient_hidden_result_coverage")
    if len(candidate.decision_branch_actions) < 2:
        blockers.append("no_registered_action_tradeoff")
    if not candidate.selection_blinded_to_policy:
        blockers.append("selection_not_blinded_to_policy")
    if candidate.independent_review_status != "completed":
        blockers.append("independent_review_incomplete")
    return CandidateAssessment(candidate.identifier, not blockers, tuple(blockers))


def assess_registry(path: Path) -> tuple[CandidateAssessment, ...]:
    return tuple(assess_candidate(candidate) for candidate in load_candidate_registry(path))


def _candidate(data: Any) -> CandidateCase:
    if not isinstance(data, dict):
        raise ValueError("Each candidate must be an object.")
    status = _text(data, "status")
    if status not in {"screened", "screening", "excluded"}:
        raise ValueError("Candidate status must be screened, screening, or excluded.")
    review = _text(data, "independent_review_status")
    if review not in {"not_started", "in_progress", "completed", "not_applicable"}:
        raise ValueError("Candidate independent_review_status is invalid.")
    return CandidateCase(
        identifier=_text(data, "identifier"),
        source_clusters=_texts(data, "source_clusters", require_items=True),
        biological_context=_text(data, "biological_context"),
        category=_text(data, "category"),
        status=status,
        action_identifiers=_texts(data, "action_identifiers"),
        hidden_result_actions=_texts(data, "hidden_result_actions"),
        decision_branch_actions=_texts(data, "decision_branch_actions"),
        provenance_complete=_bool(data, "provenance_complete"),
        conditions_complete=_bool(data, "conditions_complete"),
        selection_blinded_to_policy=_bool(data, "selection_blinded_to_policy"),
        independent_review_status=review,
        notes=_texts(data, "notes", require_items=True),
    )


def _text(data: dict[str, Any], name: str) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Candidate '{name}' must be nonempty text.")
    return value.strip()


def _texts(data: dict[str, Any], name: str, *, require_items: bool = False) -> tuple[str, ...]:
    value = data.get(name)
    if (
        not isinstance(value, list)
        or (require_items and not value)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ValueError(f"Candidate '{name}' must be a list of nonempty text.")
    return tuple(item.strip() for item in value)


def _bool(data: dict[str, Any], name: str) -> bool:
    value = data.get(name)
    if type(value) is not bool:
        raise ValueError(f"Candidate '{name}' must be a boolean.")
    return value


def build_main(argv: Sequence[str] | None = None) -> int:
    """Build the real-data case package and return a process exit code."""

    parser = argparse.ArgumentParser(
        description="Build leakage-bounded mechanism-contrast cases from the local DepMap and PRISM releases."
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--public-cases", type=Path, default=Path("data/evaluation/cases/real/public"))
    parser.add_argument("--private-results", type=Path, default=Path("data/evaluation/cases/real/private"))
    parser.add_argument("--manifest", type=Path, default=Path("data/evaluation/derived/real_case_manifest.json"))
    parser.add_argument("--per-archetype", type=int, default=12)
    parser.add_argument("--per-gene", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing case package.")
    arguments = parser.parse_args(argv)
    if arguments.per_archetype < 1 or arguments.per_gene < 1:
        parser.error("--per-archetype and --per-gene must be positive.")

    existing = sorted(arguments.public_cases.glob("*.json")) if arguments.public_cases.is_dir() else []
    if existing and not arguments.overwrite:
        parser.error("A case package already exists; pass --overwrite to rebuild it.")
    for path in existing:
        path.unlink()
    if arguments.private_results.is_dir() and arguments.overwrite:
        for path in arguments.private_results.glob("*.results.json"):
            path.unlink()

    base = build_evidence_base(arguments.workspace)
    payloads = build_cases(base, per_archetype=arguments.per_archetype, per_gene=arguments.per_gene)
    manifest = write_cases(
        payloads,
        public_directory=arguments.public_cases,
        private_directory=arguments.private_results,
        manifest_path=arguments.manifest,
        releases=base.release_manifest(),
    )
    archetypes = Counter(entry["archetype"] for entry in manifest["cases"])
    splits = Counter(entry["split"] for entry in manifest["cases"])
    print(
        json.dumps(
            {
                "cases": len(manifest["cases"]),
                "archetypes": dict(sorted(archetypes.items())),
                "splits": dict(sorted(splits.items())),
                "genes": len({entry["gene"] for entry in manifest["cases"]}),
                "models": len({entry["model_id"] for entry in manifest["cases"]}),
                "manifest": str(arguments.manifest),
            },
            indent=2,
        )
    )
    return 0


def screen_main(argv: Sequence[str] | None = None) -> int:
    """Run the G2 candidate screening CLI and return a process exit code."""

    parser = argparse.ArgumentParser(description="Validate MAESTRO G2 source-screening records.")
    parser.add_argument("--registry", type=Path, default=Path("data/evaluation/candidate_registry.json"))
    arguments = parser.parse_args(argv)
    assessments = assess_registry(arguments.registry)
    print(json.dumps([asdict(item) for item in assessments], ensure_ascii=False, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or screen source-backed case records.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "screen"):
        commands.add_parser(name, add_help=False)
    arguments, remaining = parser.parse_known_args(argv)
    return {"build": build_main, "screen": screen_main}[arguments.command](remaining)


if __name__ == "__main__":
    raise SystemExit(main())
