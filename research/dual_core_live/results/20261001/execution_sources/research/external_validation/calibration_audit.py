"""Calibration and realized-risk audit of the forecasts that chose measurements, by stratum.

File summary
- Path: research/external_validation/calibration_audit.py
- Purpose: for every QC-passed measurement an arm chose, compare its forecast P(correct reading)
  and P(wrong reading) under the true hypothesis with what the registered validator actually read,
  overall and within each registered stratum.
- Core points:
  - The truth is used only here, after the replay, to score forecasts; arms never saw it.
  - Strata: cell context, action (time and dose), support, scaffold novelty, batch or plate
    cohort, response magnitude (tercile of the measured profile norm) and forecast basis.
  - Diagnostic only (ECE is not a safety gate); the gates read terminal wrong-risk instead.
- Depends on: statistics.py, pandas
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import statistics as S

ARMS = ("myopic_edv", "sparse_two_step", "maestro_vc")
NOVELTY_BINS = [-0.01, 0.3, 0.5, 0.7, 1.01]
NOVELTY_LABELS = ["<0.3", "0.3-0.5", "0.5-0.7", ">=0.7"]
SUPPORT_BINS = [-0.5, 0.5, 1.5, 4.5, 1e9]
SUPPORT_LABELS = ["0", "1", "2-4", ">=5"]


def rows(steps: list, features: pd.DataFrame, diagnostics: pd.DataFrame) -> pd.DataFrame:
    novelty = features.set_index(["dataset", "tier", "compound"]).max_train_tanimoto
    magnitude = diagnostics.set_index(["dataset", "tier", "compound", "action"]).measured_norm
    out = []
    for s in steps:
        if s["policy"] not in ARMS or not s["qc"]:
            continue
        branch = (s["note"].get("prediction_by_hypothesis") or {}).get(s["truth"])
        if not branch or "p_correct" not in branch:
            continue
        correct_label = "eliminate_b" if s["truth"] == s["h1"] else "eliminate_a"
        wrong_label = "eliminate_a" if s["truth"] == s["h1"] else "eliminate_b"
        batch = s.get("cluster_plate_cohort", s.get("cluster_batch_cohort"))
        out.append({"dataset": s["dataset"], "tier": s["tier"], "policy": s["policy"], "step": s["step"],
                     "unit": s.get("cluster_skeleton", s.get("cluster_component")),
                     "line": s["key"][0], "action_type": f"{s['key'][1]:g}h|{s['key'][2]:g}nM",
                     "support": branch.get("local_support", 0) + branch.get("parent_support", 0),
                     "basis": branch.get("basis") or "unknown", "batch": batch,
                     "novelty": novelty.get((s["dataset"], s["tier"], s["compound"]), np.nan),
                     "measured_norm": magnitude.get((s["dataset"], s["tier"], s["compound"], s["action"]), np.nan),
                     "p_correct": float(branch["p_correct"]), "p_wrong": float(branch["p_wrong"]),
                     "correct": float(s["outcome"] == correct_label), "wrong": float(s["outcome"] == wrong_label)})
    frame = pd.DataFrame(out)
    if len(frame):
        frame["novelty_bin"] = pd.cut(frame.novelty, NOVELTY_BINS, labels=NOVELTY_LABELS).astype(str)
        frame["support_bin"] = pd.cut(frame.support, SUPPORT_BINS, labels=SUPPORT_LABELS).astype(str)
        frame["magnitude_tercile"] = frame.groupby(["dataset", "tier"]).measured_norm.transform(
            lambda x: pd.qcut(x.rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str))
    return frame


STRATA = ("line", "action_type", "support_bin", "novelty_bin", "batch", "magnitude_tercile", "basis")


def audit(frame: pd.DataFrame) -> dict:
    out = {}
    for (dataset, tier, policy), group in frame.groupby(["dataset", "tier", "policy"]):
        support = int(len(group))
        wrong_rate = float(group.wrong.mean()) if support else None
        wrong_upper = S.wilson_upper(float(group.wrong.sum()), support)
        entry = {"all": {t: S.calibration_metrics(group[f"p_{t}"], group[t]) for t in ("correct", "wrong")}}
        entry["all"]["wrong"]["direct_wrong_risk_upper95"] = wrong_upper
        # Keep realised wrong risk separate from confidence calibration.  Forecast calibration
        # can look benign in a thin stratum even when its direct risk bound is wide.
        entry["all"].update({
            "support": support,
            "realized_wrong_reading_rate": wrong_rate,
            "direct_wrong_risk": {"estimate": wrong_rate, "upper95": wrong_upper, "support": support},
            "direct_wrong_risk_upper95": wrong_upper,
            "realized_wrong_reading_rate_upper95": wrong_upper,
        })
        for stratum in STRATA:
            per = {}
            for level, sub in group.groupby(stratum):
                if len(sub) < 20 and stratum == "batch":
                    continue
                sub_support = int(len(sub))
                sub_wrong_rate = float(sub.wrong.mean()) if sub_support else None
                sub_wrong_upper = S.wilson_upper(float(sub.wrong.sum()), sub_support)
                per[str(level)] = {t: {k: v for k, v in S.calibration_metrics(sub[f"p_{t}"], sub[t]).items()
                                       if k != "reliability"} for t in ("correct", "wrong")}
                per[str(level)]["wrong"]["direct_wrong_risk_upper95"] = sub_wrong_upper
                per[str(level)].update({
                    "support": sub_support,
                    "realized_wrong_reading_rate": sub_wrong_rate,
                    "direct_wrong_risk": {"estimate": sub_wrong_rate, "upper95": sub_wrong_upper,
                                           "support": sub_support},
                    "direct_wrong_risk_upper95": sub_wrong_upper,
                    "realized_wrong_reading_rate_upper95": sub_wrong_upper,
                })
            entry[stratum] = per
        out[f"{dataset}|{tier}|{policy}"] = entry
    return out


def worst_strata(result: dict, minimum: int = 50) -> list[dict]:
    """Strata whose correct-forecast ECE is largest, among strata with enough measurements."""
    found = []
    for name, entry in result.items():
        for stratum in STRATA:
            for level, metrics in entry.get(stratum, {}).items():
                m = metrics["correct"]
                if m.get("n", 0) >= minimum and m.get("ece") is not None:
                    found.append({"arm": name, "stratum": stratum, "level": level, "n": m["n"],
                                  "support": m.get("support", m["n"]), "ece": m["ece"],
                                  "mean_forecast": m["mean_forecast"], "observed": m["observed"],
                                  "direct_wrong_risk_upper95": metrics.get("direct_wrong_risk_upper95")})
    return sorted(found, key=lambda r: -r["ece"])[:15]
