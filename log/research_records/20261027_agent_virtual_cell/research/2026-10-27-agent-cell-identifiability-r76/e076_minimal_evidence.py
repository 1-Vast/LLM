"""E076: how many measurements does a NEW cell need before its own data beats plain drug
marginals? The marginal predictor is the baseline established by R70-R75.

Pre-registered in PROTOCOL_E073.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r76"
METRIC = "SYNERGY_DELTA_AUC"
K = 20
MS = (10, 25, 50, 100, 200, 400)
REPEATS = 20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)
    A = d["a"].to_numpy()
    B = d["b"].to_numpy()
    CELL = d["cell"].to_numpy()
    cells = sorted(set(CELL))

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        order = rng.permutation(len(cells))
        for ci in order:
            c = cells[ci]
            po = np.where(CELL == c)[0]
            tr = np.where(CELL != c)[0]
            if len(po) < 600 or len(tr) < 50000:
                continue
            # drug marginals from training cells only
            grand = float(y[tr].mean())
            dm = {}
            for i, yy in zip(tr, y[tr]):
                dm.setdefault(A[i], []).append(yy)
                dm.setdefault(B[i], []).append(yy)
            deff = {g: float(np.mean(v)) - grand for g, v in dm.items()}
            base_score = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) + grand for i in po])
            perm = rng.permutation(len(po))
            for m in MS:
                if m >= len(po) // 2:
                    continue
                meas = po[perm[:m]]
                rest = po[perm[m:]]
                # cell-specific drug residuals estimated from the measured m
                res = {}
                for i in meas:
                    r = y[i] - 0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) - grand
                    res.setdefault(A[i], []).append(r)
                    res.setdefault(B[i], []).append(r)
                reff = {g: float(np.mean(v)) for g, v in res.items()}
                sc_rest = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) + grand for i in rest])
                sc_rest2 = np.array([
                    0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) +
                    0.5 * (reff.get(A[i], 0.0) + reff.get(B[i], 0.0)) + grand for i in rest])
                b0 = float(syn[rest][np.argsort(-sc_rest)[:K]].mean())
                bm = float(syn[rest][np.argsort(-sc_rest2)[:K]].mean())
                rows.append({"rep": rep, "cell": c, "m": m, "B0": b0, "Bm": bm,
                             "n_rest": int(len(rest)), "base": float(syn[rest].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "minimal_personal_evidence_against_the_marginal_baseline",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"k": K, "ms": list(MS), "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "cells": len(cells),
                     "cells_scored": int(r["cell"].nunique()) if len(r) else 0},
           "by_m": {}, "files": {}}

    for m in MS:
        sub = r[r.m == m]
        if not len(sub):
            continue
        ent = {"n": int(len(sub)), "B0": float(sub["B0"].mean()), "Bm": float(sub["Bm"].mean()),
               "base": float(sub["base"].mean()),
               "gain_pp": float((sub["Bm"] - sub["B0"]).mean()),
               "paired": paired(sub["Bm"], sub["B0"], 10001 + m)}
        # split by cell for a robustness check
        ent["frac_cells_improved"] = float((sub.groupby("cell").apply(
            lambda g: g["Bm"].mean() > g["B0"].mean())).mean())
        res["by_m"][str(m)] = ent

    gains = {m: res["by_m"][str(m)]["gain_pp"] for m in MS if str(m) in res["by_m"]}
    first_sig = None
    for m in MS:
        e = res["by_m"].get(str(m))
        if e and e["paired"] and e["paired"]["ci95"][0] > 0:
            first_sig = m
            break
    mono = all(gains[MS[i]] <= gains[MS[i + 1]] + 0.005 for i in range(len(MS) - 1) if MS[i] in gains and MS[i + 1] in gains)
    res["decisions"] = {"H192_threshold_exists": first_sig is not None,
                        "H193_threshold_small": (first_sig is not None and first_sig <= 50),
                        "first_significant_m": first_sig,
                        "roughly_monotone": mono}
    res["decisions"]["verdict"] = ("own_data_beats_marginals_beyond_a_small_threshold" if first_sig and first_sig <= 50 else
                                   "own_data_beats_marginals_only_at_large_m" if first_sig else
                                   "own_data_never_beats_marginals")
    res["limits"] = [
        "Drug marginals come from the training cells only; the held-out cell contributes nothing to the baseline.",
        "The personal arm re-estimates drug residuals from the m measured rows, so its advantage grows with m by construction.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r76/PROTOCOL_E073.md",
                "research/2026-10-27-agent-cell-identifiability-r76/e076_minimal_evidence.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E076_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E076_rows.csv", index=False)

    print("keys=%d cells=%d scored=%d" % (len(d), len(cells), res["audit"]["cells_scored"]))
    for m in MS:
        e = res["by_m"].get(str(m))
        if not e:
            continue
        c = e["paired"]
        print("  m=%-4d B0=%.4f Bm=%.4f | gain %+.4f [%+.4f,%+.4f] | cells improved %.2f n=%d" % (
            m, e["B0"], e["Bm"], e["gain_pp"], c["ci95"][0], c["ci95"][1],
            e["frac_cells_improved"], e["n"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
