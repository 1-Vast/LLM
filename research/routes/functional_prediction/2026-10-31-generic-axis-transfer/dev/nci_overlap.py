import pandas as pd, numpy as np
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
x = pd.read_excel(r"D:/MAESTRO/data/external/nci60_cellminer_20261031/raw/extracted/output/DTP_NCI60_ZSCORE.xlsx", header=8)
x.columns = [str(c) for c in x.columns]
print(x.shape, x.columns[:7].tolist())
lines = [c for c in x.columns if ":" in c]
print("lines", len(lines))
Z = x[lines].replace("na", np.nan).apply(pd.to_numeric, errors="coerce")
x["n_lines"] = Z.notna().sum(1)
x["z_sd"] = Z.std(1)
def ik(s):
    try:
        m = Chem.MolFromSmiles(str(s))
        return Chem.MolToInchiKey(m)[:14] if m is not None else None
    except Exception:
        return None
x["ik14"] = x["SMILES d"].map(ik)
print("NCI rows", len(x), "with ik", x.ik14.notna().sum(), ">=50 lines", (x.n_lines >= 50).sum())
p = pd.read_csv(r"D:/MAESTRO/data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t")
p = p[p.pert_type == "trt_cp"]
s = pd.read_csv(r"D:/MAESTRO/data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", usecols=["sig_id", "pert_id", "pert_type", "cell_id", "pert_idose", "pert_itime"])
s = s[s.pert_type == "trt_cp"]
core = {"A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP"}
s = s[s.cell_id.isin(core) & s.pert_itime.isin(["6 h", "24 h"])]
p = p.merge(s.groupby("pert_id").size().rename("n_sig").reset_index(), on="pert_id", how="inner")
lk = set(p.inchi_key_prefix.dropna())
x["in_l1000"] = x.ik14.isin(lk)
ok = x[(x.n_lines >= 50) & x.in_l1000]
print("NCI compounds with >=50 lines AND L1000 core-line signatures:", len(ok), " unique ik14:", ok.ik14.nunique())
print("  of which z_sd>0.5 (non-flat):", (ok.z_sd > 0.5).sum())
blockn = set(np.load(r"D:/MAESTRO/data/external/prism_19q4/derived/block_n_prism_open.npz", allow_pickle=True)["drug"]) | set(np.load(r"D:/MAESTRO/data/external/prism_19q4/derived/block_n_prism_sealed.npz", allow_pickle=True)["drug"])
nm = p.set_index("inchi_key_prefix").pert_iname
ok_names = ok.ik14.map(lambda k: nm.get(k) if not isinstance(nm.get(k), pd.Series) else nm.get(k).iloc[0])
print("  of which name in Block N PRISM pool:", ok_names.isin(blockn).sum())
print(s[s.pert_id.isin(p[p.inchi_key_prefix.isin(ok.ik14)].pert_id)].pert_idose.value_counts().head(8))
