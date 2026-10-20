"""Part 4 (pre-declared, minimal): is the Waves1+2 -> Waves3+4 shift a continuation of drift already visible inside Waves1+2?

LABEL: EXPOSED RELEASED DEVELOPMENT DATA. Same pool/standardisation as parts 1-3. Within Waves1+2 only, per-drug difference between the later and
earlier half of samples ordered by median run_index (early-vs-late), centred over drugs (the global part cannot change a ranking). Reported:
correlation with the centred Waves3+4 shift, and the R^2 of the best single scale factor (an upper bound; the scale is fitted on the outcome
here and is therefore NOT a usable forecast).  Also: panel/plate coverage of the shift (not tested: no labelled assay-condition variable).
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
ri = pd.read_csv(D/"beataml_wv1to4_raw_inhibitor_v4_dbgap.txt", sep="\t", usecols=["dbgap_subject_id","dbgap_rnaseq_sample","dbgap_dnaseq_sample","run_index"]).drop_duplicates()
ri["sid"] = ri.dbgap_subject_id.astype(str)+"|"+ri.dbgap_rnaseq_sample.fillna("")+"|"+ri.dbgap_dnaseq_sample.fillna("")
run = ri.groupby("sid").run_index.median().reindex(tr).sort_values()
half = len(run)//2
early, late = run.index[:half], run.index[half:]
d_el = Z.loc[late].mean()-Z.loc[early].mean()
d_w = Z.loc[te].mean()
c1, c2 = d_el-d_el.mean(), d_w-d_w.mean()
b = float((c1*c2).sum()/(c1*c1).sum())
rep = {"early_n": len(early), "late_n": len(late), "run_index_split": float(run.iloc[half]),
       "corr_centred_late_minus_early_vs_W34_shift": float(c1.corr(c2)),
       "best_scale": b, "R2_at_best_scale_upper_bound": float(1-((c2-b*c1)**2).sum()/(c2**2).sum()),
       "sign_agreement_frac": float((np.sign(c1)==np.sign(c2)).mean()),
       "mean_abs_within_W12_drift": float(d_el.abs().mean())}
# split-half reliability of the shift itself (noise floor): random half of W34 samples vs the other half
rng = np.random.default_rng(1); rs=[]
for _ in range(200):
    idx = rng.permutation(len(te)); a, bb = te[idx[:len(te)//2]], te[idx[len(te)//2:]]
    x, y = Z.loc[a].mean(), Z.loc[bb].mean(); rs.append((x-x.mean()).corr(y-y.mean()))
rep["W34_split_half_corr_of_centred_shift"] = float(np.mean(rs))
json.dump(rep, open(OUT/"FEASIBILITY4.json","w"), indent=1); print(json.dumps(rep, indent=1))
