"""Feasibility F8 (exploratory; exposed block-N compounds): intervals for the unexpected-hit endpoint.

F3 (5 seeds x 14 lineages, selection orders already written to f3_rows.csv) showed that the virtual
cell's advantage is concentrated in *unexpected* hits: a hit whose annotated mechanism class has no
selective member for that lineage among the reference compounds. F8 attaches lineage-cluster
bootstrap intervals to those contrasts, at each budget, and reports the same for total hits and for
secondary-screen-replicated hits.

Reads f3_rows.csv only; no new campaigns are run.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
METRICS = ("hits", "unexpected", "replicated")
PAIRS = {
    "vc_vs_novc_static": ("static_vc", "static_novc"),
    "vc_vs_novc_refit": ("refit_vc", "refit_novc"),
    "all_vs_novc_refit": ("refit_all", "refit_novc"),
    "all_vs_fixed_class": ("refit_all", "fixed_class"),
    "vc_vs_fixed_class": ("refit_vc", "fixed_class"),
    "feedback_vc": ("refit_vc", "static_vc"),
    "feedback_novc": ("refit_novc", "static_novc"),
    "feedback_all": ("refit_all", "static_all"),
    "interaction_vc_minus_novc": None,   # (refit_vc - static_vc) - (refit_novc - static_novc)
}


def boot(d, groups, B=4000, seed=7):
    u = np.unique(groups)
    r = np.random.default_rng(seed)
    est = [sum(d[groups == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
    return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]


def main():
    df = pd.read_csv(HERE / "f3_rows.csv")
    out = {"budget_totals": {}, "contrasts": {}}
    for f in sorted(df.frac.unique()):
        sub = df[df.frac == f]
        w = sub.pivot_table(index=["seed", "T"], columns="arm", values=list(METRICS)).fillna(0)
        g = np.array([t for _, t in w.index])
        out["budget_totals"][str(f)] = {m: {a: int(w[m][a].sum()) for a in sorted(set(sub.arm))} for m in METRICS}
        out["contrasts"][str(f)] = {}
        for name, pair in PAIRS.items():
            for m in METRICS:
                if pair is None:
                    d = ((w[m]["refit_vc"] - w[m]["static_vc"]) - (w[m]["refit_novc"] - w[m]["static_novc"])).to_numpy(float)
                else:
                    d = (w[m][pair[0]] - w[m][pair[1]]).to_numpy(float)
                out["contrasts"][str(f)][f"{name}|{m}"] = boot(d, g)
    print(json.dumps({"budget_totals": out["budget_totals"]}, indent=1))
    for f in out["contrasts"]:
        print("--- budget fraction", f)
        for k, v in out["contrasts"][f].items():
            if abs(v[0]) > 0 and (v[1] > 0 or v[2] < 0):
                print(f"  {k}: {v[0]:+.0f} [{v[1]:+.0f}, {v[2]:+.0f}]  *")
            else:
                print(f"  {k}: {v[0]:+.0f} [{v[1]:+.0f}, {v[2]:+.0f}]")
    (HERE / "f8_unexpected.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
