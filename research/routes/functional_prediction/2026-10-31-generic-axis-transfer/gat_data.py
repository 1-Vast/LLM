"""Build the development pool and the two confirmation sets of the GAT study (run after the freeze).

Usage: python gat_data.py OUT_DIR [--no-24q2 | --only-24q2]
Writes dev_pool.npz, nci60.npz and prism24q2.npz to OUT_DIR. L1000 inputs come from the frozen extractor
outputs (`l1000_nci.npz`, `l1000_24q2.npz`) in OUT_DIR. The first two files are built before the freeze
(`--no-24q2`); after the freeze only the 24Q2 set is built (`--only-24q2`), so the frozen files are not rewritten.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

RDLogger.DisableLog("rdApp.*")
EXT = Path("D:/MAESTRO/data/external")
NCI_Z = EXT / "nci60_cellminer_20261031/raw/extracted/output/DTP_NCI60_ZSCORE.xlsx"
NCI_RAW = EXT / "nci60_cellminer_20261031/raw/extracted_raw/output/DTP_NCI60_RAW.xlsx"
P24 = EXT / "prism_24q2_20261031"
SEALED = Path("D:/MAESTRO/log/research_records/knowledge_reality_20261013/sealed_compounds.csv")
KILL_PLOG = 5.60          # -log10 GI50 at 2.5 uM, the PRISM dose
ACTIVE_FRACTION = 0.05


def ik14(smiles: str) -> str | None:
    try:
        m = Chem.MolFromSmiles(str(smiles))
        return Chem.MolToInchiKey(m)[:14] if m is not None else None
    except Exception:
        return None


def morgan(smiles: str | None) -> np.ndarray:
    m = Chem.MolFromSmiles(str(smiles)) if isinstance(smiles, str) else None
    if m is None:
        return np.zeros(2048, dtype=np.uint8)
    fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
    return np.frombuffer(fp.ToBitString().encode(), dtype=np.uint8) - ord("0")


def fold_of(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % 10


def dev_pool(out: Path) -> None:
    o = np.load(EXT / "prism_19q4/derived/block_n_prism_open.npz", allow_pickle=True)
    s = np.load(EXT / "prism_19q4/derived/block_n_prism_sealed.npz", allow_pickle=True)
    lo = np.load(EXT / "lincs_l1000_gse92742/derived/block_m_landmark_open.npz", allow_pickle=True)
    ls = np.load(EXT / "lincs_l1000_gse92742/derived/block_m_landmark_sealed.npz", allow_pickle=True)
    drugs = np.concatenate([o["drug"], s["drug"]])
    Y = np.concatenate([o["primary"], s["primary"]]).astype(float)
    ldr = np.concatenate([lo["drug"], ls["drug"]])
    lx = np.concatenate([lo["x"], ls["x"]]).astype(np.float32)
    idx = {d: i for i, d in enumerate(ldr)}
    X = np.stack([lx[idx[d]] for d in drugs])
    t = pd.concat([pd.read_csv(EXT / f"prism_19q4/raw/{n}-screen-replicate-collapsed-treatment-info.csv", dtype=str)
                   for n in ("primary", "secondary")])
    smi = t.dropna(subset=["name", "smiles"]).drop_duplicates("name").set_index("name").smiles
    smiles = [sm.split(",")[0] if isinstance(sm, str) else None for sm in (smi.get(d) for d in drugs)]
    fp = np.stack([morgan(sm) for sm in smiles])
    keys = np.array([(ik14(sm) or "") if sm else "" for sm in smiles])
    np.savez_compressed(out / "dev_pool.npz", drug=drugs, line=o["line"], profile=Y, signature=X,
                        option=lo["option"], fingerprint=fp, ik14=keys)
    print(f"dev pool {len(drugs)} compounds, fingerprints {int((fp.sum(1) > 0).sum())}")


def nci60(out: Path) -> None:
    z = pd.read_excel(NCI_Z, header=8)
    z.columns = [str(c) for c in z.columns]
    lines = [c for c in z.columns if ":" in c]
    z["key"] = z["SMILES d"].map(ik14)
    z = z.dropna(subset=["key"])
    zv = z[lines].replace("na", np.nan).apply(pd.to_numeric, errors="coerce")
    zv["key"] = z["key"].to_numpy()
    prof = zv.groupby("key")[lines].mean()
    prof = prof[prof.notna().sum(axis=1) >= 50]
    smiles = z.drop_duplicates("key").set_index("key")["SMILES d"]
    l1 = np.load(out / "l1000_nci.npz", allow_pickle=True)
    have = np.isfinite(l1["x"][:, :, 0]).any(axis=1)
    keys = [k for k, h in zip(l1["key"], have) if h and k in prof.index]
    nsc_of = z.groupby("key")["NSC # b"].apply(lambda s: sorted(set(s.astype(str))))
    raw = pd.read_excel(NCI_RAW, header=9)
    raw.columns = [str(c) for c in raw.columns]
    raw["NSC"] = raw["NSC #"].astype(str)
    raw = raw[raw["Failure reason"].astype(str).str.strip() == "-"]
    rv = raw[lines].replace("na", np.nan).apply(pd.to_numeric, errors="coerce")
    rv["NSC"] = raw["NSC"].to_numpy()
    active = []
    killed_lines = []
    for k in keys:
        rows = rv[rv.NSC.isin(nsc_of[k])]
        mean_plog = rows[lines].mean(axis=0) if len(rows) else pd.Series(np.nan, index=lines)
        n_killed = int((mean_plog >= KILL_PLOG).sum())
        killed_lines.append(n_killed)
        active.append(n_killed >= int(np.ceil(ACTIVE_FRACTION * len(lines))))
    kidx = {k: i for i, k in enumerate(l1["key"])}
    X = np.stack([l1["x"][kidx[k]] for k in keys]).astype(np.float32)
    fp = np.stack([morgan(smiles.get(k)) for k in keys])
    np.savez_compressed(out / "nci60.npz", key=np.array(keys), line=np.array(lines), profile=prof.loc[keys].to_numpy(),
                        signature=X, option=l1["option"], fingerprint=fp, active=np.array(active),
                        killed_lines=np.array(killed_lines), fold=np.array([fold_of(k) for k in keys]))
    print(f"NCI-60 {len(keys)} compounds, active {int(np.sum(active))}")


def core_of(ids: str) -> str | None:
    m = re.search(r"BRD-[A-Z]\d{8}", str(ids))
    return m.group(0) if m else None


def prism24q2(out: Path) -> None:
    pool = np.load(out / "dev_pool.npz", allow_pickle=True)
    l1 = np.load(out / "l1000_24q2.npz", allow_pickle=True)
    have = np.isfinite(l1["x"][:, :, 0]).any(axis=1)
    ik = pd.read_csv(out / "keys_24q2.tsv", sep="\t", dtype=str).set_index("key")["ik14"]
    in_pool = set(pool["ik14"]) - {""}
    duplicates = [k for k, h in zip(l1["key"], have) if h and ik.get(k) in in_pool]
    cores = {k for k, h in zip(l1["key"], have) if h and k not in duplicates}
    listing = pd.read_csv(P24 / "meta/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv", dtype=str)
    rep1m = set(listing.loc[listing.screen == "REP.1M", "IDs"])           # the 24Q2 extension rows only
    matrix = P24 / "matrix/Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv"
    header = pd.read_csv(matrix, nrows=0).columns.tolist()
    first = header[0]
    if any(str(c).startswith("ACH-") for c in header[1:]):   # rows are treatments
        rows = []
        for chunk in pd.read_csv(matrix, chunksize=500):
            ids = chunk[first].astype(str)
            rows.append(chunk[ids.isin(rep1m) & ids.map(core_of).isin(cores)])
        sub = pd.concat(rows)
        sub["core"] = sub[first].map(core_of)
        n_rows = len(sub)
        prof = sub.drop(columns=[first]).groupby("core").mean()
    else:                                                     # columns are treatments
        cols = [c for c in header[1:] if c in rep1m and core_of(c) in cores]
        sub = pd.read_csv(matrix, usecols=[first] + cols).set_index(first)
        n_rows = len(cols)
        sub.columns = [core_of(c) for c in sub.columns]
        prof = sub.T.groupby(level=0).mean()
    lines = [ln for ln in pool["line"] if ln in prof.columns]
    keys = [str(c) for c in l1["key"] if c in cores and c in prof.index]
    Yq = prof.loc[keys, lines].to_numpy(dtype=float)
    active = np.nanmean(Yq <= -1.0, axis=1) >= ACTIVE_FRACTION
    kidx = {k: i for i, k in enumerate(l1["key"])}
    X = np.stack([l1["x"][kidx[k]] for k in keys]).astype(np.float32)
    sealed = pd.read_csv(SEALED, dtype=str).drop_duplicates("core").set_index("core")
    fp = np.stack([morgan(sealed.smiles.get(k)) for k in keys])
    np.savez_compressed(out / "prism24q2.npz", key=np.array(keys), line=np.array(lines), profile=Yq, signature=X,
                        option=l1["option"], fingerprint=fp, active=active, parsed_treatments=n_rows,
                        dropped_in_pool=np.array(duplicates, dtype=str))
    print(f"24Q2 {len(keys)} compounds ({n_rows} treatments parsed, {len(duplicates)} dropped as pool duplicates), "
          f"lines {len(lines)}, active {int(active.sum())}")


if __name__ == "__main__":
    target = Path(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    if mode in ("all", "--no-24q2"):
        dev_pool(target)
        nci60(target)
    if mode in ("all", "--only-24q2"):
        prism24q2(target)
