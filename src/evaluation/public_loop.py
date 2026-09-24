"""Reproducible PRISM dry loop; real fitted data never masquerade as raw assays.

Run in maestro: python -m evaluation.public_loop --output log/YYYYMMDD/public_loop
The reviewed-template arm checks software integration, not autonomous LLM ability.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from agent.audit import RunLogger
from agent.cases import CaseStore, MeasurementResult
from agent.cli import _json_default
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.template_client import TemplateCompleter
from agent.tool_runtime import ToolRouter
from agent.vision import VisualInspector
from maestro import EvidenceAction, EvidenceKind, FunctionalInterventionProfile
from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
from virtual_cell.state_adapter import StateAdapterConfig, StateCapabilityAdapter


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, default=_json_default, allow_nan=False) + "\n", encoding="utf-8")


def run(workspace: Path, output: Path, *, client_factory=None) -> dict:
    """Use reviewed templates by default; an injected provider is a separate live arm."""
    output.mkdir(parents=True, exist_ok=True)
    raw = workspace / "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv"
    provenance = json.loads(raw.with_suffix(".csv.provenance.json").read_text(encoding="utf-8"))
    with raw.open("rb") as stream:
        digest = hashlib.file_digest(stream, "md5").hexdigest()
    if digest != provenance["declared_md5"]:
        raise ValueError("public_data_digest_mismatch")
    question = ("Assess EGFR genetic dependency versus osimertinib response in SNU761 (ACH-000537). "
                "Review the public PRISM curve, check virtual-cell applicability, and request matched functional "
                "evidence before mechanistic attribution. No matched occupancy or functional assay is supplied.")
    context_id = "ACH-000537:SNU761_LIVER"
    query = PredictionRequest("prism-state-query", "public-prism", "egfr-gap", 1,
                              Intervention("osimertinib", "drug", ("EGFR",)),
                              SystemContext(context_id, "PRISM cell line", "prism", "prism"),
                              ("viability",), "state_generalization_zeroshot_X_hvg")
    candidate_path, query_path = output / "candidate.json", output / "state_query.json"
    _write(candidate_path, {"source": provenance["figshare_doi"], "model": "ACH-000537", "drug": "osimertinib",
                            "screen": "MTS010", "measurement_values": "withheld_until_registered_result_import"})
    _write(query_path, query.to_dict())
    action = EvidenceAction("review_prism_curve", "Review the registered PRISM MTS010 fitted curve.", 1,
                            ("incomplete", "alternative"), detection_power=1,
                            expected_outcomes={"incomplete": "matched_function_low", "alternative": "matched_function_high"})
    preregistration = {
        "question": question, "hypotheses": ["incomplete", "alternative"], "action": asdict(action),
        "result_admission": "A fitted screen curve cannot eliminate either mechanistic explanation.",
        "missing_result_stop": "awaiting_result", "cost_unit": "record_retrieval",
        "lab_cost": {"wells": 0, "turnaround_days": 0}, "new_measurements": 0,
        "claim_status": "mechanism_unresolved", "raw_data_md5": digest,
        "license": "CC BY 4.0; official metadata in log/20260915/public_data_access.json",
        "design": "retrospective software validation on previously explored public data, not confirmatory preregistration",
    }
    _write(output / "preregistered_outcomes.json", preregistration)
    responses = {
        "task_triage": {"task_type": "mechanism_diagnosis", "research_question": question,
                        "target_or_targets": ["EGFR"], "interventions": ["osimertinib"],
                        "biological_context": context_id, "phenotype_endpoint": "viability",
                        "supplied_evidence": [], "constraints": [], "missing_information": [],
                        "evidence_gaps": ["matched functional assay"], "needs_visual_review": False},
        "contrast_planner": {"identifier": "egfr-gap", "hypotheses": [
            {"identifier": "incomplete", "description": "Functional EGFR perturbation is incomplete.",
             "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
            {"identifier": "alternative", "description": "Mode, timing or other targets explain the discordance.",
             "proposed_action": "revise_attribution", "causal_factor": "unresolved"}],
            "differing_assumptions": ["functional realization"], "action_identifier": action.identifier,
            "outcome_categories": ["matched_function_low", "matched_function_high"],
            "interpretation_boundaries": ["A PRISM curve is insufficient for mechanism attribution."]},
        "tool_router": [
            {"tool_id": "data_profile", "dataset_id": "dataset_1", "arguments": {}},
            {"tool_id": "virtual_cell_query", "dataset_id": "dataset_2", "arguments": {}},
            {"tool_id": None}],
    }
    _write(output / "reviewed_template.json", {"responses": responses})
    reports = {}
    for arm in ("missing_result", "public_result_import"):
        directory = output / arm
        if directory.exists():
            raise ValueError("Use a fresh output directory to preserve experiment history.")
        client = TemplateCompleter(responses) if client_factory is None else client_factory(directory)
        ledger = EvidenceLedger(directory / "evidence.sqlite")
        knowledge = ledger.load_knowledge_package(workspace / "data/knowledge/biological_constraints.json")
        memory = MemoryStore(directory / "memory.sqlite")
        controller = MAESTROOrchestrator(
            interpreter=TaskInterpreter(client), context_builder=ContextBuilder(ledger, memory),
            planner=MechanismContrastPlanner(client), visual_inspector=VisualInspector(client, "unused"),
            memory=memory, logger=RunLogger(directory), case_store=CaseStore(directory / "cases.sqlite"),
            tool_router=ToolRouter(client, workspace / "tools"), power_aware_selection=True,
            virtual_cell=StateCapabilityAdapter(StateAdapterConfig.from_workspace(workspace)),
        )

        def provider(selected, turn):
            if arm == "missing_result":
                return None
            # Values are read only after the controller writes the plan.
            with raw.open(newline="", encoding="utf-8") as stream:
                rows = [row for row in csv.DictReader(stream) if row["depmap_id"] == "ACH-000537"
                        and row["broad_id"] == "BRD-K42805893-001-04-9" and row["screen_id"] == "MTS010"]
            if len(rows) != 1:
                raise ValueError("public_result_identity_not_unique")
            row = rows[0]
            _write(directory / "original_row.json", row)
            return MeasurementResult(selected.identifier, "Public PRISM fitted curve; functional state remains unknown.",
                                     provenance["figshare_doi"] + ":ACH-000537:osimertinib:MTS010", context_id,
                                     None, None, False, metrics={key: row[key] for key in ("auc", "ec50", "ic50", "r2")},
                                     evidence_kind=EvidenceKind.DERIVED_ANALYSIS,
                                     limitations=("Unknown biological QC, independent units and matched functional assay.",),
                                     result_id="prism-original-fit")

        loop = controller.run_case_loop(question, available_actions=(action,),
                                        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier=context_id),
                                        result_provider=provider, case_id="public-prism", budget=1, max_rounds=2,
                                        expected_hypothesis_identifiers=("incomplete", "alternative"),
                                        dataset_paths=(candidate_path, query_path), prediction_request=query)
        _write(directory / "trace.json", asdict(loop))
        reports[arm] = {"stop_reason": loop.stop_reason, "knowledge_constraints_loaded": len(knowledge),
                        "tools": [item.tool_id for turn in loop.turns for item in turn.tool_executions],
                        "model_refusals": [turn.prediction.abstain_reason for turn in loop.turns if turn.prediction],
                        "surviving_hypotheses": sorted(loop.evidence_state.candidates) if loop.evidence_state else [],
                        "mechanism_updates": len(loop.evidence_state.mechanism_updates()) if loop.evidence_state else 0,
                        "reflections": [asdict(item) for item in loop.reflections],
                        "case_state": asdict(controller._case_store.snapshot("public-prism")),
                        "template_calls" if client_factory is None else "provider_calls": client.calls}
    acceptance = (reports["missing_result"]["stop_reason"] == "awaiting_result"
                  and reports["public_result_import"]["stop_reason"] == "result_quality_failed"
                  and all(item["mechanism_updates"] == 0 for item in reports.values()))
    summary = {"arms": reports, "planner": "reviewed_template_not_LLM" if client_factory is None else "live_provider",
               "acceptance_passed": acceptance, "api_cost_usd": 0 if client_factory is None else None,
               "new_experiment_wells": 0, "turnaround_days": 0,
               "conclusion": ("Public data were imported; unsupported mechanistic updates were refused. Matched measurements remain missing."
                              if acceptance else "The registered software closure was not reached; inspect arm stops. No biological success is established.")}
    _write(output / "summary.json", summary)
    if client_factory is None:
        assert acceptance, "public_loop_contract_failed; inspect summary.json"
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = run(arguments.workspace.resolve(), arguments.output.resolve())
    print(json.dumps({key: value["stop_reason"] for key, value in report["arms"].items()}))
