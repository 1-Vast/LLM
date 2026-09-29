"""The pre-registered analysis of the replay: every claim of `protocol.json`, with its verdict.

File summary
- Path: research/maestro_vc_v1/analyze.py
- Purpose: apply the protocol's claims to the replay records and write one JSON with every table and
  verdict, so the report quotes numbers from a file and not from memory.
- Core points:
  - Claims and rules are those written into `protocol.json` before the run: calibration (forecast NLL and
    the wrong-elimination ratio), hypothesis discrimination against the scalar control, the value of
    failure and negative cases (three ablation worlds), terminal decisions against the fixed order and
    the current planner (SAFE and SIGNAL screens), efficiency, abstention quality, structural-novelty
    robustness and the misled-neighbour interaction.
  - Verdict words: `IMPROVES`, `HURTS` and `NO_DETECTABLE_DIFFERENCE` for forecast comparisons, with the
    protocol's own bounds; `ADVANCES`, `SIGNAL_BUT_UNSAFE` and `NO_DEVELOPMENT_SIGNAL` for decisions.
  - The interaction (misled minus aligned neighbour) is a unit bootstrap over the arm-minus-comparator
    difference of every episode, so a stratum's small size widens its interval instead of hiding it.
  - Nothing here reads a truth except where `evaluate_*` joins it to a scored record.
- Run: python -m research.maestro_vc_v1.analyze [--replay DIR] [--out FILE]
- Interfaces: `analyse`, `interaction`, `verdict_forecast`, `main`
- Depends on: research/scientific_case_memory/evaluate_*.py, research/external_validation/statistics.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.external_validation import statistics as S
from research.scientific_case_memory import evaluate_case_retrieval as F
from research.scientific_case_memory import evaluate_decision_policy as D

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
OUT = ROOT / "outputs/maestro_vc_v1/analysis/results.json"
WORLDS = ["class", "similarity", "similarity_unitout", "cm_full", "cm_nofail", "cm_nomisleading", "cm_nonegative", "scalar"]
CANDIDATES = ["cm_similarity_unitout", "cm_full", "cm_full_prior", "cm_full_prior_anchored", "cm_nofail", "prior_only",
              "belief_class", "belief_similarity", "vc_incontext", "scalar_vc", "coverage", "random_legal"]
COMPARATORS = ["fixed", "belief_similarity"]
FLOOR = 0.40


def verdict_forecast(pooled: dict, per_tier: list[dict]) -> str:
    """The protocol's calibration rule for a paired NLL difference (negative = the first world is better)."""
    lo, hi = pooled["ci"]
    if hi < 0 and not any(t["ci"][0] > 0 for t in per_tier):
        return "IMPROVES"
    if lo > 0:
        return "HURTS"
    return "NO_DETECTABLE_DIFFERENCE"


def _paired_by_tier(frame: pd.DataFrame, a: str, b: str, metric: str) -> tuple[dict, list[dict]]:
    tiers = []
    for (dataset, tier), sub in frame.groupby(["dataset", "tier"]):
        r = F.paired_metric(sub, a, b, metric)
        r["tier"] = f"{dataset}:{tier}"
        tiers.append(r)
    return F.paired_metric(frame, a, b, metric), tiers


def interaction(scored: pd.DataFrame, arm: str, comparator: str, tier: str, metric: str = "correct") -> dict | None:
    """(misled - aligned) mean of the arm-minus-comparator difference, unit-bootstrapped."""
    tf = scored[scored.tier == tier]
    a = tf[tf.arm == arm].set_index(["compound", "h1", "h2"])
    b = tf[tf.arm == comparator].set_index(["compound", "h1", "h2"])
    if a.empty or b.empty:
        return None
    delta = (a[metric] - b[metric].reindex(a.index)).rename("delta")
    frame = a[["unit", "nn_similarity", "nn_class", "truth"]].join(delta)
    close = frame.nn_similarity.fillna(0) >= FLOOR
    misled = close & (frame.nn_class != frame.truth)
    aligned = close & (frame.nn_class == frame.truth)
    if frame[misled].unit.nunique() < 10 or frame[aligned].unit.nunique() < 10:
        return {"tier": tier, "note": "fewer than 10 units in a stratum", "misled_units": int(frame[misled].unit.nunique()),
                "aligned_units": int(frame[aligned].unit.nunique())}
    units = sorted(frame.unit.unique())
    pos = {u: i for i, u in enumerate(units)}
    code = frame.unit.map(pos).to_numpy()
    n = len(units)

    def stat(mask):
        s = np.bincount(code[mask.to_numpy()], weights=frame.delta.to_numpy()[mask.to_numpy()], minlength=n)
        c = np.bincount(code[mask.to_numpy()], minlength=n).astype(float)
        return s, c

    sm, cm = stat(misled)
    sa, ca = stat(aligned)
    index = np.random.default_rng(S.SEED).integers(n, size=(S.DRAWS, n))
    boot = sm[index].sum(1) / np.maximum(cm[index].sum(1), 1e-12) - sa[index].sum(1) / np.maximum(ca[index].sum(1), 1e-12)
    point = float(frame[misled].delta.mean() - frame[aligned].delta.mean())
    return {"tier": tier, "arm": arm, "comparator": comparator, "misled_mean": float(frame[misled].delta.mean()),
            "aligned_mean": float(frame[aligned].delta.mean()), "interaction": point,
            "ci": np.quantile(boot, [0.025, 0.975]).tolist(), "misled_units": int(frame[misled].unit.nunique()),
            "aligned_units": int(frame[aligned].unit.nunique())}


def analyse(replay: Path = REPLAY) -> dict:
    scored = D.load_scored(replay / "scored")
    out: dict = {"replay": str(replay), "episodes": int(scored.groupby(["dataset", "tier", "fold", "compound", "h1", "h2"]).ngroups),
                 "units": int(scored.assign(u=scored.dataset + ":" + scored.unit).u.nunique())}
    manifest = json.loads((replay / "manifest.json").read_text(encoding="utf-8")) if (replay / "manifest.json").exists() else {}
    out["integrity"] = {"problems": {k: len(v) for k, v in manifest.get("problems", {}).items()},
                        "total_problems": sum(len(v) for v in manifest.get("problems", {}).values()),
                        "hyperparameters": manifest.get("hyperparameters", {}), "snapshots": manifest.get("snapshots", {})}
    # ------------------------------------------------------------ decisions
    out["summary"] = D.summary_table(scored).round(5).to_dict("records")
    head = D.headroom(scored)
    out["headroom"] = head
    arms = [a for a in CANDIDATES if a in set(scored.arm)]
    pairs = D.paired_table(scored, arms, COMPARATORS)
    out["paired"] = pairs
    out["screens"] = [D.screens(pairs, head, a, c) for a in arms for c in COMPARATORS if a != c]
    out["regret"] = D.regret(scored).round(5).to_dict("records")
    out["abstention"] = D.abstention_table(scored)
    cm_arms = [a for a in ("cm_full", "cm_full_prior", "cm_full_prior_anchored", "cm_nofail", "prior_only", "belief_similarity",
                           "vc_incontext") if a in set(scored.arm)]
    out["strata_decisions"] = D.strata_decisions(scored, cm_arms, "fixed")
    out["interaction"] = [r for a in cm_arms for t in sorted(scored.tier.unique()) if (r := interaction(scored, a, "fixed", t))]
    # ------------------------------------------------------------ forecasts
    rows = F.load_items(replay / "forecasts")
    frame = F.item_frame(rows, WORLDS)
    out["forecast_items"] = int(len(frame[frame.world == "class"]))
    out["world_metrics_pooled"] = [F.world_metrics(frame, w) for w in WORLDS]
    out["world_metrics_by_tier"] = []
    for (dataset, tier), sub in frame.groupby(["dataset", "tier"]):
        for w in WORLDS:
            m = F.world_metrics(sub, w)
            if m:
                out["world_metrics_by_tier"].append({"tier": f"{dataset}:{tier}", **m})
    comparisons = [("cm_full", "similarity"), ("cm_full", "class"), ("similarity", "class"), ("similarity_unitout", "similarity"),
                   ("cm_full", "similarity_unitout"), ("cm_nofail", "cm_full"), ("cm_nomisleading", "cm_full"),
                   ("cm_nonegative", "cm_full")]
    out["forecast_comparisons"] = []
    frame["brier_wrong"] = (frame.p_wrong - frame.y_wrong) ** 2
    for a, b in comparisons:
        for metric in ("nll", "lr", "brier_wrong"):
            pooled, tiers = _paired_by_tier(frame, a, b, metric)
            out["forecast_comparisons"].append({"a": a, "b": b, "metric": metric, "pooled": pooled, "tiers": tiers,
                                                "verdict": verdict_forecast(pooled, tiers) if metric == "nll" else None})
    out["discrimination_vs_scalar"] = [{"world": w, **{k: F.world_metrics(frame, w)[k] for k in ("discrimination", "discrimination_ci")}}
                                       for w in ("class", "similarity", "cm_full", "scalar")]
    out["strata_forecast"] = F.strata_table(frame, ["class", "similarity", "cm_full", "cm_nofail"], "nll")
    out["calibration_curves"] = {w: F.calibration_curve(frame, w) for w in ("class", "similarity", "cm_full", "cm_nofail")}
    out["prior_quality"] = {"pooled": F.prior_quality(rows)}
    for (dataset, tier) in sorted({(r["dataset"], r["tier"]) for r in rows}):
        out["prior_quality"][f"{dataset}:{tier}"] = F.prior_quality([r for r in rows if r["dataset"] == dataset and r["tier"] == tier])
    out["selected_calibration"] = D.selected_calibration(scored, rows, ["fixed", "belief_similarity", "cm_full", "cm_full_prior"],
                                                          ["similarity", "cm_full", "class"])
    # ------------------------------------------------------------ own-forecast calibration of planner arms (recorded notes)
    out["own_forecast_calibration"] = _own_calibration(scored)
    return out


def _own_calibration(scored: pd.DataFrame) -> list[dict]:
    rows = []
    for arm in ("belief_similarity", "cm_full", "cm_full_prior", "vc_incontext"):
        a = scored[scored.arm == arm]
        p, y = [], []
        for r in a.itertuples():
            for s in r.steps:
                pred = (s.get("note") or {}).get("prediction_by_hypothesis")
                if not pred or s.get("lifecycle") != "measured_valid":
                    continue
                truth_pred = pred.get(r.truth)
                if not truth_pred:
                    continue
                truth_is_h1 = r.truth == r.h1
                wrong = (s["outcome"] == "eliminate_a" and truth_is_h1) or (s["outcome"] == "eliminate_b" and not truth_is_h1)
                p.append(float(truth_pred["p_wrong"]))
                y.append(float(wrong))
        if p:
            p, y = np.asarray(p), np.asarray(y)
            rows.append({"arm": arm, "steps": len(p), "mean_forecast": float(p.mean()), "observed": float(y.mean()),
                         "ratio": float(y.sum() / max(p.sum(), 1e-12))})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", default=str(REPLAY))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    result = analyse(Path(args.replay))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
