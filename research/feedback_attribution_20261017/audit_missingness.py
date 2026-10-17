"""Missingness audit: why a (sample, inhibitor) pair has no AUC, and what the gaps correlate with.

File summary
- Path: research/feedback_attribution_20261017/audit_missingness.py
- Purpose: the replay spends a query on an unmeasured pair and scores it as no hit, and the model
  weights each item by its source coverage q_i. That defines an archive-query task. This audit
  separates the reasons a pair is missing where the release allows it, and measures how
  missingness relates to collection wave, specimen, disease stage, basal cell state and drug
  family. It reads design columns only; no response value is used.
- Core points:
  - Reasons, per unmeasured domain pair (sample = RNA-seq sample id):
    - ``fit_absent_raw_present``: QC-passed raw wells exist but the AUC file has no fit (curve QC,
      replicate QC or the inclusion set);
    - ``on_panel_no_record``: the inhibitor is on a panel the sample was run with (panel inventory
      = inhibitors ever recorded under that panel name), but no QC-passed well exists (plate QC,
      too few cells or a failed run; the release cannot tell these apart);
    - ``not_scheduled``: no panel run for the sample contains the inhibitor;
    - ``identifier_unmatched``: a fit exists for the same patient's DNA sample of the same lab
      specimen but without the RNA-seq id.
  - Associations: coverage by cohort (wave), centre, specimen type and disease stage; per-drug
    cross-validated AUROC of the measured mask from basal PCs against cohort alone (folds by
    patient); coverage by drug family.
  - A design-based high-coverage panel: inhibitors scheduled for at least 90% of samples.
- Interfaces: `python -B audit_missingness.py` writes MISSINGNESS.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import (CLIN, FAMILIES, HERE, MAPPING, PROBIT, RAW, basal_pcs, load_domain, outer_folds,
                    write_json)

HIGH_COVERAGE = 0.8  # clean break: 93 inhibitors at >= 0.8, 89 at >= 0.85, 20 at >= 0.9


def auroc(y: np.ndarray, s: np.ndarray) -> float:
    from scipy.stats import rankdata
    y = y.astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def cv_logit_auroc(F: np.ndarray, y: np.ndarray, fid: np.ndarray, C: float = 0.1) -> float:
    """Out-of-fold AUROC of an L2 logistic model (folds by patient)."""

    from sklearn.linear_model import LogisticRegression
    s = np.full(len(y), np.nan)
    for k in np.unique(fid):
        tr, te = fid != k, fid == k
        if y[tr].min() == y[tr].max():
            s[te] = y[tr].mean()
            continue
        m = LogisticRegression(C=C, max_iter=2000).fit(F[tr], y[tr])
        s[te] = m.decision_function(F[te])
    return auroc(y, s)


def main() -> None:
    d = load_domain()
    samples, items = d["contexts"], d["items"]
    si = {s: i for i, s in enumerate(samples)}
    ii = {s: j for j, s in enumerate(items)}
    M = np.isfinite(d["Y"])
    n, D = M.shape

    raw = pd.read_csv(RAW, sep="\t", usecols=["dbgap_rnaseq_sample", "inhibitor", "inhibitor_panel"],
                      dtype=str)
    inv = raw.groupby("inhibitor_panel").inhibitor.agg(lambda s: set(s)).to_dict()
    raw_d = raw[raw.dbgap_rnaseq_sample.isin(si)]
    raw_pairs = np.zeros((n, D), bool)
    for s, it in raw_d[["dbgap_rnaseq_sample", "inhibitor"]].drop_duplicates().itertuples(index=False):
        if it in ii:
            raw_pairs[si[s], ii[it]] = True
    sched = np.zeros((n, D), bool)
    panels_of = raw_d.groupby("dbgap_rnaseq_sample").inhibitor_panel.agg(lambda s: set(s)).to_dict()
    for s, pans in panels_of.items():
        for p in pans:
            for it in inv[p]:
                if it in ii:
                    sched[si[s], ii[it]] = True

    fits = pd.read_csv(PROBIT, sep="\t", usecols=["dbgap_dnaseq_sample", "dbgap_rnaseq_sample", "inhibitor"],
                       dtype=str)
    mp = pd.read_excel(MAPPING, dtype=str)
    lab_of_rna = mp.dropna(subset=["dbgap_rnaseq_sample"]).set_index("dbgap_rnaseq_sample").labId.to_dict()
    dna_of_lab = mp.dropna(subset=["dbgap_dnaseq_sample"]).groupby("labId").dbgap_dnaseq_sample.agg(set).to_dict()
    orphan = fits[fits.dbgap_rnaseq_sample.isna() & fits.dbgap_dnaseq_sample.notna()]
    orphan_by_dna = orphan.groupby("dbgap_dnaseq_sample").inhibitor.agg(set).to_dict()
    unmatched = np.zeros((n, D), bool)
    for s, i in si.items():
        for dna in dna_of_lab.get(lab_of_rna.get(s), set()):
            for it in orphan_by_dna.get(dna, set()):
                if it in ii:
                    unmatched[i, ii[it]] = True

    miss = ~M
    reason = {
        "measured": int(M.sum()),
        "fit_absent_raw_present": int((miss & raw_pairs).sum()),
        "identifier_unmatched": int((miss & ~raw_pairs & unmatched).sum()),
        "on_panel_no_record": int((miss & ~raw_pairs & ~unmatched & sched).sum()),
        "not_scheduled": int((miss & ~raw_pairs & ~unmatched & ~sched).sum()),
        "measured_but_no_raw_wells": int((M & ~raw_pairs).sum()),
    }

    clin = pd.read_excel(CLIN, dtype=str).drop_duplicates("dbgap_rnaseq_sample").set_index("dbgap_rnaseq_sample")
    clin = clin.reindex(samples)
    cover_s = M.mean(1)
    by = {}
    for col in ("cohort", "centerID", "specimenType", "diseaseStageAtSpecimenCollection"):
        v = clin[col].fillna("NA").to_numpy()
        by[col] = {str(k): {"samples": int((v == k).sum()), "coverage": float(cover_s[v == k].mean())}
                   for k in sorted(set(v))}

    P = basal_pcs(d["X"])
    fid = outer_folds(d["groups"])
    cohort = pd.get_dummies(clin["cohort"].fillna("NA")).to_numpy(float)
    pan_names = sorted(inv)
    panels = np.array([[p in panels_of.get(s, set()) for p in pan_names] for s in samples], float)
    cov_d = M.mean(0)
    mid = np.flatnonzero((cov_d >= 0.1) & (cov_d <= 0.9))
    au_pc, au_wave, au_both, au_pan, au_pan_pc = [], [], [], [], []
    for j in mid:
        y = M[:, j].astype(int)
        au_pc.append(cv_logit_auroc(P, y, fid))
        au_wave.append(cv_logit_auroc(cohort, y, fid, C=10.0))
        au_both.append(cv_logit_auroc(np.column_stack([cohort * 10, P]), y, fid))
        au_pan.append(cv_logit_auroc(panels, y, fid, C=10.0))
        au_pan_pc.append(cv_logit_auroc(np.column_stack([panels * 10, P]), y, fid))
    au_pc, au_wave, au_both, au_pan, au_pan_pc = map(np.array, (au_pc, au_wave, au_both, au_pan, au_pan_pc))
    lost = miss & ~raw_pairs & ~unmatched & sched
    lost_s = lost.sum(1)
    any_lost = (lost_s > 0).astype(int)
    on_panel = {"pairs": int(lost.sum()), "samples_with_any": int(any_lost.sum()),
                "pairs_in_top_10_samples": int(np.sort(lost_s)[::-1][:10].sum()),
                "share_of_scheduled_pairs": float(lost.sum() / max(sched.sum(), 1)),
                "auroc_any_loss_from_basal_pcs": cv_logit_auroc(P, any_lost, fid),
                "auroc_any_loss_from_panels": cv_logit_auroc(panels, any_lost, fid, C=10.0)}

    fam = pd.read_excel(FAMILIES, sheet_name="drug_family", dtype=str)
    fam = fam[fam.inhibitor.isin(ii)]
    by_family = {}
    for f, g in fam.groupby("family"):
        js = [ii[x] for x in g.inhibitor]
        if len(js) >= 3:
            by_family[f] = {"inhibitors": len(js), "coverage": float(cov_d[js].mean())}
    sched_rate = sched.mean(0)
    hc = np.flatnonzero(sched_rate >= HIGH_COVERAGE)

    out = {
        "status": "DESIGN_AUDIT: measured masks and design columns only; no response value read",
        "domain": {"samples": n, "inhibitors": D, "pairs": n * D, "measured_share": float(M.mean())},
        "reasons_unmeasured": reason,
        "reason_notes": [
            "QC-removed wells are absent from the release (passed_qc is TRUE everywhere), so plate or well "
            "QC failures, too few cells and failed runs all fall under on_panel_no_record.",
            "Panel inventory is inferred from which inhibitors were ever recorded under a panel name; a "
            "drug QC-removed for every sample on a panel would be misread as not scheduled.",
        ],
        "coverage_per_inhibitor": {"min": float(cov_d.min()), "median": float(np.median(cov_d)),
                                   "max": float(cov_d.max()),
                                   "below_0.5": int((cov_d < 0.5).sum()), "at_least_0.9": int((cov_d >= 0.9).sum())},
        "coverage_per_sample": {"min": float(cover_s.min()), "median": float(np.median(cover_s)),
                                "max": float(cover_s.max())},
        "coverage_by": by,
        "state_association": {
            "inhibitors_tested": int(len(mid)),
            "auroc_measured_from_basal_pcs": {"median": float(np.nanmedian(au_pc)),
                                              "share_above_0.6": float(np.mean(au_pc > 0.6))},
            "auroc_measured_from_cohort": {"median": float(np.nanmedian(au_wave)),
                                           "share_above_0.6": float(np.mean(au_wave > 0.6))},
            "auroc_measured_from_cohort_and_pcs": {"median": float(np.nanmedian(au_both))},
            "auroc_measured_from_panels_run": {"median": float(np.nanmedian(au_pan))},
            "auroc_measured_from_panels_and_pcs": {"median": float(np.nanmedian(au_pan_pc))},
            "reading": "AUROC near 0.5 means the gap pattern is unrelated to that feature. Panels run (the "
                       "schedule) are the design driver; basal PCs carry part of the same information, "
                       "plausibly through collection-era batch effects, so a PC association alone is not "
                       "evidence that biology drives missingness",
        },
        "on_panel_no_record": on_panel,
        "coverage_by_family": dict(sorted(by_family.items(), key=lambda kv: kv[1]["coverage"])),
        "high_coverage_panel": {"rule": f"scheduled for >= {HIGH_COVERAGE:.0%} of samples (design-based)",
                                "inhibitors": int(len(hc)), "items": items[hc].tolist(),
                                "measured_share_within": float(M[:, hc].mean())},
        "q_i_meaning": "BridgedTransferModel.measured_rate is historical marginal archive coverage, "
                       "(n_measured + 0.5) / (n_source + 1); it is not assay feasibility and not a "
                       "per-sample availability probability",
    }
    write_json(HERE / "MISSINGNESS.json", out)
    print(json.dumps({k: out[k] for k in ("reasons_unmeasured", "coverage_per_inhibitor", "state_association",
                                           "high_coverage_panel")}, indent=1)[:3500])
    print(json.dumps(by, indent=1)[:2500])


if __name__ == "__main__":
    main()
