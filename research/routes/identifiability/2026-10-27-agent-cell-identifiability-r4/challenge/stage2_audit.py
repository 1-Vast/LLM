"""
STAGE 2 audit — re-implement the audited analysis' estimators independently and
test each of the six audit points numerically.  Does NOT run or modify the
audited script, and never writes outside challenge/.

Checks
  A. reproduce the four per-plate probe differences to 4 dp
  B. reproduce sigma_e naive (anchors in) and the corrected / level-matched values
  C. which plate formats the duplicate pairs come from (exchangeability)
  D. truncation-free noise: replicate-plate RAW-count contrasts (no clipping anywhere)
  E. N2 degeneracy: is sigma_b estimable by the audited formula?
  F. level-mix correction for the A673 contrast (its two wells differ by 0.31 in y)
  G. difference-of-differences test (A673 vs BJ)
  H. power / plates-needed arithmetic, one- and two-sided
"""
import itertools
import json
import math

import numpy as np
import pandas as pd

RAW = r"D:\MAESTRO\research\eight_directions_20261026\evidence_audit\raw\PAIR_SCREEN.csv"
OUT = r"D:\MAESTRO\research\2026-10-27-agent-cell-identifiability-r4\challenge"
ANCH = {"high control", "low control"}
Z95, ZA, ZB = 1.959964, 1.6449, 0.8416
log = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    log.append(s)


def sig2(d):
    d = np.asarray(d, float)
    return float(d.std(ddof=1) / math.sqrt(2)) if d.size > 2 else float("nan")


def norm_sf2(t):
    return 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))


df = pd.read_csv(RAW, low_memory=False)
df["Drug 1"] = df["Drug 1"].astype(str).str.strip()
df["Drug 2"] = df["Drug 2"].astype(str).str.strip()
df["iter"] = df["Iteration"].astype(str)
df["anchor"] = df["Drug 1"].isin(ANCH) | df["Drug 2"].isin(ANCH)
df["clipped"] = (df.Viability == 0.0) | (df.Viability == 1.0)
df["fq"] = df["Failed QC"].astype(str).str.lower().isin(["true", "1"])
df["y"] = df["Viability"]
df["col"] = df["Well"].str.extract(r"(\d+)").astype(int)
df["row"] = df["Well"].str.extract(r"([A-P]+)")
df["ri"] = df["row"].map({r: i for i, r in enumerate("ABCDEFGHIJKLMNOP")})
K4 = ["Drug 1", "Conc 1 (uM)", "Drug 2", "Conc 2 (uM)"]

# ---------------------------------------------------------------- A. probes
say("=" * 78)
say("A. PROBE RECONSTRUCTION (independent, to 4 dp)")
PRB = {("A673", "157", "O1"): "a", ("A673", "157", "O2"): "b",
       ("A673", "158", "O1"): "a", ("A673", "158", "O2"): "b",
       ("BJ", "147", "N22"): "a", ("BJ", "147", "O22"): "b",
       ("BJ", "148", "N22"): "a", ("BJ", "148", "O22"): "b"}
AUTH_Y = {("BJ", "147", "N22"): 0.8790778891519334, ("BJ", "147", "O22"): 0.8995959285970027,
          ("BJ", "148", "N22"): 0.8584440599392772, ("BJ", "148", "O22"): 0.9069964777457572,
          ("A673", "157", "O1"): 0.9343294159333844, ("A673", "157", "O2"): 0.6311935274316424,
          ("A673", "158", "O1"): 0.9370612344276265, ("A673", "158", "O2"): 0.6852453029257801}
rows = []
for (cell, plate, well), letter in PRB.items():
    s = df[(df["Cell line"] == cell) & (df["Plate"] == plate) & (df["Well"] == well)]
    assert len(s) == 1, (cell, plate, well, len(s))
    r = s.iloc[0]
    rows.append({"cell": cell, "plate": plate, "well": well, "probe": letter,
                 "drug1": r["Drug 1"], "conc1": r["Conc 1 (uM)"],
                 "drug2": r["Drug 2"], "conc2": r["Conc 2 (uM)"],
                 "iteration": r["iter"], "y": float(r["Viability"]),
                 "y_author": AUTH_Y[(cell, plate, well)], "fq": bool(r["fq"])})
P = pd.DataFrame(rows)
P["y_diff"] = (P.y - P.y_author).abs()
say(P[["cell", "plate", "well", "drug1", "conc1", "drug2", "conc2", "iteration", "y"]].to_string(index=False))
say(f"max |y - y_author| over 8 wells = {P.y_diff.max():.2e}")
D4 = []
for cell, (p1, p2, wa, wb) in {"A673": ("157", "158", "O1", "O2"),
                               "BJ": ("147", "148", "N22", "O22")}.items():
    for plate in (p1, p2):
        a = P[(P.cell == cell) & (P.plate == plate) & (P.well == wa)].y.iloc[0]
        b = P[(P.cell == cell) & (P.plate == plate) & (P.well == wb)].y.iloc[0]
        D4.append({"cell": cell, "plate": plate, "y_a": a, "y_b": b, "d": a - b})
D4 = pd.DataFrame(D4)
D4["d_4dp"] = D4.d.round(4)
say(D4.round(6).to_string(index=False))
say("drug pair identical across the two cells? " + str(
    sorted([P[P.cell == "A673"].drug1.iloc[0], P[P.cell == "A673"].drug2.iloc[0]]) ==
    sorted([P[P.cell == "BJ"].drug1.iloc[0], P[P.cell == "BJ"].drug2.iloc[0]])))
say("Drug1/Drug2 roles swapped between cells: " +
    str(P[(P.cell == "A673") & (P.well == "O1")].drug1.iloc[0] != P[(P.cell == "BJ") & (P.well == "N22")].drug1.iloc[0]))

# ---------------------------------------------------------------- B. sigma_e
say("\n" + "=" * 78)
say("B. REPRODUCE THE AUDITED sigma_e")


def pairs(drop_anchor, drop_clipped, qc=True):
    d = df[~df.anchor] if drop_anchor else df
    out = []
    for f, g in d.groupby("file", sort=True):
        for k, sub in g.groupby(K4, sort=False, dropna=False):
            if len(sub) < 2:
                continue
            if qc:
                sub = sub[~sub.fq & sub.y.notna()]
            if drop_clipped:
                sub = sub[~sub.clipped]
            if len(sub) < 2:
                continue
            for (_, r1), (_, r2) in itertools.combinations(sub.iterrows(), 2):
                out.append((f, r1["Cell line"], float(r1.y - r2.y),
                            float((r1.y + r2.y) / 2), str(k[0]).lower() != "dmso" and str(k[2]).lower() != "dmso"))
    return pd.DataFrame(out, columns=["file", "cell", "d", "mean_y", "combo"])


N = pairs(False, False)
say(f"naive (anchors in): n_pairs={len(N)} sigma_e={sig2(N.d):.6f}   [author 233696 / 0.018023]")
say(f"   exact-equal fraction={float((N.d.abs()<1e-9).mean()):.4f} [author 0.4293]")
C = pairs(True, True)
say(f"corrected pooled: n_pairs={len(C)} n_files={C.file.nunique()} sigma_e={sig2(C.d):.6f}  [author 4883 / 140 / 0.044587]")
CB = C[C.combo]
say(f"corrected double-drug: n_pairs={len(CB)} sigma_e={sig2(CB.d):.6f}  [author 1666 / 0.046111]")
L = C[(C.mean_y >= 0.75) & (C.mean_y <= 1.0001)]
LB = L[L.combo]
say(f"level-matched [0.75,1]: n={len(L)} sigma_e={sig2(L.d):.6f}  [author 2453 / 0.040762]")
say(f"level-matched double-drug: n={len(LB)} sigma_e={sig2(LB.d):.6f}  [author 510 / 0.047953]")
for lo, hi, lab in [(0, .25, "[0,.25)"), (.25, .5, "[.25,.5)"), (.5, .75, "[.5,.75)"), (.75, 1.0001, "[.75,1]")]:
    s = C[(C.mean_y >= lo) & (C.mean_y < hi)]
    say(f"   by level {lab}: n={len(s):5d} sigma_e={sig2(s.d):.6f}")

# how much does dropping clipped wells move sigma inside the SAME level window?
L_incl = pairs(True, False)
Li = L_incl[(L_incl.mean_y >= 0.75) & (L_incl.mean_y <= 1.0001)]
say(f"\nSAME window [0.75,1] but KEEPING clipped wells: n={len(Li)} sigma_e={sig2(Li.d):.6f}"
    f"  (drop-clipped value {sig2(L.d):.6f})")
say(f"   of those, both wells at exactly 1.0: {float(((Li.d.abs()<1e-9)).mean()):.4f}")

# ---------------------------------------------------------------- C. format
say("\n" + "=" * 78)
say("C. WHICH PLATE FORMATS SUPPLY THE DUPLICATES")
C2 = C.copy()
C2["fmt"] = np.where(C2.file.str.startswith("Plate"), "primary/validation (Plate N_...)",
                     "Batchie Project_Validation (xlsx)")
say(C2.fmt.value_counts().to_string())
say("iteration of each supplying file (top): " + str(C2.file.map(df.groupby('file')['iter'].first()).value_counts().head(8).to_dict()))
probe_iter = set(P.iteration)
say(f"probe files' iteration = {probe_iter}; duplicate files' iterations = "
    f"{sorted(set(C2.file.map(df.groupby('file')['iter'].first())))}")
say(f"do ANY duplicate pairs come from the 4 probe files? "
    f"{bool(set(C2.file) & set(df[df.Plate.isin(['147','148','157','158']) & df.file.str.startswith(('Plate 147','Plate 148','Plate 157','Plate 158'))].file.unique()))}")

# ---------------------------------------------------------------- D. truncation-free
say("\n" + "=" * 78)
say("D. TRUNCATION-FREE NOISE FROM RAW COUNTS (replicate plates)")
df["wkey"] = (df.Well.astype(str) + "|" + df["Drug 1"] + "|" + df["Drug 2"] + "|" +
              df["Conc 1 (uM)"].astype(str) + "|" + df["Conc 2 (uM)"].astype(str))
grp = {}
for f, g in df.groupby("file"):
    grp.setdefault((hash(tuple(sorted(g.wkey))), g["Cell line"].iloc[0]), []).append(f)
rp = []
for _, fl in grp.items():
    fl = sorted(fl)
    rp += [(fl[i], fl[j]) for i in range(len(fl)) for j in range(i + 1, len(fl))]
tabs = {f: g.set_index("Well") for f, g in df.groupby("file")}
RD = {}
for f1, f2 in rp:
    a, b = tabs[f1], tabs[f2]
    com = a.index.intersection(b.index)
    a, b = a.loc[com], b.loc[com]
    keep = ~(a.anchor.values | b.anchor.values)
    if not keep.any():
        continue
    hc = a.loc[a["Drug 1"] == "high control", "Raw count"].mean()
    lc = a.loc[a["Drug 1"] == "low control", "Raw count"].mean()
    span = hc - lc
    RD[(f1, f2)] = pd.DataFrame({
        "dif": ((a["Raw count"] - b["Raw count"]) / span).values[keep],
        "vb": ((a.Viability + b.Viability) / 2).values[keep],
        "ri": a.ri.values[keep], "col": a.col.values[keep],
        "iter": a.iter.iloc[0]})
rawc = []
for (f1, f2), g in RD.items():
    pv = g.pivot_table(index="ri", columns="col", values="vb")
    pf = g.pivot_table(index="ri", columns="col", values="dif")
    band = ((pv >= 0.55) & (pv <= 0.95)).astype(float).fillna(0.0)
    b2 = band.shift(periods=-1, axis=1).fillna(0.0)
    mask = (band.values == 1) & (b2.values == 1) & np.isfinite(pf.values)
    d2 = pf.shift(periods=-1, axis=1)
    m = mask & np.isfinite(d2.values)
    if m.any():
        rawc.append((pf.values - d2.values)[m])
rawc = np.concatenate(rawc) if rawc else np.array([])
sd_raw = rawc.std(ddof=1)

# why "vb in band" is a choice, not a truncation: report how many band pairs are clipped
say(f"raw-count adjacent-column contrast pairs in band 0.55-0.95: n={rawc.size}")
say(f"   SD of contrast (truncation-free) = {sd_raw:.5f}; sigma_equiv = {sd_raw/math.sqrt(2):.5f}")
say(f"   Var(d) = {sd_raw**2:.6f}")
say("   (raw counts are never clipped, so this number contains no truncation artefact at all)")

# ---------------------------------------------------------------- E. N2
say("\n" + "=" * 78)
say("E. IS sigma_b ESTIMABLE BY THE AUDITED N2 FORMULA?")
plate_stats = []
for (f1, f2), g in RD.items():
    dd = g.dif.to_numpy()
    plate_stats.append({"sd": float(dd.std(ddof=1)), "mean": float(dd.mean()), "n": len(dd)})
ps = pd.DataFrame(plate_stats)
sd_within = float(ps["sd"].mean())
say(f"mean within-file-pair SD of delta across wells = {sd_within:.5f}   [author 0.055830]")
say(f"author: var_b = sd_within^2/2 - sigma_e^2 = {sd_within**2/2 - 0.04076155120138758**2:+.6f} -> clipped to 0")
say("   sqrt(2)*sigma_e_primary = %.5f, i.e. the two terms are the same quantity up to noise;" % (math.sqrt(2) * 0.04076155120138758))
say("   the plate offset is a CONSTANT inside a file pair, so it cannot enter a variance taken ACROSS wells.")
say(f"correct route: SD across file pairs of the MEAN delta = {ps['mean'].std(ddof=1):.5f}"
    f" -> sigma_b = {ps['mean'].std(ddof=1)/math.sqrt(2):.5f}; mean|offset| = {ps['mean'].abs().mean():.5f}"
    f"  [author mean_abs_plate_offset 0.011578]")

# ---------------------------------------------------------------- F. level mix
say("\n" + "=" * 78)
say("F. LEVEL MIX: the A673 pair, at 0.63 and 0.93, is NOT inside the [0.75,1] window")
sig_lv = {}
for lo, hi, lab in [(0, .25, "[0,.25)"), (.25, .5, "[.25,.5)"), (.5, .75, "[.5,.75)"), (.75, 1.0001, "[.75,1]")]:
    s = C[(C.mean_y >= lo) & (C.mean_y < hi)]
    sig_lv[lab] = sig2(s.d)
    say(f"   sigma_e{lab} = {sig_lv[lab]:.5f}")
s_mix_A = math.sqrt(sig_lv["[.5,.75)"] ** 2 + sig_lv["[.75,1]"] ** 2)
say(f"A673 wells sit one in [.5,.75) (0.631) and one in [.75,1] (0.934):")
say(f"   sqrt(sigma_e(.63)^2 + sigma_e(.93)^2) = {s_mix_A:.5f}  vs author's sqrt(2)*sigma_e_primary = "
    f"{math.sqrt(2)*0.04076155120138758:.5f}")
say(f"BJ wells both in [.75,1] (0.86-0.91): level-matched window is the right window for BJ.")
dA, dB = 0.27747591000179417, -0.03453522862577463

# ---------------------------------------------------------------- G. diff-of-diff
say("\n" + "=" * 78)
say("G. DIFFERENCE OF DIFFERENCES  (does the ORDER DIFFER between contexts?)")
se_dd_author = math.sqrt((math.sqrt(2) * 0.04076155120138758) ** 2 / 2 + (math.sqrt(2) * 0.04076155120138758) ** 2 / 2)
dd = dA - dB
say(f"d_A673 - d_BJ = {dd:.5f}; SE under author's sigma = {se_dd_author:.5f}; t = {dd/se_dd_author:.2f}; "
    f"p = {norm_sf2(dd/se_dd_author):.3g}")
se_dd_mine = math.sqrt((0.059293 ** 2) / 2 + (0.066409 ** 2) / 2)
say(f"                     SE under my direct estimates (adj col / adj row) = {se_dd_mine:.5f}; "
    f"t = {dd/se_dd_mine:.2f}; p = {norm_sf2(dd/se_dd_mine):.3g}")
say("   NB this establishes that the two contexts DIFFER, not that the sign reverses;")
say("   a reversal needs d_BJ < 0, which is the audited criterion.")

# ---------------------------------------------------------------- H. power
say("\n" + "=" * 78)
say("H. POWER / DETECTABILITY ARITHMETIC")
s = 0.04076155120138758
for k in (2, 3, 4, 6, 8, 12):
    se = s * math.sqrt(2 / k)
    say(f"   K={k:2d} SE={se:.5f} min|d|95%={Z95*se:.5f} min|d|80%1sided={(ZA+ZB)*se:.5f}")
say(f"   [author K=2: SE 0.040762, 95% 0.079891, 80% 0.101354]")
say(f"plates for BJ at 80% one-sided: 2*s^2*(ZA+ZB)^2/dB^2 = {2*s**2*(ZA+ZB)**2/dB**2:.3f}  [author 17.226]")
say(f"plates for BJ at 80% TWO-sided (consistent with the 1.96 criterion): "
    f"{2*s**2*(Z95+ZB)**2/dB**2:.3f}")
say(f"plates for A673: {2*s**2*(ZA+ZB)**2/dA**2:.3f}  [author 0.2668]  <- below 1: 'fewer than one plate' is not a "
    f"reportable quantity; the answer is 'already detected with K=2'")
say(f"min|d| needed with K=2 at 80% power one-sided: {(ZA+ZB)*s:.5f}; two-sided: {(Z95+ZB)*s:.5f}")

# ---------------------------------------------------------------- summary
say("\n" + "=" * 78)
say("SUMMARY NUMBERS USED IN REVIEW.md")
say(f"  author sigma_e primary          = 0.040762")
say(f"  author implied SD(contrast)     = {math.sqrt(2)*0.040762:.5f}")
say(f"  my direct SD(contrast) adj col  = 0.059293")
say(f"  my direct SD(contrast) adj row  = 0.066409")
say(f"  my truncation-free SD(contrast) = {sd_raw:.5f}")
say(f"  author t: A673 6.81  BJ -0.85")
say(f"  mine   : A673 {dA/ (0.059293/math.sqrt(2)):.2f}  BJ {dB/(0.066409/math.sqrt(2)):.2f}")

res = {"probe_max_abs_y_diff_vs_author": float(P.y_diff.max()),
       "per_plate_d": D4.round(6).to_dict(orient="records"),
       "sigma_e": {"naive": sig2(N.d), "naive_n": int(len(N)),
                   "corrected_pooled": sig2(C.d), "corrected_n": int(len(C)),
                   "level_matched": sig2(L.d), "level_matched_n": int(len(L)),
                   "level_matched_keep_clipped": sig2(Li.d), "level_matched_keep_clipped_n": int(len(Li)),
                   "by_level": {k: float(v) for k, v in sig_lv.items()}},
       "level_mix_sigma_A673": float(s_mix_A),
       "truncation_free_sd_contrast": float(sd_raw),
       "n2": {"mean_within_pair_sd": sd_within,
              "author_formula_var_b": float(sd_within ** 2 / 2 - 0.04076155120138758 ** 2),
              "correct_sigma_b": float(ps["mean"].std(ddof=1) / math.sqrt(2)),
              "mean_abs_offset": float(ps["mean"].abs().mean())},
       "diff_of_diff": {"value": float(dd), "se_author": float(se_dd_author),
                        "t_author": float(dd / se_dd_author), "se_mine": float(se_dd_mine),
                        "t_mine": float(dd / se_dd_mine)},
       "plates_needed_BJ_one_sided": float(2 * s ** 2 * (ZA + ZB) ** 2 / dB ** 2),
       "plates_needed_BJ_two_sided": float(2 * s ** 2 * (Z95 + ZB) ** 2 / dB ** 2)}
with open(OUT + r"\stage2_audit.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2)
with open(OUT + r"\stage2_log.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(log))
say("\nwrote stage2_audit.json + stage2_log.txt")

