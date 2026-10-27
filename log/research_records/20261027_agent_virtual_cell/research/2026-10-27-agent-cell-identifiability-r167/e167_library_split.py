"""E167: split by the library-side pathway, and check whether pathway-over-target ever reverses.

R166 split by the visible (anchor) side and found the gain spread but heterogeneous. Two things remained:
whether the library side behaves the same way, and whether the pathway-over-target ordering that the
practitioner rule rests on survives at level granularity.

Pre-registered in PROTOCOL_E155.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r167"
REPS = 40
N_BOOT = 2000
SEED = 20261068
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
MIN_SUB = 200
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "ANCHOR_TARGET", "LIBRARY_TARGET", "SYNERGY_DELTA_EMAX"]


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
        lp=("LIBRARY_PATHWAY", "first"), at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"),
        emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); LP = g["lp"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xt = np.hstack([oh(g["at"].to_numpy(), sorted(g["at"].unique())),
                    oh(g["lt"].to_numpy(), sorted(g["lt"].unique()))])
    Xp_all = np.hstack([Xid, Xp]); Xt_all = np.hstack([Xid, Xt])
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
        p_pa = fit_arm(Xp_all[tr], ytr, Xp_all[te_all], LAMBDAS, SEED + rep)
        p_tg = fit_arm(Xt_all[tr], ytr, Xt_all[te_all], LAMBDAS, SEED + rep + 7)
        for lvl in np.unique(LP[te_all]):
            mask = LP[te_all] == lvl
            if mask.sum() < MIN_SUB:
                continue
            yt = y[te_all][mask]
            if np.std(yt) == 0:
                continue
            ri = spearmanr(p_id[mask], yt).statistic
            rp = spearmanr(p_pa[mask], yt).statistic
            rt = spearmanr(p_tg[mask], yt).statistic
            per_level.setdefault(str(lvl), []).append(
                {"rep": rep, "n": int(mask.sum()),
                 "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                 "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp),
                 "rho_target": 0.0 if not np.isfinite(rt) else float(rt)})

    rows = []
    for lvl, recs in per_level.items():
        s = pd.DataFrame(recs)
        gp = (s["rho_pathway"] - s["rho_identity"]).to_numpy()
        gt = (s["rho_target"] - s["rho_identity"]).to_numpy()
        dp = (s["rho_pathway"] - s["rho_target"]).to_numpy()
        rng2 = np.random.default_rng(SEED + 1100 + (hash(lvl) % 89))
        bp = [float(np.mean(rng2.choice(gp, size=len(gp), replace=True))) for _ in range(N_BOOT)]
        bd = [float(np.mean(rng2.choice(dp, size=len(dp), replace=True))) for _ in range(N_BOOT)]
        rows.append({"level": lvl, "n_reps": int(len(s)), "mean_eval_rows": float(s["n"].mean()),
                     "rho_identity": float(s["rho_identity"].mean()),
                     "gain_pathway": float(gp.mean()),
                     "gain_target": float(gt.mean()),
                     "pathway_minus_target": float(dp.mean()),
                     "pmt_ci95": [float(np.quantile(bd, 0.025)), float(np.quantile(bd, 0.975))],
                     "gain_pathway_ci95": [float(np.quantile(bp, 0.025)), float(np.quantile(bp, 0.975))],
                     "mde_80pct": float(2.802 * dp.std(ddof=1) / np.sqrt(len(dp)))})
    L = pd.DataFrame(rows).sort_values("pathway_minus_target", ascending=False).reset_index(drop=True)

    neg_pmt = L[L["pathway_minus_target"] < 0]
    pos_gain = L[L["gain_pathway"] > 0]
    res = {"kind": "library_side_split_and_whether_pathway_over_target_reverses",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "min_subset_rows": MIN_SUB,
                        "lambdas": list(LAMBDAS), "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "levels_analysed": int(len(L))},
           "per_level": L.to_dict(orient="records"),
           "summary": {"n_levels": int(len(L)),
                       "n_pathway_gain_positive": int(len(pos_gain)),
                       "n_pmt_negative": int(len(neg_pmt)),
                       "pmt_significantly_negative": [r["level"] for _, r in neg_pmt.iterrows()
                                                       if r["pmt_ci95"][1] < 0]},
           "files": {}}
    s = res["summary"]
    h398 = bool(s["n_pathway_gain_positive"] >= 0.5 * s["n_levels"] and s["n_pmt_negative"] <= 1)
    h399 = bool(s["n_pmt_negative"] >= 2)
    res["decisions"] = {"H398_consistent_and_robust": h398, "H399_reversal_appears": h399}
    res["decisions"]["verdict"] = (
        "the_library_side_behaves_like_the_anchor_side_and_pathway_beats_target_everywhere_it_matters" if h398 else
        "pathway_over_target_reverses_in_some_levels_so_the_rule_needs_a_named_exception_list")
    res["limits"] = ["Subsets are small; every minimum detectable effect is reported.",
                     "Reversals in thin subsets are recorded with their key counts so they can be told apart from noise.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r167/PROTOCOL_E155.md",
                "research/2026-10-27-agent-cell-identifiability-r167/e167_library_split.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E167_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    L.to_csv(OUT / "E167_levels.csv", index=False)

    print("levels analysed: %d" % len(L))
    print("  %-30s %5s %7s %9s %9s %10s" % ("level", "reps", "evalN", "gain_path", "gain_tgt", "path-tgt"))
    for _, r in L.iterrows():
        print("  %-30s %5d %7.0f %+9.4f %+9.4f  %+.4f [%+.4f,%+.4f]" % (
            str(r["level"])[:30], r["n_reps"], r["mean_eval_rows"], r["gain_pathway"],
            r["gain_target"], r["pathway_minus_target"], r["pmt_ci95"][0], r["pmt_ci95"][1]))
    print("  pathway gain positive: %d / %d ; pathway-target negative: %d" % (
        s["n_pathway_gain_positive"], s["n_levels"], s["n_pmt_negative"]))
    print("  significantly negative path-target:", s["pmt_significantly_negative"])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
