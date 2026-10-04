"""Audit the frozen LLM-planner receipts of the certified-discovery block (read-only).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws4_agent_literature/receipt_audit.py
- Purpose: describe, from the recorded planner events and spend ledgers only, how the
  deepseek-flash planner's replies failed the exact-cardinality contract: returned-id counts
  against k and the menu size, validity codes, agreement with the world model after repair,
  reply lengths (completion tokens), latency, and which calls were never priced.
- Core points:
  - Inputs are the three frozen receipt sets (dev v1 INVALID, dev v2, confirmatory ALMANAC LLM).
    Nothing under research/certified_discovery is modified; no library or label is loaded.
  - The receipts record only the COUNT of returned ids, the repaired agreement with the world
    model's top k and a rationale; raw ids and the presented order were never logged, so
    duplicates, invalid ids and order cannot be separated from these files alone.
  - A failed parse raised before `SpendBook.charge`, so those calls are absent from spend.json;
    their cost is estimated here as an upper bound (prompt at cache-miss rate + max_tokens).
- Interfaces: `main` (python receipt_audit.py) writes receipt_audit.json next to this file.
- Depends on: numpy, json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
RESULTS = ROOT / "research/certified_discovery/results"
SETS = {"dev_v1_INVALID": RESULTS / "dev_llm_20261003_v1", "dev_v2": RESULTS / "dev_llm_20261003_v2",
        "confirm_almanac": RESULTS / "confirm_almanac_20261003/llm"}
RATES = {"input_cache_miss": 0.30, "input_cache_hit": 0.006, "output": 1.20}  # USD per 1e6 tokens
MAX_TOKENS = 3000  # LLMPlannerArm default used by every recorded run


def q(values) -> dict:
    a = np.asarray(values, dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {"n": int(a.size), "min": float(a.min()), "p25": float(np.percentile(a, 25)),
            "median": float(np.median(a)), "p75": float(np.percentile(a, 75)), "max": float(a.max()),
            "mean": round(float(a.mean()), 4)}


def audit(folder: Path) -> dict:
    records = [json.loads(line) for line in open(folder / "campaigns.jsonl", encoding="utf-8")]
    spend = json.loads((folder / "spend.json").read_text(encoding="utf-8"))
    priced = {}
    for entry in spend["entries"]:
        priced.setdefault(entry["label"], []).append(entry)
    out: dict = {"records": len(records), "priced_calls": spend["calls"], "spend_usd": round(spend["total_usd"], 6),
                 "ceiling_usd": spend["ceiling_usd"], "by_mode": {}}
    unpriced_prompt = []
    for mode in sorted({r["arm"] for r in records}):
        rows = []
        for record in (r for r in records if r["arm"] == mode):
            for event in record["planner_events"] or []:
                label = f"{mode}:{record['seed']}:{event['round_measured']}"
                entry = (priced.get(label) or [None])[0]
                rows.append((record, event, entry))
        codes: dict = {}
        for _, event, _ in rows:
            codes[str(event.get("code"))] = codes.get(str(event.get("code")), 0) + 1
        answered = [(r, e, s) for r, e, s in rows if "returned" in e]
        ret = np.array([e["returned"] for _, e, _ in answered])
        k = np.array([e["k"] for _, e, _ in answered])
        menu = np.array([e["menu"] for _, e, _ in answered])
        agreement = np.array([e["agreement_with_world_model"] for _, e, _ in answered])
        valid = np.array([e.get("code") is None for _, e, _ in answered])
        with_cost = [(e, s) for _, e, s in answered if s is not None]
        comp = np.array([s["completion_tokens"] for _, s in with_cost])
        prom = np.array([s["prompt_tokens"] for _, s in with_cost])
        ret_c = np.array([e["returned"] for e, _ in with_cost])
        secs = np.array([s["seconds"] for _, s in with_cost])
        slope = float(np.polyfit(ret_c, comp, 1)[0]) if ret_c.size > 2 and np.ptp(ret_c) > 0 else None
        rationale_all = sum(bool(re.search(r"\ball\b", e.get("rationale", ""), re.I)) for _, e, _ in answered)
        final = [e for _, e, _ in answered if e["menu"] != 2 * e["k"]]
        by_k = {}
        for kk in sorted(set(k.tolist())):
            m = k == kk
            by_k[str(kk)] = {"rounds": int(m.sum()), "valid": int(valid[m].sum()),
                             "returned_eq_k": int((ret[m] == kk).sum()),
                             "returned_eq_menu": int((ret[m] == menu[m]).sum()),
                             "returned_gt_menu": int((ret[m] > menu[m]).sum())}
        unav = [e for _, e, _ in rows if e.get("code") == "LLM_UNAVAILABLE"]
        for record, event, _ in rows:
            if event.get("code") == "LLM_UNAVAILABLE":
                same_line = [s["prompt_tokens"] for lab, ss in priced.items() for s in ss
                             if lab.startswith(f"{mode}:{record['seed']}:")]
                unpriced_prompt.append(float(np.mean(same_line)) if same_line else float(np.mean(prom)))
        out["by_mode"][mode] = {
            "rounds": len(rows), "codes": codes, "answered": len(answered), "valid_rate": round(float(valid.mean()), 4),
            "k": q(k), "menu": q(menu), "returned": q(ret), "returned_over_k": q(ret / k),
            "returned_eq_k": int((ret == k).sum()), "returned_eq_menu": int((ret == menu).sum()),
            "returned_gt_menu": int((ret > menu).sum()), "returned_between_k_and_menu": int(((ret > k) & (ret < menu)).sum()),
            "returned_lt_k": int((ret < k).sum()),
            "agreement_after_repair": q(agreement), "agreement_eq_1": int((agreement == 1.0).sum()),
            "completion_tokens": q(comp), "prompt_tokens": q(prom), "seconds": q(secs),
            "completion_tokens_per_returned_id_slope": slope,
            "rationale_says_all": rationale_all, "by_k": by_k,
            "unavailable_details": sorted({f"{e.get('error')}:{e.get('detail')}" for e in unav}),
            "rounds_menu_not_2k": len(final),
        }
    # The unparseable replies were billed by the provider but never charged to spend.json.
    bound = [p * RATES["input_cache_miss"] / 1e6 + MAX_TOKENS * RATES["output"] / 1e6 for p in unpriced_prompt]
    out["unpriced_calls"] = len(unpriced_prompt)
    out["unpriced_upper_bound_usd"] = round(float(sum(bound)), 4)
    return out


def main() -> int:
    report = {name: audit(folder) for name, folder in SETS.items()}
    report["note"] = ("Receipts store returned-id counts, repaired agreement and rationale only; raw ids and "
                      "presented order were not logged. Unpriced calls raised before SpendBook.charge; their "
                      "cost bound assumes cache-miss input and a full max_tokens=3000 completion.")
    path = Path(__file__).with_name("receipt_audit.json")
    path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    for name in SETS:
        r = report[name]
        print(name, "priced", r["priced_calls"], "usd", r["spend_usd"], "unpriced", r["unpriced_calls"],
              "bound", r["unpriced_upper_bound_usd"])
        for mode, m in r["by_mode"].items():
            print("  ", mode, m["codes"], "ret", m["returned"].get("median"), m["returned"].get("max"),
                  "eq_k", m["returned_eq_k"], "eq_menu", m["returned_eq_menu"], ">menu", m["returned_gt_menu"],
                  "agree", m["agreement_after_repair"].get("mean"), "comp_tok", m["completion_tokens"].get("median"),
                  "slope", None if m["completion_tokens_per_returned_id_slope"] is None
                  else round(m["completion_tokens_per_returned_id_slope"], 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
