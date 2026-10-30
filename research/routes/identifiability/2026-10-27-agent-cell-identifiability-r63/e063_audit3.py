"""E063: audit the five early claims C1, C3, C4, C5, C6 - the last block of the register audit.

Pre-registered in PROTOCOL_E061.md. Same three-state discipline as R62: every check reports
ok / mismatch / not_located, and only a mismatch counts against the register.
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
E = "2026-10-27-agent-cell-identifiability-"
OUT = R / (E + "r63")
OUT.mkdir(parents=True, exist_ok=True)

CACHE = {}


def load(ep, fn):
    key = (ep, fn)
    if key not in CACHE:
        CACHE[key] = json.load(open(R / (E + ep) / fn, encoding="utf-8"))
    return CACHE[key]


def dig(obj, path):
    cur = obj
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
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
        fval = float(val)
    except (TypeError, ValueError):
        rec.update(status="mismatch", actual=val, note="not numeric")
        results.append(rec)
        return
    rec.update(status="ok" if abs(fval - expected) <= tol else "mismatch", actual=fval)
    results.append(rec)


# ---------------- C1: BJ reversal within noise ----------------
check("C1", "BJ dbar -0.0345", "r4", "E004_RESULTS.json",
      ["tests", "primary_level_matched", "cells", "BJ", "dbar"], -0.0345, 0.001)
check("C1", "BJ t -0.85", "r4", "E004_RESULTS.json",
      ["tests", "primary_level_matched", "cells", "BJ", "t"], -0.85, 0.02)
ci = load("r4", "E004_RESULTS.json")["tests"]["primary_level_matched"]["cells"]["BJ"]["ci95"]
results.append({"claim": "C1", "label": "BJ CI contains 0", "episode": "r4", "file": "E004_RESULTS.json",
                "path": "tests.primary_level_matched.cells.BJ.ci95", "expected": "contains 0",
                "actual": ci, "tol": 0,
                "status": "ok" if (ci[0] < 0 < ci[1]) else "mismatch"})

# ---------------- C3: reversal is real, not the circular null ----------------
check("C3", "valid null cross-cell 0.42%", "r6", "E007C_SHARED_ORDER_NULL.json",
      ["null_cross_cell_reversal_rate", "mean"], 0.0042, 0.0005,
      note="the circular null in E007_RESULTS was renamed _INVALID; the valid one lives here")
check("C3", "observed cross-cell 3.96%", "r6", "E007C_SHARED_ORDER_NULL.json",
      ["observed", "cross_cell"], 0.0396, 0.001)
check("C3", "observed same-cell 0.28%", "r6", "E007C_SHARED_ORDER_NULL.json",
      ["observed", "same_cell"], 0.0028, 0.0005)

# ---------------- C4: reversal clusters by regimen, not by cell pair ----------------
check("C4", "ICC drug pair 0.294", "r6", "E007_RESULTS.json",
      ["by_gap", "0.1", "dispersion_drugpair", "icc_moment"], 0.294, 0.005)
check("C4", "n units 5626", "r6", "E007_RESULTS.json",
      ["by_gap", "0.1", "dispersion_drugpair", "n"], 5626, 0)
check("C4", "ICC cell pair 0.028", "r6", "E007_RESULTS.json",
      ["by_gap", "0.1", "dispersion_cellpair", "icc_moment"], 0.028, 0.003)

# ---------------- C5: drug-pair propensity beats spacing ----------------
check("C5", "pooled AUC 0.869", "r7", "E008B_CHECKS.json",
      ["auc_observed_drugpair"], 0.869, 0.002,
      note="the pooled AUC lives in E008B_CHECKS.json, not in E008_RESULTS.json")
check("C5", "constant AUC 0.500", "r7", "E008_RESULTS.json",
      ["auc", "M0_constant", "weighted_mean"], 0.5, 0.001)
check("C5", "spacing AUC 0.828", "r7", "E008_RESULTS.json",
      ["auc", "M1_spacing", "weighted_mean"], 0.828, 0.002)
check("C5", "beyond spacing +0.095", "r7", "E008_RESULTS.json",
      ["differences", "M3_minus_M1", "weighted_mean"], 0.095, 0.002)
c5ci = load("r7", "E008_RESULTS.json")["differences"]["M3_minus_M1"]["ci95_layout_clustered"]
results.append({"claim": "C5", "label": "beyond spacing CI [0.059,0.126]", "episode": "r7",
                "file": "E008_RESULTS.json", "path": "differences.M3_minus_M1.ci95_layout_clustered",
                "expected": [0.059, 0.126], "actual": c5ci, "tol": 0.003,
                "status": "ok" if abs(c5ci[0] - 0.059) < 0.003 and abs(c5ci[1] - 0.126) < 0.003 else "mismatch"})

# ---------------- C6: acquisition has no decision value ----------------
check("C6", "k=8 instability vs exploit +0.0201", "r8", "E009_RESULTS.json",
      ["paired", "8", "instab_vs_exploit_regret", "mean_diff"], 0.0201, 0.002,
      note="positive here means the contender had HIGHER regret, i.e. was worse")
c6ci = load("r8", "E009_RESULTS.json")["paired"]["8"]["instab_vs_exploit_regret"]["ci95_layout_clustered"]
results.append({"claim": "C6", "label": "k=8 CI contains 0", "episode": "r8", "file": "E009_RESULTS.json",
                "path": "paired.8.instab_vs_exploit_regret.ci95_layout_clustered",
                "expected": "contains 0", "actual": c6ci, "tol": 0,
                "status": "ok" if (c6ci[0] < 0 < c6ci[1]) else "mismatch"})
b8 = load("r8", "E009_RESULTS.json")["by_k"]["8"]
same = (b8["contender"]["regret_mean"] == b8["exploit"]["regret_mean"])
results.append({"claim": "C6", "label": "EI identical to exploitation (diff exactly 0)", "episode": "r8",
                "file": "E009_RESULTS.json", "path": "by_k.8.contender vs exploit regret_mean",
                "expected": "identical", "actual": [b8["contender"]["regret_mean"], b8["exploit"]["regret_mean"]],
                "tol": 0, "status": "ok" if same else "mismatch"})

n_ok = sum(1 for r in results if r["status"] == "ok")
n_bad = sum(1 for r in results if r["status"] == "mismatch")
n_missing = sum(1 for r in results if r["status"] == "not_located")

res = {"kind": "register_numeric_audit_round3_early_claims",
       "n_checks": len(results), "n_ok": n_ok, "n_mismatch": n_bad, "n_not_located": n_missing,
       "claims_covered": sorted(set(r["claim"] for r in results)),
       "checks": results,
       "decisions": {"H160_no_wrong_values": n_bad == 0,
                     "H161_locating_complete": n_missing == 0},
       "register_corrections_needed": n_bad}
(OUT / "E063_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

for r in results:
    mark = {"ok": "OK  ", "mismatch": "FAIL", "not_located": "N/A "}[r["status"]]
    print("%s %-3s %-42s exp=%s act=%s %s" % (mark, r["claim"], r["label"], r["expected"],
                                              r["actual"], r.get("note", "")))
print("\n%d checks: %d ok, %d mismatch, %d not located" % (len(results), n_ok, n_bad, n_missing))
