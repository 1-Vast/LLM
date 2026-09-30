"""Tests for the MAESTRO-VC v1 data layer, views, second case family and decision-support system.

File summary
- Path: research/maestro_vc_v1/test_maestro_vc_v1.py
- Purpose: pin the boundaries the closed loop depends on: verified-or-unverified provenance, identifier
  and control validation, the policy/evaluator separation, typed measurement status in the tables, the
  second case family's structure, and the system's handling of positive, negative, ambiguous,
  invalid and missing results.
- Core points:
  - Synthetic tests need no data; integration tests use SciPlex3 tier B fold 0 and the prepared releases
    and are skipped when those are absent.
  - The invariance test is the leakage guard: changing every truth in an episode leaves the policy view
    byte-identical.
- Run: python -m pytest research/maestro_vc_v1 -q
- Depends on: the package under test, numpy, pandas
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.scientific_case_memory import case_schema as S

from . import family2 as F2
from . import preprocess as PP
from . import sources as SRC
from . import views as V

ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------------------------------ sources
def test_source_records_state_only_what_is_verified(tmp_path):
    data = tmp_path / "x.csv"
    data.write_text("a,b\n1,2\n", encoding="utf-8")
    prov = tmp_path / "x.csv.provenance.json"
    prov.write_text(json.dumps({"source_url": "https://example.org/x", "retrieved_at_utc": "2026-01-01", "licence": "CC BY 4.0"}),
                    encoding="utf-8")
    record = SRC.collect([{"id": "x", "path": "x.csv", "role": "r", "provenance": "x.csv.provenance.json"},
                          {"id": "y", "path": "y.csv", "role": "r"}], root=tmp_path)
    x, y = record
    assert x["url"] == "https://example.org/x" and x["licence"] == "CC BY 4.0" and x["download_date"] == "2026-01-01"
    assert x["sha256"] == SRC.sha256_file(data) and x["checksum_source"] == "computed"
    assert x["schema"]["columns"] == ["a", "b"]
    assert y["exists"] is False and y["licence"] == SRC.UNVERIFIED and y["url"] == SRC.UNVERIFIED


def test_the_repository_registry_uses_the_unverified_marker_never_a_guess():
    ids = {s["id"] for s in SRC.SOURCES}
    assert {"sciplex3", "hgnc", "prism_secondary", "reactome", "case_package_real_v3"} <= ids
    kinobeads = next(s for s in SRC.SOURCES if s["id"] == "kinobeads")
    assert kinobeads["licence"] == SRC.UNVERIFIED and kinobeads["limitations"]
    assert all(s["limitations"] for s in SRC.SOURCES)


# ------------------------------------------------------------------------------------------ preprocess
def _means(offset_labels):
    """Context means in which marker gene j peaks in its own context, columns laid out per `offset_labels`."""
    from virtual_cell import artifacts as IM

    labels = list(offset_labels)
    means = {c: np.ones(len(labels)) for c in IM.IDENTITY_MARKERS}
    for context, genes in IM.IDENTITY_MARKERS.items():
        for g in genes:
            if g in labels:
                means[context][labels.index(g)] = 50.0
    return means


def test_feature_label_check_accepts_aligned_labels_and_recovers_a_one_row_shift():
    from virtual_cell import artifacts as IM

    genes = [g for gs in IM.IDENTITY_MARKERS.values() for g in gs] + [f"G{i}" for i in range(20)]
    means = _means(genes)
    ok = PP.check_feature_labels(means, genes)
    assert ok["status"] == PP.PASS and ok["chosen_offset"] == 0
    shifted = ["<stray header>"] + genes[:-1]  # every label one row late, as the raw SciPlex3 release publishes them
    bad = PP.check_feature_labels(means, shifted)
    assert bad["chosen_offset"] == 1 and bad["status"] == PP.FAIL  # found, and refused at offset 0
    junk = PP.check_feature_labels(means, [f"J{i}" for i in range(len(genes))])
    assert junk["status"] == PP.INCONCLUSIVE and junk["refusal"]


def test_inchikey_is_recomputed_from_structure():
    assert PP.inchikey_of("CC(=O)Oc1ccccc1C(=O)O") == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"  # aspirin, as PubChem reports it
    assert PP.inchikey_of("not a structure") is None and PP.inchikey_of(None) is None
    frame = pd.DataFrame({"compound": ["a", "b", "c"], "smiles": ["CC(=O)Oc1ccccc1C(=O)O", "???", None],
                          "unit": ["BSYNRYMUTXBXSQ", "X", "Y"]})
    report = PP.check_compounds(frame, stored_block="unit")
    assert report["status"] == PP.FAIL and report["unparsable"] == ["b"] and report["without_structure"] >= 1


def test_gene_ids_are_joined_to_hgnc_and_disagreements_are_reported():
    hgnc = pd.DataFrame({"symbol": ["TP53", "EGFR"], "entrez_id": ["7157", "1956"], "ensembl_gene_id": ["ENSG1", "ENSG2"]})
    good = pd.DataFrame({"symbol": ["TP53", "EGFR"], "entrez": [7157, 1956], "ensembl": ["ENSG1", "ENSG2"]})
    assert PP.check_gene_ids(good, hgnc)["status"] == PP.PASS
    bad = pd.DataFrame({"symbol": ["TP53", "NOTAGENE"], "entrez": [1, 9], "ensembl": ["ENSG1", "ENSGX"]})
    report = PP.check_gene_ids(bad, hgnc)
    assert report["status"] == PP.FAIL and report["unmatched"] == ["NOTAGENE"] and report["entrez_disagree"] == 1


def test_controls_conditions_and_splits_are_checked():
    wells = pd.DataFrame({"cell_line": ["A", "A", "A"], "time": [24, 24, 24], "is_control": [True, True, True],
                          "dose": [0, 0, 5]})
    cond = pd.DataFrame({"cell_line": ["A", "B"], "time": [24, 24], "dose": [10, 10]})
    report = PP.check_controls(wells, cond)
    assert report["status"] == PP.FAIL and report["controls_with_dose"] == 1 and ["B", "24"] in report["unmatched_groups"]
    assert PP.check_conditions(pd.DataFrame({"time": [24, -1], "dose": [10, 0]}))["status"] == PP.FAIL
    compounds = pd.DataFrame({"unit": ["u1", "u1", "u2"], "fold": [0, 1, 2], "identity": ["i", "j", "k"],
                              "scaffold": ["s", "s", "t"]})
    split = PP.check_splits(compounds, unit="unit")
    assert split["status"] == PP.FAIL and split["units_spanning_folds"] == 1 and split["scaffolds_across_folds"] == 1


# ------------------------------------------------------------------------------------------ views
def _episode(truth="A"):
    return {"episode_id": "d|T|f0|c|A|B", "dataset": "d", "tier": "T", "compound": "c", "unit": "u",
            "initial_hypotheses": ["A", "B"], "available_actions": ["K1|024h|00100nM", "K2|024h|00100nM"],
            "truth": truth, "observed_outcome": {"K1|024h|00100nM": "eliminate_b"}, "history_by_arm": {"fixed": {}},
            "evaluation_split": "fold_0", "nn_class": truth, "klass": truth}


SETTING = {"days": {"K1|024h|00100nM": 6.0, "K2|024h|00100nM": 6.0}, "max_measurements": 2, "budget_days": 16.0}


def test_policy_view_is_invariant_to_every_truth_label_and_outcome():
    a = V.policy_view(_episode("A"), SETTING, smiles={"c": "CCO"}, snapshot_digest="d" * 64, training_references=10)
    other = _episode("B")
    other["observed_outcome"] = {"K1|024h|00100nM": "undetected"}
    other["history_by_arm"] = {"oracle": {"terminal_decision": "wrong"}}
    b = V.policy_view(other, SETTING, smiles={"c": "CCO"}, snapshot_digest="d" * 64, training_references=10)
    assert V.view_digest(a) == V.view_digest(b)
    assert set(a) == set(V.POLICY_KEYS) and V.audit_policy_records([a]) == []
    assert V.evaluator_view(_episode("A"))["truth"] == "A"


def test_audit_names_leaks_unknown_keys_and_empty_menus():
    good = V.policy_view(_episode(), SETTING, smiles={}, snapshot_digest="d" * 64, training_references=1)
    leaky = dict(good, truth="A", extra=1)
    leaky["menu_days"] = {"outcome": 1.0}
    problems = V.audit_policy_records([leaky, dict(good, menu=[])])
    assert any(p.startswith("unknown_keys") for p in problems) and any(p.startswith("forbidden_key") for p in problems)
    assert any(p.startswith("empty_menu") for p in problems)


# ------------------------------------------------------------------------------------------ family two
@pytest.fixture(scope="module")
def family2():
    if not F2.MANIFEST.exists() or not (ROOT / "data/raw/depmap/Model.csv").exists():
        pytest.skip("case packages or DepMap metadata absent")
    return F2.build_store()


def test_second_family_cases_are_structured_typed_and_leave_registered_hypotheses_unchanged(family2):
    cases = family2.latest()
    assert len(cases) == 64 and family2.verify() == ()
    kinds = {c.case_kind for c in cases}
    assert kinds == {S.CaseKind.CANONICAL, S.CaseKind.CONTRASTIVE, S.CaseKind.FAILURE}
    for c in cases:
        registered = [h for h in c.initial_hypotheses if not h.advisory]
        assert len(registered) == 2 and any(h.advisory for h in c.initial_hypotheses)
        assert "target_engagement" in c.provenance["graph"]["unmeasured_layers"]
        assert c.final_decision["basis"].startswith("declared evidence-sufficiency rule")
    failures = [c for c in cases if c.case_kind is S.CaseKind.FAILURE]
    assert failures and all(c.failure_modes[0].severity == "major" for c in failures)
    assert any(a.available is False for c in cases for a in c.candidate_actions)  # a needed measurement is unavailable


def test_processed_records_are_never_promoted_to_qualified_evidence(family2):
    for c in family2.latest():
        for m in c.real_measurements:
            if m.status is S.MeasurementStatus.QUALIFIED:
                assert any(card["action_id"] == m.action_id for card in c.qualified_evidence)
        assert all(o.status is not S.MeasurementStatus.QUALIFIED for o in c.initial_observations
                   if "gene-effect" in o.condition_id or "prism" in o.condition_id)


def test_semantic_similarity_does_not_recover_the_evidence_pattern(family2):
    result = F2.evaluate_retrieval(family2.latest())
    assert result["cases"] == 58 and result["genes"] == 40
    semantic = result["retrievers"]["semantic"]["pattern_accuracy"]
    assert semantic < result["majority_pattern_share"] + 0.05  # no better than always guessing the commonest pattern
    assert result["semantic_neighbour_shares_pattern"] < 0.3


# ------------------------------------------------------------------------------------------ tables
def test_state_table_never_turns_a_missing_or_failed_condition_into_a_value():
    if not (ROOT / "outputs/dynamic_world_model_20260926/prepared/conditions.csv").exists():
        pytest.skip("prepared data absent")
    from . import tables as T

    state = T.state_table("sciplex3")
    assert list(state.columns) == T.STATE_COLUMNS
    assert set(state.measurement_status) <= {"planned_missing", "qc_failed", "undetected", "qualified"}
    missing = state[state.measurement_status.isin(["planned_missing", "qc_failed"])]
    assert (missing.state_vector_uri.isna() | missing.measurement_status.eq("qc_failed")).all()
    assert state[state.measurement_status == "planned_missing"].state_vector_uri.isna().all()
    assert state.dose_realized.isna().all()  # nominal dose only; realised dose is not recorded in the release
    assert state.unit_id.is_unique and (state.dose_nominal > 0).all()
    measured = state[state.measurement_status.isin(["qualified", "undetected"])]
    assert measured.qc_status.eq("pass").all() and measured.replicate_count.eq(2).all()


# ------------------------------------------------------------------------------------------ system
@pytest.fixture(scope="module")
def system():
    if not (ROOT / "outputs/dynamic_world_model_20260926/prepared/shifts.npz").exists():
        pytest.skip("prepared SciPlex3 data absent")
    pytest.importorskip("rdkit")
    from research.scientific_case_memory import build_cases as BC

    from . import system as SY
    inputs = BC.load_inputs("sciplex3", "B", 0)
    snap = BC.build_snapshot(inputs, created_at="2026-09-29")
    return SY, inputs, snap, SY.DecisionSupport(inputs, snap)


def _problem(system, index=3, history=()):
    from research.protocol_v2 import tasks_v21 as V21
    SY, inputs, snap, ds = system
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    c, truth, _decoy, h1, h2 = V21.episode_list(inputs.ctx, 0)[index]
    return SY.UserProblem(c, comp.smiles.get(c), (h1, h2), tuple(history), unit=inputs.unit_of.get(c)), truth


def test_answer_has_every_section_names_its_assumptions_and_never_lets_a_forecast_eliminate(system):
    SY, _inputs, snap, ds = system
    problem, _truth = _problem(system)
    report = ds.answer(problem)
    text = ds.render(problem, report)
    for heading in ("## 1. Current data assessment", "## 2. Competing hypotheses", "## 3. Retrieved precedent cases",
                    "## 4. Virtual-cell forecast", "## 5. Recommended next action", "## 6. Branching interpretation plan",
                    "## 7. Confidence and abstention"):
        assert heading in text
    assert report.recommendation["action"] and report.recommendation["cost_wells"] > 0
    cases = {b["case"] for b in report.branches}
    assert {"positive", "ambiguous", "negative", "technically_invalid", "missing_result"} <= cases | {"contradictory_to_precedent"}
    assert all(f["evidence_class"] == "model_prediction" and f["calibration_status"] == "uncalibrated_on_held_out_units"
               for f in report.forecasts if "hypothesis" in f)
    assert report.assessment["history"] == [] and report.confidence["qualified_evidence"] == []
    hypotheses = {h["hypothesis_id"]: h["advisory"] for h in report.graph["hypotheses"]}
    assert hypotheses["H_a"] is False and hypotheses["H_b"] is False and hypotheses["H_artifact"] is True
    assert problem.name not in snap.index.cases  # the user's compound is never a reference


def test_out_of_domain_compound_is_flagged_and_the_answer_says_what_it_cannot_infer(system):
    _SY, _inputs, _snap, ds = system
    problem, _ = _problem(system)
    report = ds.answer(problem)
    if not report.assessment["in_distribution"]:
        assert report.abstention is not None
        assert any("applicability" in r for r in report.abstention["reasons"])
        assert "structural precedent" in " ".join(report.assessment["cannot_be_inferred"])
        assert report.abstention["minimum_informative_next_action"] and report.abstention["decision_rule_after_each"]


def test_a_qc_failure_updates_no_biological_hypothesis_and_a_qualified_reading_does(system):
    SY, _inputs, _snap, ds = system
    problem, _ = _problem(system)
    report = ds.answer(problem)
    key = ds.keys[report.recommendation["action"]]
    store = __import__("research.scientific_case_memory.case_store", fromlist=["CaseStore"]).CaseStore()
    invalid = ds.ingest(problem, report, key, "quality_failed", store=store)
    assert invalid["biological_update_allowed"] is False and len(invalid["candidates"]) == 2 and not invalid["resolved"]
    assert invalid["evidence_card"].status is S.MeasurementStatus.QC_FAILED
    qualified = ds.ingest(problem, report, key, "eliminate_b", agreement=0.6, store=store)
    assert qualified["biological_update_allowed"] is True and qualified["resolved"] and len(qualified["candidates"]) == 1
    absent = ds.ingest(problem, report, key, "undetected", store=__import__("research.scientific_case_memory.case_store",
                                                                           fromlist=["CaseStore"]).CaseStore())
    assert absent["biological_update_allowed"] is False and len(absent["candidates"]) == 2


def test_ingest_supersedes_the_case_and_grades_the_forecast_append_only(system):
    from research.scientific_case_memory import case_store as CS
    SY, _inputs, _snap, ds = system
    problem, _ = _problem(system)
    report = ds.answer(problem)
    key = ds.keys[report.recommendation["action"]]
    store = CS.CaseStore()
    first = ds.ingest(problem, report, key, "undetected", store=store)
    assert first["case_version"] == 1 and store.get(first["case_id"]).final_decision["status"] == "open"
    after = SY.UserProblem(problem.name, problem.smiles, problem.hypotheses,
                           ({"key": key, "outcome": "undetected", "agreement": None},), unit=problem.unit)
    report2 = ds.answer(after)
    second_key = ds.keys[report2.recommendation["action"]] if report2.recommendation else None
    assert second_key != key  # the measured condition is not offered again
    second = ds.ingest(after, report2, second_key, "eliminate_a", agreement=0.5, store=store)
    assert second["case_version"] == 2 and second["resolved"]
    latest = store.get(first["case_id"])
    assert latest.final_decision["status"] == "decided" and latest.supersedes == S.digest(store.get(first["case_id"], 1))
    assert store.get(first["case_id"], 1).final_decision["status"] == "open"  # the earlier version is intact
    assert latest.calibration_history and 0.0 <= latest.calibration_history[0].forecast <= 1.0
    assert store.verify() == ()


# ------------------------------------------------------------------------------------------ stress, update, analysis rules
def _tiny_index():
    from research.scientific_case_memory import case_index as CI

    pool = ("A", "B")
    keys = [("K1", 24.0, 100.0), ("K1", 24.0, 1000.0), ("K2", 24.0, 100.0)]
    names = [f"a{i}" for i in range(4)] + [f"b{i}" for i in range(4)]
    klass = np.array(["A"] * 4 + ["B"] * 4, dtype=object)
    unit = np.array([f"u{i}" for i in range(8)], dtype=object)
    tables = {}
    for j, key in enumerate(keys):
        code = np.full((8, 2), -1, dtype=int)
        code[:4, 1] = [0, 0, 0, 1 - (j == 0)]  # class A reads against decoy B
        code[4:, 0] = [0, 0, 2, 2]
        tables[key] = CI.ReadingTable(key, names, klass, code, np.ones(8, bool), np.full(8, 0.5), unit, {n: i for i, n in enumerate(names)})
    return CI.CaseIndex(pool, keys, tables, {n: None for n in names}, None, {}, dict(zip(names, unit)), dict(zip(names, klass))), keys


def test_stress_helpers_score_codes_and_build_a_table_without_the_withheld_condition():
    from . import stress as ST

    assert ST._code_of("profile_matches_h1", True) == 0 and ST._code_of("profile_matches_h1", False) == 1
    assert ST._code_of("profile_unresolved", True) == 2 and ST._code_of("no_detectable_response", False) == 3
    assert ST._code_of("quality_failed", True) == 4
    p4 = np.array([0.5, 0.2, 0.2, 0.1])
    assert abs(ST._nll(p4, 0.1, 0) + np.log(0.9 * 0.5)) < 1e-12 and abs(ST._nll(p4, 0.1, 4) + np.log(0.1)) < 1e-12
    index, keys = _tiny_index()
    others = keys[:2]
    table = ST.adaptation_table_from_index(index, others, "sciplex3")
    trials = sum(n for _s, n in table.counts.values())
    every = ST.adaptation_table_from_index(index, keys, "sciplex3")
    assert trials < sum(n for _s, n in every.counts.values())  # pairs involving the withheld key are absent
    pooled = ST._pooled(index, others)
    dist = ST.class_distribution(index, keys[0], "A", "B", pooled)
    assert abs(dist.sum() - 1.0) < 1e-12 and dist[0] > dist[1]


def test_online_update_aggregation_reports_a_gain_by_arrival_position():
    from . import online_update as OU

    rows = [{"task": "t", "tier": "d:T", "unit": f"u{i}", "position": i, "static": 1.0, "online": 0.9 if i >= 10 else 1.0}
            for i in range(60)]
    out = OU._aggregate(rows)
    assert out["overall"]["difference"] < 0 and out["buckets"][0]["difference"] == 0.0 and out["buckets"][-1]["difference"] < 0


def test_forecast_verdict_follows_the_registered_rule():
    from . import analyze as AN

    better = {"ci": [-0.02, -0.005]}
    assert AN.verdict_forecast(better, [{"ci": [-0.03, 0.0]}]) == "IMPROVES"
    assert AN.verdict_forecast(better, [{"ci": [0.01, 0.03]}]) == "NO_DETECTABLE_DIFFERENCE"  # one tier is clearly worse
    assert AN.verdict_forecast({"ci": [0.004, 0.02]}, []) == "HURTS"
    assert AN.verdict_forecast({"ci": [-0.01, 0.02]}, []) == "NO_DETECTABLE_DIFFERENCE"


def test_screens_apply_the_protocol_v2_rules_unchanged():
    from research.scientific_case_memory import evaluate_decision_policy as D

    def rec(tier, metric, est, lo, hi):
        return {"tier": tier, "arm": "x", "comparator": "fixed", "metric": metric, "difference": est, "lo": lo, "hi": hi}

    pairs = [rec("B", "correct", 0.03, 0.01, 0.05), rec("B", "wrong", 0.0, -0.002, 0.003)]
    head = [{"tier": "B", "headroom": 0.08, "lo": 0.05, "hi": 0.1, "eligible": True}]
    assert D.screens(pairs, head, "x", "fixed")["verdict"] == "ADVANCES"
    assert D.screens(pairs, [{**head[0], "eligible": False}], "x", "fixed")["verdict"] == "NO_DEVELOPMENT_SIGNAL"
    unsafe = pairs[:1] + [rec("B", "wrong", 0.01, 0.0, 0.02)]
    assert D.screens(unsafe, head, "x", "fixed")["verdict"] == "SIGNAL_BUT_UNSAFE"


def test_forecast_metrics_reward_a_hypothesis_conditional_forecast_over_a_scalar_one():
    from research.scientific_case_memory import evaluate_case_retrieval as F

    labels = F.LABELS
    rows = []
    for i in range(40):
        y = "profile_matches_h1" if i % 2 == 0 else "no_detectable_response"
        truth_vec = [0.8, 0.02, 0.02, 0.15, 0.01] if y == "profile_matches_h1" else [0.2, 0.02, 0.02, 0.75, 0.01]
        other = [0.05, 0.6, 0.05, 0.29, 0.01]
        pooled = [0.3, 0.3, 0.05, 0.34, 0.01]
        rows.append({"dataset": "d", "tier": "T", "fold": 0, "compound": f"c{i}", "unit": f"u{i}", "key": "K", "h1": "A", "h2": "B",
                     "truth": "A", "y": y, "nn_similarity": 0.3, "nn_class": None,
                     "worlds": {"cond": {"h1": truth_vec, "h2": other, "support": [5, 5]},
                                "scalar": {"h1": pooled, "h2": pooled, "support": [0, 0]}}})
    frame = F.item_frame(rows, ["cond", "scalar"])
    cond, scalar = F.world_metrics(frame, "cond"), F.world_metrics(frame, "scalar")
    assert scalar["discrimination"] == 0.0 and cond["discrimination"] > 0.5
    assert cond["nll"] < scalar["nll"]
    diff = F.paired_metric(frame, "cond", "scalar", "nll")
    assert diff["difference"] < 0 and diff["ci"][1] < 0 and diff["items"] == 40
    assert abs(F.ece(np.array([0.5, 0.5]), np.array([1.0, 0.0]))) < 1e-12


# ------------------------------------------------------------------------------------------ typed bridges
def test_bridge_labels_discordance_with_the_declared_thresholds_and_writes_valid_contrastive_cases():
    from research.scientific_case_memory import case_store as CS

    from . import bridges as B

    frame = pd.DataFrame({
        "dataset": ["sciplex3"] * 4, "compound_id": ["a", "b", "c", "d"], "block": list("ABCD"), "cell_line": ["A549"] * 4,
        "transcript_shift_norm": [6.0, 5.0, 0.4, 0.3], "detection_status": ["detected", "detected", "undetected", "undetected"],
        "measurement_status": ["qualified", "qualified", "undetected", "undetected"], "mechanism_annotation": [None] * 4,
        "unit_id": list("wxyz"), "viability_auc": [0.95, 0.5, 0.4, 0.9], "viability_curve_r2": [0.9] * 4,
        "prism_name": ["a", "b", "c", "d"], "prism_moa": [None] * 4})
    frame["discordance"] = np.where((frame.detection_status == "detected") & (frame.viability_auc >= B.INACTIVE_AUC), "response_without_phenotype",
                                    np.where((frame.detection_status == "undetected") & (frame.viability_auc <= B.ACTIVE_AUC),
                                             "phenotype_without_response", "concordant_or_intermediate"))
    assert (B.ACTIVE_AUC, B.INACTIVE_AUC) == (0.60, 0.85)  # the case package's declared construction settings
    assert frame.discordance.tolist() == ["response_without_phenotype", "concordant_or_intermediate", "phenotype_without_response",
                                          "concordant_or_intermediate"]
    summary = B.summarise(frame)
    assert summary["discordance"]["detected_with_inactive_auc"] == 1 and summary["discordance"]["undetected_with_active_auc"] == 1
    refs = (S.RawDataRef("data/raw/prism/x.csv", "a" * 64, "viability"),)
    cases = B.discordant_cases(frame, refs)
    assert len(cases) == 2 and all(c.case_kind is S.CaseKind.CONTRASTIVE for c in cases)
    store = CS.CaseStore()
    store.append_many(cases)  # every case validates against the schema
    for c in cases:
        prism = next(o for o in c.initial_observations if o.condition_id == "prism_viability_auc")
        assert prism.status is S.MeasurementStatus.AMBIGUOUS and "not dose" in prism.note  # a processed record is not qualified evidence
        assert any(a.available is False for a in c.candidate_actions) and c.final_decision["status"] == "defer"
