"""Beat AML 2.0 feasibility part 2: what explains the wave shift, and is it separable by one observation?

LABEL: EXPOSED RELEASED DEVELOPMENT DATA (see feasibility.py). Same pool, endpoint and standardisation as part 1
(116 drugs measured in >=100 samples of both waves with identical dose ranges; AUC z-scored with Waves1+2 mean/sd).
Pre-declared candidate explanations for the same observation (a later-sample drug measurement):
  H_comp   composition shift: the Waves1+2 response model is right given clinical/genotype covariates
           (FLT3-ITD, NPM1, RUNX1, ASXL1, TP53, specimen type, disease stage, ELN2017 risk, age, log WBC);
           the wave shift is only the later cohort having different covariates.
  H_time   smooth assay/run drift: per-drug slope on run_index learned inside Waves1+2 only extrapolates.
  H_step   per-drug step offsets between waves (re-estimated from later data) - the ordinary refit.
Chronological check: later samples ordered by median run_index, offset estimated only from earlier-run later samples.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(r"D:/MAESTRO/data/external/beataml2_20261017")
OUT = Path(__file__).parent
rng = np.random.default_rng(20261021)

fit = pd.read_csv(D / "beataml_probit_curve_fits_v4_dbgap.txt", sep="\t")
clin = pd.read_excel(D / "beataml_wv1to4_clinical.xlsx").drop_duplicates("dbgap_subject_id")
fit["sid"] = (fit.dbgap_subject_id.astype(str) + "|" + fit.dbgap_rnaseq_sample.fillna("") + "|" + fit.dbgap_dnaseq_sample.fillna(""))
fit = fit.merge(clin[["dbgap_subject_id", "cohort"]], on="dbgap_subject_id", how="left")
fit = fit[fit.cohort.isin(["Waves1+2", "Waves3+4"])].sort_values(["converged", "aic"], ascending=[False, True])
fit = fit.drop_duplicates(["sid", "inhibitor"])
cnt = fit.groupby(["inhibitor", "cohort"]).sid.nunique().unstack()
pool = sorted(cnt[(cnt["Waves1+2"] >= 100) & (cnt["Waves3+4"] >= 100)].index)
p = fit[fit.inhibitor.isin(pool)]
A = p.pivot(index="sid", columns="inhibitor", values="auc")[pool]
meta = p.drop_duplicates("sid").set_index("sid")[["cohort", "dbgap_subject_id"]]
tr = meta.index[meta.cohort == "Waves1+2"]
te = meta.index[meta.cohort == "Waves3+4"]
Z = (A - A.loc[tr].mean()) / A.loc[tr].std()

# run index per sample (median over its raw runs)
ri = pd.read_csv(D / "beataml_wv1to4_raw_inhibitor_v4_dbgap.txt", sep="\t",
                 usecols=["dbgap_subject_id", "dbgap_rnaseq_sample", "dbgap_dnaseq_sample", "run_index"]).drop_duplicates()
ri["sid"] = ri.dbgap_subject_id.astype(str) + "|" + ri.dbgap_rnaseq_sample.fillna("") + "|" + ri.dbgap_dnaseq_sample.fillna("")
run = ri.groupby("sid").run_index.median()

# covariates
c = clin.set_index("dbgap_subject_id")
X = pd.DataFrame(index=c.index)
for col in ["FLT3-ITD", "NPM1", "RUNX1", "ASXL1", "TP53"]:
    X[col] = (c[col] == "positive").astype(float)
X["BM"] = (c.specimenType == "Bone Marrow Aspirate").astype(float)
X["PB"] = (c.specimenType == "Peripheral Blood").astype(float)
for s in ["Initial Diagnosis", "Residual", "Relapse", "Remission"]:
    X["stage_" + s] = (c.diseaseStageAtSpecimenCollection == s).astype(float)
for s in ["Adverse", "Favorable", "Intermediate"]:
    X["eln_" + s] = (c.ELN2017 == s).astype(float)
age = pd.to_numeric(c.ageAtSpecimenAcquisition, errors="coerce")
X["age"] = (age - age.mean()) / age.std()
X["logwbc"] = np.log1p(pd.to_numeric(c.wbcCount, errors="coerce"))
X["logwbc"] = (X.logwbc - X.logwbc.mean()) / X.logwbc.std()
X = X.fillna(0.0)
Xs = X.loc[meta.dbgap_subject_id].set_index(meta.index)

rep = {"n_train": int(len(tr)), "n_later": int(len(te)), "pool": len(pool)}
delta = Z.loc[te].mean()
tot_ss = float((delta ** 2).sum())
rep["observed_shift"] = {"sum_sq": tot_ss, "mean_abs": float(delta.abs().mean())}

# covariate shift
cov_shift = (Xs.loc[te].mean() - Xs.loc[tr].mean())
rep["covariate_shift_largest"] = {k: float(v) for k, v in cov_shift.abs().sort_values(ascending=False).head(6).items()}


def ridge(Xa, Ya, alpha):
    xm = Xa.mean(0)
    ym = np.nanmean(Ya, axis=0)
    Y0 = np.where(np.isnan(Ya), ym, Ya) - ym
    Xc = Xa - xm
    W = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(Xa.shape[1]), Xc.T @ Y0)
    return xm, ym, W


mc = ridge(Xs.loc[tr].values, Z.loc[tr].values, 10.0)
predc = mc[1] + (Xs.loc[te].values - mc[0]) @ mc[2]
d_comp = pd.Series(predc.mean(axis=0), index=pool)
rep["H_comp"] = {
    "corr_with_observed_shift": float(np.corrcoef(d_comp, delta)[0, 1]),
    "frac_shift_ss_explained": float(1 - ((delta - d_comp) ** 2).sum() / tot_ss),
}
# time trend learned in Waves1+2 only, extrapolated
r_tr = run.reindex(tr).values
mr, sr = np.nanmean(r_tr), np.nanstd(r_tr)
tz = (r_tr - mr) / sr
slopes = []
for j, d in enumerate(pool):
    y = Z.loc[tr, d].values
    m = ~np.isnan(y) & ~np.isnan(tz)
    slopes.append(np.polyfit(tz[m], y[m], 1)[0])
slopes = np.array(slopes)
tz_te = (run.reindex(te).values - mr) / sr
d_time = pd.Series(slopes * np.nanmean(tz_te), index=pool)
rep["H_time"] = {
    "mean_extrapolated_run_z": float(np.nanmean(tz_te)),
    "mean_abs_slope_per_sd_run": float(np.abs(slopes).mean()),
    "corr_with_observed_shift": float(np.corrcoef(d_time, delta)[0, 1]),
    "frac_shift_ss_explained": float(1 - ((delta - d_time) ** 2).sum() / tot_ss),
}
rep["H_comp_plus_time_frac_explained"] = float(1 - ((delta - d_comp - d_time) ** 2).sum() / tot_ss)

# residual after composition: per-drug, is it a family-level (shared) shift?
resid = delta - d_comp
sd_res = (Z.loc[te].values - predc)
sig = pd.Series(np.nanstd(sd_res, axis=0), index=pool)
n_obs = Z.loc[te].notna().sum()
dprime = (resid.abs() / sig)
rep["single_observation_separability"] = {
    "median_abs_resid_shift_over_resid_sd": float(dprime.median()),
    "p90": float(dprime.quantile(0.9)),
    "later_samples_for_80pct_power_alpha05_median": float(((1.96 + 0.84) ** 2 / dprime ** 2).median()),
    "frac_drugs_where_detectable_with_le_60_later_samples": float(((1.96 + 0.84) ** 2 / dprime ** 2 <= 60).mean()),
    "frac_drugs_where_detectable_with_le_1_sample": float(((1.96 + 0.84) ** 2 / dprime ** 2 <= 1).mean()),
}
# H_comp vs H_step prediction difference per observation relative to noise
diff = (delta - d_comp).abs() / sig
rep["H_comp_vs_H_step_dprime_per_observation"] = {"median": float(diff.median()), "p90": float(diff.quantile(0.9))}

# --- chronology: order later samples by run index; offsets learned only from earlier-run later samples ---
# decision utility with the k=0 conventional predictor (ridge on covariates, Waves1+2) + online offset
te_sorted = run.reindex(te).sort_values().index
Zt = Z.loc[te_sorted]
Pc = pd.DataFrame(predc, index=te, columns=pool).loc[te_sorted]
res = {"stationary_cov": [], "online_offset": [], "online_offset_cov": [], "stationary_zero": [], "random": [], "oracle": []}
ids = []
warm = 30
for t in range(warm, len(te_sorted)):
    prev = Zt.iloc[:t]
    base_prev = Pc.iloc[:t]
    n = prev.notna().sum()
    off_cov = ((prev - base_prev).mean()).fillna(0) * (n / (n + 10.0))   # shift beyond composition
    off_raw = prev.mean().fillna(0) * (n / (n + 10.0))                    # shift in raw z
    z = Zt.iloc[t]
    obs = z.notna()
    if obs.sum() < 60:
        continue
    true = z[obs].values
    pc = Pc.iloc[t][obs].values
    res["random"].append(-true.mean())
    res["oracle"].append(-np.sort(true)[:5].mean())
    res["stationary_zero"].append(-true.mean())
    res["stationary_cov"].append(-true[np.argsort(pc)[:5]].mean())
    res["online_offset"].append(-true[np.argsort(off_raw[obs].values)[:5]].mean())
    res["online_offset_cov"].append(-true[np.argsort((pc + off_cov[obs].values))[:5]].mean())
    ids.append(meta.loc[te_sorted[t], "dbgap_subject_id"])


def boot(v, ids, B=400):
    v = np.asarray(v); ids = np.asarray(ids); us = np.unique(ids)
    ix = {u: np.where(ids == u)[0] for u in us}
    o = [np.mean(np.concatenate([v[ix[u]] for u in rng.choice(us, len(us))])) for _ in range(B)]
    return [float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5))]


rep["prequential_k0"] = {"n_decisions": len(ids), "n_subjects": int(len(set(ids)))}
for k_, v in res.items():
    rep["prequential_k0"][k_] = float(np.mean(v))
for a, b in [("online_offset_cov", "stationary_cov"), ("online_offset", "stationary_cov"), ("online_offset_cov", "online_offset")]:
    d = np.array(res[a]) - np.array(res[b])
    rep["prequential_k0"][f"{a}-{b}"] = {"mean": float(d.mean()), "ci95_cluster_boot": boot(d, ids)}
bc = np.array(res["random"])
rep["prequential_k0"]["frac_oracle_gain_online_offset_cov"] = float((np.array(res["online_offset_cov"]) - bc).mean() / (np.array(res["oracle"]) - bc).mean())
rep["prequential_k0"]["frac_oracle_gain_stationary_cov"] = float((np.array(res["stationary_cov"]) - bc).mean() / (np.array(res["oracle"]) - bc).mean())

with open(OUT / "FEASIBILITY2.json", "w") as fh:
    json.dump(rep, fh, indent=1)
print(json.dumps(rep, indent=1))
