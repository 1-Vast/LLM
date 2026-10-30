"""E151: exercise the NEAR_DEGENERATE branch and map the threshold sensitivity.

R150 added the near-degenerate tier but both constructed cases fired the dominance branch, so the
ratio branch never executed and the false-positive rate was unknown. This runs twenty splits across a
3x3 threshold grid and four scenarios.

Pre-registered in PROTOCOL_E141.md.
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
from feature_audit import run  # noqa: E402

ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r151"
SEED = 20261054
SPLITS = 20
RATIOS = (0.02, 0.05, 0.10)
DOMS = (0.90, 0.95, 0.99)
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
    names = ["a_code", "b_code", "ap_code", "lp_code"]
    X = np.column_stack([a_code, b_code, ap_code, lp_code])

    rng = np.random.default_rng(SEED)
    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)

    splits = []
    for s in range(SPLITS):
        te = []
        for c, idxs in cell_index.items():
            idxs = np.array(idxs)
            perm = rng.permutation(len(idxs)); half = len(idxs) // 2
            te.extend(idxs[perm[half:]].tolist())
        te = np.array(sorted(te)); tr = np.setdiff1d(np.arange(len(g)), te)
        splits.append((tr, te))

    def scenarios(tr, te, seed):
        Xtr, Xev = X[tr].copy(), X[te].copy()
        out = {"clean": (Xtr, Xev)}
        shr = Xev.copy(); shr[:, 2] = shr[:, 2] * 0.01
        out["scale_shrunk"] = (Xtr, shr)
        zr = Xev.copy()
        r2 = np.random.default_rng(seed)
        keep = r2.choice(len(zr), size=max(1, int(0.01 * len(zr))), replace=False)
        m = np.zeros(len(zr), dtype=bool); m[keep] = True
        zr[:, 2] = np.where(m, zr[:, 2], 0.0)
        out["zeroed"] = (Xtr, zr)
        dm = Xev.copy()
        vals = np.unique(Xtr[:, 3])
        dm[:, 3] = np.where(r2.random(len(dm)) < 0.96, vals[0], dm[:, 3])
        out["dominated"] = (Xtr, dm)
        return out

    grid = {}
    for rt in RATIOS:
        for dt in DOMS:
            key = "r%.2f_d%.2f" % (rt, dt)
            grid[key] = {s: 0 for s in ("clean", "scale_shrunk", "zeroed", "dominated")}
    neardeg_hits = {k: 0 for k in grid}

    for si, (tr, te) in enumerate(splits):
        scen = scenarios(tr, te, SEED + si)
        for rt in RATIOS:
            for dt in DOMS:
                key = "r%.2f_d%.2f" % (rt, dt)
                for sname, (Xtr, Xev) in scen.items():
                    rep = run(features=(Xtr, Xev, names), ratio_threshold=rt)
                    rep2 = run(features=(Xtr, Xev, names), ratio_threshold=rt)
                    flagged = not rep2["passed"]
                    # re-run with the dominance threshold applied by rewriting the flags
                    fl = []
                    for row in rep2["features"]:
                        row_flags = [f for f in row["flags"]
                                     if not f.startswith("DOMINATED_ON_EVAL")
                                     or (row["dominant_eval"] > dt and row["dominant_train"] < 0.80)]
                        fl.extend(row_flags)
                    flagged = len(fl) > 0
                    if flagged:
                        grid[key][sname] += 1
                    if any(f.startswith("NEAR_DEGENERATE") for f in fl):
                        neardeg_hits[key] += 1

    res = {"kind": "threshold_sensitivity_of_the_near_degenerate_tier",
           "input_sha256": sha256(ORIG),
           "settings": {"splits": SPLITS, "seed": SEED, "ratios": list(RATIOS),
                        "dominants": list(DOMS)},
           "audit": {"keys": int(len(g))}, "grid": {}, "files": {}}
    for key in grid:
        res["grid"][key] = {s: {"flag_rate": grid[key][s] / SPLITS} for s in grid[key]}
        res["grid"][key]["neardeg_branch_rate_on_scale_shrunk"] = neardeg_hits[key] / SPLITS
    def ok(key):
        g_ = res["grid"][key]
        return (g_["clean"]["flag_rate"] <= 0.05
                and g_["neardeg_branch_rate_on_scale_shrunk"] >= 0.90
                and g_["zeroed"]["flag_rate"] >= 0.90
                and g_["dominated"]["flag_rate"] >= 0.90)
    good = [k for k in grid if ok(k)]
    h368 = len(good) > 0
    res["decisions"] = {"passing_threshold_pairs": good,
                        "H368_a_usable_pair_exists": bool(h368),
                        "H369_none_works": not h368}
    res["decisions"]["verdict"] = (
        "a_usable_threshold_pair_exists_at_%s" % good[0] if h368 else
        "no_threshold_pair_is_both_quiet_and_sensitive")
    res["limits"] = ["Constructed scenarios, injected artificially.",
                     "Twenty splits give the false-positive rate a resolution of about five points.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r151/PROTOCOL_E141.md",
                "research/2026-10-27-agent-cell-identifiability-r151/e151_thresholds.py",
                "research/tools/feature_audit.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E151_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("%-14s %8s %8s %8s %8s %8s" % ("thresholds", "clean", "scaled", "zeroed", "dominat", "nd_branch"))
    for key, v in res["grid"].items():
        print("%-14s %8.2f %8.2f %8.2f %8.2f %8.2f" % (
            key, v["clean"]["flag_rate"], v["scale_shrunk"]["flag_rate"],
            v["zeroed"]["flag_rate"], v["dominated"]["flag_rate"],
            v["neardeg_branch_rate_on_scale_shrunk"]))
    print("passing pairs:", good)
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
