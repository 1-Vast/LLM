"""Workstream C, task 4: agent evaluation records (verifier's own code; SQLite opened read-only).

For arms A and B (required) and noneA / noneB (extra), and every case in arm_results.jsonl:
  * screen purchases in cases.sqlite (planned_actions 'screen-*' with a recorded result) equal
    the screens listed in arm_results.jsonl (count and ordered labels);
  * every 'validate-*' action was planned after the case's last screen (plan_version) and its
    result was created after the last screen result (created_at);
  * validates cover exactly the flagged labels;
  * budgets not exceeded: arm_results budget.recorded_use <= budget.budget, and
    cases.spent <= cases.budget with spent equal to the summed cost of recorded actions;
  * V equals the sum of y_B over flagged labels from EPISODES.json rows (line, menu);
  * extra: screens observed the A well (plate_A, metric == y_A), validates the B well
    (plate_B, metric == y_B); SUMMARY.json per-episode V and mean V agree with arm_results.
Writes task4_agent_records.json.
"""
import json
import os
import sqlite3

import numpy as np

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
V = os.path.join(S, "verification")
TOL = 1e-12


def load_json(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    episodes = load_json(os.path.join(S, "agent_eval_inputs", "EPISODES.json"))
    ep = {(e["line"], e["menu"]): {r["label"]: r for r in e["rows"]} for e in episodes}
    cases = []
    with open(os.path.join(S, "agent_eval", "arm_results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                cases.append(json.loads(line))
    out = {"arms": {}, "mismatches": []}
    for arm in ("A", "B", "noneA", "noneB"):
        db = os.path.join(S, "agent_eval", arm, "cases.sqlite")
        con = sqlite3.connect("file:" + db.replace("\\", "/") + "?mode=ro", uri=True)
        cur = con.cursor()
        arm_cases = [c for c in cases if c["arm"] == arm]
        db_cases = {r[0]: r for r in cur.execute("select case_id, state, plan_version, budget, spent, stop_reason from cases")}
        summary = {"cases_in_jsonl": len(arm_cases), "cases_in_sqlite": len(db_cases), "per_case": []}
        for c in arm_cases:
            cid = c["case_id"]
            rows = ep[(c["line"], c["menu"])]
            acts = cur.execute("select plan_version, action_identifier, cost, status, expected_conditions_json "
                               "from planned_actions where case_id=? order by plan_version", (cid,)).fetchall()
            res = {r[0]: r for r in cur.execute("select action_identifier, created_at, metrics_json, conditions_json, quality_passed "
                                                "from results where case_id=?", (cid,)).fetchall()}
            screens = [a for a in acts if a[1].startswith("screen-")]
            validates = [a for a in acts if a[1].startswith("validate-")]
            other = [a for a in acts if not (a[1].startswith("screen-") or a[1].startswith("validate-"))]
            screens_purchased = [a for a in screens if a[1] in res]
            screen_labels = [json.loads(a[4])["label"] for a in screens_purchased]
            val_labels = [json.loads(a[4])["label"] for a in validates if a[1] in res]
            last_screen_pv = max((a[0] for a in screens), default=0)
            last_screen_time = max((res[a[1]][1] for a in screens_purchased), default="")
            val_after = all(a[0] > last_screen_pv for a in validates)
            val_time_after = all(res[a[1]][1] > last_screen_time for a in validates if a[1] in res)
            # observation wells
            wells_ok, metric_ok = True, True
            for a in screens_purchased:
                cond = json.loads(a[4])
                r = rows[cond["label"]]
                m = float(json.loads(res[a[1]][2])["root_deviation_energy_replicate_well"])
                wells_ok &= cond["well_role"] == "A" and cond["plate"] == r["plate_A"]
                metric_ok &= abs(m - r["y_A"]) < TOL
            for a in validates:
                if a[1] not in res:
                    continue
                cond = json.loads(a[4])
                r = rows[cond["label"]]
                m = float(json.loads(res[a[1]][2])["root_deviation_energy_replicate_well"])
                wells_ok &= cond["well_role"] == "B" and cond["plate"] == r["plate_B"]
                metric_ok &= abs(m - r["y_B"]) < TOL
            log_ok = all(abs(s["observed_root_energy"] - rows[lab]["y_A"]) < TOL
                         for s, lab in zip(c.get("log", []), c["screens"]))
            v_recomputed = float(sum(rows[lab]["y_B"] for lab in c["flags"]))
            yb_list_ok = np.allclose([rows[lab]["y_B"] for lab in c["flags"]], c["validated_y_B"], rtol=0, atol=TOL)
            dbc = db_cases.get(cid)
            spent_from_actions = float(sum(a[2] for a in acts if a[1] in res))
            rec = {
                "case_id": cid, "line": c["line"], "menu": c["menu"],
                "screens_jsonl": len(c["screens"]), "screens_sqlite_purchased": len(screens_purchased),
                "screens_sqlite_planned": len(screens),
                "screen_count_equal": len(screens_purchased) == len(c["screens"]),
                "screen_labels_equal_in_order": screen_labels == c["screens"],
                "validates": len(validates), "flags": len(c["flags"]),
                "validate_labels_equal_flags": sorted(val_labels) == sorted(c["flags"]) and len(val_labels) == len(c["flags"]),
                "validates_planned_after_last_screen": val_after,
                "validate_results_created_after_last_screen_result": val_time_after,
                "other_actions": len(other),
                "budget_jsonl": c["budget"]["budget"], "recorded_use_jsonl": c["budget"]["recorded_use"],
                "budget_ok_jsonl": c["budget"]["recorded_use"] <= c["budget"]["budget"],
                "budget_sqlite": dbc[3] if dbc else None, "spent_sqlite": dbc[4] if dbc else None,
                "budget_ok_sqlite": bool(dbc and dbc[4] <= dbc[3]),
                "spent_equals_recorded_action_costs": bool(dbc and abs(dbc[4] - spent_from_actions) < TOL),
                "recorded_use_equals_sqlite_spent": bool(dbc and abs(dbc[4] - c["budget"]["recorded_use"]) < TOL),
                "case_state": dbc[1] if dbc else None,
                "V_jsonl": c["V"], "V_recomputed": v_recomputed, "V_abs_diff": abs(c["V"] - v_recomputed),
                "V_equal": abs(c["V"] - v_recomputed) < 1e-12,
                "validated_y_B_list_equal": bool(yb_list_ok),
                "screens_observed_A_well_and_validates_B_well": bool(wells_ok),
                "result_metrics_equal_episode_y": bool(metric_ok),
                "log_observations_equal_y_A": bool(log_ok),
            }
            checks = ["screen_count_equal", "screen_labels_equal_in_order", "validate_labels_equal_flags",
                      "validates_planned_after_last_screen", "validate_results_created_after_last_screen_result",
                      "budget_ok_jsonl", "budget_ok_sqlite", "spent_equals_recorded_action_costs",
                      "recorded_use_equals_sqlite_spent", "V_equal", "validated_y_B_list_equal",
                      "screens_observed_A_well_and_validates_B_well", "result_metrics_equal_episode_y",
                      "log_observations_equal_y_A"]
            rec["all_ok"] = all(rec[k] for k in checks)
            for k in checks:
                if not rec[k]:
                    out["mismatches"].append({"arm": arm, "case_id": cid, "check": k})
            summary["per_case"].append(rec)
        summary["all_cases_ok"] = all(r["all_ok"] for r in summary["per_case"]) and \
            summary["cases_in_jsonl"] == summary["cases_in_sqlite"]
        summary["mean_V_recomputed"] = float(np.mean([r["V_recomputed"] for r in summary["per_case"]]))
        out["arms"][arm] = summary
        con.close()
    # SUMMARY.json consistency
    sm = load_json(os.path.join(S, "agent_eval", "SUMMARY.json"))
    order = [tuple(x) for x in sm["episodes"]]
    summ = {}
    for arm in out["arms"]:
        by = {(r["line"], r["menu"]): r["V_recomputed"] for r in out["arms"][arm]["per_case"]}
        mine = [by[k] for k in order]
        summ[arm] = {"per_episode_max_abs_diff": float(np.max(np.abs(np.array(mine) - np.array(sm["per_episode_V"][arm])))),
                     "mean_V_summary": sm["mean_V"][arm], "mean_V_recomputed": float(np.mean(mine))}
    perfect = []
    for e in episodes:
        ys = sorted((r["y_B"] for r in e["rows"]), reverse=True)
        perfect.append(sum(ys[:5]))
    summ["perfect_information_mean_V"] = {"summary": sm.get("perfect_information_mean_V"),
                                          "recomputed_top5_y_B_mean": float(np.mean(perfect))}
    out["summary_json_consistency"] = summ
    out["pass_required_arms_A_B"] = out["arms"]["A"]["all_cases_ok"] and out["arms"]["B"]["all_cases_ok"]
    out["pass_all_arms"] = all(a["all_cases_ok"] for a in out["arms"].values())
    out["pass"] = bool(out["pass_required_arms_A_B"])
    with open(os.path.join(V, "task4_agent_records.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"mismatches": out["mismatches"], "pass_A_B": out["pass_required_arms_A_B"],
                      "pass_all": out["pass_all_arms"], "summary": summ,
                      "means": {a: v["mean_V_recomputed"] for a, v in out["arms"].items()}}, indent=1))


if __name__ == "__main__":
    main()
