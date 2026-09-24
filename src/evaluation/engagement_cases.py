"""Build the engagement-repair package from real releases, blind to every hidden value.

File summary
- Path: src/evaluation/engagement_cases.py
- Purpose: execute the pre-registration
  `data/evaluation/preregistrations/20260914_engagement_package.md`. Each case states a
  genetic-versus-pharmacological discordance from public records, offers a menu that cannot
  settle it, and leaves the interpretation premise to a capability a policy has to propose.
  The premise is real, the hidden record is real, and the outcome rule was fixed before any
  value was read.
- Core points:
  - Selection reads premise releases only: dependency, abundance, fitted phenotype and the
    engagement release's own curated-target annotation and coverage flags. It never reads an
    engagement value, so no case exists because its answer was convenient.
  - Licensing rules enumerate every possible outcome of every route, so writing them needs
    no knowledge of which outcome occurred. They are an evidence-sufficiency convention
    declared in advance, not biological ground truth.
  - The always-hidden partition is an independent release (cell-lysate competition binding),
    which the framework refuses as an engagement supplier and which is therefore usable only
    as a test of a decision already made.
  - Every screening decision, including every exclusion, is written to a screening table.
- Interfaces: `EngagementArchetype`, `Candidate`, `screen_k562`, `screen_mcf7`,
  `build_package`, `write_package`, `capability_registry_payload`, `main`
- Depends on: evaluation.engagement_sources, evaluation.capabilities, evaluation.case_builder
  (declared thresholds and the split rule), evaluation.lab_cost, maestro.models
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.capabilities import canonical_repair_identifier  # noqa: E402
from evaluation.case_builder import ARCHETYPE_THRESHOLDS, assign_split  # noqa: E402
from evaluation.engagement_sources import (  # noqa: E402
    ENGAGEMENT_UNITS,
    DepMapProfile,
    EngagementAsset,
    Gdsc2Record,
    KinobeadsRecord,
    load_depmap_profile,
    load_engagement_asset,
    load_gdsc2,
    load_kinobeads,
    normalise_compound,
)
from evaluation.xlsx import Workbook, sheet_digest  # noqa: E402
from maestro.models import BiologicalQuantity, EvidenceActionKind  # noqa: E402

ACTION_COST = 1.0
CASE_BUDGET = 3.0
UNAVAILABLE_ENGAGEMENT_COST = 3.0
# The report's section 36 illustrative row for a condition-matched engagement assay. It is
# the only new-measurement price in the package, and the action carrying it is unavailable.
UNAVAILABLE_ENGAGEMENT_WELLS = 24
UNAVAILABLE_ENGAGEMENT_DAYS = 4.0
# PRISM's own screened range, quoted from `data/raw/prism/secondary-screen-readme.txt`:
# "an 8-step, 4-fold dilution, starting from 10uM".
PRISM_MAXIMUM_DOSE_MICROMOLAR = 10.0

K562_MODEL = "ACH-000551"
K562_CONTEXT = "ACH-000551:K562"
K562_GDSC_NAME = "K-562"
MCF7_MODEL = "ACH-000019"
MCF7_CONTEXT = "ACH-000019:MCF7"
MCF7_GDSC_NAME = "MCF7"

PISA_ZIP = Path("data/external/pisa_living_cells/PMC11554310_supplementary.zip")
PISA_CELL_MEMBER = "elife-95595-supp3.xlsx"
PISA_ANNOTATION_MEMBER = "elife-95595-supp1.xlsx"
PISA_SOURCE = (
    "PISA living-cell arm, eLife 2024 (DOI 10.7554/eLife.95595), "
    "member elife-95595-supp3.xlsx, sheet 'Cell-based data'"
)
GDSC2_PATH = Path("data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx")
KINOBEADS_PATH = Path("data/raw/kinobeads/Klaeger_allTargets.xlsx")
DEPMAP_DIRECTORY = Path("data/raw/depmap")
PRISM_CURVES = Path("data/raw/prism/secondary-screen-dose-response-curve-parameters.csv")
PRISM_SCREEN_PREFERENCE = ("MTS010", "MTS006", "MTS005", "HTS002")

ABUNDANCE_PREMISE = "abundance:target_rna"
SELECTIVITY_PREMISE = "attribution:dependency_selectivity"
INDEX_ENGAGEMENT_PREMISE = "engagement:index_on_target"
COMPARATOR_ENGAGEMENT_PREMISE = "engagement:comparator_on_target"
OVERLAP_PREMISE = "attribution:engaged_context_dependency"

INSUFFICIENT = "insufficient_functional_perturbation"
MODE_NON_EQUIVALENCE = "genetic_pharmacological_mode_non_equivalence"
TARGET_MEDIATED = "target_mediated_pharmacology"
ATTRIBUTION_ERROR = "phenotype_not_target_attributable"

DEVELOPMENT_ACTIONS = {
    INSUFFICIENT: "revise_intervention",
    MODE_NON_EQUIVALENCE: "change_intervention_mode",
    TARGET_MEDIATED: "continue",
    ATTRIBUTION_ERROR: "revise_attribution",
}
CAUSAL_FACTORS = {
    INSUFFICIENT: "incomplete_perturbation",
    MODE_NON_EQUIVALENCE: "mode_non_equivalence",
    TARGET_MEDIATED: "target_mediated",
    ATTRIBUTION_ERROR: "attribution_error",
}

INDEX_CAPABILITY = "pisa_living_cell_engagement_k562"
COMPARATOR_CAPABILITY = "pisa_living_cell_comparator_engagement_k562"
OVERLAP_CAPABILITY = "pisa_living_cell_engaged_dependency_overlap_k562"
LYSATE_CAPABILITY = "kinobeads_lysate_binding_estimate"


class EngagementArchetype(str, Enum):
    """The joint premise pattern a case represents, recorded outside the public file."""

    ENGAGEMENT_GAP_OR_MODE = "engagement_gap_or_mode"
    UNATTRIBUTED_ACTIVE_COMPOUND = "unattributed_active_compound"
    CONCORDANT_SUPPORT = "concordant_support"
    NO_ENGAGEMENT_COVERAGE = "no_engagement_coverage"
    ENGAGEMENT_CAPABILITY_OUT_OF_CONTEXT = "engagement_capability_out_of_context"


PAIRS: Mapping[EngagementArchetype, tuple[str, str]] = {
    EngagementArchetype.ENGAGEMENT_GAP_OR_MODE: (INSUFFICIENT, MODE_NON_EQUIVALENCE),
    EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND: (TARGET_MEDIATED, ATTRIBUTION_ERROR),
    EngagementArchetype.CONCORDANT_SUPPORT: (TARGET_MEDIATED, ATTRIBUTION_ERROR),
    EngagementArchetype.NO_ENGAGEMENT_COVERAGE: (INSUFFICIENT, MODE_NON_EQUIVALENCE),
    EngagementArchetype.ENGAGEMENT_CAPABILITY_OUT_OF_CONTEXT: (INSUFFICIENT, MODE_NON_EQUIVALENCE),
}


@dataclass(frozen=True)
class PhenotypeRecord:
    """One fitted phenotype curve, from whichever release supplies this context."""

    release: str
    source_id: str
    compound: str
    identifier: str
    active: float | None
    ic50_micromolar: float | None
    maximum_dose_micromolar: float
    auc: float
    fit_quality: float
    statement: str
    conditions: Mapping[str, str]

    @property
    def is_active(self) -> bool:
        """The release's own boundary: a fitted IC50 inside the screened range."""

        return self.ic50_micromolar is not None and self.ic50_micromolar <= self.maximum_dose_micromolar + 1e-12


@dataclass(frozen=True)
class Candidate:
    """One screened (context, compound) pair with its premise values and its verdict."""

    context_identifier: str
    model_id: str
    cell_line: str
    compound: str
    curated_targets: tuple[str, ...]
    primary_target: str | None
    gene_effect: float | None
    dependent_fraction: float | None
    abundance: float | None
    phenotype: PhenotypeRecord | None
    engagement_covered: bool
    comparator: str | None
    comparator_engagement_covered: bool
    archetype: EngagementArchetype | None
    exclusion: str | None

    def row(self) -> Mapping[str, object]:
        return {
            "context_identifier": self.context_identifier,
            "model_id": self.model_id,
            "compound": self.compound,
            "curated_targets": list(self.curated_targets),
            "primary_target": self.primary_target,
            "gene_effect": None if self.gene_effect is None else round(self.gene_effect, 6),
            "dependent_fraction": None if self.dependent_fraction is None else round(self.dependent_fraction, 6),
            "abundance_log2_tpm1": None if self.abundance is None else round(self.abundance, 6),
            "phenotype_release": None if self.phenotype is None else self.phenotype.release,
            "phenotype_active": None if self.phenotype is None else self.phenotype.is_active,
            "phenotype_ic50_micromolar": None if self.phenotype is None else self.phenotype.ic50_micromolar,
            "phenotype_auc": None if self.phenotype is None else self.phenotype.auc,
            "engagement_covered": self.engagement_covered,
            "comparator": self.comparator,
            "comparator_engagement_covered": self.comparator_engagement_covered,
            "archetype": None if self.archetype is None else self.archetype.value,
            "exclusion": self.exclusion,
        }


def _pisa_annotation(zip_path: Path) -> Mapping[str, Mapping[str, object]]:
    """The release's own curated target annotation and assay coverage flags."""

    workbook = Workbook(zip_path, member=PISA_ANNOTATION_MEMBER)
    rows = list(workbook.rows("Sheet1"))
    workbook.close()
    annotation: dict[str, Mapping[str, object]] = {}
    for row in rows[1:]:
        if not row or not isinstance(row[0], str):
            continue
        name = row[0].strip()
        raw_targets = str(row[1] or "")
        targets = tuple(
            part.strip()
            for part in raw_targets.replace(":", ";").split(";")
            if part.strip()
        )
        annotation[name] = {
            "targets": targets,
            "in_cells": str(row[2]).strip() == "Yes" if len(row) > 2 else False,
            "in_lysates": str(row[3]).strip() == "Yes" if len(row) > 3 else False,
        }
    return annotation


def _gdsc_phenotype(records: Sequence[Gdsc2Record], compound: str) -> PhenotypeRecord | None:
    """The GDSC2 curve for one compound, preferring the widest screened range."""

    folded = normalise_compound(compound)
    matches = [record for record in records if normalise_compound(record.drug_name) == folded]
    if not matches:
        return None
    # Declared before any run: the widest tested range first, then the lowest drug id, so
    # the choice never depends on the response the curve reports.
    chosen = sorted(matches, key=lambda record: (-record.maximum_concentration, record.drug_id))[0]
    return PhenotypeRecord(
        release="GDSC2 release 8.5",
        source_id=chosen.source_id(),
        compound=chosen.drug_name,
        identifier=chosen.drug_id,
        active=None,
        ic50_micromolar=chosen.ic50_micromolar,
        maximum_dose_micromolar=chosen.maximum_concentration,
        auc=chosen.auc,
        fit_quality=chosen.rmse,
        statement=(
            f"GDSC2 release 8.5 reports {chosen.drug_name} (putative target "
            f"'{chosen.putative_target}', pathway '{chosen.pathway}') in {chosen.cell_line} with "
            f"fitted ln(IC50) {chosen.ln_ic50:.4f} ({chosen.ic50_micromolar:.4f} uM), AUC "
            f"{chosen.auc:.4f} and RMSE {chosen.rmse:.4f} over a screened range of "
            f"{chosen.minimum_concentration}-{chosen.maximum_concentration} uM."
        ),
        conditions={
            "cell_line": chosen.cell_line,
            "sanger_model_id": chosen.sanger_model_id,
            "drug_id": chosen.drug_id,
            "assay": "GDSC2 fitted dose-response",
            "maximum_screened_concentration_micromolar": str(chosen.maximum_concentration),
        },
    )


def _prism_rows(path: Path, model_id: str) -> tuple[Mapping[str, str], ...]:
    """PRISM fitted curves for one model, one screen per compound by release preference."""

    order = {screen: rank for rank, screen in enumerate(PRISM_SCREEN_PREFERENCE)}
    best: dict[str, Mapping[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if (row.get("depmap_id") or "").strip() != model_id:
                continue
            target = (row.get("target") or "").strip()
            if not target or "," in target:
                continue
            name = (row.get("name") or "").strip()
            if not name:
                continue
            current = best.get(name)
            if current is None or order.get(row.get("screen_id", ""), 99) < order.get(current.get("screen_id", ""), 99):
                best[name] = row
    return tuple(best.values())


def _prism_phenotype(row: Mapping[str, str]) -> PhenotypeRecord | None:
    ic50 = _number(row.get("ic50"))
    auc = _number(row.get("auc"))
    r2 = _number(row.get("r2"))
    if auc is None or r2 is None:
        return None
    return PhenotypeRecord(
        release="PRISM Repurposing 19Q4",
        source_id=(
            "PRISM-19Q4:secondary-screen-dose-response-curve-parameters.csv:"
            f"{row.get('depmap_id')}:{row.get('broad_id')}:{row.get('screen_id')}"
        ),
        compound=(row.get("name") or "").strip(),
        identifier=(row.get("broad_id") or "").strip(),
        active=None,
        ic50_micromolar=ic50,
        maximum_dose_micromolar=PRISM_MAXIMUM_DOSE_MICROMOLAR,
        auc=auc,
        fit_quality=r2,
        statement=(
            f"PRISM Repurposing 19Q4 {row.get('screen_id')} reports {(row.get('name') or '').strip()} "
            f"(annotated target {(row.get('target') or '').strip()}, mechanism "
            f"'{(row.get('moa') or 'unknown').strip()}') in {row.get('depmap_id')} with fitted AUC "
            f"{auc:.4f}, curve R2 {r2:.4f} and fitted IC50 "
            f"{'unreported' if ic50 is None else format(ic50, '.4f') + ' uM'} over the release's "
            f"8-step dilution from {PRISM_MAXIMUM_DOSE_MICROMOLAR} uM."
        ),
        conditions={
            "model_id": str(row.get("depmap_id")),
            "broad_id": str(row.get("broad_id")),
            "screen": str(row.get("screen_id")),
            "assay": "PRISM secondary screen fitted dose-response",
            "maximum_screened_concentration_micromolar": str(PRISM_MAXIMUM_DOSE_MICROMOLAR),
        },
    )


def _number(value: object) -> float | None:
    if value in (None, "", "NA", "NaN", "Inf", "-Inf"):
        return None
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _primary_target(targets: Sequence[str], profile: DepMapProfile) -> str | None:
    """The curated target with the strongest genetic dependency in this context."""

    scored = [(profile.effect(gene), gene) for gene in targets if profile.effect(gene) is not None]
    if not scored:
        return None
    return sorted(scored, key=lambda item: (item[0], item[1]))[0][1]


def screen_k562(
    *,
    asset: EngagementAsset,
    annotation: Mapping[str, Mapping[str, object]],
    gdsc: Sequence[Gdsc2Record],
    profile: DepMapProfile,
    require_selective_dependency: bool,
) -> tuple[Candidate, ...]:
    """Classify every engagement-release compound against the K562 premise records."""

    thresholds = ARCHETYPE_THRESHOLDS
    candidates: list[Candidate] = []
    by_target: dict[str, list[str]] = {}
    for name, entry in annotation.items():
        for gene in entry["targets"]:  # type: ignore[index]
            by_target.setdefault(gene, []).append(name)
    for name in sorted(annotation, key=normalise_compound):
        entry = annotation[name]
        targets = tuple(entry["targets"])  # type: ignore[arg-type]
        phenotype = _gdsc_phenotype(gdsc, name)
        primary = _primary_target(targets, profile)
        effect = profile.effect(primary) if primary else None
        fraction = profile.dependent_fraction.get(primary) if primary else None
        abundance = profile.abundance(primary) if primary else None
        covered = bool(primary) and bool(asset.covers(name)) and bool(asset.quantified(primary or ""))
        comparator = None
        comparator_covered = False
        if primary:
            others = [
                other
                for other in sorted(by_target.get(primary, ()), key=normalise_compound)
                if normalise_compound(other) != normalise_compound(name)
                and _gdsc_phenotype(gdsc, other) is not None
            ]
            preferred = [other for other in others if asset.covers(other)]
            comparator = (preferred or others)[0] if (preferred or others) else None
            comparator_covered = bool(comparator) and bool(asset.covers(comparator or ""))
        exclusion: str | None = None
        archetype: EngagementArchetype | None = None
        if not entry["in_cells"]:
            exclusion = "compound_not_assayed_in_cells_by_the_engagement_release"
        elif not asset.covers(name):
            exclusion = "compound_absent_from_the_engagement_matrix"
        elif phenotype is None:
            exclusion = "no_phenotype_record_in_this_context"
        elif primary is None:
            exclusion = "curated_targets_unscored_in_depmap"
        elif effect is None or abundance is None or fraction is None:
            exclusion = "primary_target_premise_incomplete"
        else:
            strong = effect <= thresholds["strong_dependency"]
            selective = fraction <= thresholds["selective_gene_fraction"]
            expressed = abundance >= thresholds["expressed_log2_tpm1"]
            unexpressed = abundance < thresholds["unexpressed_log2_tpm1"]
            absent_everywhere = all(
                (profile.effect(gene) is None or profile.effect(gene) > thresholds["absent_dependency"])
                for gene in targets
            )
            active = phenotype.is_active
            if strong and (selective or not require_selective_dependency) and not active and expressed:
                archetype = (
                    EngagementArchetype.ENGAGEMENT_GAP_OR_MODE
                    if covered
                    else EngagementArchetype.NO_ENGAGEMENT_COVERAGE
                )
            elif active and absent_everywhere and unexpressed:
                archetype = EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND
            elif strong and selective and active and expressed:
                archetype = EngagementArchetype.CONCORDANT_SUPPORT
            else:
                exclusion = (
                    "premise_matches_no_registered_archetype:"
                    f"strong={strong},selective={selective},active={active},"
                    f"expressed={expressed},unexpressed={unexpressed},absent_everywhere={absent_everywhere}"
                )
        candidates.append(
            Candidate(
                context_identifier=K562_CONTEXT,
                model_id=K562_MODEL,
                cell_line="K562",
                compound=name,
                curated_targets=targets,
                primary_target=primary,
                gene_effect=effect,
                dependent_fraction=fraction,
                abundance=abundance,
                phenotype=phenotype,
                engagement_covered=covered,
                comparator=comparator,
                comparator_engagement_covered=comparator_covered,
                archetype=archetype,
                exclusion=exclusion,
            )
        )
    return tuple(candidates)


def screen_mcf7(
    *,
    rows: Sequence[Mapping[str, str]],
    profile: DepMapProfile,
    require_selective_dependency: bool,
) -> tuple[Candidate, ...]:
    """Classify PRISM MCF7 curves as the second context, where no engagement asset applies."""

    thresholds = ARCHETYPE_THRESHOLDS
    candidates: list[Candidate] = []
    for row in sorted(rows, key=lambda item: normalise_compound(str(item.get("name")))):
        name = (row.get("name") or "").strip()
        gene = (row.get("target") or "").strip()
        phenotype = _prism_phenotype(row)
        effect = profile.effect(gene)
        fraction = profile.dependent_fraction.get(gene)
        abundance = profile.abundance(gene)
        exclusion: str | None = None
        archetype: EngagementArchetype | None = None
        if phenotype is None:
            exclusion = "phenotype_record_incomplete"
        elif phenotype.fit_quality < thresholds["minimum_curve_r2"]:
            exclusion = "phenotype_curve_below_the_declared_minimum_fit"
        elif effect is None or abundance is None or fraction is None:
            exclusion = "primary_target_premise_incomplete"
        else:
            strong = effect <= thresholds["strong_dependency"]
            selective = fraction <= thresholds["selective_gene_fraction"]
            expressed = abundance >= thresholds["expressed_log2_tpm1"]
            if strong and (selective or not require_selective_dependency) and not phenotype.is_active and expressed:
                archetype = EngagementArchetype.ENGAGEMENT_CAPABILITY_OUT_OF_CONTEXT
            else:
                exclusion = (
                    "premise_matches_no_registered_archetype:"
                    f"strong={strong},selective={selective},active={phenotype.is_active},expressed={expressed}"
                )
        candidates.append(
            Candidate(
                context_identifier=MCF7_CONTEXT,
                model_id=MCF7_MODEL,
                cell_line="MCF7",
                compound=name,
                curated_targets=(gene,) if gene else (),
                primary_target=gene or None,
                gene_effect=effect,
                dependent_fraction=fraction,
                abundance=abundance,
                phenotype=phenotype,
                engagement_covered=False,
                comparator=None,
                comparator_engagement_covered=False,
                archetype=archetype,
                exclusion=exclusion,
            )
        )
    return tuple(candidates)


def select(
    candidates: Sequence[Candidate], *, per_archetype: int = 4, per_target: int = 1
) -> tuple[Candidate, ...]:
    """Take a deterministic sample: alphabetical by folded compound, capped per target."""

    selected: list[Candidate] = []
    for archetype in EngagementArchetype:
        pool = [item for item in candidates if item.archetype is archetype]
        taken: list[Candidate] = []
        counts: dict[str, int] = {}
        for item in sorted(pool, key=lambda entry: normalise_compound(entry.compound)):
            key = f"{item.primary_target}"
            if counts.get(key, 0) >= per_target:
                continue
            counts[key] = counts.get(key, 0) + 1
            taken.append(item)
            if len(taken) >= per_archetype:
                break
        selected.extend(taken)
    return tuple(selected)
