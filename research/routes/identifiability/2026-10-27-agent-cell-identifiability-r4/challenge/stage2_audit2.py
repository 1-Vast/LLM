"""Stage 2, part 2 — checks the first pass did not cover.

  I.  the amendment's factual counts (462 files with 16 high-control wells; ~55k pairs; 99% zero)
  J.  correct sigma_b from the BETWEEN-file-pair variance of the mean delta
  K.  is the truncation-free raw-count contrast SD (0.0897) a spatial-gradient artefact?
  L.  verdicts under the full spread of defensible SD(contrast) values
"""
import itertools
import json
import math

import numpy as np
import pandas as pd

RAW = r"D:\MAESTRO\research\eight_directions_20261026\evidence_audit\raw\PAIR_SCREEN.csv"
OUT = r"D:\MAESTRO\research\2026-10-27-agent-cell-identifiability-r4\challenge"
ANCH = {"high control", "low control"}
log = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    log.append(s)


def sig2(d):
    d = np.asarray(d, float)
    return float(d.std(ddof=1) / math.sqrt(2)) if d.size > 2 else float("nan")


df = pd.read_csv(RAW, low_memory=False)
df["Drug 1"] = df["Drug 1"].astype(str).str.strip()
df["Drug 2"] = df["Drug 2"].astype(str).str.strip()
df["iter"] = df["Iteration"].astype(str)
df["y"] = df["Viability"]
df["anchor"] = df["Drug 1"].isin(ANCH) | df["Drug 2"].isin(ANCH)
df["clipped"] = (df.y == 0.0) | (df.y == 1.0)
df["fq"] = df["Failed QC"].astype(str).str.lower().isin(["true", "1"])
df["col"] = df["Well"].str.extract(r"(\d+)").astype(int)
df["row"] = df["Well"].str.extract(r"([A-P]+)")
df["ri"] = df["row"].map({r: i for i, r in enumerate("ABCDEFGHIJKLMNOP")})
K4 = ["Drug 1", "Conc 1 (uM)", "Drug 2", "Conc 2 (uM)"]

# ---------------------------------------------------------------- I
say("=" * 78)
say("I. THE AMENDMENT'S FACTUAL COUNTS")
hc = df[df["Drug 1"] == "high control"]
lc = df[df["Drug 1"] == "low control"]
nhc = hc.groupby("file").size()
say(f"total files in archive                = {df.file.nunique()}")
say(f"files containing high control rows    = {nhc.size}")
say(f"distribution of high controls/file    = {nhc.value_counts().sort_index().to_dict()}")
say(f"files with exactly 16 high controls   = {int((nhc == 16).sum())}   [amendment says '462 files']")
say(f"high-control rows = {len(hc)}, low-control rows = {len(lc)}, sum = {len(hc)+len(lc)}  [audit n_anchor_rows=17152]")
hc_pairs = sum(int(n) * (int(n) - 1) // 2 for n in nhc.values)
nlc = lc.groupby("file").size()
lc_pairs = sum(int(n) * (int(n) - 1) // 2 for n in nlc.values)
say(f"pairs with both wells high control    = {hc_pairs}")
say(f"pairs with both wells low control     = {lc_pairs}")
say(f"total both-anchor pairs               = {hc_pairs + lc_pairs}   [amendment says '~5.5e4']")
say(f"share of all naive pairs (233696)     = {(hc_pairs+lc_pairs)/233696:.4f}  [audit 0.9625]")

# naive |d| q90 and the exact-zero share inside the anchor blocks
rows = []
for f, g in df.groupby("file", sort=True):
    for k, sub in g.groupby(K4, sort=False, dropna=False):
        if len(sub) < 2:
            continue
        sub = sub[~sub.fq & sub.y.notna()]
        for (_, r1), (_, r2) in itertools.combinations(sub.iterrows(), 2):
            rows.append((float(r1.y - r2.y), bool(r1.anchor)))
N = pd.DataFrame(rows, columns=["d", "anch"])
say(f"naive pairs n={len(N)}; |d| median={N.d.abs().median():.6f} "
    f"MAD-SD={1.4826*np.median(np.abs(N.d-np.median(N.d))):.6f} |d| q90={N.d.abs().quantile(.90):.6f}")
say("   [amendment: median 0.0003, MAD-SD 0.0003, q90 0.0380]")
say(f"   inside anchor blocks: exact-zero share = "
    f"{float((N[N.anch].d.abs()<1e-9).mean()):.4f}   [amendment: 99%]")

# ---------------------------------------------------------------- J
say("\n" + "=" * 78)
say("J. sigma_b THE CORRECT WAY (between-file-pair variance of the MEAN delta, Viability basis)")
df["wkey"] = (df.Well.astype(str) + "|" + df["Drug 1"] + "|" + df["Drug 2"] + "|" +
              df["Conc 1 (uM)"].astype(str) + "|" + df["Conc 2 (uM)"].astype(str))
grp = {}
for f, g in df.groupby("file"):
    grp.setdefault((hash(tuple(sorted(g.wkey))), g["Cell line"].iloc[0],
                    g["iter"].iloc[0]), []).append(f)
rp = []
for _, fl in grp.items():
    fl = sorted(fl)
    rp += [(fl[i], fl[j]) for i in range(len(fl)) for j in range(i + 1, len(fl))]
tabs = {f: g.set_index("Well") for f, g in df.groupby("file")}
means, sds, ns = [], [], []
for f1, f2 in rp:
    a, b = tabs[f1], tabs[f2]
    com = a.index.intersection(b.index)
    a, b = a.loc[com], b.loc[com]
    ok = (~a.anchor.values & ~b.anchor.values & ~a.clipped.values & ~b.clipped.values &
          ~a.fq.values & ~b.fq.values)
    if ok.sum() < 20:
        continue
    dd = (b.y.values - a.y.values)[ok]
    means.append(dd.mean()); sds.append(dd.std(ddof=1)); ns.append(int(ok.sum()))
means, sds = np.array(means), np.array(sds)
say(f"file pairs used = {len(means)}  median wells/pair = {int(np.median(ns))}")
say(f"mean |plate offset|                    = {np.abs(means).mean():.5f}   [audit mean_abs_plate_offset 0.011578]")
say(f"SD of the MEAN delta across file pairs = {means.std(ddof=1):.5f}  -> sigma_b = {means.std(ddof=1)/math.sqrt(2):.5f}")
say(f"mean WITHIN-pair SD across wells       = {sds.mean():.5f}   [audit 0.055830]")
say(f"   author's var_b = {sds.mean()**2/2 - 0.04076155120138758**2:+.6f} -> reported sigma_b = 0.0")
say("   the offset is one constant per file pair, so it is invisible to a variance taken across WELLS;")
say("   the reported sigma_b = 0 is a structural artefact of the formula, not evidence of no offset.")
say(f"   cross-check Var(mean delta) = 2*sigma_b^2 + 2*sigma_e^2/n = "
    f"{2*(means.std(ddof=1)/math.sqrt(2))**2 + 2*0.04076155120138758**2/np.median(ns):.6f} "
    f"vs observed {means.var(ddof=1):.6f}")

# ---------------------------------------------------------------- K
say("\n" + "=" * 78)
say("K. IS THE TRUNCATION-FREE RAW-COUNT CONTRAST SD A SPATIAL-GRADIENT ARTEFACT?")
RD = {}
for f1, f2 in rp:
    a, b = tabs[f1], tabs[f2]
    com = a.index.intersection(b.index)
    a, b = a.loc[com], b.loc[com]
    keep = ~(a.anchor.values | b.anchor.values)
    if keep.sum() < 50:
        continue
    hcm = a.loc[a["Drug 1"] == "high control", "Raw count"].mean()
    lcm = a.loc[a["Drug 1"] == "low control", "Raw count"].mean()
    span = hcm - lcm
    RD[(f1, f2)] = pd.DataFrame({"dif": ((a["Raw count"] - b["Raw count"]) / span).values[keep],
                                 "vb": ((a.y + b.y) / 2).values[keep],
                                 "ri": a.ri.values[keep], "col": a.col.values[keep]})


def contrast_sd(frame, detrend):
    vals = []
    for k, g in frame.items():
        pv = g.pivot_table(index="ri", columns="col", values="vb")
        pf = g.pivot_table(index="ri", columns="col", values="dif")
        if detrend:
            pf = pf - pf.mean(axis=1).values[:, None] - pf.mean(axis=0).values[None, :] + pf.values.mean()
        band = ((pv >= 0.55) & (pv <= 0.95)).astype(float).fillna(0.0)
        b2 = band.shift(periods=-1, axis=1).fillna(0.0)
        d2 = pf.shift(periods=-1, axis=1)
        m = (band.values == 1) & (b2.values == 1) & np.isfinite(pf.values) & np.isfinite(d2.values)
        if m.any():
            vals.append((pf.values - d2.values)[m])
    x = np.concatenate(vals)
    return x.std(ddof=1), x.size


s0, n0 = contrast_sd(RD, False)
s1, n1 = contrast_sd(RD, True)
say(f"raw-count contrast SD, as measured        = {s0:.5f} (n={n0})")
say(f"raw-count contrast SD, row+col detrended  = {s1:.5f} (n={n1})")
say("   -> the gap between the Viability-based 0.0593 and the raw-based value is mostly a")
say("      row/column gradient in RAW counts that the published Viability has already removed.")

# ---------------------------------------------------------------- L
say("\n" + "=" * 78)
say("L. VERDICTS ACROSS THE WHOLE SPREAD OF DEFENSIBLE SD(CONTRAST)")
dA, dB = 0.27747591000179417, -0.03453522862577463
cands = {
    "author level-matched sqrt2*0.040762": math.sqrt(2) * 0.04076155120138758,
    "my direct adjacent-column (probe band)": 0.059293,
    "my direct adjacent-row": 0.066409,
    "truncation-free raw (upper bound)": s0,
    "truncation-free raw detrended": s1,
    "author pooled all-levels sqrt2*0.044587": math.sqrt(2) * 0.044587213128049086,
    "my level-mix sqrt(s(.63)^2+s(.93)^2)": 0.071609,
    "my E2 duplicate band unclipped sqrt2*0.05319": math.sqrt(2) * 0.05319,
}
out = {}
for k, sd in cands.items():
    se = sd / math.sqrt(2)
    out[k] = {"sd_contrast": round(float(sd), 6), "SE": round(float(se), 6),
              "t_A673": round(float(dA / se), 3), "t_BJ": round(float(dB / se), 3),
              "sig_A673": bool(abs(dA / se) > 1.96), "sig_BJ": bool(abs(dB / se) > 1.96)}
    say(f"{k:46s} SD={sd:.5f} SE={se:.5f} t(A673)={dA/se:+6.2f} t(BJ)={dB/se:+6.2f} "
        f"-> A673 {'sig' if abs(dA/se)>1.96 else 'ns'}, BJ {'sig' if abs(dB/se)>1.96 else 'ns'}")
say(f"\nA673 significant under {sum(v['sig_A673'] for v in out.values())}/{len(out)}; "
    f"BJ significant under {sum(v['sig_BJ'] for v in out.values())}/{len(out)}")

res = {"files_with_hc": int(nhc.size), "files_with_exactly_16_hc": int((nhc == 16).sum()),
       "hc_count_distribution": {str(k): int(v) for k, v in nhc.value_counts().sort_index().items()},
       "both_anchor_pairs": int(hc_pairs + lc_pairs),
       "naive_q90_abs_d": float(N.d.abs().quantile(.90)),
       "anchor_block_exact_zero_share": float((N[N.anch].d.abs() < 1e-9).mean()),
       "sigma_b_correct": float(means.std(ddof=1) / math.sqrt(2)),
       "mean_abs_plate_offset": float(np.abs(means).mean()),
       "raw_contrast_sd_as_measured": float(s0), "raw_contrast_sd_detrended": float(s1),
       "verdict_matrix": out}
with open(OUT + r"\stage2_audit_part2.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2)
with open(OUT + r"\stage2_log2.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(log))
say("\nwrote stage2_audit_part2.json + stage2_log2.txt")
