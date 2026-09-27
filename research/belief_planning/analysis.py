"""Frozen analysis: matched rates, paired gates, attribution of agent and virtual cell, calibration, frontiers.

File summary
- Path: research/belief_planning/analysis.py
- Purpose: turn the registered records (development or external) into the endpoints and gates
  that `protocol.json` pre-registers.
- Core points:
  - Units:
    - Independent units: SciPlex3 skeletons, L1000 identity/scaffold components, and GSE70138
      test-compound components.
    - Intervals are 2,000-draw unit-cluster bootstraps (seed 20260927, `external_validation.statistics`).
    - Episodes, cells and replicates are never the unit.
  - Endpoints are reported separately:
    - correct, wrong and deferred decisions;
    - coverage (a decision reached) and selective risk (wrong among decided);
    - measurements, assay-days and wells.
    Utility (+1 / -2 / 0 with 0.02 per measurement) is secondary.
  - Gates (candidate minus comparator, same episodes):
    - G1: the upper bound of the candidate's wrong rate is at most 0.05.
    - G2: the upper bound of the wrong difference is at most +0.005.
    - G3: the lower bound of the correct difference is above 0, and the estimate is at least
      0.02 (MPIE).
    - G4: the upper bound of the measurement difference is at most +0.10.
    Status:
    - DEMONSTRATED if G1-G4 all pass.
    - REJECTED if the upper bound of the correct difference is below -0.01, or the lower bound
      of the wrong rate is above 0.05.
    - INCONCLUSIVE otherwise.
  - Contribution of the virtual cell (real vs masked, real vs permuted) and of feedback (true vs
    withheld, true vs permuted): report
    - the action-switch rate;
    - the difference on switched episodes;
    - the overall difference, wrong difference and cost difference.
    Status:
    - DEMONSTRATED if the lower bound of the overall correct difference is above 0 against both
      controls.
    - REJECTED as a practically meaningful contribution if the upper bound is below the MPIE
      against either control.
    - INCONCLUSIVE otherwise.
  - Calibration: forecasts of the chosen action, for the true hypothesis's branch (correct- and
    wrong-elimination probability), against the realised reading. Overall and by stratum
    (support, line, dose, time, detection, scaffold novelty). ECE is diagnostic only. Sparse
    or separated strata use the stable fits in `statistics.calibration_metrics`.
- Run: python -m research.belief_planning.analysis --records DIR_OR_FILE --out DIR [--external]
- Depends on: research/external_validation/statistics.py, replay.py, matplotlib
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.external_validation import statistics as S

from . import replay as R

CAP, WRONG_NI, MPIE, CORRECT_NI, COST_NI = 0.05, 0.005, 0.02, 0.01, 0.10
PRICE = 0.02
CANDIDATES = ("belief", "anchored")
PRIMARY_COMPARATOR = "fixed"
VC_CONTROLS = ("belief_vc_masked", "belief_vc_permuted")
FEEDBACK_CONTROLS = ("belief_feedback_withheld", "belief_feedback_permuted")
BASELINES = ("defer_floor", "random_legal", "fixed", "cost_only", "marginal_only", "retrieval", "magnitude",
             "ridge", "info_gain", "myopic_edv")


def load(path: Path) -> pd.DataFrame:
    files = [path] if path.is_file() else sorted(Path(p) for p in glob.glob(str(path / "*.jsonl.gz")))
    rows = []
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows += [json.loads(line) for line in fh]
    frame = pd.DataFrame(rows)
    frame["policy"] = frame["arm"]
    frame = S.outcome_columns(frame)
    frame["utility_priced"] = frame.utility - PRICE * frame.measurements
    if "wells" not in frame.columns:
        frame["wells"] = [2 * len(s) + 4 * len({(x["key"][0], x["key"][1]) for x in s}) for s in frame.steps]
    frame["first_action"] = [s[0]["action"] if s else None for s in frame.steps]
    frame["second_action"] = [s[1]["action"] if len(s) > 1 else None for s in frame.steps]
    frame["sequence"] = ["|".join(x["action"] for x in s) for s in frame.steps]
    frame["episode"] = frame.compound + "|" + frame.h1 + "|" + frame.h2 + "|" + frame.fold.astype(str)
    return frame


def _ratio(frame, num, den, unit):
    blocks = frame.groupby(frame[unit].astype(str)).agg(n=(num, "sum"), d=(den, "sum")).sort_index()
    index = S.draws(len(blocks))
    est = float(frame[num].sum() / max(frame[den].sum(), 1e-12))
    return {"estimate": est, "ci": S._interval(blocks.n.to_numpy(float), blocks.d.to_numpy(float), index, 0.95)}


def arm_table(frame: pd.DataFrame) -> dict:
    out = {}
    for arm, g in frame.groupby("arm"):
        out[arm] = {m: S.rate(g, m, "unit") for m in ("correct", "wrong", "deferred", "decided", "measurements",
                                                          "days", "wells", "utility", "utility_priced")}
        out[arm]["selective_risk"] = _ratio(g, "wrong", "decided", "unit")
        out[arm]["episodes"] = int(len(g))
    return out


def _pair(frame, left, right, metric):
    sub = frame[frame.arm.isin((left, right))].copy()
    sub["policy"] = sub.arm
    sub = sub.assign(fold_compound=sub.compound)
    # episodes are unique within a tier by (fold, compound, h1, h2); fold is folded into the compound key
    sub["compound"] = sub.fold.astype(str) + ":" + sub.compound
    return S.paired(sub, left, right, metric, "unit")


def gates(frame: pd.DataFrame, candidate: str, comparator: str) -> dict:
    cand = frame[frame.arm == candidate]
    wrong_rate = S.rate(cand, "wrong", "unit")
    d = {m: _pair(frame, candidate, comparator, m) for m in ("correct", "wrong", "measurements", "days", "utility_priced")}
    g = {
        "G1_wrong_rate_upper_le_cap": wrong_rate["ci"][1] <= CAP,
        "G2_wrong_difference_upper_le_margin": d["wrong"]["ci"][1] <= WRONG_NI,
        "G3_correct_difference_lower_gt_0_and_estimate_ge_mpie": d["correct"]["ci"][0] > 0 and d["correct"]["difference"] >= MPIE,
        "G4_measurement_difference_upper_le_margin": d["measurements"]["ci"][1] <= COST_NI,
    }
    if all(g.values()):
        status = "DEMONSTRATED"
    elif d["correct"]["ci"][1] < -CORRECT_NI or wrong_rate["ci"][0] > CAP:
        status = "REJECTED"
    else:
        status = "INCONCLUSIVE"
    return {"candidate": candidate, "comparator": comparator, "wrong_rate": wrong_rate, "differences": d,
            "gates": g, "status": status}


def contribution(frame: pd.DataFrame, candidate: str, controls, *, step: int | None = None) -> dict:
    out = {}
    base = frame[frame.arm == candidate].set_index("episode")
    for control in controls:
        other = frame[frame.arm == control].set_index("episode").reindex(base.index)
        if step is None:
            switched = base.sequence != other.sequence
        else:
            both = (base.measurements > step) & (other.measurements > step)
            col = "first_action" if step == 0 else "second_action"
            switched = both & (base[col] != other[col])
        diff = {m: _pair(frame, candidate, control, m) for m in ("correct", "wrong", "measurements", "utility_priced")}
        sw = base[switched]
        benefit = float((sw.correct - other.loc[switched, "correct"]).mean()) if len(sw) else None
        benefit_wrong = float((sw.wrong - other.loc[switched, "wrong"]).mean()) if len(sw) else None
        if len(sw):
            tmp = pd.DataFrame({"delta": sw.correct - other.loc[switched, "correct"], "unit": sw.unit.astype(str)})
            blocks = tmp.groupby("unit").delta.agg(["sum", "size"]).sort_index()
            ci = S._interval(blocks["sum"].to_numpy(float), blocks["size"].to_numpy(float), S.draws(len(blocks)), 0.95)
        else:
            ci = None
        lower, upper = diff["correct"]["ci"]
        out[control] = {"switch_rate": float(switched.mean()), "switched_episodes": int(switched.sum()),
                        "benefit_on_switched_correct": benefit, "benefit_on_switched_ci": ci,
                        "benefit_on_switched_wrong": benefit_wrong, "overall": diff,
                        "status": "positive" if lower > 0 else ("no_practical_effect" if upper < MPIE else "inconclusive")}
    statuses = [v["status"] for v in out.values()]
    verdict = ("DEMONSTRATED" if all(s == "positive" for s in statuses) else
               "REJECTED" if any(s == "no_practical_effect" for s in statuses) else "INCONCLUSIVE")
    return {"controls": out, "status": verdict}


def feedback_use(frame: pd.DataFrame, candidate: str = "belief", control: str = "belief_feedback_withheld") -> dict:
    """When real feedback changes the second action, and whether that change improves the decision."""
    base = frame[frame.arm == candidate].set_index("episode")
    other = frame[frame.arm == control].set_index("episode").reindex(base.index)
    reached = (base.measurements >= 2) & (other.measurements >= 2) & (base.first_action == other.first_action)
    changed = reached & (base.second_action != other.second_action)
    stop_diff = (base.measurements != other.measurements) & (base.first_action == other.first_action)
    first_labels = [s[0]["outcome"] if s else None for s in base.steps]
    by_label = {}
    for label in ("ambiguous", "undetected", "quality_failed"):
        mask = pd.Series([f == label for f in first_labels], index=base.index)
        m = mask & reached
        by_label[label] = {"reached_second_step": int(m.sum()), "second_action_changed": int((m & changed).sum())}
    return {"episodes_reaching_step_2_in_both": int(reached.sum()), "second_action_changed": int(changed.sum()),
            "stopping_changed": int(stop_diff.sum()),
            "changed_correct_difference": float((base.correct[changed] - other.correct[changed]).mean()) if changed.any() else None,
            "changed_wrong_difference": float((base.wrong[changed] - other.wrong[changed]).mean()) if changed.any() else None,
            "by_first_reading": by_label}


def calibration(frame: pd.DataFrame, features: pd.DataFrame | None = None) -> dict:
    rows = pd.DataFrame(R.forecasts_for_calibration(frame.to_dict(orient="records")))
    if rows.empty:
        return {}
    if features is not None and not features.empty:
        rows = rows.merge(features, on=["tier", "fold", "compound"], how="left")
    out = {}
    for arm, g in rows.groupby("arm"):
        entry = {"correct": S.calibration_metrics(g.p_correct, g.y_correct),
                 "wrong": S.calibration_metrics(g.p_wrong, g.y_wrong), "strata": {}}
        strata = {"support": pd.cut(pd.to_numeric(g.support, errors="coerce"), [-1, 4, 9, 19, 49, 1e9],
                                    labels=["0-4", "5-9", "10-19", "20-49", "50+"]).astype(str),
                  "line": g.line.astype(str), "dose": g.dose.astype(str), "time": g.time.astype(str),
                  "detected": g.detected.astype(str), "step": g.step.astype(str)}
        if "max_train_tanimoto" in g.columns:
            strata["scaffold_novelty"] = pd.cut(g.max_train_tanimoto, [-1, 0.3, 0.4, 0.6, 1.01],
                                                labels=["<0.3", "0.3-0.4", "0.4-0.6", ">=0.6"]).astype(str)
        for name, labels in strata.items():
            entry["strata"][name] = {str(k): {"n": int(len(s)), "wrong": S.calibration_metrics(s.p_wrong, s.y_wrong),
                                              "correct": S.calibration_metrics(s.p_correct, s.y_correct)}
                                     for k, s in g.groupby(labels)}
        out[arm] = entry
    return out


def frontiers(table: dict) -> dict:
    points = [{"arm": a, "measurements": v["measurements"]["estimate"], "days": v["days"]["estimate"],
               "correct": v["correct"]["estimate"], "wrong": v["wrong"]["estimate"],
               "coverage": v["decided"]["estimate"], "selective_risk": v["selective_risk"]["estimate"]}
              for a, v in table.items()]
    def pareto(pts, x, y, better_low_x=True):
        keep = []
        for p in pts:
            dominated = any((q[x] <= p[x] and q[y] >= p[y]) and (q[x] < p[x] or q[y] > p[y]) for q in pts)
            if not dominated:
                keep.append(p["arm"])
        return keep
    under = [p for p in points if p["wrong"] <= CAP and p["arm"] != "oracle"]
    return {"points": points, "correct_cost_pareto_under_cap": pareto(under, "measurements", "correct"),
            "risk_coverage": sorted(({"arm": p["arm"], "coverage": p["coverage"], "selective_risk": p["selective_risk"]}
                                     for p in points), key=lambda r: r["coverage"])}


def figure(table: dict, title: str, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for arm, v in table.items():
        color = "#b2182b" if arm in CANDIDATES else ("#999999" if arm == "oracle" else "#2166ac")
        axes[0].errorbar(v["measurements"]["estimate"], v["correct"]["estimate"],
                         yerr=[[v["correct"]["estimate"] - v["correct"]["ci"][0]], [v["correct"]["ci"][1] - v["correct"]["estimate"]]],
                         fmt="o", color=color, ms=4, lw=0.8)
        axes[0].annotate(arm, (v["measurements"]["estimate"], v["correct"]["estimate"]), fontsize=6)
        axes[1].plot(v["decided"]["estimate"], v["selective_risk"]["estimate"], "o", color=color, ms=4)
        axes[1].annotate(arm, (v["decided"]["estimate"], v["selective_risk"]["estimate"]), fontsize=6)
    axes[0].set_xlabel("measurements per episode")
    axes[0].set_ylabel("correct terminal decisions")
    axes[0].set_title(f"{title}: correctness vs cost")
    axes[1].axhline(CAP, color="k", lw=0.5, ls="--")
    axes[1].set_xlabel("coverage (decided)")
    axes[1].set_ylabel("selective risk (wrong / decided)")
    axes[1].set_title(f"{title}: risk vs coverage")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def analyse(frame: pd.DataFrame, out: Path, *, comparators=("fixed", "myopic_edv", "retrieval", "marginal_only"),
            features=None) -> dict:
    summary = {}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        key = f"{dataset}|{tier}"
        table = arm_table(g)
        entry = {"arms": table, "frontiers": frontiers(table), "gates": {}, "attribution": {}}
        for cand in CANDIDATES:
            if cand in table:
                entry["gates"][cand] = {c: gates(g, cand, c) for c in comparators if c in table}
        if "belief" in table:
            entry["attribution"]["virtual_cell"] = contribution(g, "belief", [c for c in VC_CONTROLS if c in table])
            entry["attribution"]["feedback"] = contribution(g, "belief", [c for c in FEEDBACK_CONTROLS if c in table])
            if "belief_feedback_withheld" in table:
                entry["attribution"]["feedback_use"] = feedback_use(g)
            if "belief_h1" in table:
                entry["attribution"]["lookahead"] = contribution(g, "belief", ["belief_h1"])
        entry["calibration"] = calibration(g, features)
        baselines = {a: table[a]["correct"]["estimate"] for a in BASELINES if a in table and table[a]["wrong"]["estimate"] <= CAP}
        entry["strongest_baseline_under_cap"] = max(baselines, key=baselines.get) if baselines else None
        figure(table, key, out / "figures" / f"{dataset}_{tier}.png")
        summary[key] = entry
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_bytes(json.dumps(summary, indent=1, default=float).encode("utf-8"))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--features", default=None)
    args = parser.parse_args()
    frame = load(Path(args.records))
    features = pd.read_csv(args.features) if args.features else None
    summary = analyse(frame, Path(args.out), features=features)
    for key, entry in summary.items():
        print("==", key, "strongest baseline under cap:", entry["strongest_baseline_under_cap"])
        for cand, by in entry["gates"].items():
            for comp, g in by.items():
                d = g["differences"]["correct"]
                print(f"  {cand} vs {comp}: correct {d['difference']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}] "
                      f"wrong {g['differences']['wrong']['difference']:+.4f} meas {g['differences']['measurements']['difference']:+.2f} -> {g['status']}")
        for what in ("virtual_cell", "feedback", "lookahead"):
            a = entry["attribution"].get(what)
            if a:
                for c, v in a["controls"].items():
                    d = v["overall"]["correct"]
                    print(f"  {what} vs {c}: switch {v['switch_rate']:.3f} overall {d['difference']:+.3f} "
                          f"[{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}] switched-benefit {v['benefit_on_switched_correct']} -> {v['status']}")


if __name__ == "__main__":
    main()
