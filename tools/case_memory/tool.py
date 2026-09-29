"""Registered runtime entry for the case-memory tool.

File summary
- Path: tools/case_memory/tool.py
- Purpose: `run(parameters)` reads a typed open-problem JSON and returns the full case-memory
  contract: retrieval explanations, adaptation differences, hypothesis-conditional forecast
  branches with probabilities and support counts, calibration status, applicability, abstention
  reason, a decision-valued next-action ranking and the branching interpretation plan. Every
  forecast is a planning-only model prediction; insufficient input returns a typed refusal.
- Core points:
  - Production invocations require MAESTRO_CASE_MEMORY_ENABLED; with the flag unset the tool
    refuses with `case_memory_disabled`.
  - Research evaluation is explicit and separate: `research_mode=true` is honoured only when the
    problem JSON declares `"evaluation": true`, and the receipt is stamped
    `mode: research_evaluation` - it can never be mistaken for a production answer.
- Depends on: src/maestro/{case_memory,directional,adaptive_retrieval,hypothesis_forecast,
  case_update,models,outcome}.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from maestro import case_memory as CM  # noqa: E402
from maestro import case_update as CU  # noqa: E402
from maestro import adaptive_retrieval as DR  # noqa: E402
from maestro import hypothesis_forecast as HF  # noqa: E402
from maestro.models import EvidenceAction, MechanismContrast, MechanismHypothesis  # noqa: E402


def _refused(reason: str, *limitations: str) -> dict:
    return {"schema_version": "1.0", "status": "refused", "reason": reason,
            "observations": [], "limitations": list(limitations), "artifacts": []}


def _user_state(payload: dict) -> HF.UserStateContext:
    context = payload.get("context", {})
    state = DR.directional_state_from_shift(payload.get("signed_feature_delta", {}),
                                            payload.get("gene_sets", {}))
    return HF.UserStateContext(
        directional_state=state,
        cell_state_summaries=payload.get("cell_state_summaries", {}),
        intervention_identity=payload.get("intervention", ""),
        chemical_structure=payload.get("chemical_structure"),
        cell_context=context.get("cell_line"),
        time_h=context.get("time_h"),
        dose_nM=context.get("dose_nM"),
        assay=payload.get("assay", ""),
        hypothesis_graph=payload.get("hypothesis_graph", {}),
        evidence_history=tuple(payload.get("evidence_history", ())),
        biological_system=payload.get("biological_system", ""),
        intervention_type=payload.get("intervention_type", ""),
        measurement_type=payload.get("measurement_type", ""),
        control_design=payload.get("control_design", ""),
        laboratory=payload.get("laboratory", ""),
        outcome_mode=payload.get("outcome_mode", "valid_readout"),
    )


def run(parameters: dict) -> dict:
    """Execute one case-memory query and return a strict JSON receipt."""

    path = Path(str(parameters.get("dataset_path", "")))
    if not path.is_file():
        return _refused("dataset_path_missing", "The supplied problem JSON does not exist.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return _refused("malformed_input", str(error))
    if not isinstance(payload, dict):
        return _refused("malformed_input", "The problem JSON must be an object.")
    hypotheses = payload.get("hypotheses")
    if not isinstance(hypotheses, list) or len(hypotheses) != 2 or not all(
            isinstance(h, str) and h.strip() for h in hypotheses):
        return _refused("invalid_problem", "The problem must name exactly two competing hypotheses.")
    if payload.get("requires_control", True) and not str(payload.get("control_design", "")).strip():
        return _refused("missing_control",
                        "The problem declares treated conditions without a control design.")
    research_mode = bool(parameters.get("research_mode", False))
    if research_mode and payload.get("evaluation") is not True:
        return _refused("research_mode_requires_evaluation_payload",
                        "research_mode is honoured only for problem files that declare "
                        '"evaluation": true; a normal runtime invocation must use the enabled '
                        "production flag.")
    if not research_mode and not CM.case_memory_enabled():
        return _refused("case_memory_disabled",
                        "The case memory is disabled by default; set MAESTRO_CASE_MEMORY_ENABLED "
                        "for production or pass research_mode with an evaluation payload.")
    arm = DR.FeatureArm(parameters.get("feature_arm", "combined"))
    top_k = int(parameters.get("top_k", 5))
    store_ref = payload.get("episode_store")
    store = CM.EpisodeStore(ROOT / store_ref) if store_ref else CM.EpisodeStore()
    user_state = _user_state(payload)
    h1, h2 = hypotheses
    contrast = MechanismContrast("case-memory-query",
                                 (MechanismHypothesis(h1, h1), MechanismHypothesis(h2, h2)), (), None)
    action_payloads = payload.get("actions") or [{
        "action_id": "query:primary", "description": "the queried measurement",
        "assay": payload.get("assay", ""), "cost_wells": 8.0, "duration_days": 2.0,
        "readout": payload.get("measurement_type", ""),
    }]
    actions = tuple(
        EvidenceAction(str(a["action_id"]), str(a.get("description", a["action_id"])),
                       float(a.get("cost_wells", 1.0)), (h1, h2),
                       readout=str(a.get("readout", "")), time_hours=a.get("time_h"),
                       execution_context=a.get("cell_line"),
                       expected_outcomes=a.get("expected_outcomes", {h1: "match_h1", h2: "match_h2"}))
        for a in action_payloads)
    forecaster = HF.CaseMemoryOutcomeForecaster(store, feature_arm=arm, research_mode=research_mode)
    detailed = {a.identifier: forecaster.forecast_detailed(contrast, a, None, user_state)
                for a in actions}
    usable = {h: d["applicable"] for h, d in ((a.identifier, d) for a, d in
              ((a, detailed[a.identifier]) for a in actions))}
    if not any(d["applicable"] for d in detailed.values()):
        first = next(iter(detailed.values()), {})
        return {"schema_version": "1.0", "status": "abstained",
                "reason": first.get("abstain_reason") or "insufficient_support",
                "mode": "research_evaluation" if research_mode else "production",
                "calibration_status": first.get("calibration_status", HF.CALIBRATION_STATUS),
                "model_version": HF.MODEL_VERSION, "observations": [],
                "limitations": ["No hypothesis branch met the minimum independent support; the "
                                "system abstains rather than fabricating a forecast."],
                "artifacts": []}
    # Retrieval explanations come from the forecaster's retriever on the same problem.
    from maestro.adaptive_retrieval import RetrievalProblem
    from maestro.adaptive_retrieval import ContextFeatures

    problem = RetrievalProblem(
        problem_id=payload.get("problem_id", "unnamed"),
        biological_system=payload.get("biological_system", ""),
        assay=payload.get("assay", ""), intervention_type=payload.get("intervention_type", ""),
        measurement_type=payload.get("measurement_type", ""),
        control_design=payload.get("control_design", ""),
        context=ContextFeatures(cell_line=user_state.cell_context, time_h=user_state.time_h,
                                dose_nM=user_state.dose_nM),
        hypotheses=(h1, h2), state=user_state.directional_state, feature_arm=arm)
    retrieval = forecaster.retriever.retrieve(problem, top_k=top_k, research_mode=True)
    candidate_actions = tuple(
        CM.CandidateAction(str(a["action_id"]), str(a.get("description", a["action_id"])),
                           str(a.get("assay", "")), float(a.get("cost_wells", 1.0)),
                           float(a.get("duration_days", 1.0)), str(a.get("readout", "")))
        for a in action_payloads)
    consequences = {str(label): frozenset(eliminated)
                    for a in action_payloads
                    for label, eliminated in (a.get("consequences") or {}).items()}
    forecasts = {a.identifier: forecaster.forecast(contrast, (a,), None, user_state)[a.identifier]
                 for a in actions}
    rankings = CU.rank_actions_by_decision_value((h1, h2), candidate_actions, forecasts,
                                                 consequences or {"match_h1": frozenset((h2,)),
                                                                  "match_h2": frozenset((h1,))})
    plans = {a.action_id: {"on_outcome": dict(p.on_outcome), "on_ambiguous": p.on_ambiguous,
                           "on_invalid": p.on_invalid}
             for a in candidate_actions
             for p in (CU.branching_interpretation_plan(a, sorted(consequences) or ["match_h1", "match_h2"]),)}
    observations = []
    for action in actions:
        d = detailed[action.identifier]
        observations.append({
            "action_identifier": action.identifier,
            "applicable": d["applicable"],
            "abstain_reason": d["abstain_reason"],
            "branches": d["branches"],
            "support": d["support"],
            "calibration_status": d["calibration_status"],
            "calibration_dataset": d["calibration_dataset"],
            "model_version": d["model_version"],
            "outcome_mode": d["outcome_mode"],
            "decision_applicable": d["decision_applicable"],
            "calibration_fit": d["calibration_fit"],
            "regularisation": d["regularisation"],
            "provenance": d["provenance"],
        })
    retrieval_view = {
        hypothesis: {
            "usable": retrieval.usable[hypothesis],
            "kish_effective_precedents": round(retrieval.kish[hypothesis], 3),
            "reason": retrieval.reason[hypothesis],
            "precedents": [
                {"case_id": p.case_id, "score": p.score, "components": p.components,
                 "matches": list(p.matches), "differences": p.differences,
                 "adaptation": p.adaptation, "why": p.why}
                for p in retrieval.precedents[hypothesis]],
        }
        for hypothesis in (h1, h2)
    }
    return {
        "schema_version": "1.0", "status": "ok",
        "mode": "research_evaluation" if research_mode else "production",
        "feature_arm": arm.value,
        "calibration_status": HF.CALIBRATION_STATUS,
        "model_version": HF.MODEL_VERSION,
        "stage1": {"eligible": list(retrieval.stage1.eligible),
                   "excluded": dict(retrieval.stage1.excluded)},
        "retrieval": retrieval_view,
        "observations": observations,
        "action_ranking": [
            {"action_id": r.action_id, "net_value": round(r.net_value, 6),
             "expected_terminal_decision_value": round(r.expected_terminal_decision_value, 6),
             "hypothesis_discrimination": round(r.hypothesis_discrimination, 6),
             "measurement_cost": r.measurement_cost, "admissible": r.admissible,
             "reason": r.reason}
            for r in rankings],
        "branching_interpretation_plan": plans,
        "limitations": ["Forecasts are planning-only model predictions with calibration status "
                        "'uncalibrated'; they admit no evidence and update no hypothesis."],
        "artifacts": [],
    }


if __name__ == "__main__":  # pragma: no cover - manual invocation
    print(json.dumps(run(json.loads(sys.argv[1])), indent=2, sort_keys=True))
