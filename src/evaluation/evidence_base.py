"""Provenance-checked extraction of a real perturbation evidence base from local releases.

File summary
- Path: src/evaluation/evidence_base.py
- Purpose: Turn the local DepMap and PRISM releases into a small, hashed evidence base for case building.
- Core points:
  - Every extracted value keeps its release, file, row key, and declared checksum.
  - Derived features (dependency selectivity, comparator sets) are labelled derived, never measured anew.
  - Extraction is dependency-free and streams the wide release files column-wise.
- Interfaces: `EvidenceBase`, `build_evidence_base`, `DependencyRecord`, `ExposureRecord`, `SourceRelease`
- Depends on: (standard library only)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

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


def _number(value: object) -> float | None:
    if value in (None, "", "NA", "NaN", "Inf", "-Inf"):
        return None
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None
