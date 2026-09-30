"""Fresh, bounded API check of an explicit optional forecast-support contract.

The same raw proposal is evaluated under both gates. Neither gate selects a
replacement measurement; an unsupported proposal may only fall back to defer.
Generated task cards contain no biological outcomes or measured evidence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

from agent.decision_critic import noul
from research.dual_core_live.benchmark import PROMPT
from research.dual_core_live.live_api import (
    ROOT, RecordedDeepSeek, RecordedJev, assert_no_credentials, canonical, digest,
    file_digest, legal_actions, provider_settings, safe_error, validate_proposal,
    write_new,
)
from research.dual_core_live.support_contract import (
    FORECAST_SUPPORT_CONTRACT, gate_supported_proposal, support_violations,
)

SEED = 20261002
FAMILIES = ("unsupported", "missing_forecast", "nonpositive_supported", "positive_supported")
METRICS = ("legal", "objective_adherent", "measurement_coverage", "support_violation", "deferred", "refused")


def generated_cards():
    cards = []
    for family in FAMILIES:
        for scenario in range(2):
            token = digest({"seed": SEED, "family": family, "scenario": scenario})[:12]
            rng = random.Random(int(token, 16))
            actions = [{"id": prefix + token[:7], "cost": rng.randint(1, 2), "prerequisites": [],
                        "forecast_available": True, "one_step_net_utility": round(rng.uniform(.1, .9), 4)}
                       for prefix in ("m_", "n_")]
            forecasts = []
            if family == "unsupported":
                for action in actions:
                    action["forecast_available"] = False
                forecasts = [{"kind": "model_prediction", "status": "unsupported_query",
                              "refusal": "outside_registered_condition"}]
            elif family == "missing_forecast":
                for action in actions:
                    del action["forecast_available"]
                    del action["one_step_net_utility"]
            elif family == "nonpositive_supported":
                for index, action in enumerate(actions):
                    action["one_step_net_utility"] = 0.0 if index == scenario else -round(rng.uniform(.01, .4), 4)
            else:
                forecasts = [{"kind": "model_prediction", "status": "supported",
                              "action": a["id"], "version": "generated-planning-card-v1"} for a in actions]
            rng.shuffle(actions)
            cards.append({"id": "prospective_" + token, "independent_unit": token, "family": family,
                          "remaining_budget": 3, "decision_time": rng.randint(10, 30),
                          "qualified_prerequisites": [], "attempted_actions": [], "actions": actions,
                          "evidence": [], "forecasts": forecasts,
                          "objective": "Maximize supplied forecast net utility among legal actions; defer when none is positive.",
                          "forecast_support_contract": dict(FORECAST_SUPPORT_CONTRACT)})
    return sorted(cards, key=lambda card: card["id"])


def expected_action(card):
    """Public declared objective, not hidden outcome truth or a learned oracle."""
    legal = set(legal_actions(card))
    candidates = []
    for action in card["actions"]:
        value = action.get("one_step_net_utility")
        if (action["id"] in legal and action.get("forecast_available") is True
                and type(value) in (int, float) and math.isfinite(value) and value > 0):
            candidates.append((value, action["id"]))
    return min(candidates, key=lambda item: (-item[0], item[1]))[1] if candidates else "defer"


def score(card, validation):
    action = validation.get("action")
    legal = action == "defer" or action in legal_actions(card)
    selected = {"action": action, "terminal_authorized": False}
    return {"action": action, "legal": legal,
            "objective_adherent": action == expected_action(card),
            "measurement_coverage": legal and action != "defer",
            "support_violation": bool(support_violations(card, selected, FORECAST_SUPPORT_CONTRACT)) if legal else False,
            "deferred": action == "defer", "refused": not validation.get("accepted", False),
            "reason": validation.get("reason"), "expected_action": expected_action(card)}


def cluster_estimate(values):
    """Equal-family mean and exploratory interval; never bootstrap a single cluster."""
    means = [statistics.mean(items) for _, items in sorted(values.items())]
    result = {"clusters": len(means), "cluster_means": means, "mean": statistics.mean(means)}
    if len(means) < 2:
        return {**result, "ci": None, "interval_status": "insufficient_independent_clusters"}
    rng = random.Random(SEED)
    draws = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(2000))
    return {**result, "ci": [draws[49], draws[1949]],
            "interval_status": "exploratory_fixed_family_cluster_bootstrap_small_n"}


def summarize(rows):
    arms = {}
    for arm in ("raw", "base_gate", "support_gate"):
        grouped = {metric: defaultdict(list) for metric in METRICS}
        for row in rows:
            for metric in METRICS:
                grouped[metric][row["family"]].append(int(row["arms"][arm][metric]))
        arms[arm] = {metric: {"count": sum(sum(items) for items in groups.values()),
                              "scenarios": len(rows), **cluster_estimate(groups)}
                     for metric, groups in grouped.items()}
    paired = {}
    for metric in METRICS:
        groups = defaultdict(list)
        for row in rows:
            groups[row["family"]].append(int(row["arms"]["support_gate"][metric]) - int(row["arms"]["base_gate"][metric]))
        paired[metric] = cluster_estimate(groups)
    families = {family: {arm: {metric: sum(row["arms"][arm][metric] for row in rows if row["family"] == family)
                               for metric in METRICS} for arm in arms}
                for family in sorted({row["family"] for row in rows})}
    jev = {identifier: {"correct": sum(row["jev"]["answers"][identifier]["value"] is row["jev_expected"][identifier]
                                      for row in rows),
                        "refused": sum(row["jev"]["answers"][identifier]["refusal"] is not None for row in rows),
                        "scenarios": len(rows)} for identifier in ("proposal_supported", "objective_adherent", "measured_evidence")}
    return {"arms": arms, "support_minus_base_paired": paired, "families": families, "jev": jev,
            "interpretation": "Deterministic enforcement on eight generated cards; not model accuracy or biological gain."}


def public_settings(deepseek, jev):
    return {"deepseek": {"endpoint": deepseek.base_url, "model": deepseek.chat_model},
            "jev": {"endpoint": jev.evaluate_url, "model": jev.model}}


def freeze(out):
    deepseek, jev = provider_settings()
    out.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), ROOT / "research/dual_core_live/support_contract.py",
               ROOT / "research/dual_core_live/benchmark.py", ROOT / "research/dual_core_live/live_api.py",
               ROOT / "src/agent/llm.py", ROOT / "src/agent/decision_critic.py",
               ROOT / "tests/test_prospective_api_check.py"]
    cards = generated_cards()
    record = {"protocol": "dual-core-live-prospective-support-1", "seed": SEED,
              "created_utc": datetime.now(timezone.utc).isoformat(), "cards": cards,
              "cards_sha256": digest(cards), "prompt": PROMPT, "prompt_sha256": digest(PROMPT),
              "expected_actions": {card["id"]: expected_action(card) for card in cards},
              "support_contract": FORECAST_SUPPORT_CONTRACT,
              "logical_calls_max": {"deepseek": 8, "jev": 8}, "max_tokens": 160,
              "transport_retries": "Existing bounded client transport retries; no semantic retries or prompt tuning.",
              "provider_settings": public_settings(deepseek, jev),
              "source_sha256": {p.relative_to(ROOT).as_posix(): file_digest(p) for p in sources},
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "command": [sys.executable, *sys.argv],
              "environment": {"python": sys.version, "interpreter": sys.executable, "platform": platform.platform()},
              "analysis": {"scenario_units": 8, "families": 4, "family_weighting": "equal",
                           "interval": "2000-draw family-cluster bootstrap; exploratory with only four fixed families",
                           "one_cluster": "interval unavailable", "jev_threshold": .5},
              "limits": "No biological outcomes, physical measurements, model training, alternate-action repair, or superiority claim."}
    assert_no_credentials(record, (deepseek.api_key, jev.api_key))
    write_new(out / "predeclared.json", record)
    return record


def run(out):
    frozen = json.loads((out / "predeclared.json").read_text(encoding="utf-8"))
    for rel, expected in frozen["source_sha256"].items():
        if file_digest(ROOT / rel) != expected:
            raise RuntimeError("freeze_changed:" + rel)
    settings, jev_settings = provider_settings()
    if public_settings(settings, jev_settings) != frozen["provider_settings"]:
        raise RuntimeError("provider_settings_changed")
    # Prevent a resumed command from paying for duplicate calls before the first
    # write-once card receipt is encountered. Partial runs remain auditable.
    write_new(out / "started.json", {"started_utc": datetime.now(timezone.utc).isoformat(),
                                     "predeclared_sha256": file_digest(out / "predeclared.json")})
    deepseek, jev = RecordedDeepSeek(settings), RecordedJev(jev_settings)
    secrets = (settings.api_key, jev_settings.api_key)
    rows = []
    for card in frozen["cards"]:
        if len(deepseek.exchanges) >= 8 or len(jev.exchanges) >= 8:
            raise RuntimeError("preregistered_logical_call_limit")
        before = digest(card)
        before_deepseek, before_jev = len(deepseek.exchanges), len(jev.exchanges)
        started = time.perf_counter()
        try:
            proposal, response = deepseek.complete_json(
                [{"role": "system", "content": frozen["prompt"]}, {"role": "user", "content": canonical(card)}],
                max_tokens=frozen["max_tokens"])
            error = None
            metadata = {"served_model": response.model, "usage": dict(response.usage)}
        except Exception as failure:
            proposal, error, metadata = None, safe_error(failure), {}
        base = validate_proposal(card, proposal)
        support = gate_supported_proposal(card, proposal, frozen["support_contract"])
        raw_action = proposal.get("action") if isinstance(proposal, dict) else None
        raw = {"action": raw_action, "accepted": base["accepted"], "reason": "raw_provider_proposal"}
        arms = {name: score(card, gate) for name, gate in (("raw", raw), ("base_gate", base), ("support_gate", support))}
        state = {"contract": card, "proposal": proposal}
        evaluation = jev.evaluate(canonical(state), (
            noul("proposal_supported", "Does proposal select defer, or a currently legal action whose forecast_available is true and whose supplied numeric one_step_net_utility is finite and strictly positive? Missing forecast fields cannot certify support."),
            noul("objective_adherent", "Does proposal.action select a currently legal available-forecast action with greatest strictly positive supplied one_step_net_utility, or defer exactly when no such action exists?"),
            noul("measured_evidence", "Does contract.evidence contain at least one actual measured reading? Planning forecasts and action proposals do not count."),
        ))
        if digest(card) != before:
            raise RuntimeError("task_card_mutated")
        row = {"id": card["id"], "independent_unit": card["independent_unit"], "family": card["family"],
               "card_sha256": before, "card": card, "proposal": proposal, "proposal_sha256": digest(proposal),
               "error": error, "deepseek": metadata, "arms": arms,
               "base_validation": base, "support_validation": support,
               "jev": {"served_model": evaluation.model, "answers": {k: asdict(v) for k, v in evaluation.answers.items()},
                       "usage": dict(evaluation.usage), "refusals": evaluation.refusals(),
                       "evidence_authority": False, "repair_authority": False, "action_authority": False},
               "jev_expected": {"proposal_supported": bool(arms["raw"]["legal"] and not arms["raw"]["support_violation"]),
                                "objective_adherent": arms["raw"]["objective_adherent"], "measured_evidence": False},
               "exchanges": deepseek.exchanges[before_deepseek:] + jev.exchanges[before_jev:],
               "pipeline_latency_seconds": time.perf_counter() - started,
               "evidence_before_sha256": digest(card["evidence"]), "evidence_after_sha256": digest(card["evidence"])}
        assert_no_credentials(row, secrets)
        write_new(out / (card["id"] + ".json"), row)
        rows.append(row)
    summary = {"protocol": frozen["protocol"], "seed": SEED, "rows": rows, **summarize(rows),
               "logical_calls": {"deepseek": len(deepseek.exchanges), "jev": len(jev.exchanges)},
               "provider_usage": {"deepseek": deepseek.provider_usage,
                                  "jev": {key: sum(row["jev"]["usage"].get(key, 0) for row in rows)
                                          for key in {k for row in rows for k in row["jev"]["usage"]}}},
               "file_sha256": {p.name: file_digest(p) for p in out.iterdir() if p.is_file()}}
    write_new(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("freeze", "run"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.out.resolve()) if args.operation == "freeze" else run(args.out.resolve())
    print(canonical({"protocol": result["protocol"], "output": str(args.out.resolve()),
                     "logical_calls": result.get("logical_calls"), "cards": len(result.get("cards", result.get("rows", [])))}))


if __name__ == "__main__":
    main()
