"""E015: how much interaction should be transferred, and in which parameterisation?

Pre-registered in PROTOCOL_E015.md. Reads only PAIR_SCREEN.csv.

Interaction I = Y - bliss, where bliss uses the held-out cell's own single agents.
Other cells supply I_mean (full 7x9), and three low-dimensional projections
(row-only, column-only, diagonal j-i). Predictors are bliss + lambda * X with lambda
inner-tuned on a disjoint 25% of units over a fixed grid.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r14"
ANCHORS = {"high control", "low control"}
LAMBDAS = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25)
TUNE_FRAC = 0.25
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    if a.size < 3:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def build_units():
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
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]
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

    units = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        ref = cells[good[0]][0]
        rg = ok[ok["file"] == ref]
        if rg.empty:
            continue
        for (d1, d2) in sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])}):
            sub = rg[(rg["Drug 1"] == d1) & (rg["Drug 2"] == d2)]
            doses1 = sorted(sub["c1"].unique())
            doses2 = sorted(sub["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}

            def surface(files):
                arrs = []
                for f in files:
                    s = ok[(ok["file"] == f) & (ok["Drug 1"] == d1) & (ok["Drug 2"] == d2)]
                    if s.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in s.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                return np.nanmean(np.vstack(arrs), axis=0) if arrs else None

            def single(files, drug):
                vals = []
                for f in files:
                    s = ok[ok["file"] == f]
                    m = (s["Drug 1"].str.lower() == "dmso") & (s["Drug 2"] == drug)
                    if m.any():
                        vals.append(s[m].sort_values("c2")["y"].to_numpy(float))
                    m2 = (s["Drug 2"].str.lower() == "dmso") & (s["Drug 1"] == drug)
                    if m2.any():
                        vals.append(s[m2].sort_values("c1")["y"].to_numpy(float))
                if not vals:
                    return None
                L = min(len(v) for v in vals)
                return np.mean([v[:L] for v in vals], axis=0)

            Y, sa, sb = {}, {}, {}
            for c in good:
                fs = cells[c]
                Y[c] = surface(fs)
                a, b = single(fs, d1), single(fs, d2)
                if a is not None and len(a) >= len(doses1):
                    sa[c] = a[:len(doses1)]
                if b is not None and len(b) >= len(doses2):
                    sb[c] = b[:len(doses2)]
            cells_ok = [c for c in good if Y[c] is not None and np.isfinite(Y[c]).all() and c in sa and c in sb]
            if len(cells_ok) < 3:
                continue

            n1, n2 = len(doses1), len(doses2)
            diag = np.array([j - i for i, j in grid])

            def bliss(c):
                return np.array([sa[c][i] * sb[c][j] for i, j in grid])

            I = {c: Y[c] - bliss(c) for c in cells_ok}
            for ci, c in enumerate(cells_ok):
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                Imean = np.mean([I[x] for x in others], axis=0)
                Irow = np.array([np.mean(Imean[[k for k, (i, j) in enumerate(grid) if i == ii]]) for ii in range(n1)])
                Icol = np.array([np.mean(Imean[[k for k, (i, j) in enumerate(grid) if j == jj]]) for jj in range(n2)])
                Idiag = {d: np.mean(Imean[diag == d]) for d in np.unique(diag)}
                reps = {
                    "I_mean": Imean,
                    "I_row": np.array([Irow[i] for i, j in grid]),
                    "I_col": np.array([Icol[j] for i, j in grid]),
                    "I_diag": np.array([Idiag[d] for d in diag]),
                }
                mo = np.mean([Y[x] for x in others], axis=0)
                units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                              "truth": Y[c], "bliss": bliss(c), "reps": reps, "mean_other": mo})
    return units


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    units = build_units()
    rng = np.random.default_rng(SEED)
    idx_all = np.arange(len(units))
    tune = set(rng.choice(idx_all, max(20, int(TUNE_FRAC * len(units))), replace=False))

    reps = ("I_mean", "I_row", "I_col", "I_diag")
    # inner search for lambda per representation, on the tuning subset only
    lam_best, inner = {}, {}
    for rep in reps:
        scores = {}
        for lam in LAMBDAS:
            vals = []
            for i in sorted(tune):
                u = units[i]
                p = u["bliss"] + lam * u["reps"][rep]
                vals.append(float(np.sqrt(np.mean((p - u["truth"]) ** 2))))
            scores[lam] = float(np.mean(vals))
        lam_best[rep] = min(scores, key=scores.get)
        inner[rep] = scores

    rows = []
    for u in units:
        truth = u["truth"]
        best_true = float(truth.min())
        rank_true = np.argsort(np.argsort(truth))
        preds = {f"bliss_lam1.0": u["bliss"] + 1.0 * u["reps"]["I_mean"],
                 "mean_other": u["mean_other"]}
        for rep in reps:
            preds[f"{rep}_lam{lam_best[rep]}"] = u["bliss"] + lam_best[rep] * u["reps"][rep]
        for name, p in preds.items():
            ch = int(np.argmin(p))
            rows.append({"layout": u["layout"], "pair": u["pair"], "cell": u["cell"], "strategy": name,
                         "rmse": float(np.sqrt(np.mean((p - truth) ** 2))),
                         "rank_corr": spearman(p, truth),
                         "hit3": int(rank_true[ch] < 3),
                         "regret": float(truth[ch] - best_true)})
    r = pd.DataFrame(rows)

    res = {"kind": "interaction_transfer_amount_and_parameterisation",
           "input_sha256": sha256(CSV),
           "settings": {"lambdas": list(LAMBDAS), "tune_frac": TUNE_FRAC, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": len(units), "tuning_units": len(tune), "layouts": int(r["layout"].nunique())},
           "inner_search_rmse": inner, "lambda_selected": lam_best,
           "comparators": {s: {"n": int(len(d)), "rmse_mean": float(d["rmse"].mean()),
                               "rank_corr_mean": float(d["rank_corr"].mean()),
                               "hit3": float(d["hit3"].mean()), "regret_mean": float(d["regret"].mean())}
                           for s, d in r.groupby("strategy")},
           "paired": {}, "files": {}}

    def paired(a, b, metric):
        A = r[r.strategy == a][["layout", "pair", "cell", metric]]
        B = r[r.strategy == b][["layout", "pair", "cell", metric]]
        m = A.merge(B, on=["layout", "pair", "cell"], suffixes=("_a", "_b"))
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng2 = np.random.default_rng(SEED + 3)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"n": int(len(m)), "mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    best_rep = min(reps, key=lambda k: res["comparators"][f"{k}_lam{lam_best[k]}"]["rmse_mean"])
    res["paired"] = {
        "best_shrunk_minus_lam1_rmse": paired(f"{best_rep}_lam{lam_best[best_rep]}", "bliss_lam1.0", "rmse"),
        "mean_other_minus_best_shrunk_rmse": paired("mean_other", f"{best_rep}_lam{lam_best[best_rep]}", "rmse"),
        "mean_other_minus_best_shrunk_regret": paired("mean_other", f"{best_rep}_lam{lam_best[best_rep]}", "regret"),
    }
    for rep in reps:
        res["paired"][f"{rep}_minus_Imean_regret"] = paired(f"{rep}_lam{lam_best[rep]}", "bliss_lam1.0", "regret")
    res["best_rep"] = best_rep

    h029 = bool(lam_best["I_mean"] < 1.0
                and res["paired"]["best_shrunk_minus_lam1_rmse"]
                and res["paired"]["best_shrunk_minus_lam1_rmse"]["ci95_layout_clustered"]
                and res["paired"]["best_shrunk_minus_lam1_rmse"]["ci95_layout_clustered"][1] < 0)
    low_win = [k for k in ("I_row", "I_col", "I_diag")
               if res["paired"].get(f"{k}_minus_Imean_regret")
               and res["paired"][f"{k}_minus_Imean_regret"]["ci95_layout_clustered"]
               and res["paired"][f"{k}_minus_Imean_regret"]["ci95_layout_clustered"][1] < 0]
    h030 = bool(low_win)
    pm = res["paired"]["mean_other_minus_best_shrunk_regret"]
    h031 = bool(pm and pm["ci95_layout_clustered"] and pm["ci95_layout_clustered"][1] < 0)
    res["decisions"] = {"H029_shrinkage_helps": h029, "H030_lowdim_better_regret": h030,
                        "H030_lowdim_winners": low_win, "H031_pooling_still_best_for_ordering": h031}
    res["limits"] = [
        "Bliss is an arithmetic null on fractional survival; the interaction residual is not a target or pathway effect.",
        "lambda is tuned on 25% of units and evaluated on all; that subset is not independent of the evaluation set, so the shrinkage gain is optimistic by construction.",
        "Functional viability only; exploratory (plates were scoring endpoints earlier, cells cross days).",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r14/PROTOCOL_E015.md",
                "research/2026-10-27-agent-cell-identifiability-r14/e015_interaction_transfer.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E015_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E015_per_prediction.csv", index=False)

    print("units=%d layouts=%d" % (len(units), r["layout"].nunique()))
    print("lambda selected:", lam_best, "| best rep:", best_rep)
    for s, v in sorted(res["comparators"].items(), key=lambda kv: kv[1]["rmse_mean"]):
        print("  %-22s RMSE=%.4f rho=%.3f hit@3=%.3f regret=%.4f" % (s, v["rmse_mean"], v["rank_corr_mean"], v["hit3"], v["regret_mean"]))
    print("paired:", json.dumps({k: (None if v is None else {"d": round(v["mean_diff"], 4), "ci": [round(x, 4) for x in v["ci95_layout_clustered"]]}) for k, v in res["paired"].items() if v}, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
