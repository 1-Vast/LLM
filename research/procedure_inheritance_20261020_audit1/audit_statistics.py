"""Correct accounting and interpretation using saved logs only; no scientific rerun."""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).resolve().parent.with_name("procedure_inheritance_20261020")
DELTA = 0.01


def original_decider():
    """Load only the frozen decision function, without importing any experiment code."""
    path = SOURCE / "pi_stats.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "decide")
    namespace = {"np": np, "DELTA": DELTA}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["decide"]


def decide_corrected(means, anchors, delta=DELTA):
    """Add the missing primary gate; do not replace the consumed study's decision."""
    decision = original_decider()(means, anchors, delta)
    decision["original_label"] = decision["label"]
    decision["advance_requires_primary_saving"] = True
    if decision["label"] == "ADVANCE_TO_POWERED_INDEPENDENT_DESIGN" and not decision["primary_unit_saving_holds"]:
        decision["label"] = "INCONCLUSIVE_DEVELOPMENT"
    return decision


def task_cpu(rows, arm, budget):
    selected = [r for r in rows if r["role"] == "task" and r["arm"] == arm and r["budget_arm"] == budget]
    return {"n_tasks": len(selected), "cpu_s": float(sum(r["cpu_s"] for r in selected))}


def exits_for(rows):
    selected = [(sid, r) for sid, r in rows if r["role"] == "task"
                and r["arm"] in ("f1_kg1", "f1_kg2", "f1_plan", "f1_distill")]

    def count(values):
        return {"logged_campaigns": len(values),
                "unique_backgrounds": len({(sid, r["bg"]) for sid, r in values}),
                "unknown_exits": sum(bool(r["exit_unknown"]) for _, r in values)}

    return {
        "novel_all_four_arms": count([(s, r) for s, r in selected if r["regime"] == 5]),
        "novel_plan_only": count([(s, r) for s, r in selected if r["regime"] == 5 and r["arm"] == "f1_plan"]),
        "known_all_four_arms": count([(s, r) for s, r in selected if r["regime"] != 5]),
    }


def audit():
    streams, transplants, hashes = {}, {}, {}
    for path in sorted((SOURCE / "RUN/eval/streams").glob("*.json.gz")):
        raw = path.read_bytes()
        data = json.loads(gzip.decompress(raw))
        (transplants if ".xplant." in path.name else streams)[data["sid"]] = data
        hashes[path.relative_to(SOURCE).as_posix()] = hashlib.sha256(raw).hexdigest()
    expected = {f"{kind}_{seed}" for kind in ("alias", "chain", "novel", "null") for seed in (71001, 71002)}
    if set(streams) != expected or set(transplants) != expected:
        raise ValueError("All eight original streams and their transplant records are required.")
    summary = json.loads((SOURCE / "SUMMARY.json").read_text(encoding="utf-8"))
    config = json.loads((SOURCE / "CONFIG.json").read_text(encoding="utf-8"))
    for name in ("SUMMARY.json", "CONFIG.json", "PROTOCOL.md", "pi_stats.py", "pi_run.py", "pi_plan.py", "pi_world.py", "POSTHOC.json"):
        hashes[name] = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()

    all_rows = {sid: data["rows"] + transplants[sid]["rows"] for sid, data in streams.items()}
    means, anchors = {}, {}
    for sid, rows in all_rows.items():
        task_values, anchor_values = {}, {}
        for row in rows:
            if row["role"] == "task" and row["batch"] in (2, 3, 4):
                task_values.setdefault((row["arm"], row["budget_arm"]), []).append(row["utility"])
            elif row["role"] == "anchor":
                anchor_values.setdefault((row["arm"], row["ckpt"]), []).append(row["utility"])
        if any(len(v) != 12 for v in task_values.values()):
            raise ValueError(f"Incomplete later-task coverage: {sid}")
        means[sid] = {key: float(np.mean(v)) for key, v in task_values.items()}
        anchors[sid] = {key: float(np.mean(v)) for key, v in anchor_values.items()}

    costs, replay_counts = {}, {}
    for key, old in summary["costs"].items():
        arm, budget_text = key.split("@")
        budget = int(budget_text)
        invocations = [task_cpu(rows, arm, budget) for rows in all_rows.values()]
        if any(r["n_tasks"] != 16 for r in invocations):
            raise ValueError(f"Incomplete full-task CPU coverage: {key}")
        invocation_cpu = float(np.mean([r["cpu_s"] for r in invocations]))
        corrected = dict(old, invocation_tasks=invocation_cpu,
                         total_cpu_s=old["factor_learning"] + old["arm_learning"] + invocation_cpu)
        costs[key] = {"original": old, "corrected_full_16_tasks": corrected,
                      "missing_batch1_cpu_s_mean": invocation_cpu - old["invocation_tasks"]}
    for arm in ("f1_plan", "f0_plan", "f1_plan_re"):
        for budget in (3, 4):
            records = [g["plans"][f"{arm}|{budget}"] for d in streams.values() for g in d["generations"]]
            # pi_plan.py:369 performs this replay but does not increment n_replays.
            omitted = 4 * sum(r["status"] in ("demonstrated", "incumbent_kept", "rolled_back_to_default") for r in records)
            reported = sum(r["n_replays"] for r in records)
            replay_counts[f"{arm}@{budget}"] = {"reported_total": reported,
                "unrecorded_final_default_check_replays": omitted, "corrected_total": reported + omitted,
                "source": "Four validation backgrounds replayed at pi_plan.py:369; CPU already includes these calls."}

    break_even = {}
    for budget in (3, 4):
        for arm in ("f1_plan", "f1_distill"):
            for comp in ("f1_kg1", "f1_kg2"):
                own = costs[f"{arm}@{budget}"]["corrected_full_16_tasks"]
                baseline = costs[f"{comp}@{budget}"]["corrected_full_16_tasks"]
                per_own, per_base = own["invocation_tasks"] / 16, baseline["invocation_tasks"] / 16
                gap = per_base - per_own
                key = f"{arm}@{budget} vs fresh {comp}"
                break_even[key] = {"original": summary["break_even"][key], "corrected_full_16_tasks": {
                    "arm_learning_cpu_s": own["arm_learning"], "per_use_cpu_arm": per_own,
                    "per_use_cpu_fresh": per_base, "break_even_uses": own["arm_learning"] / gap if gap > 1e-9 else None,
                    "uses_in_study": 16}}

    groups = {kind: [sid for sid in means if sid.startswith(kind + "_")] for kind in ("alias", "chain", "novel", "null")}
    groups.update(all=list(means), nonnull=[sid for sid in means if not sid.startswith("null_")],
                  alias_chain=[sid for sid in means if sid.startswith(("alias_", "chain_"))])
    groups.update({f"seed_block_{seed}": [sid for sid in means if sid.endswith(str(seed))] for seed in (71001, 71002)})
    contrasts = {}
    for group, sids in groups.items():
        row = {"n_condition_streams": len(sids), "n_seed_blocks": len({sid.rsplit("_", 1)[1] for sid in sids})}
        for a, b in ((("f1_plan", 3), ("f1_kg2", 4)), (("f1_plan", 3), ("f1_kg1", 3)),
                     (("f1_plan", 3), ("f1_kg2", 3)), (("f1_plan", 3), ("f1_distill", 3)),
                     (("f1_plan", 3), ("f1_plan_re", 3))):
            values = {sid: means[sid][a] - means[sid][b] for sid in sids}
            row[f"{a[0]}@{a[1]} - {b[0]}@{b[1]}"] = {"mean": float(np.mean(list(values.values()))),
                "per_condition_stream": values, "count_below_negative_margin": sum(v < -DELTA for v in values.values()),
                "count_at_least_positive_margin": sum(v >= DELTA for v in values.values())}
        contrasts[group] = row

    flat_rows = [(sid, row) for sid, rows in all_rows.items() for row in rows]
    exit_counts = exits_for(flat_rows)
    for label, arm in (("own_plan", "f1_plan"), ("transplant", "f1_plan_xplant")):
        selected = [r for _, r in flat_rows if r["role"] == "task" and r["arm"] == arm and r.get("plan_applicable") is not None]
        exit_counts[label] = {"candidate_invocations": len(selected),
                              "inapplicable": sum(r["plan_applicable"] is False for r in selected)}
    times = [r["cpu_s"] for d in streams.values() for r in d["rows"] if r["role"] == "task"]
    old_decision = original_decider()(means, anchors)
    corrected_decision = decide_corrected(means, anchors)
    if old_decision != summary["decision"]:
        raise ValueError("Stored original decision was not reproduced from saved utility rows.")
    return {
        "schema": "procedure_inheritance_saved_statistics_audit_v1",
        "label": "READ_ONLY_POST_HOC_DIAGNOSTIC_NO_NEW_EVALUATION",
        "source_package": str(SOURCE), "input_sha256": hashes,
        "calculation": {
            "utility": "Paired means over the original 12 later tasks; subgroup summaries are post hoc descriptive.",
            "compute": "Sum all 16 logged task CPU times per arm/budget, then average over eight condition streams. Recorded learning costs are retained.",
            "replication": "Four conditions share each of two random seed blocks; eight condition streams are not eight independent random worlds.",
            "break_even": "Cumulative four-version learning cost divided by the mean per-invocation CPU difference. Aggregate projection, not observed per-artifact break-even or assay savings.",
            "uncertainty": "No confidence intervals, significance tests, or SUPPORT labels.",
        },
        "original_decision": old_decision, "corrected_decision_logic_on_original_outputs": corrected_decision,
        "decision_review": {
            "frozen_advance_rule": config["decision_rule"]["ADVANCE_TO_POWERED_INDEPENDENT_DESIGN"],
            "original_advance_omits_primary_gate": True,
            "current_label_unchanged": old_decision["label"] == corrected_decision["label"],
            "scope": "Retain the frozen development stopping label; it is not population-level proof that no useful benefit exists.",
        },
        "costs_original_vs_corrected": costs, "validation_replay_accounting": replay_counts,
        "corrected_break_even": break_even, "family_and_seed_block_contrasts": contrasts,
        "exit_denominators": exit_counts,
        "timing_resolution": {"n_task_rows": len(times), "n_zero_cpu_rows": sum(t == 0 for t in times),
            "smallest_positive_cpu_s": min(t for t in times if t > 0),
            "all_times_on_1_over_64_second_grid": all(abs(t * 64 - round(t * 64)) < 1e-8 for t in times)},
        "limits": [
            "Original transplant arm-learning cost is zero although the partner plan required discovery. Its complete source-training allocation remains unspecified.",
            "Tiny quantized timing differences do not support precise large break-even counts.",
            "All 112 registered transplant invocations were rejected: content-specific transfer was not tested by that arm.",
            "Zero novel exits comprise four unique backgrounds, not 32 independent trials; the detector failed those cases but its general sensitivity is not estimated.",
            "The per-stream maximum conventional score is a prespecified oracle envelope, not a deployable selector; individual fixed comparators also show small pooled gaps.",
            "The wins>=1 rule was chosen before evaluation; strict-rule flags cannot reconstruct the counterfactual downstream trajectory under wins>=2.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print(f"Saved statistical/accounting correction: {args.out}")
