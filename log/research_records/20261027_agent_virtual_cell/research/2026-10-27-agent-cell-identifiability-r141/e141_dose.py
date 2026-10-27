"""E141: dose-response of the substitution effect to the fraction of correct group content.

R140 established the two endpoints: a fully random grouping gives +0.0046 and the real one +0.1343.
This sweeps the fraction of drugs whose group assignment is corrupted, so that "content matters"
becomes a graded quantity rather than a binary contrast.

Pre-registered in PROTOCOL_E131.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r141"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261044
FRACTIONS = (0.00, 0.25, 0.50, 0.75, 1.00)
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    m = len(j)
    if m < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=m, replace=True))) for _ in range(N_BOOT)]
    return {"n": int(m), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def oh(vals, levels):
    idx = {v: j for j, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            M[t, j] = 1.0
    return M


def ridge_fp(Xtr, ytr, Xte, lam=LAMBDA):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    ap_lv = sorted(g["ap"].unique()); lp_lv = sorted(g["lp"].unique())
    n_ap, n_lp = len(ap_lv), len(lp_lv)
    ap_idx = {v: i for i, v in enumerate(ap_lv)}
    lp_idx = {v: i for i, v in enumerate(lp_lv)}
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    a_code = pd.Categorical(g["a"], categories=drugs).codes
    b_code = pd.Categorical(g["b"], categories=drugs).codes
    # real group per drug, per side (a drug maps to exactly one level, verified in R136)
    a_real = np.zeros(len(drugs), dtype=int); b_real = np.zeros(len(drugs), dtype=int)
    for i, dr in enumerate(drugs):
        m = A == dr
        a_real[i] = ap_idx[g["ap"].to_numpy()[np.where(m)[0][0]]] if m.any() else 0
        m2 = B == dr
        b_real[i] = lp_idx[g["lp"].to_numpy()[np.where(m2)[0][0]]] if m2.any() else 0
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        te = np.where(au & bu)[0]; tr = np.where((~au) & (~bu))[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr, yte = y[tr], y[te]
        base_id = ridge_fp(Xid[tr], ytr, Xid[te])
        row = {"rep": rep, "n_eval": len(te),
               "identity": 0.0 if np.std(base_id) == 0 else float(spearmanr(base_id, yte).statistic)}
        for f in FRACTIONS:
            a_grp = a_real.copy(); b_grp = b_real.copy()
            n_corr = int(round(f * len(drugs)))
            if n_corr > 0:
                who = rng.choice(len(drugs), size=n_corr, replace=False)
                a_grp[who] = rng.integers(0, n_ap, size=n_corr)
                b_grp[who] = rng.integers(0, n_lp, size=n_corr)
            Xc = np.hstack([oh(a_grp[a_code], list(range(n_ap))), oh(b_grp[b_code], list(range(n_lp)))])
            XX = np.hstack([Xid, Xc])
            p = ridge_fp(XX[tr], ytr, XX[te])
            row["f%.2f" % f] = 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "dose_response_of_substitution_to_content_corruption",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "fractions": list(FRACTIONS),
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_fraction": {}, "files": {}}
    res["identity_rho"] = float(r["identity"].mean())
    for f in FRACTIONS:
        col = "f%.2f" % f
        e = {"rho": float(r[col].mean()), "vs_identity": paired(r[col], r["identity"], 63001 + int(f * 100))}
        if f > 0:
            e["vs_uncorrupted"] = paired(r[col], r["f0.00"], 63101 + int(f * 100))
        res["by_fraction"][col] = e
    rhos = [res["by_fraction"]["f%.2f" % f]["rho"] for f in FRACTIONS]
    monotone = all(rhos[i] >= rhos[i + 1] for i in range(len(rhos) - 1))
    sig_drops = sum(1 for f in (0.25, 0.50, 0.75, 1.00)
                    if res["by_fraction"]["f%.2f" % f]["vs_uncorrupted"]
                    and res["by_fraction"]["f%.2f" % f]["vs_uncorrupted"]["ci95"][1] < 0)
    res["decisions"] = {"rhos": rhos, "monotone": bool(monotone),
                        "significant_drops_vs_uncorrupted": int(sig_drops),
                        "H348_graded_dose_response": bool(monotone and sig_drops >= 2),
                        "H349_threshold_like": bool(not monotone or sig_drops <= 1)}
    res["decisions"]["verdict"] = (
        "content_contributes_graded_with_a_clear_dose_response" if res["decisions"]["H348_graded_dose_response"] else
        "the_effect_is_threshold_like_not_graded")
    res["limits"] = ["Corruption is by proportion and slightly changes group sizes.",
                     "Only the both-unseen condition and only ridge.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r141/PROTOCOL_E131.md",
                "research/2026-10-27-agent-cell-identifiability-r141/e141_dose.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E141_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E141_rows.csv", index=False)

    print("rows=%d  identity rho %.4f" % (len(r), res["identity_rho"]))
    for f in FRACTIONS:
        col = "f%.2f" % f
        e = res["by_fraction"][col]
        line = "  f=%.2f  rho %.4f  vs identity %+.4f [%+.4f,%+.4f]" % (
            f, e["rho"], e["vs_identity"]["mean_diff"], e["vs_identity"]["ci95"][0], e["vs_identity"]["ci95"][1])
        if "vs_uncorrupted" in e:
            u = e["vs_uncorrupted"]
            line += "   vs f0 %+.4f [%+.4f,%+.4f]" % (u["mean_diff"], u["ci95"][0], u["ci95"][1])
        print(line)
    print("DECISIONS:", json.dumps({k: v for k, v in res["decisions"].items() if k != "rhos"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
