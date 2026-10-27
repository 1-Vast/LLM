"""E143: does shrinkage make the pathway prior usable at the drug level?

R142 found the grouping carries real signal (permutation p 0.000, Pearson 0.44) but a crude
leave-one-out group mean is too noisy to beat the grand mean. The inference was that shrinkage is
what makes it usable. This tests that directly with an empirical-Bayes estimator.

Pre-registered in PROTOCOL_E133.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r143"
N_BOOT = 2000
SEED = 20261046
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def variance_components(y, groups):
    """Method-of-moments variance components for a one-way random effects model."""
    df = pd.DataFrame({"y": y, "g": groups})
    gs = df.groupby("g")["y"]
    n_g = gs.size().to_numpy(float)
    m_g = gs.mean().to_numpy(float)
    k = len(n_g); N = n_g.sum()
    grand = float(y.mean())
    ss_within = float(((df["y"] - df.groupby("g")["y"].transform("mean")) ** 2).sum())
    df_within = N - k
    sigma2 = ss_within / df_within if df_within > 0 else 0.0
    ss_between = float((n_g * (m_g - grand) ** 2).sum())
    ms_between = ss_between / (k - 1) if k > 1 else 0.0
    n0 = (N - (n_g ** 2).sum() / N) / (k - 1) if k > 1 else 1.0
    tau2 = max(0.0, (ms_between - sigma2) / n0) if n0 > 0 else 0.0
    return sigma2, tau2


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

    inst = []
    for side, dcol, pcol in (("anchor", "a", "ap"), ("library", "b", "lp")):
        m = g.groupby(dcol).agg(emax=("emax", "mean"), pathway=(pcol, "first"), n=("emax", "size"))
        for drug, row in m.iterrows():
            inst.append({"side": side, "drug": drug, "pathway": str(row["pathway"]),
                         "y": float(row["emax"]), "n": int(row["n"])})
    I = pd.DataFrame(inst)
    I = I[I["n"] >= 30].reset_index(drop=True)

    res = {"kind": "does_shrinkage_make_the_pathway_prior_usable",
           "input_sha256": sha256(ORIG),
           "settings": {"n_boot": N_BOOT, "seed": SEED},
           "audit": {"drug_instances": int(len(I)),
                     "anchor": int((I["side"] == "anchor").sum()),
                     "library": int((I["side"] == "library").sum())},
           "results": {}, "files": {}}

    rng = np.random.default_rng(SEED)
    for side in ("anchor", "library", "both"):
        sub = I if side == "both" else I[I["side"] == side]
        if len(sub) < 20:
            continue
        y = sub["y"].to_numpy(float); grp = sub["pathway"].to_numpy()
        sigma2, tau2 = variance_components(y, grp)
        grand = float(y.mean())
        pred_shrunk = np.full(len(y), np.nan)
        pred_crude = np.full(len(y), np.nan)
        for i in range(len(y)):
            mask = np.ones(len(y), dtype=bool); mask[i] = False
            same = grp[mask] == grp[i]
            n_g = int(same.sum())
            if n_g == 0:
                pred_shrunk[i] = grand; pred_crude[i] = np.nan
                continue
            m_g = float(y[mask][same].mean())
            pred_crude[i] = m_g
            lam = tau2 / (tau2 + sigma2 / n_g) if (tau2 + sigma2 / n_g) > 0 else 0.0
            pred_shrunk[i] = lam * m_g + (1 - lam) * grand
        e = {"n": int(len(y)), "sigma2": float(sigma2), "tau2": float(tau2),
             "tau2_over_sigma2": float(tau2 / sigma2) if sigma2 > 0 else None}
        for nm, pr in (("grand", np.full(len(y), grand)), ("crude", pred_crude), ("shrunk", pred_shrunk)):
            m = np.isfinite(pr)
            ss_res = float(((y[m] - pr[m]) ** 2).sum())
            ss_tot = float(((y[m] - y[m].mean()) ** 2).sum())
            e[nm] = {"n": int(m.sum()),
                     "r2": (1 - ss_res / ss_tot) if ss_tot > 0 else None,
                     "pearson": float(pearsonr(pr[m], y[m]).statistic) if m.sum() > 5 else None}
        for a, b in (("shrunk", "grand"), ("crude", "grand"), ("shrunk", "crude")):
            m = np.isfinite(pred_shrunk if a == "shrunk" else (pred_crude if a == "crude" else np.full(len(y), grand)))
            pa = pred_shrunk if a == "shrunk" else (pred_crude if a == "crude" else np.full(len(y), grand))
            pb = pred_shrunk if b == "shrunk" else (pred_crude if b == "crude" else np.full(len(y), grand))
            m = np.isfinite(pa) & np.isfinite(pb)
            dif = (y[m] - pb[m]) ** 2 - (y[m] - pa[m]) ** 2   # positive = a better than b
            boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
            e["%s_minus_%s" % (a, b)] = {"mean": float(dif.mean()),
                                          "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
        res["results"][side] = e

    both = res["results"].get("both", {})
    h352 = bool(both and both["shrunk_minus_grand"]["ci95"][0] > 0
                and both["shrunk_minus_crude"]["ci95"][0] > 0)
    res["decisions"] = {"H352_shrinkage_makes_it_usable": h352, "H353_shrinkage_does_not_help": not h352}
    res["decisions"]["verdict"] = (
        "shrinkage_makes_the_pathway_prior_usable_closing_the_mechanism_chain" if h352 else
        "shrinkage_does_not_rescue_it_so_the_mechanism_story_needs_revision")
    res["limits"] = ["111 drug instances and 21 pathways.",
                     "Moments rather than REML, and tau-squared is truncated at zero which affects lambda.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r143/PROTOCOL_E133.md",
                "research/2026-10-27-agent-cell-identifiability-r143/e143_shrinkage.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E143_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    for side, e in res["results"].items():
        print(" [%-8s] n=%3d  sigma2=%.6f  tau2=%.6f  tau2/sigma2=%.3f" % (
            side, e["n"], e["sigma2"], e["tau2"], e["tau2_over_sigma2"] or float("nan")))
        for nm in ("grand", "crude", "shrunk"):
            v = e[nm]
            print("     %-7s R2 %s  pearson %s" % (
                nm, ("%+.4f" % v["r2"]) if v["r2"] is not None else "n/a",
                ("%.3f" % v["pearson"]) if v["pearson"] is not None else "n/a"))
        for k in ("shrunk_minus_grand", "crude_minus_grand", "shrunk_minus_crude"):
            if k in e:
                c = e[k]
                print("     %-20s %+.8f [%+.8f,%+.8f]" % (k, c["mean"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
