"""E163: the frozen claim's headline number, recomputed with a tuned penalty.

The both-unseen gain of about +0.13 Spearman was measured at lambda equal to 1. R162 found inner
cross-validation picks lambda near 54 for this feature count, so that headline has never been checked
at a tuned penalty. This does the check on the cell the claim actually rests on.

Pre-registered in PROTOCOL_E151.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r163"
REPS = 40
N_BOOT = 2000
SEED = 20261065
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
HISTORICAL = 0.13
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
    return ym + Zte @ ww, best


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
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        for pool_name, te in (("both_unseen", np.where(au & bu)[0]),
                              ("one_unseen", np.where(au ^ bu)[0])):
            if len(te) < 150:
                continue
            ytr = y[tr]; yte = y[te]
            p_id, lam_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
            p_pa, lam_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
            ri = spearmanr(p_id, yte).statistic
            rp = spearmanr(p_pa, yte).statistic
            rows.append({"rep": rep, "pool": pool_name, "n_eval": int(len(te)),
                         "lam_identity": lam_id, "lam_pathway": lam_pa,
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "frozen_claim_headline_with_tuned_lambda",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "lambdas": list(LAMBDAS), "folds": FOLDS,
                        "historical_value": HISTORICAL, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_pool": {}, "files": {}}
    for pool in ("both_unseen", "one_unseen"):
        sub = r[r.pool == pool]
        if len(sub) < 10:
            continue
        gain = (sub["rho_pathway"] - sub["rho_identity"]).to_numpy()
        rng2 = np.random.default_rng(SEED + 700 + (0 if pool == "both_unseen" else 1))
        boots = [float(np.mean(rng2.choice(gain, size=len(gain), replace=True))) for _ in range(N_BOOT)]
        res["by_pool"][pool] = {
            "n": int(len(sub)), "mean_eval": float(sub["n_eval"].mean()),
            "lam_identity": float(sub["lam_identity"].mean()),
            "lam_pathway": float(sub["lam_pathway"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": float(gain.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "mde_80pct": float(2.802 * gain.std(ddof=1) / np.sqrt(len(sub)))}
    both = res["by_pool"].get("both_unseen", {})
    new_gain = both.get("gain")
    rel = abs(new_gain - HISTORICAL) / HISTORICAL if new_gain is not None else None
    h390 = bool(rel is not None and rel > 0.20)
    res["decisions"] = {"new_gain_both_unseen": new_gain, "historical": HISTORICAL,
                        "relative_change": rel,
                        "H390_headline_must_change": h390, "H391_headline_stands": not h390}
    res["decisions"]["verdict"] = (
        "the_headline_number_changes_materially_under_a_tuned_penalty" if h390 else
        "the_headline_number_is_stable_under_a_tuned_penalty")
    res["limits"] = ["The historical value came from different seeds and a different split implementation, so this compares magnitudes rather than exact numbers.",
                     "Only ridge and one resource; three inner folds.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel_path in ("research/2026-10-27-agent-cell-identifiability-r163/PROTOCOL_E151.md",
                     "research/2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py"):
        p = ROOT / rel_path
        if p.exists():
            res["files"][rel_path] = sha256(p)
    (OUT / "E163_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E163_rows.csv", index=False)

    print("rows=%d" % len(r))
    for pool, e in res["by_pool"].items():
        print("  [%-11s] n=%3d eval %6.0f lam_id %6.1f lam_path %6.1f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            pool, e["n"], e["mean_eval"], e["lam_identity"], e["lam_pathway"],
            e["rho_identity"], e["rho_pathway"], e["gain"], e["ci95"][0], e["ci95"][1], e["mde_80pct"]))
    print("  historical %.3f vs new %s -> relative change %s" % (
        HISTORICAL, ("%.4f" % new_gain) if new_gain is not None else "n/a",
        ("%.1f%%" % (100 * rel)) if rel is not None else "n/a"))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
