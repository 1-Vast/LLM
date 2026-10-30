"""E064: final audit block - C2, C23, C32 (BATCHIE side), C37, C39.

Pre-registered in PROTOCOL_E062.md. Three-state discipline as in R62/R63. Where a register
number is a report-level or derived value with no stored field, the check reports
not_located with that reason - it is NOT counted as a mismatch, but it IS reported.
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
E = "2026-10-27-agent-cell-identifiability-"
OUT = R / (E + "r64")
OUT.mkdir(parents=True, exist_ok=True)

CACHE = {}


def load(ep, fn):
    k = (ep, fn)
    if k not in CACHE:
        CACHE[k] = json.load(open(R / (E + ep) / fn, encoding="utf-8"))
    return CACHE[k]


def dig(obj, path):
    cur = obj
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            raise KeyError(".".join(str(x) for x in path))
    return cur


results = []


def check(claim, label, ep, fn, path, expected, tol, note=""):
    rec = {"claim": claim, "label": label, "episode": ep, "file": fn,
           "path": ".".join(str(p) for p in path), "expected": expected, "tol": tol}
    if note:
        rec["note"] = note
    try:
        val = dig(load(ep, fn), path)
    except (KeyError, FileNotFoundError) as exc:
        rec.update(status="not_located", actual=None, note=str(exc)[:120])
        results.append(rec)
        return
    try:
        fv = float(val)
    except (TypeError, ValueError):
        rec.update(status="mismatch", actual=val, note="not numeric")
        results.append(rec)
        return
    rec.update(status="ok" if abs(fv - expected) <= tol else "mismatch", actual=fv)
    results.append(rec)


def not_located(claim, label, reason):
    results.append({"claim": claim, "label": label, "status": "not_located",
                    "actual": None, "expected": "(report-level)", "note": reason})


# ---------------- C2: shared-order model rejected ----------------
check("C2", "validation cell pairs 192", "r5", "E006_RESULTS.json", ["primary", "n_cellpairs"], 192, 0)
check("C2", "validation cell pairs all positive", "r5", "E006_RESULTS.json", ["primary", "n_positive"], 192, 0)
check("C2", "high-diversity ceiling 0.947", "r20", "E020_RESULTS.json", ["same_cell_ceiling", "median_rho"], 0.947, 0.002)
check("C2", "high-diversity cross 0.816", "r20", "E020_RESULTS.json", ["cross_cell", "median_rho"], 0.816, 0.002)
check("C2", "gap +0.1395", "r20", "E020_RESULTS.json", ["gap", "mean_gap"], 0.1395, 0.002)
check("C2", "independence null 0.035", "r20", "E020_RESULTS.json", ["independence_null", "mean_rho"], 0.035, 0.003)
gap_ci = load("r20", "E020_RESULTS.json")["gap"]["ci95_layout_bootstrap"]
results.append({"claim": "C2", "label": "gap CI [0.1015,0.1735]", "episode": "r20",
                "file": "E020_RESULTS.json", "path": "gap.ci95_layout_bootstrap",
                "expected": [0.1015, 0.1735], "actual": gap_ci, "tol": 0.002,
                "status": "ok" if abs(gap_ci[0] - 0.1015) < 0.002 and abs(gap_ci[1] - 0.1735) < 0.002 else "mismatch"})
not_located("C2", "validation tau 0.891 vs 0.712", "these aggregate medians and the layout-clustered CI [0.116,0.291] are quoted from CANDIDATE_I003.md; E006_RESULTS.json stores per-cell and per-pair values plus a bootstrap CI [0.0915,0.2049] under a different clustering, not the cited pair")
not_located("C2", "validation CI [0.116,0.291]", "not a stored field; 0.116 and 0.291 do not appear anywhere in E006_RESULTS.json")

# ---------------- C23: GDSC combination-level reliability ----------------
check("C23", "between-unit share 0.304", "r28", "E028_RESULTS.json", ["results", "between_unit_share"], 0.304, 0.002)
check("C23", "permutation null 0.0156", "r28", "E028_RESULTS.json", ["results", "permutation_null", "mean"], 0.0156, 0.001)
check("C23", "split-half 0.904", "r28", "E028_RESULTS.json", ["results", "split_half_reliability", "mean"], 0.904, 0.002)
check("C23", "within-unit sd 0.044", "r28", "E028_RESULTS.json", ["results", "within_unit_sd_median"], 0.044, 0.002)
sh_ci = load("r28", "E028_RESULTS.json")["results"]["split_half_reliability"]["ci95"]
results.append({"claim": "C23", "label": "split-half CI [0.901,0.907]", "episode": "r28",
                "file": "E028_RESULTS.json", "path": "results.split_half_reliability.ci95",
                "expected": [0.901, 0.907], "actual": sh_ci, "tol": 0.002,
                "status": "ok" if abs(sh_ci[0] - 0.901) < 0.002 and abs(sh_ci[1] - 0.907) < 0.002 else "mismatch"})
not_located("C23", "between-unit sd 0.032", "not stored; the JSON keeps the variance SHARE 0.304 and the within-unit sd, but not the between-unit sd itself")

# ---------------- C32 (BATCHIE side): pool size drives the rule ----------------
check("C32", "BATCHIE S=80 -30.9 pp", "r50", "E050_RESULTS.json", ["by_size", "80", "diff"], -0.309, 0.005)
check("C32", "BATCHIE S=320 -25.5 pp", "r50", "E050_RESULTS.json", ["by_size", "320", "diff"], -0.255, 0.005)
check("C32", "BATCHIE S=160 -23.4 pp", "r50", "E050_RESULTS.json", ["by_size", "160", "diff"], -0.234, 0.005)

# ---------------- C37: transfer is one-way ----------------
check("C37", "transfer A holds", "r54", "E054_RESULTS.json",
      ["transfer_A_gdsc_to_batchie", "prediction_holds"], 1.0, 0.5,
      note="boolean stored as JSON true; 1.0 is the coerced value")
n_b = load("r54", "E054_RESULTS.json")["transfer_B_batchie_to_gdsc"]
results.append({"claim": "C37", "label": "transfer B threshold unlearnable", "episode": "r54",
                "file": "E054_RESULTS.json", "path": "transfer_B_batchie_to_gdsc.threshold_learnable",
                "expected": False, "actual": n_b["threshold_learnable"], "tol": 0,
                "status": "ok" if n_b["threshold_learnable"] is False else "mismatch"})

# ---------------- C39: in-place re-estimation at chance ----------------
for q, exp in (("200", 0.5417), ("500", 0.4875), ("1000", 0.5167)):
    check("C39", "q=%s agreement %.4f" % (q, exp), "r59", "E059_RESULTS.json",
          ["by_probe", q, "agreement_eval"], exp, 0.003)
coin = load("r59", "E059_RESULTS.json")["coin_flip_check"]["q500"]
results.append({"claim": "C39", "label": "probe within 1 pp of a coin flip (q=500)", "episode": "r59",
                "file": "E059_RESULTS.json", "path": "coin_flip_check.q500",
                "expected": "observed - expected < 0.01",
                "actual": coin["observed"] - coin["expected_if_random"], "tol": 0.01,
                "status": "ok" if abs(coin["observed"] - coin["expected_if_random"]) < 0.01 else "mismatch"})

n_ok = sum(1 for r in results if r["status"] == "ok")
n_bad = sum(1 for r in results if r["status"] == "mismatch")
n_miss = sum(1 for r in results if r["status"] == "not_located")

res = {"kind": "register_numeric_audit_final_block",
       "n_checks": len(results), "n_ok": n_ok, "n_mismatch": n_bad, "n_not_located": n_miss,
       "claims_covered": sorted(set(r["claim"] for r in results)),
       "checks": results,
       "not_located_reason_class": "report-level or derived values with no stored field",
       "decisions": {"H162_no_wrong_values": n_bad == 0,
                     "H163_locating_complete": n_miss == 0}}
(OUT / "E064_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

for r in results:
    mark = {"ok": "OK  ", "mismatch": "FAIL", "not_located": "N/A "}[r["status"]]
    print("%s %-3s %-42s exp=%s act=%s %s" % (mark, r["claim"], r["label"], r["expected"],
                                              r["actual"], r.get("note", "")))
print("\n%d checks: %d ok, %d mismatch, %d not located" % (len(results), n_ok, n_bad, n_miss))
