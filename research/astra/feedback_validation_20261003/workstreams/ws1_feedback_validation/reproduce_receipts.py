"""WS1 step 1: recompute discovery metrics from frozen receipts and rerun a few lines.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/reproduce_receipts.py
- Purpose: independent recomputation (not via analysis.py) of per-arm hit totals and the
  per-line H1 / S1 contrasts from campaigns.jsonl for the O'Neil development run (dev v2) and
  the ALMANAC confirmatory replay; then a deterministic rerun of a few lines with the frozen
  replay.run_line, compared record by record with the receipts.
- Interfaces: run the file with PYTHONPATH="src;." from D:/MAESTRO.
- Depends on: numpy, research.certified_discovery (frozen; imported, never edited).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import replay  # noqa: E402
from research.certified_discovery.screens import CACHE, sha256  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "receipts"
RUNS = {
    "oneil_dev_v2": ROOT / "research/certified_discovery/results/dev_20261003_v2",
    "almanac_confirm": ROOT / "research/certified_discovery/results/confirm_almanac_20261003/replay",
}


def boot(diff: np.ndarray, seed: int = 20261003, n: int = 10_000) -> list[float]:
    rng = np.random.default_rng(seed)
    d = rng.integers(0, diff.size, size=(n, diff.size))
    m = diff[d].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def table(records):
    t = defaultdict(lambda: defaultdict(list))
    for r in records:
        t[r["arm"]][r["line"]].append(r)
    out = {}
    for arm, lines in t.items():
        out[arm] = {}
        for line, runs in lines.items():
            out[arm][line] = {
                "exploit": float(np.mean([x["exploit"]["hits"] for x in runs])),
                "certify": float(np.mean([c["hits"] for x in runs for c in x["certify"]])),
                "line_hits": runs[0]["line_hits"], "budget": runs[0]["budget"],
            }
    return out


def contrast(t, a, va, b, vb):
    lines = sorted(t[a])
    d = np.array([t[a][l][va] - t[b][l][vb] for l in lines])
    return {"sum": float(d.sum()), "mean": float(d.mean()), "ci": boot(d),
            "better": int((d > 0).sum()), "worse": int((d < 0).sum()), "ties": int((d == 0).sum())}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    result = {}
    for name, run in RUNS.items():
        records = [json.loads(x) for x in open(run / "campaigns.jsonl", encoding="utf-8")]
        t = table(records)
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        arms = {}
        for arm in sorted(t):
            ex = sum(v["exploit"] for v in t[arm].values())
            ce = sum(v["certify"] for v in t[arm].values())
            s = summary["arms"].get(arm, {})
            arms[arm] = {"exploit": ex, "certify": ce,
                         "receipt_summary_exploit": s.get("exploit_hits_total"),
                         "receipt_summary_certify": s.get("certify_hits_total"),
                         "match": abs(ex - s.get("exploit_hits_total", np.nan)) < 1e-6
                         and abs(ce - s.get("certify_hits_total", np.nan)) < 1e-6}
        lines = sorted(t["wm_full"])
        result[name] = {
            "records": len(records), "lines": len(lines),
            "receipt_sha256": sha256(run / "campaigns.jsonl"),
            "total_line_hits": int(sum(t["wm_full"][l]["line_hits"] for l in lines)),
            "arms": arms,
            "H1_wm_full_certify_minus_history_exploit": contrast(t, "wm_full", "certify", "history", "exploit"),
            "S1_wm_full_minus_wm_static_exploit": contrast(t, "wm_full", "exploit", "wm_static", "exploit"),
            "wm_static_minus_history_exploit": contrast(t, "wm_static", "exploit", "history", "exploit"),
            "wm_greedy_minus_wm_static_exploit": contrast(t, "wm_greedy", "exploit", "wm_static", "exploit"),
            "wm_full_minus_history_exploit": contrast(t, "wm_full", "exploit", "history", "exploit"),
            "per_line": {l: {arm: t[arm][l]["exploit"] for arm in ("history", "wm_static", "wm_full", "wm_greedy")}
                         | {"wm_full_certify": t["wm_full"][l]["certify"], "line_hits": t["wm_full"][l]["line_hits"],
                            "budget": t["wm_full"][l]["budget"]} for l in lines},
        }
    # deterministic rerun of a few O'Neil lines and two ALMANAC lines with the frozen code
    rerun = {}
    for name, lib_file, line_ids in (("oneil_dev_v2", "oneil_v1.npz", [0, 7, 21]),
                                     ("almanac_confirm", "almanac_v1.npz", [0, 33])):
        records = [json.loads(x) for x in open(RUNS[name] / "campaigns.jsonl", encoding="utf-8")]
        spec = json.loads((RUNS[name] / "manifest.json").read_text(encoding="utf-8"))["spec"]
        for li in line_ids:
            new = replay.run_line((str(CACHE / lib_file), li, spec, replay.ARMS, {}))
            line = new[0]["line"]
            old = [r for r in records if r["line"] == line]
            om = {(r["arm"], r["seed"]): r for r in old}
            mism = []
            for r in new:
                o = om[(r["arm"], r["seed"])]
                for fld in ("exploit", "per_round_hits", "dose_points"):
                    if r[fld] != o[fld]:
                        mism.append((r["arm"], r["seed"], fld, r[fld], o[fld]))
                if [c["hits"] for c in r["certify"]] != [c["hits"] for c in o["certify"]]:
                    mism.append((r["arm"], r["seed"], "certify_hits"))
                if [c["nominated"] for c in r["certify"]] != [c["nominated"] for c in o["certify"]]:
                    mism.append((r["arm"], r["seed"], "certify_nominated"))
            rerun[f"{name}:{line}"] = {"records": len(new), "receipt_records": len(old), "mismatches": mism[:20],
                                       "n_mismatch": len(mism)}
    result["rerun_frozen_code"] = rerun
    (OUT / "step1_receipts_recomputed.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for name in RUNS:
        r = result[name]
        print(name, r["records"], "records", r["lines"], "lines", "hits", r["total_line_hits"])
        for arm, v in r["arms"].items():
            print(f"  {arm:20s} exploit {v['exploit']:8.1f} certify {v['certify']:8.1f} match={v['match']}")
        for k in ("H1_wm_full_certify_minus_history_exploit", "S1_wm_full_minus_wm_static_exploit",
                  "wm_static_minus_history_exploit", "wm_greedy_minus_wm_static_exploit", "wm_full_minus_history_exploit"):
            c = r[k]
            print(f"  {k:45s} sum {c['sum']:7.1f} mean {c['mean']:6.2f} [{c['ci'][0]:.2f},{c['ci'][1]:.2f}] "
                  f"+{c['better']}/-{c['worse']}/={c['ties']}")
    for k, v in rerun.items():
        print("rerun", k, v["records"], v["receipt_records"], "mismatches", v["n_mismatch"], v["mismatches"][:3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
