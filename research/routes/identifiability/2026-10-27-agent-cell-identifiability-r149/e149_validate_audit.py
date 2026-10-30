"""E149: does the pre-flight audit catch the five historical failures?

Rebuilds the circumstances of each past failure from the real data and runs the audit from
research/tools/feature_audit.py against them, then runs it against the clean R148 design.

Pre-registered in PROTOCOL_E139.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r149"
SEED = 20261052
HOLDOUT = 0.20
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
    keys = g["key"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(float)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(float)
    ap_code = pd.Categorical(g["ap"]).codes.astype(float)
    lp_code = pd.Categorical(g["lp"]).codes.astype(float)
    rng = np.random.default_rng(SEED)

    # a single drug holdout shared by the cases that need one
    ds = drugs[:]; rng.shuffle(ds)
    held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
    au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
    te_both = np.where(au & bu)[0]
    tr_clean = np.where((~au) & (~bu))[0]
    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)
    te_key = []
    for c, idxs in cell_index.items():
        idxs = np.array(idxs); perm = rng.permutation(len(idxs)); half = len(idxs) // 2
        te_key.extend(idxs[perm[half:]].tolist())
    te_key = np.array(sorted(te_key)); tr_key = np.setdiff1d(np.arange(len(g)), te_key)

    cases = {}

    # 1. R147 attempt 1: integer drug identity codes for held-out drugs
    Xtr = np.column_stack([a_code, b_code, ap_code, lp_code])[tr_clean]
    Xev = np.column_stack([a_code, b_code, ap_code, lp_code])[te_both]
    cases["r147_attempt1"] = run(features=(Xtr, Xev, ["a_code", "b_code", "ap_code", "lp_code"]))

    # 2. R138/R139 no_identity: identity codes forced to the reserved -1
    Xtr2 = np.column_stack([a_code, b_code, ap_code, lp_code])[tr_clean]
    Xev2 = np.column_stack([np.where(au, -1.0, a_code), np.where(bu, -1.0, b_code),
                            ap_code, lp_code])[te_both]
    cases["r138_no_identity"] = run(features=(Xtr2, Xev2, ["a_code", "b_code", "ap_code", "lp_code"]))

    # 3. R144 marginal arm: two-way additive means, constant when both drugs are unseen
    grand = float(g["emax"].to_numpy()[tr_clean].mean())
    acc = {}
    for i in tr_clean:
        acc.setdefault(A[i], []).append(g["emax"].to_numpy()[i])
        acc.setdefault(B[i], []).append(g["emax"].to_numpy()[i])
    meff = {k: float(np.mean(v)) - grand for k, v in acc.items()}
    marg = np.array([meff.get(A[i], 0.0) + meff.get(B[i], 0.0) + grand for i in te_both])
    cases["r144_marginal"] = run(preds={"marginal": marg, "informative": ap_code[te_both]})

    # 4. R135 one_seen_only: pool defined as a subset of the training rows
    tr_set = set(tr_key.tolist())
    pool = np.array([i for i in tr_key[:2000]])
    cases["r135_one_seen_only"] = run(split=(keys[tr_key], keys[pool]))

    # 5. R148 clean design: key-level holdout, all drugs seen
    Xtr5 = np.column_stack([a_code, b_code, ap_code, lp_code])[tr_key]
    Xev5 = np.column_stack([a_code, b_code, ap_code, lp_code])[te_key]
    cases["r148_clean"] = run(features=(Xtr5, Xev5, ["a_code", "b_code", "ap_code", "lp_code"]),
                               split=(keys[tr_key], keys[te_key]))

    expected = {"r147_attempt1": False, "r138_no_identity": False, "r144_marginal": False,
                "r135_one_seen_only": False, "r148_clean": True}
    results = {}
    print("pre-flight audit against five historical configurations\n")
    for name, rep in cases.items():
        passed = show(name, rep)
        results[name] = {"passed": passed, "expected": expected[name], "flags": rep["flags"]}
    h364 = all(v["passed"] == v["expected"] for v in results.values())
    print()
    print("H364 all five match expectation:", h364)

    res = {"kind": "validate_the_preflight_audit_against_historical_failures",
           "input_sha256": sha256(ORIG),
           "settings": {"seed": SEED, "holdout": HOLDOUT},
           "audit": {"keys": int(len(g)), "tool": "research/tools/feature_audit.py"},
           "cases": results,
           "decisions": {"H364_audit_catches_all": bool(h364), "H365_some_missed": not h364},
           "decisions_verdict": ("the_audit_reproduces_all_five_historical_failures_and_passes_the_clean_design"
                                 if h364 else "the_audit_misses_at_least_one_historical_case"),
           "limits": ["The audit is necessary, not sufficient: passing does not make a design correct.",
                     "It handles the shapes this programme uses (integer codes, key sets, prediction arrays).",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r149/PROTOCOL_E139.md",
                "research/2026-10-27-agent-cell-identifiability-r149/e149_validate_audit.py",
                "research/tools/feature_audit.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E149_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nwritten E149_RESULTS.json")


if __name__ == "__main__":
    main()
