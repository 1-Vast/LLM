"""Summarise the WS4 exact-cardinality diagnostic (main plan and addendum) by condition.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws4_agent_literature/summarise.py
- Purpose: turn results/selections.jsonl (and results_addendum/ when present) into one table per
  condition: validity rates, failure anatomy, tokens, latency, USD per valid selection, and
  whether the reply follows the presented order or the world model's order.
- Core points:
  - Strict validity is the registered criterion; rank "prefix-valid" is reported beside it, never
    as success. A selection with no valid reply has no hit count.
  - Order: overlap of the reply's first k with the presented first k and with the world model's
    top k, and Kendall tau of reply position against presented position and against model rank.
    In model-order presentations the two coincide; only shuffled/blind cells separate them.
  - Hits are descriptive (exposed O'Neil labels, 3 lines); no inference is drawn from them.
- Interfaces: `python summarise.py` writes summary.json next to this file and prints a table.
- Depends on: numpy, scipy.stats.kendalltau.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau

HERE = Path(__file__).resolve().parent
RUNS = {"main": HERE / "results", "addendum": HERE / "results_addendum"}


def order_stats(result: dict) -> dict:
    reply, presented, wm = result.get("reply_order") or [], result.get("presented") or [], result["menu_model_order"]
    k = result["cell"]["k"]
    if not reply or not presented:
        return {}
    pos = {i: n for n, i in enumerate(presented)}
    rank = {i: n for n, i in enumerate(wm)}
    first = reply[:k]
    out = {"overlap_presented_topk": len(set(first) & set(presented[:k])) / k,
           "overlap_wm_topk": len(set(first) & set(wm[:k])) / k,
           "verbatim_echo_of_presented_prefix": first == presented[: len(first)]}
    ids = [i for i in reply if i in pos]
    if len(ids) > 2:
        out["tau_vs_presented"] = float(kendalltau(range(len(ids)), [pos[i] for i in ids])[0])
        out["tau_vs_model"] = float(kendalltau(range(len(ids)), [rank[i] for i in ids])[0])
    return out


def condition(rows: list[dict]) -> dict:
    calls = [c for r in rows for c in r["calls"]]
    priced = [c for c in calls if c.get("usd") is not None]
    valid = [r for r in rows if r["valid"]]
    usd = sum(c["usd"] for c in priced)
    orders = [order_stats(r) for r in rows]

    def mean(key, pool=orders):
        vals = [o[key] for o in pool if key in o and o[key] is not None]
        return round(float(np.mean(vals)), 3) if vals else None

    checks = [c["check"] for c in calls if c.get("check")]
    need = [r["cell"]["k"] if r["cell"]["contract"] != "rank" else 2 * r["cell"]["k"] for r in rows]
    hits_sel = [r["hits_selection"] for r in rows if r["hits_selection"] is not None]
    hits_wm = [r["hits_wm_topk"] for r in rows if r["hits_selection"] is not None]
    rand = [r["cell"]["k"] * r["hits_menu"] / len(r["menu_model_order"]) for r in rows if r["hits_selection"] is not None]
    return {
        "selections": len(rows), "valid": len(valid), "valid_first_attempt": sum(r["valid_first"] for r in rows),
        "prefix_valid": sum(bool(r.get("prefix_valid")) for r in rows) if rows[0]["cell"]["contract"] == "rank" else None,
        "failures": sorted({str(r["failure"]) for r in rows if r["failure"]}),
        "calls": len(calls), "parse_failures": sum(c["failure"] == "PARSE_FAILURE" for c in calls),
        "truncated_length": sum(c.get("finish_reason") == "length" for c in calls),
        "returned_over_needed_first_call": [round(r["calls"][0]["check"]["n"] / (n if r["cell"]["contract"] != "chunk16"
                                                                                   else min(16, r["cell"]["k"])), 3)
                                            if r["calls"][0].get("check") else None for r, n in zip(rows, need)],
        "duplicates": sum(c["dup"] for c in checks), "not_in_menu": sum(c["bad"] for c in checks),
        "non_integer": sum(c["nonint"] for c in checks),
        "http_attempts": sum(c.get("http_attempts") or 0 for c in calls),
        "prompt_tokens_per_selection": round(sum(c["usage"].get("prompt_tokens", 0) for c in priced) / len(rows), 1),
        "completion_tokens_per_selection": round(sum(c["usage"].get("completion_tokens", 0) for c in priced) / len(rows), 1),
        "seconds_per_selection": round(sum(c["seconds"] or 0 for c in calls) / len(rows), 2),
        "usd": round(usd, 5), "usd_per_valid_selection": round(usd / len(valid), 5) if valid else None,
        "overlap_presented_topk": mean("overlap_presented_topk"), "overlap_wm_topk": mean("overlap_wm_topk"),
        "verbatim_echo": sum(bool(o.get("verbatim_echo_of_presented_prefix")) for o in orders),
        "tau_vs_presented": mean("tau_vs_presented"), "tau_vs_model": mean("tau_vs_model"),
        "hits_selection": int(sum(hits_sel)), "hits_wm_topk_same_rows": int(sum(hits_wm)),
        "hits_random_in_menu_expected_same_rows": round(float(sum(rand)), 2),
    }


def main() -> int:
    summary = {}
    for run, folder in RUNS.items():
        path = folder / "selections.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(line) for line in open(path, encoding="utf-8")]
        groups = defaultdict(list)
        for r in rows:
            c = r["cell"]
            key = "|".join(str(c[x]) for x in ("contract", "variant", "k")) + "|" + str(c.get("factor", ""))
            groups[key].append(r)
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        summary[run] = {"manifest": manifest, "conditions": {key: condition(v) for key, v in groups.items()}}
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    cols = ("selections", "valid", "valid_first_attempt", "prefix_valid", "calls", "duplicates", "not_in_menu",
            "usd_per_valid_selection", "seconds_per_selection", "overlap_presented_topk", "overlap_wm_topk",
            "verbatim_echo", "tau_vs_presented", "tau_vs_model", "hits_selection", "hits_wm_topk_same_rows",
            "hits_random_in_menu_expected_same_rows")
    for run, block in summary.items():
        print("==", run, "spend", round(block["manifest"]["spend_usd"], 4), "calls", block["manifest"]["priced_calls"])
        print("condition".ljust(34), " ".join(c[:10] for c in cols))
        for key, m in block["conditions"].items():
            print(key.ljust(34), " ".join(str(m[c]) for c in cols))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
