"""E044: a proper hierarchical / partial-pooling comparator against the flat ridge.

Pre-registered in PROTOCOL_E044.md. The hierarchy allows pathway effects to vary by tissue but
shrinks that interaction block harder (lambda_inter >> lambda_base). Splits are grouped by
combination, the setting R43 showed is closer to real deployment.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r44"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA_BASE = 1.0
LAMBDA_INTER = 20.0
LAMBDA_SENS = (5.0, 50.0)
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


def rank_corr(a, b):
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


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


def fit_weighted(Xb, Xi, y, lam_b, lam_i, Xtb, Xti):
    """Ridge with a different penalty per block, plus an intercept."""
    n = len(y)
    ym = float(y.mean())
    B = Xb - Xb.mean(axis=0)
    I = Xi - Xi.mean(axis=0)
    X = np.hstack([B, I])
    p_b, p_i = B.shape[1], I.shape[1]
    pen = np.concatenate([np.full(p_b, lam_b), np.full(p_i, lam_i)])
    A = X.T @ X + np.diag(pen)
    w = np.linalg.solve(A, X.T @ (y - ym))
    Xte = np.hstack([Xtb - Xb.mean(axis=0), Xti - Xi.mean(axis=0)])
    return ym + Xte @ w


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        combo=("combo", "first"), tissue=("Tissue", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ti = sorted(d["tissue"].unique())
    ap = sorted(d["ap"].unique())
    lp = sorted(d["lp"].unique())
    T = onehot(d["tissue"].to_numpy(), ti)
    A = onehot(d["ap"].to_numpy(), ap)
    L = onehot(d["lp"].to_numpy(), lp)
    base = np.hstack([T, A, L])
    inter_blocks = [T[:, [j]] * np.hstack([A, L]) for j in range(len(ti))]
    inter = np.hstack(inter_blocks)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)
    combo = d["combo"].to_numpy()
    tissue = d["tissue"].to_numpy()

    combos = pd.unique(combo)
    rng = np.random.default_rng(SEED)
    rows = []
    for rep, (tissue_name, _) in enumerate([(None, None)] * 0):
        pass
    for rep in range(REPEATS):
        order = rng.permutation(len(combos))
        n_tr = int(0.8 * len(combos))
        tr_combos = set(combos[order[:n_tr]])
        tr = np.array([i for i, c in enumerate(combo) if c in tr_combos])
        pool = np.array([i for i, c in enumerate(combo) if c not in tr_combos])
        if len(tr) < 5000 or len(pool) < 2000:
            continue
        ytr = y[tr]
        # flat
        pf = fit_weighted(base[tr], np.zeros((len(tr), 0)), ytr, LAMBDA_BASE, 1.0,
                          base[pool], np.zeros((len(pool), 0)))
        # hierarchical (partial pooling on the tissue x pathway block)
        ph = fit_weighted(base[tr], inter[tr], ytr, LAMBDA_BASE, LAMBDA_INTER,
                          base[pool], inter[pool])
        sens = {}
        for lam in LAMBDA_SENS:
            sens[lam] = fit_weighted(base[tr], inter[tr], ytr, LAMBDA_BASE, lam,
                                     base[pool], inter[pool])
        yp = y[pool]
        sp = syn[pool]
        k10 = max(1, int(0.10 * len(yp)))
        thr = np.quantile(yp, 0.90)
        strong = yp >= thr
        row = {"rep": rep, "n_tr": int(len(tr)), "n_pool": int(len(pool)),
               "rho_flat": rank_corr(pf, yp), "rho_hier": rank_corr(ph, yp),
               "p10_flat": float(np.mean(strong[np.argsort(-pf)[:k10]])),
               "p10_hier": float(np.mean(strong[np.argsort(-ph)[:k10]]))}
        for lam, p in sens.items():
            row[f"rho_hier_lam{lam:g}"] = rank_corr(p, yp)
        # per-tissue rho for H116
        for t in ti:
            m = tissue[pool] == t
            if m.sum() >= 200:
                row[f"rho_flat_{t}"] = rank_corr(pf[m], yp[m])
                row[f"rho_hier_{t}"] = rank_corr(ph[m], yp[m])
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "hierarchical_partial_pooling_vs_flat_ridge",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda_base": LAMBDA_BASE, "lambda_inter": LAMBDA_INTER,
                        "lambda_sensitivity": list(LAMBDA_SENS), "repeats": REPEATS,
                        "split": "grouped by combination", "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "combos": int(len(combos)),
                     "base_dims": int(base.shape[1]), "inter_dims": int(inter.shape[1]),
                     "reps_used": int(len(r))},
           "summary": {}, "files": {}}

    if len(r) >= 10:
        res["summary"] = {
            "rho_flat": {"mean": float(r["rho_flat"].mean()), "median": float(r["rho_flat"].median())},
            "rho_hier": {"mean": float(r["rho_hier"].mean()), "median": float(r["rho_hier"].median())},
            "paired_rho": paired(r["rho_hier"], r["rho_flat"], 91),
            "paired_p10": paired(r["p10_hier"], r["p10_flat"], 92),
            "frac_reps_hier_better": float((r["rho_hier"] > r["rho_flat"]).mean()),
            "sensitivity_rho_hier": {f"lam{lam:g}": float(r[f"rho_hier_lam{lam:g}"].mean()) for lam in LAMBDA_SENS},
        }
        per_tissue = {}
        for t in ti:
            a, b = f"rho_hier_{t}", f"rho_flat_{t}"
            if a in r.columns and b in r.columns:
                d_ = (r[a] - r[b]).dropna()
                if len(d_) >= 5:
                    per_tissue[t] = {"n": int(len(d_)), "mean_diff": float(d_.mean())}
        res["per_tissue"] = per_tissue
        pr = res["summary"]["paired_rho"]
        pp = res["summary"]["paired_p10"]
        h115 = bool(pr and pr["ci95"][0] > 0)
        h116 = bool(per_tissue and sum(1 for v in per_tissue.values() if v["mean_diff"] > 0) >= max(2, int(np.ceil(2 / 3 * len(per_tissue)))))
        h117 = bool(pp and pp["ci95"][0] > 0)
    else:
        h115 = h116 = h117 = False
    res["decisions"] = {"H115_hierarchical_beats_flat_rho": h115, "H116_gain_in_most_tissues": h116,
                        "H117_hierarchical_beats_flat_p10": h117}
    res["decisions"]["verdict"] = ("hierarchical_adds_value" if h115 else
                                   "flat_is_enough_no_hierarchical_gain")
    res["limits"] = [
        "The hierarchy is tissue-level only; cell-level random effects are unavailable for a held-out cell, which is exactly where R11's hierarchical arm degenerated.",
        "lambda_inter is a fixed prior value; the two sensitivity values are reported but not used for selection.",
        "Retrospective candidate pool; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r44/PROTOCOL_E044.md",
                "research/2026-10-27-agent-cell-identifiability-r44/e044_hierarchical.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E044_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E044_rows.csv", index=False)

    print("keys=%d combos=%d base=%d inter=%d reps=%d" % (
        res["audit"]["keys"], res["audit"]["combos"], res["audit"]["base_dims"],
        res["audit"]["inter_dims"], res["audit"]["reps_used"]))
    if "summary" in res and res["summary"]:
        s = res["summary"]
        print("  rho flat=%.4f hier=%.4f | paired %+.4f [%+.4f,%+.4f] | frac hier better=%.2f" % (
            s["rho_flat"]["mean"], s["rho_hier"]["mean"], s["paired_rho"]["mean_diff"],
            s["paired_rho"]["ci95"][0], s["paired_rho"]["ci95"][1], s["frac_reps_hier_better"]))
        print("  p10  flat=%.4f hier=%.4f | paired %+.4f [%+.4f,%+.4f]" % (
            r["p10_flat"].mean(), r["p10_hier"].mean(), s["paired_p10"]["mean_diff"],
            s["paired_p10"]["ci95"][0], s["paired_p10"]["ci95"][1]))
        print("  sensitivity:", s["sensitivity_rho_hier"])
        print("  per tissue:", json.dumps(res.get("per_tissue"), ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
