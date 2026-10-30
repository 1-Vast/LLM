"""E059: in-place strategy selection from a small labelled probe, replacing a carried threshold.

For each pool size and split, draw a probe of q keys, decide mix vs exploit INSIDE the probe,
then apply that decision to the full pool. Pre-registered in PROTOCOL_E057.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r59"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (500, 1000, 2000, 4000, 8000, 16000)
PROBES = (200, 500, 1000)
K = 20
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def onehot(vals, levels):
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"))
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv), onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
    y = d.synergy.to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        perm = rng.permutation(len(y))
        ntr = int(0.8 * len(y))
        tr, full_pool = perm[:ntr], perm[ntr:]
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())
        for S in SIZES:
            if S > len(full_pool):
                continue
            pool = rng.choice(full_pool, size=S, replace=False)
            Xp = (X[pool] - mu) / sd
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            yp = y[pool]
            strong = yp >= np.quantile(yp, 0.90)
            e_hit = float(strong[np.argsort(-rp)[:K]].mean())
            m_hit = float(strong[np.argsort(-mix)[:K]].mean())
            row = {"rep": rep, "S": S, "exploit": e_hit, "mix": m_hit,
                   "best_fixed": max(e_hit, m_hit),
                   "best_is_mix": bool(m_hit > e_hit)}
            for q in PROBES:
                if q >= S // 2:
                    row[f"probe{q}"] = np.nan
                    row[f"agree{q}"] = np.nan
                    continue
                sub = rng.choice(S, size=q, replace=False)
                kq = max(5, int(round(K * q / S)))
                st = strong[sub]
                e_sub = float(st[np.argsort(-rp[sub])[:kq]].mean())
                m_sub = float(st[np.argsort(-mix[sub])[:kq]].mean())
                use_mix = m_sub > e_sub
                row[f"probe{q}"] = m_hit if use_mix else e_hit
                row[f"agree{q}"] = float(use_mix == row["best_is_mix"])
                row[f"decided_mix{q}"] = bool(use_mix)
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "in_place_strategy_selection_from_labelled_probe",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": list(SIZES), "probes": list(PROBES), "k": K,
                        "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(y)), "cells": int(len(r))}, "by_probe": {}, "files": {}}

    for q in PROBES:
        sub = r[r[f"probe{q}"].notna()]
        if not len(sub):
            continue
        ev = sub[sub.rep.isin(EVAL)]
        res["by_probe"][str(q)] = {
            "agreement_all": float(sub[f"agree{q}"].mean()),
            "agreement_eval": float(ev[f"agree{q}"].mean()) if len(ev) else None,
            "n": int(len(sub)),
            "probe_minus_exploit": paired(ev[f"probe{q}"], ev["exploit"], 2001 + q),
            "probe_minus_mix": paired(ev[f"probe{q}"], ev["mix"], 2101 + q),
            "probe_minus_best_fixed": paired(ev[f"probe{q}"], ev["best_fixed"], 2201 + q),
            "mean_probe_hit": float(ev[f"probe{q}"].mean()),
            "mean_exploit_hit": float(ev["exploit"].mean()),
            "mean_mix_hit": float(ev["mix"].mean()),
            "mean_best_fixed": float(ev["best_fixed"].mean())}

    a500 = res["by_probe"].get("500", {}).get("agreement_eval") or 0
    h149 = bool(a500 >= 0.75)
    c = res["by_probe"].get("500", {}).get("probe_minus_exploit")
    h150 = bool(c and c["ci95"][0] > 0)
    ags = [res["by_probe"][str(q)]["agreement_eval"] for q in PROBES if str(q) in res["by_probe"]]
    viol = sum(1 for i in range(len(ags) - 1) if ags[i] > ags[i + 1] + 1e-9)
    h151 = bool(len(ags) >= 2 and viol <= 1)
    res["decisions"] = {"H149_probe_identifies_strategy": h149, "H150_beats_always_exploit": h150,
                        "H151_bigger_probe_better": h151, "agreement_by_probe": ags}
    res["decisions"]["verdict"] = ("in_place_selection_works" if h149 and h150 else
                                   "in_place_selection_fails" if not h149 else
                                   "probe_identifies_but_does_not_pay")
    res["cost"] = "the probe consumes q labelled evaluations on top of the k picks; q is reported, not netted out"
    res["limits"] = [
        "The probe's k_q is scaled proportionally to the pool, an approximation of the full-pool budget.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r59/PROTOCOL_E057.md",
                "research/2026-10-27-agent-cell-identifiability-r59/e059_probe.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E059_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E059_rows.csv", index=False)

    print("keys=%d cells=%d" % (len(y), len(r)))
    for q in PROBES:
        b = res["by_probe"].get(str(q))
        if not b:
            continue
        print("  q=%-4d agree(eval)=%.3f n=%d | probe=%.4f exploit=%.4f mix=%.4f best=%.4f" % (
            q, b["agreement_eval"], b["n"], b["mean_probe_hit"], b["mean_exploit_hit"],
            b["mean_mix_hit"], b["mean_best_fixed"]))
        for cname in ("probe_minus_exploit", "probe_minus_mix", "probe_minus_best_fixed"):
            x = b[cname]
            print("      %-22s %+.4f [%+.4f,%+.4f]" % (cname, x["mean_diff"], x["ci95"][0], x["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
