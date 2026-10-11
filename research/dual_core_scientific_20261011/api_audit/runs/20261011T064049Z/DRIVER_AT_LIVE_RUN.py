"""Three real-provider engineering checks; synthetic forecasts are never facts."""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
from urllib.parse import urlsplit

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "src"))

import agent.llm as llm_module
from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger
from agent.llm import DeepSeekChatClient, MAESTROSettings, TemplateCompleter, VisualInspector
from agent.memory import CaseStore, MemoryStore, RunLogger
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from maestro import EvidenceAction, FunctionalInterventionProfile
from maestro.acquisition import OutcomeBranch, OutcomeForecast
from maestro.decision_value_policy import FrozenDecisionValuePolicy, decision_action_binding
from maestro.models import DevelopmentAction, EvidenceScope, MechanismHypothesis
from maestro.outcome import InterpretationTable, OutcomeRule

HERE = Path(__file__).resolve().parent
PROFILE = FunctionalInterventionProfile("synthetic-drug", nominal_dose=1.0, time_hours=24.0, context_identifier="cell-a")
HYPOTHESES = (
    MechanismHypothesis("a", "Synthetic explanation A; no biological truth is asserted.", DevelopmentAction.CONTINUE,
                        causal_factor="incomplete_perturbation"),
    MechanismHypothesis("b", "Synthetic explanation B; no biological truth is asserted.", DevelopmentAction.REVISE_INTERVENTION,
                        causal_factor="pathway_compensation"),
)
RULES = (
    OutcomeRule("match-a", "a", frozenset({"matches:a"}), eliminates=frozenset({"b"}), scope=EvidenceScope.MECHANISM_CONTRAST),
    OutcomeRule("match-b", "b", frozenset({"matches:b"}), eliminates=frozenset({"a"}), scope=EvidenceScope.MECHANISM_CONTRAST),
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2, default=str) + "\n").encode("utf-8")
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def action(identifier: str) -> EvidenceAction:
    return EvidenceAction(identifier, "Synthetic engineering assay; not a real experiment", 10.0, ("a", "b"),
                          readout="response", time_hours=24.0,
                          expected_conditions={"dose": "1uM", "assay": "synthetic", "platform": "fixture"},
                          expected_outcomes={"a": "a", "b": "b"})


class FixedInterpreter:
    def interpret(self, user_message: str) -> TaskIntent:
        return TaskIntent(
            task_type="mechanism_diagnosis", research_question=user_message,
            target_or_targets=("SYNTHETIC_TARGET",), interventions=("synthetic-drug",),
            biological_context="cell-a", phenotype_endpoint="viability", supplied_evidence=(),
            constraints=("Engineering fixture only: no measurement, biological mechanism or efficacy is established.",
                         "Propose action_identifier flat; the independent execution gate may override or refuse this proposal.",
                         "Use exactly outcome_categories a and b, with an explicit no-biological-proof interpretation boundary."),
            missing_information=(), needs_visual_review=False,
        )


class AuditedDeepSeekClient(DeepSeekChatClient):
    def __init__(self, settings: MAESTROSettings, directory: Path):
        super().__init__(settings)
        self.directory = directory
        self.scenario = "unset"
        self.request_count = 0
        self.records = []
        self.decoded = {}

    def safe_error(self, error: BaseException) -> str:
        return str(error).replace(self.settings.api_key, "<redacted>")

    def _send(self, request):
        self.request_count += 1
        stem = f"{self.request_count:02d}_{self.scenario}"
        request_path = self.directory / (stem + "_request.json")
        body = request.data or b""
        if self.settings.api_key.encode() in body:
            raise ValueError("Credential found in request body; audit will not persist it.")
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_bytes(body)  # Exact JSON body; Authorization headers are never persisted.
        payload = json.loads(body)
        if payload.get("max_tokens", 0) > 1600:
            raise ValueError("Configured output budget exceeded.")
        started = time.perf_counter()
        record = {"request_number": self.request_count, "scenario": self.scenario, "started_utc": now(),
                  "request_path": str(request_path.relative_to(HERE)), "request_sha256": hashlib.sha256(body).hexdigest(),
                  "requested_model": payload["model"], "max_tokens": payload["max_tokens"],
                  "timeout_seconds": self.settings.timeout_seconds, "transport_attempt_limit": 1,
                  "provider_host": urlsplit(request.full_url).hostname, "authorization_header_persisted": False}
        try:
            # Preserve the workspace's actual request construction, model aliases and protocol decoder.
            # Only this research process disables the client's otherwise automatic transport retries.
            with patch.object(llm_module, "_MAX_ATTEMPTS", 1):
                response = super()._send(request)
            serialized = json.dumps(response, ensure_ascii=False)
            if self.settings.api_key in serialized:
                raise ValueError("Credential found in provider envelope; response will not be persisted.")
            response_path = self.directory / (stem + "_response.json")
            response_hash = write_json(response_path, response)
            record.update(status="provider_response_received", response_path=str(response_path.relative_to(HERE)),
                          response_sha256=response_hash, usage=response.get("usage"), provider_response_id=response.get("id"),
                          response_model=response.get("model"))
            return response
        except Exception as error:
            record.update(status="failed", error_type=type(error).__name__, error=self.safe_error(error),
                          usage=None, monetary_cost=None)
            raise
        finally:
            record["elapsed_seconds"] = time.perf_counter() - started
            self.records.append(record)
            write_json(self.directory / (stem + "_receipt.json"), record)

    def complete_json(self, messages, **kwargs):
        result, response = super().complete_json(messages, **kwargs)
        self.decoded[self.scenario] = result
        write_json(self.directory / f"{self.request_count:02d}_{self.scenario}_decoded.json", result)
        return result, response


class SyntheticForecaster:
    name = "synthetic-engineering-fixture"

    def __init__(self, forecasts):
        self.forecasts = forecasts
        self.calls = 0

    def forecast(self, *args, **kwargs):
        self.calls += 1
        return self.forecasts


def fixture(directory: Path, actions, *, all_flat: bool, shifted: bool):
    calibration_revision = write_json(directory / "synthetic_calibration.json", {
        "scope": "Synthetic engineering declarations only, not measured calibration or a biological certificate.",
        "declared_reference_units": 20, "branch_support": 100, "all_flat": all_flat, "shifted": shifted})
    source_revision = write_json(directory / "synthetic_source.json", {
        "scope": "Artificial likelihood table; no observed outcome is present.",
        "hypotheses": asdict(HYPOTHESES[0]), "alternative": asdict(HYPOTHESES[1]),
        "profile": asdict(PROFILE), "actions": [asdict(a) for a in actions]})
    data = {"schema_version": "1.0", "endpoint": "viability", "wrong_decision_loss": 4.0, "defer_loss": 1.0,
            "minimum_reference_units": 10, "minimum_branch_support": 10,
            "measurement_costs": {a.identifier: 0.1 for a in actions}, "admissions": {}}
    for a in actions:
        data["admissions"][a.identifier] = {
            "admission_status": "admitted", "calibration_status": "calibrated", "model_version": "engineering-fixture-1",
            "endpoint": "viability", "readout": "response", "context": "cell-a", "reference_units": 20,
            "in_distribution": not shifted, "shift_flags": ["platform"] if shifted else [],
            "calibration_id": "synthetic-engineering-reference", "calibration_revision": calibration_revision,
            "source_revision": source_revision, "binding_sha256": decision_action_binding(a, PROFILE, "viability")}
    receipt_path = directory / "evaluation_receipt.json"
    receipt_hash = write_json(receipt_path, data)
    policy = FrozenDecisionValuePolicy.from_receipt(receipt_path, receipt_hash)
    forecasts = {}
    for a in actions:
        p = 0.5 if all_flat or a.identifier == "flat" and not shifted else 0.99
        provenance = {key: policy.admissions[a.identifier][key]
                      for key in ("calibration_id", "calibration_revision", "source_revision", "binding_sha256")}
        provenance.update(in_distribution="true", shift_status="none")
        forecasts[a.identifier] = OutcomeForecast(
            a.identifier, (OutcomeBranch("a", {"a": p, "b": 1 - p}, 100),
                           OutcomeBranch("b", {"a": 1 - p, "b": p}, 100)),
            model_version="engineering-fixture-1", provenance=provenance)
    write_json(directory / "synthetic_forecasts.json", {key: asdict(value) for key, value in forecasts.items()})
    return policy, forecasts


def events(directory: Path) -> list[dict]:
    path = directory / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def run() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = HERE / "runs" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    settings = replace(MAESTROSettings.from_workspace(WORKSPACE), log_directory=directory,
                       timeout_seconds=45.0, max_tokens=1600)
    client = AuditedDeepSeekClient(settings, directory / "provider")
    definitions = [("informative_overrides_flat", False, False, ("flat", "useful"), ["useful"]),
                   ("all_flat_refuses", True, False, ("flat",), []),
                   ("external_shift_refuses", False, True, ("flat",), [])]
    frozen = {"scope": "Actual configured provider smoke audit with synthetic engineering scenarios; no scientific effect is tested.",
              "frozen_utc": now(), "scenarios": definitions, "model": settings.chat_model,
              "max_provider_requests": 3, "max_tokens_per_request": 1600, "timeout_seconds": 45,
              "transport_attempt_limit": 1, "planner_contract_retries": 0, "enable_llm_repair": False,
              "max_repair_attempts": 0, "measurement_imports_permitted": False,
              "task_interpretation": "Fixed TaskIntent; no API triage", "hypothesis_identifiers": ["a", "b"],
              "hypothesis_definitions": [asdict(h) for h in HYPOTHESES]}
    freeze_hash = write_json(directory / "PROTOCOL.json", frozen)
    results = []
    for name, all_flat, shifted, identifiers, expected in definitions:
        case_directory = directory / name
        actions = tuple(action(identifier) for identifier in identifiers)
        policy, forecasts = fixture(case_directory, actions, all_flat=all_flat, shifted=shifted)
        forecaster = SyntheticForecaster(forecasts)
        memory = MemoryStore(case_directory / "memory.sqlite")
        store = CaseStore(case_directory / "cases.sqlite")
        store.open_case(name, budget=10.0)
        planner = MechanismContrastPlanner(client, contract_retries=0)
        controller = MAESTROOrchestrator(
            interpreter=FixedInterpreter(), context_builder=ContextBuilder(EvidenceLedger(case_directory / "evidence.sqlite"), memory),
            planner=planner, visual_inspector=VisualInspector(TemplateCompleter({}), "unused"), memory=memory,
            logger=RunLogger(case_directory), case_store=store, interpretation_table=InterpretationTable(RULES),
            outcome_forecaster=forecaster, selection_strategy="decision_value", decision_value_policy=policy,
            forecast_failure_policy="stop", enable_llm_repair=False, max_repair_attempts=0)
        before = store.snapshot(name)
        client.scenario = name
        failure = None
        turn = None
        try:
            turn = controller.run(
                "Engineering fixture: propose the registered flat action, retaining hypotheses a and b. "
                "The planned result is withheld and may establish no biological fact. "
                "Return outcome_categories exactly [a,b] and a no-biological-proof interpretation boundary.",
                available_actions=actions, intervention_profile=PROFILE, case_id=name, budget=10.0,
                expected_hypothesis_identifiers=("a", "b"), expected_hypotheses=HYPOTHESES,
                session_id=name)
        except Exception as error:
            failure = {"type": type(error).__name__, "message": client.safe_error(error)}
        after = store.snapshot(name)
        logged = events(case_directory)
        selections = [x["payload"] for x in logged if x["kind"] == "decision_value_selection_computed"]
        gates = [x["payload"] for x in logged if x["kind"] == "decision_value_execution_gate"]
        checks = {
            "actual_planner_requested_flat": client.decoded.get(name, {}).get("action_identifier") == "flat",
            "expected_action_selection": turn is not None and [a.identifier for a in turn.selected_actions] == expected,
            "registered_hypotheses_preserved": turn is not None and turn.contrast is not None and turn.contrast.hypotheses == HYPOTHESES,
            "spent_unchanged": before.spent == after.spent == 0,
            "remaining_budget_unchanged": before.remaining_budget == after.remaining_budget == 10,
            "no_measurement_results": store.result_identities(name) == (),
            "no_terminal_evidence": controller.evidence_state(name) is None,
            "no_measured_profile_fields": not PROFILE.measured_fields,
            "execution_gate_matches": bool(gates) and gates[-1]["submitted_action_ids"] == expected,
            "selection_gate_present": bool(selections),
            "no_fallback": not any(x["kind"] == "outcome_forecast_fallback" for x in logged),
            "no_llm_repair": turn is not None and turn.llm_repair is None,
            "shift_refused_before_forecast": not shifted or forecaster.calls == 0,
        }
        result = {"scenario": name, "status": "pass" if failure is None and all(checks.values()) else "fail",
                  "failure": failure, "checks": checks, "raw_planner_proposal": client.decoded.get(name),
                  "selected_action_ids": [a.identifier for a in turn.selected_actions] if turn else None,
                  "case_before": asdict(before), "case_after": asdict(after),
                  "repair_stop_reason": turn.repair_stop_reason if turn else None,
                  "forecaster_calls": forecaster.calls, "selection_gates": selections, "execution_gates": gates,
                  "receipt_sha256": policy.receipt_sha256,
                  "scope": "Engineering compatibility and authority only; synthetic calibration is not scientific certification."}
        write_json(case_directory / "AUDIT.json", result)
        results.append(result)
        print(json.dumps({"scenario": name, "status": result["status"], "selected_action_ids": result["selected_action_ids"],
                          "failure": failure, "checks_failed": [key for key, passed in checks.items() if not passed]}), flush=True)
    usage = client.provider_usage
    report = {"scope": frozen["scope"], "protocol_sha256": freeze_hash, "run_directory": str(directory.relative_to(HERE)),
              "actual_http_requests": client.request_count, "provider_reported_usage": usage,
              "monetary_cost": None, "monetary_cost_status": "No authenticated price or billing receipt; not inferred from tokens.",
              "all_scenarios_pass": all(x["status"] == "pass" for x in results), "scenarios": results,
              "provider_calls": client.records, "scientific_decision_gain_established": False,
              "llm_incremental_value_established": False, "real_measurements_created": 0}
    write_json(directory / "RESULTS.json", report)
    write_json(HERE / "LATEST.json", {"results": str((directory / 'RESULTS.json').relative_to(HERE)),
                                     "all_scenarios_pass": report["all_scenarios_pass"], "provider_usage": usage})
    print(json.dumps({"all_scenarios_pass": report["all_scenarios_pass"], "actual_http_requests": client.request_count,
                      "provider_usage": usage, "results": str(directory / "RESULTS.json")}), flush=True)
    return 0 if report["all_scenarios_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
