import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
pert = pd.read_csv(r"D:/MAESTRO/data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str)
pert = pert[pert.pert_type == "trt_cp"]
# (a) validation sample from Block M names (unique name -> single ik14)
bm = np.load(r"D:/MAESTRO/data/external/lincs_l1000_gse92742/derived/block_m_landmark_open.npz", allow_pickle=True)
g = pert.groupby("pert_iname").inchi_key_prefix.agg(lambda s: sorted(set(s.dropna())))
names = [d for d in bm["drug"] if d in g.index and len(g[d]) == 1]
rng = np.random.default_rng(3)
pick = rng.choice(names, 120, replace=False)
pd.DataFrame({"key": pick, "ik14": [g[d][0] for d in pick]}).to_csv("keys_blockm_check.tsv", sep="\t", index=False)
# (b) NCI-60 overlap keys
x = pd.read_excel(r"D:/MAESTRO/data/external/nci60_cellminer_20261031/raw/extracted/output/DTP_NCI60_ZSCORE.xlsx", header=8)
x.columns = [str(c) for c in x.columns]
lines = [c for c in x.columns if ":" in c]
Z = x[lines].replace("na", np.nan).apply(pd.to_numeric, errors="coerce")
x["n_lines"] = Z.notna().sum(1)
def ik(s):
    try:
        m = Chem.MolFromSmiles(str(s)); return Chem.MolToInchiKey(m)[:14] if m is not None else None
    except Exception:
        return None
x["ik14"] = x["SMILES d"].map(ik)
x[["NSC # b", "Drug name", "Mechanism of action c", "SMILES d", "ik14", "n_lines"]].to_csv("nci_ik14.tsv", sep="\t", index=False)
lk = set(pert.inchi_key_prefix.dropna())
ok = x[(x.n_lines >= 50) & x.ik14.isin(lk)]
pd.DataFrame({"key": sorted(ok.ik14.unique()), "ik14": sorted(ok.ik14.unique())}).to_csv("keys_nci.tsv", sep="\t", index=False)
print("blockm check keys", len(pick), " nci keys", ok.ik14.nunique())
