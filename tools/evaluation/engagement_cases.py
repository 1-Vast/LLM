"""Evaluation engagement cases: consolidated module responsibilities."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence
from tools.evaluation.capabilities import CAPABILITY_SCHEMA, canonical_repair_identifier  # noqa: E402
from tools.evaluation.construction import ARCHETYPE_THRESHOLDS, assign_split  # noqa: E402
from tools.evaluation.engagement_sources import (  # noqa: E402
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
    Workbook,
    sheet_digest,
)
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


RETRIEVAL_PRICE = {"basis": "record_retrieval", "wells": 0, "turnaround_days": 0.0}
OVERLAP_UNITS = "engaged_genes_intersected_with_context_dependencies"
LYSATE_UNITS = "apparent_kd_nanomolar"

# Which development action each possible outcome of the always-hidden binding test bears on.
# Declared before any value was read; the limitation that lysate binding does not establish
# engagement in cells is carried on every record.
FINAL_TEST_MAP: Mapping[str, Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]]] = {
    EngagementArchetype.ENGAGEMENT_GAP_OR_MODE.value: {
        "listed_as_kinobeads_target": (("change_intervention_mode",), ()),
        "not_listed_as_kinobeads_target": (("revise_intervention",), ("change_intervention_mode",)),
    },
    EngagementArchetype.NO_ENGAGEMENT_COVERAGE.value: {
        "listed_as_kinobeads_target": (("change_intervention_mode",), ()),
        "not_listed_as_kinobeads_target": (("revise_intervention",), ("change_intervention_mode",)),
    },
    EngagementArchetype.ENGAGEMENT_CAPABILITY_OUT_OF_CONTEXT.value: {
        "listed_as_kinobeads_target": (("change_intervention_mode",), ()),
        "not_listed_as_kinobeads_target": (("revise_intervention",), ("change_intervention_mode",)),
    },
    EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND.value: {
        "listed_as_kinobeads_target": ((), ()),
        "not_listed_as_kinobeads_target": (("revise_attribution",), ()),
    },
    EngagementArchetype.CONCORDANT_SUPPORT.value: {
        "listed_as_kinobeads_target": (("continue",), ()),
        "not_listed_as_kinobeads_target": (("revise_attribution",), ("continue",)),
    },
}


def _slug(value: str) -> str:
    keep = [character if character.isalnum() else "-" for character in value.lower()]
    return "".join(keep).strip("-").replace("--", "-")[:28]


def case_identifier(candidate: Candidate) -> str:
    return (
        f"eng-{_slug(candidate.primary_target or 'unknown')}-{_slug(candidate.compound)}-"
        f"{candidate.model_id.replace('ACH-', 'ach')}"
    )


def index_repair_identifier(candidate: Candidate) -> str:
    return canonical_repair_identifier(INDEX_CAPABILITY, candidate.compound, candidate.primary_target or "")


def comparator_repair_identifier(candidate: Candidate) -> str | None:
    if not candidate.comparator:
        return None
    return canonical_repair_identifier(COMPARATOR_CAPABILITY, candidate.comparator, candidate.primary_target or "")


def overlap_repair_identifier(candidate: Candidate) -> str:
    return canonical_repair_identifier(OVERLAP_CAPABILITY, candidate.compound, "proteome")


def _subject(gene: str, compound: str) -> str:
    return f"{gene}@{normalise_compound(compound)}"


def _hypotheses(candidate: Candidate) -> list[dict[str, str]]:
    first, second = PAIRS[candidate.archetype]
    gene = candidate.primary_target or "the annotated target"
    compound = candidate.compound
    line = candidate.cell_line
    descriptions = {
        INSUFFICIENT: (
            f"{compound} does not achieve sufficient functional perturbation of {gene} in {line} at the "
            "screened exposure, so the absent phenotype reflects the intervention, not the target."
        ),
        MODE_NON_EQUIVALENCE: (
            f"Genetic removal of {gene} and pharmacological inhibition by {compound} are not functionally "
            f"equivalent in {line}, so the absent phenotype reflects the intervention mode."
        ),
        TARGET_MEDIATED: (
            f"The viability phenotype of {compound} in {line} is mediated by its annotated target {gene} "
            "in this context."
        ),
        ATTRIBUTION_ERROR: (
            f"The observed phenotype in {line} is not attributable to {gene} in this context, so the "
            "target-programme interpretation of the existing records is unsupported."
        ),
    }
    return [
        {
            "identifier": identifier,
            "description": descriptions[identifier],
            "development_action": DEVELOPMENT_ACTIONS[identifier],
            "causal_factor": CAUSAL_FACTORS[identifier],
        }
        for identifier in (first, second)
    ]


def _initial_evidence(candidate: Candidate, *, annotation_source: str) -> list[dict[str, Any]]:
    gene = candidate.primary_target or ""
    phenotype = candidate.phenotype
    assert phenotype is not None
    return [
        {
            "identifier": "crispr-gene-effect",
            "statement": (
                f"DepMap 24Q2 reports a CRISPR gene-effect score of {candidate.gene_effect:.4f} for {gene} "
                f"in {candidate.model_id} ({candidate.cell_line}); {candidate.dependent_fraction * 100:.1f} "
                "percent of screened models score this gene at or below a gene effect of -0.5."
            ),
            "source_id": f"DepMap-24Q2:CRISPRGeneEffect.csv:{candidate.model_id}:{gene}",
            "conditions": {
                "model_id": candidate.model_id,
                "context_identifier": candidate.context_identifier,
                "gene": gene,
                "assay": "processed CRISPR gene-effect score",
            },
            "evidence_kind": "retrieved_source",
            "limitations": [
                "A processed cross-study dependency score is not a condition-matched target-engagement measurement.",
                "The CRISPR perturbation removes the protein over days; it is not dose-matched or time-matched to a compound exposure.",
            ],
        },
        {
            "identifier": "phenotype-curve",
            "statement": phenotype.statement,
            "source_id": phenotype.source_id,
            "conditions": dict(phenotype.conditions, context_identifier=candidate.context_identifier, gene=gene),
            "evidence_kind": "derived_analysis",
            "limitations": [
                "A fitted screening curve is one retrospective record, not an independently designed biological replicate set.",
                "The screen measures pooled viability; it measures neither target engagement nor pathway activity.",
                "A fitted concentration outside the screened range is an extrapolation of the fit, which is why activity is read against the release's own maximum screened concentration.",
            ],
        },
        {
            "identifier": "curated-target-annotation",
            "statement": (
                f"The engagement release curates {', '.join(candidate.curated_targets)} as the annotated "
                f"target set of {candidate.compound}."
            ),
            "source_id": annotation_source,
            "conditions": {"compound": candidate.compound, "assay": "release target annotation"},
            "evidence_kind": "retrieved_source",
            "limitations": [
                "A curated target annotation is release metadata, not a measurement in this context.",
                "An annotated target set does not establish which of its members carries a phenotype here.",
            ],
        },
    ]


def _abundance_outcomes(candidate: Candidate) -> dict[str, str]:
    first, second = PAIRS[candidate.archetype]
    if candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND:
        return {TARGET_MEDIATED: "target_expressed", ATTRIBUTION_ERROR: "target_not_expressed"}
    return {first: "target_expressed", second: "target_expressed"}


def _selectivity_label(candidate: Candidate) -> str:
    fraction = candidate.dependent_fraction or 0.0
    if fraction >= ARCHETYPE_THRESHOLDS["pan_essential_gene_fraction"]:
        return "dependency_pan_essential"
    if fraction <= ARCHETYPE_THRESHOLDS["selective_gene_fraction"]:
        return "dependency_selective"
    return "dependency_intermediate"


def _selectivity_outcomes(candidate: Candidate) -> dict[str, str]:
    first, second = PAIRS[candidate.archetype]
    if candidate.archetype is EngagementArchetype.CONCORDANT_SUPPORT:
        return {TARGET_MEDIATED: "dependency_selective", ATTRIBUTION_ERROR: "dependency_pan_essential"}
    label = _selectivity_label(candidate)
    return {first: label, second: label}


def _engagement_outcomes(candidate: Candidate) -> dict[str, str]:
    """What an engagement record of the index compound is declared to show per hypothesis."""

    first, second = PAIRS[candidate.archetype]
    if first == INSUFFICIENT:
        return {INSUFFICIENT: "not_engaged", MODE_NON_EQUIVALENCE: "engaged"}
    return {TARGET_MEDIATED: "engaged", ATTRIBUTION_ERROR: "not_engaged"}


def _menu_actions(candidate: Candidate) -> list[dict[str, Any]]:
    gene = candidate.primary_target or ""
    pair = list(PAIRS[candidate.archetype])
    actions: list[dict[str, Any]] = [
        {
            "identifier": "target_abundance_rna",
            "description": (
                f"Retrieve the DepMap 24Q2 RNA abundance (log2(TPM+1)) of {gene} in {candidate.model_id}, "
                "establishing whether the annotated target is present in this context."
            ),
            "cost": ACTION_COST,
            "distinguishes": pair,
            "kind": "rna_abundance_measurement",
            "quantity": "rna_abundance",
            "entity": gene,
            "units": "log2_tpm_plus_1",
            "supplies": [ABUNDANCE_PREMISE],
            "readout": "rna_abundance_log2_tpm1",
            "expected_conditions": {"model_id": candidate.model_id, "gene": gene},
            "expected_outcomes": _abundance_outcomes(candidate),
            "lab_cost": dict(RETRIEVAL_PRICE, source="DepMap 24Q2 released record"),
            "prediction_value": 0.4,
        },
        {
            "identifier": "dependency_selectivity_profile",
            "description": (
                f"Compute the fraction of DepMap 24Q2 models scoring {gene} as a dependency, establishing "
                "whether the genetic phenotype is selective or panel-wide."
            ),
            "cost": ACTION_COST,
            "distinguishes": pair,
            "kind": "evidence_review",
            "quantity": "selectivity",
            "entity": gene,
            "units": "dependent_model_fraction",
            "supplies": [SELECTIVITY_PREMISE],
            "readout": "dependent_model_fraction",
            "context_bound": False,
            "expected_conditions": {"gene": gene},
            "expected_outcomes": _selectivity_outcomes(candidate),
            "lab_cost": dict(RETRIEVAL_PRICE, source="DepMap 24Q2 panel summary"),
            "prediction_value": 0.3,
        },
    ]
    if candidate.comparator and candidate.archetype in (
        EngagementArchetype.ENGAGEMENT_GAP_OR_MODE,
        EngagementArchetype.NO_ENGAGEMENT_COVERAGE,
    ):
        actions.append(
            {
                "identifier": "mode_matched_comparator",
                "description": (
                    f"Retrieve the fitted response of {candidate.comparator}, a second compound annotated to "
                    f"{gene}, in {candidate.cell_line}. Its reading depends on whether that compound engages "
                    "the target in this context."
                ),
                "cost": ACTION_COST,
                "distinguishes": pair,
                "kind": "mode_matched_comparator",
                "quantity": "viability",
                "entity": "cell_population",
                "units": "fitted_ic50_against_the_screened_range",
                "supplies": ["functional:mode_comparator"],
                "prerequisites": [ABUNDANCE_PREMISE],
                "interpretation_gate": COMPARATOR_ENGAGEMENT_PREMISE,
                "readout": "viability_curve",
                "expected_conditions": {
                    "gene": gene,
                    # The folded identity, because the phenotype release and the engagement
                    # release spell the same compound differently and the executor compares a
                    # planned condition against the record's condition. The model is not
                    # repeated as a condition: the phenotype release names it
                    # `sanger_model_id`, and the case's context is already checked separately.
                    "compound": normalise_compound(candidate.comparator),
                },
                "expected_outcomes": {INSUFFICIENT: "comparator_active", MODE_NON_EQUIVALENCE: "comparator_inactive"},
                "lab_cost": dict(RETRIEVAL_PRICE, source="released fitted curve"),
                "prediction_value": 0.7,
            }
        )
    actions.append(
        {
            "identifier": "matched_target_engagement",
            "description": (
                f"Measure condition-matched engagement and residual activity of {gene} under the exact "
                f"{candidate.compound} exposure used in the phenotype screen. Not available in this "
                "retrospective package."
            ),
            "cost": UNAVAILABLE_ENGAGEMENT_COST,
            "distinguishes": pair,
            "kind": "functional_measurement",
            "quantity": "engagement_shift",
            "entity": _subject(gene, candidate.compound),
            "units": ENGAGEMENT_UNITS,
            "supplies": [INDEX_ENGAGEMENT_PREMISE],
            "available": False,
            "expected_outcomes": _engagement_outcomes(candidate),
            "lab_cost": {
                "basis": "new_measurement",
                "wells": UNAVAILABLE_ENGAGEMENT_WELLS,
                "turnaround_days": UNAVAILABLE_ENGAGEMENT_DAYS,
                "source": "report section 36 illustrative condition-matched engagement assay",
            },
            "prediction_value": 0.0,
        }
    )
    return sorted(actions, key=lambda item: item["identifier"])


def _premise_registry(candidate: Candidate) -> dict[str, Any]:
    gene = candidate.primary_target or ""
    registry: dict[str, Any] = {
        ABUNDANCE_PREMISE: {
            "quantity": "rna_abundance",
            "entity": gene,
            "units": "log2_tpm_plus_1",
            "context_identifier": candidate.context_identifier,
            "require_direct_measurement": True,
            "note": (
                "Bulk RNA abundance in this model. It does not establish protein presence, isoform usage, "
                "or residual catalytic activity."
            ),
        },
        SELECTIVITY_PREMISE: {
            "quantity": "selectivity",
            "entity": gene,
            "units": "dependent_model_fraction",
            "require_direct_measurement": False,
            "note": "A panel summary over released scores, not a measurement in this context.",
        },
        INDEX_ENGAGEMENT_PREMISE: {
            "quantity": "engagement_shift",
            "entity": _subject(gene, candidate.compound),
            "units": ENGAGEMENT_UNITS,
            "context_identifier": candidate.context_identifier,
            "require_direct_measurement": True,
            "note": (
                "A vehicle-referenced stability shift for this gene under this compound in this context. "
                "It is an engagement effect size, not an occupancy fraction, and no menu action supplies it."
            ),
        },
    }
    if candidate.comparator and candidate.archetype in (
        EngagementArchetype.ENGAGEMENT_GAP_OR_MODE,
        EngagementArchetype.NO_ENGAGEMENT_COVERAGE,
    ):
        registry[COMPARATOR_ENGAGEMENT_PREMISE] = {
            "quantity": "engagement_shift",
            "entity": _subject(gene, candidate.comparator),
            "units": ENGAGEMENT_UNITS,
            "context_identifier": candidate.context_identifier,
            "require_direct_measurement": True,
            "note": (
                "Whether the comparator compound engages the same target here. Without it the comparator's "
                "viability curve cannot separate a realisation failure from mode non-equivalence."
            ),
        }
    if candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND:
        registry[OVERLAP_PREMISE] = {
            "quantity": "engagement_shift",
            "units": OVERLAP_UNITS,
            "context_identifier": candidate.context_identifier,
            "require_direct_measurement": False,
            "note": (
                "Which proteins this compound engages here that are themselves dependencies in this context. "
                "It is a derived intersection of two releases, declared as an estimate."
            ),
        }
    return registry


def _repair_outcome_templates(candidate: Candidate) -> dict[str, Any]:
    first, second = PAIRS[candidate.archetype]
    templates: dict[str, Any] = {INDEX_ENGAGEMENT_PREMISE: _engagement_outcomes(candidate)}
    if COMPARATOR_ENGAGEMENT_PREMISE in _premise_registry(candidate):
        # The comparator's own engagement is a gate, not a discriminator: neither explanation
        # of the index compound predicts it, so the same label is declared under both and the
        # deterministic interpretation rule passes over it.
        templates[COMPARATOR_ENGAGEMENT_PREMISE] = {first: "engaged", second: "engaged"}
    if candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND:
        templates[OVERLAP_PREMISE] = {
            TARGET_MEDIATED: "no_engaged_dependency",
            ATTRIBUTION_ERROR: "engaged_dependency_found",
        }
    return templates


def _menu_results(candidate: Candidate, *, comparator_phenotype) -> list[dict[str, Any]]:
    gene = candidate.primary_target or ""
    expressed = (candidate.abundance or 0.0) >= ARCHETYPE_THRESHOLDS["unexpressed_log2_tpm1"]
    abundance_state = "expressed" if expressed else "not_expressed"
    selectivity_label = _selectivity_label(candidate)
    results: list[dict[str, Any]] = [
        {
            "action_identifier": "target_abundance_rna",
            "outcome": "target_expressed" if expressed else "target_not_expressed",
            "statement": (
                f"DepMap 24Q2 reports {gene} RNA abundance of {candidate.abundance:.4f} log2(TPM+1) in "
                f"{candidate.model_id}."
            ),
            "source_id": f"DepMap-24Q2:OmicsExpressionProteinCodingGenesTPMLogp1.csv:{candidate.model_id}:{gene}",
            "context_identifier": candidate.context_identifier,
            "conditions": {"model_id": candidate.model_id, "gene": gene, "assay": "bulk RNA abundance, log2(TPM+1)"},
            "metrics": {"log2_tpm1": f"{candidate.abundance:.6f}"},
            "record_count": 1,
            "independent_units": 1,
            "record_validated": True,
            "biological_quality": "passed",
            "evidence_kind": "real_measurement",
            "interpretation_fields": [ABUNDANCE_PREMISE, f"{ABUNDANCE_PREMISE}:{abundance_state}"],
            "limitations": [
                "RNA abundance is not protein abundance, and neither is target activity or engagement.",
                "The measurement comes from the untreated model profile, not from the treated screen condition.",
            ],
        },
        {
            "action_identifier": "dependency_selectivity_profile",
            "outcome": selectivity_label,
            "statement": (
                f"Across DepMap 24Q2 models, {(candidate.dependent_fraction or 0.0) * 100:.1f} percent score "
                f"{gene} at or below a gene effect of -0.5, which classifies the genetic phenotype as "
                f"{selectivity_label.replace('dependency_', '').replace('_', ' ')}."
            ),
            "source_id": f"DepMap-24Q2:CRISPRGeneEffect.csv:panel-summary:{gene}",
            "context_identifier": None,
            "conditions": {"gene": gene, "assay": "panel summary over processed gene-effect scores"},
            "metrics": {"dependent_model_fraction": f"{(candidate.dependent_fraction or 0.0):.6f}"},
            "record_count": 1,
            "record_validated": True,
            "biological_quality": "unknown",
            "evidence_kind": "derived_analysis",
            "interpretation_fields": [
                SELECTIVITY_PREMISE,
                f"{SELECTIVITY_PREMISE}:{selectivity_label.replace('dependency_', '')}",
            ],
            "limitations": [
                "This is a derived summary over already-processed scores, not a new measurement, and it cannot satisfy a biological premise.",
                "A panel-wide dependency does not establish that a compound's absent phenotype has the same cause.",
                "The threshold is a declared construction setting, not a validated biological cut-off.",
            ],
        },
    ]
    if comparator_phenotype is not None:
        active = comparator_phenotype.is_active
        results.append(
            {
                "action_identifier": "mode_matched_comparator",
                "outcome": "comparator_active" if active else "comparator_inactive",
                "statement": comparator_phenotype.statement,
                "source_id": comparator_phenotype.source_id,
                "context_identifier": candidate.context_identifier,
                "conditions": dict(
                    comparator_phenotype.conditions,
                    gene=gene,
                    compound=normalise_compound(comparator_phenotype.compound),
                    compound_as_released=comparator_phenotype.compound,
                ),
                "metrics": {
                    "ic50_micromolar": (
                        "unreported"
                        if comparator_phenotype.ic50_micromolar is None
                        else f"{comparator_phenotype.ic50_micromolar:.6f}"
                    ),
                    "auc": f"{comparator_phenotype.auc:.6f}",
                    "maximum_screened_concentration_micromolar": f"{comparator_phenotype.maximum_dose_micromolar}",
                },
                "record_count": 1,
                "independent_units": 1,
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
                "interpretation_fields": [
                    "functional:mode_comparator",
                    f"functional:mode_comparator:{'active' if active else 'inactive'}",
                ],
                "limitations": [
                    "The comparator shares an annotated target, not a measured intracellular exposure or residual activity.",
                    "Two compounds inactive in one screen do not establish that the target cannot be inhibited in this model.",
                    "The comparison is between fitted screening curves, not between matched engagement measurements.",
                ],
            }
        )
    return sorted(results, key=lambda item: item["action_identifier"])


def _engagement_record(
    *,
    action_identifier: str,
    candidate: Candidate,
    compound: str,
    gene: str,
    asset: EngagementAsset,
    premise: str,
    gate_requires_engagement: bool,
) -> dict[str, Any] | None:
    """One hidden engagement record, or None where the release quantifies nothing.

    A negative call still supplies the index premise: the measurement happened and its result
    is evidence. A negative call does **not** supply a comparator gate, because what makes the
    comparator's curve interpretable is that the comparator did engage.
    """

    call = asset.call(compound, gene)
    if call is None:
        return None
    state = "engaged" if call.engaged else "not_engaged"
    fields = [f"{premise}:{state}"]
    if call.engaged or not gate_requires_engagement:
        fields.insert(0, premise)
    return {
        "action_identifier": action_identifier,
        "outcome": state,
        "statement": (
            f"The living-cell engagement release reports a vehicle-referenced stability shift of "
            f"{call.effect_log2:+.4f} log2 for {gene} ({call.protein_identifier}) under {call.compound} in "
            f"{candidate.cell_line}, rank {call.rank_by_absolute_effect} of {call.proteins_quantified} "
            f"quantified proteins, against a measured vehicle-null threshold of "
            f"{asset.null.threshold:.4f} (held-out false-positive rate "
            f"{asset.null.holdout_rate:.5f}, one-sided 95 percent upper bound "
            f"{asset.null.holdout_rate_upper_95:.5f}). The call is '{state}'."
        ),
        "source_id": f"PISA-eLife-2024:{asset.sha256[:12]}:{asset.sheet}:{call.compound}:{call.protein_identifier}",
        "context_identifier": candidate.context_identifier,
        "conditions": {
            "compound": normalise_compound(call.compound),
            "compound_as_released": call.compound,
            "gene": gene,
            "context_identifier": candidate.context_identifier,
            "assay": "proteome-wide thermal-stability shift in living cells",
            "exposure": "undeclared_in_local_asset",
        },
        "metrics": {
            "effect_log2": f"{call.effect_log2:.6f}",
            "replicates": ", ".join(f"{value:.6f}" for value in call.replicates),
            "null_threshold_log2": f"{asset.null.threshold:.6f}",
            "rank_by_absolute_effect": str(call.rank_by_absolute_effect),
            "proteins_quantified": str(call.proteins_quantified),
        },
        "record_count": 1,
        "independent_units": len(call.replicates),
        "record_validated": True,
        "biological_quality": "passed",
        "evidence_kind": "real_measurement",
        "interpretation_fields": fields,
        "limitations": [
            "A stability shift is an engagement effect size, not an occupancy fraction.",
            "The exposure concentration and duration are undeclared in the local asset, so this record is not condition-matched to the viability screen.",
            "The two replicate channels are two channels of one experiment, not two independent experiments.",
            f"The call rests on a measured vehicle-null threshold whose held-out false-positive rate is bounded at {asset.null.holdout_rate_upper_95:.5f}.",
        ],
    }


def _overlap_record(
    *, action_identifier: str, candidate: Candidate, asset: EngagementAsset, profile: DepMapProfile
) -> dict[str, Any] | None:
    """Engaged proteins that are themselves dependencies here, excluding the curated targets."""

    if not asset.covers(candidate.compound):
        return None
    strong = ARCHETYPE_THRESHOLDS["strong_dependency"]
    curated = set(candidate.curated_targets)
    found: list[tuple[str, float, float, int]] = []
    for gene, effect, rank in asset.engaged_genes(candidate.compound):
        if gene in curated:
            continue
        dependency = profile.effect(gene)
        if dependency is not None and dependency <= strong:
            found.append((gene, effect, dependency, rank))
    state = "engaged_dependency_found" if found else "no_engaged_dependency"
    named = ", ".join(
        f"{gene} (shift {effect:+.3f}, rank {rank}, gene effect {dependency:.3f})"
        for gene, effect, dependency, rank in found[:5]
    )
    return {
        "action_identifier": action_identifier,
        "outcome": state,
        "statement": (
            f"Intersecting the engaged proteins of {candidate.compound} in {candidate.cell_line} with the "
            f"genes this context depends on at or below {strong} gene effect, excluding its curated "
            f"targets, returns {len(found)} protein(s)"
            + (f": {named}." if found else ".")
        ),
        "source_id": (
            f"derived:PISA-eLife-2024:{asset.sha256[:12]}+DepMap-24Q2:CRISPRGeneEffect.csv:"
            f"{candidate.model_id}:{candidate.compound}"
        ),
        "context_identifier": candidate.context_identifier,
        "conditions": {
            "compound": normalise_compound(candidate.compound),
            "compound_as_released": candidate.compound,
            "context_identifier": candidate.context_identifier,
            "assay": "derived intersection of engaged proteins with context dependencies",
        },
        "metrics": {
            "engaged_dependencies": str(len(found)),
            "null_threshold_log2": f"{asset.null.threshold:.6f}",
            "dependency_threshold": f"{strong}",
        },
        "record_count": 1,
        "record_validated": True,
        "biological_quality": "unknown",
        "evidence_kind": "derived_analysis",
        "interpretation_fields": [OVERLAP_PREMISE, f"{OVERLAP_PREMISE}:{state}"],
        "limitations": [
            "This is a derived intersection of two releases, not a new measurement, and it is declared as an estimate.",
            "An engaged dependency is a candidate alternative explanation, not an established one: nothing here shows the phenotype runs through it.",
            "Proteins the release did not quantify cannot appear, so the absence of an alternative is bounded by coverage.",
        ],
    }


def _repair_results(
    candidate: Candidate,
    *,
    asset: EngagementAsset,
    profile: DepMapProfile,
    comparator_covered: bool,
) -> list[dict[str, Any]]:
    """Every hidden record a compiled repair could reveal for this case."""

    gene = candidate.primary_target or ""
    records: list[dict[str, Any]] = []
    if candidate.engagement_covered:
        index = _engagement_record(
            action_identifier=index_repair_identifier(candidate),
            candidate=candidate,
            compound=candidate.compound,
            gene=gene,
            asset=asset,
            premise=INDEX_ENGAGEMENT_PREMISE,
            gate_requires_engagement=False,
        )
        if index is not None:
            records.append(index)
    comparator_id = comparator_repair_identifier(candidate)
    if comparator_id and comparator_covered and candidate.comparator:
        comparator = _engagement_record(
            action_identifier=comparator_id,
            candidate=candidate,
            compound=candidate.comparator,
            gene=gene,
            asset=asset,
            premise=COMPARATOR_ENGAGEMENT_PREMISE,
            gate_requires_engagement=True,
        )
        if comparator is not None:
            records.append(comparator)
    if candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND:
        overlap = _overlap_record(
            action_identifier=overlap_repair_identifier(candidate),
            candidate=candidate,
            asset=asset,
            profile=profile,
        )
        if overlap is not None:
            records.append(overlap)
    return sorted(records, key=lambda item: item["action_identifier"])


def _licensing_rules(candidate: Candidate, *, comparator_covered: bool) -> list[dict[str, Any]]:
    """Which decision each possible outcome of each route licenses, enumerated in advance."""

    index_id = index_repair_identifier(candidate)
    comparator_id = comparator_repair_identifier(candidate)
    rules: list[dict[str, Any]] = []
    if candidate.archetype in (
        EngagementArchetype.ENGAGEMENT_GAP_OR_MODE,
        EngagementArchetype.NO_ENGAGEMENT_COVERAGE,
    ):
        if candidate.engagement_covered:
            rules.extend(
                [
                    {
                        "decision": "revise_intervention",
                        "required_outcomes": {index_id: "not_engaged"},
                        "required_interpretation_fields": [f"{INDEX_ENGAGEMENT_PREMISE}:not_engaged"],
                        "require_biological_quality": True,
                        "note": (
                            "The compound does not move the target's stability in this context, so the "
                            "absent phenotype is an intervention-realisation failure rather than a mode "
                            "difference."
                        ),
                    },
                    {
                        "decision": "change_intervention_mode",
                        "required_outcomes": {index_id: "engaged"},
                        "required_interpretation_fields": [f"{INDEX_ENGAGEMENT_PREMISE}:engaged"],
                        "require_biological_quality": True,
                        "note": (
                            "The compound engages the target here and the phenotype is still absent while "
                            "the gene is a dependency, which supports reconsidering the intervention mode."
                        ),
                    },
                    {
                        "decision": "defer",
                        "required_outcomes": {index_id: "engaged"},
                        "require_biological_quality": True,
                        "note": (
                            "Informed deferral is equally licensed: the engagement record is not "
                            "condition-matched to the viability screen, so mode non-equivalence is "
                            "supported but not isolated. Deferral before acquiring engagement is not licensed."
                        ),
                    },
                ]
            )
        if comparator_id and comparator_covered:
            rules.extend(
                [
                    {
                        "decision": "revise_intervention",
                        "required_outcomes": {
                            comparator_id: "engaged",
                            "mode_matched_comparator": "comparator_active",
                            "target_abundance_rna": "target_expressed",
                        },
                        "required_interpretation_fields": [
                            f"{COMPARATOR_ENGAGEMENT_PREMISE}:engaged",
                            "functional:mode_comparator:active",
                            f"{ABUNDANCE_PREMISE}:expressed",
                        ],
                        "require_biological_quality": True,
                        "note": (
                            "A second compound engages the same target here and does produce the phenotype, "
                            "so the index compound's realisation is the failing element."
                        ),
                    },
                    {
                        "decision": "change_intervention_mode",
                        "required_outcomes": {
                            comparator_id: "engaged",
                            "mode_matched_comparator": "comparator_inactive",
                            "target_abundance_rna": "target_expressed",
                        },
                        "required_interpretation_fields": [
                            f"{COMPARATOR_ENGAGEMENT_PREMISE}:engaged",
                            "functional:mode_comparator:inactive",
                            f"{ABUNDANCE_PREMISE}:expressed",
                        ],
                        "require_biological_quality": True,
                        "note": (
                            "A second compound engages the target here and still produces no phenotype, "
                            "while removal of the gene does, which supports reconsidering the mode."
                        ),
                    },
                ]
            )
        if not rules:
            rules.append(
                {
                    "decision": "defer",
                    "required_outcomes": {},
                    "note": (
                        "No registered capability covers the engagement premise for this pair, and no menu "
                        "action separates the two explanations, so preserving the unknown is the licensed answer."
                    ),
                }
            )
    elif candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND:
        overlap_id = overlap_repair_identifier(candidate)
        rules.extend(
            [
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {"target_abundance_rna": "target_not_expressed"},
                    "required_interpretation_fields": [f"{ABUNDANCE_PREMISE}:not_expressed"],
                    "require_biological_quality": True,
                    "note": "A compound cannot act through a target the context does not express.",
                },
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {index_id: "not_engaged"},
                    "required_interpretation_fields": [f"{INDEX_ENGAGEMENT_PREMISE}:not_engaged"],
                    "require_biological_quality": True,
                    "note": "The compound does not engage its annotated target here, so the target-programme reading is unsupported.",
                },
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {overlap_id: "engaged_dependency_found"},
                    "required_interpretation_fields": [f"{OVERLAP_PREMISE}:engaged_dependency_found"],
                    "note": "An engaged protein that this context depends on is a supported alternative explanation of the phenotype.",
                },
                {
                    "decision": "defer",
                    "required_outcomes": {index_id: "engaged", overlap_id: "no_engaged_dependency"},
                    "note": (
                        "The compound engages its annotated target, that target is not a dependency here, and "
                        "no engaged alternative dependency was found: the phenotype is unexplained inside this package."
                    ),
                },
            ]
        )
    elif candidate.archetype is EngagementArchetype.CONCORDANT_SUPPORT:
        rules.extend(
            [
                {
                    "decision": "continue",
                    "required_outcomes": {},
                    "note": (
                        "A strong selective genetic dependency and an active fitted response for a compound "
                        "annotated to that target are concordant in this context; the premise licenses the "
                        "programme action without further acquisition."
                    ),
                },
                {
                    "decision": "continue",
                    "required_outcomes": {index_id: "engaged"},
                    "require_biological_quality": True,
                    "note": "Measured engagement of the annotated target confirms the concordant reading.",
                },
                {
                    "decision": "revise_attribution",
                    "required_outcomes": {index_id: "not_engaged"},
                    "required_interpretation_fields": [f"{INDEX_ENGAGEMENT_PREMISE}:not_engaged"],
                    "require_biological_quality": True,
                    "note": (
                        "If the active compound does not engage its annotated target here, attributing the "
                        "phenotype to that target is unsupported however concordant the premise looked."
                    ),
                },
            ]
        )
    else:
        rules.append(
            {
                "decision": "defer",
                "required_outcomes": {},
                "note": (
                    "No local release measures engagement in this context, so the premise that separates the "
                    "two explanations cannot be supplied and preserving the unknown is the licensed answer."
                ),
            }
        )
    return rules


def _final_test(candidate: Candidate, *, kinobeads: Sequence[KinobeadsRecord]) -> list[dict[str, Any]]:
    """The always-hidden independent binding test, where the release covers the compound."""

    gene = candidate.primary_target or ""
    folded = normalise_compound(candidate.compound)
    rows = [record for record in kinobeads if normalise_compound(record.compound) == folded]
    if not rows:
        return []
    listed = [record for record in rows if record.gene == gene and record.apparent_kd_nanomolar is not None]
    outcome = "listed_as_kinobeads_target" if listed else "not_listed_as_kinobeads_target"
    mapping = FINAL_TEST_MAP[candidate.archetype.value][outcome]
    if not mapping[0] and not mapping[1]:
        return []
    if listed:
        best = min(listed, key=lambda record: record.apparent_kd_nanomolar or float("inf"))
        statement = (
            f"The independent kinobeads release lists {gene} as a target of {candidate.compound} with an "
            f"apparent Kd of {best.apparent_kd_nanomolar:.1f} nM in {best.lysate} lysate "
            f"({best.classification})."
        )
        source = best.source_id()
    else:
        statement = (
            f"The independent kinobeads release profiles {candidate.compound} and does not list {gene} "
            f"among its targets with a fitted apparent Kd ({len(rows)} target rows for this compound)."
        )
        source = rows[0].source_id()
    return [
        {
            "identifier": f"kinobeads-{_slug(candidate.compound)}-{gene}",
            "statement": statement,
            "source_id": source,
            "outcome": outcome,
            "confirms": list(mapping[0]),
            "contradicts": list(mapping[1]),
            "record_validated": True,
            "biological_quality": "passed",
            "evidence_kind": "real_measurement",
            "limitations": [
                "Competition binding in a cell lysate does not establish engagement in living cells: permeability, efflux and intracellular competition are not represented.",
                "The lysate is not this context; the release profiles a fixed lysate mixture.",
                "Absence from a target list is bounded by the assay's own coverage of that protein.",
            ],
        }
    ]


def _limitations(candidate: Candidate, *, asset: EngagementAsset) -> list[str]:
    limitations = [
        "This is a retrospective package built from released records; it contains no new experiment.",
        "The dependency, phenotype, engagement and binding records come from four different releases and are not matched for exposure, dose, duration, assay or replicate structure.",
        "A stability shift is an engagement effect size, not an occupancy fraction, and no condition-matched occupancy measurement exists for any condition in this package.",
        "The engagement release's exposure concentration and duration are undeclared in the local asset.",
        "Compound identity across releases is matched on the folded name; no local release carries a structure key for every compound.",
        f"Engagement calls rest on a measured vehicle-null threshold of {asset.null.threshold:.4f} log2 whose held-out false-positive rate is {asset.null.holdout_rate:.5f} (one-sided 95 percent upper bound {asset.null.holdout_rate_upper_95:.5f}).",
    ]
    if (candidate.dependent_fraction or 0.0) >= ARCHETYPE_THRESHOLDS["pan_essential_gene_fraction"]:
        limitations.append(
            f"{candidate.primary_target} is a panel-wide dependency "
            f"({(candidate.dependent_fraction or 0.0) * 100:.1f} percent of screened models), so the genetic "
            "phenotype here is not evidence of a selective target programme."
        )
    return limitations


def build_case(
    candidate: Candidate,
    *,
    asset: EngagementAsset,
    profile: DepMapProfile,
    kinobeads: Sequence[KinobeadsRecord],
    comparator_phenotype,
    annotation_source: str,
    releases: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """One case as three payloads: public, evaluator-only, and the manifest row."""

    identifier = case_identifier(candidate)
    # One flag decides the comparator route everywhere: whether it is on the menu, whether its
    # curve is a hidden result, whether its engagement is a registered premise, and whether the
    # rules that read it exist. Two notions of "the comparator is available" let a result be
    # written for an action the menu never carried.
    comparator_on_menu = bool(
        candidate.comparator
        and candidate.comparator_engagement_covered
        and comparator_phenotype is not None
        and candidate.archetype
        in (EngagementArchetype.ENGAGEMENT_GAP_OR_MODE, EngagementArchetype.NO_ENGAGEMENT_COVERAGE)
    )
    comparator_covered = comparator_on_menu
    actions = _menu_actions(candidate)
    if not comparator_on_menu:
        # A comparator whose engagement no capability can supply would leave a gated action on
        # the menu that nothing can ever make interpretable, so it is not registered at all.
        actions = [item for item in actions if item["identifier"] != "mode_matched_comparator"]
    public = {
        "identifier": identifier,
        "provenance": f"retrospective_real_public_records; {releases}",
        "evaluation_status": "engagement_repair_case_with_hidden_results",
        "initial_evidence": _initial_evidence(candidate, annotation_source=annotation_source),
        "context_identifier": candidate.context_identifier,
        "budget": CASE_BUDGET,
        "hypotheses": _hypotheses(candidate),
        "actions": actions,
        "premise_registry": _premise_registry(candidate),
        "repair_outcome_templates": _repair_outcome_templates(candidate),
        "limitations": _limitations(candidate, asset=asset),
    }
    if not comparator_covered:
        public["premise_registry"].pop(COMPARATOR_ENGAGEMENT_PREMISE, None)
        public["repair_outcome_templates"].pop(COMPARATOR_ENGAGEMENT_PREMISE, None)
    results = _menu_results(candidate, comparator_phenotype=comparator_phenotype if comparator_covered else None)
    repair_results = _repair_results(
        candidate, asset=asset, profile=profile, comparator_covered=comparator_covered
    )
    rules = _licensing_rules(candidate, comparator_covered=comparator_covered)
    final_test = _final_test(candidate, kinobeads=kinobeads)
    critical = (
        ["target_abundance_rna"]
        if candidate.archetype is EngagementArchetype.UNATTRIBUTED_ACTIVE_COMPOUND
        else []
    )
    private = {
        "case_id": identifier,
        "results": results,
        "repair_results": repair_results,
        "final_test": final_test,
        "scoring": {"decision_rules": rules, "critical_actions": critical},
    }
    metadata = {
        "case_id": identifier,
        "archetype": candidate.archetype.value,
        "context_identifier": candidate.context_identifier,
        "model_id": candidate.model_id,
        "cell_line": candidate.cell_line,
        "gene": candidate.primary_target,
        "source_cluster": candidate.primary_target,
        "compound": candidate.compound,
        "curated_targets": list(candidate.curated_targets),
        "comparator_compound": candidate.comparator,
        "comparator_engagement_covered": comparator_covered,
        "engagement_covered": candidate.engagement_covered,
        "gene_effect": candidate.gene_effect,
        "dependent_model_fraction": candidate.dependent_fraction,
        "abundance_log2_tpm1": candidate.abundance,
        "phenotype_release": candidate.phenotype.release if candidate.phenotype else None,
        "phenotype_active": candidate.phenotype.is_active if candidate.phenotype else None,
        "phenotype_ic50_micromolar": candidate.phenotype.ic50_micromolar if candidate.phenotype else None,
        "phenotype_auc": candidate.phenotype.auc if candidate.phenotype else None,
        "licensed_decisions": sorted({rule["decision"] for rule in rules}),
        "critical_actions": critical,
        "repair_identifiers": [row["action_identifier"] for row in repair_results],
        "final_test_records": [row["identifier"] for row in final_test],
        "hidden_result_actions": [row["action_identifier"] for row in repair_results],
    }
    return public, private, metadata


def capability_registry_payload(
    *,
    asset: EngagementAsset,
    kinobeads: Sequence[KinobeadsRecord],
    kinobeads_source: str,
    kinobeads_sha256: str,
) -> dict[str, Any]:
    """The public catalogue: declarations and coverage, never a value."""

    genes = sorted({identifier.split("_")[0] for identifier in asset.proteins})
    compounds = list(asset.compounds)
    engagement_common = {
        "quantity": "engagement_shift",
        "kind": "functional_measurement",
        "units": ENGAGEMENT_UNITS,
        "context_identifier": asset.context_identifier,
        "is_estimate": False,
        "cost": ACTION_COST,
        "lab_cost": dict(RETRIEVAL_PRICE, source="released supplementary record"),
        "readout": "vehicle_referenced_stability_shift_log2",
        "compounds": compounds,
        "entities": genes,
        "source": asset.source,
        "source_sha256": asset.sha256,
    }
    return {
        "schema": CAPABILITY_SCHEMA,
        "identifier": "engagement-capabilities-v1",
        "note": (
            "What each local release could supply for a missing premise, with its declared type and its "
            "coverage. No value appears here: a policy proposes from the declaration, and the framework "
            "decides admissibility by the same typed comparison the executor uses."
        ),
        "null_model": asset.null.payload(),
        "capabilities": [
            dict(
                engagement_common,
                identifier=INDEX_CAPABILITY,
                description="Vehicle-referenced stability shift of one protein under one compound in living K562 cells.",
                supplies=INDEX_ENGAGEMENT_PREMISE,
                note="Supplies the premise whichever way the call comes out; a negative call is evidence, not a missing premise.",
            ),
            dict(
                engagement_common,
                identifier=COMPARATOR_CAPABILITY,
                description="The same release, read for the comparator compound's engagement of the same target.",
                supplies=COMPARATOR_ENGAGEMENT_PREMISE,
                note="Only a positive call makes the comparator's viability curve interpretable.",
            ),
            {
                "identifier": OVERLAP_CAPABILITY,
                "description": "Proteins this compound engages in this context that are themselves dependencies here, excluding its curated targets.",
                "supplies": OVERLAP_PREMISE,
                "quantity": "engagement_shift",
                "kind": "evidence_review",
                "units": OVERLAP_UNITS,
                "context_identifier": asset.context_identifier,
                "is_estimate": True,
                "cost": ACTION_COST,
                "lab_cost": dict(RETRIEVAL_PRICE, source="derived intersection of two released records"),
                "readout": "engaged_dependency_overlap",
                "compounds": compounds,
                "entities": [],
                "entity_is_proteome": True,
                "source": f"derived: {asset.source} intersected with DepMap 24Q2 CRISPRGeneEffect.csv",
                "source_sha256": asset.sha256,
                "note": "A derived intersection of two releases, declared as an estimate rather than a measurement.",
            },
            {
                "identifier": LYSATE_CAPABILITY,
                "description": "Competition binding of one compound to one kinase in a fixed cell-lysate mixture.",
                "supplies": INDEX_ENGAGEMENT_PREMISE,
                "quantity": "target_occupancy",
                "kind": "functional_measurement",
                "units": LYSATE_UNITS,
                "context_identifier": None,
                "is_estimate": True,
                "cost": ACTION_COST,
                "lab_cost": dict(RETRIEVAL_PRICE, source="released supplementary record"),
                "readout": "apparent_dissociation_constant",
                "compounds": sorted({record.compound for record in kinobeads}),
                "entities": sorted({record.gene for record in kinobeads}),
                "source": kinobeads_source,
                "source_sha256": kinobeads_sha256,
                "note": (
                    "Registered so that proposing it is answered by name rather than by silence: a foreign-lysate "
                    "estimate cannot discharge an in-context engagement premise, and the typed admission says so."
                ),
            },
        ],
    }


def write_package(
    payloads: Sequence[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    *,
    public_directory: Path,
    private_directory: Path,
    manifest_path: Path,
    screening_path: Path,
    registry_path: Path,
    registry: Mapping[str, Any],
    screening: Sequence[Mapping[str, Any]],
    manifest_header: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Write the public cases, the evaluator-only files, the registry and both tables."""

    public_directory.mkdir(parents=True, exist_ok=True)
    private_directory.mkdir(parents=True, exist_ok=True)
    for path in (manifest_path, screening_path, registry_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[Mapping[str, Any]] = []
    for public, private, metadata in payloads:
        identifier = public["identifier"]
        (public_directory / f"{identifier}.json").write_text(
            json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (private_directory / f"{identifier}.results.json").write_text(
            json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rows.append(metadata)
    manifest = dict(manifest_header, cases=rows)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    screening_path.write_text(
        json.dumps({"rows": list(screening)}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Build and write the package; prints counts only, never a hidden value."""

    import argparse

    from tools.evaluation.engagement_cases import (
        DEPMAP_DIRECTORY,
        GDSC2_PATH,
        K562_CONTEXT,
        K562_GDSC_NAME,
        K562_MODEL,
        KINOBEADS_PATH,
        MCF7_GDSC_NAME,
        MCF7_MODEL,
        PISA_ANNOTATION_MEMBER,
        PISA_CELL_MEMBER,
        PISA_SOURCE,
        PISA_ZIP,
        PRISM_CURVES,
        _gdsc_phenotype,
        _pisa_annotation,
        _prism_rows,
        screen_k562,
        screen_mcf7,
        select,
    )
    from tools.evaluation.engagement_sources import (
        load_depmap_profile,
        load_engagement_asset,
        load_gdsc2,
        load_kinobeads,
    )
    from tools.evaluation.engagement_sources import sheet_digest

    parser = argparse.ArgumentParser(description="Build the MAESTRO engagement-repair case package.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--package", default="engagement_v1")
    parser.add_argument("--cache", type=Path, help="Directory for release extraction caches.")
    parser.add_argument(
        "--require-selective-dependency",
        action="store_true",
        help=(
            "Apply the superseded section 5 rule. The addendum of 2026-09-14 21:15 UTC drops the "
            "selectivity requirement from the engagement archetype; this flag reproduces the original."
        ),
    )
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    workspace = arguments.workspace
    cache = arguments.cache or (workspace / "tmp" / "engagement_cache")
    cache.mkdir(parents=True, exist_ok=True)

    asset = load_engagement_asset(
        workspace / PISA_ZIP,
        member=PISA_CELL_MEMBER,
        source=PISA_SOURCE,
        context_identifier=K562_CONTEXT,
        exposure_note="undeclared_in_local_asset",
    )
    annotation = _pisa_annotation(workspace / PISA_ZIP)
    gdsc = load_gdsc2(
        workspace / GDSC2_PATH,
        cell_lines=(K562_GDSC_NAME, MCF7_GDSC_NAME),
        cache=cache / "gdsc2_two_lines.json",
    )
    k562_rows = [record for record in gdsc if record.cell_line == K562_GDSC_NAME]
    curated = sorted({gene for entry in annotation.values() for gene in entry["targets"]})
    k562 = load_depmap_profile(
        directory=workspace / DEPMAP_DIRECTORY,
        model_id=K562_MODEL,
        cell_line="K562",
        genes=curated,
        cache=cache / "depmap_k562.json",
    )
    prism_rows = _prism_rows(workspace / PRISM_CURVES, MCF7_MODEL)
    prism_targets = sorted({(row.get("target") or "").strip() for row in prism_rows if (row.get("target") or "").strip()})
    mcf7 = load_depmap_profile(
        directory=workspace / DEPMAP_DIRECTORY,
        model_id=MCF7_MODEL,
        cell_line="MCF7",
        genes=prism_targets,
        cache=cache / "depmap_mcf7.json",
    )
    require_selective = bool(arguments.require_selective_dependency)
    candidates = list(
        screen_k562(
            asset=asset,
            annotation=annotation,
            gdsc=k562_rows,
            profile=k562,
            require_selective_dependency=require_selective,
        )
    ) + list(screen_mcf7(rows=prism_rows, profile=mcf7, require_selective_dependency=require_selective))
    selected = select([item for item in candidates if item.archetype])
    genes = sorted({item.primary_target or "" for item in selected})
    kinobeads = load_kinobeads(
        workspace / KINOBEADS_PATH, compounds=[item.compound for item in selected]
    )
    releases = "; ".join(
        (
            f"DepMap 24Q2 Public:CRISPRGeneEffect.csv (MD5 {k562.digests.get('CRISPRGeneEffect.csv', '')[:12]})",
            f"GDSC2 release 8.5 (SHA-256 {sheet_digest(workspace / GDSC2_PATH)[:12]})",
            "PRISM Repurposing 19Q4:secondary-screen-dose-response-curve-parameters.csv",
            f"{asset.source} (SHA-256 {asset.sha256[:12]})",
        )
    )
    payloads = []
    for candidate in selected:
        comparator_phenotype = (
            _gdsc_phenotype(k562_rows, candidate.comparator)
            if candidate.comparator and candidate.context_identifier == K562_CONTEXT
            else None
        )
        public, private, metadata = build_case(
            candidate,
            asset=asset,
            profile=k562 if candidate.model_id == K562_MODEL else mcf7,
            kinobeads=kinobeads,
            comparator_phenotype=comparator_phenotype,
            annotation_source=f"PISA-eLife-2024:{PISA_ANNOTATION_MEMBER}:curated-targets",
            releases=releases,
        )
        metadata["split"] = assign_split(candidate.primary_target or "", genes)
        payloads.append((public, private, metadata))

    root = workspace / "data" / "evaluation"
    manifest = write_package(
        payloads,
        public_directory=root / "cases" / arguments.package / "public",
        private_directory=root / "cases" / arguments.package / "private",
        manifest_path=root / "derived" / f"engagement_case_manifest_{arguments.package.split('_')[-1]}.json",
        screening_path=root / "derived" / f"engagement_screening_{arguments.package.split('_')[-1]}.json",
        registry_path=root / "capabilities" / "engagement_capabilities_v1.json",
        registry=capability_registry_payload(
            asset=asset,
            kinobeads=load_kinobeads(workspace / KINOBEADS_PATH),
            kinobeads_source="Klaeger et al. 2017 kinobeads target table, sheet 'Kinobeads'",
            kinobeads_sha256=sheet_digest(workspace / KINOBEADS_PATH),
        ),
        screening=[item.row() for item in candidates],
        manifest_header={
            "package": arguments.package,
            "preregistration": "data/evaluation/preregistrations/20260914_engagement_package.md",
            "construction_settings": dict(ARCHETYPE_THRESHOLDS),
            "require_selective_dependency": require_selective,
            "action_cost": ACTION_COST,
            "case_budget": CASE_BUDGET,
            "engagement_null_model": asset.null.payload(),
            "engagement_source": asset.provenance(),
            "screened_candidates": len(candidates),
        },
    )
    counts: dict[str, int] = {}
    for row in manifest["cases"]:
        counts[row["archetype"]] = counts.get(row["archetype"], 0) + 1
    print(
        f"cases={len(manifest['cases'])} archetypes={counts} "
        f"contexts={sorted({row['context_identifier'] for row in manifest['cases']})} "
        f"clusters={len({row['source_cluster'] for row in manifest['cases']})} "
        f"screened={len(candidates)}"
    )
    for row in manifest["cases"]:
        print(
            f"  {row['case_id']:44s} {row['archetype']:34s} split={row['split']:11s} "
            f"repairs={len(row['repair_identifiers'])} final_test={len(row['final_test_records'])} "
            f"licensed={row['licensed_decisions']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
