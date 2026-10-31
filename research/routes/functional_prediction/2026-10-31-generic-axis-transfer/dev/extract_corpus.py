"""All GSE92742 trt_cp level-5 landmark signatures in the 9 core lines (any dose/time), float16.

No viability outcome is read. Output: corpus.npz with x (n x 978, alphabetical landmark symbols),
sig_id, pert_id, ik14, cell, idose, itime, tas, cc_q75.
"""
import sys

import h5py
import numpy as np
import pandas as pd

L1000 = "D:/MAESTRO/data/external/lincs_l1000_gse92742"
LINES = ["A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP"]

sig = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", dtype=str,
                  usecols=["sig_id", "pert_id", "pert_type", "cell_id", "pert_idose", "pert_itime"])
sig = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(LINES)]
met = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_sig_metrics.txt.gz", sep="\t", dtype=str,
                  usecols=["sig_id", "tas", "distil_cc_q75"])
sig = sig.merge(met, on="sig_id", how="left")
pert = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str)
sig = sig.merge(pert[["pert_id", "inchi_key_prefix"]], on="pert_id", how="left")
gene = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t", dtype=str)
lm = gene[gene.pr_is_lm == "1"].sort_values("pr_gene_symbol")
with h5py.File(f"{L1000}/GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx", "r") as f:
    cid = pd.Index(f["/0/META/COL/id"][:].astype(str))
    rid = pd.Index(f["/0/META/ROW/id"][:].astype(str))
    gcols = rid.get_indexer(lm.pr_gene_id)
    rows = cid.get_indexer(sig.sig_id)
    assert (rows >= 0).all() and (gcols >= 0).all()
    want = np.zeros(len(cid), dtype=bool)
    want[rows] = True
    pos = np.full(len(cid), -1)
    pos[rows] = np.arange(len(rows))
    out = np.empty((len(rows), len(gcols)), dtype=np.float16)
    M = f["/0/DATA/0/matrix"]
    step = 8000
    for a in range(0, len(cid), step):
        b = min(a + step, len(cid))
        sel = np.where(want[a:b])[0]
        if len(sel) == 0:
            continue
        block = M[a:b, :]
        out[pos[a + sel]] = block[sel][:, gcols].astype(np.float16)
        print(f"rows {b}/{len(cid)}", flush=True)
np.savez(sys.argv[1], x=out, sig_id=sig.sig_id.to_numpy(), pert_id=sig.pert_id.to_numpy(),
         ik14=sig.inchi_key_prefix.fillna("").to_numpy(), cell=sig.cell_id.to_numpy(),
         idose=sig.pert_idose.to_numpy(), itime=sig.pert_itime.to_numpy(),
         tas=pd.to_numeric(sig.tas, errors="coerce").to_numpy(),
         cc_q75=pd.to_numeric(sig.distil_cc_q75, errors="coerce").to_numpy(),
         gene=lm.pr_gene_symbol.to_numpy())
print("done", out.shape)
