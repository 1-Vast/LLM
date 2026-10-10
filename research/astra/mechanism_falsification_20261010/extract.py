"""Extract landmark-gene Level 5 signatures for the SPLIT.json universe (writes once).

Source: GSE92742 Level 5 (MODZ consensus z-scores), verified against GEO's SHA-512 list before use.
For every drug and design option (line x time at 10 uM) the signatures listed in SPLIT.json are
averaged (unweighted) over the 978 landmark genes. Output (git-ignored bulk):
``data/external/lincs_l1000_gse92742/derived/block_m_landmark.npz`` with
* ``drug`` (n_drug), ``option`` (18 strings "LINE|TIME"), ``gene`` (978 symbols),
* ``x`` float32 (n_drug, 18, 978), NaN where an option is absent,
* ``n_sig`` int16 (n_drug, 18).
Reference and development drugs go to ``block_m_landmark_open.npz``; confirmation drugs go to
``block_m_landmark_sealed.npz``, which no analysis opens before FREEZE.json exists.
A receipt with the source digest and output digest is written next to this script.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "data/external/lincs_l1000_gse92742"
GZ = SRC / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx.gz"
GCTX = SRC / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx"
OUT = SRC / "derived" / "block_m_landmark_open.npz"       # reference + development drugs
SEALED = SRC / "derived" / "block_m_landmark_sealed.npz"  # confirmation drugs; opened only after FREEZE.json


def sha512_expected(name: str) -> str:
    with gzip.open(SRC / "GSE92742_SHA512SUMS.txt.gz", "rt") as fh:
        for line in fh:
            digest, fname = line.split()
            if fname.lstrip("*") == name:
                return digest
    raise SystemExit(f"{name} not listed in GSE92742_SHA512SUMS")


def file_digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def main() -> dict:
    if OUT.exists():
        raise SystemExit("output exists; extraction runs once")
    expected = sha512_expected(GZ.name)
    got = file_digest(GZ, "sha512")
    if got != expected:
        raise SystemExit(f"SOURCE_DIGEST_MISMATCH: {GZ.name}")
    if not GCTX.exists():
        with gzip.open(GZ, "rb") as src, open(GCTX, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1 << 24)
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    sig = pd.read_csv(SRC / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", low_memory=False).set_index("sig_id")
    genes = pd.read_csv(SRC / "GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t")
    lm = genes[genes.pr_is_lm == 1].sort_values("pr_gene_symbol")
    options = [f"{c}|{t}" for c in split["core_lines"] for t in split["times"]]
    drugs = sorted(split["drugs"])
    with h5py.File(GCTX, "r") as f:
        col_ids = f["0/META/COL/id"][:].astype(str)
        row_ids = f["0/META/ROW/id"][:].astype(str)
        mat = f["0/DATA/0/matrix"]
        col_index = {s: i for i, s in enumerate(col_ids)}
        row_pos = {r: i for i, r in enumerate(row_ids)}
        gene_cols = np.array([row_pos[str(g)] for g in lm.pr_gene_id])
        wanted = sorted({s for d in drugs for s in split["drugs"][d]["sig_ids"]})
        missing = [s for s in wanted if s not in col_index]
        if missing:
            raise SystemExit(f"SIGNATURES_ABSENT: {len(missing)}")
        idx = np.array(sorted(col_index[s] for s in wanted))
        vals: dict[str, np.ndarray] = {}
        for start in range(0, len(idx), 2000):
            block = idx[start:start + 2000]
            data = mat[block, :][:, gene_cols]
            for i, row in zip(block, data):
                vals[col_ids[i]] = row.astype(np.float32)
    x = np.full((len(drugs), len(options), len(lm)), np.nan, dtype=np.float32)
    n_sig = np.zeros((len(drugs), len(options)), dtype=np.int16)
    opt_pos = {o: j for j, o in enumerate(options)}
    for i, d in enumerate(drugs):
        acc: dict[int, list[np.ndarray]] = {}
        for s in split["drugs"][d]["sig_ids"]:
            o = f"{sig.at[s, 'cell_id']}|{sig.at[s, 'pert_itime']}"
            acc.setdefault(opt_pos[o], []).append(vals[s])
        for j, rows in acc.items():
            x[i, j] = np.mean(rows, axis=0)
            n_sig[i, j] = len(rows)
    OUT.parent.mkdir(exist_ok=True)
    roles = np.array([split["drugs"][d]["role"] for d in drugs])
    gene_names = lm.pr_gene_symbol.astype(str).values
    for path, mask in ((OUT, roles != "confirmation"), (SEALED, roles == "confirmation")):
        np.savez_compressed(path, drug=np.array(drugs)[mask], option=np.array(options), gene=gene_names,
                            x=x[mask], n_sig=n_sig[mask])
    rec = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": GZ.name, "source_sha512": got,
           "output": str(OUT.relative_to(ROOT)).replace("\\", "/"), "output_sha256": file_digest(OUT, "sha256"),
           "sealed": str(SEALED.relative_to(ROOT)).replace("\\", "/"), "sealed_sha256": file_digest(SEALED, "sha256"),
           "n_drug": len(drugs), "n_signatures": len(wanted), "n_genes": int(len(lm)),
           "options_present": int((n_sig > 0).sum()), "n_open": int((roles != "confirmation").sum()),
           "n_sealed": int((roles == "confirmation").sum())}
    (HERE / "EXTRACT_RECEIPT.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    print(main())
