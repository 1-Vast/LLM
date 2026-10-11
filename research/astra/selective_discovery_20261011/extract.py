"""Block P inputs, written once: GSE70138 landmark signatures and PRISM tiers for its compounds.

Universe: compounds in GSE70138 (L1000 phase 2, trt_cp) whose 13-character Broad ID appears in the
PRISM Repurposing 19Q4 primary screen.
* ``blockn``: also a block-N unit (matched by the Broad IDs of its PRISM columns); outcomes exposed.
* ``new``: not a block-N unit; PRISM outcomes go to the sealed tier.

L1000: Level 5 MODZ signatures, 24 h, the 7 phase-2 core lines and 6 doses, averaged (unweighted)
per compound x line x dose over the 978 landmark genes (GSE92742 gene_info landmark list; same
Entrez IDs). The source archive is checked against GEO's SHA-512 list.

PRISM: primary log fold change = mean over the compound's primary columns (block N rule);
secondary = mean over the secondary columns at the dose closest to 2.5 uM.

Outputs (git-ignored bulk):
* data/external/lincs_l1000_phase2/derived/block_p_phase2_landmark.npz (inputs; open)
* data/external/prism_19q4/derived/block_p_prism_dev.npz (blockn compounds; exposed)
* data/external/prism_19q4/derived/block_p_prism_sealed.npz (new compounds; ``load_prism('sealed')``
  refuses with TIER_SEALED until FREEZE.json exists)
* EXTRACT_RECEIPT.json here (digests and counts only; no outcome statistic).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P2 = ROOT / "data/external/lincs_l1000_phase2"
P1 = ROOT / "data/external/lincs_l1000_gse92742"
PRISM = ROOT / "data/external/prism_19q4/raw"
GZ = P2 / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx.gz"
GCTX = P2 / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx"
OUT_L = P2 / "derived/block_p_phase2_landmark.npz"
OUT_DEV = ROOT / "data/external/prism_19q4/derived/block_p_prism_dev.npz"
OUT_SEALED = ROOT / "data/external/prism_19q4/derived/block_p_prism_sealed.npz"
BLOCK_N_SPLIT = ROOT / "research/astra/mechanism_routing_20261011/SPLIT.json"
CORE = ["A375", "HA1E", "HELA", "HT29", "MCF7", "PC3", "YAPC"]
DOSES = ["0.04 um", "0.12 um", "0.37 um", "1.11 um", "3.33 um", "10.0 um"]


class TierSealed(RuntimeError):
    code = "TIER_SEALED"


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def expected_sha512(name: str) -> str:
    with gzip.open(P2 / "meta/GSE70138_SHA512SUMS.txt.gz", "rt") as fh:
        for line in fh:
            d, f = line.split()
            if f.lstrip("*") == name:
                return d
    raise SystemExit(f"{name} not in GSE70138_SHA512SUMS")


def main() -> dict:
    if (HERE / "EXTRACT_RECEIPT.json").exists():
        raise SystemExit("EXTRACT_RECEIPT.json exists; extraction runs once")
    t0 = time.time()
    got = digest(GZ, "sha512")
    if got != expected_sha512(GZ.name):
        raise SystemExit("SOURCE_DIGEST_MISMATCH")
    sig = pd.read_csv(P2 / "meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz", sep="\t")
    sig = sig[(sig.pert_type == "trt_cp") & (sig.pert_itime == "24 h") & sig.cell_id.isin(CORE) & sig.pert_idose.isin(DOSES)].copy()
    sig["brd"] = sig.pert_id.str[:13]
    info = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv")
    info["brd"] = info.broad_id.str[:13]
    split = json.loads(BLOCK_N_SPLIT.read_text(encoding="utf-8"))["units"]
    blockn_brd = {}
    for name, u in split.items():
        for c in u["prism_columns"]:
            blockn_brd[c.split("::")[0][:13]] = name
    universe = sorted(set(sig.brd) & set(info.brd))
    meta = info.drop_duplicates("brd").set_index("brd")
    role = np.array(["blockn" if b in blockn_brd else "new" for b in universe])
    genes = pd.read_csv(P1 / "GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t")
    lm = genes[genes.pr_is_lm == 1].sort_values("pr_gene_symbol")
    sig = sig[sig.brd.isin(universe)]
    bpos = {b: i for i, b in enumerate(universe)}
    x = np.zeros((len(universe), len(CORE), len(DOSES), len(lm)), np.float32)
    n_sig = np.zeros((len(universe), len(CORE), len(DOSES)), np.int16)
    with h5py.File(GCTX, "r") as f:
        col_ids = f["0/META/COL/id"][:].astype(str)
        row_ids = f["0/META/ROW/id"][:].astype(str)
        col_index = {s: i for i, s in enumerate(col_ids)}
        row_pos = {r: i for i, r in enumerate(row_ids)}
        gene_cols = np.array([row_pos[str(g)] for g in lm.pr_gene_id])
        missing = [s for s in sig.sig_id if s not in col_index]
        if missing:
            raise SystemExit(f"SIGNATURES_ABSENT: {len(missing)}")
        dest = {col_index[r.sig_id]: (bpos[r.brd], CORE.index(r.cell_id), DOSES.index(r.pert_idose)) for r in sig.itertuples()}
        idx = np.array(sorted(dest))
        mat = f["0/DATA/0/matrix"]
        for start in range(0, len(idx), 1000):  # accumulate while reading; no per-signature cache
            block = idx[start:start + 1000]
            data = mat[block, :][:, gene_cols]
            for k, row in zip(block, data):
                i, c, d = dest[int(k)]
                x[i, c, d] += row
                n_sig[i, c, d] += 1
    x = np.where(n_sig[..., None] > 0, x / np.maximum(n_sig[..., None], 1), np.nan).astype(np.float16)
    OUT_L.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT_L, brd=np.array(universe), name=np.array([str(meta.at[b, "name"]) for b in universe]),
                        moa=np.array([str(meta.at[b, "moa"]) for b in universe]),
                        target=np.array([str(meta.at[b, "target"]) for b in universe]),
                        smiles=np.array([str(meta.at[b, "smiles"]) for b in universe]),
                        role=role, blockn_name=np.array([blockn_brd.get(b, "") for b in universe]),
                        line=np.array(CORE), dose=np.array(DOSES), gene=lm.pr_gene_symbol.astype(str).values,
                        x=x, n_sig=n_sig)
    # PRISM tiers
    lfc = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    lines = list(lfc.index)
    sec_info = pd.read_csv(PRISM / "secondary-screen-replicate-collapsed-treatment-info.csv")
    sec_info["brd"] = sec_info.broad_id.astype(str).str[:13]
    sec = pd.read_csv(PRISM / "secondary-screen-replicate-collapsed-logfold-change.csv", index_col=0).reindex(lines)
    sec_info = sec_info[sec_info.column_name.isin(sec.columns)]
    rec_tiers = {}
    for tier, path in (("blockn", OUT_DEV), ("new", OUT_SEALED)):
        bs = [b for b, r in zip(universe, role) if r == tier]
        P = np.stack([lfc[info.loc[info.brd == b, "column_name"].tolist()].mean(axis=1).to_numpy(np.float32) for b in bs])
        S2 = np.full_like(P, np.nan)
        sdose = np.full(len(bs), np.nan)
        for i, b in enumerate(bs):
            g = sec_info[sec_info.brd == b]
            if len(g):
                dd = g.dose.astype(float).to_numpy()
                best = dd[np.argmin(np.abs(np.log(dd / 2.5)))]
                S2[i] = sec[g.loc[np.isclose(dd, best), "column_name"].tolist()].mean(axis=1).to_numpy(np.float32)
                sdose[i] = best
        np.savez_compressed(path, brd=np.array(bs), line=np.array(lines), primary=P, secondary=S2, secondary_dose=sdose)
        rec_tiers[tier] = {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": digest(path, "sha256"),
                           "n": len(bs), "n_with_secondary": int(np.isfinite(sdose).sum())}
    rec = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": GZ.name, "source_sha512": got,
           "gctx_note": "decompressed copy of the verified archive (decompressed 2026-10-11 10:27 local by the block O session)",
           "landmark": {"file": str(OUT_L.relative_to(ROOT)).replace("\\", "/"), "sha256": digest(OUT_L, "sha256"),
                        "n_compounds": len(universe), "n_signatures": int(len(sig)), "lines": CORE, "doses": DOSES,
                        "cells_present": int((n_sig > 0).sum())},
           "prism": rec_tiers, "seconds": round(time.time() - t0, 1),
           "disclosure": "Before extraction, the author saw one outcome statistic of the new tier: 325 of 987 compounds "
                         "kill >= 5% of lines (LFC < -1), computed 2026-10-11 ~11:20 local while sizing the pool."}
    (HERE / "EXTRACT_RECEIPT.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def load_prism(tier: str) -> dict:
    path = {"dev": OUT_DEV, "sealed": OUT_SEALED}[tier]
    if tier == "sealed" and not (HERE / "FREEZE.json").exists():
        raise TierSealed("TIER_SEALED: new-compound outcomes open only after FREEZE.json")
    rec = json.loads((HERE / "EXTRACT_RECEIPT.json").read_text(encoding="utf-8"))
    want = rec["prism"]["blockn" if tier == "dev" else "new"]["sha256"]
    if digest(path, "sha256") != want:
        raise SystemExit(f"TIER_DIGEST_MISMATCH: {path.name}")
    with np.load(path) as f:
        return {k: f[k] for k in f.files}


def load_l1000() -> dict:
    rec = json.loads((HERE / "EXTRACT_RECEIPT.json").read_text(encoding="utf-8"))
    if digest(OUT_L, "sha256") != rec["landmark"]["sha256"]:
        raise SystemExit("TIER_DIGEST_MISMATCH: landmark")
    # gene symbols were stored as an object array; the digest is checked above before pickling is allowed
    with np.load(OUT_L, allow_pickle=True) as f:
        return {k: (f[k].astype(str) if f[k].dtype == object else f[k]) for k in f.files}


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
