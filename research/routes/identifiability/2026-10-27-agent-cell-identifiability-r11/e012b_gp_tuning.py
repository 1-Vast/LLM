"""E012b: fair GP comparison.

E012 ran the GP with fixed hyperparameters (length 0.5, noise 0.05) and it lost on the
decision metrics. That is not a fair test of the comparator. Here the kernel
hyperparameters are chosen by a reduced inner search on a subset of the held-out cells,
then the selected configuration is evaluated on all of them. Also tests an
empirical-Bayes shrunk surface, since the nominal 'hier' arm collapsed into the mean
surface (a held-out cell has no cell effect to estimate).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r11"
ANCHORS = {"high control", "low control"}
LENGTHS = (0.25, 0.5, 1.0)
NOISES = (0.02, 0.05, 0.1)
SHRINKS = (1.0, 0.9, 0.8)      # empirical-Bayes weight on the grid effect
GP_MAX_TRAIN = 300
TUNE_FRAC = 0.25
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def gp_predict(x_tr, y_tr, x_te, length, noise):
    d2 = ((x_tr[:, None, :] - x_tr[None, :, :]) ** 2).sum(-1)
    K = np.exp(-0.5 * d2 / length ** 2) + noise * np.eye(x_tr.shape[0])
    d2t = ((x_tr[:, None, :] - x_te[None, :, :]) ** 2).sum(-1)
    Ks = np.exp(-0.5 * d2t / length ** 2)
    try:
        alpha = np.linalg.solve(K, y_tr - y_tr.mean())
    except np.linalg.LinAlgError:
        return np.full(x_te.shape[0], float(np.mean(y_tr)))
    return y_tr.mean() + Ks.T @ alpha


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    keep = df[(~df["anchor"]) & (~df["dmso"]) & (~df["failed_qc"]) & df["y"].notna()]
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    units = []          # (layout, pair, cell, truth, others_matrix, xg)
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        ref = cells[good[0]][0]
        rg = keep[keep["file"] == ref]
        if rg.empty:
            continue
        for (d1, d2) in sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])}):
            sub_ref = rg[(rg["Drug 1"] == d1) & (rg["Drug 2"] == d2)]
            doses1 = sorted(sub_ref["c1"].unique())
            doses2 = sorted(sub_ref["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}
            surf = {}
            for c in good:
                arrs = []
                for f in cells[c]:
                    sub = keep[(keep["file"] == f) & (keep["Drug 1"] == d1) & (keep["Drug 2"] == d2)]
                    if sub.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in sub.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                if arrs:
                    surf[c] = np.nanmean(np.vstack(arrs), axis=0)
            cells_ok = [c for c in good if c in surf and np.isfinite(surf[c]).all()]
            if len(cells_ok) < 3:
                continue
            xg = np.array([[math.log10(doses1[i] + 1e-9), math.log10(doses2[j] + 1e-9)] for i, j in grid])
            xg = (xg - xg.mean(0)) / (xg.std(0) + 1e-9)
            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                              "truth": surf[c], "train": np.vstack([surf[x] for x in others]), "xg": xg})

    rng = np.random.default_rng(SEED)
    tune_idx = set(rng.choice(len(units), max(20, int(TUNE_FRAC * len(units))), replace=False))
    # inner search on the tuning subset
    scores = {}
    for L in LENGTHS:
        for nz in NOISES:
            vals = []
            for i in sorted(tune_idx):
                u = units[i]
                xi, yi = np.where(np.isfinite(u["train"]))
                if xi.size > GP_MAX_TRAIN:
                    sel = rng.choice(xi.size, GP_MAX_TRAIN, replace=False)
                    xi, yi = xi[sel], yi[sel]
                pred = gp_predict(u["xg"][yi], u["train"][xi, yi], u["xg"], L, nz)
                vals.append(spearman(pred, u["truth"]))
            scores["L%.2f_n%.2f" % (L, nz)] = float(np.nanmean(vals))
    best = max(scores, key=scores.get)
    bL = float(best.split("_")[0][1:])
    bn = float(best.split("_")[1][1:])

    rows = []
    for u in units:
        truth = u["truth"]
        best_true = float(np.min(truth))
        rank_true = np.argsort(np.argsort(truth))
        train = u["train"]
        xi, yi = np.where(np.isfinite(train))
        if xi.size > GP_MAX_TRAIN:
            sel = rng.choice(xi.size, GP_MAX_TRAIN, replace=False)
            xi, yi = xi[sel], yi[sel]
        gp = gp_predict(u["xg"][yi], train[xi, yi], u["xg"], bL, bn)
        mean_surface = np.nanmean(train, axis=0)
        grand = float(np.nanmean(train))
        g_eff = np.nanmean(train, axis=0) - grand
        for name, pred in (("mean_surface", mean_surface), ("gp_tuned", gp)):
            ch = int(np.argmin(pred))
            rows.append({"layout": u["layout"], "pair": u["pair"], "cell": u["cell"], "strategy": name,
                         "hit_at3": int(rank_true[ch] < 3), "regret": float(truth[ch] - best_true),
                         "rank_corr": spearman(pred, truth)})
        for w in SHRINKS:
            pred = grand + w * g_eff
            ch = int(np.argmin(pred))
            rows.append({"layout": u["layout"], "pair": u["pair"], "cell": u["cell"],
                         "strategy": "shrunk_%.1f" % w, "hit_at3": int(rank_true[ch] < 3),
                         "regret": float(truth[ch] - best_true), "rank_corr": spearman(pred, truth)})
    r = pd.DataFrame(rows)

    res = {"kind": "fair_gp_tuning_and_eb_shrinkage",
           "input_sha256": sha256(CSV),
           "inner_search_scores": scores, "selected": {"length": bL, "noise": bn},
           "n_units": len(units), "n_tuning": len(tune_idx),
           "comparators": {s: {"n": int(len(d)), "hit_at3": float(d["hit_at3"].mean()),
                               "regret_mean": float(d["regret"].mean()),
                               "rank_corr_mean": float(d["rank_corr"].mean())}
                           for s, d in r.groupby("strategy")},
           "files": {}}

    def paired(a, s, metric):
        A = r[r.strategy == a][["layout", "pair", "cell", metric]]
        B = r[r.strategy == s][["layout", "pair", "cell", metric]]
        m = A.merge(B, on=["layout", "pair", "cell"], suffixes=("_a", "_b"))
        m = m[np.isfinite(m[metric + "_a"]) & np.isfinite(m[metric + "_b"])]
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng2 = np.random.default_rng(SEED + 9)
        boots = []
        for _ in range(1000):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    res["paired"] = {
        "gp_tuned_minus_mean_rank_corr": paired("gp_tuned", "mean_surface", "rank_corr"),
        "gp_tuned_minus_mean_regret": paired("gp_tuned", "mean_surface", "regret"),
        "gp_tuned_minus_mean_hit": paired("gp_tuned", "mean_surface", "hit_at3"),
    }
    g = res["paired"]["gp_tuned_minus_mean_rank_corr"]
    res["decisions"] = {
        "H020_gp_tuned_adds_rank_corr": bool(g and g["mean_diff"] >= 0.02 and g["ci95_layout_clustered"] and g["ci95_layout_clustered"][0] > 0),
        "verdict": ("gp_adds_rank_corr" if (g and g["mean_diff"] >= 0.02 and g["ci95_layout_clustered"] and g["ci95_layout_clustered"][0] > 0)
                    else "static_surface_is_enough_even_with_tuned_gp"),
    }
    for rel in ("research/2026-10-27-agent-cell-identifiability-r11/e012b_gp_tuning.py",):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E012B_GP_TUNED.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E012B_per_prediction.csv", index=False)

    print("inner search best: %s (scores range %.3f..%.3f)" % (best, min(scores.values()), max(scores.values())))
    for s, v in sorted(res["comparators"].items(), key=lambda kv: kv[1]["regret_mean"]):
        print("  %-13s hit@3=%.3f regret=%.4f rankcorr=%.3f" % (s, v["hit_at3"], v["regret_mean"], v["rank_corr_mean"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
