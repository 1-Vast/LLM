"""Beat AML 2.0 feasibility part 3: is the wave shift delta_d structured over drugs (family, readout time, potency)?

LABEL: EXPOSED RELEASED DEVELOPMENT DATA. Pre-declared: delta_d = mean later z of drug d (Waves1+2-standardised AUC, same pool as part 1/2).
Leave-one-drug-out prediction of delta_d from (a) the mean delta of other drugs sharing >=1 target family, (b) readout time (24 h vs 72 h, from raw
time_of_read), (c) Waves1+2 mean raw AUC (potency), (d) a global mean. Reported as the fraction of sum(delta^2) removed. A structure that predicts
delta_d for a drug NOT queried in the later wave is the only thing that could make a structural revision differ from ordinary per-drug refitting.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
D = Path(r"D:/MAESTRO/data/external/beataml2_20261017"); OUT = Path(__file__).parent
fit = pd.read_csv(D/"beataml_probit_curve_fits_v4_dbgap.txt", sep="\t")
clin = pd.read_excel(D/"beataml_wv1to4_clinical.xlsx").drop_duplicates("dbgap_subject_id")
fit["sid"] = fit.dbgap_subject_id.astype(str)+"|"+fit.dbgap_rnaseq_sample.fillna("")+"|"+fit.dbgap_dnaseq_sample.fillna("")
fit = fit.merge(clin[["dbgap_subject_id","cohort"]], on="dbgap_subject_id", how="left")
fit = fit[fit.cohort.isin(["Waves1+2","Waves3+4"])].sort_values(["converged","aic"], ascending=[False,True]).drop_duplicates(["sid","inhibitor"])
cnt = fit.groupby(["inhibitor","cohort"]).sid.nunique().unstack()
pool = sorted(cnt[(cnt["Waves1+2"]>=100)&(cnt["Waves3+4"]>=100)].index)
p = fit[fit.inhibitor.isin(pool)]
A = p.pivot(index="sid", columns="inhibitor", values="auc")[pool]
meta = p.drop_duplicates("sid").set_index("sid").cohort
tr, te = meta.index[meta=="Waves1+2"], meta.index[meta=="Waves3+4"]
Z = (A-A.loc[tr].mean())/A.loc[tr].std()
delta = Z.loc[te].mean(); se = Z.loc[te].std()/np.sqrt(Z.loc[te].notna().sum())
fam = pd.read_excel(D/"beataml_drug_families.xlsx", sheet_name="drug_family")
fam = fam[fam.inhibitor.isin(pool)]
fm = fam.groupby("inhibitor").family.apply(set)
raw = pd.read_csv(D/"beataml_wv1to4_raw_inhibitor_v4_dbgap.txt", sep="\t", usecols=["inhibitor","time_of_read"]).drop_duplicates()
tor = raw[raw.inhibitor.isin(pool)].groupby("inhibitor").time_of_read.agg(lambda x: sorted(set(x)))
rep = {"pool": len(pool), "pool_with_family": int(sum(d in fm.index for d in pool)),
       "readout_times": {str(k): int(v) for k, v in pd.Series([tuple(tor[d]) for d in pool]).value_counts().items()} }
tot = float((delta**2).sum())
def lodo_family():
    pred = pd.Series(0.0, index=pool)
    n_with = 0
    for d in pool:
        mates = [e for e in pool if e != d and d in fm.index and e in fm.index and fm[d] & fm[e]]
        if len(mates) >= 2:
            pred[d] = delta[mates].mean() * len(mates)/(len(mates)+3.0); n_with += 1
    return pred, n_with
pf, nw = lodo_family()
rep["family"] = {"drugs_with_>=2_family_mates": nw, "frac_ss_explained_lodo": float(1-((delta-pf)**2).sum()/tot), "corr": float(np.corrcoef(pf, delta)[0,1])}
# readout time
t72 = pd.Series([1.0 if 72 in tor[d] else 0.0 for d in pool], index=pool)
if t72.nunique() > 1:
    pr = pd.Series(index=pool, dtype=float)
    for d in pool:
        m = t72.drop(d); g = delta.drop(d)
        pr[d] = g[m == t72[d]].mean() if (m == t72[d]).sum() else g.mean()
    rep["readout_time"] = {"n_72h": int(t72.sum()), "frac_ss_explained_lodo": float(1-((delta-pr)**2).sum()/tot)}
# potency and mean level (Waves1+2 mean raw AUC), linear LODO
pot = A.loc[tr].mean(); pot = (pot-pot.mean())/pot.std()
pp = pd.Series(index=pool, dtype=float)
for d in pool:
    o = [e for e in pool if e != d]
    b = np.polyfit(pot[o], delta[o], 1); pp[d] = np.polyval(b, pot[d])
rep["potency"] = {"frac_ss_explained_lodo": float(1-((delta-pp)**2).sum()/tot), "corr": float(np.corrcoef(pp, delta)[0,1])}
rep["global_mean_only"] = float(1-((delta-delta.mean())**2).sum()/tot)
rep["delta_summary"] = {"mean": float(delta.mean()), "sd": float(delta.std()), "mean_se": float(se.mean())}
# sample-level low-rank structure of the later shift: top PCs of later-residual (after removing delta) vs Waves1+2
def pcs(M, k=5):
    M = M.fillna(0).values; M = M-M.mean(0)
    s = np.linalg.svd(M, compute_uv=False); return (s**2/np.sum(s**2))[:k].round(3).tolist()
rep["pc_var_W12"] = pcs(Z.loc[tr]); rep["pc_var_W34"] = pcs(Z.loc[te])
json.dump(rep, open(OUT/"FEASIBILITY3.json","w"), indent=1); print(json.dumps(rep, indent=1))

# --- addendum (pre-declared before reading the output above): decision-relevant (centred) part of the shift ---
dc = delta-delta.mean()
rep2 = {"centred_ss": float((dc**2).sum()), "global_part_ss": float(len(pool)*delta.mean()**2),
        "insample_corr_potency_delta": float(np.corrcoef(pot, delta)[0,1]),
        "insample_corr_potency_delta_centred_same": float(np.corrcoef(pot, dc)[0,1]),
        "lodo_family_centred_frac": float(1-((dc-(pf-pf.mean()))**2).sum()/(dc**2).sum()),
        "lodo_potency_centred_frac": float(1-((dc-(pp-pp.mean()))**2).sum()/(dc**2).sum())}
rep["addendum_centred"] = rep2
json.dump(rep, open(OUT/"FEASIBILITY3.json","w"), indent=1); print(json.dumps(rep2, indent=1))
