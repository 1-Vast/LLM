"""E159: validate the continuous-column sentinel check, the last known blind spot in the audit.

R158 caught sentinels only in indicator columns. A concentration column with 3 percent of values filled
as -999, or with zeros among otherwise positive values, went unseen. This adds an extreme-value spike
detector and checks that it fires on those two shapes while NOT firing on a legitimately capped feature.

Pre-registered in PROTOCOL_E148.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
sys.path.insert(0, str(ROOT / "research" / "tools"))
from feature_audit import run as audit  # noqa: E402

ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r159"
SEED = 20261061
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    # realistic continuous columns: log-normal concentrations
    n_tr, n_ev = 400, 200
    def conc(n):
        return np.exp(rng.normal(-8.0, 1.2, size=n))
    tr = np.column_stack([conc(n_tr), conc(n_tr)])
    ev = np.column_stack([conc(n_ev), conc(n_ev)])
    names = ["conc_a", "conc_b"]

    cases = {}
    cases["clean_continuous"] = audit(features=(tr, ev, names))

    m1 = ev.copy(); idx = rng.choice(n_ev, size=int(0.03 * n_ev), replace=False); m1[idx, 0] = -999.0
    cases["minus999"] = audit(features=(tr, m1, names))

    m2 = ev.copy(); idx = rng.choice(n_ev, size=int(0.03 * n_ev), replace=False); m2[idx, 1] = 0.0
    cases["zero_fill"] = audit(features=(tr, m2, names))

    # legitimately capped: the top 3 percent of one column share the same ceiling value
    capped_tr = tr.copy(); capped_ev = ev.copy()
    thr_tr = np.quantile(capped_tr[:, 0], 0.97); thr_ev = np.quantile(capped_ev[:, 0], 0.97)
    capped_tr[capped_tr[:, 0] > thr_tr, 0] = thr_tr
    capped_ev[capped_ev[:, 0] > thr_ev, 0] = thr_ev
    cases["legit_capped"] = audit(features=(capped_tr, capped_ev, names))

    # the R158 clean one-hot design, to confirm no regression
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["key"] = (d["CELL_LINE_NAME"].astype(str) + "|" + d["ANCHOR_NAME"].astype(str)
                + " + " + d["LIBRARY_NAME"].astype(str))
    g = d.groupby("key", as_index=False).agg(a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
                                             emax=("emax", "mean"))
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)
    A = g["a"].astype(str).to_numpy(); B = g["b"].astype(str).to_numpy()
    drugs = sorted(set(A) | set(B))
    def oh(vals, levels):
        ix = {v: i for i, v in enumerate(levels)}
        M = np.zeros((len(vals), len(levels)))
        for t, v in enumerate(vals):
            M[t, ix[v]] = 1.0
        return M
    X = np.hstack([oh(A, drugs), oh(B, drugs)])
    nm = ["a_%s" % s for s in drugs] + ["b_%s" % s for s in drugs]
    ds = drugs[:]; rng.shuffle(ds)
    held = set(ds[:10])
    au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
    trr = np.where((~au) & (~bu))[0]; tee = np.where(au & bu)[0]
    cases["clean_onehot_design"] = audit(features=(X[trr], X[tee], nm))

    expected = {"clean_continuous": True, "minus999": False, "zero_fill": False,
                "legit_capped": True, "clean_onehot_design": True}
    results = {}
    print("continuous sentinel validation\n")
    for name, rep in cases.items():
        got = rep["passed"]
        ok = got == expected[name]
        flagged = [f for f in rep["flags"] if "SENTINEL_SPIKE" in f]
        print("[%s] %-22s passed=%-5s expected=%-5s %s" % (
            "OK " if ok else "BAD", name, got, expected[name], flagged[:1]))
        results[name] = {"passed": bool(got), "expected": expected[name], "ok": bool(ok),
                         "flags": rep["flags"]}

    h384 = all(v["ok"] for v in results.values())
    res = {"kind": "validate_the_continuous_column_sentinel_check",
           "input_sha256": sha256(ORIG),
           "settings": {"seed": SEED, "min_frac": 0.02, "off_scale_factor": 100.0},
           "audit": {"keys": int(len(g))}, "cases": results, "files": {}}
    res["what_it_targets"] = {
        "targets": "a value that recurs on at least 2 percent of rows, lies outside the range of the remaining values, and is more than 100 times off-scale relative to the column median",
        "does_not_target": "a sentinel in the middle of a distribution, such as a missing value filled with the mean, which is numerically indistinguishable from a real value",
        "the_third_condition": "is what protects a legitimately capped feature, which sits at a few times the median rather than a hundred",
        "an_earlier_version_that_failed": "an absolute-gap version missed a zero fill among log-normal concentrations, because the fill sits only micro-units below the minimum"}
    res["decisions"] = {"H384_check_works_without_false_positives": bool(h384),
                        "H385_false_positive_or_miss": not h384}
    res["decisions"]["verdict"] = (
        "the_continuous_sentinel_check_fires_where_it_should_and_spares_a_capped_feature"
        if h384 else "the_continuous_sentinel_check_misjudges_at_least_one_case")
    res["status_of_the_tool"] = ("with this, the known blind spots recorded since R149 are closed and feature_audit is in a handover-able state"
                                 if h384 else "one case still misjudged")
    res["limits"] = ["The 2 percent and hundredfold thresholds are chosen, not optimised.",
                     "Only extreme-value sentinels are covered; mid-distribution ones are not detectable in principle.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r159/PROTOCOL_E148.md",
                "research/2026-10-27-agent-cell-identifiability-r159/e159_sentinel.py",
                "research/tools/feature_audit.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E159_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nH384:", h384)


if __name__ == "__main__":
    main()
