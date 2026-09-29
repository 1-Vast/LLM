"""The repaired risk control and risk ranking applied to block 7's own E2 traces (before/after on identical data).

File summary
- Path: research/dual_core_v2/block7_repaired.py
- Purpose: the "before" row of every v2 comparison. Block 7's traces keep their flawed lineage (their
  calibration folds' models saw the test fold); that is labelled, not hidden.
- Core points:
  - Truncation is checked against block 7's own `agent.truncate` on every trace at five thresholds.
  - Repaired Learn-then-Test (both p-values) and repaired P2 with the `block7_crossfit` design.
  - Risk ranking (unit-cluster bootstrap AUROC) of the step, plan and conservative plan risks.
  - Writes `outputs/dual_core_v2_20260928/block7_repaired/{ltt_p2.json, risk_ranking.json}` and
    `traces.pkl` (block 7's traces in one file, used by `data_audit` and `horizon_headroom`).
- Interfaces: `main`; CLI `python -m research.dual_core_v2.block7_repaired`
- Depends on: analysis.py, research/dual_core (e2, agent)
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

from . import analysis as A

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_v2_20260928/block7_repaired"


def main() -> dict:
    from research.dual_core import agent as AG
    from research.dual_core import e2 as E2
    OUT.mkdir(parents=True, exist_ok=True)
    traces, _, _ = E2._load(E2.OUT)
    pickle.dump(traces, open(OUT / "traces.pkl", "wb"))
    mismatches = sum(any(A.truncate(t, t["truth"], lam)[k] != AG.truncate(t, t["truth"], lam)[k]
                         for k in ("decided", "wrong", "abstained", "measurements"))
                     for t in traces for lam in (0.0, 0.005, 0.02, 0.1, 1.0))
    ltt = {"status": "block 7 traces; flawed lineage (calibration models saw the test fold)",
           "truncation_mismatches_vs_block7": mismatches, "results": {}}
    for ds in ("sciplex3", "l1000"):
        for arm in ("reference", "incontext"):
            tr = [t for t in traces if t["dataset"] == ds and t["arm"] == arm]
            for method in ("betting", "hb"):
                r = A.certify_design(tr, "block7_crossfit", method=method)
                ltt["results"][f"{ds}|{arm}|{method}"] = {
                    "folds": {f: {k: v.get(k) for k in ("status", "policy", "abstains", "calibration_units",
                                                        "plugin_policy", "plugin_status")} for f, v in r["folds"].items()},
                    "min_p": {f: min(((k, c["p_risk"], c["p_cov"]) for k, c in v["candidates"].items()), key=lambda x: max(x[1], x[2]))
                              for f, v in r["folds"].items() if v.get("candidates")},
                    "certified_policy_test": A.summarise(r["test"]), "plugin_test": A.summarise(r["plugin_test"])}
    (OUT / "ltt_p2.json").write_text(json.dumps(ltt, indent=1, default=str), encoding="utf-8")
    steps = A.step_table(traces)
    ranking = {}
    for (ds, arm), g in steps.groupby(["dataset", "arm"]):
        for score in ("risk_step", "risk_plan", "risk_plan_upper"):
            if g[score].notna().sum():
                ranking[f"{ds}|{arm}|{score}"] = A.risk_ranking(g.reset_index(drop=True), score, draws=2000)
    (OUT / "risk_ranking.json").write_text(json.dumps(ranking, indent=1, default=float), encoding="utf-8")
    return {"truncation_mismatches": mismatches, "ltt_statuses": {k: sorted({f["status"] for f in v["folds"].values()})
                                                                   for k, v in ltt["results"].items()}}


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
