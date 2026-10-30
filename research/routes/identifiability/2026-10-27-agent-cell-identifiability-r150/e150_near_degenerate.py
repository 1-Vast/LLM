"""E150: validate the near-degenerate tier.

R149's audit used exact criteria. This adds NEAR_DEGENERATE (evaluation dispersion a small fraction of
training dispersion) and DOMINATED_ON_EVAL (one level dominating on evaluation but not in training),
then checks that the new tier fires where it should and does not fire on the clean design.

Pre-registered in PROTOCOL_E140.md.
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
from feature_audit import run, show  # noqa: E402

ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r150"
SEED = 20261053
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
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B))
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(float)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(float)
    ap_code = pd.Categorical(g["ap"]).codes.astype(float)
    lp_code = pd.Categorical(g["lp"]).codes.astype(float)
    rng = np.random.default_rng(SEED)
    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)
    te = []
    for c, idxs in cell_index.items():
        idxs = np.array(idxs); perm = rng.permutation(len(idxs)); half = len(idxs) // 2
        te.extend(idxs[perm[half:]].tolist())
    te = np.array(sorted(te)); tr = np.setdiff1d(np.arange(len(g)), te)

    base_tr = np.column_stack([a_code, b_code, ap_code, lp_code])[tr]
    base_ev = np.column_stack([a_code, b_code, ap_code, lp_code])[te]
    names = ["a_code", "b_code", "ap_code", "lp_code"]

    cases = {}
    # 1. clean design
    cases["clean_design"] = run(features=(base_tr, base_ev, names))

    # 2. dead code (R138 reproduction): identity forced to the reserved -1
    ev_dead = base_ev.copy(); ev_dead[:, 0] = -1.0; ev_dead[:, 1] = -1.0
    cases["dead_code"] = run(features=(base_tr, ev_dead, names))

    # 3. near degenerate: a pathway column almost entirely zero on evaluation
    tr_nd = base_tr.copy(); ev_nd = base_ev.copy()
    col = ev_nd[:, 2]
    keep = rng.choice(len(col), size=max(1, int(0.01 * len(col))), replace=False)
    mask = np.zeros(len(col), dtype=bool); mask[keep] = True
    ev_nd[:, 2] = np.where(mask, col, 0.0)
    cases["near_degenerate"] = run(features=(tr_nd, ev_nd, names))

    # 4. dominated on evaluation: 96 percent one value, 60 percent in training
    tr_dm = base_tr.copy(); ev_dm = base_ev.copy()
    vals = np.unique(tr_dm[:, 3])
    tr_dm[:, 3] = np.where(rng.random(len(tr_dm)) < 0.60, vals[0], tr_dm[:, 3])
    ev_dm[:, 3] = np.where(rng.random(len(ev_dm)) < 0.96, vals[0], ev_dm[:, 3])
    cases["dominated"] = run(features=(tr_dm, ev_dm, names))

    expected = {"clean_design": True, "dead_code": False,
                "near_degenerate": False, "dominated": False}
    results = {}
    print("near-degenerate tier validation\n")
    for name, rep in cases.items():
        passed = show(name, rep)
        results[name] = {"passed": passed, "expected": expected[name], "flags": rep["flags"]}
    h366 = all(v["passed"] == v["expected"] for v in results.values())
    print("\nH366 all four match expectation:", h366)
    new_tier_flags = []
    for name in ("near_degenerate", "dominated"):
        for f in results[name]["flags"]:
            if "NEAR_DEGENERATE" in f or "DOMINATED_ON_EVAL" in f:
                new_tier_flags.append("%s -> %s" % (name, f))
    res = {"kind": "validate_the_near_degenerate_tier",
           "input_sha256": sha256(ORIG),
           "settings": {"seed": SEED, "ratio_threshold": 0.05,
                        "dominant_threshold": 0.95, "dominant_train_below": 0.80},
           "audit": {"keys": int(len(g)), "rows": len(te)},
           "cases": results, "new_tier_flags": new_tier_flags,
           "decisions": {"H366_new_tier_works_without_false_positives": bool(h366),
                         "H367_false_positive_or_miss": not h366},
           "decisions_verdict": ("the_near_degenerate_tier_fires_where_expected_and_leaves_the_clean_design_untouched"
                                 if h366 else "the_new_tier_misjudges_at_least_one_case"),
           "limits": ["The two constructed cases are artificially injected and do not correspond to a real design seen here.",
                     "The 0.05 and 0.95 thresholds are chosen, not optimised; this round only shows they do not false-positive on the clean design.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r150/PROTOCOL_E140.md",
                "research/2026-10-27-agent-cell-identifiability-r150/e150_near_degenerate.py",
                "research/tools/feature_audit.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E150_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nnew-tier flags raised:")
    for f in new_tier_flags:
        print("   ", f)
    print("written E150_RESULTS.json")


if __name__ == "__main__":
    main()
