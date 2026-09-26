"""Summarise the transition arms: cosine, R^2 against zero, replicate ceiling, and decision-relevant class recovery.

File summary
- Path: research/dynamic_world_model/analyze_transition.py
- Purpose: P3 (best learned time arm minus persistence) and the dose and context tables, on
  held-out compounds whose target response is detected, with skeleton-clustered intervals.
- Run: python research/dynamic_world_model/analyze_transition.py
- Depends on: common.py, analyze.py (bootstrap), transition.py (arm names)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import analyze as A
import common as C
from transition import ARMS, LEARNED

T3_ARMS = ("zero", "nearest_dose", "log_dose_interpolation", "ridge_neighbours")


def read(name: str) -> pd.DataFrame:
    with (C.OUTPUTS / "transition" / f"{name}.jsonl").open(encoding="utf-8") as stream:
        return pd.DataFrame([json.loads(line) for line in stream])


def summarise(frame: pd.DataFrame, arms, reference: str) -> dict:
    out = {"pairs": int(len(frame)), "compounds": int(frame.compound.nunique()),
           "ceiling_cosine": float(frame.ceiling.mean()), "arms": {}}
    clusters = frame.skeleton
    for arm in arms:
        cos = A.bootstrap_mean(frame[f"cos:{arm}"], clusters)
        r2 = A.bootstrap_mean(frame[f"r2:{arm}"], clusters)
        diff = A.bootstrap_mean(frame[f"cos:{arm}"] - frame[f"cos:{reference}"], clusters) if arm != reference else None
        entry = {"cosine": cos, "r2_vs_zero": r2, f"cosine_minus_{reference}": diff}
        if f"class:{arm}" in frame:
            known = frame[frame.klass.notna() & frame["class:observed"].notna()]
            entry["class_agrees_with_observed"] = float((known[f"class:{arm}"] == known["class:observed"]).mean()) if arm != "zero" else None
            entry["class_is_true_class"] = float((known[f"class:{arm}"] == known.klass).mean()) if arm != "zero" else None
        out["arms"][arm] = entry
    if "class:observed" in frame:
        known = frame[frame.klass.notna() & frame["class:observed"].notna()]
        out["observed_class_is_true_class"] = float((known["class:observed"] == known.klass).mean())
        out["class_pairs"] = int(len(known))
    return out


def main() -> None:
    results = {}
    for name in ("T2_time", "T4_context", "dose_single_source"):
        frame = read(name)
        detected = frame[frame.target_detected]
        results[name] = {"detected_targets": summarise(detected, ARMS, "persistence"),
                         "all_targets": summarise(frame, ARMS, "persistence")}
    t3 = read("T3_dose")
    results["T3_dose"] = {kind: summarise(t3[(t3.kind == kind) & t3.target_detected], T3_ARMS, "nearest_dose")
                          for kind in ("interpolation", "extrapolation")}
    t2 = results["T2_time"]["detected_targets"]["arms"]
    best = max(LEARNED, key=lambda a: t2[a]["cosine"]["mean"])
    results["P3"] = {"best_learned_arm": best, "difference_vs_persistence": t2[best]["cosine_minus_persistence"],
                     "selection_note": "the best arm is chosen on the same held-out results it is reported on; the interval is therefore optimistic"}
    C.write_json(C.OUTPUTS / "analysis" / "transition_summary.json", C.clean(results))
    for name, block in results.items():
        if name == "P3":
            continue
        for subset, s in block.items():
            print(f"\n{name} [{subset}] pairs={s['pairs']} compounds={s['compounds']} ceiling={s['ceiling_cosine']:.3f}"
                  + (f" observed-class-correct={s['observed_class_is_true_class']:.3f}" if 'observed_class_is_true_class' in s else ""))
            for arm, e in s["arms"].items():
                d = next((v for k, v in e.items() if k.startswith("cosine_minus_") and v), None)
                extra = f" class-true={e['class_is_true_class']:.3f}" if e.get("class_is_true_class") is not None else ""
                print(f"  {arm:24s} cos={e['cosine']['mean']:.3f} r2={e['r2_vs_zero']['mean']:+.3f}"
                      + (f" d={d['mean']:+.3f} [{d['low']:+.3f},{d['high']:+.3f}]" if d else "") + extra)
    p3 = results["P3"]
    d = p3["difference_vs_persistence"]
    print(f"\nP3: best learned = {p3['best_learned_arm']}, minus persistence = {d['mean']:+.3f} [{d['low']:+.3f}, {d['high']:+.3f}]")


if __name__ == "__main__":
    main()
