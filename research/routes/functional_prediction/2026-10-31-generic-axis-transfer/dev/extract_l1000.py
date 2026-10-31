"""Mean GSE92742 landmark signatures per compound x (core line, 6/24 h) at 10 uM.

Usage: extract_l1000.py KEYS.tsv OUT.npz
KEYS.tsv has columns key, ik14 (InChIKey connectivity block); every LINCS trt_cp pert_id whose
inchi_key_prefix equals ik14 contributes. Signatures are the level-5 MODZ z-scores; the value for
(key, line, time) is the mean over all matching signatures (n_sig records how many).
"""
import sys

import h5py
import numpy as np
import pandas as pd

L1000 = "D:/MAESTRO/data/external/lincs_l1000_gse92742"
LINES = ["A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP"]
TIMES = ["6 h", "24 h"]
OPTIONS = [f"{c}|{t}" for c in LINES for t in TIMES]


def main(keys_path: str, out_path: str) -> None:
    keys = pd.read_csv(keys_path, sep="\t", dtype=str)
    pert = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str)
    pert = pert[pert.pert_type == "trt_cp"]
    sig = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", dtype=str,
                      usecols=["sig_id", "pert_id", "pert_type", "cell_id", "pert_idose", "pert_itime"])
    sig = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(LINES) & sig.pert_itime.isin(TIMES)
              & (sig.pert_idose == "10 \u00b5M")]
    gene = pd.read_csv(f"{L1000}/GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t", dtype=str)
    lm = gene[gene.pr_is_lm == "1"].sort_values("pr_gene_symbol")
    pid2key = {}
    for key, ik in zip(keys.key, keys.ik14):
        for pid in pert.loc[pert.inchi_key_prefix == ik, "pert_id"]:
            pid2key.setdefault(pid, set()).add(key)
    sig = sig[sig.pert_id.isin(pid2key)]
    with h5py.File(f"{L1000}/GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx", "r") as f:
        cid = pd.Index(f["/0/META/COL/id"][:].astype(str))
        rid = pd.Index(f["/0/META/ROW/id"][:].astype(str))
        gcols = rid.get_indexer(lm.pr_gene_id)
        assert (gcols >= 0).all()
        rows = cid.get_indexer(sig.sig_id)
        assert (rows >= 0).all()
        order = np.argsort(rows)
        data = f["/0/DATA/0/matrix"][np.sort(rows), :][:, gcols]
    vals = np.empty_like(data)
    vals[order] = data
    k_index = {k: i for i, k in enumerate(keys.key)}
    o_index = {o: j for j, o in enumerate(OPTIONS)}
    total = np.zeros((len(keys), len(OPTIONS), len(lm)))
    count = np.zeros((len(keys), len(OPTIONS)), dtype=np.int32)
    for v, pid, c, t in zip(vals, sig.pert_id, sig.cell_id, sig.pert_itime):
        j = o_index[f"{c}|{t}"]
        for key in pid2key[pid]:
            total[k_index[key], j] += v
            count[k_index[key], j] += 1
    x = np.where(count[..., None] > 0, total / np.maximum(count, 1)[..., None], np.nan).astype(np.float32)
    np.savez_compressed(out_path, key=keys.key.to_numpy(), ik14=keys.ik14.to_numpy(), option=np.array(OPTIONS),
                        gene=lm.pr_gene_symbol.to_numpy(), x=x, n_sig=count.astype(np.int16))
    print(f"{len(keys)} keys, {len(sig)} signatures, keys with any signature: {(count.sum(1) > 0).sum()}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
