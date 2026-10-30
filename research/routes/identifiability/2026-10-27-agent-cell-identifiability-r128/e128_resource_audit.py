"""E128: resource-capability audit of the four things the objective says to verify first.

Drug-by-cell cross, target engagement, independent functional endpoints, and replication have all
been treated as established premises across rounds without ever being quantified. This measures
them.

Pre-registered in PROTOCOL_E120.md.
"""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
GDSC = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
PAIR = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r128"
METRICS = ["SYNERGY_DELTA_AUC", "SYNERGY_DELTA_EMAX", "SYNERGY_DELTA_fAUC", "SYNERGY_DELTA_XMID"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"kind": "resource_capability_audit", "files": {}}

    # ---------- 1. drug by cell cross ----------
    use = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
           "ANCHOR_TARGET", "LIBRARY_TARGET"] + METRICS
    d = pd.read_csv(GDSC, low_memory=False, usecols=use)
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), combo=("combo", "first"),
        tissue=("Tissue", "first"), **{m: (m, "mean") for m in METRICS})
    n_cells = g["cell"].nunique(); n_combos = g["combo"].nunique(); n_keys = len(g)
    full = n_cells * n_combos
    per_cell = g.groupby("cell")["combo"].nunique()
    per_combo = g.groupby("combo")["cell"].nunique()
    res["cross"] = {
        "cells": int(n_cells), "combos": int(n_combos), "observed_keys": int(n_keys),
        "full_cross": int(full), "coverage": float(n_keys / full),
        "keys_per_cell": {"min": int(per_cell.min()), "median": float(per_cell.median()),
                          "max": int(per_cell.max()), "sd": float(per_cell.std(ddof=1))},
        "cells_per_combo": {"min": int(per_combo.min()), "median": float(per_combo.median()),
                            "max": int(per_combo.max())},
        "keys_per_tissue": {str(k): int(v) for k, v in g.groupby("tissue").size().items()}}

    # ---------- 2. target annotation inventory ----------
    res["targets"] = {
        "anchor_target_levels": int(d["ANCHOR_TARGET"].astype(str).nunique()),
        "library_target_levels": int(d["LIBRARY_TARGET"].astype(str).nunique()),
        "interpretation": "annotation only; no binding, occupancy or engagement measurement exists in this file"}

    # ---------- 4. are the four synergy metrics independent? ----------
    M = g[METRICS].apply(pd.to_numeric, errors="coerce")
    ok = M.notna().all(axis=1)
    Mm = M[ok]
    rhos = {}
    for a, b in combinations(METRICS, 2):
        r = spearmanr(Mm[a], Mm[b], nan_policy="omit").statistic
        rhos[f"{a} vs {b}"] = float(r)
    vals = np.array([abs(v) for v in rhos.values()])
    res["metric_independence"] = {
        "n": int(ok.sum()), "spearman": rhos,
        "abs_median": float(np.median(vals)), "abs_min": float(vals.min()), "abs_max": float(vals.max())}

    # ---------- 5. replication in BATCHIE ----------
    p = pd.read_csv(PAIR, low_memory=False)
    p.columns = [c.strip() for c in p.columns]
    for c in ("Drug 1", "Drug 2", "Cell line", "file"):
        p[c] = p[c].astype(str).str.strip()
    p["anchor"] = p["Drug 1"].isin({"high control", "low control"}) | p["Drug 2"].isin({"high control", "low control"})
    q = p[~p["anchor"]].copy()
    # layout = the (well, drug1, drug2) signature of a plate, as in R118
    layout = {}
    for fname, sub in q.groupby("file", sort=True):
        sig = tuple(sorted(zip(sub["Well"], sub["Drug 1"], sub["Drug 2"])))
        layout[fname] = hashlib.sha1(repr(sig).encode()).hexdigest()
    q["layout"] = q["file"].map(layout)
    q["pairkey"] = q["Drug 1"] + "|" + q["Drug 2"]
    q["cellpair"] = q["pairkey"] + "@" + q["Cell line"]
    per_cellpair = q.groupby("cellpair")["layout"].nunique()
    res["replication"] = {
        "layouts": int(q["layout"].nunique()),
        "cellpair_observations": int(len(per_cellpair)),
        "measured_in_more_than_one_layout": int((per_cellpair > 1).sum()),
        "frac_replicated": float((per_cellpair > 1).mean()),
        "max_layouts_per_cellpair": int(per_cellpair.max())}

    # ---------- decisions ----------
    h318 = res["cross"]["coverage"] < 0.20
    h319 = res["metric_independence"]["abs_median"] > 0.60
    h320 = res["replication"]["frac_replicated"] < 0.30
    res["decisions"] = {"H318_cross_is_sparse": bool(h318), "H319_metrics_not_independent": bool(h319),
                        "H320_replication_low": bool(h320)}
    res["consequences"] = {
        "cross": ("the drug-by-cell design is a subset, not a full cross, so any cell-level or drug-level claim inherits the sampling pattern. "
                  "This must be stated wherever results are aggregated across cells." if h318 else
                  "the cross is dense enough that the sampling pattern is not a first-order concern."),
        "metrics": ("the four synergy metrics move together, so they are four scalings of one functional readout rather than four independent endpoints. "
                    "The objective's request for independent functional endpoints is therefore unmet by this resource." if h319 else
                    "the metrics carry enough independent variation to be treated as distinct readouts."),
        "replication": ("technical replication is the exception rather than the rule, so reproducibility claims can only be made for the minority of "
                        "cell-pair combinations that appear on more than one plate." if h320 else
                        "technical replication is common enough to support reproducibility checks.")}
    res["what_this_resource_cannot_support"] = {
        "independent_functional_endpoints": "all four metrics derive from one viability matrix",
        "target_engagement": "annotation only, no occupancy measurement",
        "genetic_perturbation_reference": "no CRISPR or RNAi data on this machine",
        "true_replication": "one primary screen for GDSC; BATCHIE offers only plate-level technical repeats"}
    res["limits"] = ["Covers only the two resources on this machine.",
                     "Coverage structure is examined at tissue and combo level only.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r128/PROTOCOL_E120.md",
                "research/2026-10-27-agent-cell-identifiability-r128/e128_resource_audit.py"):
        fp = ROOT / rel
        if fp.exists():
            res["files"][rel] = sha256(fp)
    (OUT / "E128_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("cross: cells=%d combos=%d keys=%d full=%d coverage=%.4f" % (
        n_cells, n_combos, n_keys, full, res["cross"]["coverage"]))
    print("  keys/cell min/med/max = %d/%.0f/%d ; cells/combo min/med/max = %d/%.0f/%d" % (
        per_cell.min(), per_cell.median(), per_cell.max(), per_combo.min(), per_combo.median(), per_combo.max()))
    print("targets: anchor=%d library=%d levels (annotation only)" % (
        res["targets"]["anchor_target_levels"], res["targets"]["library_target_levels"]))
    print("metric independence: median |rho| = %.3f (min %.3f, max %.3f, n=%d)" % (
        res["metric_independence"]["abs_median"], res["metric_independence"]["abs_min"],
        res["metric_independence"]["abs_max"], res["metric_independence"]["n"]))
    for k, v in rhos.items():
        print("   %-52s %+.3f" % (k, v))
    print("replication: layouts=%d cellpairs=%d replicated=%d (%.4f) max=%d" % (
        res["replication"]["layouts"], res["replication"]["cellpair_observations"],
        res["replication"]["measured_in_more_than_one_layout"], res["replication"]["frac_replicated"],
        res["replication"]["max_layouts_per_cellpair"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
