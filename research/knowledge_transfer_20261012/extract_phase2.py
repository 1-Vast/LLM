"""Confirmation tiers: GSE70138 (L1000 phase 2) landmark responses for block Q.

Compound responses: Level 5 trt_cp signatures at 10 uM, 24 h, the seven phase-2 core lines,
averaged per compound x line (compound key as in phase 1). Two tiers:
* reference (open): compounds that also have a phase-1 10 uM/24 h response; the confirmation atlas;
* query (sealed): compounds absent from phase 1; written separately and readable through
  ``load_query`` only after ``FREEZE.json`` exists (refusal code ``TIER_SEALED``).

The open file also carries query-compound identities (names, PubChem CIDs, SMILES), which are
inputs to knowledge routes, the vehicle signatures of the seven lines, and the CRISPR knockout
(trt_xpr) mean per gene x parental line (Cas9 clone .311 preferred, 96 h) for the exploratory genetic route.
This script prints counts and hashes only; it computes no statistic of the query responses.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from extract_phase1 import compound_key, read_rows

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "data/external/lincs_l1000_phase2"
GCTX = SRC / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx"
GENE_INFO = ROOT / "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_gene_info.txt.gz"
PHASE1 = ROOT / "data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz"
OUT_REF = SRC / "derived/blockq_phase2_reference.npz"
OUT_QUERY = SRC / "derived/blockq_phase2_query_SEALED.npz"
LINES = ["A375", "HA1E", "HELA", "HT29", "MCF7", "PC3", "YAPC"]
XPR_TIME_PREFERENCE = ["96 h", "120 h", "144 h", "72 h", "48 h", "24 h", "6 h", "3 h"]


class TierSealed(RuntimeError):
    code = "TIER_SEALED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    t0 = time.time()
    sig = pd.read_csv(SRC / "meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz", sep="\t", low_memory=False)
    pert = pd.read_csv(SRC / "meta/GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz", sep="\t", low_memory=False)
    pert = pert.drop_duplicates("pert_id").set_index("pert_id")
    gene = pd.read_csv(GENE_INFO, sep="\t", low_memory=False)
    lm = gene[gene.pr_is_lm == 1]
    p1 = set(np.load(PHASE1, allow_pickle=True)["compound"])
    with h5py.File(GCTX, "r") as h5:
        row_ids = [x.decode() for x in h5["0/META/ROW/id"][:]]
        col_ids = [x.decode() for x in h5["0/META/COL/id"][:]]
        gpos = {g: i for i, g in enumerate(row_ids)}
        lm_cols = np.array([gpos[str(g)] for g in lm.pr_gene_id])
        spos = {s: i for i, s in enumerate(col_ids)}

        cp = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(LINES) & sig.pert_idose.astype(str).str.startswith("10.0 um")
                 & (sig.pert_itime == "24 h")].copy()
        cp["key"] = [compound_key(n, p) for n, p in zip(cp.pert_iname, cp.pert_id)]
        cp = cp[cp.sig_id.isin(spos)]
        X = read_rows(h5, np.array([spos[s] for s in cp.sig_id]), lm_cols)
        row = {s: i for i, s in enumerate(cp.sig_id)}
        keys = sorted(cp.key.unique())
        tiers = {"reference": [k for k in keys if k in p1], "query": [k for k in keys if k not in p1]}
        blocks = {}
        for tier, tk in tiers.items():
            kpos = {k: i for i, k in enumerate(tk)}
            Y = np.full((len(tk), len(LINES), len(lm_cols)), np.nan, np.float32)
            n_sig = np.zeros((len(tk), len(LINES)), np.int16)
            sub = cp[cp.key.isin(kpos)]
            for (k, c), g in sub.groupby(["key", "cell_id"]):
                Y[kpos[k], LINES.index(c)] = X[[row[s] for s in g.sig_id]].mean(0)
                n_sig[kpos[k], LINES.index(c)] = len(g)
            ids = sub.groupby("key").pert_id.apply(lambda s: "|".join(sorted(set(s))))
            names = sub.sort_values("sig_id").drop_duplicates("key").set_index("key").pert_iname
            smiles, cids = [], []
            for k in tk:
                pids = [p for p in ids[k].split("|") if p in pert.index]
                smi = next((s for s in pert.loc[pids].canonical_smiles.astype(str) if s and s not in ("-666", "nan", "restricted")), "")
                smiles.append(smi)
                cids.append("")
            blocks[tier] = dict(compound=np.array(tk), pert_ids=np.array([ids[k] for k in tk]),
                                iname=np.array([str(names[k]) for k in tk]), smiles=np.array(smiles), cp=Y, n_sig=n_sig)

        veh = sig[(sig.pert_type == "ctl_vehicle") & sig.cell_id.isin(LINES) & (sig.pert_itime == "24 h") & sig.sig_id.isin(spos)]
        Xv = read_rows(h5, np.array([spos[s] for s in veh.sig_id]), lm_cols)

        xpr = sig[(sig.pert_type == "trt_xpr") & sig.sig_id.isin(spos)].copy()
        xpr["parent"] = xpr.cell_id.astype(str).str.split(".").str[0]
        xpr = xpr[xpr.parent.isin(LINES)]
        xpr["clone_rank"] = (~xpr.cell_id.astype(str).str.endswith(".311")).astype(int)  # Cas9 clone 311 preferred
        xpr = xpr[xpr.clone_rank == xpr.groupby("parent").clone_rank.transform("min")]
        xpr["rank"] = xpr.pert_itime.map({t: i for i, t in enumerate(XPR_TIME_PREFERENCE)}).fillna(99)
        best = xpr.groupby(["pert_iname", "parent"])["rank"].transform("min")
        xpr = xpr[xpr["rank"] == best]
        Xx = read_rows(h5, np.array([spos[s] for s in xpr.sig_id]), lm_cols) if len(xpr) else np.zeros((0, len(lm_cols)), np.float32)
        xrow = {s: i for i, s in enumerate(xpr.sig_id)}
        xg = sorted(xpr.pert_iname.astype(str).unique())
        XPR = np.full((len(xg), len(LINES), len(lm_cols)), np.nan, np.float32)
        for (g, c), grp in xpr.groupby(["pert_iname", "parent"]):
            XPR[xg.index(str(g)), LINES.index(c)] = Xx[[xrow[s] for s in grp.sig_id]].mean(0)

    ref = blocks["reference"]; qry = blocks["query"]
    np.savez_compressed(OUT_REF, line=np.array(LINES), gene_id=lm.pr_gene_id.astype(str).values,
                        gene_symbol=lm.pr_gene_symbol.astype(str).values,
                        **{f"ref_{k}": v for k, v in ref.items()},
                        **{f"query_{k}": v for k, v in qry.items() if k not in ("cp", "n_sig")},
                        vehicle=Xv, vehicle_line=veh.cell_id.astype(str).values,
                        xpr_gene=np.array(xg), xpr=XPR)
    np.savez_compressed(OUT_QUERY, compound=qry["compound"], cp=qry["cp"], n_sig=qry["n_sig"])
    record = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "source": GCTX.name, "reference": {"path": OUT_REF.relative_to(ROOT).as_posix(), "sha256": sha256(OUT_REF),
                                                 "n_compounds": len(ref["compound"]), "n_cells": int((ref["n_sig"] > 0).sum())},
              "query_sealed": {"path": OUT_QUERY.relative_to(ROOT).as_posix(), "sha256": sha256(OUT_QUERY),
                               "n_compounds": len(qry["compound"])},
              "n_vehicle": int(len(Xv)), "n_xpr_genes": len(xg), "n_xpr_cells": int(np.isfinite(XPR[..., 0]).sum()),
              "seconds": round(time.time() - t0, 1),
              "note": "Query responses were written without computing any statistic of them."}
    (HERE / "extract_phase2.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


def load_query():
    if not (HERE / "FREEZE.json").exists():
        raise TierSealed("TIER_SEALED: query responses open only after FREEZE.json")
    record = json.loads((HERE / "extract_phase2.json").read_text(encoding="utf-8"))["query_sealed"]
    if sha256(OUT_QUERY) != record["sha256"]:
        raise RuntimeError("SEALED_TIER_HASH_MISMATCH")
    z = np.load(OUT_QUERY, allow_pickle=True)
    return {k: z[k] for k in z.files}


if __name__ == "__main__":
    main()
