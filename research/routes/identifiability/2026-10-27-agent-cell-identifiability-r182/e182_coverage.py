"""E182: does the pathway prior work when the pathway level itself was never seen in training?

R149 noted in passing that about 6.2 percent of both-unseen evaluation rows carry a library pathway code
that never occurs in training, and guessed that it made the substitution effect a mild underestimate. It
was never tested. This is a genuine applicability boundary: if a drug's pathway level is absent from
training, its one-hot column is all zero there, the coefficient is zero, and the prior cannot help.

Pre-registered in PROTOCOL_E170.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r182"
REPS = 20
N_BOOT = 2000
SEED = 20261072
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
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
    ap_levels = sorted(set(AP)); lp_levels = sorted(set(LP))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(AP, ap_levels), oh(LP, lp_levels)])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        seen_ap = set(AP[tr]); seen_lp = set(LP[tr])
        ytr = y[tr]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
        ok_a = np.array([v in seen_ap for v in AP[te]])
        ok_b = np.array([v in seen_lp for v in LP[te]])
        both_seen = ok_a & ok_b
        for name, mask in (("path_seen", both_seen), ("path_partly_unseen", ~both_seen)):
            if mask.sum() < 60:
                continue
            yt = y[te][mask]
            if np.std(yt) == 0:
                continue
            ri = spearmanr(p_id[mask], yt).statistic
            rp = spearmanr(p_pa[mask], yt).statistic
            gv = (0.0 if not np.isfinite(rp) else float(rp)) - (0.0 if not np.isfinite(ri) else float(ri))
            rows.append({"rep": rep, "stratum": name, "n": int(mask.sum()),
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp),
                         "gain": gv})

    r = pd.DataFrame(rows)
    res = {"kind": "does_the_prior_need_the_pathway_level_itself_to_have_been_seen",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "lambdas": list(LAMBDAS), "folds": FOLDS,
                        "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_stratum": {}, "files": {}}
    for name in ("path_seen", "path_partly_unseen"):
        sub = r[r.stratum == name]
        if len(sub) < 8:
            continue
        v = sub["gain"].to_numpy()
        res["by_stratum"][name] = {
            "n": int(len(sub)), "mean_eval_rows": float(sub["n"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": float(v.mean()), "ci95": boot_ci(v, SEED + (1 if name == "path_seen" else 2)),
            "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(v)))}
        if name == "path_partly_unseen":
            res["fraction_partly_unseen_rows"] = float(
                (sub["n"].sum()) / (r.groupby("stratum")["n"].sum().sum()))
    seen = res["by_stratum"].get("path_seen", {})
    uns = res["by_stratum"].get("path_partly_unseen", {})
    h428 = bool(seen and uns and seen["ci95"][0] > 0 and uns["ci95"][0] <= 0)
    h429 = bool(seen and uns and seen["ci95"][0] > 0 and uns["ci95"][0] > 0)
    res["decisions"] = {"H428_prior_needs_the_level_seen": h428, "H429_prior_works_anyway": h429}
    res["decisions"]["verdict"] = (
        "the_prior_helps_only_where_the_pathway_level_was_observed_and_is_inert_otherwise" if h428 else
        "the_prior_helps_even_when_the_pathway_level_was_never_observed" if h429 else
        "neither_stratum_shows_a_clean_pattern")
    res["limits"] = ["Grouping is by whether the level ever occurred, not by how often.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r182/PROTOCOL_E170.md",
                "research/2026-10-27-agent-cell-identifiability-r182/e182_coverage.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E182_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E182_rows.csv", index=False)

    for name, e in res["by_stratum"].items():
        print("  [%-18s] n=%3d rows/rep %5.1f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            name, e["n"], e["mean_eval_rows"], e["rho_identity"], e["rho_pathway"],
            e["gain"], e["ci95"][0], e["ci95"][1], e["mde_80pct"]))
    print("  fraction of eval rows with an unseen pathway level: %s" % res.get("fraction_partly_unseen_rows"))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
