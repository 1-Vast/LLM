"""E157: the powered version of the starvation test.

E156 starved one visible drug and evaluated on a single drug pair, which left only about 78 evaluation
keys per cell and a minimum detectable effect of roughly 0.04 - larger than the effects being compared,
so its null was uninformative. This starves EVERY drug's training support to k keys and evaluates on all
keys containing a held-out drug, which is a much larger evaluation set.

Pre-registered by extension of PROTOCOL_E146.md; the change of design is stated in the record.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r156"
LAMBDA = 1.0
REPS = 40
N_BOOT = 2000
SEED = 20261058
KS = (None, 400, 120, 40, 12)
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
        held = set(ds[:5])
        hu = np.array([x in held for x in A]); hv = np.array([z in held for z in B])
        eval_idx = np.where(hu | hv)[0]
        tr0 = np.where((~hu) & (~hv))[0]
        if len(eval_idx) < 200 or len(tr0) < 15000:
            continue
        for k in KS:
            tr = tr0
            if k is not None:
                # keep at most k keys per drug: a key survives if both its drugs still have budget
                budget = {dname: k for dname in drugs}
                keep = []
                perm = rng.permutation(len(tr0))
                for i in tr0[perm]:
                    if budget.get(A[i], 0) > 0 and budget.get(B[i], 0) > 0:
                        keep.append(i)
                        budget[A[i]] -= 1
                        budget[B[i]] -= 1
                tr = np.array(sorted(keep))
            if len(tr) < 600:
                continue
            ytr = y[tr]
            p_id = ridge_fp(Xid[tr], ytr, Xid[eval_idx])
            p_pa = ridge_fp(Xboth[tr], ytr, Xboth[eval_idx])
            yev = y[eval_idx]
            ri = spearmanr(p_id, yev).statistic
            rp = spearmanr(p_pa, yev).statistic
            rows.append({"rep": rep, "k": -1 if k is None else k, "n_train": int(len(tr)),
                         "n_eval": int(len(eval_idx)),
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "powered_starvation_test_uniform_budget_reduction",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "ks": [k if k else "all" for k in KS], "seed": SEED,
                        "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_k": {}, "files": {}}
    for k in (-1, 400, 120, 40, 12):
        sub = r[r.k == k]
        if len(sub) < 8:
            continue
        gain = sub["rho_pathway"] - sub["rho_identity"]
        rng2 = np.random.default_rng(SEED + 50 + (k if k > 0 else 0))
        boots = [float(np.mean(rng2.choice(gain.to_numpy(), size=len(gain), replace=True)))
                 for _ in range(N_BOOT)]
        res["by_k"][str(k)] = {
            "n": int(len(sub)), "mean_train": float(sub["n_train"].mean()),
            "mean_eval": float(sub["n_eval"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": float(gain.mean()),
            "gain_ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "sd": float(gain.std(ddof=1)),
            "mde_80pct": float(2.802 * gain.std(ddof=1) / np.sqrt(len(sub)))}
    if "12" in res["by_k"] and "-1" in res["by_k"]:
        g30 = (r[r.k == 12]["rho_pathway"] - r[r.k == 30]["rho_identity"]).to_numpy()
        gall = (r[r.k == -1]["rho_pathway"] - r[r.k == -1]["rho_identity"]).to_numpy()
        rng3 = np.random.default_rng(SEED + 77)
        diffs = [float(np.mean(rng3.choice(g30, size=len(g30), replace=True))
                       - np.mean(rng3.choice(gall, size=len(gall), replace=True)))
                 for _ in range(N_BOOT)]
        res["k12_minus_all"] = {"mean": float(np.mean(g30) - np.mean(gall)),
                                "ci95": [float(np.quantile(diffs, 0.025)),
                                         float(np.quantile(diffs, 0.975))],
                                "degenerate": bool(np.std(diffs) == 0.0)}
    km = res.get("k12_minus_all") or {}
    under = any(e["mde_80pct"] > abs(res["by_k"]["12"]["gain"]) for e in [res["by_k"]["12"]]) if "12" in res["by_k"] else True
    h378 = bool(km and not km.get("degenerate") and km["ci95"][0] > 0)
    res["decisions"] = {"k12_minus_all": km.get("mean"), "H378_starving_raises_the_gain": h378,
                        "H379_no_effect": not h378}
    res["decisions"]["verdict"] = (
        "starving_the_training_budget_raises_the_pathway_gain" if h378 else
        "no_resolvable_change_in_the_pathway_gain_under_budget_starvation")
    res["limits"] = ["Uniform budget reduction starves the pathway prior too, unlike E156 which left it intact.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r156/PROTOCOL_E146.md",
                "research/2026-10-27-agent-cell-identifiability-r156/e157_starve_powered.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E157_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E157_rows.csv", index=False)

    print("rows=%d" % len(r))
    for k in ("-1", "400", "120", "40", "12"):
        e = res["by_k"].get(k)
        if not e:
            continue
        print("  k=%-4s n=%3d train %.0f eval %.0f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), e["n"], e["mean_train"], e["mean_eval"],
            e["rho_identity"], e["rho_pathway"], e["gain"],
            e["gain_ci95"][0], e["gain_ci95"][1], e["mde_80pct"]))
    if km:
        print("  k12 - all: %+.4f [%+.4f,%+.4f]" % (km["mean"], km["ci95"][0], km["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
