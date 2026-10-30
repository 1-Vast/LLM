"""E017: can the boundary between two rules be revised from data?

Pre-registered in PROTOCOL_E017.md. Reads only PAIR_SCREEN.csv.

Rule A = cross-cell mean surface (pooling).
Rule B = the cell's own single-agent Bliss additivity + the mean interaction of the
         other cells (R13's bliss_other).
Boundary feature = mean pairwise rank correlation of the interaction surfaces among the
other cells (available without the held-out cell).
Boundary rule = use B iff inter_consistency >= t, with t chosen on OTHER layouts
(outer leave-one-layout-out), so selection and evaluation never share a layout.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r17"
ANCHORS = {"high control", "low control"}
THRESHOLDS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
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
            if len(cells_ok) < 4:
                continue

            def bliss(c):
                return np.array([sa[c][i] * sb[c][j] for i, j in grid])

            I = {c: Y[c] - bliss(c) for c in cells_ok}
            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 3:
                    continue
                # boundary feature: mean pairwise rank correlation of interaction among others
                rhos = []
                for x in range(len(others)):
                    for y in range(x + 1, len(others)):
                        rhos.append(spearman(I[others[x]], I[others[y]]))
                rhos = [r for r in rhos if np.isfinite(r)]
                inter_consistency = float(np.mean(rhos)) if rhos else float("nan")
                A_pred = np.mean([Y[x] for x in others], axis=0)
                B_pred = bliss(c) + np.mean([I[x] for x in others], axis=0)
                truth = Y[c]
                units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                              "inter_consistency": inter_consistency,
                              "regret_A": float(truth[np.argmin(A_pred)] - truth.min()),
                              "regret_B": float(truth[np.argmin(B_pred)] - truth.min()),
                              "hit_A": int(np.argsort(np.argsort(truth))[int(np.argmin(A_pred))] < 3),
                              "hit_B": int(np.argsort(np.argsort(truth))[int(np.argmin(B_pred))] < 3),
                              "rmse_A": float(np.sqrt(np.mean((A_pred - truth) ** 2))),
                              "rmse_B": float(np.sqrt(np.mean((B_pred - truth) ** 2)))})
    return pd.DataFrame(units)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    u = build_units()
    layouts = sorted(u["layout"].unique())
    res = {"kind": "rule_boundary_revision_between_pooling_and_additivity",
           "input_sha256": sha256(CSV),
           "settings": {"thresholds": list(THRESHOLDS), "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(u)), "layouts": len(layouts),
                     "mean_regret_A": float(u["regret_A"].mean()),
                     "mean_regret_B": float(u["regret_B"].mean()),
                     "mean_regret_oracle": float(np.minimum(u["regret_A"], u["regret_B"]).mean()),
                     "frac_B_better": float((u["regret_B"] < u["regret_A"]).mean()),
                     "mean_inter_consistency": float(u["inter_consistency"].mean())},
           "nested_threshold_selection": {}, "files": {}}

    # nested: choose t on the other layouts, apply to the held-out layout
    rows = []
    chosen = {}
    for lay in layouts:
        train = u[u["layout"] != lay]
        test = u[u["layout"] == lay]
        best_t, best_r = None, np.inf
        for t in THRESHOLDS:
            picks = np.where(train["inter_consistency"] >= t, train["regret_B"], train["regret_A"])
            r = float(np.mean(picks))
            if r < best_r:
                best_t, best_r = t, r
        chosen[lay] = {"t": best_t, "train_regret": best_r, "n_train": int(len(train))}
        mu = np.where(test["inter_consistency"] >= best_t, test["regret_B"], test["regret_A"])
        rows.append({"layout": lay, "n": int(len(test)), "t": best_t,
                     "rule": float(np.mean(mu)),
                     "A": float(test["regret_A"].mean()),
                     "B": float(test["regret_B"].mean()),
                     "oracle": float(np.minimum(test["regret_A"], test["regret_B"]).mean()),
                     "hit_rule": float(np.mean(np.where(test["inter_consistency"] >= best_t, test["hit_B"], test["hit_A"]))),
                     "hit_A": float(test["hit_A"].mean()), "hit_B": float(test["hit_B"].mean())})
    r = pd.DataFrame(rows)
    res["nested_threshold_selection"] = {"chosen_by_layout": chosen, "per_layout": rows}

    def boot_diff(col, base):
        rng = np.random.default_rng(SEED + 5)
        vals = []
        for _ in range(N_BOOT):
            pick = rng.choice(r["layout"].to_numpy(), size=len(r), replace=True)
            sel = pd.concat([r[r["layout"] == p] for p in pick])
            w = sel["n"]
            vals.append(float(np.average(sel[col] - sel[base], weights=w)))
        return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]

    best_fixed = "A" if r["A"].mean() <= r["B"].mean() else "B"
    rule_mean = float(np.average(r["rule"], weights=r["n"]))
    fixed_mean = float(np.average(r[best_fixed], weights=r["n"]))
    oracle_mean = float(np.average(r["oracle"], weights=r["n"]))
    res["comparison"] = {"rule_mean_regret": rule_mean, "best_fixed": best_fixed,
                         "best_fixed_mean_regret": fixed_mean, "oracle_mean_regret": oracle_mean,
                         "rule_minus_best_fixed": rule_mean - fixed_mean,
                         "rule_minus_best_fixed_ci": boot_diff("rule", best_fixed),
                         "oracle_minus_best_fixed": oracle_mean - fixed_mean,
                         "oracle_minus_best_fixed_ci": boot_diff("oracle", best_fixed),
                         "n_layouts_rule_wins": int((r["rule"] < r[best_fixed]).sum())}

    # H037: does the boundary feature orient the choice?
    better = (u["regret_B"] < u["regret_A"]).astype(float)
    rho = spearman(u["inter_consistency"].to_numpy(float), better.to_numpy(float))
    rng = np.random.default_rng(SEED + 7)
    boots = []
    for _ in range(N_BOOT):
        pick = rng.choice(layouts, size=len(layouts), replace=True)
        sel = pd.concat([u[u["layout"] == p] for p in pick])
        v = spearman(sel["inter_consistency"].to_numpy(float),
                     (sel["regret_B"] < sel["regret_A"]).astype(float).to_numpy())
        if np.isfinite(v):
            boots.append(v)
    res["boundary_feature"] = {"point_biserial_rank": rho,
                               "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    c = res["comparison"]
    h036 = bool(c["oracle_minus_best_fixed"] <= -0.010)
    h035 = bool(c["rule_minus_best_fixed"] <= -0.005 and c["rule_minus_best_fixed_ci"][1] < 0)
    h037 = bool(res["boundary_feature"]["ci95"] and res["boundary_feature"]["ci95"][0] > 0)
    res["decisions"] = {"H036_there_is_headroom": h036, "H035_boundary_rule_wins": h035,
                        "H037_feature_orients_choice": h037}
    res["decisions"]["verdict"] = ("boundary_revision_works" if h035 else
                                   "headroom_exists_but_boundary_not_learnable" if h036 else
                                   "no_headroom_rule_selection_line_stops")
    res["limits"] = [
        "Only nine layouts, so the outer loop has nine folds; per-layout threshold choices are noisy.",
        "Rule B uses the held-out cell's own single agents; that is legitimate (they are measured before the combination) but it is extra information relative to rule A.",
        "Functional viability only; exploratory (plates were scoring endpoints earlier, cells cross days).",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r17/PROTOCOL_E017.md",
                "research/2026-10-27-agent-cell-identifiability-r17/e017_boundary_revision.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E017_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    u.to_csv(OUT / "E017_units.csv", index=False)

    a = res["audit"]
    print("units=%d layouts=%d | regret A=%.4f B=%.4f oracle=%.4f | frac B better=%.2f | inter_consistency=%.3f" % (
        a["units"], a["layouts"], a["mean_regret_A"], a["mean_regret_B"], a["mean_regret_oracle"],
        a["frac_B_better"], a["mean_inter_consistency"]))
    for row in rows:
        print("  %-22s n=%-3d t=%.1f rule=%.4f A=%.4f B=%.4f oracle=%.4f" % (
            row["layout"], row["n"], row["t"], row["rule"], row["A"], row["B"], row["oracle"]))
    print("comparison:", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()
                                     if not isinstance(v, list)}, ensure_ascii=False))
    print("boundary feature:", json.dumps(res["boundary_feature"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
