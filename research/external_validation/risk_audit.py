"""Decision-focused and risk-focused summaries: rates, curves, Pareto frontiers.

File summary
- Path: research/external_validation/risk_audit.py
- Purpose: from the locked-replay records, every arm's correct rate, wrong-risk, coverage,
  selective risk, deferral and costs with cluster intervals; risk-coverage, correct-cost and
  wrong-cost curves; and the non-dominated arms.
- Core points:
  - `collect` flattens the gzipped records once into an episode table and the rows other modules
    need (calibration, confidence at the decisive step).
  - A priced arm contributes a curve over its price sweep; every other arm is a point.
  - The confidence-ranked risk-coverage curve uses only what the arm forecast before it measured
    (its planning-weighted P(correct) and P(wrong) at the eliminating step), never the truth.
  - The oracle is drawn as a reference and excluded from frontiers.
- Depends on: statistics.py, numpy, pandas, matplotlib
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import statistics as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs" / "external_validation_20260927"
TIERS = (("sciplex3", "A"), ("sciplex3", "B"), ("l1000", "LT"), ("l1000", "T"))
UNIT = {"sciplex3": "cluster_skeleton", "l1000": "cluster_component"}
SENSITIVITY = {"sciplex3": ("cluster_compound", "cluster_murcko_scaffold", "cluster_plate_cohort"),
               "l1000": ("cluster_identity", "cluster_batch_cohort")}
STEP_ARMS = ("maestro_vc", "maestro_masked", "myopic_edv", "sparse_two_step", "retrieval", "info_gain")
ENDPOINTS = ("correct", "wrong", "decided", "deferred", "measurements", "days", "wells", "compute_seconds")


def _confidence(note: dict) -> float | None:
    """The arm's own pre-measurement P(correct)/(P(correct)+P(wrong)) for the step, truth-blind."""
    if not note:
        return None
    if "p_correct" in note and "p_wrong" in note:
        c, w = note["p_correct"], note["p_wrong"]
    else:
        branches = note.get("prediction_by_hypothesis") or {}
        if not branches:
            return None
        c = float(np.mean([b["p_correct"] for b in branches.values()]))
        w = float(np.mean([b["p_wrong"] for b in branches.values()]))
    return c / (c + w) if c + w > 0 else None


def collect(replay: Path = OUT / "replay"):
    episodes, steps = [], []
    for path in sorted(replay.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                r = json.loads(line)
                actions = [s["action"] for s in r["steps"]]
                decisive = next((s for s in r["steps"] if s["eliminated"]), None)
                episodes.append({
                    **{k: r.get(k) for k in ("dataset", "tier", "fold", "policy", "arm", "price", "rung", "control",
                                             "reads_hidden_outcomes", "compound", "truth", "h1", "h2", "decoy", "final",
                                             "utility", "stop", "measurements", "days", "wells", "compute_seconds",
                                             "provider_usd", "used_vc", "unit")},
                    **{k: v for k, v in r.items() if k.startswith("cluster_")},
                    "actions": "|".join(actions), "first_action": actions[0] if actions else "",
                    "decisive_confidence": _confidence(decisive.get("note")) if decisive else None})
                for i, s in enumerate(r["steps"] if r["policy"] in STEP_ARMS else ()):
                    steps.append({"dataset": r["dataset"], "tier": r["tier"], "fold": r["fold"], "policy": r["policy"],
                                  "compound": r["compound"], "truth": r["truth"], "h1": r["h1"], "h2": r["h2"],
                                  "step": i, "action": s["action"], "key": s["key"], "qc": s["qc"],
                                  "outcome": s["outcome"], "note": s.get("note") or {},
                                  **{k: v for k, v in r.items() if k.startswith("cluster_")}})
    frame = S.outcome_columns(pd.DataFrame(episodes))
    return frame, steps


def arm_table(frame: pd.DataFrame, unit: str) -> dict:
    out = {}
    for policy, group in frame.groupby("policy"):
        entry = {m: S.rate(group, m, unit) for m in ENDPOINTS}
        decided = group[group.decided == 1]
        entry["selective_risk"] = {"estimate": float(decided.wrong.mean()) if len(decided) else None,
                                   "wilson_upper95": S.wilson_upper(decided.wrong.sum(), len(decided))}
        entry["utility"] = float(group.utility.mean())
        entry["provider_usd"] = float(group.provider_usd.sum())
        entry["episodes"] = int(len(group))
        out[policy] = entry
    return out


def pareto(points: pd.DataFrame) -> list[str]:
    """Arms no other arm beats on correct (higher), wrong (lower) and measurements (lower) at once."""
    keep = []
    for name, p in points.iterrows():
        dominated = any((q.correct >= p.correct and q.wrong <= p.wrong and q.measurements <= p.measurements and
                         (q.correct > p.correct or q.wrong < p.wrong or q.measurements < p.measurements))
                        for other, q in points.iterrows() if other != name)
        if not dominated:
            keep.append(name)
    return keep


def confidence_curve(group: pd.DataFrame) -> dict:
    """Selective risk as decisions are kept in order of the arm's own confidence (AURC over coverage)."""
    n = len(group)
    decided = group[(group.decided == 1) & group.decisive_confidence.notna()].sort_values("decisive_confidence", ascending=False)
    if not len(decided):
        return {"coverage": [], "selective_risk": [], "aurc": None}
    wrong = decided.wrong.to_numpy()
    kept = np.arange(1, len(decided) + 1)
    risk = np.cumsum(wrong) / kept
    return {"coverage": (kept / n).tolist()[:: max(1, len(kept) // 200)], "selective_risk": risk.tolist()[:: max(1, len(kept) // 200)],
            "aurc": float(np.mean(risk)), "decided_with_confidence": int(len(decided))}


def figures(frame: pd.DataFrame, spec: dict, path: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.mkdir(parents=True, exist_ok=True)
    cap = spec["thresholds"]["wrong_risk_cap"]
    rates = frame.groupby(["dataset", "tier", "policy"])[["correct", "wrong", "decided", "measurements"]].mean().reset_index()
    rates["selective"] = rates.wrong / rates.decided.replace(0, np.nan)
    made = {}
    for name, (x, y, title) in {"correct_cost": ("measurements", "correct", "correct decisions vs measurements"),
                                "wrong_cost": ("measurements", "wrong", "wrong-risk vs measurements"),
                                "risk_coverage": ("decided", "selective", "selective risk vs coverage")}.items():
        fig, axes = plt.subplots(2, 2, figsize=(11, 9))
        for ax, (dataset, tier) in zip(axes.flat, TIERS):
            sub = rates[(rates.dataset == dataset) & (rates.tier == tier)]
            base = sub[~sub.policy.str.contains("@")]
            for _, r in base.iterrows():
                marker = "*" if r.policy == "maestro_vc" else ("x" if r.policy == "oracle" else "o")
                ax.scatter(r[x], r[y], marker=marker, s=60 if marker != "o" else 25)
                ax.annotate(r.policy, (r[x], r[y]), fontsize=6, xytext=(2, 2), textcoords="offset points")
            for arm in ("myopic_edv", "sparse_two_step"):
                line = sub[sub.policy.str.startswith(arm)].copy()
                line["price"] = [0.02 if "@" not in p else float(p.split("@")[1]) for p in line.policy]
                line = line.sort_values("price")
                ax.plot(line[x], line[y], "-", lw=1, label=f"{arm} price sweep")
            if y == "wrong":
                ax.axhline(cap, ls=":", lw=1, color="grey")
            ax.set_title(f"{dataset} {tier}: {title}", fontsize=9)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            ax.legend(fontsize=6)
        fig.tight_layout()
        target = path / f"{name}.png"
        fig.savefig(target, dpi=130)
        plt.close(fig)
        made[name] = target.relative_to(ROOT).as_posix()
    return made


def summarize(frame: pd.DataFrame, spec: dict) -> dict:
    out = {}
    for dataset, tier in TIERS:
        sub = frame[(frame.dataset == dataset) & (frame.tier == tier)]
        unit = UNIT[dataset]
        table = arm_table(sub, unit)
        points = sub[~sub.policy.isin(["oracle"])].groupby("policy")[["correct", "wrong", "measurements"]].mean()
        capped = points[points.wrong <= spec["thresholds"]["wrong_risk_cap"]]
        curves = {p: confidence_curve(g) for p, g in sub.groupby("policy")
                  if p in ("maestro_vc", "maestro_masked", "myopic_edv", "sparse_two_step", "retrieval", "info_gain")}
        out[f"{dataset}|{tier}"] = {"arms": table, "pareto_all": pareto(points), "pareto_under_cap": pareto(capped),
                                    "confidence_curves": curves}
    return out
