"""
STAGE 1 — independent estimate of well-level replicate noise in PAIR_SCREEN.csv,
and a noise-based verdict on two specific readout-order contrasts.

Written BEFORE reading any result file in the audited directory.
Input : research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv
Output: independent_estimate.json, stage1_log.txt

Contrast under test (given in the brief):
  d = Viability(well1) - Viability(well2), one pair per file, K = 2 files per cell
    A673 : O1 - O2   in Plate 157, Plate 158
    BJ   : N22 - O22 in Plate 147, Plate 148

Noise model
-----------
  V_i(w) = mu(w) + p_i + e_i(w)                     i = plate/file, w = well
  p_i  : plate offset, cancels in a within-plate contrast
  e_i(w): per-well preparation/read error, sd sigma, with within-plate correlation rho
          at two different well positions (dye / edge / seeding gradient)
  d_i  = (mu1-mu2) + e_i(w1) - e_i(w2);   Var(d_i) = 2*sigma^2*(1-rho) =: Vd
  dbar = mean over K files;  SE(dbar) = sqrt(Vd / K)
  The audited analysis uses rho = 0 and sigma from same-condition duplicate wells:
  SE = sigma*sqrt(2/K); note sqrt(2/K) = 1 for K = 2, so its SE equals its sigma.

PRIMARY estimator (P) measures Vd directly and therefore needs no rho assumption:
  replicate plates give diff(w) = e1(w) - e2(w) with E[diff] = 0 for the same well.
  For two wells w1,w2 the quantity  D = diff(w1) - diff(w2)  has E[D] = 0 and
  Var(D) = 2*Vd   =>   Vd = Var(D)/2.
  That is a direct, assumption-light estimate of the variance of the very
  within-plate contrast being tested, at matched well geometry and viability band.
"""
import json
from math import erf, sqrt

import numpy as np
import pandas as pd

RAW = r"D:\MAESTRO\research\eight_directions_20261026\evidence_audit\raw\PAIR_SCREEN.csv"
OUT = r"D:\MAESTRO\research\2026-10-27-agent-cell-identifiability-r4\challenge"
TPK = "ABCDEFGHIJKLMNOP"

log = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    log.append(s)


def sd(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return (x.std(ddof=1), len(x)) if len(x) > 4 else (np.nan, len(x))


def mad_sd(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return (1.4826 * np.median(np.abs(x - np.median(x))), len(x)) if len(x) > 4 else (np.nan, len(x))


def p2(t):
    return 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


# ------------------------------------------------------------------ load
df = pd.read_csv(RAW, low_memory=False)
df["col"] = df["Well"].str.extract(r"(\d+)").astype(int)
df["row"] = df["Well"].str.extract(r"([A-P]+)")
df["ri"] = df["row"].map({r: i for i, r in enumerate(TPK)})
df["iter"] = df["Iteration"].astype(str)
df["cell"] = df["Cell line"].astype(str)
df["ctl"] = df["Drug 1"].isin(["high control", "low control", "dmso"])
say(f"rows={len(df)} files={df.file.nunique()} cells={df.cell.nunique()} iters={df.iter.nunique()}")

# ------------------------------------------------------------------ hazards
hc = df[df["Drug 1"] == "high control"]
lc = df[df["Drug 1"] == "low control"]
per_file = df.groupby("file").apply(
    lambda g: pd.Series({
        "hc_all_1": bool((g.loc[g["Drug 1"] == "high control", "Viability"] == 1).all()),
        "lc_all_0": bool((g.loc[g["Drug 1"] == "low control", "Viability"] == 0).all()),
        "n_hc": int((g["Drug 1"] == "high control").sum()),
    }), include_groups=False)
HZ = {
    "n_rows": int(len(df)),
    "n_well_viability_eq_0": int((df.Viability == 0).sum()),
    "n_well_viability_eq_1": int((df.Viability == 1).sum()),
    "frac_viability_clipped_0_or_1": round(float(((df.Viability == 0) | (df.Viability == 1)).mean()), 4),
    "n_viability_outside_0_1": int(((df.Viability < 0) | (df.Viability > 1)).sum()),
    "n_nan_viability": int(df.Viability.isna().sum()),
    "n_duplicate_well_within_file": int(df.duplicated(["file", "Well"]).sum()),
    "n_exact_duplicate_rows": int(df.drop(columns=["Unnamed: 0"]).duplicated().sum()),
    "n_failed_qc": int(df["Failed QC"].sum()),
    "frac_files_all_hc_exactly_1": round(float(per_file.hc_all_1.mean()), 3),
    "frac_files_all_lc_exactly_0": round(float(per_file.lc_all_0.mean()), 3),
    "n_lc_not_zero": int((lc.Viability != 0).sum()),
    "n_lc": int(len(lc)),
    "n_hc_not_one": int((hc.Viability != 1).sum()),
    "n_hc": int(len(hc)),
}
say("\nHAZARDS " + json.dumps(HZ, indent=1))

# normalisation identity  V = (raw - LC)/(HC - LC), clipped to [0,1]
norm = []
for f, g in df.groupby("file"):
    m = g[(g.Viability > 0.02) & (g.Viability < 0.98)]
    h = g.loc[g["Drug 1"] == "high control", "Raw count"]
    l = g.loc[g["Drug 1"] == "low control", "Raw count"]
    if len(m) < 20 or len(h) == 0 or len(l) == 0:
        continue
    a, b = np.polyfit(m.Viability, m["Raw count"], 1)
    norm.append((f, a / (h.mean() - l.mean()), b - l.mean()))
N = pd.DataFrame(norm, columns=["file", "ratio", "icpt"])
NORM = {"n_files": int(len(N)),
        "slope_over_HC_minus_LC_median": round(float(N.ratio.median()), 4),
        "slope_over_HC_minus_LC_iqr": [round(float(N.ratio.quantile(.25)), 4),
                                       round(float(N.ratio.quantile(.75)), 4)],
        "intercept_minus_LC_median": round(float(N.icpt.median()), 1)}
say("\nNORMALISATION " + json.dumps(NORM))

# ------------------------------------------------------------------ replicate plates
df["wkey"] = (df.Well.astype(str) + "|" + df["Drug 1"].astype(str) + "|" +
              df["Drug 2"].astype(str) + "|" + df["Conc 1 (uM)"].astype(str) + "|" +
              df["Conc 2 (uM)"].astype(str))
groups = {}
for f, g in df.groupby("file"):
    groups.setdefault((hash(tuple(sorted(g.wkey))), g.cell.iloc[0]), []).append(f)
rep_pairs = []
for _, fl in groups.items():
    fl = sorted(fl)
    rep_pairs += [(fl[i], fl[j]) for i in range(len(fl)) for j in range(i + 1, len(fl))]
say(f"\nsame-layout same-cell-line file pairs: {len(rep_pairs)} "
    f"({len(set(f for p in rep_pairs for f in p))} files)")

tabs = {}
for f, g in df.groupby("file"):
    tabs[f] = g.set_index("Well")
DIFF = {}      # file-pair -> DataFrame well, diff, vbar, row, col, clipped
for f1, f2 in rep_pairs:
    a, b = tabs[f1], tabs[f2]
    com = a.index.intersection(b.index)
    a, b = a.loc[com], b.loc[com]
    keep = ~(a.ctl.values | b.ctl.values)
    DIFF[(f1, f2)] = pd.DataFrame({
        "well": com[keep], "diff": (a.Viability - b.Viability).values[keep],
        "vbar": ((a.Viability + b.Viability) / 2).values[keep],
        "raw_vbar": ((a["Raw count"] + b["Raw count"]) / 2).values[keep],
        "clipped_flag": (a.Viability.isin([0, 1]) | b.Viability.isin([0, 1])).values[keep],
        "ri": a.ri.values[keep], "col": a.col.values[keep],
        "fq": (a["Failed QC"] | b["Failed QC"]).values[keep],
        "iter": a.iter.iloc[0], "cell": a.cell.iloc[0],
        "f1": f1, "f2": f2,
    })
D = pd.concat(DIFF.values(), ignore_index=True)
say(f"replicate-plate same-well differences (non-control): {len(D)} in {D.groupby(['f1','f2']).ngroups} pairs")

# --- E1: per-well sigma from the same-well differences (no rho adjustment)
E1 = {}
for tag, sub in [("all", D), ("stage11", D[D["iter"] == "11"]),
                 ("band_0.55_0.95_unclipped", D[(D.vbar.between(0.55, 0.95)) & ~D["clipped_flag"]])]:
    s, n = sd(sub["diff"])
    E1[tag] = {"sigma": float(s / sqrt(2)), "n": int(n),
               "sd_of_diff": float(s), "mean_diff": float(sub["diff"].mean())}
    sr, _ = mad_sd(sub["diff"])
    E1[tag]["sigma_robust"] = float(sr / sqrt(2))
say("\nE1 same-well across replicate plates (sigma = sd(diff)/sqrt(2)):")
for k, v in E1.items():
    say(f"   {k:26s} sigma={v['sigma']:.5f} robust={v['sigma_robust']:.5f} "
        f"n={v['n']:6d} mean_offset={v['mean_diff']:+.5f}")

# --- P: PRIMARY, direct contrast variance at matched geometry & level
CONTRASTS = {}


def contrast_var(geom, lo=0.0, hi=0.05, iters=None):
    """Vd = Var(diff(w1)-diff(w2))/2 over well pairs with the given geometry.

    Pivots each replicate file-pair onto the (row, col) grid and shifts it, so
    w2 is the neighbouring well of w1.  vbar is the mean of the two plates, used
    only to restrict the viability band; 'diff' differences out the true effect,
    so no compound effect leaks into the variance.
    """
    out = []
    for (f1, f2), g in D.groupby(["f1", "f2"], sort=False):
        if iters is not None and g["iter"].iloc[0] not in iters:
            continue
        pv = g.pivot_table(index="ri", columns="col", values="vbar")
        pc = g.pivot_table(index="ri", columns="col", values="clipped_flag") > 0.5
        pff = g.pivot_table(index="ri", columns="col", values="fq") > 0.5
        pd_ = g.pivot_table(index="ri", columns="col", values="diff")
        band = ((pv >= lo) & (pv <= hi) & ~pc & ~pff).astype(float).fillna(0.0)
        for (dr, dc) in geom:
            d2 = pd_.shift(periods=-dc, axis=1) if dr == 0 else pd_.shift(periods=-dr, axis=0)
            b2 = (band.shift(periods=-dc, axis=1) if dr == 0 else band.shift(periods=-dr, axis=0)).fillna(0.0)
            mask = ((band.values == 1) & (b2.values == 1) & np.isfinite(pd_.values) & np.isfinite(d2.values))
            if mask.any():
                out.append((pd_.values - d2.values)[mask])
    if not out:
        return None
    x = np.concatenate(out)
    s, n = sd(x)
    sr, _ = mad_sd(x)
    return {"Vd": float(s ** 2 / 2), "sigma_equiv": float(s / 2), "n_pairs": int(n),
            "mean_D": float(x.mean()), "Vd_robust": float(sr ** 2 / 2),
            "sigma_equiv_robust": float(sr / 2)}


for name, (geom, lo, hi) in {
    "adjacent_column_same_row": ([(0, 1)], 0.55, 0.95),
    "adjacent_row_same_column": ([(1, 0)], 0.55, 0.95),
    "adjacent_column_same_row_wide": ([(0, 1)], 0.0, 1.0),
}.items():
    CONTRASTS[name] = contrast_var(geom, lo, hi)
    c = CONTRASTS[name]
    if c:
        say(f"P {name:30s} Vd={c['Vd']:.6f} -> per-well sigma_equiv={c['sigma_equiv']:.5f} "
            f"(robust {c['sigma_equiv_robust']:.5f}) n_pairs={c['n_pairs']} meanD={c['mean_D']:+.5f}")

# stage-11-only version of the primary estimate
CONTRASTS["adj_col_stage11"] = contrast_var([(0, 1)], 0.55, 0.95, iters={"11"})
if CONTRASTS["adj_col_stage11"]:
    c = CONTRASTS["adj_col_stage11"]
    say(f"P adjacent_column_same_row [stage11]  Vd={c['Vd']:.6f} sigma_equiv={c['sigma_equiv']:.5f} "
        f"n_pairs={c['n_pairs']}")

# ------------------------------------------------------------------ E2 within-plate duplicates
rows = []
for (f, d1, d2, c1, c2), g in df.groupby(["file", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)"],
                                         dropna=False):
    if len(g) < 2:
        continue
    v = g[["Well", "ri", "col", "Viability", "Raw count", "Failed QC"]].values
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            rows.append((f, d1, abs(int(v[i][1]) - int(v[j][1])), abs(int(v[i][2]) - int(v[j][2])),
                         float(v[i][3]), float(v[j][3]), bool(v[i][5]) or bool(v[j][5])))
DD = pd.DataFrame(rows, columns=["file", "d1", "dr", "dc", "vA", "vB", "fq"])
DD["ctl"] = DD.d1.isin(["high control", "low control"])
Dc = DD[~DD.ctl].copy()
Dc["vbar"] = (Dc.vA + Dc.vB) / 2
Dc["clipped_flag"] = Dc.vA.isin([0, 1]) | Dc.vB.isin([0, 1])
GEO = Dc.groupby(["dr", "dc"]).size().sort_values(ascending=False).head(6).to_dict()
say(f"\nwithin-plate duplicate pairs: drug={len(Dc)} control={int(DD.ctl.sum())}; geometry {GEO}")
say(f"   both wells ==1: {float(((Dc.vA==1)&(Dc.vB==1)).mean()):.3f}; any clipped: "
    f"{float(Dc['clipped_flag'].mean()):.3f}; median vbar {Dc.vbar.median():.3f}")

E2 = {}
for tag, sub in [("all_levels", Dc),
                 ("window_0.75_1", Dc[Dc.vbar.between(0.75, 1.0)]),
                 ("band_0.55_0.95_unclipped", Dc[Dc.vbar.between(0.55, 0.95) & ~Dc["clipped_flag"]])]:
    s, n = sd(sub.vA - sub.vB)
    sr, _ = mad_sd(sub.vA - sub.vB)
    E2[tag] = {"sigma": float(s / sqrt(2)), "n": int(n), "sigma_robust": float(sr / sqrt(2)),
               "frac_both_at_1": float(((sub.vA == 1) & (sub.vB == 1)).mean()) if len(sub) else None}
say("E2 within-plate same-condition duplicates:")
for k, v in E2.items():
    say(f"   {k:26s} sigma={v['sigma']:.5f} robust={v['sigma_robust']:.5f} n={v['n']:6d} "
        f"frac_both_at_1={v['frac_both_at_1']}")

# ------------------------------------------------------------------ E3 adjacent control columns (raw)
cc = df[df["Drug 1"] == "high control"].groupby("file")["col"].agg(lambda s: sorted(s.unique()))
multi = {f: v for f, v in cc.items() if len(v) >= 2}
rec = []
for f, cols in multi.items():
    g = df[(df.file == f) & (df["Drug 1"] == "high control")]
    w = g.pivot_table(index="row", columns="col", values="Raw count")
    lcm = df[(df.file == f) & (df["Drug 1"] == "low control")]["Raw count"].mean()
    span = g["Raw count"].mean() - lcm
    for k in range(len(cols) - 1):
        dd = (w[cols[k]] - w[cols[k + 1]]).dropna() / span
        rec += [(f, cols[k], r, v) for r, v in dd.items()]
C = pd.DataFrame(rec, columns=["file", "colA", "row", "dv"])
E3 = {}
if len(C):
    s, n = sd(C.dv)
    E3 = {"sigma": float(s / sqrt(2)), "n": int(n), "mean_offset": float(C.dv.mean()),
          "offset_by_col": {f"col{k}": {"mean": round(float(v['mean']), 5), "n": int(v['count'])}
                            for k, v in C.groupby("colA").dv.agg(['mean', 'count']).to_dict('index').items()},
          "n_files": int(C.file.nunique())}
    say(f"\nE3 adjacent high-control columns: sigma={E3['sigma']:.5f} n={n} files={E3['n_files']} "
        f"mean offset={E3['mean_offset']:+.5f}")
    say("   offset by column pair: " + json.dumps(E3["offset_by_col"]))
else:
    say("\nE3 not available")

# ------------------------------------------------------------------ E4 poisson floor
den = df.groupby("file").apply(
    lambda g: g.loc[g["Drug 1"] == "high control", "Raw count"].mean() -
              g.loc[g["Drug 1"] == "low control", "Raw count"].mean(), include_groups=False)
df["den"] = df.file.map(den)
P4 = (np.sqrt(df["Raw count"]) / df["den"])[(df.Viability > 0.05) & (df.Viability < 0.95)]
E4 = {"sigma": float(P4.median()), "n": int(len(P4))}
say(f"\nE4 Poisson read-noise floor sigma={E4['sigma']:.5f} (median, n={E4['n']})")

# ------------------------------------------------------------------ row/column position
posrec = []
for f, g in df[df["Drug 1"] == "high control"].groupby("file"):
    lcm = df[(df.file == f) & (df["Drug 1"] == "low control")]["Raw count"].mean()
    span = g["Raw count"].mean() - lcm
    mu = g["Raw count"].mean()
    for r, v in g.groupby("row")["Raw count"].mean().items():
        posrec.append((f, r, (v - mu) / span))
POS = pd.DataFrame(posrec, columns=["file", "row", "dev"])
rp = POS.groupby("row").dev.mean()
say("\nHC row profile (viability units): " + ", ".join(f"{r}:{v:+.3f}" for r, v in rp.items()))
say(f"   sd across rows={rp.std():.5f}; within-row sd across plates={POS.dev.std():.5f}")
pN = POS[POS.row == "N"].set_index("file").dev
pO = POS[POS.row == "O"].set_index("file").dev
com = pN.index.intersection(pO.index)
dNO = pO.loc[com] - pN.loc[com]
ROWNO = {"mean": float(dNO.mean()), "sd": float(dNO.std()), "n": int(len(dNO)),
         "t": float(dNO.mean() / (dNO.std() / sqrt(len(dNO))))}
say(f"   rowO-rowN offset {ROWNO['mean']:+.5f} (sd {ROWNO['sd']:.5f}, n={ROWNO['n']}, t={ROWNO['t']:.2f})")

# ------------------------------------------------------------------ probes
probes = [("A673", "Plate 157", "O1", "O2"), ("A673", "Plate 158", "O1", "O2"),
          ("BJ", "Plate 147", "N22", "O22"), ("BJ", "Plate 148", "N22", "O22")]
pr = []
for cell, pre, w1, w2 in probes:
    f = [x for x in df.file.unique() if x.startswith(pre)][0]
    g = tabs[f]
    a, b = g.loc[w1], g.loc[w2]
    pr.append({"cell": cell, "plate": pre, "file": f, "w1": w1, "w2": w2,
               "combo1": f"{a['Drug 1']} {a['Conc 1 (uM)']} + {a['Drug 2']} {a['Conc 2 (uM)']}",
               "combo2": f"{b['Drug 1']} {b['Conc 1 (uM)']} + {b['Drug 2']} {b['Conc 2 (uM)']}",
               "v1": float(a.Viability), "v2": float(b.Viability),
               "raw1": float(a["Raw count"]), "raw2": float(b["Raw count"]),
               "fq1": bool(a["Failed QC"]), "fq2": bool(b["Failed QC"]),
               "d": float(a.Viability - b.Viability)})
PR = pd.DataFrame(pr)
say("\nPROBE WELLS")
say(PR[["cell", "plate", "w1", "combo1", "v1", "w2", "combo2", "v2", "d"]].to_string(index=False))
say(PR.groupby("cell").d.agg(["mean", "min", "max", "count"]).round(6).to_string())

# ------------------------------------------------------------------ verdicts
ests = {
    "P_contrast_var_adjacent_column": CONTRASTS.get("adjacent_column_same_row"),
    "P_contrast_var_adjacent_row": CONTRASTS.get("adjacent_row_same_column"),
    "P_contrast_var_adjacent_column_stage11": CONTRASTS.get("adj_col_stage11"),
    "E1_replicate_plate_all": E1["all"],
    "E1_replicate_plate_stage11": E1["stage11"],
    "E1_replicate_plate_band": E1["band_0.55_0.95_unclipped"],
    "E2_within_dup_all": E2["all_levels"],
    "E2_within_dup_0.75_1": E2["window_0.75_1"],
    "E2_within_dup_band": E2["band_0.55_0.95_unclipped"],
    "E3_adjacent_control_columns": E3,
    "E4_poisson_floor": E4,
}
sig = {}
for k, v in ests.items():
    if not v:
        continue
    if "Vd" in v:
        sig[k] = {"sd_contrast": float(np.sqrt(v["Vd"])), "n": v["n_pairs"],
                  "source": "direct variance of the within-plate contrast"}
    else:
        sig[k] = {"sd_contrast": float(v["sigma"] * sqrt(2)), "n": v["n"],
                  "source": "per-well sigma * sqrt(2) (rho = 0)"}

V = {}
for cell in ["A673", "BJ"]:
    sub = PR[PR.cell == cell]
    dbar = float(sub.d.mean())
    out = {"per_file_d": {r.plate: round(r.d, 6) for r in sub.itertuples()},
           "dbar_K2": dbar, "tests": {}}
    for k, v in sig.items():
        se = v["sd_contrast"] / sqrt(2)          # mean of K = 2 independent per-file contrasts
        t = dbar / se
        out["tests"][k] = {"sd_contrast": round(v["sd_contrast"], 6), "SE": round(se, 6),
                           "t": round(t, 3), "p_two_sided": round(p2(t), 5),
                           "detectable_at_0.05": bool(p2(t) < 0.05), "n_source": v["n"]}
    V[cell] = out

say("\n=== VERDICTS  (SE = sd_contrast/sqrt(K), K=2) ===")
for cell, o in V.items():
    say(f"\n{cell}  dbar={o['dbar_K2']:+.5f}   per-file d={o['per_file_d']}")
    for k, t in o["tests"].items():
        say(f"   {k:40s} sd_d={t['sd_contrast']:.5f} SE={t['SE']:.5f} t={t['t']:+7.2f} "
            f"p={t['p_two_sided']:.4g}  {'DETECTABLE' if t['detectable_at_0.05'] else 'not detectable'}")

# ------------------------------------------------------------------ readout cross-check
# Viability is truncated to [0,1] and is not an exact affine function of Raw count, so
# recompute each contrast from raw counts, which are neither truncated nor corrected.
XC = []
for cell, pre, w1, w2 in probes:
    f = [x for x in df.file.unique() if x.startswith(pre)][0]
    g = tabs[f]
    span = (g.loc[g["Drug 1"] == "high control", "Raw count"].mean() -
            g.loc[g["Drug 1"] == "low control", "Raw count"].mean())
    dr = (g.loc[w1, "Raw count"] - g.loc[w2, "Raw count"]) / span
    dv = g.loc[w1, "Viability"] - g.loc[w2, "Viability"]
    XC.append({"cell": cell, "plate": pre, "d_viability": float(dv), "d_raw_span": float(dr),
               "diff": float(dv - dr), "hc_minus_lc": float(span)})
XC = pd.DataFrame(XC)
say("\nREADOUT CROSS-CHECK (raw-count contrast vs Viability contrast)")
say(XC.round(6).to_string(index=False))
say(XC.groupby("cell")[["d_viability", "d_raw_span", "diff"]].mean().round(6).to_string())

# ------------------------------------------------------------------ save
res = {
    "analysis_id": "stage1_independent_noise_and_identifiability",
    "written_before_reading_any_result_file": True,
    "date": "2026-10-27",
    "input": RAW,
    "n_rows": int(len(df)),
    "contrast": "d = Viability(w1) - Viability(w2) within one file; dbar = mean over K=2 files",
    "hazards": HZ,
    "normalisation": NORM,
    "noise_model": "Var(d_i) = Vd = 2*sigma^2*(1-rho); SE(dbar) = sqrt(Vd/K); author's case rho=0, SE = sigma*sqrt(2/K)",
    "primary_estimator": {
        "name": "P_contrast_var",
        "definition": "Vd = Var(diff(w1)-diff(w2))/2, diff = V(file1,well)-V(file2,well); "
                      "E[D]=0 by construction so no true drug effect enters",
        "value_Vd_adjacent_column": CONTRASTS["adjacent_column_same_row"]["Vd"] if CONTRASTS["adjacent_column_same_row"] else None,
        "sd_contrast_adjacent_column": float(np.sqrt(CONTRASTS["adjacent_column_same_row"]["Vd"])) if CONTRASTS["adjacent_column_same_row"] else None,
        "n_well_pairs": CONTRASTS["adjacent_column_same_row"]["n_pairs"] if CONTRASTS["adjacent_column_same_row"] else None,
    },
    "all_noise_estimates": {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv)
                                for kk, vv in v.items()} for k, v in ests.items() if v},
    "positional": {"hc_row_profile": {r: round(float(v), 5) for r, v in rp.items()},
                   "hc_row_profile_sd": round(float(rp.std()), 5),
                   "hc_within_row_sd": round(float(POS.dev.std()), 5),
                   "rowO_minus_rowN": {k: round(v, 5) for k, v in ROWNO.items()},
                   "note": "rows and columns of the primary screen ARE Drug2 and Drug1 identity, so a "
                           "positional effect is not separable from a compound effect at a single well"},
    "probes": PR.drop(columns=["file"]).to_dict(orient="records"),
    "readout_cross_check_raw_counts": XC.round(6).to_dict(orient="records"),
    "verdicts": V,
}
res["conclusion"] = {}
for cell, o in V.items():
    flags = [t["detectable_at_0.05"] for t in o["tests"].values()]
    res["conclusion"][cell] = {
        "dbar": round(o["dbar_K2"], 6),
        "all_estimators_detectable": bool(all(flags)),
        "no_estimator_detectable": bool(not any(flags)),
        "n_detectable": int(sum(flags)), "n_estimators": len(flags),
        "dbar_over_primary_sd_contrast": round(
            o["dbar_K2"] / o["tests"]["P_contrast_var_adjacent_column"]["sd_contrast"], 2)
        if "P_contrast_var_adjacent_column" in o["tests"] else None,
    }
say("\nCONCLUSION " + json.dumps(res["conclusion"], indent=1))

with open(OUT + r"\independent_estimate.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, default=str)
with open(OUT + r"\stage1_log.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(log))
say("\nwrote independent_estimate.json + stage1_log.txt")





