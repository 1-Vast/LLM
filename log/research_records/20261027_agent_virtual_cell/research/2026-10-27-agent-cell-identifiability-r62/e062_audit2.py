"""E062: audit the register's remaining numeric claims against each round's result JSON.

Pre-registered in PROTOCOL_E060.md. Design lesson from R60/R61: a check can fail because
the PATH is wrong, not because the number is wrong. Every check therefore reports one of
three states - ok / mismatch / not_located - and only mismatch counts against the register.
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
E = "2026-10-27-agent-cell-identifiability-"
OUT = R / (E + "r62")
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


def check(claim, label, ep, fn, path, expected, tol):
    rec = {"claim": claim, "label": label, "episode": ep, "path": ".".join(path),
           "expected": expected, "tol": tol}
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
    ok = abs(fval - expected) <= tol
    rec.update(status="ok" if ok else "mismatch", actual=fval)
    results.append(rec)


# --- C7 optimum dose combination predictable: hit@3 and regret
check("C7", "mean hit@3 0.671", "r11", "E012_RESULTS.json", ["comparators", "mean_surface", "hit_at3"], 0.671, 0.01)
check("C7", "mean regret 0.026", "r11", "E012_RESULTS.json", ["comparators", "mean_surface", "regret_mean"], 0.026, 0.005)
check("C7", "random hit@3 0.044", "r11", "E012_RESULTS.json", ["comparators", "random", "hit_at3"], 0.044, 0.01)

# --- C8 boundary moves
check("C8", "within-cell 0.810", "r11", "E012_RESULTS.json", ["boundary", "mean_within_cell_agreement"], 0.810, 0.005)
check("C8", "cross-cell 0.725", "r11", "E012_RESULTS.json", ["boundary", "mean_cross_cell_agreement"], 0.725, 0.005)
check("C8", "drop 0.086", "r11", "E012_RESULTS.json", ["boundary", "mean_drop"], 0.086, 0.003)

# --- C11 additive vs pooled
check("C11", "additive regret 0.206", "r13", "E014_RESULTS.json", ["comparators", "bliss", "regret_mean"], 0.206, 0.005)
check("C11", "additive+interaction rmse 0.135", "r13", "E014_RESULTS.json", ["comparators", "bliss_other", "rmse_mean"], 0.135, 0.005)

# --- C12 interaction residual conserved
check("C12", "validation rho 0.353", "r13", "E014_RESULTS.json", ["interaction_conservation", "mean_interaction_rho_cross_cell"], 0.353, 0.01)
check("C12", "high-diversity rho 0.596", "r24", "E024_RESULTS.json", ["residual_conservation", "mean"], 0.596, 0.005)

# --- C14 conformal coverage
check("C14", "alpha 0.20 empirical 0.800", "r16", "E016_RESULTS.json", ["coverage", "0.2", "empirical"], 0.800, 0.01)
check("C14", "alpha 0.10 empirical 0.900", "r16", "E016_RESULTS.json", ["coverage", "0.1", "empirical"], 0.900, 0.01)

check("C12", "high-diversity 25/25 positive", "r24", "E024_RESULTS.json", ["residual_conservation", "frac_positive"], 1.0, 0.001)
# the register's "bound" is the MEDIAN of the per-layout conformal quantiles (derived, not stored)
def derived_q(alpha, expected, tol):
    rec = {"claim": "C14", "label": "alpha %s median quantile %.4f" % (alpha, expected),
           "episode": "r16", "path": "median(coverage[%s].per_layout[*].q)" % alpha,
           "expected": expected, "tol": tol, "derived": True}
    try:
        pl = load("r16", "E016_RESULTS.json")["coverage"][alpha]["per_layout"]
        qs = sorted(v["q"] for v in pl.values())
        med = qs[len(qs) // 2] if len(qs) % 2 else 0.5 * (qs[len(qs) // 2 - 1] + qs[len(qs) // 2])
    except (KeyError, FileNotFoundError) as exc:
        rec.update(status="not_located", actual=None, note=str(exc)[:120])
        results.append(rec)
        return
    rec.update(status="ok" if abs(med - expected) <= tol else "mismatch", actual=med)
    results.append(rec)


derived_q("0.2", 0.0342, 0.002)
derived_q("0.1", 0.0760, 0.002)

# --- C17 cross-plate reproduction
check("C17", "cross-plate median 0.851", "r21", "E021_RESULTS.json", ["summary", "cross_plate", "median"], 0.851, 0.005)
check("C17", "difference +0.147", "r21", "E021_RESULTS.json", ["cross_plate_minus_cross_cell", "mean"], 0.147, 0.005)

# --- C18 pooling ceiling
check("C18", "pooling precision@10 0.333", "r22", "E022_RESULTS.json", ["by_m", "0", "mean_precision10"], 0.333, 0.005)

# --- C19 unseen combination
check("C19", "additive loo median 0.941", "r23", "E023_RESULTS.json", ["additive_loo", "median"], 0.941, 0.005)
check("C19", "precision@10 0.225", "r23", "E023_RESULTS.json", ["additive_precision10", "mean"], 0.225, 0.005)

# --- C20 D-optimal
check("C20", "dopt 0.161", "r25", "E025_RESULTS.json", ["by_m", "5", "dopt", "mean"], 0.161, 0.005)
check("C20", "random 0.086", "r25", "E025_RESULTS.json", ["by_m", "5", "random", "mean"], 0.086, 0.005)

# --- C21 variance decomposition
check("C21", "LOO main share median 0.696", "r26", "E026_RESULTS.json", ["main_share_loo", "median"], 0.696, 0.005)
check("C21", "in-sample 0.725", "r26", "E026_RESULTS.json", ["main_share_insample", "median"], 0.725, 0.005)
check("C21", "residual 0.275", "r26", "E026_RESULTS.json", ["resid_share", "median"], 0.275, 0.005)

# --- C30 program search gain
check("C30", "R35 eval +3.6 pp", "r35", "E035_RESULTS.json", ["eval", "searched_program", "mean_diff"], 0.036, 0.003)
check("C30", "R35 eval 12.80%", "r35", "E035_RESULTS.json", ["eval", "searched_program", "a"], 0.128, 0.003)

n_ok = sum(1 for r in results if r["status"] == "ok")
n_bad = sum(1 for r in results if r["status"] == "mismatch")
n_missing = sum(1 for r in results if r["status"] == "not_located")

res = {"kind": "register_numeric_audit_round2",
       "n_checks": len(results), "n_ok": n_ok, "n_mismatch": n_bad, "n_not_located": n_missing,
       "claims_covered": sorted(set(r["claim"] for r in results)),
       "checks": results}
(OUT / "E062_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

for r in results:
    mark = {"ok": "OK  ", "mismatch": "FAIL", "not_located": "N/A "}[r["status"]]
    print("%s %-4s %-30s exp=%s act=%s %s" % (
        mark, r["claim"], r["label"], r["expected"], r["actual"],
        r.get("note", "")))
print("\n%d checks: %d ok, %d mismatch, %d not located" % (len(results), n_ok, n_bad, n_missing))
