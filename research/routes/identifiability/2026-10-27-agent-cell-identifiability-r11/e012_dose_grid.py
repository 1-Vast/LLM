"""E012: on the 7x9 dose grid of each compound pair — is the best dose combination
predictable from other cell lines, and does the dose-ratio boundary move?

Pre-registered in PROTOCOL_E012.md. Reads only PAIR_SCREEN.csv.

Boundary definition: for each partner-dose row i (7 values), j*(i) = argmin_j y(i,j)
is the most effective Cytarabine dose in that row; j*(.) is the boundary curve.

Comparators at equal information: random, corners (max dose), mean surface over other
cells, an additive empirical-Bayes model, and a 2-D Gaussian process on log-dose
coordinates (constructible here because the dose grid supplies a metric).
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
N_RANDOM = 20
N_BOOT = 1000
GP_MAX_TRAIN = 300
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def build():
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
    # layout signature over all non-anchor wells, so cells of one layout group together
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
    return keep, meta, groups


def gp_predict(x_tr, y_tr, x_te, length=0.5, noise=0.05):
    """Plain GP regression with an RBF kernel on normalised log-dose coordinates."""
    d2 = ((x_tr[:, None, :] - x_tr[None, :, :]) ** 2).sum(-1)
    K = np.exp(-0.5 * d2 / length ** 2) + noise * np.eye(x_tr.shape[0])
    d2t = ((x_tr[:, None, :] - x_te[None, :, :]) ** 2).sum(-1)
    Ks = np.exp(-0.5 * d2t / length ** 2)
    try:
        alpha = np.linalg.solve(K, y_tr - y_tr.mean())
    except np.linalg.LinAlgError:
        return np.full(x_te.shape[0], y_tr.mean())
    return y_tr.mean() + Ks.T @ alpha


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    keep, meta, groups = build()
    rng = np.random.default_rng(SEED)

    rows, boundary_rows = [], []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        # build per-cell, per-compound-pair surfaces on the common grid
        ref = cells[good[0]][0]
        rg = keep[keep["file"] == ref]
        if rg.empty:
            continue
        pairs = sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])})
        for (d1, d2) in pairs:
            sub_ref = rg[(rg["Drug 1"] == d1) & (rg["Drug 2"] == d2)]
            doses1 = sorted(sub_ref["c1"].unique())
            doses2 = sorted(sub_ref["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}
            files_surf = {}     # cell -> list of arrays over grid (one per file)
            for c in good:
                arrs = []
                for f in cells[c]:
                    sub = keep[(keep["file"] == f) & (keep["Drug 1"] == d1) & (keep["Drug 2"] == d2)]
                    if sub.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, r in sub.iterrows():
                        i = doses1.index(r["c1"])
                        j = doses2.index(r["c2"])
                        a[gidx[(i, j)]] = r["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                if arrs:
                    files_surf[c] = arrs
            cells_ok = [c for c in good if c in files_surf]
            if len(cells_ok) < 3:
                continue
            Y = {c: np.nanmean(np.vstack(files_surf[c]), axis=0) for c in cells_ok}
            # coordinates: normalised log doses
            xg = np.array([[math.log10(doses1[i] + 1e-9), math.log10(doses2[j] + 1e-9)]
                           for i, j in grid], dtype=float)
            xg = (xg - xg.mean(0)) / (xg.std(0) + 1e-9)

            # ---- boundary movement: j*(i) agreement ----
            def jstar(surf):
                S = surf.reshape(len(doses1), len(doses2))
                return np.nanargmin(S, axis=1)
            half_pairs = []
            for c in cells_ok:
                if len(files_surf[c]) >= 2:
                    a, b = files_surf[c][0], files_surf[c][1]
                    if np.isfinite(a).all() and np.isfinite(b).all():
                        half_pairs.append((c, float(np.mean(jstar(a) == jstar(b)))))
            cross = []
            for ii in range(len(cells_ok)):
                for jj in range(ii + 1, len(cells_ok)):
                    a, b = Y[cells_ok[ii]], Y[cells_ok[jj]]
                    if np.isfinite(a).all() and np.isfinite(b).all():
                        cross.append(float(np.mean(jstar(a) == jstar(b))))
            if half_pairs and cross:
                boundary_rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2),
                                      "n_cells": len(cells_ok), "n_halves": len(half_pairs),
                                      "within_cell_agreement": float(np.mean([x[1] for x in half_pairs])),
                                      "cross_cell_agreement": float(np.mean(cross)),
                                      "n_cross": len(cross)})

            # ---- prediction task ----
            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                truth = Y[c]
                if not np.isfinite(truth).all():
                    continue
                train = np.vstack([Y[x] for x in others])
                ok = np.isfinite(train)
                mean_surface = np.nanmean(train, axis=0)
                # additive empirical Bayes: grand + grid + cell effects
                grand = np.nanmean(train)
                g_eff = np.nanmean(train, axis=0) - grand
                c_eff = np.nanmean(train, axis=1) - grand
                hier = grand + g_eff
                # GP on all observed other-cell points
                xi, yi = np.where(ok)
                if xi.size > GP_MAX_TRAIN:
                    sel = rng.choice(xi.size, GP_MAX_TRAIN, replace=False)
                    xi, yi = xi[sel], yi[sel]
                gp = gp_predict(xg[yi], train[xi, yi], xg)
                best_true = float(np.nanmin(truth))
                order_true = np.argsort(np.argsort(truth))
                for name, pred in (("mean_surface", mean_surface), ("hier", hier), ("gp", gp),
                                   ("corners", np.full(truth.size, np.nan))):
                    if name == "corners":
                        k_best = int(np.argmin([(math.log10(doses1[i]) + math.log10(doses2[j]))
                                                for i, j in grid]))
                        ch = k_best
                    else:
                        ch = int(np.argmin(pred))
                    top3 = list(np.argsort(pred)[:3]) if name != "corners" else [ch]
                    rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                                 "strategy": name,
                                 "hit_at3": int(order_true[ch] < 3),
                                 "regret": float(truth[ch] - best_true),
                                 "rank_corr": spearman(pred, truth) if name != "corners" else float("nan")})
                hits, regs, rcs = [], [], []
                for _ in range(N_RANDOM):
                    ch = int(rng.integers(0, truth.size))
                    hits.append(int(order_true[ch] < 3))
                    regs.append(float(truth[ch] - best_true))
                rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                             "strategy": "random", "hit_at3": float(np.mean(hits)),
                             "regret": float(np.mean(regs)), "rank_corr": float("nan")})

    r = pd.DataFrame(rows)
    b = pd.DataFrame(boundary_rows)
    res = {"kind": "dose_grid_optimum_predictability_and_boundary_movement",
           "input_sha256": sha256(CSV),
           "settings": {"n_random": N_RANDOM, "n_boot": N_BOOT, "gp_max_train": GP_MAX_TRAIN, "seed": SEED},
           "audit": {"layouts": int(r["layout"].nunique()), "compound_pairs": int(r.groupby(["layout", "pair"]).ngroups),
                     "heldout_cells": int(r.groupby(["layout", "pair", "cell"]).ngroups), "rows": int(len(r)),
                     "boundary_units": int(len(b))},
           "comparators": {}, "boundary": {}, "files": {}}

    agg = {}
    for s, d in r.groupby("strategy"):
        agg[s] = {"n": int(len(d)), "hit_at3": float(d["hit_at3"].mean()),
                  "regret_mean": float(d["regret"].mean()),
                  "rank_corr_mean": float(d["rank_corr"].mean()) if d["rank_corr"].notna().any() else None}
    res["comparators"] = agg

    def paired(a, s, metric="regret"):
        A = r[r.strategy == a][["layout", "pair", "cell", metric]]
        B = r[r.strategy == s][["layout", "pair", "cell", metric]]
        m = A.merge(B, on=["layout", "pair", "cell"], suffixes=("_a", "_b"))
        m = m[np.isfinite(m[metric + "_a"]) & np.isfinite(m[metric + "_b"])]
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng2 = np.random.default_rng(SEED + 2)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"n": int(len(m)), "mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    res["paired"] = {
        "gp_minus_mean_rank_corr": paired("gp", "mean_surface", "rank_corr"),
        "gp_minus_mean_regret": paired("gp", "mean_surface", "regret"),
        "gp_minus_mean_hit": paired("gp", "mean_surface", "hit_at3"),
        "mean_minus_random_regret": paired("mean_surface", "random", "regret"),
        "mean_minus_corners_regret": paired("mean_surface", "corners", "regret"),
    }
    if len(b):
        d = b["within_cell_agreement"] - b["cross_cell_agreement"]
        lays = sorted(b["layout"].unique())
        rng3 = np.random.default_rng(SEED + 4)
        boots = []
        for _ in range(N_BOOT):
            pick = rng3.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([b[b["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float((sel["within_cell_agreement"] - sel["cross_cell_agreement"]).mean()))
        res["boundary"] = {"n_units": int(len(b)),
                           "mean_within_cell_agreement": float(b["within_cell_agreement"].mean()),
                           "mean_cross_cell_agreement": float(b["cross_cell_agreement"].mean()),
                           "mean_drop": float(d.mean()),
                           "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
                           "frac_units_with_drop": float((d > 0).mean())}

    g = res["paired"]["gp_minus_mean_rank_corr"]
    h020 = bool(g and g["mean_diff"] >= 0.02 and g["ci95_layout_clustered"] and g["ci95_layout_clustered"][0] > 0)
    m = res["comparators"].get("mean_surface", {})
    gp = res["comparators"].get("gp", {})
    h020b = bool(m and gp and m["regret_mean"] <= gp["regret_mean"] and m["hit_at3"] >= gp["hit_at3"])
    rd = res["paired"]["mean_minus_random_regret"]
    cd = res["paired"]["mean_minus_corners_regret"]
    h022 = bool(rd and rd["mean_diff"] < 0 and rd["ci95_layout_clustered"] and rd["ci95_layout_clustered"][1] < 0
                and cd and cd["mean_diff"] < 0 and cd["ci95_layout_clustered"] and cd["ci95_layout_clustered"][1] < 0)
    bnd = res["boundary"]
    h021 = bool(bnd and bnd.get("ci95_layout_clustered") and bnd["ci95_layout_clustered"][0] > 0)
    res["decisions"] = {"H020_gp_adds_rank_corr": h020, "H020b_static_is_enough": h020b,
                        "H021_boundary_moves": h021, "H022_predictability_exists": h022}
    res["limits"] = [
        "Functional viability only; no mechanism, target engagement, selectivity or clinical claim.",
        "Validation plates were used as scoring endpoints in an earlier round and cross-cell comparisons cross days: exploratory.",
        "GP hyperparameters are fixed, not tuned per pair; that under-serves the GP and must be stated when it 'loses'.",
        "Compound pairs are few (29 across layouts), so no compound-level generalisation is claimed.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r11/PROTOCOL_E012.md",
                "research/2026-10-27-agent-cell-identifiability-r11/e012_dose_grid.py",
                str(CSV.relative_to(ROOT))):
        p_ = ROOT / rel
        if p_.exists():
            res["files"][rel] = sha256(p_)
    (OUT / "E012_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E012_per_prediction.csv", index=False)
    if len(b):
        b.to_csv(OUT / "E012_boundary.csv", index=False)

    print("layouts=%d pairs=%d heldout=%d" % (res["audit"]["layouts"], res["audit"]["compound_pairs"], res["audit"]["heldout_cells"]))
    for s, v in sorted(res["comparators"].items(), key=lambda kv: kv[1]["regret_mean"]):
        print("  %-13s hit@3=%.3f regret=%.4f rankcorr=%s" % (
            s, v["hit_at3"], v["regret_mean"], ("%.3f" % v["rank_corr_mean"]) if v["rank_corr_mean"] is not None else "-"))
    print("boundary:", json.dumps(res["boundary"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
