"""E188: does active learning help at the data-starved end?

R187 found no advantage for uncertainty-based pair selection when the initial training set held 60 percent
of the pairs, and attributed that to the estimate being saturated. That attribution makes a testable
prediction: if saturation is the reason, a smaller initial training set should let active learning show an
advantage. This sweeps the initial fraction and looks for that boundary.

Pre-registered in PROTOCOL_E176.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r188"
REPS = 10
N_BOOT_MODELS = 10
N_ACQUIRE = 50
N_BOOT_CI = 2000
SEED = 20261080
FRACS = (0.15, 0.30, 0.60)
LAM = 54.0
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


def fit_ridge(Xtr, ytr, Xte, lam=LAM):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def gain_on_eval(tr_idx, te_idx, Xid, Xboth, y):
    ytr = y[tr_idx]
    p_id = fit_ridge(Xid[tr_idx], ytr, Xid[te_idx])
    p_pa = fit_ridge(Xboth[tr_idx], ytr, Xboth[te_idx])
    yte = y[te_idx]
    ri = spearmanr(p_id, yte).statistic
    rp = spearmanr(p_pa, yte).statistic
    return (0.0 if not np.isfinite(rp) else float(rp)) - (0.0 if not np.isfinite(ri) else float(ri))


def boot_ci(v, seed):
    rng = np.random.default_rng(seed)
    bs = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT_CI)]
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
    g["pair"] = g["a"] + "|" + g["b"]

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    pair = g["pair"].to_numpy()
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        pool = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(pool) < 20000 or len(te) < 150:
            continue
        pairs = np.unique(pair[pool]); rng.shuffle(pairs)
        for frac in FRACS:
            n_init = max(1, int(frac * len(pairs)))
            init_pairs = set(pairs[:n_init]); cand_pairs = pairs[n_init:]
            if len(cand_pairs) < N_ACQUIRE:
                continue
            init_idx = pool[np.array([p in init_pairs for p in pair[pool]])]
            cand_idx = pool[np.array([p in cand_pairs for p in pair[pool]])]
            if len(init_idx) < 3000:
                continue
            g0 = gain_on_eval(init_idx, te, Xid, Xboth, y)
            cand_rows = {p: cand_idx[pair[cand_idx] == p] for p in cand_pairs}
            rep_rows = np.array([cand_rows[p][0] for p in cand_pairs])
            preds = []
            for b in range(N_BOOT_MODELS):
                rb = np.random.default_rng(SEED + 1000 + rep * 31 + b + int(frac * 100))
                boot_idx = rb.choice(init_idx, size=len(init_idx), replace=True)
                preds.append(fit_ridge(Xboth[boot_idx], y[boot_idx], Xboth[rep_rows]))
            unc = np.vstack(preds).std(axis=0)
            pick_unc = [cand_pairs[i] for i in np.argsort(-unc)[:N_ACQUIRE]]
            rb2 = np.random.default_rng(SEED + 9000 + rep + int(frac * 100))
            pick_rand = list(rb2.choice(cand_pairs, size=N_ACQUIRE, replace=False))
            gA = gain_on_eval(np.concatenate([init_idx, cand_idx[np.isin(pair[cand_idx], pick_unc)]]),
                              te, Xid, Xboth, y)
            gB = gain_on_eval(np.concatenate([init_idx, cand_idx[np.isin(pair[cand_idx], pick_rand)]]),
                              te, Xid, Xboth, y)
            rows.append({"rep": rep, "frac": frac, "gain_before": g0,
                         "delta_unc": gA - g0, "delta_rand": gB - g0,
                         "init_rows": int(len(init_idx))})

    r = pd.DataFrame(rows)
    res = {"kind": "does_active_learning_help_at_the_data_starved_end",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "fracs": list(FRACS), "n_acquire": N_ACQUIRE,
                        "n_bootstrap_models": N_BOOT_MODELS, "seed": SEED, "lambda": LAM},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_frac": {}, "files": {}}
    for frac in FRACS:
        sub = r[r.frac == frac]
        if len(sub) < 5:
            continue
        diff = (sub["delta_unc"] - sub["delta_rand"]).to_numpy()
        res["by_frac"][str(frac)] = {
            "n": int(len(sub)), "mean_init_rows": float(sub["init_rows"].mean()),
            "gain_before": float(sub["gain_before"].mean()),
            "delta_unc": float(sub["delta_unc"].mean()),
            "delta_rand": float(sub["delta_rand"].mean()),
            "difference": float(diff.mean()),
            "ci95": boot_ci(diff, SEED + int(frac * 1000)),
            "mde_80pct": float(2.802 * diff.std(ddof=1) / np.sqrt(len(diff)))}
    any_pos = [k for k, v in res["by_frac"].items() if v["ci95"][0] > 0]
    diffs = {float(k): v["difference"] for k, v in res["by_frac"].items()}
    shrinking = (len(diffs) == 3 and diffs[0.15] > diffs[0.30] > diffs[0.60])
    res["decisions"] = {"any_positive": any_pos, "monotone_decreasing": bool(shrinking),
                        "H440_helps_when_starved": bool(any_pos),
                        "H441_no_advantage_anywhere": not any_pos}
    res["decisions"]["verdict"] = (
        "active_learning_shows_an_advantage_only_when_the_training_set_is_small" if any_pos else
        "active_learning_shows_no_advantage_at_any_initial_fraction_tested")
    res["limits"] = ["Fifty pairs acquired; initial fraction swept but k not.",
                     "Ten splits per fraction, so power is limited and every minimum detectable effect is reported.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r188/PROTOCOL_E176.md",
                "research/2026-10-27-agent-cell-identifiability-r188/e188_starvation.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E188_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E188_rows.csv", index=False)

    for k, v in res["by_frac"].items():
        print("  frac %-5s init %5.0f rows | gain_before %+.4f | d_unc %+.4f d_rand %+.4f | diff %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            k, v["mean_init_rows"], v["gain_before"], v["delta_unc"], v["delta_rand"],
            v["difference"], v["ci95"][0], v["ci95"][1], v["mde_80pct"]))
    print("  monotone decreasing:", shrinking, "| any positive:", any_pos)
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
