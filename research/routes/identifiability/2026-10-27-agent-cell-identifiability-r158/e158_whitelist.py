"""E158: validate the expected_uninformative whitelist, including the case where it hides a real defect.

R157's design flagged every held-out drug's identity column, which is correct about the data and wrong
about the intent. The whitelist fixes that. But intent declarations can themselves be wrong: R138's
masked identity block was also "intentional", and it silently handicapped the tree. This checks both
sides.

Pre-registered by extension of PROTOCOL_E147.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r158"
SEED = 20261060
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xa = oh(A, drugs); Xb = oh(B, drugs)
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    a_names = ["a_%s" % s for s in drugs]
    b_names = ["b_%s" % s for s in drugs]
    p_names = (["ap_%d" % i for i in range(Xp.shape[1] // 2)]
               + ["lp_%d" % i for i in range(Xp.shape[1] // 2)])
    names = a_names + b_names + p_names
    X = np.hstack([Xa, Xb, Xp])

    rng = np.random.default_rng(SEED)
    ds = drugs[:]; rng.shuffle(ds)
    held = set(ds[:10])
    au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
    tr = np.where((~au) & (~bu))[0]
    te = np.where(au & bu)[0]
    held_names = [n for n in names[:len(a_names) + len(b_names)]
                  if n.split("_", 1)[1] in held]

    path_names = p_names
    cases = {}
    # 1. R157-style design, no whitelist. After the R158 fix, held-out identity columns are reported as
    #    ABSENT_LEVEL notes rather than flags, so what remains is the pathway unseen-code fact.
    cases["r157_no_whitelist"] = audit(features=(X[tr], X[te], names))
    # 2. same, with the held-out identity columns declared expected: expect PASS
    cases["r157_with_pathway_whitelisted"] = audit(features=(X[tr], X[te], names),
                                                   expected_uninformative=path_names)
    # 3. R138-style: held-out identity columns masked to the reserved -1 AND whitelisted.
    #    The declaration of intent is the same, but the masked column still enters the model and
    #    still consumes capacity. Expect PASS, which is exactly the danger.
    Xmask = X.copy()
    Xmask[np.ix_(np.arange(len(g)), np.arange(len(a_names) + len(b_names)))] = 0.0
    for j, nm in enumerate(names[:len(a_names) + len(b_names)]):
        pass
    apos = {s: j for j, s in enumerate(drugs)}
    for i in te:
        # R138 masked ONLY the held drug's own column, leaving it at the reserved -1
        if A[i] in held:
            Xmask[i, apos[A[i]]] = -1.0
        if B[i] in held:
            Xmask[i, len(a_names) + apos[B[i]]] = -1.0
    cases["r138_masked_no_whitelist"] = audit(features=(Xmask[tr], Xmask[te], names))
    cases["r138_masked_whitelisted"] = audit(features=(Xmask[tr], Xmask[te], names),
                                             expected_uninformative=held_names + path_names)
    # 4. a prediction-level alarm must survive the whitelist
    cases["prediction_alarm_with_whitelist"] = audit(
        features=(X[tr], X[te], names), expected_uninformative=path_names + held_names,
        preds={"dead": np.zeros(len(te))})
    # 5. a split-level alarm must survive the whitelist
    cases["split_alarm_with_whitelist"] = audit(
        split=(g["key"].to_numpy()[tr], g["key"].to_numpy()[tr][:50]),
        expected_uninformative=path_names + held_names)

    # After the R158 fixes, a one-hot design in which levels are held out is CLEAN: absent levels are
    # notes and indicator columns are exempt from the unseen-code test. So case 1 must pass.
    expected = {"r157_no_whitelist": True, "r157_with_pathway_whitelisted": True,
                "r138_masked_no_whitelist": False, "r138_masked_whitelisted": True,
                "prediction_alarm_with_whitelist": False, "split_alarm_with_whitelist": False}
    results = {}
    print("whitelist validation\n")
    for name, rep in cases.items():
        got = rep["passed"]
        ok = got == expected[name]
        print("[%s] %-34s passed=%-5s expected=%-5s suppressed=%d" % (
            "OK " if ok else "BAD", name, got, expected[name], len(rep["suppressed"])))
        results[name] = {"passed": bool(got), "expected": expected[name], "ok": bool(ok),
                         "flags": rep["flags"], "suppressed": rep["suppressed"]}

    h382 = all(v["ok"] for v in results.values())
    res = {"kind": "validate_the_expected_uninformative_whitelist",
           "input_sha256": sha256(ORIG),
           "settings": {"seed": SEED, "n_held_drugs": len(held), "n_eval": int(len(te))},
           "audit": {"keys": int(len(g))}, "cases": results, "files": {}}
    res["the_danger_it_introduces"] = {
        "case": "r138_masked_whitelisted",
        "what_happens": ("the masked identity block is declared expected, so the audit passes. But that block still enters the model and still consumes splits, "
                         "which is precisely the defect that cost two rounds to find in R147 and R148."),
        "so": "the whitelist buys quiet at the price of trusting the declaration of intent, and intent declarations can be wrong"}
    res["what_still_works"] = {
        "prediction_level": "a constant arm is still flagged with the whitelist in place",
        "split_level": "training and evaluation overlap is still flagged with the whitelist in place",
        "scope": "suppression is confined to feature-level flags on the named columns"}
    res["decisions"] = {"H382_whitelist_behaves_as_designed": bool(h382),
                        "H383_it_over_or_under_suppresses": not h382}
    res["decisions"]["verdict"] = (
        "the_whitelist_suppresses_only_the_declared_features_but_it_can_also_hide_a_real_defect"
        if h382 else "the_whitelist_misbehaves_on_at_least_one_case")
    res["limits"] = ["Intent declarations are the operator's, and they can be wrong.",
                     "Only feature-level flags can be suppressed; that is by design.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r158/PROTOCOL_E147_ext.md",
                "research/2026-10-27-agent-cell-identifiability-r158/e158_whitelist.py",
                "research/tools/feature_audit.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E158_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nH382:", h382)


if __name__ == "__main__":
    main()
