"""Tests for the case memory: schema, append-only store, graph, cards, adaptation, retrieval and world.

File summary
- Path: research/scientific_case_memory/test_case_memory.py
- Purpose: pin each boundary the case memory relies on. Synthetic tests need no data. The integration
  tests use one real task (SciPlex3 tier A, fold 0) and prove the properties the evaluation depends on:
  the memory reproduces the reference world exactly, a snapshot contains no held-out compound, and no
  change to a held-out label can move the memory.
- Core points:
  - Schema, store, graph, evidence cards, protocol library, adaptation model and retrieval are tested
    with synthetic records.
  - Integration tests are skipped when the prepared data are absent.
- Run: python -m pytest research/scientific_case_memory -q
- Depends on: the package under test, numpy
"""
from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from . import adaptation_model as AM
from . import case_index as CI
from . import case_retrieval as CR
from . import case_schema as S
from . import case_store as CS
from . import evidence_cards as EC
from . import hypothesis_graph as HG
from . import protocol_library as PL

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64


def make_case(case_id="ds:T:c1", version=1, kind=S.CaseKind.CANONICAL, klass="A", compound="c1", codes="-1223", **kw):
    obs = (S.Observation("K1|024h|00100nM", S.MeasurementStatus.QUALIFIED, "rna", "K1", 24.0, 100.0,
                         "transcriptome_shift_norm", 1.2, 0.8, True),
           S.Observation("K2|024h|00100nM", S.MeasurementStatus.QC_FAILED, "rna", "K2", 24.0, 100.0))
    fields = dict(
        case_id=case_id, case_version=version, case_kind=kind, problem_type=S.ProblemType.MECHANISM_CONTRAST_TRANSCRIPTOMIC,
        problem_statement="Which class?", user_question="What next?",
        raw_data_references=(S.RawDataRef("x.npz", SHA, "state_vector", 3),), data_quality_report={"usable": True},
        context_fingerprint={"dataset": "ds", "assay": "rna", "context": "ds:T", "compound": compound, "unit": "u1",
                             "hypothesis_class": klass},
        initial_observations=obs,
        initial_hypotheses=(S.HypothesisClaim("own", "class A"), S.HypothesisClaim("decoy", "class B")),
        candidate_actions=(S.ActionSpec("K1|024h|00100nM", "d", "rna", 2.0, 6.0, "shift"),
                           S.ActionSpec("K2|024h|00100nM", "d", "rna", 2.0, 6.0, "shift")),
        retrieved_knowledge=(), virtual_cell_predictions=(), predicted_outcome_branches=(),
        real_measurements=(S.Measurement("K1|024h|00100nM", S.MeasurementStatus.QUALIFIED, "matches_own_class", 1),),
        measurement_quality={}, qualified_evidence=({"action_id": "K1|024h|00100nM"},),
        hypothesis_updates=(S.HypothesisUpdate("K1|024h|00100nM", ("A", "*pool*"), "r", ("B",), True,
                                               S.ReadingKind.CANONICAL, "", codes),),
        final_decision={"status": "decided", "basis": "annotation"}, next_action={}, failure_modes=(),
        adaptation_map=(), calibration_history=(),
        provenance={"builder": "test", "sources": {"x": SHA}, "created_at": "2026-09-29"})
    fields.update(kw)
    return S.Case(**fields)


# ------------------------------------------------------------------------------------------ schema
def test_well_formed_case_validates_and_round_trips_with_the_same_digest():
    case = make_case()
    assert S.validate_case(case) == ()
    again = S.case_from_dict(json.loads(json.dumps(S.to_dict(case))))
    assert S.digest(again) == S.digest(case)
    assert again == case


@pytest.mark.parametrize("change,error", [
    ({"provenance": {"builder": "x"}}, "missing:provenance.sources"),
    ({"raw_data_references": ()}, "missing:raw_data_references"),
    ({"candidate_actions": ()}, "missing:candidate_actions"),
    ({"final_decision": {"status": "maybe", "basis": "x"}}, "invalid:final_decision.status"),
    ({"final_decision": {"status": "decided"}}, "missing:final_decision.basis"),
    ({"initial_hypotheses": (S.HypothesisClaim("own", "x"),)}, "missing:two_registered_hypotheses"),
    ({"case_version": 2}, "missing:supersedes"),
    ({"supersedes": "abc"}, "invalid:first_version_supersedes"),
])
def test_case_validation_names_each_structural_error(change, error):
    assert error in S.validate_case(make_case(**change))


def test_a_value_without_a_biological_status_is_refused_so_missing_never_becomes_zero():
    bad = S.Observation("K2|024h|00100nM", S.MeasurementStatus.QC_FAILED, "rna", value=0.0)
    case = make_case(initial_observations=(bad,))
    assert any(e.startswith("value_without_biological_status") for e in S.validate_case(case))


def test_a_forecast_may_not_claim_measurement_status_and_must_normalise():
    forecast = S.ForecastRecord("K1|024h|00100nM", "own", {"a": 0.6, "b": 0.5}, 3, "m", "b",
                                evidence_class=S.EvidenceClass.QUALIFIED_EVIDENCE)
    errors = S.validate_case(make_case(virtual_cell_predictions=(forecast,)))
    assert any(e.startswith("forecast_claims_status") for e in errors)
    normalised = replace(forecast, branches={"a": 0.5, "b": 0.5}, evidence_class=S.EvidenceClass.MODEL_PREDICTION)
    assert S.validate_case(make_case(virtual_cell_predictions=(normalised,))) == ()
    skewed = replace(normalised, branches={"a": 0.5, "b": 0.4})
    assert any(e.startswith("forecast_not_normalised") for e in S.validate_case(make_case(virtual_cell_predictions=(skewed,))))


def test_qualified_evidence_needs_a_qualified_measurement():
    case = make_case(qualified_evidence=({"action_id": "K2|024h|00100nM"},))
    assert any(e.startswith("qualified_without_qualified_measurement") for e in S.validate_case(case))


def test_typed_kinds_require_their_contents():
    assert "adaptation_case_without_links" in S.validate_case(make_case(kind=S.CaseKind.ADAPTATION))
    assert "failure_case_without_failure_mode" in S.validate_case(make_case(kind=S.CaseKind.FAILURE))
    assert "contrastive_case_without_contrast" in S.validate_case(make_case(kind=S.CaseKind.CONTRASTIVE))
    link = S.AdaptationLink("a", "b", {"time": "far"}, ("cross_time_transfer",), 0.5, True)
    assert S.validate_case(make_case(kind=S.CaseKind.ADAPTATION, adaptation_map=(link,))) == ()
    unresolved = replace(link, success=None)
    assert "adaptation_link_incomplete" in S.validate_case(make_case(kind=S.CaseKind.ADAPTATION, adaptation_map=(unresolved,)))


def test_open_problem_refuses_a_failed_or_missing_measurement_reported_as_zero_and_any_truth_field():
    problem = S.OpenProblem("p", "human cell line", "A549", None, "drug", {"name": "x"}, None, "EGFR",
                            S.MeasurementStatus.PLANNED_MISSING, S.MeasurementStatus.NOT_PLANNED, 24.0, 100.0, "rna",
                            "vehicle", 2, None, (), {"HALLMARK_P53": 0.0}, None,
                            {"HALLMARK_P53": S.MeasurementStatus.QC_FAILED}, {"truth": "A"}, (), "decide")
    errors = S.validate_open_problem(problem)
    assert "missing_or_failed_reported_as_zero:HALLMARK_P53" in errors
    assert "truth_field_in_open_problem" in errors


# ------------------------------------------------------------------------------------------ store
def test_store_is_append_only_with_a_digest_chain(tmp_path):
    store = CS.CaseStore()
    c1 = make_case()
    assert store.append(c1) is True
    assert store.append(c1) is False  # identical content is a no-op
    with pytest.raises(CS.VersionConflict):
        store.append(replace(c1, problem_statement="edited in place"))
    c2 = store.supersede(c1, calibration_history=(S.CalibrationEntry("m", "K1", 0.4, 1.0),))
    assert c2.case_version == 2 and c2.supersedes == S.digest(c1)
    assert store.get("ds:T:c1").case_version == 2
    assert store.get("ds:T:c1", 1) == c1  # nothing was overwritten
    assert store.verify() == ()
    with pytest.raises(CS.VersionConflict):
        store.append(replace(c1, case_version=4, supersedes=S.digest(c2)))
    with pytest.raises(CS.VersionConflict):
        store.append(replace(c2, case_version=3, supersedes="0" * 64))


def test_store_detects_a_hand_edited_file_and_snapshots_are_order_independent(tmp_path):
    a, b = make_case("ds:T:a", compound="a"), make_case("ds:T:b", compound="b")
    s1, s2 = CS.CaseStore(), CS.CaseStore()
    s1.append_many([a, b])
    s2.append_many([b, a])
    assert s1.snapshot_digest() == s2.snapshot_digest()
    path = tmp_path / "cases.jsonl"
    persisted = CS.CaseStore(path)
    persisted.append(a)
    assert CS.CaseStore(path).ids() == ["ds:T:a"]
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0])
    row["case"]["problem_statement"] = "tampered"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(CS.StoreCorrupt):
        CS.CaseStore(path)


def test_snapshot_file_hash_is_reproducible_because_gzip_carries_no_timestamp(tmp_path):
    store = CS.CaseStore()
    store.append(make_case())
    first = store.write_snapshot(tmp_path / "a.jsonl.gz")
    second = store.write_snapshot(tmp_path / "b.jsonl.gz")
    assert first == second
    assert CS.CaseStore(tmp_path / "a.jsonl.gz").ids() == ["ds:T:c1"]


def test_an_invalid_case_is_refused_and_leaves_no_trace_in_the_store():
    store = CS.CaseStore()
    with pytest.raises(ValueError, match="invalid_case"):
        store.append(make_case(provenance={}))
    assert "ds:T:c1" not in store and len(store) == 0


# ------------------------------------------------------------------------------------------ graph
def _statuses(**kw):
    base = {"engagement": S.MeasurementStatus.NOT_PLANNED, "function": S.MeasurementStatus.NOT_PLANNED,
            "pathway": S.MeasurementStatus.QUALIFIED, "cell_state": S.MeasurementStatus.NOT_PLANNED,
            "phenotype": S.MeasurementStatus.UNDETECTED, "assay": S.MeasurementStatus.QUALIFIED}
    base.update(kw)
    return base


def test_template_graph_is_consistent_and_keeps_advisory_hypotheses_out_of_the_candidate_set():
    g = HG.template_for("p", "drugX", "EGFR", "A549", "rna", _statuses(),
                        action_ids=["matched_target_engagement", "orthogonal_context_control", "replicate_qc",
                                    "viability_phenotype"])
    assert g.validate() == ()
    assert [h.hypothesis_id for h in g.registered()] == ["H1", "H3"]
    assert {h.hypothesis_id for h in g.hypotheses if h.advisory} == {"H2", "H4", "H5"}
    assert "target_engagement" in g.unmeasured_layers()
    assert g.undistinguishable_pairs() == ()
    assert "matched_target_engagement" in g.distinguishing_actions("H1", "H3")
    assert all(edge.evidence_strength in ("predicted", "retrieved") for edge in g.edges[:3])


def test_graph_rejects_backward_edges_measured_claims_into_unmeasured_nodes_and_thin_hyperedges():
    nodes = [HG.Node("a", "intervention", "a", S.MeasurementStatus.QUALIFIED),
             HG.Node("b", "phenotype", "b", S.MeasurementStatus.NOT_PLANNED)]
    edge = HG.Edge("b", "a", "causes", "positive", "ctx", "24h", "rna", ("s",), "predicted", "u")
    assert any(e.startswith("edge_not_forward") for e in HG.HypothesisGraph(nodes, [edge]).validate())
    forward = HG.Edge("a", "b", "causes", "positive", "ctx", "24h", "rna", ("s",), "measured", "u")
    assert any(e.startswith("measured_edge_to_unmeasured_node") for e in HG.HypothesisGraph(nodes, [forward]).validate())
    hyper = HG.HyperEdge(("a",), "b", "causes", "dose x time", ("s",), "predicted", "u")
    assert any(e.startswith("hyperedge_needs_two_inputs") for e in HG.HypothesisGraph(nodes, [], [hyper]).validate())
    bare = HG.Edge("a", "b", "causes", "positive", "", "24h", "rna", (), "predicted", "u")
    errors = HG.HypothesisGraph(nodes, [bare]).validate()
    assert "missing:context:a->b" in errors and "missing:evidence_sources:a->b" in errors


def test_graph_names_hypothesis_pairs_no_action_can_separate():
    nodes = [HG.Node("i", "intervention", "i", S.MeasurementStatus.QUALIFIED),
             HG.Node("o", "observed_assay", "o", S.MeasurementStatus.QUALIFIED)]
    hyps = [HG.Hypothesis("H1", "x", ("i", "o"), predicted={"act": "up"}),
            HG.Hypothesis("H2", "y", ("i", "o"), predicted={"act": "up"})]
    g = HG.HypothesisGraph(nodes, [], [], hyps)
    assert g.undistinguishable_pairs() == (("H1", "H2"),)


# ------------------------------------------------------------------------------------------ cards
def test_only_a_real_qc_passed_eliminating_reading_is_qualified_evidence():
    assert EC.classify(real_measurement=True, qc_passed=True, eliminated=True) is S.EvidenceClass.QUALIFIED_EVIDENCE
    assert EC.classify(real_measurement=True, qc_passed=False, eliminated=True) is S.EvidenceClass.MEASURED_FACT
    assert EC.classify(real_measurement=True, qc_passed=True, eliminated=False) is S.EvidenceClass.MEASURED_FACT
    assert EC.classify(real_measurement=False, qc_passed=None, eliminated=False, from_model=True) is S.EvidenceClass.MODEL_PREDICTION
    assert EC.classify(real_measurement=False, qc_passed=None, eliminated=False, from_case=True) is S.EvidenceClass.HISTORICAL_ANALOGY
    ledger = EC.EvidenceLedger()
    with pytest.raises(EC.PromotionRefused):
        ledger.add(EC.EvidenceCard("x", S.EvidenceClass.QUALIFIED_EVIDENCE, "s", "src", "a", S.MeasurementStatus.AMBIGUOUS))
    with pytest.raises(EC.PromotionRefused):
        ledger.add(EC.EvidenceCard("y", S.EvidenceClass.MODEL_PREDICTION, "s", "src", "a", S.MeasurementStatus.QUALIFIED))


def test_cards_from_runner_steps_never_promote_a_failed_or_missing_measurement():
    qc = {"state": "quality_failed", "action": "a1", "qc": False, "eliminated": []}
    card = EC.card_from_step("c", qc, ("A", "B"))
    assert card.status is S.MeasurementStatus.QC_FAILED and card.evidence_class is S.EvidenceClass.MEASURED_FACT
    assert EC.card_from_step("c", {"state": "not_measured", "action": "a2"}, ("A", "B")) is None
    good = {"state": "measured_eliminating", "action": "a3", "qc": True, "eliminated": ["B"], "readout": "eliminating"}
    ledger = EC.EvidenceLedger()
    ledger.add(EC.card_from_step("c", good, ("A", "B"), 2))
    assert ledger.qualified_eliminations() == frozenset({"B"})
    assert ledger.abstention_reasons(["A", "B"]) == ()
    assert "more_than_one_hypothesis_compatible_with_qualified_evidence" in EC.EvidenceLedger().abstention_reasons(["A", "B"])


# ------------------------------------------------------------------------------------------ protocol
def test_protocol_costs_reproduce_the_runners_well_and_day_sums():
    keys = [("K1", 24.0, 100.0), ("K1", 24.0, 1000.0), ("K2", 24.0, 100.0)]
    days, wells = PL.plan_cost(keys, lambda k: 6.0)
    assert (days, wells) == (18.0, 3 * 2 + 4 * 2)  # two vehicle groups, shared across doses
    lib = PL.build_protocol_library(keys, lambda k: 6.0, assay="rna", detected_at={keys[0]: (9, 10), keys[1]: (2, 3)},
                                    planned=keys[:2])
    assert lib[0].detection_power == 0.9  # enough references
    assert lib[1].detection_power is None  # too few references: no power is claimed
    assert lib[2].available is False and lib[2].to_action_spec().available is False
    assert lib[0].action_id == "K1|024h|00100nM"


# ------------------------------------------------------------------------------------------ adaptation
def _ctx(**kw):
    base = dict(dataset="d", assay="rna", cell_line="A", time_h=24.0, dose_nM=100.0)
    base.update(kw)
    return AM.Context(**base)


def test_difference_signatures_and_operations():
    same = AM.differences(_ctx(), _ctx())
    assert AM.signature(same) == (False, False, "same", "same", None) or AM.signature(same)[:4] == (False, False, "same", "same")
    diff = AM.differences(_ctx(), _ctx(cell_line="B", time_h=72.0, dose_nM=10000.0))
    assert diff["cell_line"] is True and diff["time"] == "near" and diff["dose"] == "far"
    assert set(AM.operations_for(diff)) == {"cross_cell_line_transfer", "cross_time_transfer", "cross_dose_transfer"}
    assert AM.operations_for(same) == ("same_condition_transfer",)


def test_cost_is_zero_at_zero_difference_and_priced_from_history_only_when_supported():
    table = AM.AdaptationTable(chance=0.25)
    zero = AM.differences(_ctx(), _ctx())
    far = AM.differences(_ctx(), _ctx(cell_line="B", dose_nM=10000.0))
    table.add_bulk(AM.signature(zero), 60, 100)
    unsupported = table.cost(far)
    assert unsupported.supported is False and unsupported.reason.startswith("declared_prior")
    assert unsupported.cost == pytest.approx(AM.PRIOR_COST_PER_DIFFERENCE * 2)
    table.add_bulk(AM.signature(far), 28, 100)  # success 0.28, within 0.05 of chance 0.25
    priced = table.cost(far)
    assert priced.supported is True and 0.8 < priced.cost <= 1.0
    assert table.cost(zero).cost == 0.0
    assert AM._sig_text(AM.signature(far)) in table.failed_when()
    assert AM._sig_text(AM.signature(zero)) in table.valid_when()


def test_link_records_source_target_differences_operations_and_priced_cost():
    table = AM.AdaptationTable()
    link = AM.make_link("s", "t", _ctx(), _ctx(time_h=72.0), table, True)
    assert link.source_case == "s" and link.success is True and link.operations == ("cross_time_transfer",)
    assert link.differences["time"] == "near" and 0.0 < link.cost <= 1.0


def test_transition_matrix_rows_are_distributions_and_ignore_unscored_readings():
    src = np.array([0, 0, 1, -1, 2, 3])
    tgt = np.array([0, 1, 1, 2, -1, 3])
    m = AM.transition_matrix(src, tgt)
    assert m.shape == (4, 4) and np.allclose(m.sum(1), 1.0)
    assert m[0, 0] > 0.0 and m[3, 3] > m[3, 0]


# ------------------------------------------------------------------------------------------ index and filter
def test_codes_round_trip_and_masking_removes_only_the_named_readings():
    codes = np.array([0, 1, 2, 3, -1])
    assert (CI.decode_codes(CI.encode_codes(codes)) == codes).all()
    cases = [make_case(f"ds:T:{n}", compound=n, klass=k, codes=c) for n, k, c in
             (("a", "A", "-1233"), ("b", "A", "-0233"), ("c", "B", "1-23"))]
    index = CI.CaseIndex.from_cases(cases, ("A", "B", "C", "D"), [("K1", 24.0, 100.0)])
    masked = index.masked((1,))
    table, mtable = index.tables[("K1", 24.0, 100.0)], masked.tables[("K1", 24.0, 100.0)]
    assert (table.code == 1).any() and not (mtable.code == 1).any()
    assert ((mtable.code == 3) == (table.code == 3)).all()
    assert index.reading_kind_counts()["misleading"] >= 1


def test_hard_filter_excludes_incompatible_cases_with_a_named_reason():
    case = make_case()
    fp = dict(case.context_fingerprint, measurement_type="transcriptome_shift", control_design="matched_vehicle")
    case = replace(case, context_fingerprint=fp)
    assert CI.hard_filter({"assay": "rna"}, case) == (True, None)
    ok, reason = CI.hard_filter({"assay": "proteomics"}, case)
    assert not ok and reason.startswith("incompatible_assay")
    assert CI.hard_filter({"control_design": "no_control"}, case)[1].startswith("incompatible_control_design")
    unusable = replace(case, data_quality_report={"usable": False})
    assert CI.hard_filter({}, unusable) == (False, "case_marked_unusable")


# ------------------------------------------------------------------------------------------ retrieval terms
def test_case_score_is_the_specified_sum_and_the_modifier_is_bounded():
    n = 3
    c = {k: np.full(n, v) for k, v in dict(state_similarity=0.5, mechanism_compatibility=0.6, assay_compatibility=1.0,
                                           temporal_compatibility=1.0, evidence_quality=0.4, historical_reliability=0.7,
                                           adaptation_cost=0.1, domain_shift=0.3, measurement_mismatch=0.0).items()}
    score = CR.PrecedentScorer.case_score(c)
    assert np.allclose(score, 0.5 + 0.6 + 1 + 1 + 0.4 + 0.7 - 0.1 - 0.3 - 0.0)
    assert np.all((0.0 <= CR.PrecedentScorer.modifier(c)) & (CR.PrecedentScorer.modifier(c) <= 1.0))
    assert set(CR.SCORE_TERMS) == {"state_similarity", "mechanism_compatibility", "assay_compatibility",
                                   "temporal_compatibility", "evidence_quality", "historical_reliability",
                                   "adaptation_cost", "domain_shift", "measurement_mismatch"}


def test_kernel_floor_matches_the_registered_reference_floor():
    from research.belief_planning import world as W
    assert CR.SIM_FLOOR == W.SIM_FLOOR
    assert CR.kernel(np.array([0.39, 0.40, 1.0])).tolist() == [0.0, 0.0, 1.0]
    from research.scientific_case_memory import world as CW
    assert CW.MIN_SUPPORT == 6 and CW.PRIOR_BOUND == 0.95


# ------------------------------------------------------------------------------------------ integration
@pytest.fixture(scope="module")
def task():
    pytest.importorskip("rdkit")
    prepared = ROOT / "outputs/dynamic_world_model_20260926/prepared/shifts.npz"
    if not prepared.exists() or not (ROOT / "data/raw/sciplex3").exists():
        pytest.skip("prepared SciPlex3 data are absent")
    from . import build_cases as BC
    inputs = BC.load_inputs("sciplex3", "A", 0)
    return inputs, BC.build_snapshot(inputs, created_at="2026-09-29")


def test_snapshot_contains_no_heldout_compound_and_no_unit_overlap(task):
    inputs, snap = task
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 0])
    heldout_units = {inputs.unit_of[c] for c in heldout if c in inputs.unit_of}
    refs = [c for c in snap.store.latest() if c.case_kind is not S.CaseKind.ADAPTATION]
    assert refs and not ({c.context_fingerprint["compound"] for c in refs} & heldout)
    assert not ({c.context_fingerprint["unit"] for c in refs} & heldout_units)
    assert snap.store.verify() == ()
    assert all(S.validate_case(c) == () for c in snap.store.latest())


def test_snapshot_is_invariant_to_any_change_of_heldout_labels_structures_and_units(task):
    from . import build_cases as BC
    inputs, snap = task
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 0])
    altered = copy.copy(inputs)
    altered.klass_of = {c: ("zzz" if c in heldout else k) for c, k in inputs.klass_of.items()}
    altered.unit_of = {c: ("u-" + c if c in heldout else u) for c, u in inputs.unit_of.items()}
    altered.smiles_of = {c: ("C" if c in heldout else s) for c, s in inputs.smiles_of.items()}
    again = BC.build_snapshot(altered, created_at="2026-09-29")
    assert again.manifest["digest"] == snap.manifest["digest"]


def test_all_four_case_kinds_are_present_or_absent_for_a_named_reason(task):
    _, snap = task
    kinds = snap.manifest["kinds"]
    assert kinds.get("canonical", 0) > 0 and kinds.get("failure", 0) > 0 and kinds.get("adaptation", 0) > 0
    failures = [c for c in snap.store.latest() if c.case_kind is S.CaseKind.FAILURE]
    assert all(any(m.severity == "major" for m in c.failure_modes) for c in failures)
    reading = snap.manifest["reading_kinds"]
    assert reading["negative"] > 0 and reading["misleading"] > 0  # negative and failure precedents are kept


def test_a_qc_failed_condition_is_a_status_never_a_zero(task):
    _, snap = task
    for case in snap.store.latest():
        for o in case.initial_observations:
            if o.status in (S.MeasurementStatus.QC_FAILED, S.MeasurementStatus.NOT_PLANNED):
                assert o.value is None and o.readout is None


def test_case_memory_world_reproduces_the_reference_world_exactly(task):
    from research.belief_planning import arms as BA
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import tasks_v21 as V

    from . import world as CW
    inputs, snap = task
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 0])
    view = K.public_view(inputs.ctx, heldout, training_compounds=inputs.training, design=inputs.design)
    assert K.public_view_problems(view, heldout) == []
    episodes = V.episode_list(inputs.ctx, 0)[:150]
    for name, vc in (("similarity", "on"), ("class", "masked")):
        ref = BA.world_for(view, vc, "true")
        cm = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS[name], vc=vc)
        assert {k: ref.hyperparameters[k] for k in "sek"} == {k: cm.hyperparameters[k] for k in "sek"}
        for compound, _truth, _decoy, h1, h2 in episodes:
            for key in inputs.ctx.tier.keys:
                a, b = ref.forecast(key, h1, h2, compound, ()), cm.forecast(key, h1, h2, compound, ())
                assert bool(a.refusal) == bool(b.refusal)
                for x, y in zip(a.branches, b.branches):
                    assert x.support == y.support
                    assert all(abs(x.probabilities[k] - y.probabilities[k]) < 1e-12 for k in x.probabilities)


def test_forecasts_are_cached_by_full_identity_and_history_changes_them(task):
    from research.belief_planning import world as W
    from research.protocol_v2 import tasks_v21 as V

    from . import world as CW
    inputs, snap = task
    world = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_full"])
    compound, _truth, _decoy, h1, h2 = V.episode_list(inputs.ctx, 0)[0]
    keys = list(inputs.ctx.tier.keys)
    first = world.forecast(keys[0], h1, h2, compound, ())
    assert world.forecast(keys[0], h1, h2, compound, ()) is first
    other = world.forecast(keys[0], h1, h2, compound, ((keys[1], W.ABSENT),))
    assert other is not first
    assert first.evidence_kind.value == "model_prediction" and first.model_version == CW.MODEL_VERSION


def test_removing_failure_and_negative_cases_makes_the_forecast_overconfident(task):
    from . import world as CW
    inputs, snap = task
    full = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_full"])
    nofail = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_nofail"])
    key = inputs.ctx.tier.keys[0]
    entry_full, entry_nofail = full.keys[key], nofail.keys[key]
    assert (entry_full["cat"] == 3).any() and not (entry_nofail["cat"] == 3).any()
    assert not (entry_nofail["cat"] == 1).any()
    assert entry_nofail["pooled"][3] < 0.01 < entry_full["pooled"][3]


def test_prior_is_advisory_bounded_and_uniform_without_a_neighbour(task):
    from research.protocol_v2 import tasks_v21 as V

    from . import world as CW
    inputs, snap = task
    world = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_full_prior"])
    seen = set()
    for compound, _t, _d, h1, h2 in V.episode_list(inputs.ctx, 0):
        p = world.hypothesis_prior(compound, h1, h2)
        assert abs(sum(p.values()) - 1.0) < 1e-12
        assert 1 - CW.PRIOR_BOUND - 1e-12 <= p[h1] <= CW.PRIOR_BOUND + 1e-12
        seen.add(round(p[h1], 3))
    assert 0.5 in seen and len(seen) > 3
    plain = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_full"])
    assert plain.hypothesis_prior("x", "A", "B") == {"A": 0.5, "B": 0.5}


def test_retrieval_returns_stage_counts_reasons_and_named_terms(task):
    from research.protocol_v2 import tasks_v21 as V

    from . import world as CW
    inputs, snap = task
    world = CW.CaseMemoryWorld(snap.index, inputs.ctx.params, inputs.training, config=CW.CONFIGS["cm_full"],
                               context=AM.Context("sciplex3", "transcriptome"), adaptation=snap.adaptation)
    compound, _t, _d, h1, h2 = V.episode_list(inputs.ctx, 0)[0]
    key = inputs.ctx.tier.keys[0]
    fp = world.fp[world.pos[compound]]
    query = CR.RetrievalQuery(compound, key, (h1, h2), AM.Context("sciplex3", "transcriptome", key[0], key[1], key[2]), fp,
                              inputs.unit_of.get(compound), {"assay": snap.cases()[0].context_fingerprint["assay"]})
    out = world.retriever.retrieve(query, top_k=3)
    assert out["stage1"]["eligible"] > 0
    assert set(out["hypotheses"]) == {h1, h2}
    for hyp in (h1, h2):
        entry = out["hypotheses"][hyp]
        for case in entry["cases"]:
            assert set(case.components) == set(CR.SCORE_TERMS)
            assert case.adaptation["cost"] >= 0.0 and "operations" in case.adaptation
            assert case.hypothesis == hyp
    blocked = world.retriever.retrieve(replace(query, problem={"assay": "proteomics"}), top_k=3)
    assert blocked["stage1"]["eligible"] == 0 and blocked["stage1"]["reasons"]


# ------------------------------------------------------------------------------------------ audit and replay integrity
def test_the_audit_catches_planted_leaks_duplicates_and_bad_codes():
    from . import case_quality_audit as QA

    pool = ("A", "B", "C", "D")
    a = make_case("ds:T:a", compound="a", klass="A", codes="-123")
    twin = make_case("ds:T:twin", compound="twin", klass="A", codes="-123")  # identical content, another id
    own = make_case("ds:T:own", compound="own", klass="A", codes="0123")     # scored against its own class
    short = make_case("ds:T:short", compound="short", klass="B", codes="1-")
    bad = make_case("ds:T:bad", compound="bad", klass="B", codes="1x23")
    report = QA.audit_cases([a, twin, own, short, bad], pool=pool, heldout_compounds={"a"}, heldout_units={"u1"})
    checks = report["checks"]
    assert not report["passed"]
    assert checks["heldout_compound"]["failures"] == 1 and checks["heldout_unit"]["failures"] == 5
    assert checks["duplicate_content"]["failures"] >= 1
    assert any("own_class" in f for f in checks["reading_codes"]["examples"] + [str(x) for x in checks["reading_codes"]["examples"]])
    assert checks["reading_codes"]["failures"] >= 3
    clean = QA.audit_cases([a], pool=pool)
    assert clean["passed"] and clean["balance"]["case_kinds"] == {"canonical": 1}


def test_the_audit_sees_a_success_only_memory_and_a_broken_version_chain():
    from . import case_quality_audit as QA

    only_success = make_case("ds:T:s", codes="-000")
    balance = QA.kind_balance([only_success])
    assert balance["failure_share"] == 0.0 and balance["reading_kinds"]["misleading"] == 0
    v1 = make_case("ds:T:v")
    v2 = replace(v1, case_version=2, supersedes="0" * 64)
    assert QA.audit_cases([v1, v2])["checks"]["version_chain"]["failures"] == 1


def test_replay_integrity_flags_leaked_fields_mismatched_menus_and_orphans_and_the_probe_catches_a_leaky_builder():
    from . import build_episode_replay as ER

    policy = {"episode_id": "e", "menu": ["a1", "a2"], "initial_hypotheses": ["A", "B"], "snapshot_digest": "d" * 64}
    evaluator = {"episode_id": "e", "available_actions": ["a1", "a2"], "truth": "A", "observed_outcome": {"a1": "x", "a2": "y"}}
    assert ER.verify_replay_integrity([policy], [evaluator]) == []
    assert any(p.startswith("policy_record_names_hidden_fields") for p in ER.verify_replay_integrity([dict(policy, truth="A")], [evaluator]))
    assert any(p.startswith("menu_differs") for p in ER.verify_replay_integrity([dict(policy, menu=["a1"])], [evaluator]))
    assert any(p.startswith("truth_outside_contrast") for p in ER.verify_replay_integrity([policy], [dict(evaluator, truth="Z")]))
    assert any(p.startswith("menu_action_without_outcome") for p in ER.verify_replay_integrity([policy], [dict(evaluator, observed_outcome={"a1": "x"})]))
    assert any(p.startswith("evaluator_episode_without_policy_record") for p in ER.verify_replay_integrity([], [evaluator]))

    honest = lambda e: {"episode_id": e["episode_id"], "menu": e["available_actions"]}  # noqa: E731
    leaky = lambda e: {"episode_id": e["episode_id"], "menu": e["available_actions"], "hint": e["truth"]}  # noqa: E731
    assert ER.leak_probe(honest, evaluator) is True
    assert ER.leak_probe(leaky, evaluator) is False
    assert len(ER.REPLAY_STEPS) == 9
