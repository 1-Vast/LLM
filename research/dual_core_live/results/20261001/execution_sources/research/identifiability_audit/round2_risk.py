"""Conditional-error intervals and same-episode coverage matching; descriptive only."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from research.identifiability_audit import round2 as R


def risk_ci(frame):
    means = frame.groupby("independent_unit")[["correct", "wrong"]].mean()
    values = means.to_numpy(float)
    decided = values.sum(axis=1)
    if not len(values) or decided.sum() == 0:
        return {"risk": None, "ci95": None, "units": len(values), "coverage": 0.0}
    rng = np.random.default_rng(R.SEED)
    sample = rng.integers(0, len(values), (2000, len(values)))
    den = decided[sample].sum(axis=1)
    valid = den > 0
    risk = values[:, 1][sample].sum(axis=1)[valid] / den[valid]
    return {"risk": float(values[:, 1].sum() / decided.sum()), "ci95": np.quantile(risk, [0.025, 0.975]).tolist(),
            "units": len(values), "coverage": float(decided.mean()), "zero_denominator_bootstraps": int((~valid).sum())}


def run(out):
    result = {}
    for dataset, tier in R.TASKS:
        task = dataset + "_" + tier
        frame = pd.read_csv(out / "interventions" / (task + "_path_attribution.csv"), usecols=[
            "episode", "forecast", "policy", "independent_unit", "correct", "wrong", "measurements", "days", "coverage"])
        fixed = frame[(frame.forecast == "reference") & (frame.policy == "fixed")].set_index("episode")
        cells = {}
        for (forecast, policy), part in frame.groupby(["forecast", "policy"]):
            sub = part.set_index("episode").loc[fixed.index]
            joint = (sub.correct + sub.wrong > 0) & (fixed.correct + fixed.wrong > 0)
            acted = (sub.measurements > 0) & (fixed.measurements > 0)
            cells[forecast + "|" + policy] = {"whole_replay": risk_ci(sub),
                "same_acted_subset": {"episodes": int(acted.sum()), "candidate": risk_ci(sub[acted]), "fixed": risk_ci(fixed[acted])},
                "same_decided_subset": {"episodes": int(joint.sum()), "candidate": risk_ci(sub[joint]), "fixed": risk_ci(fixed[joint]),
                    "candidate_cost": {m: R.paired_ci(sub[joint], m) for m in ("measurements", "days")},
                    "fixed_cost": {m: R.paired_ci(fixed[joint], m) for m in ("measurements", "days")}},
                "unresolved_source_rows": int((sub.coverage == "source_linkage_unresolved").sum())}
        result[task] = cells
    R.save(out / "matched_risk_summary.json", {"tasks": result,
        "method": "2,000 chemical-unit bootstrap draws, seed 20260930; risk = E[wrong_u]/E[decided_u]. "
                  "Source-affected results are local replay descriptives, not point identification. "
                  "Matching uses same jointly acted/decided episodes; the jointly decided subset is outcome-selected "
                  "and cannot be a pre-action policy or population risk guarantee."})


if __name__ == "__main__":
    run(R.OUT)
