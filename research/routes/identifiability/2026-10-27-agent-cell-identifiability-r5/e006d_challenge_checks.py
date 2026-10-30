"""E006d: checks demanded by the independent challenge (challenge/CHALLENGE.md).

1. Calibration of the parametric null against the same-cell split-half control.
   The challenger's point 7: under the truth "same cell, two files", any usable null
   must reproduce the observed same-cell agreement. If the parametric null predicts a
   much higher same-cell agreement than observed, that null is misspecified - which is
   why AMENDMENT-003 replaced it with the empirical ceiling.
2. Layout-clustered bootstrap of the per-cell drop (inference that respects shared plates).
3. Stricter detectability floor (sigma = 0.059, the high-viability bin from R4) so the
   concordance gap is not an artefact of an optimistic pooled sigma.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r5"
ANCHORS = {"high control", "low control"}
N_SUB = 60
N_REDRAW = 50
N_SIM = 200
N_BOOT = 2000
SEED = 20261027
STRICT_SIGMA = 0.059


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def main() -> None:
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")

    files = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        files[fname] = {"cell": g["Cell line"].iloc[0],
                        "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                        "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                        "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                  for w, (d1, c1, d2, c2) in
                                  {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                        "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in files.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    def vec(fname: str, units: list[str]) -> np.ndarray:
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    rng = np.random.default_rng(SEED)
    calib, per_cell, strict = [], [], []
    for (it, h), cells in groups.items():
        if len(cells) < 3:
            continue
        good = [c for c in sorted(cells) if max(files[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        units = [u for u in sorted(files[cells[good[0]][0]]["combo"]) if files[cells[good[0]][0]]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        if np.all(np.vstack([np.sum([~np.isnan(v) for v in V[c]], axis=0) > 0 for c in good]), axis=0).sum() < 20:
            continue
        sub_idx = [rng.choice(len(units), N_SUB, replace=False) for _ in range(N_REDRAW)]

        # ---- 1. parametric-null calibration against the same-cell control ----
        for c in good:
            if len(V[c]) < 2:
                continue
            a, b = V[c][0], V[c][1]
            obs = []
            for idx in sub_idx:
                aa, bb = a[idx], b[idx]
                ok = ~np.isnan(aa) & ~np.isnan(bb)
                if ok.sum() >= 20:
                    obs.append(spearman(aa[ok], bb[ok]))
            if not obs:
                continue
            obs_tau = float(np.mean(obs))
            m = np.nanmean(np.vstack([a, b]), axis=0)
            ok = ~np.isnan(m)
            mm = m[ok]
            # de-noise the cell's own profile and re-inject iid noise at the measured level
            sig_file = float(np.nanstd(a - b, ddof=1) / math.sqrt(2.0))
            lam = math.sqrt(max(0.0, 1.0 - sig_file ** 2 / max(np.var(mm), 1e-12)))
            prof = mm.mean() + lam * (mm - mm.mean())
            pred = []
            for _ in range(N_SIM):
                x = prof + rng.normal(0, sig_file, prof.size)
                y = prof + rng.normal(0, sig_file, prof.size)
                pred.append(spearman(x, y))
            calib.append({"layout": f"{it}/{h[:12]}", "cell": c, "tau_half_observed": obs_tau,
                          "tau_half_predicted_parametrically": float(np.mean(pred)),
                          "sigma_per_file": sig_file, "n_units": int(prof.size)})

        # ---- 3. strict floor concordance (half vs cross) ----
        for c in good:
            if len(V[c]) < 2:
                continue
            a = V[c][0]
            # same-cell strict concordance
            def strict_conc(x, y):
                n = x.size
                i, j = np.triu_indices(n, 1)
                gx = np.abs(x[i] - x[j])
                gy = np.abs(y[i] - y[j])
                keep = (gx >= STRICT_SIGMA) & (gy >= STRICT_SIGMA)
                if keep.sum() < 10:
                    return float("nan"), 0
                return float(np.mean(np.sign(x[i][keep] - x[j][keep]) == np.sign(y[i][keep] - y[j][keep]))), int(keep.sum())
            half_c, half_n = strict_conc(V[c][0], V[c][1])
            for d in good:
                if d == c:
                    continue
                vals = [strict_conc(fa, fb) for fa in V[c] for fb in V[d]]
                cs = [v[0] for v in vals if np.isfinite(v[0])]
                if cs and np.isfinite(half_c):
                    strict.append({"layout": f"{it}/{h[:12]}", "cell_a": c, "cell_b": d,
                                   "conc_half_strict": half_c, "conc_cross_strict": float(np.mean(cs)),
                                   "diff": float(np.mean(cs)) - half_c, "n_pairs_half": half_n})

    cal = pd.DataFrame(calib)
    st = pd.DataFrame(strict)
    res = {
        "kind": "challenge_checks_for_E006",
        "input_sha256": sha256(CSV),
        "check1_param_null_calibration": {
            "n_cell_controls": int(len(cal)),
            "median_tau_half_observed": float(cal["tau_half_observed"].median()) if len(cal) else None,
            "median_tau_half_predicted": float(cal["tau_half_predicted_parametrically"].median()) if len(cal) else None,
            "median_gap_observed_minus_predicted": float((cal["tau_half_observed"] - cal["tau_half_predicted_parametrically"]).median()) if len(cal) else None,
            "n_controls_observed_below_predicted": int((cal["tau_half_observed"] < cal["tau_half_predicted_parametrically"]).sum()) if len(cal) else None,
            "interpretation": ("If observed same-cell agreement is materially below what the parametric null "
                               "predicts for the same quantity, that null is misspecified and cannot be used "
                               "to reject anything - which is why AMENDMENT-003 replaced it with the empirical "
                               "ceiling."),
            "table": cal.round(4).to_dict("records"),
        },
        "check2_layout_clustered_bootstrap": {},
        "check3_strict_floor": {
            "strict_sigma": STRICT_SIGMA,
            "n_cellpairs": int(len(st)),
            "median_conc_half_strict": float(st["conc_half_strict"].median()) if len(st) else None,
            "median_conc_cross_strict": float(st["conc_cross_strict"].median()) if len(st) else None,
            "median_diff_cross_minus_half": float(st["diff"].median()) if len(st) else None,
            "frac_cellpairs_with_negative_diff": float((st["diff"] < 0).mean()) if len(st) else None,
            "median_pairs_used_half": float(st["n_pairs_half"].median()) if len(st) else None,
        },
    }

    # ---- 2. layout-clustered bootstrap on the per-cell drop ----
    pc = pd.DataFrame(per_cell)
    base = json.loads((OUT / "E006C_ROBUSTNESS.json").read_text(encoding="utf-8"))
    tab = pd.DataFrame(base["per_cell_table"])
    if len(tab):
        layouts = sorted(tab["layout"].unique())
        boots = []
        for _ in range(N_BOOT):
            pick = rng.choice(layouts, size=len(layouts), replace=True)
            sel = pd.concat([tab[tab["layout"] == p] for p in pick])
            if len(sel):
                boots.append(float(sel["drop"].median()))
        boots = np.asarray(boots)
        res["check2_layout_clustered_bootstrap"] = {
            "n_layouts": len(layouts),
            "median_drop": float(tab["drop"].median()),
            "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "n_cells": int(len(tab)),
            "n_cells_drop_positive": int((tab["drop"] > 0).sum()),
            "note": "resamples whole layouts, so shared plates and days are carried together",
        }
    (OUT / "E006D_CHALLENGE_CHECKS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    c1 = res["check1_param_null_calibration"]
    print("CHECK1 same-cell calibration: n=%d observed=%.3f predicted=%.3f gap=%.3f | observed<predicted in %d" % (
        c1["n_cell_controls"], c1["median_tau_half_observed"] or float("nan"),
        c1["median_tau_half_predicted"] or float("nan"),
        c1["median_gap_observed_minus_predicted"] or float("nan"),
        c1["n_controls_observed_below_predicted"] or 0))
    print("CHECK2 layout-clustered:", res["check2_layout_clustered_bootstrap"])
    c3 = res["check3_strict_floor"]
    print("CHECK3 strict floor (sigma=%.3f): half=%.4f cross=%.4f diff=%.4f | fraction pairs negative=%.3f" % (
        STRICT_SIGMA, c3["median_conc_half_strict"] or float("nan"), c3["median_conc_cross_strict"] or float("nan"),
        c3["median_diff_cross_minus_half"] or float("nan"), c3["frac_cellpairs_with_negative_diff"] or float("nan")))


if __name__ == "__main__":
    main()
