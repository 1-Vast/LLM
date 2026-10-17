"""Development diagnostic: which part of the drug response does each prior predict?

File summary
- Path: research/feedback_attribution_20261017/decomposition.py
- Purpose: PROTOCOL.md s7. The frozen endpoint removes the inhibitor's mean and the sample's
  overall sensitivity (b_d G). A cell-state prior that mainly predicts overall sensitivity would
  then add little on this endpoint, which is one possible reason vc0 did not beat the item prior.
  This diagnostic checks that hypothesis; it does not change the endpoint.
- Parts:
  - ``variance``: per inhibitor, least squares of AUC on [1, G] splits the sum of squares over
    measured pairs exactly into inhibitor mean, sample-wide sensitivity (b_d (G - mean G)) and the
    residual (the endpoint's quantity).
  - ``state_predictable_residual``: the share of the residual a ridge on 30 basal PCs predicts in
    held-out patients (outer folds).
  - ``technical_noise``: replicate 7-dose profiles in the raw file. A curve-free AUC (trapezoid of
    viability over log10 dose) per replicate, rescaled to the probit AUC by least squares on
    single-run pairs; half the variance of replicate differences is the noise variance.
  - ``prediction``: on held-out patients (rank 20), how well each state predicts G and the residual,
    before and after the four exploit readouts: Pearson r for G, mean within-inhibitor r for the
    residual.
  - ``outcome_related_missingness``: whether samples with a scheduled-but-unrecorded profile
    differ in G from the samples recorded for that inhibitor.
- Interfaces: ``python -B decomposition.py`` writes DECOMPOSITION.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import (DOMAIN_CACHE, HERE, RAW, ROOT, basal_pcs, load_domain, outer_folds, schedule_matrix, sha256,
                    tie, write_json)
from coherent import CoherentScorer

from agent.bridge_design import nominate  # noqa: E402
from virtual_cell.bridged_transfer import RIDGE_ALPHAS, BridgedTransferModel, residualise  # noqa: E402

RANK, K = 20, 4


def variance(Y):
    G = np.nanmedian(Y, axis=1)
    ss = {"total": 0.0, "inhibitor_mean": 0.0, "sample_sensitivity": 0.0, "residual": 0.0}
    grand = np.nanmean(Y)
    R, coef = residualise(Y.T, G)
    for j in range(Y.shape[1]):
        f = np.isfinite(Y[:, j])
        if not np.isfinite(coef[j]).all():
            continue
        y = Y[f, j]
        fit = coef[j, 0] + coef[j, 1] * G[f]
        ss["total"] += float(((y - grand) ** 2).sum())
        ss["inhibitor_mean"] += float(f.sum() * (y.mean() - grand) ** 2)
        ss["sample_sensitivity"] += float(((fit - y.mean()) ** 2).sum())
        ss["residual"] += float(((y - fit) ** 2).sum())
    share = {k: v / ss["total"] for k, v in ss.items() if k != "total"}
    return {"sum_of_squares": ss, "share": share, "slopes_b": {"median": float(np.nanmedian(coef[:, 1])),
                                                               "p10": float(np.nanpercentile(coef[:, 1], 10)),
                                                               "p90": float(np.nanpercentile(coef[:, 1], 90))}}, R.T, G


def ridge_cv(Pall, Rm, fid):
    """Out-of-fold R^2 of the residual from basal PCs, pooled over measured pairs."""

    pred = np.full(Rm.shape, np.nan)
    pen = None
    for k in range(5):
        tr, te = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        P = basal_pcs(Pall, rows=tr)
        P1 = np.column_stack([np.ones(len(P)), P])
        pen = np.diag([0.0] + [1.0] * (P1.shape[1] - 1))
        for j in range(Rm.shape[1]):
            rows = tr[np.isfinite(Rm[tr, j])]
            if len(rows) < 30:
                continue
            best = None
            for alpha in RIDGE_ALPHAS:
                A = P1[rows].T @ P1[rows] + alpha * pen
                B = np.linalg.solve(A, P1[rows].T @ Rm[rows, j])
                H = np.einsum("ij,jk,ik->i", P1[rows], np.linalg.inv(A), P1[rows])
                loo = (Rm[rows, j] - P1[rows] @ B) / (1 - H)
                if best is None or (loo ** 2).mean() < best[0]:
                    best = ((loo ** 2).mean(), B)
            pred[te, j] = P1[te] @ best[1]
    m = np.isfinite(Rm) & np.isfinite(pred)
    return float(1 - ((Rm[m] - pred[m]) ** 2).sum() / (Rm[m] ** 2).sum())


def technical_noise(d):
    raw = pd.read_csv(RAW, sep="\t", usecols=["dbgap_rnaseq_sample", "inhibitor", "run_index", "replicate",
                                              "well_concentration", "normalized_viability"],
                      dtype={"dbgap_rnaseq_sample": str, "inhibitor": str})
    raw = raw[raw.dbgap_rnaseq_sample.isin(set(d["contexts"])) & raw.inhibitor.isin(set(d["items"]))]
    raw = raw.assign(v=raw.normalized_viability.clip(0, 100), x=np.log10(raw.well_concentration))

    def cf_auc(g):
        g = g.sort_values("x")
        return float(np.trapezoid(g.v.to_numpy(), g.x.to_numpy())) if len(g) == 7 else np.nan

    per = raw.groupby(["dbgap_rnaseq_sample", "inhibitor", "run_index", "replicate"]).apply(cf_auc, include_groups=False)
    per = per.dropna().reset_index(name="cf")
    nrep = per.groupby(["dbgap_rnaseq_sample", "inhibitor"]).cf.transform("size")
    si = {s: i for i, s in enumerate(d["contexts"])}
    ii = {s: j for j, s in enumerate(d["items"])}
    single = per[nrep == 1]
    y = np.array([d["Y"][si[s], ii[i]] for s, i in zip(single.dbgap_rnaseq_sample, single.inhibitor)])
    ok = np.isfinite(y)
    A = np.column_stack([np.ones(ok.sum()), single.cf.to_numpy()[ok]])
    (c0, c1), *_ = np.linalg.lstsq(A, y[ok], rcond=None)
    r_scale = float(np.corrcoef(single.cf.to_numpy()[ok], y[ok])[0, 1])
    two = per[nrep >= 2].sort_values("replicate").groupby(["dbgap_rnaseq_sample", "inhibitor"]).cf.apply(
        lambda s: s.iloc[0] - s.iloc[1])
    noise_var = float((c1 * two).var() / 2)
    return {"replicate_pairs": int(len(two)), "single_profile_pairs": int(ok.sum()),
            "curve_free_to_probit_slope": float(c1), "curve_free_vs_probit_r": r_scale,
            "noise_variance_probit_scale": noise_var,
            "note": "replicates within the same specimen and run; between-run and specimen noise not included"}


def prediction(d, R, G):
    Y, X = d["Y"], d["X"]
    fid = outer_folds(d["groups"])
    order = tie(d["items"])
    out = {s: {"G_pred": [], "R_pred": [], "R_true": [], "rows": []} for s in
           ("population", "rna", "population_updated", "rna_updated")}
    Gt = []
    for k in range(5):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        model = BridgedTransferModel(rank=RANK, abs_gate=None, min_measured=100, impute_iters=15).fit(Y[src], X[src])
        sc = CoherentScorer(model, Y[src])
        pop = model.prior(None)
        for c in tgt:
            st = model.prior(X[c])
            B = nominate(model.expected_hit(st), K, [], order)
            states = {"population": pop, "rna": st, "population_updated": model.posterior(pop, B, Y[c, B]),
                      "rna_updated": model.posterior(st, B, Y[c, B])}
            Gt.append(G[c])
            for name, s in states.items():
                mean, _ = sc.residual(s)
                out[name]["G_pred"].append(sc.predicted_G(s)[0])
                keep = np.isfinite(R[c]) & model.threshold_ok
                keep[B] = False
                out[name]["R_pred"].append(np.where(keep, mean, np.nan))
                out[name]["R_true"].append(np.where(keep, Y[c] - model.a - model.b * G[c], np.nan))
    Gt = np.array(Gt)
    res = {}
    for name, v in out.items():
        gp = np.array(v["G_pred"])
        Rp, Rt = np.array(v["R_pred"]), np.array(v["R_true"])
        rs = []
        for j in range(Rp.shape[1]):
            m = np.isfinite(Rp[:, j]) & np.isfinite(Rt[:, j])
            if m.sum() >= 30 and Rp[m, j].std() > 1e-9:
                rs.append(np.corrcoef(Rp[m, j], Rt[m, j])[0, 1])
        res[name] = {"G_pearson_r": float(np.corrcoef(gp, Gt)[0, 1]) if gp.std() > 1e-9 else 0.0,
                     "residual_within_inhibitor_r_mean": float(np.mean(rs)) if rs else 0.0,
                     "inhibitors_scored": len(rs)}
    return res


def missing_vs_G(d, G):
    S = schedule_matrix(d)
    M = np.isfinite(d["Y"])
    lost = S & ~M
    z = (G - G.mean()) / G.std()
    diffs, n = [], 0
    for j in range(M.shape[1]):
        if lost[:, j].sum() >= 3 and (S[:, j] & M[:, j]).sum() >= 30:
            diffs.append(z[lost[:, j]].mean() - z[S[:, j] & M[:, j]].mean())
            n += int(lost[:, j].sum())
    diffs = np.array(diffs)
    return {"inhibitors": int(len(diffs)), "lost_pairs": n,
            "mean_G_z_lost_minus_recorded": float(diffs.mean()),
            "share_inhibitors_lost_more_sensitive": float(np.mean(diffs < 0)),
            "note": "lower G = more sensitive overall; positive values mean lost profiles come from more "
                    "resistant samples"}


def main() -> None:
    d = load_domain()
    var, R, G = variance(d["Y"])
    fid = outer_folds(d["groups"])
    var["state_predictable_residual_r2_oof"] = ridge_cv(d["X"], R, fid)
    noise = technical_noise(d)
    var["technical_noise_share_of_residual"] = noise["noise_variance_probit_scale"] * np.isfinite(R).sum() / \
        var["sum_of_squares"]["residual"]
    out = {"status": "DEVELOPMENT DIAGNOSTIC (Beat AML exposed); PROTOCOL.md s7",
           "inputs_sha256": {str(DOMAIN_CACHE.relative_to(ROOT)).replace("\\", "/"): sha256(DOMAIN_CACHE),
                             str(RAW.relative_to(ROOT)).replace("\\", "/"): sha256(RAW)},
           "variance": var, "technical_noise": noise, "prediction_held_out": prediction(d, R, G),
           "outcome_related_missingness": missing_vs_G(d, G)}
    write_json(HERE / "DECOMPOSITION.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
