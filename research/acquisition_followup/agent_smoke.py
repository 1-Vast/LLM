"""One bounded live-agent episode on real SciPlex3 data, with no performance claim.

Identity, mechanism truth and unbought measurements never enter the provider prompt.
Only E.execute followed by C.evidence_update can alter the candidate hypotheses.
Run with the maestro environment; at most two requests, no transport retries.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import two_step as S
from agent.configuration import ConfigurationError, MAESTROSettings
from agent.llm import DeepSeekChatClient, LLMError
from evaluation.provider_spend import RATES, SpendLedger
from maestro.outcome import EvidenceState

C, E, V = S.C, S.E, S.V
OUT = S.ROOT / "outputs" / "acquisition_followup" / "agent"
CEILING = 0.02
RESERVATION = 0.01
SYSTEM = (
    "You are the MAESTRO experiment-planning agent. Choose one legal action or defer. "
    "The conditional reference cards are planning-only model predictions, never measured evidence "
    "about this unknown compound. A deterministic validator interprets each purchased measurement. "
    "profile_matches_h1 removes H2; profile_matches_h2 removes H1; profile_unresolved and "
    "no_detectable_response remove neither. Aim to resolve the mechanism within two measurements: "
    "correct elimination +1, wrong elimination -2, unresolved 0; compare cost after scientific value. "
    "You may plan a second measurement after seeing the first result. Reply only with JSON "
    '{"action": "<legal action id or defer>", "reason": "<at most 40 words>"}.'
)


def prompt_state(contrast, menu, state, executed, forecaster):
    actions = [E.make_action(key, *(h.identifier for h in contrast.hypotheses)) for key in menu]
    forecasts = forecaster.forecast(contrast, actions, state)
    return {
        "hypotheses": {f"H{i + 1}": h.identifier for i, h in enumerate(contrast.hypotheses)},
        "candidate_hypotheses": sorted(state.candidates),
        "measurements_remaining": 2 - len(executed),
        "legal_actions": [{"id": action.identifier, "line": key[0], "time_hours": key[1],
                           "dose_nM": key[2], "cost_days": action.cost}
                          for key, action in zip(menu, actions)],
        "results_so_far": [{k: step[k] for k in ("action", "outcome", "qc", "agreement")}
                           for step in executed],
        "planning_only_reference_cards": {
            name: {"branches": [asdict(branch) for branch in forecast.branches],
                   "basis": forecast.basis, "refusal": forecast.refusal,
                   "evidence_kind": forecast.evidence_kind.value}
            for name, forecast in forecasts.items()},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result_path = OUT / "result.json"
    if result_path.exists() or (OUT / "trace.jsonl").exists():
        raise RuntimeError("smoke_already_recorded; existing assets are preserved")
    ledger = SpendLedger.load(OUT / "deepseek_spend.json", ceiling_usd=CEILING)
    protocol, data = C.load_protocol(), C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    ctx, fold = next(E.contexts(data, protocol, detected, E.Magnitude(data, detected),
                                tier_names=("A",), folds=(1,)))
    # Episode selection is fixed before inspecting any of its measurement outcomes.
    compound, truth, decoy, h1, h2 = next(iter(E.episode_list(ctx, fold)))
    actions = [E.make_action(key, h1, h2) for key in ctx.tier.keys]
    contrast = E.contrast_for(h1, h2, actions)
    state = EvidenceState.open(contrast.hypotheses)
    forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
    executed, trace = [], []
    failure = None
    C.write_json(OUT / "manifest.json", {
        "selection": "first episode yielded in tier A fold 1, without outcome filtering",
        "max_requests": 2, "transport_attempts_per_request": 1, "timeout_seconds": 20,
        "max_completion_tokens": 240, "ceiling_usd": CEILING,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "purpose": "agent/world-model/real-measurement data-flow smoke, not efficacy evaluation",
    })
    try:
        settings = replace(MAESTROSettings.from_workspace(C.ROOT), timeout_seconds=20, max_tokens=240)
        if settings.chat_model != RATES["model"]:
            raise ValueError("unpriced_model_for_smoke_budget")
        client = DeepSeekChatClient(settings)
    except (ConfigurationError, ValueError) as error:
        failure = type(error).__name__
        client = None

    for step_number in range(1, 3) if client is not None else ():
        menu = [key for key in ctx.tier.keys if key not in [step["key"] for step in executed]
                and (not executed or key[1] >= executed[-1]["key"][1])]
        before = state
        payload = prompt_state(contrast, menu, state, executed, forecaster)
        prompt = json.dumps(C.clean(payload), default=C._default)
        assert compound not in prompt
        label = f"fixed_episode:step_{step_number}"
        entry = {"step": step_number, "prompt": payload, "before": sorted(state.candidates)}
        ledger.reserve(label, RESERVATION)
        usage_before = client.provider_usage
        try:
            with patch("agent.llm._MAX_ATTEMPTS", 1):
                answer, response = client.complete_json([
                    {"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], max_tokens=240)
        except LLMError as error:
            failure = getattr(error, "code", type(error).__name__)
            usage = {key: value - usage_before.get(key, 0) for key, value in client.provider_usage.items()
                     if key != "calls" and value != usage_before.get(key, 0)}
            ledger.charge(label, usage or None, status="failed", reserved_usd=RESERVATION, note=failure)
            entry["failure"] = failure
            assert state == before
            trace.append(entry)
            ledger.write()
            break
        ledger.charge(label, response.usage, reserved_usd=RESERVATION)
        ledger.write()
        entry.update(answer=answer, model=response.model, usage=dict(response.usage))
        assert state == before  # Forecasts and the agent answer are planning only.
        entry["unchanged_after_planning"] = True
        chosen = answer.get("action")
        if chosen == "defer":
            trace.append(entry)
            break
        by_id = {C.action_id(key): key for key in menu}
        if not isinstance(chosen, str) or chosen not in by_id:
            failure = "answer_outside_legal_menu"
            entry["failure"] = failure
            trace.append(entry)
            break
        key = by_id[chosen]
        reading = E.execute(ctx, compound, key, h1, h2)
        action = next(action for action in actions if action.identifier == chosen)
        state, interpretation, outcome = C.evidence_update(
            state, contrast, action, key, reading, h1, h2, qc=reading["qc"],
            agreement=reading["agreement"], source="sciplex3:identity_withheld")
        assert len(state.updates) == len(before.updates) + 1
        if not reading["qc"] or outcome in ("ambiguous", "undetected"):
            assert state.candidates == before.candidates
        step = {"key": key, "action": chosen, "outcome": outcome, "qc": reading["qc"],
                "agreement": reading["agreement"], "eliminated": sorted(state.eliminated)}
        executed.append(step)
        entry.update(real_measurement=step, after=sorted(state.candidates),
                     outcome_label=interpretation.outcome_label,
                     state_change_source="real_measurement_only")
        trace.append(entry)
        if state.eliminated:
            break
    ledger.write()
    with (OUT / "trace.jsonl").open("x", encoding="utf-8") as stream:
        for entry in trace:
            stream.write(json.dumps(C.clean(entry), default=C._default) + "\n")
    assert len(ledger.entries) <= 2 and ledger.total_usd <= CEILING
    result = E.finish("live_agent_smoke", compound, truth, h1, h2, state, executed,
                      "deferred" if not executed else None)
    result.update(tier="A", fold=fold, failure=failure, final_candidates=sorted(state.candidates),
                  checks={"predictions_never_update_state": True, "updates_equal_real_measurements":
                          len(state.updates) == len(executed)},
                  api_requests=len(ledger.entries), accounted_usd=ledger.total_usd,
                  performance_claim=False)
    C.write_json(result_path, result)
    print(json.dumps({k: result[k] for k in ("final", "failure", "api_requests", "accounted_usd", "checks")}))


if __name__ == "__main__":
    main()
