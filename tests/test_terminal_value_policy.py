"""Opt-in terminal value: external bindings, unit costs, repair authority and measured facts."""
from dataclasses import replace
import hashlib
import json

import pytest

from agent.context import ContextBuilder, TaskInterpreter
from agent.case_store import MeasurementResult
from agent.knowledge import EvidenceLedger
from agent.llm import TemplateCompleter, VisualInspector
from agent.memory import CaseStore, MemoryStore, RunLogger
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from maestro import EvidenceAction, FunctionalInterventionProfile
from maestro.acquisition import OutcomeBranch, OutcomeForecast
from maestro.decision_value_policy import FrozenDecisionValuePolicy, decision_action_binding, decision_hypotheses_binding, decision_interpretation_binding
from maestro.models import BiologicalQuantity, DevelopmentAction, EvidenceActionKind, EvidenceKind, EvidenceScope, MechanismHypothesis, PremiseRequirement
from maestro.outcome import InterpretationTable, OutcomeRule
from tests.fixtures.orchestration import TASK, _plan


PROFILE = FunctionalInterventionProfile("drug", nominal_dose=1.0, time_hours=24.0, context_identifier="cell-a")
HYPOTHESES = (MechanismHypothesis("a", "A", DevelopmentAction.CONTINUE),
              MechanismHypothesis("b", "B", DevelopmentAction.REVISE_INTERVENTION))
RULES = (
    OutcomeRule("match-a", "a", frozenset({"matches:a"}), eliminates=frozenset({"b"}), scope=EvidenceScope.MECHANISM_CONTRAST),
    OutcomeRule("match-b", "b", frozenset({"matches:b"}), eliminates=frozenset({"a"}), scope=EvidenceScope.MECHANISM_CONTRAST),
)
CONSEQUENCES = {"a": frozenset({"b"}), "b": frozenset({"a"})}


def action(identifier="useful"):
    return EvidenceAction(identifier, "Synthetic assay", 10.0, ("a", "b"), readout="response", time_hours=24.0,
                          expected_conditions={"dose": "1uM", "assay": "synthetic", "platform": "fixture"},
                          expected_outcomes={"a": "a", "b": "b"})


def receipt_data(actions):
    return {"schema_version": "1.0", "endpoint": "viability", "wrong_decision_loss": 4.0, "defer_loss": 1.0,
            "hypotheses_sha256": decision_hypotheses_binding(HYPOTHESES),
            "interpretation_sha256": decision_interpretation_binding(RULES),
            "minimum_reference_units": 10, "minimum_branch_support": 10,
            "measurement_costs": {a.identifier: 0.1 for a in actions}, "admissions": {
                a.identifier: {"admission_status": "admitted", "calibration_status": "calibrated", "model_version": "fixture-1",
                               "endpoint": "viability", "readout": "response", "context": "cell-a", "reference_units": 20,
                               "in_distribution": True, "shift_flags": [], "calibration_id": "synthetic-reference",
                               "calibration_revision": "c" * 64, "source_revision": "d" * 64,
                               "binding_sha256": decision_action_binding(a, PROFILE, "viability")}
                for a in actions}}


def policy_from(tmp_path, data):
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return FrozenDecisionValuePolicy.from_receipt(path, hashlib.sha256(path.read_bytes()).hexdigest())


def forecast(a, policy, informative=True):
    provenance = {key: policy.admissions[a.identifier][key]
                  for key in ("calibration_id", "calibration_revision", "source_revision", "binding_sha256")}
    provenance.update(in_distribution="true", shift_status="none")
    p = 0.99 if informative else 0.5
    return OutcomeForecast(a.identifier, (OutcomeBranch("a", {"a": p, "b": 1 - p}, 100),
                                         OutcomeBranch("b", {"a": 1 - p, "b": p}, 100)),
                           model_version="fixture-1", provenance=provenance)


def select(policy, a, f, *, endpoint="viability", profile=PROFILE, budget=10.0, hypotheses=HYPOTHESES,
           interpretation_rules=RULES, consequences=CONSEQUENCES, **settings):
    return policy.select(frozenset({"a", "b"}), (a,), profile, budget, {a.identifier: f}, consequences,
                         endpoint=endpoint, hypotheses=hypotheses, interpretation_rules=interpretation_rules, **settings)


def orchestrator(tmp_path, policy, forecasts, **options):
    plan = _plan(options.pop("llm_choice", "flat"))
    definitions = options.pop("llm_definitions", None)
    if definitions is not None:
        plan["hypotheses"] = definitions
    client = TemplateCompleter({"task_triage": TASK, "contrast_planner": plan})
    memory = MemoryStore(tmp_path / "memory.sqlite")
    interpretation_table = options.pop("interpretation_table", InterpretationTable(RULES))

    class Forecaster:
        name = "synthetic-calibrated-fixture"
        def forecast(self, *args, **kwargs):
            if isinstance(forecasts, Exception):
                raise forecasts
            return forecasts

    return MAESTROOrchestrator(interpreter=TaskInterpreter(client),
                              context_builder=ContextBuilder(EvidenceLedger(tmp_path / "evidence.sqlite"), memory),
                              planner=MechanismContrastPlanner(client),
                              visual_inspector=VisualInspector(client, "unused"), memory=memory, logger=RunLogger(tmp_path),
                              case_store=CaseStore(tmp_path / "cases.sqlite"), interpretation_table=interpretation_table,
                              outcome_forecaster=Forecaster(), selection_strategy="decision_value", decision_value_policy=policy, **options)


def events(tmp_path, kind):
    return [row["payload"] for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if (row := json.loads(line))["kind"] == kind]


def test_utility_price_is_separate_from_budget_and_non_decisive_likelihood_does_not_buy(tmp_path):
    a = action()
    policy = policy_from(tmp_path, receipt_data((a,)))
    result = select(policy, a, forecast(a, policy))
    assert result.chosen.cost == 0.1 and result.chosen.net_value == pytest.approx(0.86)
    assert select(policy, a, forecast(a, policy, False)).chosen is None
    assert select(policy, a, forecast(a, policy), budget=9).chosen is None


@pytest.mark.parametrize("field,value,reason", [
    ("calibration_status", "uncalibrated", "outcome_distribution_uncalibrated"),
    ("admission_status", "unsupported", "external_admission_refused"),
    ("in_distribution", False, "outcome_distribution_shifted"),
    ("shift_flags", ["platform"], "outcome_distribution_shifted"),
    ("reference_units", 0, "insufficient_calibration_reference_units"),
    ("readout", "other", "decision_domain_mismatch"),
    ("endpoint", "other", "decision_domain_mismatch"),
    ("context", "other", "decision_domain_mismatch"),
    ("binding_sha256", "0" * 64, "decision_action_binding_mismatch"),
])
def test_external_admission_failures_are_named(tmp_path, field, value, reason):
    a = action()
    data = receipt_data((a,)); data["admissions"][a.identifier][field] = value
    policy = policy_from(tmp_path, data)
    result = select(policy, a, forecast(a, policy))
    assert result.chosen is None and reason in result.evaluations[0].reason


@pytest.mark.parametrize("change,reason", [
    ({"model_version": "other"}, "forecast_model_version_mismatch"),
    ({"provenance": {}}, "forecast_calibration_binding_mismatch"),
    ({"evidence_kind": EvidenceKind.REAL_MEASUREMENT}, "outcome_forecast_is_not_model_prediction"),
    ({"branches": (OutcomeBranch("a", {"a": 1.0}, 0), OutcomeBranch("b", {"b": 1.0}, 100))}, "insufficient_forecast_branch_support"),
])
def test_unbound_or_zero_support_forecast_cannot_become_a_purchase(tmp_path, change, reason):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,)))
    result = select(policy, a, replace(forecast(a, policy), **change))
    assert result.chosen is None and reason in result.evaluations[0].reason


def test_source_calibration_shift_and_exact_conditions_are_bound(tmp_path):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,))); f = forecast(a, policy)
    for key in ("source_revision", "calibration_revision", "calibration_id", "binding_sha256"):
        changed = replace(f, provenance={**f.provenance, key: "other"})
        assert "forecast_calibration_binding_mismatch" in select(policy, a, changed).evaluations[0].reason
    assert "forecast_domain_unqualified" in select(policy, a, replace(f, provenance={**f.provenance, "shift_status": "time"})).evaluations[0].reason
    for changed in (replace(a, time_hours=72), replace(a, expected_conditions={**a.expected_conditions, "dose": "2uM"}),
                    replace(a, expected_conditions={**a.expected_conditions, "platform": "other"})):
        assert "decision_action_binding_mismatch" in select(policy, changed, f).evaluations[0].reason
    assert "decision_endpoint_mismatch" in select(policy, a, f, endpoint="other").evaluations[0].reason


def test_missing_costs_and_external_admission_never_infer_units_or_permissions(tmp_path):
    a = action(); data = receipt_data((a,)); data["measurement_costs"] = {}
    policy = policy_from(tmp_path, data)
    result = select(policy, a, forecast(a, policy))
    assert result.chosen is None and "utility_measurement_cost_missing" in result.evaluations[0].reason
    assert result.evaluations[0].cost == 0.0
    data = receipt_data((a,)); data["admissions"] = {}
    policy = policy_from(tmp_path, data)
    assert "external_admission_missing" in select(policy, a, OutcomeForecast(a.identifier)).evaluations[0].reason


def test_receipt_hash_and_immutable_policy_prevent_runtime_relabeling(tmp_path):
    a = action(); data = receipt_data((a,)); policy = policy_from(tmp_path, data)
    with pytest.raises(ValueError, match="hash_mismatch"):
        FrozenDecisionValuePolicy.from_receipt(tmp_path / "evaluation.json", "0" * 64)
    with pytest.raises(TypeError):
        policy.measurement_costs[a.identifier] = 0
    with pytest.raises(TypeError):
        policy.admissions[a.identifier]["calibration_status"] = "uncalibrated"


def test_constructor_requires_explicit_policy_and_forbids_coverage_fallback(tmp_path):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,)))
    with pytest.raises(ValueError, match="cannot fall back"):
        orchestrator(tmp_path, policy, {}, forecast_failure_policy="coverage")
    with pytest.raises(ValueError, match="requires an outcome_forecaster"):
        orchestrator(tmp_path, None, {})


def test_llm_choice_loses_to_terminal_value_without_creating_measurement_facts(tmp_path):
    useful, flat = action(), action("flat"); policy = policy_from(tmp_path, receipt_data((useful, flat)))
    controller = orchestrator(tmp_path, policy, {"useful": forecast(useful, policy), "flat": forecast(flat, policy, False)})
    turn = controller.run("Resolve.", available_actions=(flat, useful), intervention_profile=PROFILE, case_id="case", budget=10,
                          expected_hypotheses=HYPOTHESES)
    assert turn.selected_actions == (useful,) and turn.case.spent == 0
    assert controller.evidence_state("case") is None and controller._case_store.result_identities("case") == ()
    assert not PROFILE.measured_fields
    assert events(tmp_path, "decision_value_selection_computed")[-1]["chosen"] == "useful"


@pytest.mark.parametrize("failure,budget", [(False, 10.0), (True, 10.0), (False, 0.0), (False, None)])
def test_refusal_or_forecaster_failure_never_falls_back_to_the_llm_action(tmp_path, failure, budget):
    a = action("flat"); policy = policy_from(tmp_path, receipt_data((a,)))
    controller = orchestrator(tmp_path, policy, RuntimeError("offline") if failure else {a.identifier: forecast(a, policy, False)})
    calls = []
    controller.run_case_loop("Resolve.", available_actions=(a,), intervention_profile=PROFILE, case_id="case", budget=budget,
                             result_provider=lambda action, turn: calls.append(action.identifier), max_rounds=1, expected_hypotheses=HYPOTHESES)
    assert calls == [] and events(tmp_path, "decision_value_execution_gate")[-1]["submitted_action_ids"] == []
    assert events(tmp_path, "outcome_forecast_fallback") == []


@pytest.mark.parametrize("edit", ["replacement", "conditions", "hypotheses", "repeated"])
def test_repair_cannot_override_an_admitted_action_or_relabel_its_scientific_problem(tmp_path, monkeypatch, edit):
    a, other = action(), action("other"); policy = policy_from(tmp_path, receipt_data((a, other)))
    controller = orchestrator(tmp_path, policy, {a.identifier: forecast(a, policy), other.identifier: forecast(other, policy, False)}, llm_choice="other")
    original = controller._check_and_repair
    def repaired(*args, **kwargs):
        outcome = original(*args, **kwargs)
        if edit == "hypotheses":
            contrast = replace(outcome.contrast, hypotheses=(replace(outcome.contrast.hypotheses[0], description="New scientific meaning"),
                                                            outcome.contrast.hypotheses[1]))
        elif edit == "repeated":
            contrast = replace(outcome.contrast, additional_plans=(a,))
        else:
            contrast = replace(outcome.contrast, plan=other if edit == "replacement" else replace(a, time_hours=72))
        return replace(outcome, contrast=contrast)
    monkeypatch.setattr(controller, "_check_and_repair", repaired)
    turn = controller.run("Resolve.", available_actions=(a, other), intervention_profile=PROFILE, case_id="case", budget=10,
                          expected_hypotheses=HYPOTHESES)
    assert turn.selected_actions == () and "after_value_selection" in turn.repair_stop_reason
    assert events(tmp_path, "decision_value_execution_gate")[-1]["rejected"]


def test_external_refusal_filters_forecasts_before_model_work(tmp_path):
    a = action("flat"); data = receipt_data((a,)); data["admissions"][a.identifier]["admission_status"] = "unsupported"
    policy = policy_from(tmp_path, data)
    controller = orchestrator(tmp_path, policy, AssertionError("A refused action must not trigger model work"))
    turn = controller.run("Resolve.", available_actions=(a,), intervention_profile=PROFILE, case_id="case", budget=10,
                          expected_hypotheses=HYPOTHESES)
    assert turn.selected_actions == ()
    result = events(tmp_path, "decision_value_selection_computed")[-1]
    assert result["status"] == "no_admissible_action" and "external_admission_refused" in result["evaluations"][a.identifier]["reason"]


@pytest.mark.parametrize("evidence_kind", [EvidenceKind.MODEL_PREDICTION, EvidenceKind.REAL_MEASUREMENT])
def test_only_supplied_real_measurements_change_the_evidence_after_value_selection(tmp_path, evidence_kind):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,)))
    controller = orchestrator(tmp_path, policy, {a.identifier: forecast(a, policy)}, llm_choice=a.identifier)
    observation = MeasurementResult(a.identifier, "Synthetic contract observation", "fixture-source", "cell-a", 24.0, 3,
                                    True, conditions=dict(a.expected_conditions), metrics={"response": "0.7"},
                                    evidence_kind=evidence_kind, interpretation_fields=("matches:a",), result_id="fixture-result")
    loop = controller.run_case_loop("Resolve.", available_actions=(a,), intervention_profile=PROFILE,
                                    case_id="case", budget=10, max_rounds=1, result_provider=lambda action, turn: observation,
                                    expected_hypotheses=HYPOTHESES)
    real = evidence_kind is EvidenceKind.REAL_MEASUREMENT
    assert loop.evidence_state.candidates == (frozenset({"a"}) if real else frozenset({"a", "b"}))
    assert len(controller._case_store.result_identities("case")) == int(real)
    assert controller._case_store.snapshot("case").spent == (10.0 if real else 0.0)
    assert observation.metrics == {"response": "0.7"} and observation.evidence_kind is evidence_kind


def test_registered_hypothesis_semantics_bind_the_likelihood_before_forecasting(tmp_path):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,))); f = forecast(a, policy)
    assert "registered_hypotheses_required" in select(policy, a, f, hypotheses=()).evaluations[0].reason
    for field, value in (("description", "Other meaning"), ("causal_factor", "pathway_compensation"),
                         ("proposed_action", DevelopmentAction.STOP)):
        changed = (replace(HYPOTHESES[0], **{field: value}), HYPOTHESES[1])
        assert "decision_hypotheses_binding_mismatch" in select(policy, a, f, hypotheses=changed).evaluations[0].reason
    assert decision_hypotheses_binding(HYPOTHESES[::-1]) == policy.hypotheses_sha256
    definitions = [{"identifier": "a", "description": "Other meaning", "proposed_action": "continue"},
                   {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"}]
    controller = orchestrator(tmp_path, policy, AssertionError("Do not forecast an unregistered scientific problem"),
                              llm_choice=a.identifier, llm_definitions=definitions)
    turn = controller.run("Resolve.", available_actions=(a,), intervention_profile=PROFILE, budget=10)
    assert turn.selected_actions == ()
    assert "decision_hypotheses_binding_mismatch" in events(tmp_path, "decision_value_selection_computed")[-1]["reason"]


def test_registered_definitions_canonically_compile_llm_proposal_without_changing_scientific_meaning(tmp_path):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,)))
    definitions = [{"identifier": "a", "description": "LLM proposal text", "proposed_action": "continue"},
                   {"identifier": "b", "description": "Another proposal", "proposed_action": "stop"}]
    controller = orchestrator(tmp_path, policy, {a.identifier: forecast(a, policy)}, llm_choice=a.identifier,
                              llm_definitions=definitions)
    turn = controller.run("Resolve.", available_actions=(a,), intervention_profile=PROFILE, budget=10, expected_hypotheses=HYPOTHESES)
    assert turn.contrast.hypotheses == HYPOTHESES and turn.selected_actions == (a,)


def test_calibrated_reading_definition_and_consequences_cannot_be_replaced(tmp_path):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,))); f = forecast(a, policy)
    assert decision_interpretation_binding(RULES[::-1]) == policy.interpretation_sha256
    assert "registered_interpretation_rules_required" in select(policy, a, f, interpretation_rules=()).evaluations[0].reason
    assert "decision_outcome_consequences_mismatch" in select(policy, a, f, consequences={}).evaluations[0].reason
    for settings in ({"time_tolerance_hours": 2.0}, {"require_context_match": False}):
        assert "decision_interpretation_binding_mismatch" in select(policy, a, f, **settings).evaluations[0].reason
    changes = (("matched_fields", frozenset({"other-reading"})), ("eliminates", frozenset()),
               ("scope", EvidenceScope.MEASUREMENT_FEASIBILITY), ("minimum_independent_units", 100),
               ("metric_bounds", {"response": (0.5, 1.0)}), ("requires_time_match", True),
               ("required_conditions", frozenset({"assay"})), ("matched_condition_keys", ("dose",)),
               ("field_requirements", (PremiseRequirement("matches:a", BiologicalQuantity.VIABILITY),)),
               ("evidence_requirements", (PremiseRequirement("occupancy", BiologicalQuantity.TARGET_OCCUPANCY),)))
    for field, value in changes:
        changed = (replace(RULES[0], **{field: value}), RULES[1])
        result = select(policy, a, f, interpretation_rules=changed)
        assert result.chosen is None and "decision_interpretation_binding_mismatch" in result.evaluations[0].reason
    nested = (replace(RULES[0], allowed_action_kinds=frozenset({EvidenceActionKind.READOUT_MEASUREMENT,
                         EvidenceActionKind.FUNCTIONAL_MEASUREMENT}), metric_bounds={"response": (None, 1.0)},
                         field_requirements=(PremiseRequirement("matches:a", BiologicalQuantity.VIABILITY),)), RULES[1])
    assert decision_interpretation_binding(nested) == decision_interpretation_binding(nested[::-1])


@pytest.mark.parametrize("table", [InterpretationTable((replace(RULES[0], metric_bounds={"response": (0.5, 1.0)}), RULES[1])),
                                   InterpretationTable(RULES, time_tolerance_hours=2.0),
                                   InterpretationTable(RULES, require_context_match=False)])
def test_rule_or_table_condition_changes_refuse_before_forecasting(tmp_path, table):
    a = action(); policy = policy_from(tmp_path, receipt_data((a,)))
    controller = orchestrator(tmp_path, policy, AssertionError("Changed reading definitions cannot trigger forecast work"),
                              llm_choice=a.identifier, interpretation_table=table)
    turn = controller.run("Resolve.", available_actions=(a,), intervention_profile=PROFILE, budget=10,
                          expected_hypotheses=HYPOTHESES)
    assert turn.selected_actions == ()
    assert "decision_interpretation_binding_mismatch" in events(tmp_path, "decision_value_selection_computed")[-1]["reason"]
