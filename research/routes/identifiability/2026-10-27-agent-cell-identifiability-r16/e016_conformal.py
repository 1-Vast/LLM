"""E016: conformal coverage-risk on the leave-one-layout dose-grid task.

Pre-registered in PROTOCOL_E016.md. Reads only PAIR_SCREEN.csv.

Unit = (layout, compound pair, held-out cell). Prediction = cross-cell mean surface,
nonconformity = regret of the predicted best dose combination. Two schemes:
  (1) plain split conformal, calibration = all units outside the test layout;
  (2) normalised conformal s = regret / spread, spread = mean across grid points of the
      sd across other cells' surfaces (other cells only), so widths vary per unit and
      selective prediction becomes possible.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r16"
ANCHORS = {"high control", "low control"}
ALPHAS = (0.05, 0.1, 0.2, 0.3, 0.5)
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
            surf = {}
            for c in good:
                arrs = []
                for f in cells[c]:
                    s = ok[(ok["file"] == f) & (ok["Drug 1"] == d1) & (ok["Drug 2"] == d2)]
                    if s.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in s.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                if arrs:
                    surf[c] = np.nanmean(np.vstack(arrs), axis=0)
            cells_ok = [c for c in good if c in surf and np.isfinite(surf[c]).all()]
            if len(cells_ok) < 3:
                continue
            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                M = np.vstack([surf[x] for x in others])
                mu = M.mean(axis=0)
                spread = float(np.mean(M.std(axis=0, ddof=1)))
                truth = surf[c]
                ch = int(np.argmin(mu))
                units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                              "regret": float(truth[ch] - truth.min()), "spread": spread})
    return pd.DataFrame(units)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    u = build_units()
    res = {"kind": "conformal_coverage_risk_on_dose_grid_transfer",
           "input_sha256": sha256(CSV), "settings": {"alphas": list(ALPHAS), "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(u)), "layouts": int(u["layout"].nunique()),
                     "pairs": int(u.groupby("pair").ngroups),
                     "regret_mean": float(u["regret"].mean()),
                     "spread_mean": float(u["spread"].mean())},
           "coverage": {}, "adaptive": {}, "files": {}}

    layouts = sorted(u["layout"].unique())
    # ---- plain split conformal, leave-one-layout-out ----
    plain = {}
    for a in ALPHAS:
        cover = {}
        for lay in layouts:
            cal = u[u["layout"] != lay]["regret"].to_numpy(float)
            test = u[u["layout"] == lay]["regret"].to_numpy(float)
            if len(cal) < 10 or len(test) == 0:
                continue
            k = int(math.ceil((len(cal) + 1) * (1 - a)))
            q = float(np.sort(cal)[min(k, len(cal)) - 1])
            cover[lay] = {"q": q, "coverage": float(np.mean(test <= q)), "n_test": int(len(test))}
        if cover:
            emp = float(np.average([v["coverage"] for v in cover.values()],
                                   weights=[v["n_test"] for v in cover.values()]))
            rng = np.random.default_rng(SEED)
            lays = sorted(cover)
            boots = []
            for _ in range(N_BOOT):
                pick = rng.choice(lays, size=len(lays), replace=True)
                w = sum(cover[p]["n_test"] for p in pick)
                boots.append(sum(cover[p]["coverage"] * cover[p]["n_test"] for p in pick) / w)
            plain[a] = {"nominal": 1 - a, "empirical": emp,
                        "ci95_layout_bootstrap": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                        "per_layout": cover}
    res["coverage"] = {str(a): v for a, v in plain.items()}

    # ---- normalised (locally adaptive) conformal ----
    u = u.copy()
    u["s"] = u["regret"] / np.maximum(u["spread"], 1e-6)
    adapt = {}
    for a in ALPHAS:
        rows = []
        for lay in layouts:
            cal = u[u["layout"] != lay]
            test = u[u["layout"] == lay]
            if len(cal) < 10 or len(test) == 0:
                continue
            k = int(math.ceil((len(cal) + 1) * (1 - a)))
            q = float(np.sort(cal["s"].to_numpy(float))[min(k, len(cal)) - 1])
            width = q * test["spread"].to_numpy(float)
            rows.append({"layout": lay, "coverage": float(np.mean(test["regret"].to_numpy(float) <= width)),
                         "mean_width": float(np.mean(width)), "n": int(len(test))})
        if rows:
            adapt[a] = {"nominal": 1 - a,
                        "empirical": float(np.average([r["coverage"] for r in rows], weights=[r["n"] for r in rows])),
                        "mean_width": float(np.average([r["mean_width"] for r in rows], weights=[r["n"] for r in rows])),
                        "per_layout": rows}
    res["adaptive"] = {str(a): v for a, v in adapt.items()}

    # ---- H034: does the uncertainty proxy order realised error? ----
    rho = spearman(u["spread"].to_numpy(float), u["regret"].to_numpy(float))
    rng = np.random.default_rng(SEED + 1)
    boots = []
    for _ in range(N_BOOT):
        pick = rng.choice(layouts, size=len(layouts), replace=True)
        sel = pd.concat([u[u["layout"] == p] for p in pick])
        v = spearman(sel["spread"].to_numpy(float), sel["regret"].to_numpy(float))
        if np.isfinite(v):
            boots.append(v)
    res["spread_vs_regret"] = {"spearman": rho,
                               "ci95_layout_bootstrap": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None}

    # ---- H033: selective prediction with the conformal width ----
    a0 = 0.2
    q_by_layout = {}
    for lay in layouts:
        cal = u[u["layout"] != lay]
        if len(cal) < 10:
            continue
        k = int(math.ceil((len(cal) + 1) * (1 - a0)))
        q_by_layout[lay] = float(np.sort(cal["s"].to_numpy(float))[min(k, len(cal)) - 1])
    u["width"] = [q_by_layout.get(l, np.nan) * s for l, s in zip(u["layout"], u["spread"])]
    u = u.sort_values("width")
    fr = np.linspace(0.1, 1.0, 10)
    curve_sel, curve_rand = [], []
    rng2 = np.random.default_rng(SEED + 2)
    for f in fr:
        n = max(1, int(f * len(u)))
        curve_sel.append(float(u.iloc[:n]["regret"].mean()))
        rs = [float(u.sample(n=n, random_state=int(rng2.integers(1e6)))["regret"].mean()) for _ in range(50)]
        curve_rand.append(float(np.mean(rs)))
    aurc_sel = float(np.mean(curve_sel))
    aurc_rand = float(np.mean(curve_rand))
    res["selective_prediction"] = {"alpha": a0, "fractions": list(fr),
                                   "risk_by_width": curve_sel, "risk_random": curve_rand,
                                   "aurc_width": aurc_sel, "aurc_random": aurc_rand,
                                   "aurc_diff": aurc_sel - aurc_rand}

    h032 = all(abs(plain[a]["empirical"] - (1 - a)) <= 0.05
               and plain[a]["ci95_layout_bootstrap"][0] <= (1 - a) <= plain[a]["ci95_layout_bootstrap"][1]
               for a in (0.1, 0.2, 0.3) if a in plain)
    h033 = bool(aurc_sel < aurc_rand - 0.002)
    h034 = bool(res["spread_vs_regret"]["ci95_layout_bootstrap"]
                and res["spread_vs_regret"]["ci95_layout_bootstrap"][0] > 0)
    res["decisions"] = {"H032_coverage_valid": h032, "H033_selective_better_than_random": h033,
                        "H034_width_informative": h034}
    res["decisions"]["verdict"] = (
        "conformal_gives_valid_and_ordered_uncertainty" if h032 and h034 else
        "valid_coverage_but_no_ordering" if h032 else
        "exchangeability_broken")
    res["limits"] = [
        "Conformal validity assumes exchangeability; layouts differ by date and plates, which is exactly what this test probes.",
        "Regret is defined against the cell's own measured minimum, so it inherits that measurement's noise.",
        "Functional viability only; no mechanism, selectivity or clinical claim.",
        "Exploratory: plates were used as scoring endpoints earlier.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r16/PROTOCOL_E016.md",
                "research/2026-10-27-agent-cell-identifiability-r16/e016_conformal.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E016_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    u.to_csv(OUT / "E016_units.csv", index=False)

    print("units=%d layouts=%d mean regret=%.4f mean spread=%.4f" % (
        len(u), u["layout"].nunique(), u["regret"].mean(), u["spread"].mean()))
    print("plain conformal coverage:")
    for a, v in plain.items():
        print("   alpha=%.2f nominal=%.2f empirical=%.3f CI=%s" % (a, v["nominal"], v["empirical"],
                                                                  ["%.3f" % x for x in v["ci95_layout_bootstrap"]]))
    print("adaptive conformal coverage:")
    for a, v in adapt.items():
        print("   alpha=%.2f nominal=%.2f empirical=%.3f mean width=%.4f" % (a, v["nominal"], v["empirical"], v["mean_width"]))
    print("spread vs regret spearman=%.3f CI=%s" % (rho, res["spread_vs_regret"]["ci95_layout_bootstrap"]))
    print("AURC width=%.4f random=%.4f diff=%+.4f" % (aurc_sel, aurc_rand, aurc_sel - aurc_rand))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
