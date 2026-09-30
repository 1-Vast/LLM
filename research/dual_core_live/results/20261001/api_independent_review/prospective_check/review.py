"""Independent offline integrity check of the eight-card prospective API receipt."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "outputs/dual_core_live_20261001/post_fix_prospective_v1"
ORIGINAL = ROOT / "outputs/dual_core_live_20261001/fixed_benchmark_v1"
METRICS = ("legal", "objective_adherent", "measurement_coverage", "support_violation", "deferred", "refused")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks, findings = 0, []


def check(value, name, detail=None):
    global checks
    checks += 1
    if not value:
        findings.append({"check": name, "detail": detail})


def legal(card):
    return [a["id"] for a in card["actions"] if a["cost"] <= card["remaining_budget"]
            and a["id"] not in card["attempted_actions"]
            and set(a["prerequisites"]).issubset(card["qualified_prerequisites"])]


def expected(card):
    available = [a for a in card["actions"] if a["id"] in legal(card) and a.get("forecast_available") is True
                 and type(a.get("one_step_net_utility")) in (int, float)
                 and math.isfinite(a["one_step_net_utility"]) and a["one_step_net_utility"] > 0]
    return min(available, key=lambda a: (-a["one_step_net_utility"], a["id"]))["id"] if available else "defer"


def forbidden(value):
    if isinstance(value, dict):
        return bool(set(value) & {"truth", "expected_actions", "jev_expected", "score_a", "score_b", "expected_defect"}) or any(forbidden(v) for v in value.values())
    return any(forbidden(v) for v in value) if isinstance(value, list) else False


def cluster_estimate(groups):
    means = [statistics.mean(v) for _, v in sorted(groups.items())]
    rng = random.Random(20261002)
    draws = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(2000))
    return {"clusters": len(means), "cluster_means": means, "mean": statistics.mean(means),
            "ci": [draws[49], draws[1949]], "interval_status": "exploratory_fixed_family_cluster_bootstrap_small_n"}


frozen = read(RUN / "predeclared.json")
summary = read(RUN / "summary.json")
original = read(ORIGINAL / "predeclared.json")
started = read(RUN / "started.json")
check(frozen["seed"] == 20261002 and len(frozen["cards"]) == 8, "frozen_population_seed")
check(frozen["logical_calls_max"] == {"deepseek": 8, "jev": 8}, "frozen_call_cap")
check(frozen["prompt"].encode("utf-8") == original["prompt"].encode("utf-8"), "prompt_byte_identical_original")
check(frozen["prompt_sha256"] == digest(frozen["prompt"]), "prompt_sha256")
check(frozen["cards_sha256"] == digest(frozen["cards"]), "cards_sha256")
check(started["predeclared_sha256"] == file_hash(RUN / "predeclared.json"), "started_prereg_hash")
check(datetime.fromisoformat(frozen["created_utc"]) < datetime.fromisoformat(started["started_utc"]), "prereg_before_start")
source_hashes = {}
for rel, expected_hash in frozen["source_sha256"].items():
    source_hashes[rel] = file_hash(ROOT / rel)
    check(source_hashes[rel] == expected_hash, "source_sha256", rel)
for name, expected_hash in summary["file_sha256"].items():
    check(file_hash(RUN / name) == expected_hash, "artifact_sha256", name)

rows = []
exchanges = []
negative_jev = []
for card in frozen["cards"]:
    row = read(RUN / (card["id"] + ".json"))
    rows.append(row)
    exchanges.extend(row["exchanges"])
    check(row["card"] == card and row["card_sha256"] == digest(card), "exact_frozen_card", card["id"])
    check(row["proposal_sha256"] == digest(row["proposal"]), "proposal_hash")
    check(row["evidence_before_sha256"] == row["evidence_after_sha256"] == digest([]), "evidence_unchanged_empty")
    check(not card["evidence"] and not forbidden(card), "no_hidden_truth_or_actual_measurement")
    check(frozen["expected_actions"][card["id"]] == expected(card), "independent_expected_public_objective")
    check(row["proposal"]["terminal_authorized"] is False, "proposal_no_terminal_authority")
    check(all(row["jev"][k] is False for k in ("evidence_authority", "repair_authority", "action_authority")), "jev_report_only")
    selected = row["proposal"]["action"]
    base_accepted = selected == "defer" or selected in legal(card)
    base = {"accepted": base_accepted, "action": selected if base_accepted else None,
            "reason": "contract_checked" if base_accepted else "action_not_currently_legal"}
    check(row["base_validation"] == base, "base_gate_same_proposal")
    check(row["support_validation"] == {"accepted": True, "action": selected, "reason": "forecast_support_checked", "violations": []}, "support_gate_same_proposal")
    for arm in ("raw", "base_gate", "support_gate"):
        stat = row["arms"][arm]
        expected_stat = {"legal": selected == "defer" or selected in legal(card), "objective_adherent": selected == expected(card),
                         "measurement_coverage": selected != "defer", "support_violation": False, "deferred": selected == "defer", "refused": False}
        check(all(stat[k] == v for k, v in expected_stat.items()), "arm_metrics_independent", (card["id"], arm))
        check(stat["action"] == selected, "same_raw_proposal_all_arms")
    for exchange in row["exchanges"]:
        check(digest(exchange["request"]) == exchange["request_sha256"], "request_sha256")
        check(digest(exchange["response"]) == exchange["response_sha256"], "response_sha256")
        check(exchange["served_model"] == exchange["response"]["model"], "served_model_exact")
        check(exchange["usage"] == exchange["response"]["usage"], "recorded_usage_exact")
        if exchange["provider"] == "deepseek":
            messages = exchange["request"]["messages"]
            check(messages[0]["content"].encode() == original["prompt"].encode(), "actual_request_prompt_byte_identical")
            check(json.loads(messages[1]["content"]) == card, "actual_deepseek_public_card")
            check(json.loads(exchange["response"]["choices"][0]["message"]["content"]) == row["proposal"], "actual_response_proposal_same")
        else:
            state = json.loads(exchange["request"]["state"])
            check(state == {"contract": card, "proposal": row["proposal"]} and not forbidden(state), "actual_jev_same_public_proposal")
            for identifier, answer in row["jev"]["answers"].items():
                probability = exchange["response"]["answers"][identifier]["noul"]
                check(answer["probability"] == probability and answer["value"] is (probability >= .5), "jev_probability_threshold_exact")
                expected_value = identifier != "measured_evidence"
                check(row["jev_expected"][identifier] is expected_value, "jev_grounded_expected_label")
                if answer["value"] is not expected_value:
                    negative_jev.append({"id": row["id"], "family": row["family"], "question": identifier,
                                         "probability": probability, "value": answer["value"], "expected": expected_value})
check(rows == summary["rows"], "summary_exact_row_copies")
counts = Counter(e["provider"] for e in exchanges)
check(counts == {"deepseek": 8, "jev": 8} == summary["logical_calls"], "eight_calls_per_provider")
for arm in ("raw", "base_gate", "support_gate"):
    for metric in METRICS:
        groups = defaultdict(list)
        for row in rows:
            groups[row["family"]].append(int(row["arms"][arm][metric]))
        expected_stat = {"count": sum(sum(v) for v in groups.values()), "scenarios": 8, **cluster_estimate(groups)}
        check(summary["arms"][arm][metric] == expected_stat, "family_weighted_arm_summary", (arm, metric))
for metric in METRICS:
    groups = defaultdict(list)
    for row in rows:
        groups[row["family"]].append(int(row["arms"]["support_gate"][metric]) - int(row["arms"]["base_gate"][metric]))
    check(summary["support_minus_base_paired"][metric] == cluster_estimate(groups), "paired_gate_difference_summary")
for identifier in ("proposal_supported", "objective_adherent", "measured_evidence"):
    correct = sum(row["jev"]["answers"][identifier]["value"] is row["jev_expected"][identifier] for row in rows)
    check(summary["jev"][identifier] == {"correct": correct, "refused": 0, "scenarios": 8}, "jev_correct_summary")
check(len(negative_jev) == 2 and all(r["question"] == "objective_adherent" for r in negative_jev), "two_jev_objective_negatives_preserved")
for provider in counts:
    usage = Counter()
    for e in exchanges:
        if e["provider"] == provider:
            usage.update({k: v for k, v in e["usage"].items() if type(v) is int})
    if provider == "deepseek":
        usage["calls"] = 8
    check(dict(usage) == summary["provider_usage"][provider], "provider_usage_recomputed")
check("not model accuracy or biological gain" in summary["interpretation"], "no_model_gain_claim_in_summary")

result = {"status": "passed" if not findings else "findings", "created_utc": datetime.now(timezone.utc).isoformat(),
          "command": [sys.executable, *sys.argv], "script_sha256": file_hash(Path(__file__)), "checks": checks, "findings": findings,
          "source_sha256": source_hashes, "predeclared_sha256": file_hash(RUN / "predeclared.json"), "summary_sha256": file_hash(RUN / "summary.json"),
          "original_prompt_sha256": digest(original["prompt"]), "receipt_sha256": {r["id"]: file_hash(RUN / (r["id"] + ".json")) for r in rows},
          "logical_calls": dict(counts), "objective_success": {arm: summary["arms"][arm]["objective_adherent"]["count"] for arm in summary["arms"]},
          "jev_objective_correct": summary["jev"]["objective_adherent"]["correct"], "negative_jev": negative_jev,
          "limitations": ["New generated cards explicitly expose the optional support contract; unchanged prompt does not mean unchanged task information.",
                           "All three action arms are already 8/8, so support gating adds no observed gain in this fresh sample.",
                           "Four fixed families and eight generated cases cannot establish general biological superiority or model improvement.",
                           "No provider calls, training or source edits were performed by this independent review."]}
with (OUT / "receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(result, handle, indent=2, allow_nan=False)
    handle.write("\n")
print(json.dumps({"status": result["status"], "checks": checks, "findings": findings, "negative_jev": negative_jev}, indent=2))
