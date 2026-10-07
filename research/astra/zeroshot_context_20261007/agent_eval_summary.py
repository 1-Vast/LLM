"""Summarise the frozen acquisition evaluation: arm values, factorial contrasts, controls, costs.

Purchase-swap replay: for every episode, the flags each world's belief would commit given the
other arm's purchased screens (shared acquired information), isolating acquisition choices from priors.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_policy as ap  # noqa: E402

RATES_USD_PER_M = {"input_cache_miss": 0.30, "input_cache_hit": 0.006, "output": 1.20, "basis": "provider rates recorded 2026-09-12; billed amount not returned by the provider"}


def flags_given(ep, world, protocol, corr_all, label_index, screens):
    rows = ep["rows"]
    li = [label_index[r["label"]] for r in rows]
    mean, sd = np.array(ep["prior"][world]["mean"]), np.array(ep["prior"][world]["sd"])
    a, b, s = ep["obs"]
    belief = ap.Belief(mean, np.outer(sd, sd) * corr_all[np.ix_(li, li)], np.full(len(rows), s ** 2), b, a)
    index = {r["label"]: i for i, r in enumerate(rows)}
    for label in screens:
        i = index[label]
        belief.update(i, rows[i]["y_A"])
    f = ap.flags(belief, protocol["design"]["m"])
    return float(sum(rows[i]["y_B"] for i in f))


def main():
    protocol = json.loads((HERE / "AGENT_PROTOCOL.json").read_text(encoding="utf-8"))
    episodes = {(e["line"], e["menu"]): e for e in json.loads((HERE / "agent_eval_inputs" / "EPISODES.json").read_text(encoding="utf-8"))}
    results = [json.loads(l) for l in (HERE / "agent_eval" / "arm_results.jsonl").read_text(encoding="utf-8").splitlines()]
    corr_all = np.array(protocol["correlation"]["matrix"])
    label_index = {l: i for i, l in enumerate(protocol["correlation"]["labels"])}
    by = {(r["arm"], r["line"], r["menu"]): r for r in results}
    keys = sorted(episodes)
    arms = sorted({r["arm"] for r in results})
    table = {arm: [by[(arm, *k)]["V"] for k in keys if (arm, *k) in by] for arm in arms}
    out = {"episodes": [list(k) for k in keys], "mean_V": {a: float(np.mean(v)) for a, v in table.items()},
           "per_episode_V": {a: v for a, v in table.items()}}
    oracle = []
    for k in keys:
        yB = sorted((r["y_B"] for r in episodes[k]["rows"]), reverse=True)
        oracle.append(sum(yB[:protocol["design"]["m"]]))
    out["perfect_information_mean_V"] = float(np.mean(oracle))
    contrasts = {}
    def diff(a, b):
        if a not in table or b not in table or len(table[a]) != len(keys) or len(table[b]) != len(keys):
            return None
        d = np.array(table[a]) - np.array(table[b])
        lines = sorted({k[0] for k in keys})
        rng = np.random.default_rng(20261007)
        boot = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)]
        return {"mean": float(d.mean()), "per_episode": d.tolist(),
                "per_line": {ln: float(np.mean([x for x, k in zip(d, keys) if k[0] == ln])) for ln in lines},
                "episode_bootstrap_ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}
    for label, a, b in (("B_minus_A_world_value_under_KG", "B", "A"), ("noneB_minus_noneA_forecast_value", "noneB", "noneA"),
                        ("A_minus_noneA_acquisition_value_simple", "A", "noneA"), ("B_minus_noneB_acquisition_value_state", "B", "noneB"),
                        ("C_minus_A_llm_value_simple", "C", "A"), ("D_minus_B_llm_value_state", "D", "B")):
        contrasts[label] = diff(a, b)
    if all(contrasts.get(x) for x in ("C_minus_A_llm_value_simple", "D_minus_B_llm_value_state")):
        dc = np.array(contrasts["D_minus_B_llm_value_state"]["per_episode"]) - np.array(contrasts["C_minus_A_llm_value_simple"]["per_episode"])
        contrasts["interaction_(D-C)-(B-A)"] = {"mean": float(dc.mean()), "per_episode": dc.tolist()}
    out["contrasts"] = contrasts
    swap = []
    for k in keys:
        ep = episodes[k]
        row = {"episode": list(k)}
        for arm in arms:
            if (arm, *k) not in by:
                continue
            screens = by[(arm, *k)]["screens"]
            row[f"{arm}_screens_in_simple"] = flags_given(ep, "simple", protocol, corr_all, label_index, screens)
            row[f"{arm}_screens_in_state"] = flags_given(ep, "state", protocol, corr_all, label_index, screens)
        swap.append(row)
    out["purchase_swap_replay"] = swap
    usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cache_hit_tokens": 0, "failures": 0, "followed_kg": 0, "stops": 0}
    for r in results:
        for rec in r.get("llm_receipts", []):
            usage["calls"] += 1
            u = rec.get("usage", {})
            usage["prompt_tokens"] += int(u.get("prompt_tokens", 0))
            usage["completion_tokens"] += int(u.get("completion_tokens", 0))
            usage["cache_hit_tokens"] += int(u.get("prompt_cache_hit_tokens", 0))
            usage["failures"] += rec["status"] != "accepted"
            usage["followed_kg"] += bool(rec.get("followed_kg"))
            usage["stops"] += rec.get("choice") is None
    miss = usage["prompt_tokens"] - usage["cache_hit_tokens"]
    usage["estimated_usd_at_recorded_rates"] = (miss * RATES_USD_PER_M["input_cache_miss"] + usage["cache_hit_tokens"] * RATES_USD_PER_M["input_cache_hit"]
                                                + usage["completion_tokens"] * RATES_USD_PER_M["output"]) / 1e6
    usage["billed_usd"] = None
    usage["rates"] = RATES_USD_PER_M
    out["llm_usage"] = usage
    out["wells"] = {a: float(np.mean([len(by[(a, *k)]["screens"]) for k in keys if (a, *k) in by])) for a in arms}
    out["operational_threshold_delta_agent"] = protocol["delta_agent"]
    (HERE / "agent_eval" / "SUMMARY.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("mean_V", "perfect_information_mean_V", "contrasts", "llm_usage", "wells")}, indent=1))


if __name__ == "__main__":
    main()
