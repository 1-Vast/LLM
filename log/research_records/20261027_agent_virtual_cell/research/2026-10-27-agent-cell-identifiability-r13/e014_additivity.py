"""E014: the standard pharmacology null (additivity from the cell's own single agents)
against the cross-cell mean, and whether the interaction surface is conserved.

Pre-registered in PROTOCOL_E014.md. Reads only PAIR_SCREEN.csv.

Per held-out cell c and compound pair:
  y_A(i)  partner single agent at dose i (c's own wells)
  y_B(j)  Cytarabine single agent at dose j (c's own wells)
  bliss(i,j) = y_A(i) * y_B(j)          hsa(i,j) = min(y_A(i), y_B(j))
  mean_other  = mean of other cells' combination surfaces
  bliss_other = bliss + mean over other cells of (Y_c' - bliss_c')
Then RMSE / Spearman / hit@3 / regret against c's observed surface.
Interaction conservation: rank correlation of (Y - bliss) between cells, with the
same-cell split-half value as the noise ceiling.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r13"
ANCHORS = {"high control", "low control"}
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
    return ok, meta, groups


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    ok, meta, groups = build()

    units, inter_rows = [], []
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
            if sub.empty:
                continue
            doses1 = sorted(sub["c1"].unique())
            doses2 = sorted(sub["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}

            def surface(files, partner, cyto):
                arrs = []
                for f in files:
                    sub = ok[(ok["file"] == f) & (ok["Drug 1"] == partner) & (ok["Drug 2"] == cyto)]
                    if sub.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in sub.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                return np.nanmean(np.vstack(arrs), axis=0) if arrs else None

            def single(files, drug):
                vals = []
                for f in files:
                    s = ok[(ok["file"] == f)]
                    m = ((s["Drug 1"].str.lower() == "dmso") & (s["Drug 2"] == drug))
                    v = s[m]
                    if len(v):
                        vals.append(v.sort_values("c2")["y"].to_numpy(float))
                    m2 = ((s["Drug 2"].str.lower() == "dmso") & (s["Drug 1"] == drug))
                    v2 = s[m2]
                    if len(v2):
                        vals.append(v2.sort_values("c1")["y"].to_numpy(float))
                if not vals:
                    return None
                L = min(len(v) for v in vals)
                return np.mean([v[:L] for v in vals], axis=0)

            Y, sa, sb, files_of = {}, {}, {}, {}
            for c in good:
                fs = cells[c]
                Y[c] = surface(fs, d1, d2)
                files_of[c] = fs
                a = single(fs, d1)
                b = single(fs, d2)
                if a is not None and len(a) >= len(doses1):
                    sa[c] = a[:len(doses1)]
                if b is not None and len(b) >= len(doses2):
                    sb[c] = b[:len(doses2)]
            cells_ok = [c for c in good if Y[c] is not None and np.isfinite(Y[c]).all()
                        and c in sa and c in sb]
            if len(cells_ok) < 3:
                continue

            def bliss(c):
                return np.array([sa[c][i] * sb[c][j] for i, j in grid])
            def hsa(c):
                return np.array([min(sa[c][i], sb[c][j]) for i, j in grid])

            # interaction surfaces
            I = {c: Y[c] - bliss(c) for c in cells_ok}
            for ii in range(len(cells_ok)):
                for jj in range(ii + 1, len(cells_ok)):
                    inter_rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2),
                                       "cell_a": cells_ok[ii], "cell_b": cells_ok[jj],
                                       "interaction_rho": spearman(I[cells_ok[ii]], I[cells_ok[jj]]),
                                       "raw_rho": spearman(Y[cells_ok[ii]], Y[cells_ok[jj]])})
            # same-cell split-half ceiling for the interaction
            for c in cells_ok:
                if len(files_of[c]) >= 2:
                    a1 = surface([files_of[c][0]], d1, d2)
                    a2 = surface([files_of[c][1]], d1, d2)
                    if a1 is not None and a2 is not None and np.isfinite(a1).all() and np.isfinite(a2).all():
                        ia = a1 - bliss(c)
                        ib = a2 - bliss(c)
                        inter_rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2),
                                           "cell_a": c, "cell_b": c, "interaction_rho": spearman(ia, ib),
                                           "raw_rho": spearman(a1, a2), "split_half": 1})

            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                truth = Y[c]
                rank_true = np.argsort(np.argsort(truth))
                best_true = float(truth.min())
                mo = np.mean([Y[x] for x in others], axis=0)
                inter_other = np.mean([I[x] for x in others], axis=0)
                preds = {"mean_other": mo, "const_other": np.full(truth.size, float(np.mean(mo))),
                         "bliss": bliss(c), "hsa": hsa(c), "bliss_other": bliss(c) + inter_other}
                for name, p in preds.items():
                    ch = int(np.argmin(p))
                    units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                                  "strategy": name,
                                  "rmse": float(np.sqrt(np.mean((p - truth) ** 2))),
                                  "rank_corr": spearman(p, truth),
                                  "hit3": int(rank_true[ch] < 3),
                                  "regret": float(truth[ch] - best_true)})

    u = pd.DataFrame(units)
    ir = pd.DataFrame(inter_rows)
    res = {"kind": "additivity_null_vs_cross_cell_mean_and_interaction_conservation",
           "input_sha256": sha256(CSV), "settings": {"n_boot": N_BOOT, "seed": SEED},
           "audit": {"heldout_units": int(u.groupby(["layout", "pair", "cell"]).ngroups),
                     "comparisons": int(len(u)), "layouts": int(u["layout"].nunique()),
                     "interaction_pairs": int(len(ir))},
           "comparators": {s: {"n": int(len(d)), "rmse_mean": float(d["rmse"].mean()),
                               "rank_corr_mean": float(d["rank_corr"].mean()),
                               "hit3": float(d["hit3"].mean()), "regret_mean": float(d["regret"].mean())}
                           for s, d in u.groupby("strategy")},
           "interaction_conservation": {}, "paired": {}, "files": {}}

    def paired(a, b, metric):
        A = u[u.strategy == a][["layout", "pair", "cell", metric]]
        B = u[u.strategy == b][["layout", "pair", "cell", metric]]
        m = A.merge(B, on=["layout", "pair", "cell"], suffixes=("_a", "_b"))
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng = np.random.default_rng(SEED + 1)
        boots = []
        for _ in range(N_BOOT):
            pick = rng.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"n": int(len(m)), "mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    res["paired"] = {
        "mean_other_minus_bliss_rmse": paired("mean_other", "bliss", "rmse"),
        "bliss_other_minus_bliss_rmse": paired("bliss_other", "bliss", "rmse"),
        "bliss_other_minus_mean_other_rmse": paired("bliss_other", "mean_other", "rmse"),
        "bliss_minus_const_rmse": paired("bliss", "const_other", "rmse"),
    }
    if len(ir):
        cross = ir[ir.get("split_half").isna()] if "split_half" in ir else ir
        split = ir[ir["split_half"].notna()] if "split_half" in ir else ir.iloc[0:0]
        lays = sorted(cross["layout"].unique())
        rng = np.random.default_rng(SEED + 2)
        boots = []
        for _ in range(N_BOOT):
            pick = rng.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([cross[cross["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["interaction_rho"].mean()))
        res["interaction_conservation"] = {
            "n_cross_pairs": int(len(cross)),
            "mean_interaction_rho_cross_cell": float(cross["interaction_rho"].mean()),
            "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
            "mean_raw_rho_cross_cell": float(cross["raw_rho"].mean()),
            "n_split_half": int(len(split)),
            "mean_interaction_rho_split_half": float(split["interaction_rho"].mean()) if len(split) else None,
            "frac_cross_pairs_positive": float((cross["interaction_rho"] > 0).mean()),
        }

    mb = res["paired"]["mean_other_minus_bliss_rmse"]
    h026 = bool(mb and mb["mean_diff"] <= -0.02 and mb["ci95_layout_clustered"] and mb["ci95_layout_clustered"][1] < 0)
    ic = res["interaction_conservation"]
    h027 = bool(ic.get("ci95_layout_clustered") and ic["ci95_layout_clustered"][0] > 0)
    b1 = res["paired"]["bliss_other_minus_bliss_rmse"]
    b2 = res["paired"]["bliss_other_minus_mean_other_rmse"]
    h028 = bool(b1 and b1["ci95_layout_clustered"] and b1["ci95_layout_clustered"][1] < 0
                and b2 and b2["ci95_layout_clustered"] and b2["ci95_layout_clustered"][1] < 0)
    res["decisions"] = {"H026_mean_other_beats_bliss": h026, "H027_interaction_conserved": h027,
                        "H028_bliss_plus_transferable_interaction_best": h028}
    res["decisions"]["verdict"] = ("transfer_is_interaction" if h026 and h027 and h028 else
                                   "transfer_is_additive_baseline" if not h026 else
                                   "mixed")
    res["limits"] = [
        "Bliss and HSA are arithmetic null models on fractional survival, not mechanism claims.",
        "Single-agent wells are the cell's own; their doses match the grid by construction but the pairing of doses is positional.",
        "Functional viability only; no target engagement, selectivity or clinical claim.",
        "Exploratory: plates were used as scoring endpoints earlier and cross-cell comparisons cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r13/PROTOCOL_E014.md",
                "research/2026-10-27-agent-cell-identifiability-r13/e014_additivity.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E014_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    u.to_csv(OUT / "E014_per_prediction.csv", index=False)
    if len(ir):
        ir.to_csv(OUT / "E014_interactions.csv", index=False)

    print("heldout units=%d layouts=%d" % (res["audit"]["heldout_units"], res["audit"]["layouts"]))
    for s, v in sorted(res["comparators"].items(), key=lambda kv: kv[1]["rmse_mean"]):
        print("  %-12s RMSE=%.4f rho=%.3f hit@3=%.3f regret=%.4f" % (s, v["rmse_mean"], v["rank_corr_mean"], v["hit3"], v["regret_mean"]))
    print("paired:", json.dumps({k: (None if v is None else {"d": round(v["mean_diff"], 4), "ci": [round(x, 4) for x in v["ci95_layout_clustered"]]}) for k, v in res["paired"].items()}, ensure_ascii=False))
    print("interaction:", json.dumps(ic, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
