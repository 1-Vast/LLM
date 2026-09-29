"""Integration tests for the production case-memory and conditional-forecast modules.

File summary
- Path: tests/test_case_memory_integration.py
- Purpose: the registered test suite of the case-memory production integration: schema validation,
  append-only storage, digest verification, policy/evaluator separation, leak refusal, gene
  alignment, compound canonicalisation, directional features, control matching, missingness,
  adaptation cost, retrieval reasons, hypothesis-graph validity, the conditional forecast
  interface, history-aware cache identity, abstention, evidence-state immutability, decision-value
  action selection, the external-study split and the case update after a new real result.
- Depends on: src/maestro/{case_memory,directional,hypothesis_graph,adaptive_retrieval,
  case_update,problem_compiler,hypothesis_forecast}.py, src/virtual_cell/{interface,
  conditional_forecast}.py
"""
from __future__ import annotations

import pytest

from maestro import adaptive_retrieval as AR
from maestro import case_memory as CM
from maestro import case_update as CU
from maestro import directional as DR
from maestro import hypothesis_graph as HG
from maestro import problem_compiler as PC
from maestro.acquisition import OutcomeBranch, OutcomeForecast
from virtual_cell import conditional_forecast as CF
from virtual_cell import interface as VC

Q = CM.ScientificMeasurementStatus.QUALIFIED
NP = CM.ScientificMeasurementStatus.NOT_PLANNED
UC = CM.ScientificMeasurementStatus.QC_FAILED
UD = CM.ScientificMeasurementStatus.UNDETECTED


def _sha(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _episode(case_id: str = "case-1", kind: CM.CaseKind = CM.CaseKind.CANONICAL,
             hypothesis_updates=(), observations=None, failures=(), adaptation=()) -> CM.ScientificEpisode:
    observations = observations if observations is not None else (
        CM.EpisodeObservation("cond-1", Q, "l1000", cell_line="A549", time_h=24.0, dose_nM=10000.0,
                              readout="gene:EGR1", value=2.1, direction=1, replicate_agreement=0.9),
    )
    return CM.ScientificEpisode(
        case_id=case_id, case_version=1, case_kind=kind,
        problem_type="mechanism_contrast_transcriptomic",
        user_question="Does the compound act through the nominal target?",
        raw_data_references=(CM.RawDataRef("file:///state.npz", _sha(case_id), "prepared_state_table"),),
        data_quality_report={"replicate_agreement_median": 0.9},
        context_fingerprint={"dataset": "l1000", "assay": "l1000", "context": "A549",
                             "biological_system": "l1000", "measurement_type": "transcriptomic",
                             "control_design": "vehicle", "intervention_type": "compound",
                             "cell_line": "A549", "time_h": 24.0, "dose_nM": 10000.0},
        initial_observations=observations,
        initial_hypotheses=(
            CM.HypothesisClaim("H_on", "on-target mechanism", predicted={"a1": "match_h1"}),
            CM.HypothesisClaim("H_off", "off-target mechanism", predicted={"a1": "match_h2"}),
            CM.HypothesisClaim("H_art", "assay artifact", advisory=True),
        ),
        hypothesis_graph={"nodes": 4, "edges": 3},
        retrieved_cases=(),
        adaptation_map=adaptation,
        candidate_actions=(
            CM.CandidateAction("a1", "transcriptomic repeat", "l1000", 8.0, 2.0, "signed_state_change"),
            CM.CandidateAction("a2", "orthogonal phenotype", "phenotypic", 24.0, 4.0, "phenotype"),
        ),
        virtual_cell_forecasts=(
            CM.ForecastRecord("a1", "H_on", {"match_h1": 0.7, "match_h2": 0.2, "unresolved": 0.1},
                              12, "case-memory-production-1", "test"),
        ),
        predicted_outcome_branches=(),
        real_measurements=(),
        measurement_quality={},
        qualified_evidence=(),
        hypothesis_updates=hypothesis_updates,
        next_action={},
        branching_interpretation_plan=(
            CM.BranchingPlan("a1", {"match_h1": "update:match_h1", "match_h2": "update:match_h2"},
                             "orthogonal:a2", "invalid:no_biological_hypothesis_update"),
        ),
        final_decision={"status": "open", "basis": "no real measurement yet"},
        failure_modes=failures,
        calibration_history=(),
        provenance={"builder": "test", "sources": "test", "created_at": "2026-09-29",
                    "data_origin": "real"},
    )


# -------------------------------------------------------------------------------- schema / store
def test_episode_schema_validates_and_round_trips_with_the_same_digest():
    episode = _episode()
    assert CM.validate_episode(episode) == ()
    assert CM.episode_from_dict(CM.episode_to_dict(episode)).digest == episode.digest


def test_episode_validation_names_each_structural_error():
    episode = _episode()
    bad = CM.episode_from_dict({**CM.episode_to_dict(episode), "raw_data_references": [],
                                "candidate_actions": []})
    errors = CM.validate_episode(bad)
    assert "missing:raw_data_references" in errors and "missing:candidate_actions" in errors


def test_all_seven_case_kinds_are_representable_and_typed_contents_are_enforced():
    link = CM.AdaptationLink("src-case", "dst-case", {"cell_line": "A"}, ("recalibrate",), 0.25, True)
    for kind in CM.CaseKind:
        extras = {}
        if kind is CM.CaseKind.FAILURE:
            extras["failures"] = (CM.FailureMode("undetected_everywhere", "no condition detected"),)
        if kind is CM.CaseKind.ADAPTATION:
            extras["adaptation"] = (link,)
        episode = _episode(f"case-{kind.value}", kind, **extras)
        assert CM.validate_episode(episode) == ()
    failure = _episode("failure-1", CM.CaseKind.FAILURE)
    errors = CM.validate_episode(failure)
    assert "failure_case_without_failure_mode" in errors
    adaptation = _episode("adapt-1", CM.CaseKind.ADAPTATION)
    assert "adaptation_case_without_links" in CM.validate_episode(adaptation)


def test_a_forecast_may_not_claim_measurement_status_and_must_normalise():
    episode = _episode()
    data = CM.episode_to_dict(episode)
    data["virtual_cell_forecasts"][0]["evidence_class"] = "measured_fact"
    assert any(e.startswith("forecast_claims_status") for e in CM.validate_episode(CM.episode_from_dict(data)))
    data = CM.episode_to_dict(episode)
    data["virtual_cell_forecasts"][0]["branches"] = {"match_h1": 0.9}
    assert any(e.startswith("forecast_not_normalised") for e in CM.validate_episode(CM.episode_from_dict(data)))


def test_store_is_append_only_digest_chained_and_detects_tampering(tmp_path):
    store = CM.EpisodeStore(tmp_path / "store.jsonl.gz")
    episode = _episode()
    store.append(episode)
    changed = store.supersede(episode, next_action={"action_id": "a1"})
    assert changed.case_version == 2 and changed.supersedes == episode.digest
    assert store.get(episode.case_id, 1).digest == episode.digest
    store.verify()
    with pytest.raises(CM.VersionConflict):
        store.supersede(episode, next_action={"action_id": "a2"})
    path = tmp_path / "store.jsonl.gz"
    import gzip
    lines = gzip.open(path, "rt", encoding="utf-8").read().splitlines()
    lines[0] = lines[0].replace('"a1"', '"aX"', 1)
    handle = open(path, "wb")
    with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as fh:
        fh.write(("\n".join(lines) + "\n").encode())
    handle.close()
    with pytest.raises(CM.StoreCorrupt):
        CM.EpisodeStore(path)


def test_digest_is_content_addressed_and_snapshot_is_order_independent(tmp_path):
    a, b = _episode("a"), _episode("b")
    s1, s2 = CM.EpisodeStore(), CM.EpisodeStore()
    s1.append_many((a, b))
    s2.append_many((b, a))
    assert s1.snapshot_digest() == s2.snapshot_digest()
    assert CM.digest(CM.episode_to_dict(a)) == a.digest


# -------------------------------------------------------------------------------- separation / leaks
def test_retrieval_problem_has_no_truth_field():
    import dataclasses
    assert "truth" not in {f.name for f in dataclasses.fields(AR.RetrievalProblem)}
    assert "label" not in {f.name for f in dataclasses.fields(AR.RetrievalProblem)}


def test_compiled_problem_carries_diagnostics_before_any_recommendation():
    records = [PC.MeasurementRecord("r1", "EGR1", 1.5, "treated", Q, replicate_group="g1"),
               PC.MeasurementRecord("r2", "FOS", -1.2, "treated", Q, replicate_group="g1")]
    compiled = PC.compile_problem("p1", "mechanism?", records)
    assert any(d.code == "missing:control" for d in compiled.diagnostics)
    assert compiled.measurement_status["treated"] is Q


def test_policy_view_separation_problem_compiler_never_returns_a_label():
    compiled = PC.compile_problem("p1", "mechanism?", [
        PC.MeasurementRecord("r1", "EGR1", 1.5, "treated", Q),
        PC.MeasurementRecord("r2", "DMSO", 0.0, "control", Q, is_control=True)])
    assert not hasattr(compiled, "truth") and not hasattr(compiled, "label")


# -------------------------------------------------------------------------------- identifiers
def test_gene_alignment_flags_invalid_symbols_and_out_of_space_genes():
    compiler = PC.ProblemCompiler(reference_genes=("EGR1",))
    records = [PC.MeasurementRecord("r1", "EGR1", 1.0, "treated", Q),
               PC.MeasurementRecord("r2", "not a gene", 1.0, "treated", Q),
               PC.MeasurementRecord("r3", "ZZZ9", 1.0, "treated", Q),
               PC.MeasurementRecord("r4", "DMSO", 0.0, "control", Q, is_control=True)]
    compiled = compiler.compile("p1", "mechanism?", records, assay_hint="transcriptomic_profile")
    codes = [d.code for d in compiled.diagnostics]
    assert "invalid:gene_identifier" in codes and "ood:gene" in codes


def test_compound_canonicalisation_and_connectivity_block():
    assert PC.canonicalize_smiles("C(CO)O") == PC.canonicalize_smiles("OCCO")
    assert PC.canonicalize_smiles("not-a-structure") is None
    assert PC.connectivity_block("DATAGRPVKZEWHA-UHFFFAOYSA-N") == "DATAGRPVKZEWHA"
    assert PC.connectivity_block("short") is None


def test_external_study_split_uses_the_connectivity_block():
    blocks = ["AAAAAAAAAAAAAA", "BBBBBBBBBBBBBB", "AAAAAAAAAAAAAA"]
    unseen, seen = PC.unseen_unit_split(blocks, ["BBBBBBBBBBBBBB"])
    assert unseen == ("AAAAAAAAAAAAAA",) and seen == ("BBBBBBBBBBBBBB",)


# -------------------------------------------------------------------------------- directional
def test_directional_features_keep_sign_and_missing_is_never_zero():
    state = DR.directional_state_from_shift(
        {"EGR1": 2.0, "FOS": -1.0, "JUN": -0.5}, {"SET_A": ("EGR1", "FOS"), "SET_B": ("MYC",)})
    assert state.signed_feature_delta["FOS"] == -1.0
    assert state.ranked_up_features == ("EGR1",)
    assert state.ranked_down_features == ("FOS", "JUN")
    assert state.pathway_direction["SET_A"] > 0 and "SET_B" not in state.pathway_direction
    assert state.population_shift < 0


def test_feature_arms_differ_exactly_by_directional_information():
    state = DR.directional_state_from_shift({"EGR1": 2.0, "FOS": -1.0}, {"P": ("EGR1", "FOS")})
    assert DR.feature_vector(state, DR.FeatureArm.SCALAR) == {"__magnitude__": state.magnitude}
    assert DR.feature_vector(state, DR.FeatureArm.SIGNED_DIRECTION)["FOS"] == -1.0
    assert "P" in DR.feature_vector(state, DR.FeatureArm.PATHWAY_DIRECTION)
    combined = DR.feature_vector(state, DR.FeatureArm.COMBINED)
    assert "gene:FOS" in combined and "pathway:P" in combined


def test_realization_record_keeps_nominal_apart_from_realized_and_refuses_silent_zero():
    record = DR.RealizationRecord(dose_nominal=10000.0)
    assert record.dose_realized is None and record.validation_errors() == ()
    bad = DR.RealizationRecord(engagement=NP, engagement_value=0.0)
    assert "value_without_biological_status:engagement" in bad.validation_errors()


# -------------------------------------------------------------------------------- missingness / QC
def test_a_failed_or_missing_measurement_is_a_status_never_a_value():
    obs = CM.EpisodeObservation("c1", UC, "l1000", value=0.0)
    episode = _episode(observations=(obs,))
    assert any(e.startswith("value_without_biological_status") for e in CM.validate_episode(episode))
    compiled = PC.compile_problem("p", "q?", [PC.MeasurementRecord("r", "G", 0.0, "c", UC)])
    assert any(d.code == "missing_as_zero" and d.severity == "fatal" for d in compiled.diagnostics)
    assert not compiled.usable


def test_control_matching_is_diagnosed():
    treated_only = [PC.MeasurementRecord("r1", "EGR1", 1.0, "treated", Q)]
    compiled = PC.compile_problem("p", "q?", treated_only, assay_hint="targeted_molecular_readout")
    assert any(d.code == "missing:control" for d in compiled.diagnostics)
    assert compiled.control_design == "none_identified"


# -------------------------------------------------------------------------------- retrieval
def _retrieval_problem(arm=DR.FeatureArm.COMBINED) -> AR.RetrievalProblem:
    state = DR.directional_state_from_shift({"gene:EGR1": 2.0}, {"P": ("gene:EGR1",)})
    return AR.RetrievalProblem("prob-1", "l1000", "l1000", "compound", "transcriptomic", "vehicle",
                               DR.ContextFeatures(cell_line="A549", time_h=24.0, dose_nM=10000.0),
                               ("H_on", "H_off"), state, arm)


def test_hard_compatibility_excludes_with_named_reasons():
    store = CM.EpisodeStore()
    store.append(_episode("case-ok"))
    other = CM.episode_from_dict({**CM.episode_to_dict(_episode("case-x")), "case_id": "case-x",
                                  "context_fingerprint": {"dataset": "sciplex3", "assay": "sciplex",
                                                          "context": "K562", "biological_system": "sciplex3",
                                                          "measurement_type": "transcriptomic",
                                                          "control_design": "vehicle",
                                                          "intervention_type": "compound"}})
    store.append(other)
    report = AR.AdaptiveRetriever(store).hard_compatibility(_retrieval_problem())
    assert report.eligible == ("case-ok",)
    assert report.excluded["case-x"].startswith("incompatible:")


def test_retrieval_returns_component_reports_reasons_and_adaptation():
    store = CM.EpisodeStore()
    update = CM.HypothesisUpdate("a1", ("H_on", "H_off"), "measured", ("H_off",), True)
    store.append(_episode("case-ok", hypothesis_updates=(update,)))
    retriever = AR.AdaptiveRetriever(store)
    result = retriever.retrieve(_retrieval_problem(), research_mode=True)
    precedents = result.precedents["H_on"]
    assert precedents and set(AR.SCORE_TERMS) <= set(precedents[0].components)
    assert precedents[0].why and precedents[0].adaptation["basis"] in ("declared_prior", "transfer_history")
    assert "H_off" in result.reason


def test_directional_arm_retrieves_differently_than_scalar_arm():
    same_direction = _episode("case-same")
    opposite = CM.episode_from_dict({**CM.episode_to_dict(_episode("case-opposite")),
                                     "case_id": "case-opposite",
                                     "initial_observations": [
                                         {**CM.episode_to_dict(_episode()).get("initial_observations")[0],
                                          "direction": -1}]})
    update = CM.HypothesisUpdate("a1", ("H_on", "H_off"), "measured", ("H_off",), True)
    store = CM.EpisodeStore()
    for ep in (same_direction, opposite):
        store.append(CM.episode_from_dict({**CM.episode_to_dict(ep),
                                           "hypothesis_updates": [CM.episode_to_dict(u) for u in (update,)]}))
    retriever = AR.AdaptiveRetriever(store)
    directional = retriever.retrieve(_retrieval_problem(DR.FeatureArm.COMBINED), research_mode=True)
    sims = {p.case_id: p.components["state_similarity"] for p in directional.precedents["H_on"]}
    assert sims["case-same"] > sims.get("case-opposite", 0.0)
    assert "case-opposite" not in sims or sims["case-opposite"] == 0.0


# -------------------------------------------------------------------------------- hypothesis graph
def test_hypothesis_graph_validates_and_keeps_evidence_classes_distinct():
    nodes = (HG.GraphNode("i", HG.NodeKind.INTERVENTION, "drug", Q),
             HG.GraphNode("t", HG.NodeKind.TARGET, "target"),
             HG.GraphNode("o", HG.NodeKind.OBSERVABLE, "readout", Q))
    edges = (HG.GraphEdge("i", "t", "binds", 0, evidence_class=CM.EvidenceClass.LITERATURE_SUPPORT
                          if hasattr(CM.EvidenceClass, "LITERATURE_SUPPORT") else CM.EvidenceClass.HISTORICAL_ANALOGY),)
    graph = HG.HypothesisGraph(nodes, edges, (), {"H1": ("i", "t", "o"), "H2": ("i", "o")})
    assert HG.validate_graph(graph) == ()
    assert not edges[0].promotable
    qualified = HG.GraphEdge("i", "t", "binds", 0, evidence_class=CM.EvidenceClass.QUALIFIED_EVIDENCE)
    assert qualified.promotable
    thin = HG.HyperEdge(("i",), "t", "combination", "alone")
    assert "hyperedge_too_thin:t" in HG.validate_graph(
        HG.HypothesisGraph(nodes, (), (thin,), {"H1": ("i", "t", "o"), "H2": ("i", "o")}))


def test_only_qualified_experimental_evidence_is_promotable_to_evidence_state():
    promotable = {c for c in CM.EvidenceClass if c in HG.PROMOTABLE_CLASSES}
    assert promotable == {CM.EvidenceClass.QUALIFIED_EVIDENCE}
    assert CM.EvidenceClass.MODEL_PREDICTION not in promotable
    assert CM.EvidenceClass.MEASURED_FACT not in promotable


# -------------------------------------------------------------------------------- conditional VC
def _request(**kwargs) -> VC.PredictionRequest:
    base = dict(request_id="r1", case_id="c1", contrast_id="k1", plan_version=1,
                intervention=VC.Intervention("drug", "compound", ("T",)),
                context=VC.SystemContext("ctx", "d"), readouts=("x",), model_version="m1")
    base.update(kwargs)
    return VC.PredictionRequest(**base)


def test_conditional_forecast_contract_and_abstention():
    branch = CF.HypothesisBranch("H1", {"x": 1.0}, {"x": 1}, {}, 8)
    prediction = CF.ConditionalStatePrediction("a1", True, (branch,), "calibrated", "m1",
                                               {"builder": "test"})
    assert CF.validate_conditional(prediction) == ()
    abstained = CF.ConditionalStatePrediction("a1", False, (), "not_applicable", "m1",
                                              {"builder": "test"}, abstain_reason="insufficient_support")
    assert CF.validate_conditional(abstained) == ()
    fabricated = CF.ConditionalStatePrediction("a1", False, (branch,), "uncalibrated", "m1",
                                               {"builder": "test"}, abstain_reason="x")
    assert "abstention_contains_prediction" in CF.validate_conditional(fabricated)


def test_prediction_request_extension_is_backward_compatible():
    legacy = _request()
    assert legacy.validation_errors() == () and VC.PredictionRequest.from_json(legacy.to_json()) == legacy
    extended = _request(hypotheses=("H1", "H2"), history=({"action": "a", "outcome": "o"},),
                        observation_context={"cell_line": "A549"}, forecast_mode="hypothesis_conditional")
    assert extended.validation_errors() == ()
    assert VC.PredictionRequest.from_json(extended.to_json()) == extended


def test_history_and_hypotheses_enter_the_conditional_cache_identity():
    base = _request()
    by_hypothesis = _request(hypotheses=("H1", "H2"))
    by_history = _request(history=({"action": "a", "outcome": "o"},))
    keys = {CF.conditional_cache_key(r, "backend") for r in (base, by_hypothesis, by_history)}
    assert len(keys) == 3
    assert CF.conditional_cache_key(base, "backend") == CF.conditional_cache_key(
        _request(request_id="other"), "backend")  # tracking fields excluded


# -------------------------------------------------------------------------------- evidence boundary
def test_forecast_never_mutates_evidence_state():
    from maestro.models import MechanismHypothesis
    from maestro.outcome import EvidenceState

    state = EvidenceState.open((MechanismHypothesis("H1", "a"), MechanismHypothesis("H2", "b")))
    forecast = OutcomeForecast("a1", (OutcomeBranch("H1", {"match_h1": 0.8}, 10),))
    _ = forecast.branch_for("H1")
    assert state.candidates == frozenset(("H1", "H2")) and not state.eliminated


def test_forecast_record_is_a_model_prediction_by_construction():
    forecast = OutcomeForecast("a1")
    from maestro.models import EvidenceKind
    assert forecast.evidence_kind is EvidenceKind.MODEL_PREDICTION


# -------------------------------------------------------------------------------- action selection
def test_decision_value_ranking_reports_named_terms_and_refusals_rank_last():
    actions = (CM.CandidateAction("a1", "assay one", "l1000", 8.0, 2.0, "x"),
               CM.CandidateAction("a2", "assay two", "l1000", 8.0, 2.0, "x"))
    consequences = {"match_h1": frozenset(("H2",)), "match_h2": frozenset(("H1",))}
    good = OutcomeForecast("a1", (OutcomeBranch("H1", {"match_h1": 0.9, "match_h2": 0.1}, 12),
                                  OutcomeBranch("H2", {"match_h1": 0.2, "match_h2": 0.8}, 12)))
    refused = OutcomeForecast("a2", refusal="insufficient_support")
    rankings = CU.rank_actions_by_decision_value(("H1", "H2"), actions,
                                                 {"a1": good, "a2": refused}, consequences)
    assert rankings[0].action_id == "a1" and not rankings[-1].admissible
    assert rankings[-1].reason == "insufficient_support"
    assert rankings[0].hypothesis_discrimination > 0


def test_branching_plan_covers_decisive_ambiguous_and_invalid_readings():
    action = CM.CandidateAction("a1", "assay", "l1000", 8.0, 2.0, "x")
    plan = CU.branching_interpretation_plan(action, ("match_h1", "match_h2"), orthogonal_action="a2")
    assert plan.on_outcome["match_h1"].startswith("update:")
    assert plan.on_ambiguous == "orthogonal:a2"
    assert plan.on_invalid == "invalid:no_biological_hypothesis_update"


# -------------------------------------------------------------------------------- case update
def test_result_qualification_keeps_the_five_states_apart():
    m = CM.RealMeasurement("a1", Q, "match_h1", 3)
    assert CU.qualify_result(m, qc_passed=True, detected=True, eliminated=("H2",)) is CU.OutcomeQualification.QUALIFIED
    assert CU.qualify_result(m, qc_passed=True, detected=True) is CU.OutcomeQualification.RELIABLE_BUT_INCONCLUSIVE
    assert CU.qualify_result(CM.RealMeasurement("a1", UD, None), qc_passed=True, detected=False) is CU.OutcomeQualification.NEGATIVE
    assert CU.qualify_result(CM.RealMeasurement("a1", UC, None), qc_passed=False, detected=None) is CU.OutcomeQualification.UNRELIABLE
    assert CU.qualify_result(CM.RealMeasurement("a1", NP, None), qc_passed=False, detected=None) is CU.OutcomeQualification.NOT_MEASURED


def test_case_update_after_new_result_is_append_only_and_grades_the_forecast():
    store = CM.EpisodeStore()
    episode = _episode()
    store.append(episode)
    measurement = CM.RealMeasurement("a1", Q, "match_h1", 3)
    result = CU.ingest_result(store, episode, measurement, qc_passed=True, detected=True,
                              contrast=("H_on", "H_off"), eliminated=("H_off",),
                              forecast_probability=0.7, model_version="case-memory-production-1")
    assert result.qualification is CU.OutcomeQualification.QUALIFIED
    assert result.eliminated == ("H_off",)
    assert result.episode.case_version == 2 and store.get(episode.case_id, 1).digest == episode.digest
    assert result.calibration is not None and result.calibration.forecast == 0.7
    qc_failed = CM.RealMeasurement("a2", UC, None)
    result2 = CU.ingest_result(store, result.episode, qc_failed, qc_passed=False, detected=None,
                               contrast=("H_on", "H_off"))
    assert result2.qualification is CU.OutcomeQualification.UNRELIABLE
    assert not any(u.qualified for u in result2.episode.hypothesis_updates if u.action_id == "a2")


def test_feature_flag_gates_the_production_forecaster(monkeypatch):
    from maestro import hypothesis_forecast as HF

    store = CM.EpisodeStore()
    forecaster = HF.CaseMemoryOutcomeForecaster(store, research_mode=False)
    monkeypatch.delenv("MAESTRO_CASE_MEMORY_ENABLED", raising=False)
    assert not CM.case_memory_enabled()
    from maestro.models import EvidenceAction, MechanismHypothesis, MechanismContrast

    contrast = MechanismContrast("k1", (MechanismHypothesis("H1", "a"), MechanismHypothesis("H2", "b")), (), None)
    action = EvidenceAction("a1", "assay", 1.0, ("H1",), readout="x")
    forecast = forecaster.forecast(contrast, (action,), None)["a1"]
    assert forecast.refusal == "case_memory_disabled"
