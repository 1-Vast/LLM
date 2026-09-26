"""Attribute every stop of the recorded two-step policy, and decompose the fixed policy's advantage.

File summary
- Path: research/sequence_audit/diagnose.py
- Purpose: read the follow-up's recorded SciPlex3 sequence episodes
  (`outputs/acquisition_followup/sequences/`), recompute each contrast's contingent plan exactly as
  `research/acquisition_followup/two_step.py` computed it, and give every missed continuation after
  an unresolved or undetected first reading one mutually exclusive, auditable reason.
- Core points:
  - Facts and explanations are kept apart. Facts come from the record and from the compound's own
    measured data (what a later measurement would have read). Explanations come from the planner's
    reference forecasts, re-derived here and checked against the recorded plan.
  - Reason hierarchy, first match wins: action legality or time order, budget, no paired
    references, implementation defect (a positive continuation existed but was not taken),
    inadequate support (positive on raw reference frequencies, not after Jeffreys shrinkage),
    wrong-elimination risk (a correct elimination is forecast but does not clear the 2:1 break-even),
    non-positive utility (no conditioned reference eliminates correctly).
  - The fixed policy's advantage is split by the two-step policy's path in each discordant pair:
    deferral, stop after QC failure, stop after a neutral reading, a second measurement that did not
    decide, or a different first measurement.
  - Nothing here re-runs or rewrites the recorded episodes; the source hashes they were produced
    with are checked first.
- Run: python research/sequence_audit/diagnose.py
- Depends on: research/acquisition_followup/two_step.py, research/acquisition_link/evaluate.py,
  research/dynamic_world_model (common, episodes)
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import policies as P  # noqa: E402

S, C, E, V = P.S, P.C, P.E, P.V
RECORDED = ROOT / "outputs" / "acquisition_followup" / "sequences"
OUT = ROOT / "outputs" / "sequence_audit_20260926" / "diagnosis"
NEUTRAL = P.NEUTRAL
FIXED_ORDER = P.SCIPLEX3_FIXED
REASONS = ("qc_failure", "time_order_or_action_legality", "insufficient_budget", "no_paired_references",
           "implementation_defect", "inadequate_support_or_uncertainty", "wrong_elimination_risk",
           "predicted_non_positive_continuation_utility", "other")


def reading(result, h1, h2, truth) -> str:
    """What a real measurement did for this compound: correct, wrong, neutral or qc_failed."""
    outcome = result["outcome"]
    if outcome == "quality_failed":
        return "qc_failed"
    if outcome in NEUTRAL:
        return "neutral"
    eliminated = h2 if outcome == "eliminate_b" else h1
    return "wrong" if eliminated == truth else "correct"


def run_fold(task):
    """Recompute every contrast's plan in one (tier, fold) and read every menu action for every compound."""
    tier_name, fold = task
    data, protocol = C.load(), C.load_protocol()
    detected = C.detected_flags(data, C.detection_null(data, protocol))
    magnitude = E.Magnitude(data, detected)
    plans, audits, readings = {}, {}, {}
    for ctx, f in E.contexts(data, protocol, detected, magnitude, tier_names=(tier_name,), folds=(fold,)):
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, f):
            if (h1, h2) not in plans:
                forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params)
                forecasts = {C.action_id(k): forecaster.forecast_key(k, h1, h2) for k in ctx.tier.keys}
                conditional = (lambda a, y, b, h1=h1, h2=h2: S.conditional_forecast(ctx.ft, ctx.params, a, y, b, h1, h2))
                for horizon in (2, 1):
                    plan = S.plan_two_step(ctx.tier.keys, h1, h2, forecasts, conditional, horizon=horizon)
                    plans[(h1, h2, horizon)] = None if plan is None else {
                        "first": C.action_id(plan["first"]),
                        "followups": {y: C.action_id(k) for y, k in plan["followups"].items()}}
                    if plan is not None:
                        audits[(h1, h2, horizon)] = P.continuation_audit(ctx.tier.keys, plan["first"], h1, h2, forecasts,
                                                                         conditional, days=E.days, budget=16.0)
            readings[(compound, h1, h2)] = {C.action_id(k): reading(E.execute(ctx, compound, k, h1, h2), h1, h2, truth)
                                            for k in ctx.tier.keys}
    return tier_name, fold, plans, audits, readings


def check_sources():
    recorded = json.loads((RECORDED / "summary.json").read_text(encoding="utf-8"))["source_sha256"]
    mismatched = [name for name, digest in recorded.items()
                  if hashlib.sha256((ROOT / name.replace("\\", "/")).read_bytes()).hexdigest() != digest]
    if mismatched:
        raise SystemExit(f"Recorded sequence episodes were produced by different code: {mismatched}")
    return recorded


def path_of(record) -> str:
    """The two-step policy's path through an episode, from the record alone."""
    steps = record["steps"]
    if not steps:
        return "deferred_before_first"
    first = steps[0]
    if not first["qc"]:
        return "first_qc_failed_stopped" if len(steps) == 1 else "first_qc_failed_continued"
    if first["eliminated"]:
        return "first_eliminated"
    return "first_neutral_stopped" if len(steps) == 1 else "first_neutral_continued"


def decisive_step(record):
    """Index of the measurement that eliminated, or None."""
    return next((i for i, s in enumerate(record["steps"]) if s["eliminated"]), None)


def main() -> None:
    sources = check_sources()
    records = [json.loads(line) for line in (RECORDED / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    tasks = [(tier, fold) for tier in ("B", "A") for fold in range(5)]
    plans, audits, readings = {}, {}, {}
    with ProcessPoolExecutor(max_workers=5) as pool:
        for tier, fold, p, a, r in pool.map(run_fold, tasks):
            plans.update({(tier, fold, *k): v for k, v in p.items()})
            audits.update({(tier, fold, *k): v for k, v in a.items()})
            readings.update({(tier, fold, *k): v for k, v in r.items()})
            print(f"{tier} fold {fold}: {len(p)} plans", flush=True)

    # Consistency: the recomputed plans are the ones the recorded episodes followed.
    mismatches = 0
    for r in records:
        if r["policy"] not in ("two_step", "one_step_utility") or not r["steps"]:
            continue
        horizon = 2 if r["policy"] == "two_step" else 1
        plan = plans[(r["tier"], r["fold"], r["h1"], r["h2"], horizon)]
        note = r["steps"][0]["note"]
        if plan is None or plan["first"] != C.action_id(note["first"]) or plan["followups"] != note["followups"]:
            mismatches += 1
    if mismatches:
        raise SystemExit(f"{mismatches} recorded plans differ from the recomputation")

    stops, qc_stops = [], []
    for r in records:
        if r["policy"] not in ("two_step", "one_step_utility"):
            continue
        path = path_of(r)
        if path not in ("first_neutral_stopped", "first_qc_failed_stopped"):
            continue
        horizon = 2 if r["policy"] == "two_step" else 1
        first = r["steps"][0]
        observed = readings[(r["tier"], r["fold"], r["compound"], r["h1"], r["h2"])]
        executed = {first["action"]}
        legal_later = {a: y for a, y in observed.items()
                       if a not in executed and float(a.split("|")[1][:3]) >= first["key"][1]}
        fixed_next = next((C.action_id(k) for k in FIXED_ORDER[r["tier"]]
                           if C.action_id(k) not in executed and k[1] >= first["key"][1]), None)
        row = {"tier": r["tier"], "fold": r["fold"], "policy": r["policy"], "compound": r["compound"],
               "truth": r["truth"], "h1": r["h1"], "h2": r["h2"], "first_action": first["action"],
               "first_time": first["key"][1], "first_outcome": first["outcome"],
               # observed facts: what a later measurement of this compound actually read
               "later_legal_readings": dict(Counter(legal_later.values())),
               "any_later_correct": "correct" in legal_later.values(),
               "any_later_wrong": "wrong" in legal_later.values(),
               "fixed_next_action": fixed_next,
               "fixed_next_reading": None if fixed_next is None else observed[fixed_next]}
        if path == "first_qc_failed_stopped":
            qc_stops.append({**row, "reason": "qc_failure"})
            continue
        audit = audits[(r["tier"], r["fold"], r["h1"], r["h2"], horizon)][NEUTRAL[first["outcome"]]]
        valued = [a for a in audit if a["status"] == "valued"]
        stops.append({**row, "reason": P.stop_reason(audit),
                      "candidates": len([a for a in audit if a["status"] != "time_order"]),
                      "refused": sum(a["status"] == "refused" for a in audit),
                      "valued": len(valued),
                      "max_support": max((min(a["support"]) for a in valued), default=0),
                      "refusals": dict(Counter(a["refusal"].split(":")[0] for a in audit if a["status"] == "refused"))})

    summary = {"source_sha256": sources, "recorded_episodes": len(records), "plan_mismatches": mismatches,
               "reason_hierarchy": list(REASONS), "stops": {}, "qc_stops": {}, "neutral_first": {},
               "fixed_advantage": {}, "later_measurement_facts": {}}
    for policy in ("two_step", "one_step_utility"):
        for tier in ("A", "B"):
            mine = [s for s in stops if s["policy"] == policy and s["tier"] == tier]
            neutral = [r for r in records if r["policy"] == policy and r["tier"] == tier
                       and path_of(r) in ("first_neutral_stopped", "first_neutral_continued")]
            summary["neutral_first"][f"{policy}|{tier}"] = {
                "neutral_first": len(neutral), "continued": sum(len(r["steps"]) > 1 for r in neutral),
                "stopped": len(mine)}
            table = defaultdict(Counter)
            for s in mine:
                table["reason"][s["reason"]] += 1
                table["first_outcome"][f"{s['first_outcome']}|{s['reason']}"] += 1
                table["first_time"][f"{s['first_time']:g}h|{s['reason']}"] += 1
                table["truth_class"][f"{s['truth']}|{s['reason']}"] += 1
                table["refusal_kind"].update(s["refusals"])
            summary["stops"][f"{policy}|{tier}"] = {k: dict(sorted(v.items())) for k, v in table.items()}
            q = [s for s in qc_stops if s["policy"] == policy and s["tier"] == tier]
            summary["qc_stops"][f"{policy}|{tier}"] = {
                "stopped_after_qc_failure": len(q),
                "fixed_next_reading": dict(Counter(str(s["fixed_next_reading"]) for s in q))}
            summary["later_measurement_facts"][f"{policy}|{tier}"] = {
                "stops_after_neutral": len(mine),
                "any_later_legal_correct": sum(s["any_later_correct"] for s in mine),
                "any_later_legal_wrong": sum(s["any_later_wrong"] for s in mine),
                "fixed_next_reading": dict(Counter(str(s["fixed_next_reading"]) for s in mine)),
                "by_reason": {reason: dict(Counter(str(s["fixed_next_reading"]) for s in mine if s["reason"] == reason))
                              for reason in REASONS if any(s["reason"] == reason for s in mine)}}

    # The fixed policy's advantage, split by the two-step policy's path in each discordant pair.
    index = {(r["tier"], r["policy"], r["compound"], r["h1"], r["h2"]): r for r in records}
    for tier in ("A", "B"):
        pairs = [(index[(tier, "two_step", c, h1, h2)], r) for (t, p, c, h1, h2), r in index.items()
                 if t == tier and p == "fixed"]
        n = len(pairs)
        table = defaultdict(lambda: {"fixed_better": 0, "two_step_better": 0, "fixed_decisive_step": Counter()})
        for two, fixed in pairs:
            a, b = two["final"] == "correct", fixed["final"] == "correct"
            if a == b:
                continue
            path = path_of(two)
            if path == "first_neutral_continued":
                path += "_same_second" if two["steps"][1]["action"] in {s["action"] for s in fixed["steps"]} else "_other_second"
            if path == "first_eliminated":
                path += "_same_first" if two["steps"][0]["action"] == fixed["steps"][0]["action"] else "_other_first"
            cell = table[path]
            if b:
                cell["fixed_better"] += 1
                cell["fixed_decisive_step"][str(decisive_step(fixed))] += 1
            else:
                cell["two_step_better"] += 1
        summary["fixed_advantage"][tier] = {
            "episodes": n,
            "net_correct_difference": sum((f["final"] == "correct") - (t["final"] == "correct") for t, f in pairs) / n,
            "by_two_step_path": {path: {**{k: v for k, v in cell.items() if k != "fixed_decisive_step"},
                                        "net_share": (cell["fixed_better"] - cell["two_step_better"]) / n,
                                        "fixed_decisive_step": dict(cell["fixed_decisive_step"])}
                                 for path, cell in sorted(table.items())},
            "measurements": {"two_step": sum(len(t["steps"]) for t, _ in pairs) / n,
                             "fixed": sum(len(f["steps"]) for _, f in pairs) / n}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stops.jsonl").write_bytes("".join(json.dumps(s) + "\n" for s in stops + qc_stops).encode("utf-8"))
    (OUT / "summary.json").write_bytes(json.dumps(summary, indent=1).encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("neutral_first", "stops", "qc_stops", "later_measurement_facts",
                                              "fixed_advantage")}, indent=1))


if __name__ == "__main__":
    main()
