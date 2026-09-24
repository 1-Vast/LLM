"""Materialise the engagement-repair package: cases, hidden records, registry, manifest.

File summary
- Path: src/evaluation/engagement_package.py
- Purpose: turn the screened candidates of `engagement_cases` into frozen files - a public
  case, an evaluator-only result file carrying the hidden engagement records and the
  always-hidden partition, a capability registry, an evaluator manifest and a screening
  table. The licensing rules enumerate every possible outcome of every route, so the rule
  set is written without knowing which outcome occurred.
- Core points:
  - The index-engagement premise is supplied whichever way the measurement comes out, so a
    negative engagement record is evidence rather than a missing premise. The comparator
    gate is the opposite by construction: only a positive comparator engagement makes the
    comparator's viability curve interpretable, and a negative one leaves it uninterpretable.
  - Every purchasable action is a retrieval priced at 0 wells and 0 turnaround days. The one
    action priced as a new measurement, the condition-matched assay, is registered
    unavailable, so no laboratory cost can be spent on this package.
  - The always-hidden partition is a cell-lysate competition-binding record from an
    independent release. The framework refuses it as an engagement supplier, so it can only
    ever test a decision that was already made.
- Interfaces: `build_package`, `write_package`, `capability_registry_payload`, `main`
- Depends on: evaluation.engagement_cases, evaluation.engagement_sources,
  evaluation.capabilities, evaluation.case_builder (the split rule)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.capabilities import CAPABILITY_SCHEMA, canonical_repair_identifier  # noqa: E402
from evaluation.case_builder import ARCHETYPE_THRESHOLDS, assign_split  # noqa: E402
from evaluation.engagement_cases import (  # noqa: E402
    ABUNDANCE_PREMISE,
    ACTION_COST,
    CASE_BUDGET,
    CAUSAL_FACTORS,
    COMPARATOR_CAPABILITY,
    COMPARATOR_ENGAGEMENT_PREMISE,
    DEVELOPMENT_ACTIONS,
    INDEX_CAPABILITY,
    INDEX_ENGAGEMENT_PREMISE,
    INSUFFICIENT,
    LYSATE_CAPABILITY,
    MODE_NON_EQUIVALENCE,
    OVERLAP_CAPABILITY,
    OVERLAP_PREMISE,
    PAIRS,
    SELECTIVITY_PREMISE,
    TARGET_MEDIATED,
    ATTRIBUTION_ERROR,
    UNAVAILABLE_ENGAGEMENT_COST,
    UNAVAILABLE_ENGAGEMENT_DAYS,
    UNAVAILABLE_ENGAGEMENT_WELLS,
    Candidate,
    EngagementArchetype,
)
from evaluation.engagement_sources import (  # noqa: E402
    ENGAGEMENT_UNITS,
    DepMapProfile,
    EngagementAsset,
    KinobeadsRecord,
    normalise_compound,
)

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

    from evaluation.engagement_cases import (
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
    from evaluation.engagement_sources import (
        load_depmap_profile,
        load_engagement_asset,
        load_gdsc2,
        load_kinobeads,
    )
    from evaluation.xlsx import sheet_digest

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


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())

