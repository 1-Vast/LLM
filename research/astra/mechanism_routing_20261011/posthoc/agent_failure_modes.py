"""Post hoc (after the sealed run, not registered): how the agent arms failed on confirmation killers.

Reads RESULTS.json, ROWS_killers.csv and the confirmation agent outputs only (no new model calls).
* Forecaster abstention: share of killers with no routable class, and route_lit - T among drugs it
  routed (a conditional view of A1, not a test).
* Critic: neighbours kept out of 10, and how the critic's prediction relates to the number kept.
* Trust: per-score Spearman and AUCC already in RESULTS.json, restated for the record.
Output: posthoc/agent_failure_modes.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import evaluate as EV  # noqa: E402

sys.path.insert(0, str(HERE.parents[0] / "mechanism_falsification_20261010"))
import intervals as IV  # noqa: E402


def main():
    K = pd.read_csv(HERE / "ROWS_killers.csv")
    R = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    rows = []
    for d in K["drug"].astype(str):
        rl = EV.record("route_lit", "novel_class", f"{EV.slug(d)}.json")
        rn = EV.record("route_nolit", "novel_class", f"{EV.slug(d)}.json")
        ad = EV.record("adjudicate_lit", "novel_class", f"{EV.slug(d)}.json")
        rows.append({"drug": d, "n_routes_lit": len(rl["claims"]["routes"]), "n_routes_nolit": len(rn["claims"]["routes"]),
                     "kill_lit": rl["claims"]["expected_killing"], "n_keep": len(ad["claims"]["keep_neighbours"]),
                     "n_routes_adj": len(ad["claims"]["routes"]), "n_abstracts": rl["n_abstracts"]})
    A = pd.DataFrame(rows).merge(K, on="drug")
    out = {"n_killers": int(len(A)), "label": "post hoc, not registered"}
    routed = A["n_routes_lit"] > 0
    out["forecaster"] = {"share_no_route_lit": float((~routed).mean()), "share_no_route_nolit": float((A["n_routes_nolit"] == 0).mean()),
                         "expected_killing_lit": A["kill_lit"].value_counts().to_dict(),
                         "share_with_abstracts": float((A["n_abstracts"] > 0).mean())}
    sub = A[routed]
    r = IV.paired_difference(sub["agent:route_lit"].to_numpy(float), sub["novel_class:T"].to_numpy(float),
                             sub["moa"].to_numpy(), n_boot=2000, seed=20261011)
    out["forecaster"]["routed_only_route_lit_minus_T"] = {"n": r["n"], "mean": r["mean_difference"], "ci95": r["ci95"]}
    r = IV.paired_difference(sub["agent:route_lit"].to_numpy(float), sub["novel_class:L"].to_numpy(float),
                             sub["moa"].to_numpy(), n_boot=2000, seed=20261011)
    out["forecaster"]["routed_only_route_lit_minus_L"] = {"n": r["n"], "mean": r["mean_difference"], "ci95": r["ci95"]}
    out["critic"] = {"mean_kept_of_10": float(A["n_keep"].mean()), "share_keep_none": float((A["n_keep"] == 0).mean()),
                     "share_keep_all": float((A["n_keep"] == 10).mean()),
                     "adjudicate_minus_L_by_kept": {}}
    for lo, hi in ((0, 0), (1, 3), (4, 6), (7, 10)):
        m = (A["n_keep"] >= lo) & (A["n_keep"] <= hi)
        if m.sum():
            out["critic"]["adjudicate_minus_L_by_kept"][f"{lo}-{hi}"] = {
                "n": int(m.sum()), "mean": float((A.loc[m, "agent:adjudicate_lit"] - A.loc[m, "novel_class:L"]).mean())}
    out["trust_restated"] = {k: R["trust_metrics"][k] for k in ("top_sim", "vc", "keep", "agent", "vc+agent")}
    (HERE / "posthoc" / "agent_failure_modes.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
