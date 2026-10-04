"""Summarise a feedback-decomposition run: totals, parity with frozen receipts, paired contrasts.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/summarise_decomposition.py
- Purpose: per-arm hit totals, parity of the replicated loop against the frozen receipts,
  per-line paired differences with 95% percentile bootstrap over lines (10,000, seed 20261003),
  selection overlap between arms and final-round prediction quality.
- Interfaces: run the file with PYTHONPATH="src;." RUN_NAME RECEIPT_DIR.
- Depends on: numpy.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def boot(d, seed=20261003, n=10_000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def hits(entry):
    return float(np.mean([e["hits"] for e in entry])) if isinstance(entry, list) else float(entry["hits"])


def purchased(entry):
    return set(x for r in entry["purchases"] for x in r)


CONTRASTS = [
    ("full_phit", "static_phit", "S1 registered form: full feedback vs static, P(hit) acquisition"),
    ("full_mean", "static_mean", "feedback under mean ranking"),
    ("offset_mean", "static_mean", "offset-only (mean): analytic expectation 0"),
    ("offset_phit", "static_phit", "offset-only (P(hit))"),
    ("drug_mean", "full_mean", "drug-only from joint posterior vs full (mean): analytic expectation 0"),
    ("drug_mean", "static_mean", "drug-in-line effects vs static (mean)"),
    ("drug_phit", "static_phit", "drug-in-line effects vs static (P(hit))"),
    ("drug_nooffset_mean", "full_mean", "drug model without offset term vs full (mean)"),
    ("full_mean", "shufres_mean", "full vs residual-shuffle control (mean)"),
    ("full_phit", "shufres_phit", "full vs residual-shuffle control (P(hit))"),
    ("shufres_mean", "static_mean", "residual-shuffle control vs static (mean)"),
    ("full_mean", "shuflab_mean", "full vs label-shuffle control (mean)"),
    ("shuflab_mean", "static_mean", "label-shuffle control vs static (mean)"),
    ("static_mean", "history", "ridge static model vs static retrieval"),
    ("gbm_static", "history", "GBM static model vs static retrieval"),
    ("gbm_static", "static_mean", "GBM static vs ridge static"),
    ("full_mean", "gbm_static", "full feedback (ridge prior) vs GBM static"),
    ("full_phit", "history", "wm_full (exploit) vs history"),
    ("gbm_feedback_mean", "gbm_static", "feedback on top of GBM prior"),
    ("history_feedback_mean", "history", "feedback on top of history prior"),
    ("history_feedback_mean", "full_mean", "history+feedback vs ridge+feedback"),
    ("full_phit", "full_mean", "S3: P(hit) vs mean acquisition"),
]


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    run_dir = HERE / "receipts" / argv[0]
    receipt = Path(argv[1]) if len(argv) > 1 else None
    lines = [json.loads(x) for x in open(run_dir / "lines.jsonl", encoding="utf-8")]
    names = sorted(lines[0]["arms"])
    table = {a: np.array([hits(l["arms"][a]) for l in lines]) for a in names}
    total_hits = sum(l["line_hits"] for l in lines)
    out = {"run": str(run_dir.relative_to(ROOT)), "lines": len(lines), "total_line_hits": total_hits,
           "totals": {a: round(float(v.sum()), 2) for a, v in sorted(table.items(), key=lambda kv: -kv[1].sum())},
           "contrasts": {}, "parity": {}, "overlap": {}, "prediction": {}, "variances": {}}
    for a, b, label in CONTRASTS:
        d = table[a] - table[b]
        out["contrasts"][f"{a} - {b}"] = {"label": label, "sum": round(float(d.sum()), 2), "mean": round(float(d.mean()), 3),
                                          "ci": boot(d), "better": int((d > 0).sum()), "worse": int((d < 0).sum())}
    # parity with frozen receipts and internal analytic identities
    if receipt is not None:
        recs = [json.loads(x) for x in open(receipt / "campaigns.jsonl", encoding="utf-8")]
        by = defaultdict(dict)
        for r in recs:
            if r["arm"] in ("history", "wm_static", "wm_full", "wm_greedy", "oracle"):
                by[r["arm"]][r["line"]] = r["exploit"]["hits"]
        rnd = defaultdict(list)
        for r in recs:
            if r["arm"] == "random":
                rnd[r["line"]].append(r["exploit"]["hits"])
        pairs = {"history": "history", "wm_static": "frozen_wm_static", "wm_full": "frozen_wm_full",
                 "wm_greedy": "frozen_wm_greedy", "oracle": "oracle"}
        for rec_arm, my_arm in pairs.items():
            mism = [l["line"] for l in lines if by[rec_arm][l["line"]] != hits(l["arms"][my_arm])]
            out["parity"][f"receipt {rec_arm} == {my_arm}"] = {"lines_mismatched": len(mism), "examples": mism[:5]}
        mism = [l["line"] for l in lines if abs(np.mean(rnd[l["line"]]) - hits(l["arms"]["random"])) > 1e-9]
        out["parity"]["receipt random == random"] = {"lines_mismatched": len(mism)}
    for a, b in (("static_phit", "frozen_wm_static"), ("full_phit", "frozen_wm_full"), ("full_mean", "frozen_wm_greedy"),
                 ("offset_mean", "static_mean"), ("drug_mean", "full_mean")):
        same = [purchased(l["arms"][a]) == purchased(l["arms"][b]) for l in lines]
        out["parity"][f"identical purchases {a} vs {b}"] = {"lines_identical": int(sum(same)), "of": len(lines)}
    # selection overlap: how much does feedback change what is bought, and where do the hits differ
    for a, b in (("full_mean", "static_mean"), ("full_phit", "static_phit"), ("full_mean", "history"),
                 ("full_mean", "gbm_static"), ("static_mean", "history")):
        jacc, only_a_hits, only_b_hits, only_a, only_b = [], 0, 0, 0, 0
        for l in lines:
            pa, pb = purchased(l["arms"][a]), purchased(l["arms"][b])
            jacc.append(len(pa & pb) / max(len(pa | pb), 1))
            rows = np.array(l["rows"])
            # hits are recomputed from purchases against the library
            only_a += len(pa - pb)
            only_b += len(pb - pa)
            only_a_hits += sum(_hit_cache[(run_dir.name, l["line_index"], i)] for i in pa - pb) if _hit_cache else 0
            only_b_hits += sum(_hit_cache[(run_dir.name, l["line_index"], i)] for i in pb - pa) if _hit_cache else 0
        out["overlap"][f"{a} vs {b}"] = {"mean_jaccard": round(float(np.mean(jacc)), 3), "only_a": only_a, "only_b": only_b,
                                         "only_a_hits": only_a_hits, "only_b_hits": only_b_hits}
    keys = [k for k in lines[0]["arms"]["full_mean"] if k.startswith("pred_")]
    for k in keys:
        v = np.array([l["arms"]["full_mean"][k] for l in lines], float)
        out["prediction"][k] = round(float(np.nanmean(v)), 3) if not k.endswith("top_last_hits") else float(v.sum())
    for name in ("ridge", "gbm", "history"):
        out["prediction"][f"prior_{name}_r_mean"] = round(float(np.mean([l["prior_quality"][name]["r"] for l in lines])), 3)
        out["prediction"][f"prior_{name}_rmse_mean"] = round(float(np.mean([l["prior_quality"][name]["rmse"] for l in lines])), 3)
    for k in ("s_line", "s_drug", "s_noise"):
        v = np.array([l[k] for l in lines])
        out["variances"][k] = {"median": round(float(np.median(v)), 3), "min": round(float(v.min()), 3), "max": round(float(v.max()), 3)}
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("total line hits", total_hits)
    for a, v in out["totals"].items():
        print(f"  {a:24s} {v:9.1f}")
    for k, c in out["contrasts"].items():
        print(f"  {k:40s} sum {c['sum']:8.1f} mean {c['mean']:6.2f} [{c['ci'][0]:6.2f},{c['ci'][1]:6.2f}] +{c['better']}/-{c['worse']}")
    for k, v in out["parity"].items():
        print("  parity", k, v)
    for k, v in out["overlap"].items():
        print("  overlap", k, v)
    print("  prediction", out["prediction"])
    print("  variances", out["variances"])
    return 0


_hit_cache: dict = {}


def _load_hits(run_name: str, library: str):
    sys.path.insert(0, str(ROOT))
    from research.certified_discovery.screens import CACHE, load_library
    lib = load_library(CACHE / library)
    lines = [json.loads(x) for x in open(HERE / "receipts" / run_name / "lines.jsonl", encoding="utf-8")]
    for l in lines:
        rows = np.array(l["rows"])
        h = lib.y[rows] > lib.threshold
        for i in range(rows.size):
            _hit_cache[(run_name, l["line_index"], i)] = int(h[i])


if __name__ == "__main__":
    run = sys.argv[1]
    lib_file = "almanac_v1.npz" if "almanac" in run else "oneil_v1.npz"
    _load_hits(run, lib_file)
    raise SystemExit(main())
