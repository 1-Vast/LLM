"""Contract tests for the engagement capability layer and the release readers it uses.

File summary
- Path: tests/test_engagement_package.py
- Purpose: pin the behaviour the engagement-repair package depends on: a dependency-free
  reader for the released workbooks, a measured binomial bound, the typed admission that
  decides whether a proposed capability may run, and the environment step that admits a
  compiled repair without letting any policy reach its result early.
- Core points: assertions here are contract tests, not biological results. Values read from a
  release are checked for structure and identity, never asserted to mean anything.
- Interfaces: one test per contract, named for the contract it pins.
- Depends on: evaluation.xlsx, evaluation.engagement_sources, evaluation.capabilities,
  evaluation.cases
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.capabilities import (  # noqa: E402
    CAPABILITY_SCHEMA,
    CapabilityOffer,
    CapabilityRegistry,
    ProposalRefusal,
    canonical_repair_identifier,
    compile_proposal,
    load_capability_registry,
)
from evaluation.cases import CaseRepository, ReplayCase, ReplayEnvironment, RevealRefusal  # noqa: E402
from evaluation.engagement_sources import clopper_pearson_upper, normalise_compound  # noqa: E402
from evaluation.lab_cost import LabCost, CostBasis  # noqa: E402
from evaluation.xlsx import Workbook, column_index  # noqa: E402
from maestro.models import BiologicalQuantity, EvidenceActionKind  # noqa: E402

PISA_ZIP = ROOT / "data" / "external" / "pisa_living_cells" / "PMC11554310_supplementary.zip"


def _offer(**overrides) -> CapabilityOffer:
    defaults = dict(
        identifier="index_offer",
        description="A released stability-shift record.",
        supplies="engagement:index_on_target",
        quantity=BiologicalQuantity.ENGAGEMENT_SHIFT,
        kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
        cost=1.0,
        lab_cost=LabCost(basis=CostBasis.RECORD_RETRIEVAL, wells=0, turnaround_days=0.0),
        source="a release",
        source_sha256="0" * 64,
        units="log2_shift",
        context_identifier="ACH-000551:K562",
        compounds=("Dasatinib",),
        entities=("ABL1",),
    )
    defaults.update(overrides)
    return CapabilityOffer(**defaults)


def _registry(*offers: CapabilityOffer) -> CapabilityRegistry:
    return CapabilityRegistry(
        schema=CAPABILITY_SCHEMA,
        identifier="test-registry",
        offers={offer.identifier: offer for offer in offers},
        sha256="1" * 64,
    )


def _case(tmp_path: Path, **overrides) -> ReplayCase:
    """A one-case package on disk, so the loader is what builds the objects under test."""

    public = {
        "identifier": "eng-abl1-dasatinib-ach000551",
        "provenance": "test",
        "evaluation_status": "engagement_repair_case_with_hidden_results",
        "initial_evidence": [
            {
                "identifier": "crispr-gene-effect",
                "statement": "A dependency score.",
                "source_id": "DepMap-24Q2:CRISPRGeneEffect.csv:ACH-000551:ABL1",
            }
        ],
        "context_identifier": "ACH-000551:K562",
        "budget": 3.0,
        "hypotheses": [
            {
                "identifier": "insufficient_functional_perturbation",
                "description": "The compound does not engage the target here.",
                "development_action": "revise_intervention",
            },
            {
                "identifier": "genetic_pharmacological_mode_non_equivalence",
                "description": "Engagement is achieved but does not reproduce genetic loss.",
                "development_action": "change_intervention_mode",
            },
        ],
        "actions": [
            {
                "identifier": "target_abundance_rna",
                "description": "RNA abundance.",
                "cost": 1.0,
                "distinguishes": [
                    "insufficient_functional_perturbation",
                    "genetic_pharmacological_mode_non_equivalence",
                ],
                "kind": "rna_abundance_measurement",
                "quantity": "rna_abundance",
                "entity": "ABL1",
                "units": "log2_tpm_plus_1",
                "supplies": ["abundance:target_rna"],
                "expected_outcomes": {
                    "insufficient_functional_perturbation": "target_expressed",
                    "genetic_pharmacological_mode_non_equivalence": "target_expressed",
                },
            },
            {
                "identifier": "mode_matched_comparator",
                "description": "A second compound's curve.",
                "cost": 1.0,
                "distinguishes": [
                    "insufficient_functional_perturbation",
                    "genetic_pharmacological_mode_non_equivalence",
                ],
                "kind": "mode_matched_comparator",
                "quantity": "viability",
                "prerequisites": ["abundance:target_rna"],
                "interpretation_gate": "engagement:comparator_on_target",
                "expected_outcomes": {
                    "insufficient_functional_perturbation": "comparator_active",
                    "genetic_pharmacological_mode_non_equivalence": "comparator_inactive",
                },
            },
        ],
        "premise_registry": {
            "abundance:target_rna": {
                "quantity": "rna_abundance",
                "entity": "ABL1",
                "units": "log2_tpm_plus_1",
                "context_identifier": "ACH-000551:K562",
            },
            "engagement:index_on_target": {
                "quantity": "engagement_shift",
                "entity": "ABL1@dasatinib",
                "units": "log2_shift",
                "context_identifier": "ACH-000551:K562",
                "require_direct_measurement": True,
            },
        },
        "repair_outcome_templates": {
            "engagement:index_on_target": {
                "insufficient_functional_perturbation": "not_engaged",
                "genetic_pharmacological_mode_non_equivalence": "engaged",
            }
        },
        "limitations": ["A test fixture."],
    }
    public.update(overrides)
    identifier = str(public["identifier"])
    repair_id = canonical_repair_identifier("index_offer", "Dasatinib", "ABL1")
    private = {
        "case_id": identifier,
        "results": [
            {
                "action_identifier": "target_abundance_rna",
                "outcome": "target_expressed",
                "statement": "An abundance record.",
                "source_id": "DepMap-24Q2:OmicsExpression:ACH-000551:ABL1",
                "context_identifier": "ACH-000551:K562",
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
                "interpretation_fields": ["abundance:target_rna", "abundance:target_rna:expressed"],
            }
        ],
        "repair_results": [
            {
                "action_identifier": repair_id,
                "outcome": "engaged",
                "statement": "A stability shift beyond the measured vehicle null.",
                "source_id": "PISA:record",
                "context_identifier": "ACH-000551:K562",
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
                "interpretation_fields": [
                    "engagement:index_on_target",
                    "engagement:index_on_target:engaged",
                ],
            }
        ],
        "scoring": {
            "decision_rules": [
                {
                    "decision": "change_intervention_mode",
                    "required_outcomes": {repair_id: "engaged"},
                    "require_biological_quality": True,
                }
            ],
            "critical_actions": [],
        },
    }
    (tmp_path / "public").mkdir(parents=True, exist_ok=True)
    (tmp_path / "private").mkdir(parents=True, exist_ok=True)
    (tmp_path / "public" / f"{identifier}.json").write_text(json.dumps(public), encoding="utf-8")
    (tmp_path / "private" / f"{identifier}.results.json").write_text(json.dumps(private), encoding="utf-8")
    loaded = CaseRepository(tmp_path / "public", tmp_path / "private").load()
    return loaded[0][0], loaded[0][1]


def test_column_index_reads_multi_letter_references():
    assert column_index("A1") == 0
    assert column_index("Z9") == 25
    assert column_index("AA1") == 26
    assert column_index("BK12") == 62
    with pytest.raises(ValueError):
        column_index("12")


@pytest.mark.skipif(not PISA_ZIP.is_file(), reason="the engagement release is not present locally")
def test_a_workbook_inside_an_archive_is_read_without_unpacking_it():
    """The release ships as a zip of workbooks; provenance stays the archive's digest."""

    with Workbook(PISA_ZIP, member="elife-95595-supp1.xlsx") as workbook:
        assert workbook.sheet_names == ("Sheet1",)
        rows = list(workbook.rows("Sheet1"))
    assert rows[0][:4] == ["Compound", "Curated Targets", "Assayed in cells", "Assayed in lysates"]
    annotated = {str(row[0]): str(row[1]) for row in rows[1:] if row and row[0]}
    assert "ABL1" in annotated["Dasatinib"]
    assert all(isinstance(name, str) and name for name in annotated)


def test_a_missing_archive_member_is_refused_by_name():
    with pytest.raises(KeyError):
        Workbook(PISA_ZIP, member="not-a-member.xlsx")


def test_the_binomial_bound_is_reportable_where_the_point_estimate_is_not():
    """Zero exceedances is not a zero error rate; the bound is what may be reported."""

    bound = clopper_pearson_upper(0, 100)
    assert bound is not None and 0.028 < bound < 0.031
    assert clopper_pearson_upper(0, 0) is None
    assert clopper_pearson_upper(5, 5) == 1.0
    tighter = clopper_pearson_upper(0, 1000)
    assert tighter < bound


def test_compound_identity_folds_salt_forms_and_punctuation():
    assert normalise_compound("MK-2206 (dihydrochloride)") == normalise_compound("MK2206")
    assert normalise_compound("(+)-JQ-1") == "jq1"
    assert normalise_compound("BI 2536") == "bi2536"


def test_a_compiled_proposal_takes_its_outcomes_from_the_case_not_the_proposal(tmp_path):
    case, _ = _case(tmp_path)
    registry = _registry(_offer())
    compiled = compile_proposal(
        case.public,
        registry,
        {
            "operator": "register_supplier",
            "capability": "index_offer",
            "supplies": "engagement:index_on_target",
            "compound": "Dasatinib",
            "entity": "ABL1",
            "expected_outcomes": {"insufficient_functional_perturbation": "whatever_the_model_says"},
            "cost": 0.01,
        },
    )
    assert compiled.identifier == canonical_repair_identifier("index_offer", "Dasatinib", "ABL1")
    assert compiled.action.expected_outcomes == {
        "insufficient_functional_perturbation": "not_engaged",
        "genetic_pharmacological_mode_non_equivalence": "engaged",
    }
    # The model's own price is recorded and is not what the action costs.
    assert compiled.action.cost == 1.0
    assert compiled.claimed["cost"] == 0.01
    assert compiled.action.entity == "ABL1@dasatinib"


@pytest.mark.parametrize(
    "proposal, code",
    [
        ({"operator": "invent_measurement"}, "unknown_operator"),
        ({"operator": "register_supplier", "capability": "absent"}, "capability_not_registered"),
        (
            {
                "operator": "register_supplier",
                "capability": "index_offer",
                "supplies": "abundance:target_rna",
                "compound": "Dasatinib",
                "entity": "ABL1",
            },
            "premise_not_missing",
        ),
        (
            {
                "operator": "register_supplier",
                "capability": "index_offer",
                "compound": "Nilotinib",
                "entity": "ABL1",
            },
            "capability_does_not_cover_compound",
        ),
        (
            {
                "operator": "register_supplier",
                "capability": "index_offer",
                "compound": "Dasatinib",
                "entity": "BCR",
            },
            "entity_not_quantified_in_capability",
        ),
    ],
)
def test_every_refused_proposal_names_its_reason(tmp_path, proposal, code):
    case, _ = _case(tmp_path)
    registry = _registry(_offer(compounds=("Dasatinib",), entities=("ABL1",)))
    with pytest.raises(ProposalRefusal) as refusal:
        compile_proposal(case.public, registry, proposal)
    assert refusal.value.code == code


def test_a_foreign_lysate_estimate_is_refused_for_an_in_context_engagement_premise(tmp_path):
    """The registry may offer it; the typed admission is what decides, and it says no."""

    case, _ = _case(tmp_path)
    registry = _registry(
        _offer(
            identifier="kinobeads_lysate_binding_estimate",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            is_estimate=True,
            context_identifier=None,
            units="apparent_kd_nanomolar",
        )
    )
    with pytest.raises(ProposalRefusal) as refusal:
        compile_proposal(
            case.public,
            registry,
            {
                "operator": "register_supplier",
                "capability": "kinobeads_lysate_binding_estimate",
                "compound": "Dasatinib",
                "entity": "ABL1",
            },
        )
    assert refusal.value.code == "quantity_mismatch"
    assert "estimate_offered_for_direct_measurement" in refusal.value.detail


def test_a_capability_from_another_context_is_refused(tmp_path):
    case, _ = _case(tmp_path)
    registry = _registry(_offer(context_identifier="ACH-000019:MCF7"))
    with pytest.raises(ProposalRefusal) as refusal:
        compile_proposal(
            case.public,
            registry,
            {
                "operator": "register_supplier",
                "capability": "index_offer",
                "compound": "Dasatinib",
                "entity": "ABL1",
            },
        )
    assert refusal.value.code == "context_mismatch"


def test_the_missing_premises_are_the_fields_no_available_action_supplies(tmp_path):
    case, _ = _case(tmp_path)
    missing = case.public.missing_premises()
    assert "engagement:index_on_target" in missing
    assert "engagement:comparator_on_target" in missing
    assert "abundance:target_rna" not in missing


def test_an_admitted_repair_becomes_queryable_and_only_then(tmp_path):
    case, outcomes = _case(tmp_path)
    environment = ReplayEnvironment(case, outcomes)
    repair_id = canonical_repair_identifier("index_offer", "Dasatinib", "ABL1")
    assert repair_id not in {item.action.identifier for item in environment.view().case.actions}
    with pytest.raises(RevealRefusal) as refusal:
        environment.query(repair_id)
    assert refusal.value.code == "action_not_in_menu"

    registry = _registry(_offer())
    compiled = compile_proposal(
        case.public,
        registry,
        {
            "operator": "register_supplier",
            "capability": "index_offer",
            "compound": "Dasatinib",
            "entity": "ABL1",
        },
    )
    from evaluation.cases import EvidenceMenuItem

    environment.admit(EvidenceMenuItem(action=compiled.action, lab_cost=compiled.lab_cost))
    assert environment.admitted_repairs == (repair_id,)
    revealed = environment.query(repair_id)
    assert revealed.outcome == "engaged"
    assert "engagement:index_on_target" in revealed.interpretation_fields
    assert environment.spent == 1.0


def test_a_repair_result_may_not_shadow_a_menu_action(tmp_path):
    identifier = "eng-abl1-dasatinib-ach000551"
    (tmp_path / "public").mkdir(parents=True, exist_ok=True)
    (tmp_path / "private").mkdir(parents=True, exist_ok=True)
    case, _ = _case(tmp_path)
    private_path = tmp_path / "private" / f"{identifier}.results.json"
    payload = json.loads(private_path.read_text(encoding="utf-8"))
    payload["repair_results"][0]["action_identifier"] = "target_abundance_rna"
    private_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="repair_result_identifier_not_canonical"):
        CaseRepository(tmp_path / "public", tmp_path / "private").load()


def test_a_ledger_refusal_names_the_condition_that_disagreed(tmp_path):
    """A record whose release spells a condition differently is refused with a name.

    The replay runner records a refusal code per case; before this the store raised a bare
    ValueError and every such case was counted as 'unclassified', which hides exactly the
    cross-release disagreement that matters here.
    """

    from agent.cases import CaseStore, MeasurementResult
    from maestro.models import EvidenceAction, EvidenceKind

    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case-1", budget=3.0)
    action = EvidenceAction(
        identifier="engagement_lookup",
        description="A released engagement record.",
        cost=1.0,
        distinguishes=("a", "b"),
        expected_conditions={"compound": "dasatinib"},
    )
    store.record_plan("case-1", (action,), ready_to_measure=True, context_identifier="ACH-000551:K562")
    mismatching = MeasurementResult(
        action_identifier="engagement_lookup",
        statement="A record naming the compound as the other release spells it.",
        source_id="release:record",
        context_identifier="ACH-000551:K562",
        time_hours=None,
        independent_units=2,
        quality_passed=True,
        conditions={"compound": "Dasatinib"},
        metrics={},
        record_count=1,
        biological_replicates=None,
        evidence_kind=EvidenceKind.REAL_MEASUREMENT,
        interpretation_fields=("engagement:index_on_target",),
        limitations=(),
        result_id="diag:1",
    )
    with pytest.raises(ValueError) as refused:
        store.import_measurement("case-1", mismatching)
    assert getattr(refused.value, "code", None) == "result_condition_mismatch:compound"
    assert "does not match the planned action" in str(refused.value)


def test_a_registry_file_declaring_another_schema_is_refused(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"schema": "something.else", "capabilities": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="capability_registry_schema_unsupported"):
        load_capability_registry(path)


def _gated_case(tmp_path):
    """The fixture case with both a separating premise and a gate premise declared."""

    return _case(
        tmp_path,
        premise_registry={
            "abundance:target_rna": {
                "quantity": "rna_abundance",
                "entity": "ABL1",
                "units": "log2_tpm_plus_1",
                "context_identifier": "ACH-000551:K562",
            },
            "engagement:index_on_target": {
                "quantity": "engagement_shift",
                "entity": "ABL1@dasatinib",
                "units": "log2_shift",
                "context_identifier": "ACH-000551:K562",
                "require_direct_measurement": True,
            },
            "engagement:comparator_on_target": {
                "quantity": "engagement_shift",
                "entity": "ABL1@nilotinib",
                "units": "log2_shift",
                "context_identifier": "ACH-000551:K562",
                "require_direct_measurement": True,
            },
        },
        repair_outcome_templates={
            "engagement:index_on_target": {
                "insufficient_functional_perturbation": "not_engaged",
                "genetic_pharmacological_mode_non_equivalence": "engaged",
            },
            "engagement:comparator_on_target": {
                "insufficient_functional_perturbation": "engaged",
                "genetic_pharmacological_mode_non_equivalence": "engaged",
            },
        },
    )


def test_the_rule_arm_proposes_the_premise_whose_measurement_could_decide(tmp_path):
    """Directed means directed by the declaration: the separating premise comes first."""

    from evaluation.proposal_arms import RegistryRepairRulePolicy

    case, outcomes = _gated_case(tmp_path)
    registry = _registry(
        _offer(identifier="index_offer", supplies="engagement:index_on_target"),
        _offer(
            identifier="comparator_offer",
            supplies="engagement:comparator_on_target",
            compounds=("Nilotinib",),
        ),
    )
    environment = ReplayEnvironment(case, outcomes, capabilities=registry.public_payload())
    proposals = RegistryRepairRulePolicy().propose_repairs(environment.view())
    assert proposals, "the rule arm proposed nothing for a case with a missing separating premise"
    assert proposals[0]["supplies"] == "engagement:index_on_target"
    assert proposals[0]["capability"] == "index_offer"
    assert proposals[0]["compound"] == "dasatinib"


def test_the_proposal_round_admits_what_compiles_and_names_what_does_not(tmp_path):
    from evaluation.repair_replay import run_proposal_round

    case, outcomes = _gated_case(tmp_path)
    registry = _registry(_offer(identifier="index_offer", supplies="engagement:index_on_target"))
    environment = ReplayEnvironment(case, outcomes, capabilities=registry.public_payload())

    class TwoProposals:
        name = "two_proposals"

        def propose_repairs(self, view):
            return (
                {
                    "operator": "register_supplier",
                    "capability": "index_offer",
                    "supplies": "engagement:index_on_target",
                    "compound": "Nilotinib",
                    "entity": "ABL1",
                },
                {
                    "operator": "register_supplier",
                    "capability": "index_offer",
                    "supplies": "engagement:index_on_target",
                    "compound": "Dasatinib",
                    "entity": "ABL1",
                },
                {
                    "operator": "register_supplier",
                    "capability": "index_offer",
                    "supplies": "engagement:index_on_target",
                    "compound": "Dasatinib",
                    "entity": "ABL1",
                },
            )

    records = run_proposal_round(TwoProposals(), environment, registry)
    assert [record.admitted for record in records] == [False, True, False]
    # A compound the release never assayed, then the admissible proposal, then the same
    # proposal again: once a supplier is on the menu the premise is no longer missing, and
    # the repeat is refused for that reason rather than silently admitted twice.
    assert records[0].refusal == "capability_does_not_cover_compound"
    assert records[2].refusal == "premise_not_missing"
    assert environment.admitted_repairs == (
        canonical_repair_identifier("index_offer", "Dasatinib", "ABL1"),
    )


def test_without_a_registry_no_proposal_round_happens(tmp_path):
    from evaluation.repair_replay import run_proposal_round

    case, outcomes = _gated_case(tmp_path)
    environment = ReplayEnvironment(case, outcomes)

    class Proposer:
        name = "proposer"

        def propose_repairs(self, view):  # pragma: no cover - must not be called
            raise AssertionError("a run without a registry must not ask for proposals")

    assert run_proposal_round(Proposer(), environment, None) == ()


def test_registry_extended_case_only_adds_repairs_with_a_registered_result(tmp_path):
    from evaluation.repair_replay import registry_extended_case

    case, outcomes = _gated_case(tmp_path)
    registry = _registry(
        _offer(identifier="index_offer", supplies="engagement:index_on_target"),
        _offer(
            identifier="comparator_offer",
            supplies="engagement:comparator_on_target",
            compounds=("Nilotinib",),
        ),
    )
    extended, extended_outcomes = registry_extended_case(case, outcomes, registry)
    added = {item.action.identifier for item in extended.public.actions} - {
        item.action.identifier for item in case.public.actions
    }
    # The fixture registers a hidden result for the index repair only, so the comparator
    # repair compiles but adds nothing that could have been learned.
    assert added == {canonical_repair_identifier("index_offer", "Dasatinib", "ABL1")}
    assert set(extended_outcomes) - set(outcomes) == added
