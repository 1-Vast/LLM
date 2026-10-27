"""E157: asymmetric starvation - degrade identity for the visible drug while leaving its pathway intact.

R156 starved the training budget uniformly, so identity and the pathway prior fell together and the gap
did not move. This starves only a set of visible drugs S while their pathway-mates keep all their data,
and pools the evaluation over many unseen partners to lift n_eval from about 78 into the thousands.

Pre-registered in PROTOCOL_E147.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
sys.path.insert(0, str(ROOT / "research" / "tools"))
from feature_audit import run as audit  # noqa: E402

ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r157"
LAMBDA = 1.0
REPS = 30
N_BOOT = 2000
SEED = 20261059
KS = (None, 200, 50, 20)
N_S, N_H = 6, 10
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

    rows, audit_log = [], {}
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        S_pool = set(ds[:N_S]); H_pool = set(ds[N_S:N_S + N_H])
        inH = np.array([(x in H_pool) or (z in H_pool) for x, z in zip(A, B)])
        touched_S = np.array([(x in S_pool) or (z in S_pool) for x, z in zip(A, B)])
        eval_idx = np.where(inH & touched_S)[0]
        tr0 = np.where(~inH)[0]
        if len(eval_idx) < 400 or len(tr0) < 15000:
            continue
        for k in KS:
            tr = tr0
            if k is not None:
                budget = {s: k for s in S_pool}
                keep = []
                for i in tr0[rng.permutation(len(tr0))]:
                    sa = A[i] in S_pool; sb = B[i] in S_pool
                    if sa and budget[A[i]] <= 0:
                        continue
                    if sb and budget[B[i]] <= 0:
                        continue
                    keep.append(i)
                    if sa:
                        budget[A[i]] -= 1
                    if sb:
                        budget[B[i]] -= 1
                tr = np.array(sorted(keep))
            if len(tr) < 3000:
                continue
            ytr = y[tr]
            p_id = ridge_fp(Xid[tr], ytr, Xid[eval_idx])
            p_pa = ridge_fp(Xboth[tr], ytr, Xboth[eval_idx])
            yev = y[eval_idx]
            ri = spearmanr(p_id, yev).statistic
            rp = spearmanr(p_pa, yev).statistic
            if rep == 0:
                audit_log[str(k)] = audit(features=(Xboth[tr], Xboth[eval_idx],
                                                    ["a", "b", "ap", "lp"] * 1
                                                    + ["f%d" % i for i in range(Xboth.shape[1] - 4)]),
                                          preds={"identity": p_id, "pathway": p_pa})
            rows.append({"rep": rep, "k": -1 if k is None else k,
                         "n_train": int(len(tr)), "n_eval": int(len(eval_idx)),
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "asymmetric_starvation_of_the_visible_drug_only",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "ks": [k if k else "all" for k in KS], "seed": SEED,
                        "n_starved": N_S, "n_held": N_H, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))},
           "preflight_audit_rep0": audit_log, "by_k": {}, "files": {}}
    for k in (-1, 200, 50, 20):
        sub = r[r.k == k]
        if len(sub) < 8:
            continue
        gain = sub["rho_pathway"] - sub["rho_identity"]
        rng2 = np.random.default_rng(SEED + 60 + (k if k > 0 else 0))
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
    if "20" in res["by_k"] and "-1" in res["by_k"]:
        g20 = (r[r.k == 20]["rho_pathway"] - r[r.k == 20]["rho_identity"]).to_numpy()
        gall = (r[r.k == -1]["rho_pathway"] - r[r.k == -1]["rho_identity"]).to_numpy()
        rng3 = np.random.default_rng(SEED + 88)
        diffs = [float(np.mean(rng3.choice(g20, size=len(g20), replace=True))
                       - np.mean(rng3.choice(gall, size=len(gall), replace=True)))
                 for _ in range(N_BOOT)]
        res["k20_minus_all"] = {"mean": float(np.mean(g20) - np.mean(gall)),
                                "ci95": [float(np.quantile(diffs, 0.025)),
                                         float(np.quantile(diffs, 0.975))],
                                "dispersion": float(np.std(diffs))}
    km = res.get("k20_minus_all") or {}
    h380 = bool(km and km["dispersion"] > 0 and km["ci95"][0] > 0)
    res["decisions"] = {"k20_minus_all": km.get("mean"),
                        "H380_asymmetric_starvation_raises_the_gain": h380,
                        "H381_no_effect": not h380}
    res["decisions"]["verdict"] = (
        "the_pathway_gain_grows_when_the_visible_drug_is_starved_asymmetrically" if h380 else
        "the_pathway_gain_does_not_depend_on_the_visible_drugs_sample_size")
    res["limits"] = ["The evaluation pool mixes many held-out partners, so the rank correlation is computed on that mixture.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r157/PROTOCOL_E147.md",
                "research/2026-10-27-agent-cell-identifiability-r157/e157_asymmetric.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E157A_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E157A_rows.csv", index=False)

    print("rows=%d" % len(r))
    for k in ("-1", "200", "50", "20"):
        e = res["by_k"].get(k)
        if not e:
            continue
        print("  k=%-4s n=%3d train %.0f eval %.0f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), e["n"], e["mean_train"], e["mean_eval"],
            e["rho_identity"], e["rho_pathway"], e["gain"],
            e["gain_ci95"][0], e["gain_ci95"][1], e["mde_80pct"]))
    if km:
        print("  k20 - all: %+.4f [%+.4f,%+.4f]" % (km["mean"], km["ci95"][0], km["ci95"][1]))
    any_flag = [k for k, v in audit_log.items() if not v["passed"]]
    print("  preflight audit flagged reps:", any_flag if any_flag else "none")
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
