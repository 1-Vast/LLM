"""Regression tests for gene-set pathway readouts and world-model expressivity.

File summary
- Path: tests/test_pathway_readout.py
- Purpose: pin what a transcriptional pathway score is, and pin the separate
  question of whether a backend's output coordinates can represent it at all.
- Core points:
  - A gene-set score is RNA abundance of a declared set; it is never proximal
    activity, and the typing refuses that substitution.
  - A set is identified by its resolved members and their digest, so a silently
    changed definition cannot masquerade as the registered endpoint.
  - Scoring a set whose members are not all available must be an explicit
    restriction, not a silent average over whatever happened to be present.
  - Expressivity is a property of the coordinate space, answerable before any
    prediction is made and independent of accuracy.
- Interfaces: pytest test functions
- Depends on: virtual_cell.pathway_readout, virtual_cell.biology, maestro.models
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from maestro.models import BiologicalQuantity, PremiseRequirement
from virtual_cell.biology import MeasurementModel, Observable
from virtual_cell.pathway_readout import (
    BackgroundPool,
    GeneSet,
    expressivity_audit,
    load_background_pool,
    pathway_observable,
    score_gene_set,
    standardised_score,
)


def _set(members: tuple[str, ...] = ("DUSP4", "DUSP6", "SPRY2", "ETV5")) -> GeneSet:
    return GeneSet(
        identifier="P2_mapk_output_panel",
        members=members,
        source="frozen literature panel",
        source_sha256="0" * 64,
        rule="fixed panel declared in preregistration.json",
    )


def test_a_gene_set_is_identified_by_its_members_not_their_order():
    first = _set(("DUSP4", "DUSP6", "SPRY2"))
    second = _set(("SPRY2", "DUSP4", "DUSP6"))
    assert first.digest == second.digest
    assert first.digest != _set(("DUSP4", "DUSP6")).digest


def test_scoring_refuses_a_set_whose_members_are_not_all_available():
    values = {"DUSP4": 0.5, "DUSP6": 0.7}
    with pytest.raises(ValueError):
        score_gene_set(values, _set())


def test_an_explicit_restriction_scores_and_names_what_it_dropped():
    values = {"DUSP4": 0.5, "DUSP6": 0.7}
    restricted, missing = _set().restricted_to(values)
    assert set(restricted.members) == {"DUSP4", "DUSP6"}
    assert set(missing) == {"SPRY2", "ETV5"}
    assert score_gene_set(values, restricted) == pytest.approx(0.6)
    assert restricted.digest != _set().digest, "a restricted set is a different endpoint"


def test_a_pathway_score_is_rna_abundance_and_not_proximal_activity():
    observable = pathway_observable(_set(), context_identifier="NCI-H596", time_hours=24.0)
    assert observable.quantity is BiologicalQuantity.RNA_ABUNDANCE
    assert observable.entity.endswith("P2_mapk_output_panel")

    activity = Observable(
        name="ERK_activity",
        quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        entity="MAPK1",
        units="fraction_of_control",
        assay="phospho_elisa",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="NCI-H596",
        time_hours=24.0,
    )
    assert not observable.interchangeable_with(activity)
    assert "quantity_mismatch" in observable.mismatches(activity)

    requirement = PremiseRequirement(
        field="pathway_activity_suppressed",
        quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        entity="MAPK1",
        context_identifier="NCI-H596",
    )
    grant = observable.grant_for(requirement.field, source_action="tahoe_transcriptome", quality_passed=True)
    assert any(reason.startswith("quantity_mismatch") for reason in requirement.unmet_reasons(grant))


def test_standardisation_uses_size_matched_background_sets():
    values = {f"G{i}": 0.0 for i in range(200)}
    values.update({"A": 1.0, "B": 1.0, "C": 1.0})
    target = GeneSet("target", ("A", "B", "C"), source="fixture", source_sha256="0" * 64, rule="fixture")
    # The sampling frame is declared, not inherited from whatever the values happen to
    # contain: the pool is what makes the background auditable, and it is required.
    pool = BackgroundPool(
        identifier="fixture_background",
        members=tuple(sorted(values)),
        source="test fixture coordinates",
        source_sha256="0" * 64,
        rule="every coordinate the fixture carries",
    )
    result = standardised_score(values, target, draws=200, seed=7, background=pool)
    assert result.raw == pytest.approx(1.0)
    assert result.z > 3.0
    assert result.background_draws == 200
    assert result.background_pool_id == pool.identifier
    assert result.background_pool_digest == pool.digest
    assert result.background_members_absent_from_the_values == 0

    quiet = GeneSet("quiet", ("G1", "G2", "G3"), source="fixture", source_sha256="0" * 64, rule="fixture")
    assert abs(standardised_score(values, quiet, draws=200, seed=7, background=pool).z) < 3.0


def test_standardisation_without_a_declared_pool_is_refused_by_name():
    """A guard that passes when nothing is declared is not a guard."""

    values = {"A": 1.0, "B": 1.0, "C": 1.0}
    target = GeneSet("target", ("A", "B"), source="fixture", source_sha256="0" * 64, rule="fixture")
    with pytest.raises(ValueError, match="background_pool_not_declared"):
        standardised_score(values, target, draws=20, seed=1)


def test_a_background_pool_artefact_must_match_its_own_digest(tmp_path: Path):
    """The pool travels as a digested artefact; an edited pool is refused, not used."""

    import json

    pool = BackgroundPool(
        identifier="fixture_background",
        members=("A", "B", "C"),
        source="test fixture coordinates",
        source_sha256="0" * 64,
        rule="declared fixture",
    )
    path = tmp_path / "background_pool.json"
    payload = {
        "schema": "maestro.background_pool.v1",
        "identifier": pool.identifier,
        "digest": pool.digest,
        "size": pool.size,
        "source": pool.source,
        "source_sha256": pool.source_sha256,
        "rule": pool.rule,
        "members": list(pool.members),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_background_pool(path).digest == pool.digest

    payload["members"] = [*pool.members, "D"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match its recorded digest"):
        load_background_pool(path)


def test_expressivity_is_answered_before_any_prediction():
    coordinates = ("DUSP4", "EGFR", "ERBB2")
    audit = expressivity_audit(_set(), coordinates)
    assert audit.total_members == 4
    assert audit.representable == 1
    assert audit.fraction == pytest.approx(0.25)
    assert set(audit.missing_members) == {"DUSP6", "SPRY2", "ETV5"}
    assert audit.verdict == "partially_expressible"

    assert expressivity_audit(_set(), ()).verdict == "not_expressible"
    assert expressivity_audit(_set(), _set().members).verdict == "expressible"


def test_an_inexpressible_endpoint_is_a_named_applicability_reason():
    audit = expressivity_audit(_set(), ("EGFR",))
    assert audit.applicability_reason == "endpoint_not_representable_in_output_space:P2_mapk_output_panel"
    assert expressivity_audit(_set(), _set().members).applicability_reason is None
