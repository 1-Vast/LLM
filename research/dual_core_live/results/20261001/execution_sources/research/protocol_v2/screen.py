"""Analysis of the protocol-v2 development screen: arm table, paired screens, departures, identifiability.

File summary
- Path: research/protocol_v2/screen.py
- Purpose: turn `run_dev.py`'s scored records and outcome tables into the pre-registered
  development-screen decisions (`protocol.json` `development_screen`), with the endpoints the
  protocol requires for every arm.
- Core points:
  - Arm table per tier: correct, wrong, abstention (deferral), decided, measurements, assay-days,
    net utility (+1 / -2 / 0, less 0.02 per measurement), selective risk, and the upper 95% bound
    of the wrong rate, all with unit-cluster intervals.
  - Paired against fixed for every candidate. `safety_screen` and `signal_screen` apply the rules
    as registered. A tier is eligible for the signal screen only if it passes the task gate.
  - Sensitivity for the primary candidate: re-clustered by Murcko scaffold, and split by scaffold
    overlap with the fold's training compounds and by structural applicability.
  - Departures of the baseline-safe arms: the share of decisions that left the fixed order, and
    the named reason for every decision that did not.
  - Identifiability from the evaluation-side outcome tables: per episode, whether any planned
    condition would remove the wrong hypothesis (identifiable), only the true one (misleading),
    both (conflicting), or none (unidentifiable with this menu). No policy can decide an
    unidentifiable episode, whatever its model.
- Run: python -m research.protocol_v2.screen --dev DIR --out FILE
- Interfaces: `arm_table`, `screens`, `departures`, `identifiability`, `main`
- Depends on: records.py, headroom.py, research/external_validation/statistics.py
"""
from __future__ import annotations

import argparse
import collections
import glob
import gzip
import json
from pathlib import Path

import pandas as pd

from research.external_validation import statistics as S

from . import headroom as H
from . import records as RC

PRICE = 0.02
MPIE, CORRECT_NI, WRONG_NI, COST_NI = 0.02, 0.01, 0.005, 0.10
CANDIDATES = ("safe", "safe_class", "belief", "anchored", "belief_robust", "myopic_edv", "random_legal")
PRIMARY = "safe"


def _paired(frame, left, right, metric, unit="unit"):
    sub = frame[frame.arm.isin((left, right))].copy()
    sub["policy"] = sub.arm
    sub["compound"] = sub.fold.astype(str) + ":" + sub.compound
    return S.paired(sub, left, right, metric, unit)


def arm_table(frame: pd.DataFrame) -> dict:
    frame = frame.assign(net_utility=frame.utility - PRICE * frame.measurements)
    out = {}
    for arm, g in frame.groupby("arm"):
        row = {m: S.rate(g, m, "unit") for m in ("correct", "wrong", "deferred", "decided", "measurements", "days",
                                                 "net_utility")}
        blocks = g.groupby(g.unit.astype(str)).agg(n=("wrong", "sum"), d=("decided", "sum")).sort_index()
        row["selective_risk"] = {"estimate": float(g.wrong.sum() / max(g.decided.sum(), 1e-12)),
                                 "ci": S._interval(blocks.n.to_numpy(float), blocks.d.to_numpy(float),
                                                   S.draws(len(blocks)), 0.95)}
        row["wrong_upper95"] = row["wrong"]["ci"][1]
        out[arm] = row
    return out


def screens(frame: pd.DataFrame, gates: dict) -> dict:
    out = {"per_tier": {}}
    frame = frame.assign(net_utility=frame.utility - PRICE * frame.measurements)
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        name = f"{dataset}:{tier}"
        entry = {"task_gate": gates[name]["gate"], "vs_fixed": {}}
        for cand in CANDIDATES:
            if cand not in set(g.arm):
                continue
            d = {m: _paired(g, cand, "fixed", m) for m in ("correct", "wrong", "measurements", "days", "net_utility")}
            safety = d["correct"]["ci"][0] >= -CORRECT_NI and d["wrong"]["ci"][1] <= WRONG_NI
            signal = d["correct"]["difference"] >= MPIE and d["correct"]["ci"][0] > 0
            entry["vs_fixed"][cand] = {**d, "safety_pass": bool(safety), "signal_pass": bool(signal),
                                       "cost_pass": bool(d["measurements"]["ci"][1] <= COST_NI)}
        out["per_tier"][name] = entry
    for cand in CANDIDATES:
        tiers = {n: e["vs_fixed"][cand] for n, e in out["per_tier"].items() if cand in e["vs_fixed"]}
        if not tiers:
            continue
        safe_all = all(t["safety_pass"] for t in tiers.values())
        eligible = [n for n, e in out["per_tier"].items() if e["task_gate"]["eligible_primary"]]
        signal_any = [n for n in eligible if tiers[n]["signal_pass"]]
        out.setdefault("decisions", {})[cand] = {
            "safety": "SAFE_ON_DEVELOPMENT" if safe_all else "UNSAFE_ON_DEVELOPMENT",
            "unsafe_tiers": [n for n, t in tiers.items() if not t["safety_pass"]],
            "signal": "ADVANCE_TO_EXTERNAL_REGISTRATION" if (safe_all and signal_any) else "NO_DEVELOPMENT_SIGNAL",
            "signal_tiers": signal_any, "eligible_tiers": eligible}
    return out


def sensitivity(frame: pd.DataFrame, candidate: str = PRIMARY) -> dict:
    out = {}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        g = g.copy()
        g["scaffold_cluster"] = [s if isinstance(s, str) and s else f"none:{c}" for s, c in zip(g.scaffold, g.compound)]
        row = {"by_murcko_scaffold_cluster": _paired(g, candidate, "fixed", "correct", "scaffold_cluster")}
        overlap = []
        for (fold,), sub in g.groupby(["fold"]):
            train = set(g[g.fold != fold].scaffold.dropna())
            overlap += [(i, "scaffold_seen" if s in train else "scaffold_held_out") for i, s in zip(sub.index, sub.scaffold)]
        g["overlap"] = pd.Series(dict(overlap))
        g["applicability"] = ["no_structure" if pd.isna(t) else "<0.40" if t < 0.40 else ">=0.40"
                              for t in g.max_train_tanimoto]
        for column in ("overlap", "applicability"):
            row[column] = {}
            for value, sub in g.groupby(column):
                units = sub[sub.arm == candidate].unit.nunique()
                row[column][value] = ({"units": int(units), **_paired(sub, candidate, "fixed", "correct"),
                                       "descriptive_only": units < 50} if units >= 5 else
                                      {"units": int(units), "status": "too_few_units"})
        out[f"{dataset}:{tier}"] = row
    return out


def departures(path: Path, arms=("safe", "safe_class", "anchored")) -> dict:
    counts = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(str(path / "scored" / "*.jsonl.gz"))):
        task = Path(f).name.rsplit("_", 1)[0]
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r["arm"] not in arms:
                    continue
                for s in r["steps"]:
                    n = s.get("note") or {}
                    why = n.get("why") or n.get("anchor") or "unknown"
                    counts[(task, r["arm"])][why] += 1
                    counts[(task, r["arm"])]["decisions"] += 1
                if r["stop"] not in ("eliminated", "measurement_budget_spent", "no_legal_action"):
                    counts[(task, r["arm"])][f"stop:{r['stop']}"] += 1
                    counts[(task, r["arm"])]["decisions"] += 1
    out = {}
    for (task, arm), c in sorted(counts.items()):
        n = c.pop("decisions")
        departed = sum(v for k, v in c.items() if k in ("supported_better_action", "supported_extra_measurement",
                                                       "deviation_supported", "stop:baseline_safe_supported_stop",
                                                       "stop_supported"))
        out[f"{task}:{arm}"] = {"decisions": n, "departure_rate": departed / max(n, 1), "reasons": dict(c)}
    return out


def identifiability(path: Path) -> dict:
    out = {}
    for f in sorted(glob.glob(str(path / "tables" / "*.jsonl.gz"))):
        task = Path(f).name.rsplit("_", 1)[0]
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                t = json.loads(line)
                truth, other = t["truth"], (t["h2"] if t["truth"] == t["h1"] else t["h1"])
                removes = {"eliminate_b": t["h2"], "eliminate_a": t["h1"]}
                removed = {removes.get(o["outcome"]) for o in t["outcomes"].values()} - {None}
                kind = ("conflicting" if removed == {truth, other} else "identifiable" if removed == {other}
                        else "misleading" if removed == {truth} else "unidentifiable_with_this_menu")
                c = out.setdefault(task, collections.Counter())
                c[kind] += 1
                c["episodes"] += 1
    return {task: {"episodes": c["episodes"], **{k: c[k] / c["episodes"] for k in
                                                 ("identifiable", "conflicting", "misleading",
                                                  "unidentifiable_with_this_menu")}}
            for task, c in out.items()}


BUDGET = {"sciplex3": 16.0, "l1000": 12.0}


def _days(dataset: str, action: str) -> float:
    hours = float(action.split("|")[1].rstrip("h"))
    return ({24.0: 1.0, 72.0: 3.0}[hours] + 5.0) if dataset == "sciplex3" else hours / 24.0 + 5.0


def second_step_headroom(path: Path, frame: pd.DataFrame, arms=("fixed", "belief")) -> dict:
    """After an arm's real, non-terminal first measurement: how often some legal second measurement
    would have decided correctly (hidden outcomes), against how often the arm's own second did.

    This bounds what feedback can add at the second step, whatever the model: feedback can only
    matter in these episodes, and only by finding a correct second measurement.
    """
    tables = {}
    for f in sorted(glob.glob(str(path / "tables" / "*.jsonl.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                t = json.loads(line)
                tables[(t["dataset"], t["tier"], t["fold"], t["compound"], t["h1"], t["h2"])] = t
    out = {}
    for (dataset, tier, arm), g in frame[frame.arm.isin(arms)].groupby(["dataset", "tier", "arm"]):
        n = gainable = achieved = 0
        for r in g.itertuples():
            if not r.first_action or r.first_outcome not in ("ambiguous", "undetected", "quality_failed"):
                continue
            t = tables[(dataset, tier, r.fold, r.compound, r.h1, r.h2)]
            wrong_label = "eliminate_b" if t["truth"] == r.h1 else "eliminate_a"
            first_time = float(r.first_action.split("|")[1].rstrip("h"))
            spent = _days(dataset, r.first_action)
            legal = [a for a in t["outcomes"] if a != r.first_action and float(a.split("|")[1].rstrip("h")) >= first_time
                     and spent + _days(dataset, a) <= BUDGET[dataset] + 1e-9]
            if not legal:
                continue
            n += 1
            gainable += any(t["outcomes"][a]["outcome"] == wrong_label for a in legal)
            achieved += r.correct == 1.0 and r.measurements == 2
        out[f"{dataset}:{tier}:{arm}"] = {"episodes_with_a_legal_second": n,
                                          "best_second_correct": gainable / max(n, 1),
                                          "arm_second_correct": achieved / max(n, 1),
                                          "second_step_headroom": (gainable - achieved) / max(n, 1),
                                          "share_of_all_episodes": n / max(len(g), 1)}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", default="outputs/protocol_v2_20260927/dev")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = Path(args.dev)
    frame = RC.load(path / "scored")
    gates = H.headroom_table(frame, candidate="belief")
    result = {"headroom": gates, "arms": {}, "screens": screens(frame, gates), "sensitivity": sensitivity(frame),
              "departures": departures(path), "identifiability": identifiability(path),
              "second_step_headroom": second_step_headroom(path, frame)}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        result["arms"][f"{dataset}:{tier}"] = arm_table(g)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(json.dumps(result, indent=1, default=float).encode("utf-8"))
    for name, e in result["screens"]["per_tier"].items():
        print(name, e["task_gate"]["status"])
        for cand, d in e["vs_fixed"].items():
            print(f"   {cand:14s} correct {d['correct']['difference']:+.3f} [{d['correct']['ci'][0]:+.3f},{d['correct']['ci'][1]:+.3f}]"
                  f" wrong {d['wrong']['difference']:+.3f} [..,{d['wrong']['ci'][1]:+.3f}]"
                  f" meas {d['measurements']['difference']:+.2f} [..,{d['measurements']['ci'][1]:+.2f}]"
                  f" net {d['net_utility']['difference']:+.3f}  safety {d['safety_pass']} signal {d['signal_pass']}")
    print(json.dumps(result["screens"]["decisions"], indent=1))
    print(json.dumps({k: {kk: round(vv, 3) if isinstance(vv, float) else vv for kk, vv in v.items()}
                      for k, v in result["identifiability"].items()}, indent=None))
    print(json.dumps({k: round(v["departure_rate"], 4) for k, v in result["departures"].items()}, indent=None))
    print(json.dumps({k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in result["second_step_headroom"].items()},
                     indent=None))


if __name__ == "__main__":
    main()
