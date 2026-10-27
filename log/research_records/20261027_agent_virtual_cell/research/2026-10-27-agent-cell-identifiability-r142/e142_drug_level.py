"""E142: why does the pathway prior substitute? A leave-one-drug-out test at the drug level.

The mechanism claimed since R136 is that an unseen drug inherits the behaviour of its group. That is
testable directly: can a drug's mean response be predicted from the other drugs in its pathway?
A data-derived regrouping is impossible for unseen drugs by construction, which is precisely why an
annotation is needed, so the question is whether the annotation actually partitions drugs by
behaviour.

Pre-registered in PROTOCOL_E132.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r142"
N_BOOT = 2000
N_PERM = 1000
SEED = 20261045
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def loo_pathway_pred(y, groups):
    """Leave-one-out group mean prediction."""
    gs = pd.Series(y).groupby(groups)
    sums = gs.transform("sum").to_numpy()
    counts = pd.Series(y).groupby(groups).transform("count").to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        pred = (sums - y) / (counts - 1)
    pred[counts <= 1] = np.nan
    return pred


def r2(pred, y):
    m = np.isfinite(pred)
    if m.sum() < 5:
        return float("nan")
    ss_res = float(((y[m] - pred[m]) ** 2).sum())
    ss_tot = float(((y[m] - y[m].mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])]

    # drug instances: (drug, side)
    inst = []
    for side, dcol, pcol in (("anchor", "a", "ap"), ("library", "b", "lp")):
        m = g.groupby(dcol).agg(emax=("emax", "mean"), pathway=(pcol, "first"), n=("emax", "size"))
        for drug, row in m.iterrows():
            inst.append({"side": side, "drug": drug, "pathway": str(row["pathway"]),
                         "y": float(row["emax"]), "n": int(row["n"])})
    I = pd.DataFrame(inst).reset_index(drop=True)
    I = I[I["n"] >= 30].reset_index(drop=True)

    res = {"kind": "drug_level_leave_one_out_test_of_the_pathway_prior",
           "input_sha256": sha256(ORIG),
           "settings": {"n_boot": N_BOOT, "n_perm": N_PERM, "seed": SEED},
           "audit": {"drug_instances": int(len(I)),
                     "anchor": int((I["side"] == "anchor").sum()),
                     "library": int((I["side"] == "library").sum()),
                     "pathway_levels": int(I["pathway"].nunique())},
           "results": {}, "files": {}}

    rng = np.random.default_rng(SEED)
    for side in ("anchor", "library", "both"):
        sub = I if side == "both" else I[I["side"] == side]
        if len(sub) < 20:
            continue
        y = sub["y"].to_numpy(float); grp = sub["pathway"].to_numpy()
        pred = loo_pathway_pred(y, grp)
        m = np.isfinite(pred)
        base = np.full(len(y), np.nanmean(y))
        e = {"n": int(m.sum()), "r2_pathway": r2(pred, y), "r2_grandmean": r2(base, y),
             "pearson": float(pearsonr(pred[m], y[m]).statistic) if m.sum() > 5 else None,
             "spearman": float(spearmanr(pred[m], y[m]).statistic) if m.sum() > 5 else None}
        # paired bootstrap on squared error
        se_path = (y[m] - pred[m]) ** 2
        se_base = (y[m] - base[m]) ** 2
        dif = se_base - se_path       # positive = pathway better
        boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
        e["mse_improvement"] = {"mean": float(dif.mean()),
                                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
        # permutation null on R2
        null = []
        for _ in range(N_PERM):
            gp = rng.permutation(grp)
            pr = loo_pathway_pred(y, gp)
            rr = r2(pr, y)
            if np.isfinite(rr):
                null.append(rr)
        null = np.array(null)
        e["permutation"] = {"null_mean": float(null.mean()),
                            "p_value": float((null >= e["r2_pathway"]).mean()) if np.isfinite(e["r2_pathway"]) else None}
        res["results"][side] = e

    both = res["results"].get("both", {})
    h350 = bool(both and both["mse_improvement"]["ci95"][0] > 0 and both["permutation"]["p_value"] is not None
                and both["permutation"]["p_value"] < 0.05)
    res["decisions"] = {"H350_pathway_partitions_drugs_by_behaviour": h350,
                        "H351_pathway_unrelated_to_behaviour": not h350}
    res["decisions"]["verdict"] = (
        "the_pathway_prior_works_because_pathway_members_behave_alike" if h350 else
        "pathway_membership_does_not_predict_a_drugs_behaviour_so_the_prior_story_fails")
    res["limits"] = ["Only 111 drug instances, and a drug mean averages away cell-to-cell variation.",
                     "The regrouping question is unanswerable for unseen drugs by construction, which is why an annotation is needed.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r142/PROTOCOL_E132.md",
                "research/2026-10-27-agent-cell-identifiability-r142/e142_drug_level.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E142_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    I.to_csv(OUT / "E142_drugs.csv", index=False)

    print("drug instances=%d  (anchor %d, library %d)  pathway levels=%d" % (
        res["audit"]["drug_instances"], res["audit"]["anchor"], res["audit"]["library"],
        res["audit"]["pathway_levels"]))
    for side, e in res["results"].items():
        mi = e["mse_improvement"]
        print(" [%-8s] n=%3d  R2 pathway %+.4f  R2 grandmean %+.4f  pearson %s  perm p=%s" % (
            side, e["n"], e["r2_pathway"], e["r2_grandmean"],
            ("%.3f" % e["pearson"]) if e["pearson"] is not None else "n/a",
            ("%.3f" % e["permutation"]["p_value"]) if e["permutation"]["p_value"] is not None else "n/a"))
        print("            MSE improvement %+.6f [%+.6f,%+.6f]" % (mi["mean"], mi["ci95"][0], mi["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
