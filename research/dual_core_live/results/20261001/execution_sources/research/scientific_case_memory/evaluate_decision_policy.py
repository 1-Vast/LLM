"""Decision-level evaluation of the replay: terminal decisions, cost, regret, calibration and abstention.

File summary
- Path: research/scientific_case_memory/evaluate_decision_policy.py
- Purpose: score every arm on identical episodes by what it decided, what it cost and how its risk
  forecasts held up, against the fixed expert order and the current research planner.
- Core points:
  - Endpoints follow protocol v2: correct, wrong (wrong or exhausted), deferred, decided, utility
    (+1 correct, -2 wrong or exhausted, 0 otherwise), and net utility with the registered price of
    0.02 per measurement. Cost is in laboratory units: measurements, wells and assay days.
  - Paired differences are over identical episodes and clustered by independent unit, 2,000 draws,
    seed 20260927. Two screens are applied unchanged from protocol v2: SAFE (in every tier the
    correct-difference lower bound >= -0.01 and the wrong-difference upper bound <= +0.005) and SIGNAL
    (in a tier that passes the oracle-headroom gate, correct difference >= 0.02 with lower bound > 0).
  - Headroom is `oracle - fixed` in correct decisions. A tier where headroom is below twice the
    practically meaningful gain cannot show a gain by construction, and is reported as such.
  - Regret is the oracle's utility minus the arm's, per episode.
  - Selected-action calibration scores each world's step-0 forecast on the action an arm actually
    chose (the forecast rows carry every condition), so different forecasters are compared on the same
    chosen actions. The ratio observed / forecast of the wrong-elimination event is the under-forecast
    factor; a value above 1 means the world was over-confident on the chosen action.
  - Abstention. An episode ends undetermined or deferred when the arm did not decide. Such a delay is
    `licensed` when the oracle, choosing among all legal sequences with hidden outcomes, could not have
    decided correctly either; precision and recall of the delay against that licence are reported, so a
    delay is not counted as a failure when it was the right answer.
  - Strata: structural novelty and neighbour alignment (as in `evaluate_case_retrieval.py`).
- Interfaces: `load_scored`, `endpoint_frame`, `summary_table`, `paired_table`, `headroom`, `screens`,
  `selected_calibration`, `abstention_table`, `strata_decisions`, `PRICE`
- Depends on: numpy, pandas, research/external_validation/statistics.py
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.external_validation import statistics as S

PRICE = 0.02
MPIE = 0.02
NONINF_CORRECT = 0.01
WRONG_MARGIN = 0.005
FLOOR = 0.40
EPISODE = ["compound", "h1", "h2"]


def load_scored(directory: Path, arms=None) -> pd.DataFrame:
    rows = []
    for path in sorted(Path(directory).glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if arms is not None and r["arm"] not in arms:
                    continue
                steps = r["steps"]
                rows.append({
                    "arm": r["arm"], "dataset": r["dataset"], "tier": str(r["tier"]), "fold": r["fold"],
                    "compound": r["compound"], "h1": r["h1"], "h2": r["h2"], "unit": str(r["unit"]),
                    "final": r["score"]["final"], "truth": r["score"]["truth"], "stop": r["stop"],
                    "measurements": r["measurements"], "days": r["days"], "wells": r["wells"],
                    "qc_failed_steps": sum(s.get("lifecycle") == "measured_qc_failed" for s in steps),
                    "first_action": steps[0]["action"] if steps else None,
                    "nn_similarity": r.get("nn_similarity"), "nn_class": r.get("nn_class"),
                    "max_train_tanimoto": r.get("max_train_tanimoto"),
                    "steps": steps})
    return endpoint_frame(pd.DataFrame(rows))


def endpoint_frame(frame: pd.DataFrame) -> pd.DataFrame:
    f = frame.copy()
    f["correct"] = (f.final == "correct").astype(float)
    f["wrong"] = f.final.isin(("wrong", "exhausted")).astype(float)
    f["decided"] = f.final.isin(("correct", "wrong", "exhausted")).astype(float)
    f["deferred"] = (f.final == "deferred").astype(float)
    f["undetermined"] = (f.final == "undetermined").astype(float)
    f["utility"] = f.correct - 2.0 * f.wrong
    f["net_utility"] = f.utility - PRICE * f.measurements
    return f


def summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (tier, arm), g in frame.groupby(["tier", "arm"]):
        units = g.groupby("unit")
        rows.append({"tier": tier, "arm": arm, "episodes": len(g), "units": g.unit.nunique(),
                     "correct": g.correct.mean(), "wrong": g.wrong.mean(), "deferred": g.deferred.mean(),
                     "undetermined": g.undetermined.mean(), "decided": g.decided.mean(),
                     "selective_correct": g.correct.sum() / max(g.decided.sum(), 1.0),
                     "utility": g.utility.mean(), "net_utility": g.net_utility.mean(),
                     "measurements": g.measurements.mean(), "wells": g.wells.mean(), "days": g.days.mean(),
                     "correct_unit_mean": units.correct.mean().mean()})
    return pd.DataFrame(rows)


def paired_table(frame: pd.DataFrame, arms: list[str], comparators: list[str], metrics=("correct", "wrong", "deferred",
                                                                                          "net_utility", "measurements",
                                                                                          "days", "wells")) -> list[dict]:
    rows = []
    for tier, tf in frame.groupby("tier"):
        for arm in arms:
            for comp in comparators:
                if arm == comp or arm not in set(tf.arm) or comp not in set(tf.arm):
                    continue
                for metric in metrics:
                    d = S.paired(tf, arm, comp, metric, "unit", policy="arm")
                    rows.append({"tier": tier, "arm": arm, "comparator": comp, "metric": metric,
                                 "difference": d["difference"], "lo": d["ci"][0], "hi": d["ci"][1], "units": d["units"],
                                 "episodes": d["episodes"]})
    return rows


def headroom(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for tier, tf in frame.groupby("tier"):
        if "oracle" not in set(tf.arm) or "fixed" not in set(tf.arm):
            continue
        d = S.paired(tf, "oracle", "fixed", "correct", "unit", policy="arm")
        rows.append({"tier": tier, "headroom": d["difference"], "lo": d["ci"][0], "hi": d["ci"][1],
                     "eligible": bool(d["difference"] >= 2 * MPIE and d["ci"][0] >= MPIE), "units": d["units"]})
    return rows


def screens(pairs: list[dict], head: list[dict], arm: str, comparator: str) -> dict:
    """The protocol-v2 development screens for `arm` against `comparator` (both applied unchanged)."""
    by = {(r["tier"], r["metric"]): r for r in pairs if r["arm"] == arm and r["comparator"] == comparator}
    tiers = sorted({t for t, _ in by})
    if not tiers:
        return {}
    safe = all(by[(t, "correct")]["lo"] >= -NONINF_CORRECT and by[(t, "wrong")]["hi"] <= WRONG_MARGIN for t in tiers)
    eligible = {h["tier"]: h["eligible"] for h in head}
    signal_tiers = [t for t in tiers if eligible.get(t) and by[(t, "correct")]["difference"] >= MPIE
                    and by[(t, "correct")]["lo"] > 0]
    unsafe = [t for t in tiers if not (by[(t, "correct")]["lo"] >= -NONINF_CORRECT and by[(t, "wrong")]["hi"] <= WRONG_MARGIN)]
    return {"arm": arm, "comparator": comparator, "safe": bool(safe), "unsafe_tiers": unsafe,
            "signal_tiers": signal_tiers, "signal": bool(signal_tiers),
            "verdict": ("ADVANCES" if signal_tiers and safe else "SIGNAL_BUT_UNSAFE" if signal_tiers else
                        "NO_DEVELOPMENT_SIGNAL"),
            "safety": "SAFE_ON_DEVELOPMENT" if safe else "UNSAFE"}


def regret(frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["tier", "fold", "compound", "h1", "h2"]
    oracle = frame[frame.arm == "oracle"].set_index(keys).utility.rename("oracle_utility")
    f = frame[frame.arm != "oracle"].join(oracle, on=keys)
    f["regret"] = f.oracle_utility - f.utility
    return f.groupby(["tier", "arm"]).regret.mean().reset_index()


def abstention_table(frame: pd.DataFrame) -> list[dict]:
    """Delay quality: was not deciding the licensed answer? (Licence: the oracle could not decide correctly.)"""
    keys = ["tier", "fold", "compound", "h1", "h2"]
    oracle = frame[frame.arm == "oracle"].set_index(keys).correct.rename("oracle_correct")
    rows = []
    f = frame[frame.arm != "oracle"].join(oracle, on=keys)
    f["licensed_delay"] = (f.oracle_correct == 0).astype(float)
    f["delayed"] = ((f.deferred + f.undetermined) > 0).astype(float)
    for (tier, arm), g in f.groupby(["tier", "arm"]):
        delayed = g[g.delayed == 1]
        licensed = g[g.licensed_delay == 1]
        rows.append({"tier": tier, "arm": arm, "delayed_share": float(g.delayed.mean()),
                     "precision": float(delayed.licensed_delay.mean()) if len(delayed) else float("nan"),
                     "recall": float(licensed.delayed.mean()) if len(licensed) else float("nan"),
                     "unlicensed_delay_cost": float(((g.delayed == 1) & (g.licensed_delay == 0)).mean()),
                     "wrong_among_decided": float(g.wrong.sum() / max(g.decided.sum(), 1.0))})
    return rows


def strata_decisions(frame: pd.DataFrame, arms: list[str], comparator: str = "fixed") -> list[dict]:
    """Paired correct difference against `comparator` within novelty and neighbour-alignment strata."""
    rows = []
    for tier, tf in frame.groupby("tier"):
        novelty = np.where(tf.nn_similarity.isna(), "no_structure", np.where(tf.nn_similarity < FLOOR, "novel", "familiar"))
        aligned = tf.nn_class == tf.truth
        neighbour = np.where(tf.nn_similarity.isna() | (tf.nn_similarity < FLOOR), "no_close_neighbour",
                             np.where(aligned, "aligned_neighbour", "misled_neighbour"))
        for family, labels in (("novelty", novelty), ("neighbour", neighbour)):
            for stratum in sorted(set(labels)):
                sub = tf[labels == stratum]
                if sub.unit.nunique() < 10:
                    continue
                for arm in arms:
                    if arm == comparator or arm not in set(sub.arm) or comparator not in set(sub.arm):
                        continue
                    d = S.paired(sub, arm, comparator, "correct", "unit", policy="arm")
                    w = S.paired(sub, arm, comparator, "wrong", "unit", policy="arm")
                    rows.append({"tier": tier, "family": family, "stratum": stratum, "arm": arm, "comparator": comparator,
                                 "correct_diff": d["difference"], "lo": d["ci"][0], "hi": d["ci"][1],
                                 "wrong_diff": w["difference"], "units": d["units"], "episodes": d["episodes"],
                                 "arm_correct": float(sub[sub.arm == arm].correct.mean()),
                                 "comparator_correct": float(sub[sub.arm == comparator].correct.mean())})
    return rows


def selected_calibration(scored: pd.DataFrame, forecast_rows: list[dict], arms: list[str], worlds: list[str]) -> list[dict]:
    """Step-0 calibration of each world on the action each arm chose (evaluation side, truth used only to score)."""
    index = {}
    for r in forecast_rows:
        index[(r["dataset"], str(r["tier"]), r["fold"], r["compound"], r["h1"], r["h2"], r["key"])] = r
    out = []
    for arm in arms:
        a = scored[(scored.arm == arm) & scored.first_action.notna()]
        acc = {w: {"p": [], "y": [], "unit": []} for w in worlds}
        for r in a.itertuples():
            item = index.get((r.dataset, r.tier, r.fold, r.compound, r.h1, r.h2, r.first_action))
            if item is None:
                continue
            first = r.steps[0]
            if first.get("lifecycle") != "measured_valid":
                continue
            truth_is_h1 = r.truth == r.h1
            outcome = first["outcome"]
            wrong = (outcome == "eliminate_a" and truth_is_h1) or (outcome == "eliminate_b" and not truth_is_h1)
            for w in worlds:
                entry = item["worlds"].get(w)
                if not entry:
                    continue
                vec = entry["h1" if truth_is_h1 else "h2"]
                acc[w]["p"].append(vec[1 if truth_is_h1 else 0])
                acc[w]["y"].append(float(wrong))
                acc[w]["unit"].append(f"{r.dataset}:{r.unit}")
        for w in worlds:
            p, y = np.asarray(acc[w]["p"]), np.asarray(acc[w]["y"])
            if len(p) == 0:
                continue
            codes, n = pd.factorize(pd.Series(acc[w]["unit"]))[0], len(set(acc[w]["unit"]))
            ratio_ci = None
            if y.sum() > 0:
                sums_y = np.bincount(codes, weights=y, minlength=n)
                sums_p = np.bincount(codes, weights=p, minlength=n)
                index_b = np.random.default_rng(S.SEED).integers(n, size=(S.DRAWS, n))
                boot = sums_y[index_b].sum(1) / np.maximum(sums_p[index_b].sum(1), 1e-12)
                ratio_ci = np.quantile(boot, [0.025, 0.975]).tolist()
            out.append({"arm": arm, "world": w, "steps": int(len(p)), "units": int(n), "mean_forecast": float(p.mean()),
                        "observed": float(y.mean()), "ratio": float(y.sum() / max(p.sum(), 1e-12)), "ratio_ci": ratio_ci})
    return out
