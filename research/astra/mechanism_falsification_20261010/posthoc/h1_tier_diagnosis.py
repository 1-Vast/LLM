"""POST HOC (written after the sealed run): where the H1 activity-tier failure sits, and what the
named outcomes amount to (single-survivor correctness, episodes with no rejection), and the
agent-chosen design paired with the deterministic designs on the same 100 drugs.

Reads ROWS.json (frozen evaluator output) and recomputes the evaluator's activity measure with the
frozen function. No new fitting and no new arm; the confirmatory verdicts are unchanged.
Output: posthoc/h1_tier_diagnosis.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import dev_programs as DP  # noqa: E402
import intervals as IV  # noqa: E402
import study as S  # noqa: E402

B = 4


def block(rows):
    st = [r["steps"][min(B, len(r["steps"])) - 1] for r in rows if r["steps"]]
    k = int(sum(s["covered"] for s in st))
    return {"n": len(st), "covered": k, "coverage": k / len(st) if st else None,
            "wilson95": list(IV.wilson(k, len(st))) if st else None,
            "mean_set": float(np.mean([s["set_size"] for s in st])) if st else None}


def main() -> dict:
    open_, sealed = S.load_tier("open"), S.load_tier("sealed")
    ref = open_["role"] == "reference"
    act = dict(zip(map(str, sealed["drug"]), DP.activity(sealed["x"], open_["x"][ref]).tolist()))
    support = Counter(map(str, open_["moa"][ref]))

    def bucket(moa):
        n = support.get(moa, 0)
        return "K" if n == 0 else "1" if n == 1 else "2-3" if n <= 3 else "4+"

    rows = json.loads((HERE / "ROWS.json").read_text(encoding="utf-8"))
    out = {"note": "post hoc; confirmatory verdicts unchanged", "budget": B, "arms": {}}
    for arm, pol in (("episode", "falsify"), ("episode", "fixed"), ("set", "fixed"), ("naive", "fixed")):
        rs = [r for r in rows[arm] if r["policy"] == pol]
        top = [r for r in rs if act[r["drug"]] >= 0.75]
        rec = {"top_tier": block(top),
               "top_tier_by_true_class_bucket": {b: block([r for r in top if bucket(r["moa"]) == b]) for b in ("K", "1", "2-3", "4+")},
               "by_activity_decile": {}}
        for lo in np.arange(0.0, 1.0, 0.1):
            sub = [r for r in rs if lo <= act[r["drug"]] < lo + 0.1 + (1e-9 if lo >= 0.9 else 0)]
            rec["by_activity_decile"][f"{lo:.1f}"] = block(sub)
        single = [r for r in rs if r["status"] == "SINGLE_SURVIVOR"]
        rec["outcomes"] = {"n": len(rs), "single_survivor": len(single),
                           "single_survivor_correct": int(sum(r["steps"][-1]["covered"] for r in single)),
                           "exhausted": int(sum(r["status"] == "HYPOTHESIS_SET_EXHAUSTED" for r in rs)),
                           "no_rejection_at_end": int(sum(r["steps"][-1]["set_size"] == r["n_hyp"] for r in rs))}
        out["arms"][f"{arm}/{pol}"] = rec
    llm = [r for r in json.loads((HERE / "LLM_ROWS.json").read_text(encoding="utf-8")) if r["mode"] == "agent"]
    agent = {r["drug"]: r["steps"][min(B, len(r["steps"])) - 1] for r in llm if r["steps"]}
    moa = {r["drug"]: r["moa"] for r in llm}
    out["agent_design_paired"] = {}
    for arm, pol in (("set", "fixed"), ("set", "random"), ("set", "falsify")):
        other = {r["drug"]: r["steps"][min(B, len(r["steps"])) - 1] for r in rows[arm] if r["policy"] == pol and r["steps"]}
        keys = sorted(set(agent) & set(other))
        a = np.array([len(agent[k]["falsifier_set"]) for k in keys])
        b = np.array([other[k]["set_size"] for k in keys])
        rec = IV.paired_difference(a, b, np.array([moa[k] for k in keys]))
        rec["mean_a"], rec["mean_b"] = float(a.mean()), float(b.mean())
        rec["coverage_a"] = float(np.mean([moa[k] in agent[k]["falsifier_set"] for k in keys]))
        rec["coverage_b"] = float(np.mean([other[k]["covered"] for k in keys]))
        out["agent_design_paired"][f"agent_design_minus_{arm}/{pol}"] = rec
    (HERE / "posthoc" / "h1_tier_diagnosis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    for k, v in o["agent_design_paired"].items():
        print(k, round(v["mean_difference"], 1), [round(x, 1) for x in v["ci95"]], "n", v["n"],
              "means", round(v["mean_a"], 1), round(v["mean_b"], 1), "cov", round(v["coverage_a"], 2), round(v["coverage_b"], 2))
    for k, v in o["arms"].items():
        print(k, "top", {x: v["top_tier"][x] for x in ("n", "covered", "coverage")},
              {b: (d["n"], d["covered"]) for b, d in v["top_tier_by_true_class_bucket"].items()})
        print("   outcomes", v["outcomes"])
        print("   deciles", {d: (x["n"], round(x["coverage"], 2) if x["coverage"] is not None else None) for d, x in v["by_activity_decile"].items()})
