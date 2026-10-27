"""E033: budgeted decision evaluation - which k (cell, combination) keys should be measured?

Pre-registered in PROTOCOL_E033.md. Reads only the local Jaaks 2022 GDSC file.

Features never encode drug or cell identity. Ridge with a fixed penalty gives both a
prediction and a posterior variance; selection strategies use only those. Success is the
REALISED synergy of the selected keys, not a ranking proxy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r33"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (20, 50, 100, 200)
REPEATS = 10
N_BOOT = 1000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), tissue=("Tissue", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("ap", "lp", "tissue"):
        d[c] = d[c].astype(str).fillna("NA")

    pa = sorted(d["ap"].unique())
    pl = sorted(d["lp"].unique())
    ti = sorted(d["tissue"].unique())
    X = np.zeros((len(d), len(pa) + len(pl) + len(ti)))
    for k, v in enumerate(pa):
        X[:, k] = (d["ap"] == v).to_numpy(float)
    o = len(pa)
    for k, v in enumerate(pl):
        X[:, o + k] = (d["lp"] == v).to_numpy(float)
    o2 = o + len(pl)
    for k, v in enumerate(ti):
        X[:, o2 + k] = (d["tissue"] == v).to_numpy(float)
    y = d["synergy"].to_numpy(float)
    syn = d["syn"].to_numpy(bool)
    # SIGN CORRECTION: SYNERGY_DELTA_AUC is EXP - OBS, so HIGHER = more synergistic.
    # The first run used the bottom decile (antagonism); preserved as *_INVALID_SIGNS.
    thr = float(np.quantile(y, 0.90))  # strong synergy = TOP decile of delta AUC
    strong = y >= thr

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        n = len(d)
        perm = rng.permutation(n)
        ntr = int(0.8 * n)
        tr, te = perm[:ntr], perm[ntr:]
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Xte = (X[te] - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())
        pred = ytr.mean() + Xte @ w           # higher = more synergistic
        var = np.einsum("ij,jk,ik->i", Xte, Ainv, Xte)
        for k in KS:
            if k >= len(te) // 4:
                continue
            strategies = {
                "random": rng.permutation(len(te))[:k],
                "exploit": np.argsort(-pred)[:k],
                "explore": np.argsort(-var)[:k],
                "mix": np.argsort(-(pd.Series(pred).rank(pct=True).to_numpy()
                                   + pd.Series(var).rank(pct=True).to_numpy()))[:k],
            }
            for name, idx in strategies.items():
                rows.append({"rep": rep, "k": k, "strategy": name,
                             "hit_syn": float(syn[te][idx].mean()),
                             "hit_strong": float(strong[te][idx].mean()),
                             "mean_synergy": float(y[te][idx].mean()),
                             "best_synergy": float(y[te][idx].max()),
                             "pool_syn_rate": float(syn[te].mean()),
                             "pool_strong_rate": float(strong[te].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "budgeted_decision_evaluation_on_gdsc_sign_corrected",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "cells": int(d["cell"].nunique()),
                     "synergy_rate": float(syn.mean()), "strong_threshold": thr,
                     "strong_rate": float(strong.mean()), "repeats": int(r["rep"].nunique())},
           "by_k": {}, "files": {}}

    def cmp(sub, a, b, metric):
        A = sub[sub.strategy == a].groupby("rep")[metric].mean()
        B = sub[sub.strategy == b].groupby("rep")[metric].mean()
        j = pd.concat([A.rename("a"), B.rename("b")], axis=1).dropna()
        if len(j) < 3:
            return None
        dif = (j["a"] - j["b"]).to_numpy(float)
        rng2 = np.random.default_rng(SEED + 7)
        boots = [float(np.mean(rng2.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                "a_mean": float(j["a"].mean()), "b_mean": float(j["b"].mean())}

    for k in KS:
        sub = r[r["k"] == k]
        if not len(sub):
            continue
        res["by_k"][str(k)] = {
            "precision_syn": {s: float(g["hit_syn"].mean()) for s, g in sub.groupby("strategy")},
            "precision_strong": {s: float(g["hit_strong"].mean()) for s, g in sub.groupby("strategy")},
            "pool_syn_rate": float(sub["pool_syn_rate"].mean()),
            "pool_strong_rate": float(sub["pool_strong_rate"].mean()),
            "exploit_minus_random_syn": cmp(sub, "exploit", "random", "hit_syn"),
            "exploit_minus_random_strong": cmp(sub, "exploit", "random", "hit_strong"),
            "mix_minus_exploit_syn": cmp(sub, "mix", "exploit", "hit_syn"),
            "explore_minus_exploit_syn": cmp(sub, "explore", "exploit", "hit_syn"),
        }

    ks_used = [k for k in KS if str(k) in res["by_k"]]
    h082 = all(
        (res["by_k"][str(k)]["exploit_minus_random_syn"] or {}).get("ci95", [0, 0])[0] > 0
        or (res["by_k"][str(k)]["exploit_minus_random_strong"] or {}).get("ci95", [0, 0])[0] > 0
        for k in ks_used) and bool(ks_used)
    h083 = all(
        ((res["by_k"][str(k)]["mix_minus_exploit_syn"] or {}).get("ci95", [0, 0])[0] > 0
         or (res["by_k"][str(k)]["explore_minus_exploit_syn"] or {}).get("ci95", [0, 0])[0] > 0)
        for k in ks_used) and bool(ks_used)
    res["decisions"] = {"H082_exploit_beats_random": h082, "H083_exploration_beats_exploit": h083,
                        "H084_stable_across_k": h082}
    res["decisions"]["verdict"] = ("decision_value_from_exploitation_only" if h082 and not h083 else
                                   "decision_value_from_exploration" if h082 and h083 else
                                   "no_decision_value_even_here")
    res["limits"] = [
        "One-shot budgeted selection, not sequential active learning, so the feedback-update step is untested.",
        "Retrospective: the candidate pool's ground truth is already measured, not newly measured.",
        "Features are annotation only; SYNERGY_DELTA_AUC is a model-fitted quantity; three tissues.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r33/PROTOCOL_E033.md",
                "research/2026-10-27-agent-cell-identifiability-r33/e033_decision.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E033_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E033_rows.csv", index=False)

    print("keys=%d cells=%d synergy rate=%.4f | strong thr=%.4f rate=%.3f" % (
        res["audit"]["keys"], res["audit"]["cells"], res["audit"]["synergy_rate"],
        thr, res["audit"]["strong_rate"]))
    for k, v in res["by_k"].items():
        print("  k=%-3s pool_syn=%.4f | " % (k, v["pool_syn_rate"])
              + " ".join("%s=%.4f" % (s, x) for s, x in v["precision_syn"].items()))
        c = v["exploit_minus_random_syn"]
        print("       exploit-random(syn): d=%+.4f CI=[%.4f,%.4f]" % (c["mean_diff"], c["ci95"][0], c["ci95"][1]) if c else "")
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
