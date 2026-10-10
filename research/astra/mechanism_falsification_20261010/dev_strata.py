"""Coverage and set size of development runs by drug activity and by stratum.

Activity of a drug = mean over its measured options of its signature norm's percentile in the
reference norm distribution of that option (dev_programs.drug_activity); it is computed from the
full profile, so it is a descriptor for reporting, not something an episode sees. Bins:
[0, 0.5), [0.5, 0.65), [0.65, 0.75), [0.75, 1].
Usage: python dev_strata.py run1 [run2 ...] [--budget B]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import dev_programs as DP
import study as S

HERE = Path(__file__).resolve().parent
BINS = ((0.0, 0.5), (0.5, 0.65), (0.65, 0.75), (0.75, 1.01))


def table(rows: list[dict], act: dict[str, float], budget: int) -> dict:
    out = {}
    for pol in sorted({r["policy"] for r in rows}):
        rs = [r for r in rows if r["policy"] == pol and r["steps"]]
        per = {}
        for lo, hi in BINS:
            sel = [r for r in rs if lo <= act[r["drug"]] < hi]
            st = [r["steps"][min(budget, len(r["steps"])) - 1] for r in sel]
            if st:
                per[f"{lo:.2f}-{min(hi, 1):.2f}"] = {"n": len(st), "coverage": float(np.mean([s["covered"] for s in st])),
                                                     "mean_set": float(np.mean([s["set_size"] for s in st])),
                                                     "cred_coverage": float(np.mean([s["cred_covered"] for s in st]))}
        st = [r["steps"][min(budget, len(r["steps"])) - 1] for r in rs]
        per["all"] = {"n": len(st), "coverage": float(np.mean([s["covered"] for s in st])),
                      "mean_set": float(np.mean([s["set_size"] for s in st])), "share_set_le_20": float(np.mean([s["set_size"] <= 20 for s in st]))}
        out[pol] = per
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--budget", type=int, default=4)
    a = ap.parse_args()
    data = S.load_tier("open")
    av = DP.drug_activity(data["x"], data["role"] == "reference")
    act = {str(d): float(x) for d, x in zip(data["drug"], av)}
    for name in a.runs:
        r = json.loads((HERE / "development" / f"{name}.json").read_text(encoding="utf-8"))
        ref = {m for m in {x["moa"] for x in r["rows"]}}
        for stratum in ("all", "referenced", "knowledge_only"):
            rows = r["rows"] if stratum == "all" else [x for x in r["rows"] if (stratum == "referenced") == (x["moa"] in referenced_classes(r))]
            t = table(rows, act, a.budget)
            for pol, per in t.items():
                cells = "  ".join(f"{k}:n={v['n']} cov={v['coverage']:.2f} set={v['mean_set']:.0f}" for k, v in per.items() if k != "all")
                print(f"{name:22s} {stratum:14s} {pol:9s} all cov={per['all']['coverage']:.3f} set={per['all']['mean_set']:.1f} le20={per['all']['share_set_le_20']:.2f} | {cells}")


_REF: dict = {}


def referenced_classes(run: dict) -> set:
    key = run["name"]
    if key not in _REF:
        split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
        _REF[key] = {v["moa"] for v in split["drugs"].values() if v["role"] == "reference"}
        if run["config"].get("permute_classes"):
            pass  # strata are defined by the unpermuted split
    return _REF[key]


if __name__ == "__main__":
    main()
