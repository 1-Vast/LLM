"""Beat AML 2.0 feasibility check for a measured self-repair unit.

LABEL: EXPOSED RELEASED DEVELOPMENT DATA. Beat AML was already used by context_transfer_20261017 and
feedback_attribution_20261017. Nothing here is independent confirmation, and nothing here selects a threshold
for a later test. It only measures whether the observation unit, headroom and separability required by the
qualification brief exist. No API, no network, no data outside data/external/beataml2_20261017.

Pre-declared before the first numeric output (the choices below were not tuned on the outcomes):
  pool      single-agent drugs fitted in >=100 samples of BOTH Waves1+2 (train) and Waves3+4 (later) and whose
            fitted dose range (min_conc, max_conc) is identical in both waves.
  endpoint  probit-fit AUC from the released fit file (lower = more sensitive), standardised per drug with
            Waves1+2 mean/sd (so drift shows as a shift).
  decision  after k battery queries on a later sample, nominate the 5 unqueried pool drugs with the lowest
            predicted z; utility U = -mean(true z of the nominated drugs). Oracle nominates by true z.
  battery   first k drugs of a fixed order built on Waves1+2 only (greedy by summed squared correlation).
  models    M0 drug means; M1 ridge(alpha=10) from battery trained on Waves1+2 (fixed model);
            M2 = M1 + per-drug offset estimated on other later subjects (shrunk n/(n+10)) (drift refit);
            M3 = M1 + sample offset estimated from the battery residual (global shift);
            M4 = M1 + both.  5 subject-grouped folds over later subjects.
  noise     replicate-well trapezoid AUC differences (technical noise), in z units.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(r"D:/MAESTRO/data/external/beataml2_20261017")
OUT = Path(__file__).parent
rng = np.random.default_rng(20261020)

fit = pd.read_csv(D / "beataml_probit_curve_fits_v4_dbgap.txt", sep="\t")
clin = pd.read_excel(D / "beataml_wv1to4_clinical.xlsx")
fit["sid"] = (fit.dbgap_subject_id.astype(str) + "|" + fit.dbgap_rnaseq_sample.fillna("") + "|"
              + fit.dbgap_dnaseq_sample.fillna(""))
fit = fit.merge(clin[["dbgap_subject_id", "cohort"]].drop_duplicates("dbgap_subject_id"),
                on="dbgap_subject_id", how="left")
fit = fit[fit.cohort.isin(["Waves1+2", "Waves3+4"])].copy()
# one fit per (sample, drug): keep the converged one with the lowest AIC
fit = fit.sort_values(["converged", "aic"], ascending=[False, True]).drop_duplicates(["sid", "inhibitor"])

rep = {}
# dose range identity across waves
rng_ok = fit.groupby("inhibitor").apply(
    lambda g: g.groupby("cohort")[["min_conc", "max_conc"]].agg(lambda x: tuple(sorted(set(np.round(x, 4))))).nunique().max() == 1
    if g.cohort.nunique() == 2 else False)
cnt = fit.groupby(["inhibitor", "cohort"]).sid.nunique().unstack()
cand = cnt[(cnt["Waves1+2"] >= 100) & (cnt["Waves3+4"] >= 100)].index
range_same = [d for d in cand if bool(rng_ok.get(d, False))]
rep["drugs_both_waves_ge100"] = int(len(cand))
rep["drugs_same_dose_range"] = int(len(range_same))
rep["drugs_dropped_for_range_mismatch"] = sorted(set(cand) - set(range_same))
pool = sorted(range_same)

p = fit[fit.inhibitor.isin(pool)]
A = p.pivot(index="sid", columns="inhibitor", values="auc")
coh = p.drop_duplicates("sid").set_index("sid").cohort
subj = p.drop_duplicates("sid").set_index("sid").dbgap_subject_id
tr_ids = coh[coh == "Waves1+2"].index
te_ids = coh[coh == "Waves3+4"].index
mu = A.loc[tr_ids].mean()
sd = A.loc[tr_ids].std()
Z = (A - mu) / sd
rep["n_train_samples"] = int(len(tr_ids)); rep["n_later_samples"] = int(len(te_ids))
rep["pool_size"] = len(pool)
rep["later_missing_fraction"] = float(Z.loc[te_ids].isna().mean().mean())

# --- drift structure (observation of the problem) ---
zt = Z.loc[te_ids]
delta = zt.mean()
se = zt.std() / np.sqrt(zt.notna().sum())
rep["drift"] = {
    "mean_abs_delta_z": float(delta.abs().mean()),
    "median_abs_delta_z": float(delta.abs().median()),
    "frac_drugs_abs_t_gt3": float((np.abs(delta / se) > 3).mean()),
    "frac_drugs_abs_delta_gt_0.25": float((delta.abs() > 0.25).mean()),
    "later_sd_ratio_median": float((zt.std()).median()),
}
# sample-level offset share: variance of per-sample mean z vs what independent drugs would give
sm = zt.mean(axis=1)
n_obs = zt.notna().sum(axis=1)
rep["drift"]["sample_mean_z_sd"] = float(sm.std())

# --- battery order on training only ---
Ztr = Z.loc[tr_ids].fillna(0.0)
C = np.corrcoef(Ztr.values.T)
order = list(np.argsort(-(C ** 2).sum(axis=0)))  # most informative first, deterministic
pool_arr = np.array(pool)
KS = [0, 4, 8, 16]


def ridge_fit(Xtr, Ytr, alpha=10.0):
    Xc = Xtr - Xtr.mean(0)
    W = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(Xc.shape[1]), Xc.T @ (Ytr - Ytr.mean(0)))
    return Xtr.mean(0), Ytr.mean(0), W


def ridge_pred(model, X):
    xm, ym, W = model
    return ym + (X - xm) @ W


Zte = Z.loc[te_ids]
te_subj = subj.loc[te_ids]
uniq = te_subj.unique()
fold_of = {s: i % 5 for i, s in enumerate(rng.permutation(uniq))}
folds = te_subj.map(fold_of)

res = {k: {m: [] for m in ["M0", "M1", "M2", "M3", "M4", "oracle", "random"]} for k in KS}
who = {k: [] for k in KS}
resid_rows = []
for k in KS:
    bi = order[:k]
    bcols = pool_arr[bi]
    # later samples with all battery drugs observed and >=60 pool drugs observed
    ok = Zte[bcols].notna().all(axis=1) if k else pd.Series(True, index=Zte.index)
    ok &= Zte.notna().sum(axis=1) >= 60
    for f in range(5):
        test_ids = Zte.index[(folds == f) & ok]
        later_train = Zte.index[folds != f]
        # fixed model M1 from Waves1+2 only
        if k:
            m1 = ridge_fit(Ztr[bcols].values, Ztr.values)
            # per-drug offset delta_d on other later subjects
            Pl = ridge_pred(m1, Zte.loc[later_train, bcols].fillna(0).values)
            R = Zte.loc[later_train].values - Pl
        else:
            m1 = (np.zeros(0), Ztr.values.mean(0), np.zeros((0, len(pool))))
            R = Zte.loc[later_train].values
        n = np.sum(~np.isnan(R), axis=0)
        off = np.where(n > 0, np.nanmean(R, axis=0), 0.0) * (n / (n + 10.0))
        for sid in test_ids:
            zt_s = Zte.loc[sid].values
            if k:
                p1 = ridge_pred(m1, Zte.loc[[sid], bcols].values)[0]
            else:
                p1 = m1[1].copy()
            # global sample offset from battery residual
            if k:
                g = float(np.mean(Zte.loc[sid, bcols].values - p1[bi]))
                g *= k / (k + 2.0)
            else:
                g = 0.0
            cand_idx = [j for j in range(len(pool)) if j not in bi and not np.isnan(zt_s[j])]
            if len(cand_idx) < 10:
                continue
            true = zt_s[cand_idx]
            preds = {
                "M0": Ztr.values.mean(0)[cand_idx] * 0,
                "M1": p1[cand_idx],
                "M2": (p1 + off)[cand_idx],
                "M3": (p1 + g)[cand_idx],
                "M4": (p1 + off + g)[cand_idx],
            }
            # M0 = drug-mean prior (z=0 for all in train units) -> falls back to W1+2 means, i.e. all-zero
            # scores, so nominate by the later-sample-independent prior: lowest W1+2 mean raw AUC cannot be
            # ranked in z units, hence M0 is a random nomination over the unqueried drugs (expected z = mean z)
            sel_oracle = np.argsort(true)[:5]
            res[k]["oracle"].append(-true[sel_oracle].mean())
            res[k]["random"].append(-true.mean())
            res[k]["M0"].append(-true.mean())
            for m in ["M1", "M2", "M3", "M4"]:
                sel = np.argsort(preds[m])[:5]
                res[k][m].append(-true[sel].mean())
            who[k].append(subj.loc[sid])
            if k == 8:
                resid_rows.append((sid, subj.loc[sid], f, g))


def cluster_boot(vals, ids, B=400):
    vals = np.asarray(vals)
    ids = np.asarray(ids)
    us = np.unique(ids)
    idx = {u: np.where(ids == u)[0] for u in us}
    out = []
    for _ in range(B):
        pick = rng.choice(us, len(us))
        out.append(np.mean(np.concatenate([vals[idx[u]] for u in pick])))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


rep["policy_utility"] = {}
for k in KS:
    ids = who[k]
    row = {"n_samples": len(ids), "n_subjects": int(len(set(ids)))}
    base = np.array(res[k]["random"])
    orc = np.array(res[k]["oracle"])
    for m in ["random", "M1", "M2", "M3", "M4", "oracle"]:
        v = np.array(res[k][m])
        row[m] = float(v.mean())
    for m in ["M1", "M2", "M3", "M4"]:
        row[m + "_frac_of_oracle_gain"] = float((np.array(res[k][m]) - base).mean() / (orc - base).mean())
    for a, b in [("M2", "M1"), ("M3", "M1"), ("M4", "M1"), ("M4", "M2"), ("M4", "M3")]:
        d = np.array(res[k][a]) - np.array(res[k][b])
        row[f"{a}-{b}"] = {"mean": float(d.mean()), "ci95_cluster_boot": cluster_boot(d, ids)}
    rep["policy_utility"][k] = row

# --- same-observation separability: does the battery residual vector identify the drift type? ---
k = 8
bcols = pool_arr[order[:k]]
m1 = ridge_fit(Ztr[bcols].values, Ztr.values)
ok = Zte[bcols].notna().all(axis=1) & (Zte.notna().sum(axis=1) >= 60)
ids = Zte.index[ok]
Pb = ridge_pred(m1, Zte.loc[ids, bcols].values)
Rb = Zte.loc[ids, bcols].values - Pb[:, [order[i] for i in range(k)]]
# decompose battery residuals: sample-common component vs drug-specific component, leave-one-sample-out
dmean = Rb.mean(axis=0)
gmean = Rb.mean(axis=1)
tot = Rb.var()
rep["separability"] = {
    "n_samples": int(len(ids)),
    "battery_residual_var": float(tot),
    "var_explained_by_drug_offset": float(np.var(np.tile(dmean, (len(ids), 1))) / tot),
    "var_explained_by_sample_offset": float(np.var(np.tile(gmean[:, None], (1, k))) / tot),
    "mean_abs_drug_offset": float(np.abs(dmean).mean()),
    "mean_abs_sample_offset": float(np.abs(gmean).mean()),
}
# likelihood-ratio style test, leave-subject-out: which description predicts a held-out sample's residual vector?
sj = subj.loc[ids].values
ll = {"null": 0.0, "G": 0.0, "D": 0.0, "GD": 0.0}
sig2 = tot
for i in range(len(ids)):
    mask = sj != sj[i]
    d_i = Rb[mask].mean(axis=0)
    r = Rb[i]
    g_est = r.mean()
    ll["null"] += -np.sum(r ** 2) / (2 * sig2)
    ll["G"] += -np.sum((r - g_est * k / (k + 2.0)) ** 2) / (2 * sig2)
    ll["D"] += -np.sum((r - d_i) ** 2) / (2 * sig2)
    ll["GD"] += -np.sum((r - d_i - (r - d_i).mean() * k / (k + 2.0)) ** 2) / (2 * sig2)
rep["separability"]["heldout_sse_ratio_vs_null"] = {m: float(-2 * v * sig2 / (-np.sum(Rb ** 2) / 1.0 * 1.0)) for m, v in ll.items()}
rep["separability"]["note"] = ("battery residual vector (k=8) of a held-out later subject, described by: null / global offset (G) / "
                               "drug offsets estimated on other later subjects (D) / both; values are SSE relative to null (lower=better)")

# --- replicate-well technical noise in AUC (trapezoid, log2 conc), z units ---
raw = pd.read_csv(D / "beataml_wv1to4_raw_inhibitor_v4_dbgap.txt", sep="\t",
                  usecols=["dbgap_subject_id", "dbgap_rnaseq_sample", "dbgap_dnaseq_sample", "inhibitor", "plate_num",
                           "replicate", "well_concentration", "normalized_viability", "passed_qc"])
raw["sid"] = (raw.dbgap_subject_id.astype(str) + "|" + raw.dbgap_rnaseq_sample.fillna("") + "|" + raw.dbgap_dnaseq_sample.fillna(""))
raw = raw[raw.inhibitor.isin(pool) & raw.passed_qc]
raw["rep_key"] = raw.plate_num.astype(str) + "_" + raw.replicate.astype(str)


def trap(g):
    g = g.sort_values("well_concentration")
    x = np.log2(g.well_concentration.values)
    if len(x) < 5:
        return np.nan
    y = np.clip(g.normalized_viability.values, 0, 150)
    return float(np.trapezoid(y, x) / (x[-1] - x[0]))


tab = []
for (sid, inh), g in raw.groupby(["sid", "inhibitor"]):
    keys = g.rep_key.unique()
    if len(keys) < 2:
        continue
    a = trap(g[g.rep_key == keys[0]])
    b = trap(g[g.rep_key == keys[1]])
    if np.isfinite(a) and np.isfinite(b):
        tab.append((sid, inh, a, b))
t = pd.DataFrame(tab, columns=["sid", "inh", "a", "b"])
full = raw.groupby(["sid", "inhibitor"]).apply(lambda g: trap(g.drop_duplicates(["well_concentration"])), include_groups=False)
dsd = full.groupby(level="inhibitor").std()
t["tech_sd"] = (t.a - t.b).abs() / np.sqrt(2)
t["sdz"] = t.tech_sd / t.inh.map(dsd)
rep["replicate_noise"] = {
    "n_pairs_with_two_replicate_wells": int(len(t)),
    "median_tech_sd_in_between_sample_sd_units": float(t.sdz.median()),
    "rms_tech_sd_in_between_sample_sd_units": float(np.sqrt((t.sdz ** 2).mean())),
    "note": "sd of a difference of two replicate trapezoid AUCs / sqrt(2), divided by the drug's between-sample sd of the same statistic",
}

# --- chronology: run_index separation, from the fit-independent raw ids ---
ri = pd.read_csv(D / "beataml_wv1to4_raw_inhibitor_v4_dbgap.txt", sep="\t",
                 usecols=["dbgap_subject_id", "run_index", "time_of_read"]).drop_duplicates(["dbgap_subject_id", "run_index"])
ri = ri.merge(clin[["dbgap_subject_id", "cohort"]].drop_duplicates("dbgap_subject_id"), on="dbgap_subject_id", how="left")
rep["chronology"] = {c: {"run_index_min": int(g.run_index.min()), "run_index_median": float(g.run_index.median()),
                         "run_index_max": int(g.run_index.max())} for c, g in ri.groupby("cohort")}
w12 = ri[ri.cohort == "Waves1+2"].run_index
w34 = ri[ri.cohort == "Waves3+4"].run_index
rep["chronology"]["frac_W34_runs_after_max_W12"] = float((w34 > w12.max()).mean())
rep["chronology"]["frac_W34_runs_after_W12_median"] = float((w34 > w12.median()).mean())

with open(OUT / "FEASIBILITY.json", "w") as fh:
    json.dump(rep, fh, indent=1, default=str)
print(json.dumps(rep, indent=1, default=str))
