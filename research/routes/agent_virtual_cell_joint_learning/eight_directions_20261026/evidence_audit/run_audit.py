"""Fresh minimum attempts, directions 4 and 5. Never reads old sealed responses."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd
import h5py
ROOT=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  while b:=f.read(1<<20): h.update(b)
 return h.hexdigest()

p=ROOT/"raw/PAIR_SCREEN.csv"
d=pd.read_csv(p,low_memory=False)
raw_count=len(d); qc_failed=int(d["Failed QC"].sum());d=d[~d["Failed QC"]].copy()
controls={"dmso","high control","low control"}
# Real measured wells in both equivalent orientations; do not duplicate any orientation within a grouping.
cols=["Cell line","Iteration","file","Well","Viability"]
a=d[cols].copy();b=d[cols].copy()
for frame,rev in [(a,False),(b,True)]:
 frame["replacement"]=d["Drug 2" if rev else "Drug 1"].values
 frame["partner"]=d["Drug 1" if rev else "Drug 2"].values
 frame["replacement_dose"]=d["Conc 2 (uM)" if rev else "Conc 1 (uM)"].values
 frame["partner_dose"]=d["Conc 1 (uM)" if rev else "Conc 2 (uM)"].values
oriented=pd.concat([a,b],ignore_index=True)
keys=["Cell line","Iteration","partner","partner_dose","replacement_dose"]
# Partner monotherapy measured with DMSO in the replacement slot, retaining iteration.
mono=oriented[oriented.replacement.eq("dmso") & ~oriented.partner.isin(controls)]
mono=mono.groupby(["Cell line","Iteration","partner","partner_dose"]).Viability.mean().to_dict()
combo=oriented[(~oriented.replacement.isin(controls)) & (~oriented.partner.isin(controls)) & oriented.replacement.ne(oriented.partner)]
summary=combo.groupby(keys+["replacement"]).agg(mean=("Viability","mean"),n=("Viability","size"),nfiles=("file","nunique")).reset_index()
counts={"matched_comparisons":0,"both_at_least_3_wells":0,"both_at_least_3_files":0,"matched_partner_monotherapy":0,"nontrivial_mean_comparisons":0,"qualified_equivalence_tests":0}
for k,g in summary.groupby(keys):
 n=len(g);counts["matched_comparisons"]+=n*(n-1)//2
 v=g["mean"].to_numpy();nr=g.n.to_numpy();nf=g.nfiles.to_numpy()
 for _,i in enumerate(range(n)):
  mask=np.arange(n)>i
  counts["both_at_least_3_wells"]+=int(np.sum(mask & (nr[i]>=3) & (nr>=3)))
  counts["both_at_least_3_files"]+=int(np.sum(mask & (nf[i]>=3) & (nf>=3)))
 m=mono.get(k[:4])
 if m is not None:
  counts["matched_partner_monotherapy"]+=n*(n-1)//2
  elig=(v>0.1)&(v<0.9)&((m-v)>=0.1)
  e=int(elig.sum());counts["nontrivial_mean_comparisons"]+=e*(e-1)//2
counts["maximum_files_per_condition"]=int(summary.nfiles.max())
counts["maximum_wells_per_condition"]=int(summary.n.max())
# File identity is at most a lower-level replicate identifier, not proof of biological independence.
r5={"source":"https://zenodo.org/records/13871987","source_sha256":sha(p),"source_bytes":p.stat().st_size,"raw_rows":raw_count,"qc_failed":qc_failed,"qc_pass":len(d),"cell_line_labels":sorted(d["Cell line"].unique()),"oriented_condition_groups":len(summary),"counts":counts,"status":"blocked_at_replication_gate","reason":"Under fixed cell, partner, both concentrations and iteration, no comparison has >=3 distinct measurement files per arm. Some groups have >=3 wells but only <=2 files; wells cannot be treated as independent biological replicates. Equivalence CI/TOST was therefore not run. Descriptive nontrivial counts are not equivalence results.","limits":["No time/exposure column is provided; iteration and file matching cannot prove all exposure conditions identical.","0.1 is an exploratory margin, not externally validated assay tolerance.","Design comparisons share arms and are not independent hypotheses.","This does not refute conditional substitution as a biological possibility."]}

f=h5py.File("data/external/mixseq_scperturb/mcfarland_2020.h5ad","r")
def obs(k):
 z=f["obs"][k]
 if isinstance(z,h5py.Group):
  c=np.array([x.decode() if isinstance(x,bytes) else str(x) for x in z["categories"][:]])
  codes=z["codes"][:];return np.where(codes>=0,c[np.maximum(codes,0)],"missing")
 return z[:]
meta=pd.DataFrame({k:obs(k) for k in ["time","perturbation","perturbation_type","cell_line","channel"]})
ct=meta.groupby(["time","perturbation_type"]).size(); tcounts={str(k):int(v) for k,v in meta.time.value_counts().items()}
ct.reset_index(name="cells").to_csv(ROOT/"mixseq_time_census.csv",index=False)
meta.groupby(["time","perturbation","cell_line","channel"]).size().reset_index(name="cells").to_csv(ROOT/"mixseq_design_census.csv",index=False)
f.close()
t=np.linspace(0,1,1001);x1=t;x2=t+np.sin(2*np.pi*t)/(4*np.pi)
assert np.allclose(x1[[0,-1]],x2[[0,-1]])
assert np.all(np.diff(x1)>0) and np.all(np.diff(x2)>0)
assert np.max(np.abs(x1-x2))>0.07
r4={"source":"data/external/mixseq_scperturb/mcfarland_2020.h5ad","metadata_rows":len(meta),"time_labels":tcounts,"expression_or_outcomes_read":False,"analytic_check":{"trajectories":["x1(t)=t","x2(t)=t+sin(2*pi*t)/(4*pi)"],"endpoints_equal":True,"both_monotone":True,"maximum_internal_gap":float(np.max(np.abs(x1-x2))),"gap_at_t_0_25":float(x2[250]-x1[250]),"interpretation":"Distinct admissible monotone trajectories share endpoint measurements. Endpoint fit alone cannot identify a unique dynamic mechanism."},"status":"analytic_check_passed_biological_identification_unestablished","reason":"Metadata has multi-time labels, some pooled strings (3, 6, 12, 24, 48; 72, 96), so this resource must not be dismissed as purely single-time. However cells are destructive snapshots; pooled time labels cannot be converted to individual exact times, and no independently verified pair of competing mechanism models or intervention-specific mechanistic truth has been established. No biological dynamic identification experiment is claimed."}
(ROOT/"direction4_results.json").write_text(json.dumps(r4,indent=2,ensure_ascii=False),encoding="utf-8")
(ROOT/"direction5_results.json").write_text(json.dumps(r5,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({"direction4":r4,"direction5":r5},indent=2,ensure_ascii=False))
