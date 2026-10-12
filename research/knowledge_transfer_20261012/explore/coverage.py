"""Pre-registration coverage census: counts and annotation coverage only, no outcome performance."""
import json
import pandas as pd
import numpy as np

ROOT = "data/external/"
CORE = ["PC3", "MCF7", "A375", "HA1E", "VCAP", "A549", "HEPG2", "HT29", "HCC515"]
s = pd.read_csv(ROOT + "lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", low_memory=False)
p = pd.read_csv(ROOT + "lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", low_memory=False)
print("pert_info cols", list(p.columns))
cp = s[(s.pert_type == "trt_cp") & s.cell_id.isin(CORE)]
print("trt_cp core sigs", len(cp))
print(cp.pert_idose.value_counts().head(8))
print(cp.pert_itime.value_counts().head(5))
std = cp[(cp.pert_idose.isin(["10 µM", "10.0 um", "10 um"])) & (cp.pert_itime == "24 h")]
print("10uM 24h sigs", len(std), "unique perts", std.pert_id.nunique())
per = std.groupby("pert_id").cell_id.nunique()
print("lines per pert at 10uM/24h:", per.value_counts().sort_index().to_dict())
rep = std.groupby(["pert_id", "cell_id"]).size()
print("sigs per (pert,line) at 10uM/24h:", rep.value_counts().sort_index().head(8).to_dict())
sh = s[(s.pert_type == "trt_sh.cgs") & s.cell_id.isin(CORE)]
print("trt_sh.cgs genes per line:", sh.groupby("cell_id").pert_iname.nunique().to_dict())
print("trt_sh.cgs times:", sh.pert_itime.value_counts().to_dict())
hub = pd.read_csv(ROOT + "lincs_l1000_gse92742/repurposing_drugs_20200324.txt", sep="\t", comment="!")
print("hub cols", list(hub.columns), len(hub))
names = p.set_index("pert_id").pert_iname
std_names = std.pert_iname.str.lower().unique()
hubn = hub.assign(n=hub.pert_iname.str.lower()).set_index("n")
annotated = [n for n in std_names if n in hubn.index and isinstance(hubn.loc[n, "target"], str)]
print("std perts with hub target:", len(annotated), "of", len(std_names))
shgenes = set(sh.pert_iname.unique())
def tg(n):
    t = hubn.loc[n, "target"]
    if isinstance(t, pd.Series):
        t = t.iloc[0]
    return [x for x in str(t).split("|") if x]
cov = [n for n in annotated if any(g in shgenes for g in tg(n))]
print("annotated with >=1 target having a KD consensus in some core line:", len(cov))
# phase 2
z = np.load(ROOT + "lincs_l1000_phase2/derived/block_p_phase2_landmark.npz", allow_pickle=True)
print("phase2 lines", z["line"].tolist(), "doses", z["dose"].tolist(), "roles", pd.Series(z["role"]).value_counts().to_dict())
n_sig = z["n_sig"]
has10 = (n_sig[:, :, list(z["dose"]).index("10 uM") if "10 uM" in list(z["dose"]) else -1] > 0)
print("phase2 compounds x lines with 10uM:", has10.sum(), "compounds with >=1 line:", (has10.sum(1) > 0).sum())
p1_names = set(n for n in std.pert_iname.str.lower().unique())
p2_names = [str(x).lower() for x in z["name"]]
new2 = [n for n in p2_names if n not in p1_names]
print("phase2 compounds absent from phase1 10uM/24h core set:", len(new2), "of", len(p2_names))
p2t = [t for t in z["target"] if str(t).strip()]
print("phase2 with target annotation:", len(p2t))
