"""E183: does the pathway gain rise with how thickly that pathway level was covered in training?

R182 split by whether the level was ever observed and found +0.163 where it was and an unresolvable +0.057
where it was not, with the latter covering 28 percent of the space. This asks whether thickness matters
within the observed side, which would turn the condition into a threshold rather than a yes/no test.

Pre-registered in PROTOCOL_E171.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r183"
REPS = 20
N_BOOT = 2000
SEED = 20261073
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
# include a zero bucket: coverage 0 is exactly the regime R182 studied, and leaving it out
# silently dropped 28 percent of the evaluation rows in the first run of this script
EDGES = [(0, 0), (1, 5), (6, 50), (51, 200), (201, 10**9)]
LABELS = ["0", "1-5", "6-50", "51-200", ">200"]
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def solve_path(G, b, lams):
    out = {}
    d = np.diag(G).copy()
    for lam in lams:
        out[lam] = np.linalg.solve(G + np.diag(lam + 1e-9 * (d + 1.0)), b)
    return out


def fit_arm(Xtr, ytr, Xte, lams, seed, folds=FOLDS):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    Zte = (Xte - mu) / sd
    rng = np.random.default_rng(seed)
    chunks = np.array_split(rng.permutation(len(Z)), folds)
    score = {lam: [] for lam in lams}
    for f in range(folds):
        va = chunks[f]
        tr = np.setdiff1d(np.arange(len(Z)), va)
        ym = ytr[tr].mean()
        w = solve_path(Z[tr].T @ Z[tr], Z[tr].T @ (ytr[tr] - ym), lams)
        yv = ytr[va]
        for lam, ww in w.items():
            p = ym + Z[va] @ ww
            s = spearmanr(p, yv).statistic if np.std(p) > 0 else -2.0
            score[lam].append(0.0 if not np.isfinite(s) else float(s))
    best = max(lams, key=lambda lam: float(np.mean(score[lam])))
    ym = ytr.mean()
    ww = solve_path(Z.T @ Z, Z.T @ (ytr - ym), [best])[best]
    return ym + Zte @ ww


def boot_ci(v, seed):
    rng = np.random.default_rng(seed)
    bs = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
    return [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    AP = g["ap"].to_numpy(); LP = g["lp"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(AP, sorted(set(AP))), oh(LP, sorted(set(LP)))])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    bucket_rows = {}
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        cnt_a = pd.Series(AP[tr]).value_counts()
        cnt_b = pd.Series(LP[tr]).value_counts()
        ytr = y[tr]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
        cov_a = np.array([int(cnt_a.get(v, 0)) for v in AP[te]])
        cov_b = np.array([int(cnt_b.get(v, 0)) for v in LP[te]])
        cov = np.minimum(cov_a, cov_b)
        for (lo, hi), lab in zip(EDGES, LABELS):
            mask = (cov >= lo) & (cov <= hi)
            bucket_rows[lab] = bucket_rows.get(lab, 0) + int(mask.sum())
            if mask.sum() < 80:
                continue
            yt = y[te][mask]
            if np.std(yt) == 0:
                continue
            ri = spearmanr(p_id[mask], yt).statistic
            rp = spearmanr(p_pa[mask], yt).statistic
            rows.append({"rep": rep, "bucket": lab, "n": int(mask.sum()),
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp),
                         "gain": (0.0 if not np.isfinite(rp) else float(rp))
                                 - (0.0 if not np.isfinite(ri) else float(ri))})

    r = pd.DataFrame(rows)
    res = {"kind": "does_the_gain_rise_with_pathway_coverage_thickness",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "buckets": LABELS, "lambdas": list(LAMBDAS),
                        "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_bucket": {}, "files": {}}
    for lab in LABELS:
        sub = r[r.bucket == lab]
        if len(sub) < 8:
            continue
        v = sub["gain"].to_numpy()
        res["by_bucket"][lab] = {"n": int(len(sub)), "mean_rows": float(sub["n"].mean()),
                                  "rho_identity": float(sub["rho_identity"].mean()),
                                  "rho_pathway": float(sub["rho_pathway"].mean()),
                                  "gain": float(v.mean()),
                                  "ci95": boot_ci(v, SEED + 10 + LABELS.index(lab)),
                                  "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(v)))}
    tot = sum(bucket_rows.values())
    res["rows_by_bucket"] = bucket_rows
    res["share_of_eval_rows"] = {k: (v / tot if tot else None) for k, v in bucket_rows.items()}
    gains = [res["by_bucket"][l]["gain"] for l in LABELS if l in res["by_bucket"]]
    rising = sum(1 for a, b in zip(gains, gains[1:]) if b > a)
    h430 = bool(len(gains) >= 3 and rising >= len(gains) - 1)
    res["decisions"] = {"gains_in_order": gains, "monotone_steps": rising,
                        "H430_rises_with_thickness": h430, "H431_no_dependence": not h430}
    res["decisions"]["verdict"] = (
        "the_gain_rises_with_coverage_thickness_so_the_condition_needs_a_threshold" if h430 else
        "the_gain_does_not_rise_monotonically_with_thickness_over_this_range")
    res["limits"] = ["Coverage is counted as training rows only, not as diversity of cells or pairs.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r183/PROTOCOL_E171.md",
                "research/2026-10-27-agent-cell-identifiability-r183/e183_thickness.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E183_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E183_rows.csv", index=False)

    for lab in LABELS:
        e = res["by_bucket"].get(lab)
        if not e:
            continue
        print("  [%-7s] n=%3d rows/rep %5.1f share %5.1f%% | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            lab, e["n"], e["mean_rows"], 100*res["share_of_eval_rows"].get(lab, 0),
            e["rho_identity"], e["rho_pathway"], e["gain"], e["ci95"][0], e["ci95"][1], e["mde_80pct"]))
    print("  gains in order:", ["%.4f" % g for g in gains], "| monotone steps:", rising)
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
