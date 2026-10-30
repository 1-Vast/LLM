"""E130: per-pool correlation between the two criteria.

R128 measured 0.83 over the whole dataset and that became a global reading rule. A small pool with
a different base rate might carry more independent information, in which case the rule must be
refined per pool.

Pre-registered in PROTOCOL_E121.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r130"
HOLDOUT = 0.20
SEED = 20261034
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "Synergy", "SYNERGY_DELTA_EMAX"]


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
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        syn=("syn", "mean"), emax=("emax", "mean"))
    g["syn"] = g["syn"] > 0.5
    g = g[np.isfinite(g["emax"])].copy()
    g["emax_hi"] = g["emax"] >= np.quantile(g["emax"], 0.75)

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    rng = np.random.default_rng(SEED)
    ds = drugs[:]; rng.shuffle(ds); cs = cells[:]; rng.shuffle(cs)
    heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
    heldc = set(cs[: max(3, int(round(HOLDOUT * len(cs))))])
    au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
    cu = np.array([c in heldc for c in CELL])

    pools = {"all": np.ones(len(g), bool),
             "one_unseen": (au ^ bu) & (~cu),
             "cell_unseen": cu & (au | bu),
             "both_seen_cell": au & bu & (~cu),
             "both_unseen_cell": au & bu & cu}

    res = {"kind": "per_pool_correlation_between_the_two_criteria",
           "input_sha256": sha256(ORIG),
           "settings": {"holdout": HOLDOUT, "seed": SEED},
           "audit": {"keys": int(len(g))}, "by_pool": {}, "files": {}}
    global_rho = None
    for name, mask in pools.items():
        sub = g[mask]
        if len(sub) < 50:
            continue
        r_raw = float(spearmanr(sub["syn"].astype(float), sub["emax"]).statistic)
        r_bin = float(spearmanr(sub["syn"].astype(float), sub["emax_hi"].astype(float)).statistic)
        inter = int(((sub["syn"]) & (sub["emax_hi"])).sum())
        union = int(((sub["syn"]) | (sub["emax_hi"])).sum())
        res["by_pool"][name] = {
            "n": int(len(sub)),
            "synergy_rate": float(sub["syn"].mean()),
            "emax_quartile_rate": float(sub["emax_hi"].mean()),
            "rho_flag_vs_raw_emax": r_raw,
            "rho_flag_vs_quartile": r_bin,
            "jaccard": float(inter / union) if union else None,
            "both_positive": inter}
        if name == "all":
            global_rho = r_raw

    small = res["by_pool"].get("both_unseen_cell") or res["by_pool"].get("both_seen_cell")
    rhos = {k: v["rho_flag_vs_raw_emax"] for k, v in res["by_pool"].items() if k != "all"}
    h325 = bool(small and global_rho is not None
                and abs(global_rho) - abs(small["rho_flag_vs_raw_emax"]) > 0.15)
    h326 = bool(rhos and all(abs(v) >= 0.70 for v in rhos.values()))
    res["decisions"] = {"global_rho": global_rho,
                        "small_pool_rho": small["rho_flag_vs_raw_emax"] if small else None,
                        "H325_small_pool_lower": h325,
                        "H326_all_pools_high": h326}
    res["decisions"]["verdict"] = (
        "rule_needs_per_pool_refinement" if h325 else
        "rule_holds_globally" if h326 else
        "mixed")
    res["limits"] = ["Pool masks are key-level and keys are not independent within a cell or a drug.",
                     "Covers only this resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r130/PROTOCOL_E121.md",
                "research/2026-10-27-agent-cell-identifiability-r130/e130_perpool.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E130_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("keys=%d" % len(g))
    for name, e in res["by_pool"].items():
        print("  %-18s n=%6d  syn=%.4f  emaxQ=%.4f  rho(raw)=%+.3f  rho(Q)=%+.3f  Jaccard=%.3f" % (
            name, e["n"], e["synergy_rate"], e["emax_quartile_rate"],
            e["rho_flag_vs_raw_emax"], e["rho_flag_vs_quartile"],
            e["jaccard"] if e["jaccard"] is not None else float("nan")))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
