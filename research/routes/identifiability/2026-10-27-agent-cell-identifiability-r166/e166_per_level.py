"""E166: is the pathway gain spread across pathway levels, or carried by a few?

The frozen claim reports an overall gain of about +0.118 in the both-unseen cell. That leaves an
applicability question untested: does the gain hold across the 38 pathway levels, or does a handful of
well-populated levels carry it? If the latter, the practitioner rule needs a coverage caveat.

Pre-registered in PROTOCOL_E154.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r166"
REPS = 40
N_BOOT = 2000
SEED = 20261067
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
MIN_SUB = 200
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

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); AP = g["ap"].to_numpy()
    drugs = sorted(set(A) | set(B))
    ap_levels = sorted(g["ap"].unique())
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), ap_levels), oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    per_level = {}
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te_all = np.where(au & bu)[0]
        if len(te_all) < 150:
            continue
        ytr = y[tr]
        p_id = fit_arm(Xid[tr], ytr, Xid[te_all], LAMBDAS, SEED + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te_all], LAMBDAS, SEED + rep)
        for lvl in np.unique(AP[te_all]):
            mask = AP[te_all] == lvl
            if mask.sum() < MIN_SUB:
                continue
            yt = y[te_all][mask]
            if np.std(yt) == 0:
                continue
            ri = spearmanr(p_id[mask], yt).statistic
            rp = spearmanr(p_pa[mask], yt).statistic
            per_level.setdefault(str(lvl), []).append(
                {"rep": rep, "n": int(mask.sum()),
                 "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                 "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    rows = []
    for lvl, recs in per_level.items():
        s = pd.DataFrame(recs)
        gain = (s["rho_pathway"] - s["rho_identity"]).to_numpy()
        rng2 = np.random.default_rng(SEED + 1000 + (hash(lvl) % 89))
        boots = [float(np.mean(rng2.choice(gain, size=len(gain), replace=True))) for _ in range(N_BOOT)]
        rows.append({"level": lvl, "n_reps": int(len(s)), "mean_eval_rows": float(s["n"].mean()),
                     "rho_identity": float(s["rho_identity"].mean()),
                     "rho_pathway": float(s["rho_pathway"].mean()),
                     "gain": float(gain.mean()),
                     "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                     "mde_80pct": float(2.802 * gain.std(ddof=1) / np.sqrt(len(gain)))})
    L = pd.DataFrame(rows).sort_values("gain", ascending=False).reset_index(drop=True)

    pos = L[L["gain"] > 0]
    total_pos = float(pos["gain"].sum())
    top3 = float(pos["gain"].head(3).sum())
    res = {"kind": "is_the_pathway_gain_spread_or_concentrated",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "min_subset_rows": MIN_SUB,
                        "lambdas": list(LAMBDAS), "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "levels_analysed": int(len(L))},
           "per_level": L.to_dict(orient="records"),
           "concentration": {"n_levels": int(len(L)), "n_positive": int((L["gain"] > 0).sum()),
                             "n_positive_ci_excludes_zero": int(
                                 ((L["ci95"].apply(lambda c: c[0] > 0))) .sum()),
                             "sum_positive_gain": total_pos,
                             "top3_share_of_positive": (top3 / total_pos) if total_pos > 0 else None,
                             "spread_of_gains": float(L["gain"].std(ddof=1))},
           "files": {}}
    conc = res["concentration"]
    h396 = bool(conc["n_positive"] >= 0.5 * conc["n_levels"]
                and (conc["top3_share_of_positive"] is not None and conc["top3_share_of_positive"] < 0.60))
    res["decisions"] = {"H396_spread": h396, "H397_concentrated": not h396}
    res["decisions"]["verdict"] = (
        "the_gain_is_spread_across_pathway_levels_so_no_coverage_caveat_is_needed" if h396 else
        "the_gain_is_concentrated_in_a_few_levels_so_the_rule_needs_a_coverage_caveat")
    res["limits"] = ["Subsets are defined by the anchor drug's pathway; the library side is not split separately.",
                     "Subsets are small and each minimum detectable effect is reported; small-subset gains are not treated as individual conclusions.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r166/PROTOCOL_E154.md",
                "research/2026-10-27-agent-cell-identifiability-r166/e166_per_level.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E166_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    L.to_csv(OUT / "E166_levels.csv", index=False)

    print("levels analysed: %d" % len(L))
    print("  %-28s %6s %8s %8s %8s %22s" % ("level", "reps", "evalN", "rho_id", "rho_path", "gain [CI]"))
    for _, r in L.head(10).iterrows():
        print("  %-28s %6d %8.0f %+8.4f %+8.4f  %+.4f [%+.4f,%+.4f]" % (
            str(r["level"])[:28], r["n_reps"], r["mean_eval_rows"], r["rho_identity"],
            r["rho_pathway"], r["gain"], r["ci95"][0], r["ci95"][1]))
    print("  ... %d more levels" % max(0, len(L) - 10))
    print("  positive levels: %d / %d   top3 share of positive gain: %s" % (
        conc["n_positive"], conc["n_levels"],
        ("%.1f%%" % (100 * conc["top3_share_of_positive"])) if conc["top3_share_of_positive"] is not None else "n/a"))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
