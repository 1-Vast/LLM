"""FAR arena: PRISM 19Q4 primary log-fold-change (HTS, 2.5 uM) x L1000 landmark signatures (block-Q phase-1 array, 9 lines) x ECFP4.

Tiers: 'dev' = overlap minus the 421 block-N sealed drug names; 'vault' = overlap restricted to those names (block N opened them once, so a
vault check is a reuse check, never independent confirmation of selection). Folds are MoA-family folds (sha256 hash of the family label).
Identity key = first 13 characters of the Broad id; structure identity not verified.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
RDLogger.DisableLog("rdApp.*")
EXT = Path(__file__).resolve().parents[2] / "data" / "external"
RAW = EXT / "prism_19q4/raw"
L1 = EXT / "lincs_l1000_gse92742"


def fold_of(moa, n=5):
    return int(hashlib.sha256(("far20261019|" + moa).encode()).hexdigest()[:8], 16) % n


def load(tier: str):
    ti = pd.read_csv(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    ti = ti[ti.column_name.str.endswith("::HTS")].copy()
    ti["cmp"] = ti.broad_id.str[:13]
    ti = ti.drop_duplicates("cmp")
    lfc = pd.read_csv(RAW / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    Q = np.load(L1 / "derived/blockq_phase1.npz", allow_pickle=True)
    sealed = {str(d).lower() for d in np.load(EXT / "prism_19q4/derived/block_n_prism_sealed.npz", allow_pickle=True)["drug"]}
    qi = {str(p): i for i, p in enumerate(Q["pert_ids"])}
    rows = []
    for r in ti.itertuples():
        if r.cmp in qi and r.column_name in lfc.columns and isinstance(r.smiles, str):
            nm = str(r.name).lower()
            if (nm in sealed) == (tier == "vault"):
                rows.append((r.cmp, r.column_name, nm, ("" if not isinstance(r.moa, str) or r.moa == "NA" else r.moa.split(",")[0].strip()), r.smiles))
    keep = []
    fps, drug, moa, cols, qidx = [], [], [], [], []
    for cmp_, col, nm, mo, smi in rows:
        m = Chem.MolFromSmiles(smi.split(", ")[0])
        if m is None or (Q["n_sig"][qi[cmp_]] > 0).sum() < 4:
            continue
        fps.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048)); drug.append(nm); moa.append(mo); cols.append(col); qidx.append(qi[cmp_])
    n = len(drug)
    T = np.zeros((n, n))
    for i in range(n):
        T[i] = DataStructs.BulkTanimotoSimilarity(fps[i], fps)
    Y = lfc[cols].to_numpy(dtype=np.float64).T          # drugs x lines
    X = Q["cp"][qidx].astype(np.float64)               # drugs x 9 lines x 978
    X[Q["n_sig"][qidx] == 0] = np.nan
    moa = np.array(moa)
    # family = union of shared MoA label and Tanimoto >= 0.5 connectivity (unlabelled compounds join by chemistry)
    par = list(range(n))
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    first = {}
    for i in range(n):
        if moa[i]:
            if moa[i] in first: par[f(i)] = f(first[moa[i]])
            else: first[moa[i]] = i
        for j in np.where(T[i] >= 0.5)[0]:
            par[f(i)] = f(j)
    fam = np.array([str(min(k for k in range(n) if f(k) == f(i))) for i in range(n)])
    return dict(drug=np.array(drug), moa=moa, family=fam, Y=Y, X=X, T=T, fold=np.array([fold_of(m) for m in fam]), lines=np.array(lfc.index), l1000_lines=list(Q["line"]))


def selective(Y, ref):
    """Selective residual: drop each compound's mean killing and the reference-mean line profile (generic profile)."""
    Z = Y - np.nanmean(Y, axis=1, keepdims=True)
    return Z - np.nanmean(Z[ref], axis=0, keepdims=True)


if __name__ == "__main__":
    for t in ("dev", "vault"):
        d = load(t); print(t, len(d["drug"]), len(set(d["family"])), np.bincount(d["fold"]), d["Y"].shape, d["X"].shape, np.isnan(d["Y"]).mean())
