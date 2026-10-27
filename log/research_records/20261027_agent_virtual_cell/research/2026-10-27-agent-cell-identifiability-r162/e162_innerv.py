"""E162: inner cross-validated lambda, Spearman metric, budget curve redone.

R160 showed that holding lambda fixed while n varies confounds information with regularisation. R161
patched this with lambda proportional to n, which is a convention rather than a fit. This selects lambda
by three-fold internal cross-validation on the training set, separately for each arm, and scores with
Spearman so the minimum detectable effect is not of the same order as the effect.

Pre-registered in PROTOCOL_E150.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r162"
REPS = 20
N_BOOT = 2000
SEED = 20261064
KS = (None, 400, 120)
LAMBDAS = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)
FOLDS = 3
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


def gram(Z, yc):
    return Z.T @ Z, Z.T @ yc


def solve_path(G, b, lams):
    """Solve (G + lam I) w = b for every lambda; G is shared so this is cheap."""
    out = {}
    d = np.diag(G).copy()
    for lam in lams:
        A = G + np.diag(lam + 1e-9 * (d + 1.0))
        out[lam] = np.linalg.solve(A, b)
    return out


def predict(Zte, w, ymean, mu, sd):
    return ymean + (((Zte - mu) / sd) @ w)


def fit_arm(Xtr, ytr, Xte, lams, seed, folds=FOLDS):
    """Choose lambda by internal k-fold CV on Spearman, then predict the evaluation set."""
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    Zte = (Xte - mu) / sd
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(Z))
    chunks = np.array_split(order, folds)
    score = {lam: [] for lam in lams}
    for f in range(folds):
        va = chunks[f]
        tr = np.setdiff1d(np.arange(len(Z)), va)
        ym = Z[tr].mean(0)  # not used directly; kept for clarity
        ytr_mean = ytr[tr].mean()
        G, b = gram(Z[tr], ytr[tr] - ytr_mean)
        ws = solve_path(G, b, lams)
        yv = ytr[va]
        for lam, w in ws.items():
            p = ytr_mean + Z[va] @ w
            if np.std(p) == 0:
                score[lam].append(-2.0)
            else:
                s = spearmanr(p, yv).statistic
                score[lam].append(0.0 if not np.isfinite(s) else float(s))
    best = max(lams, key=lambda lam: float(np.mean(score[lam])))
    ytr_mean = ytr.mean()
    G, b = gram(Z, ytr - ytr_mean)
    w = solve_path(G, b, [best])[best]
    return predict(Zte, w, ytr_mean, 0.0, 1.0), best


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
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpath = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xpath])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[:12])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        te = np.where(au ^ bu)[0]
        if len(te) < 200:
            continue
        for k in KS:
            tr = np.where((~au) & (~bu))[0]
            if k is not None:
                budget = {dn: k for dn in drugs}
                keep = []
                for i in tr[rng.permutation(len(tr))]:
                    if budget.get(A[i], 0) > 0 and budget.get(B[i], 0) > 0:
                        keep.append(i); budget[A[i]] -= 1; budget[B[i]] -= 1
                tr = np.array(sorted(keep))
            if len(tr) < 500:
                continue
            ytr = y[tr]; yte = y[te]
            p_id, lam_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
            p_pa, lam_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
            ri = spearmanr(p_id, yte).statistic
            rp = spearmanr(p_pa, yte).statistic
            rows.append({"rep": rep, "k": -1 if k is None else k, "n_train": int(len(tr)),
                         "lam_identity": lam_id, "lam_pathway": lam_pa,
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "inner_cv_lambda_with_spearman_metric",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "ks": [k if k else "all" for k in KS], "seed": SEED,
                        "lambdas": list(LAMBDAS), "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_k": {}, "files": {}}
    for k in (-1, 400, 120):
        sub = r[r.k == k]
        if len(sub) < 8:
            continue
        gain = (sub["rho_pathway"] - sub["rho_identity"]).to_numpy()
        rng2 = np.random.default_rng(SEED + 500 + (k if k > 0 else 0))
        boots = [float(np.mean(rng2.choice(gain, size=len(gain), replace=True))) for _ in range(N_BOOT)]
        res["by_k"][str(k)] = {
            "n": int(len(sub)), "mean_train": float(sub["n_train"].mean()),
            "lam_identity": float(sub["lam_identity"].mean()),
            "lam_pathway": float(sub["lam_pathway"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": float(gain.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "mde_80pct": float(2.802 * gain.std(ddof=1) / np.sqrt(len(sub)))}
    lo = [v["ci95"][0] for v in res["by_k"].values()]
    h388 = bool(lo and all(x > 0 for x in lo))
    full = res["by_k"].get("-1", {})
    h389 = bool(full and full["ci95"][0] <= 0 and any(
        v["ci95"][0] > 0 for kk, v in res["by_k"].items() if kk != "-1"))
    res["decisions"] = {"H388_resolvable_everywhere": h388, "H389_vanishes_with_full_data": h389}
    res["decisions"]["verdict"] = (
        "with_lambda_tuned_the_gain_is_resolvable_at_every_budget" if h388 else
        "the_gain_still_vanishes_with_full_data_even_with_tuned_lambda" if h389 else
        "neither_pattern_is_clean")
    res["does_lambda_track_n"] = {
        "lam_at_full": full.get("lam_pathway"), "lam_at_k400": res["by_k"].get("400", {}).get("lam_pathway"),
        "lam_at_k120": res["by_k"].get("120", {}).get("lam_pathway"),
        "means": ("increases with n" if full and res["by_k"].get("400")
                  and full.get("lam_pathway", 0) > res["by_k"]["400"]["lam_pathway"] else "does not increase with n"),
        "note": "if lambda rises with n, the R161 convention of lambda proportional to n is supported by the data rather than imposed"}
    res["limits"] = ["Only ridge and one resource; three inner folds.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r162/PROTOCOL_E150.md",
                "research/2026-10-27-agent-cell-identifiability-r162/e162_innerv.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E162_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E162_rows.csv", index=False)

    print("rows=%d" % len(r))
    for k in ("-1", "400", "120"):
        e = res["by_k"].get(k)
        if not e:
            continue
        print("  k=%-5s train %7.0f lam_id %6.2f lam_path %6.2f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), e["mean_train"], e["lam_identity"], e["lam_pathway"],
            e["rho_identity"], e["rho_pathway"], e["gain"], e["ci95"][0], e["ci95"][1], e["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))
    print("lambda vs n:", res["does_lambda_track_n"]["means"])


if __name__ == "__main__":
    main()
