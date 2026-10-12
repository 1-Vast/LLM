"""Development tier: GSE92742 (L1000 phase 1) landmark responses for block Q.

Writes ``data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz`` with
* compound responses: Level 5 MODZ, trt_cp, 10 uM, 24 h, the nine core lines, averaged per
  compound x line (compound = lower-cased pert_iname; a BRD-only name stays the BRD id);
  ``cp_half_a``/``cp_half_b`` are means over two disjoint halves of the signatures where a
  compound x line has at least two, the within-release replicate ceiling;
* knockdown responses: trt_sh.cgs consensus gene signatures, 96 h preferred, else the latest time;
* vehicle responses: ctl_vehicle Level 5 signatures at 24 h, the noise reference for activity calls.

Phase 2 (GSE70138) is the sealed confirmation tier and is not read here.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/external/lincs_l1000_gse92742"
GCTX = SRC / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx"
OUT = SRC / "derived/blockq_phase1.npz"
CORE = ["A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP"]
KD_TIME_PREFERENCE = ["96 h", "120 h", "144 h", "168 h", "48 h", "24 h", "6 h"]


def compound_key(iname: str, pert_id: str) -> str:
    name = str(iname).strip().lower()
    return pert_id if (not name or name.startswith("brd-")) else name


def read_rows(h5: h5py.File, rows: np.ndarray, cols: np.ndarray, batch: int = 4000) -> np.ndarray:
    """Read the given signature rows (any order) restricted to the landmark columns."""
    order = np.argsort(rows)
    srt = rows[order]
    out = np.empty((len(rows), len(cols)), np.float32)
    mat = h5["0/DATA/0/matrix"]
    for i in range(0, len(srt), batch):
        block = mat[srt[i:i + batch], :]
        out[order[i:i + batch]] = block[:, cols]
    return out


def split_half(sig_ids: list[str]) -> tuple[list[str], list[str]]:
    ranked = sorted(sig_ids, key=lambda s: hashlib.sha256(s.encode()).hexdigest())
    return ranked[0::2], ranked[1::2]


def main() -> None:
    t0 = time.time()
    sig = pd.read_csv(SRC / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", low_memory=False)
    gene = pd.read_csv(SRC / "GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t", low_memory=False)
    lm = gene[gene.pr_is_lm == 1]
    with h5py.File(GCTX, "r") as h5:
        row_ids = [x.decode() for x in h5["0/META/ROW/id"][:]]
        col_ids = [x.decode() for x in h5["0/META/COL/id"][:]]
        gpos = {g: i for i, g in enumerate(row_ids)}
        lm_cols = np.array([gpos[str(g)] for g in lm.pr_gene_id])
        spos = {s: i for i, s in enumerate(col_ids)}

        cp = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(CORE) & (sig.pert_idose == "10 µM")
                 & (sig.pert_itime == "24 h")].copy()
        cp["key"] = [compound_key(n, p) for n, p in zip(cp.pert_iname, cp.pert_id)]
        keys = sorted(cp.key.unique())
        kpos = {k: i for i, k in enumerate(keys)}
        X = read_rows(h5, np.array([spos[s] for s in cp.sig_id]), lm_cols)
        sig_row = {s: i for i, s in enumerate(cp.sig_id)}
        shape = (len(keys), len(CORE), len(lm_cols))
        cp_mean = np.full(shape, np.nan, np.float32)
        half_a = np.full(shape, np.nan, np.float32)
        half_b = np.full(shape, np.nan, np.float32)
        n_sig = np.zeros(shape[:2], np.int16)
        for (k, c), g in cp.groupby(["key", "cell_id"]):
            i, j = kpos[k], CORE.index(c)
            ids = list(g.sig_id)
            rows = [sig_row[s] for s in ids]
            cp_mean[i, j] = X[rows].mean(0)
            n_sig[i, j] = len(ids)
            if len(ids) >= 2:
                a, b = split_half(ids)
                half_a[i, j] = X[[sig_row[s] for s in a]].mean(0)
                half_b[i, j] = X[[sig_row[s] for s in b]].mean(0)
        first = cp.sort_values("sig_id").drop_duplicates("key").set_index("key")
        pert_ids = cp.groupby("key").pert_id.apply(lambda s: "|".join(sorted(set(s))))

        sh = sig[(sig.pert_type == "trt_sh.cgs") & sig.cell_id.isin(CORE)].copy()
        sh["rank"] = sh.pert_itime.map({t: i for i, t in enumerate(KD_TIME_PREFERENCE)}).fillna(99)
        sh = sh.sort_values(["pert_iname", "cell_id", "rank", "sig_id"]).drop_duplicates(["pert_iname", "cell_id"])
        kd_genes = sorted(sh.pert_iname.unique())
        kd_pos = {g: i for i, g in enumerate(kd_genes)}
        Xk = read_rows(h5, np.array([spos[s] for s in sh.sig_id]), lm_cols)
        kd = np.full((len(kd_genes), len(CORE), len(lm_cols)), np.nan, np.float32)
        kd_time = np.full((len(kd_genes), len(CORE)), "", dtype="<U6")
        for r, row in enumerate(sh.itertuples()):
            kd[kd_pos[row.pert_iname], CORE.index(row.cell_id)] = Xk[r]
            kd_time[kd_pos[row.pert_iname], CORE.index(row.cell_id)] = row.pert_itime

        veh = sig[(sig.pert_type == "ctl_vehicle") & sig.cell_id.isin(CORE) & (sig.pert_itime == "24 h")]
        Xv = read_rows(h5, np.array([spos[s] for s in veh.sig_id]), lm_cols)

    np.savez_compressed(
        OUT,
        compound=np.array(keys), pert_ids=np.array([pert_ids[k] for k in keys]),
        iname=np.array([str(first.loc[k, "pert_iname"]) for k in keys]),
        line=np.array(CORE), gene_id=lm.pr_gene_id.astype(str).values, gene_symbol=lm.pr_gene_symbol.astype(str).values,
        cp=cp_mean, cp_half_a=half_a, cp_half_b=half_b, n_sig=n_sig,
        kd_gene=np.array(kd_genes), kd=kd, kd_time=kd_time,
        vehicle=Xv, vehicle_line=veh.cell_id.astype(str).values,
    )
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    record = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "output": str(OUT.relative_to(ROOT)),
              "sha256": digest, "n_compounds": len(keys), "n_cp_cells": int((n_sig > 0).sum()),
              "n_kd_genes": len(kd_genes), "n_kd_cells": int(np.isfinite(kd[..., 0]).sum()), "n_vehicle": int(len(Xv)),
              "seconds": round(time.time() - t0, 1)}
    (Path(__file__).parent / "extract_phase1.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
