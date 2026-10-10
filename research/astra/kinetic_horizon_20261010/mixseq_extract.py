"""Tier-gated MIX-Seq cell extraction on the candidate 2,000-gene STATE axis.

Per cell it stores library-normalised values ``x / total`` for the axis genes present in MIX-Seq
(1,905 of 2,000; absent genes are flagged in ``present``), the total count, and a cell-cycle phase
called from full-gene expression with a fixed reference (Tirosh S/G2M lists; control genes drawn
from expression bins computed on control cells of pools A, C and D only; seed 20261010).

Controls (pool A/C 24 h control, pool D ``DMSO_*`` hashes) are always readable. Treated cells are
readable for pool-A development lines; pool-A confirmation, seen-context and every pool-D
``Tram_*`` hash require FREEZE.json and ``--allow-sealed`` (``TIER_SEALED``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import anndata as ad
import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
H5 = ROOT / "data/external/mixseq_scperturb/mcfarland_2020.h5ad"
OUT = ROOT / "data/external/kinetic_horizon_20261010/mixseq"
GENES = json.loads((ROOT / "research/decision_value/axis_recovery_20261010/authority/sources/RHAISTER_splits__tahoe__static_2k_genes.json").read_text())
G2M = "HMGB2 CDK1 NUSAP1 UBE2C BIRC5 TPX2 TOP2A NDC80 CKS2 NUF2 CKS1B MKI67 TMPO CENPF TACC3 FAM64A SMC4 CCNB2 CKAP2L CKAP2 AURKB BUB1 KIF11 ANP32E TUBB4B GTSE1 KIF20B HJURP CDCA3 HN1 CDC20 TTK CDC25C KIF2C RANGAP1 NCAPD2 DLGAP5 CDCA2 CDCA8 ECT2 KIF23 HMMR AURKA PSRC1 ANLN LBR CKAP5 CENPE CTCF NEK2 G2E3 GAS2L3 CBX5 CENPA".split()
SG = "MCM5 PCNA TYMS FEN1 MCM2 MCM4 RRM1 UNG GINS2 MCM6 CDCA7 DTL PRIM1 UHRF1 MLF1IP HELLS RFC2 RPA2 NASP RAD51AP1 GMNN WDR76 SLBP CCNE2 UBR7 POLD3 MSH2 ATAD2 RAD51 RRM2 CDC45 CDC6 EXO1 TIPIN DSCC1 BLM CASP8AP2 USP1 CLSPN POLA1 CHAF1B BRIP1 E2F8".split()
SEED = 20261010
PHASES = ("G1", "S", "G2M")


def selections(o, split):
    """Named cell selections: (tier, mask) per extraction unit."""
    A = set(split["pool_A"]); dev = set(split["pool_A_development"]); D = set(split["pool_D"])
    q = o.cell_quality == "normal"
    d = o.DepMap_ID
    sel = {
        "A_control": ("open", q & (o.perturbation == "control") & (o.time == "24") & o.channel.isin(["1", "10"]) & d.isin(A)),
        "C_control": ("open", q & (o.perturbation == "control") & (o.time == "24") & (o.channel == "nan")),
        "D_control": ("open", q & (o.time == "3, 6, 12, 24, 48") & o.hash_tag.str.startswith("DMSO_")),
        "A_treated_dev": ("open", q & (o.perturbation != "control") & (o.time == "24") & (o.channel != "nan") & d.isin(dev)),
        "A_treated_sealed": ("sealed", q & (o.perturbation != "control") & (o.time == "24") & (o.channel != "nan") & d.isin(A - dev)),
        "C_treated": ("sealed", q & (o.perturbation == "Trametinib") & (o.time == "24") & (o.channel == "nan")),
        "D_treated": ("sealed", q & (o.time == "3, 6, 12, 24, 48") & (o.hash_tag.str.startswith("Tram_") | (o.hash_tag == "Untreated_48hr"))),
    }
    return sel


def phase_reference(a, o, gene_index):
    """Bins and control genes from control cells only (log1p of 1e4-normalised counts)."""
    ctrl = np.flatnonzero(((o.perturbation == "control") | o.hash_tag.str.startswith("DMSO_")).to_numpy() & (o.cell_quality == "normal").to_numpy())
    rng = np.random.default_rng(SEED)
    pick = np.sort(rng.choice(ctrl, min(20000, len(ctrl)), replace=False))
    X = a[pick].to_memory().X.tocsr().astype(np.float64)
    tot = np.asarray(X.sum(1)).ravel()
    X = sp.diags(1e4 / tot) @ X
    X.data = np.log1p(X.data)
    mean = np.asarray(X.mean(0)).ravel()
    order = np.argsort(mean)
    bins = np.empty(len(mean), int)
    bins[order] = np.arange(len(mean)) * 25 // len(mean)
    ref = {}
    for name, genes in (("S", SG), ("G2M", G2M)):
        idx = [gene_index[g] for g in genes if g in gene_index]
        ctl = []
        for g in idx:
            pool = np.flatnonzero(bins == bins[g])
            pool = pool[~np.isin(pool, idx)]
            ctl.extend(rng.choice(pool, 50, replace=False).tolist())
        ref[name] = (np.array(idx), np.array(sorted(set(ctl))))
    return ref


def run(unit: str, allow_sealed: bool) -> dict:
    split = json.loads((HERE / "MIXSEQ_SPLIT.json").read_text(encoding="utf-8"))
    a = ad.read_h5ad(H5, backed="r")
    o = a.obs[["DepMap_ID", "cell_quality", "channel", "perturbation", "time", "dose_value", "hash_tag"]].copy()
    for c in o.columns:
        o[c] = o[c].astype(str)
    tier, mask = selections(o, split)[unit]
    if tier == "sealed" and not ((HERE / "FREEZE.json").exists() and allow_sealed):
        raise SystemExit(f"TIER_SEALED: {unit} requires FREEZE.json and --allow-sealed")
    var = list(a.var.index.astype(str))
    gene_index = {g: i for i, g in enumerate(var)}
    present = np.array([g in gene_index for g in GENES])
    axis_cols = np.array([gene_index[g] for g in GENES if g in gene_index])
    t0 = time.time()
    ref = phase_reference(a, o, gene_index)
    idx = np.flatnonzero(mask.to_numpy())
    X = a[idx].to_memory().X.tocsr().astype(np.float64)
    tot = np.asarray(X.sum(1)).ravel()
    L = sp.diags(1e4 / tot) @ X
    L.data = np.log1p(L.data)
    s = {k: np.asarray(L[:, g].mean(1)).ravel() - np.asarray(L[:, c].mean(1)).ravel() for k, (g, c) in ref.items()}
    phase = np.where(np.maximum(s["S"], s["G2M"]) < 0, 0, np.where(s["S"] >= s["G2M"], 1, 2)).astype(np.int8)
    frac = (sp.diags(1.0 / tot) @ X[:, axis_cols]).toarray().astype(np.float32)
    meta = o.iloc[idx]
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / f"{unit}.npz", frac=frac, total=tot.astype(np.float32), phase=phase,
                        depmap=meta.DepMap_ID.to_numpy(), perturbation=meta.perturbation.to_numpy(), time=meta.time.to_numpy(),
                        dose=meta.dose_value.to_numpy(), channel=meta.channel.to_numpy(), hash_tag=meta.hash_tag.to_numpy(),
                        present=present, s_score=s["S"].astype(np.float32), g2m_score=s["G2M"].astype(np.float32))
    a.file.close()
    receipt = {"unit": unit, "tier": tier, "cells": int(len(idx)), "lines": int(meta.DepMap_ID.nunique()),
               "axis_genes_present": int(present.sum()), "seconds": round(time.time() - t0, 1),
               "phase_marker_genes": {k: int(len(v[0])) for k, v in ref.items()},
               "cell_index_sha256": hashlib.sha256(idx.astype(np.int64).tobytes()).hexdigest(),
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (HERE / "mixseq").mkdir(exist_ok=True)
    (HERE / "mixseq" / f"{unit}.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return receipt


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("unit", choices=["A_control", "C_control", "D_control", "A_treated_dev", "A_treated_sealed", "C_treated", "D_treated"])
    ap.add_argument("--allow-sealed", action="store_true")
    a = ap.parse_args()
    print(json.dumps(run(a.unit, a.allow_sealed)))
