"""Build leakage-bounded mechanism-contrast cases from the real evidence base.

File summary
- Path: src/evaluation/case_builder.py
- Purpose: Turn real DepMap and PRISM records into frozen public cases with evaluator-only outcomes and licensing rules.
- Core points:
  - A case archetype is defined by a joint evidence pattern, never by a desired answer.
  - Licensing rules state which decision the revealed evidence supports; they are not biological ground truth.
  - Public material holds the premise and the menu; measured values behind a menu action stay private until queried.
- Interfaces: `CaseArchetype`, `ClassifiedCase`, `classify`, `select_comparator`, `assign_split`, `build_cases`, `write_cases`, `ARCHETYPE_THRESHOLDS`
- Depends on: evaluation.evidence_base, maestro.models
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .evidence_base import EvidenceBase, ExposureRecord

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
