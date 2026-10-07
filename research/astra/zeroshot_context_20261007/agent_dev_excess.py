"""Development-only check of an alternative acquisition objective (run after agent_dev.py, before freezing).

The registered objective (validated deviation magnitude) was already ranked almost perfectly by the panel's
heterogeneity, leaving no attainable acquisition gain. The natural alternative is the deviation in EXCESS of
that panel expectation. An acquisition objective is only meaningful if the target is reproducible across
independent wells and some world can predict it, so this script measures exactly that.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_data as ad  # noqa: E402
from agent_dev import design_matrix  # noqa: E402


def features(rows, well):
    return np.array([[1.0] + [float(ad.root(r[f"{c}_{well}"])) for c in ("zdisp", "dev", "m0energy")] for r in rows])


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    R = json.loads((HERE / "agent_dev" / "AGENT_DEV_RESULTS.json").read_text(encoding="utf-8"))
    beta = np.array([R["simple_prior_coefficients"][k] for k in ("intercept", "zdisp_B", "dev_B", "m0energy_B")])
    tables = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (HERE / "agent_dev" / "tables").glob("*.json")}
    out = {"status": "development only; decides whether the excess-deviation objective is a valid acquisition target", "lines": {}}
    for name in ("PANC-1", "HepG2_C3A"):
        rows = tables[name]
        yA, yB = np.array([r["y_A"] for r in rows]), np.array([r["y_B"] for r in rows])
        sA, sB = features(rows, "A") @ beta, design_matrix(rows) @ beta
        tA, tB = yA - sA, yB - sB
        st = np.array([float(ad.root(r["state_B"])) for r in rows])
        out["lines"][name] = {"labels": len(rows), "pearson_yB_simple_prior": float(np.corrcoef(yB, sB)[0, 1]),
                              "spearman_yB_simple_prior": spearman(yB, sB),
                              "replicate_well_pearson_y": float(np.corrcoef(yA, yB)[0, 1]),
                              "replicate_well_pearson_excess": float(np.corrcoef(tA, tB)[0, 1]),
                              "replicate_well_spearman_excess": spearman(tA, tB),
                              "pearson_state_energy_vs_excess_B": float(np.corrcoef(st, tB)[0, 1]),
                              "spearman_state_energy_vs_excess_B": spearman(st, tB)}
    reps = []
    for k, rows in tables.items():
        if k in ("PANC-1", "HepG2_C3A"):
            continue
        yA, yB = np.array([r["y_A"] for r in rows]), np.array([r["y_B"] for r in rows])
        reps.append(float(np.corrcoef(yA - features(rows, "A") @ beta, yB - design_matrix(rows) @ beta)[0, 1]))
    out["training_contexts_replicate_well_pearson_excess"] = {"median": float(np.median(reps)), "q25": float(np.percentile(reps, 25)),
                                                              "q75": float(np.percentile(reps, 75)), "contexts": len(reps),
                                                              "note": "32-cell wells, so lower reliability is expected than in held-out lines"}
    out["decision"] = ("Not pursued: the excess beyond panel expectation is weakly reproducible across independent wells "
                       "and STATE's prediction of it changes sign between development lines, so an acquisition comparison "
                       "on it would mostly measure well-level noise.")
    (HERE / "agent_dev" / "EXCESS_OBJECTIVE_CHECK.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
