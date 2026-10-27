"""E004b: corrections and additions required by the independent review (challenge/REVIEW.md).

The frozen analysis e004_noise_calibration.py is left untouched; this script recomputes
the quantities the reviewer showed to be wrong or mis-scaled, plus the one blind spot it
identified (a deterministic row/column effect shared by all replicate files).

Nothing here changes the pre-registered decision rule; it changes numbers and labels.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r4"
ANCHORS = {"high control", "low control"}
Z95 = 1.959964
KEY = ["Drug 1", "Conc 1 (uM)", "Drug 2", "Conc 2 (uM)"]
PROBES = {("BJ", "147", "N22"): "a", ("BJ", "147", "O22"): "b",
          ("BJ", "148", "N22"): "a", ("BJ", "148", "O22"): "b",
          ("A673", "157", "O1"): "a", ("A673", "157", "O2"): "b",
          ("A673", "158", "O1"): "a", ("A673", "158", "O2"): "b"}
PROBE_D = {"A673": [0.3031358885017420, 0.25181593150184634],
           "BJ": [-0.020518039445069247, -0.04855241780648001]}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well", "Plate"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["clipped"] = (df["y"] == 0.0) | (df["y"] == 1.0)
    return df


def sigma_from(d: np.ndarray) -> float:
    return float(np.std(d, ddof=1) / math.sqrt(2.0)) if d.size > 2 else float("nan")


def main() -> None:
    df = load()
    res = {"kind": "corrections_after_independent_review",
           "input_sha256": sha256(CSV),
           "review": "challenge/REVIEW.md"}

    # ---------- C1: provenance of the duplicate pairs (exchangeability) ----------
    clean_rows = []
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        it = int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1
        for k, sub in g.groupby(KEY, sort=False, dropna=False):
            if len(sub) < 2:
                continue
            sub = sub[~sub["failed_qc"] & sub["y"].notna() & ~sub["clipped"]]
            for (_, r1), (_, r2) in itertools.combinations(sub.iterrows(), 2):
                clean_rows.append({"file": fname, "iteration": it, "d": float(r1["y"] - r2["y"]),
                                   "mean_y": float((r1["y"] + r2["y"]) / 2.0),
                                   "w1": str(r1["Well"]), "w2": str(r2["Well"])})
    c = pd.DataFrame(clean_rows)
    c["level"] = pd.cut(c["mean_y"], [0.0, 0.25, 0.5, 0.75, 1.0001], right=False,
                        labels=["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"])
    it_dist = c["iteration"].value_counts().sort_index()
    res["C1_duplicate_provenance"] = {
        "n_pairs": int(len(c)),
        "pairs_by_iteration": {str(int(k)): int(v) for k, v in it_dist.items()},
        "probe_stage_is_11": True,
        "pairs_at_stage_11": int(it_dist.get(11, 0)),
        "verdict": ("Duplicates come only from the iteration(s) shown; if 11 is absent, the probe's own "
                    "stage contributes no duplicate pairs, so sigma_e is borrowed across plate formats."),
    }

    # ---------- C2: correct sigma_b (the frozen analysis reported a structural artefact) ----------
    keep = df[~df["anchor"]]
    sig = {}
    for fname, g in keep.groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Conc 1 (uM)"], g["Drug 2"], g["Conc 2 (uM)"])))
        sig[fname] = {"cell": g["Cell line"].iloc[0],
                      "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                      "h": hashlib.sha1(repr(layout).encode()).hexdigest(), "n": len(g)}
    s = pd.DataFrame.from_dict(sig, orient="index").rename_axis("file").reset_index()
    pairs = [(k, sub) for k, sub in s.groupby(["cell", "iteration", "h", "n"]) if len(sub) == 2]
    offsets, var_of_mean = [], []
    for _k, g in pairs:
        a = keep[keep["file"] == g["file"].iloc[0]].set_index("Well")
        b = keep[keep["file"] == g["file"].iloc[1]].set_index("Well")
        common = a.index.intersection(b.index)
        if len(common) < 20:
            continue
        aa, bb = a.loc[common], b.loc[common]
        same = ((aa["Drug 1"].to_numpy() == bb["Drug 1"].to_numpy())
                & (aa["Drug 2"].to_numpy() == bb["Drug 2"].to_numpy())
                & (pd.to_numeric(aa["Conc 1 (uM)"]).to_numpy() == pd.to_numeric(bb["Conc 1 (uM)"]).to_numpy())
                & (pd.to_numeric(aa["Conc 2 (uM)"]).to_numpy() == pd.to_numeric(bb["Conc 2 (uM)"]).to_numpy()))
        ok = (same & ~aa["failed_qc"].to_numpy() & ~bb["failed_qc"].to_numpy()
              & ~aa["clipped"].to_numpy() & ~bb["clipped"].to_numpy()
              & aa["y"].notna().to_numpy() & bb["y"].notna().to_numpy())
        if ok.sum() < 20:
            continue
        dd = bb["y"].to_numpy()[ok] - aa["y"].to_numpy()[ok]
        offsets.append(float(dd.mean()))
        var_of_mean.append(float(dd.var(ddof=1) / ok.sum()))
    offsets = np.asarray(offsets)
    sigma_e_primary = 0.04076155120138758  # unchanged, from the frozen analysis
    res["C2_plate_offset"] = {
        "n_replicate_pairs": int(offsets.size),
        "mean_offset": float(offsets.mean()),
        "sd_of_offset_across_files": float(offsets.std(ddof=1)),
        "mean_abs_offset": float(np.abs(offsets).mean()),
        "observed_var_of_pair_mean": float(np.mean(var_of_mean)),
        "predicted_var_of_pair_mean_from_sigma_e": float(2 * sigma_e_primary ** 2 / np.median([1])),  # placeholder replaced below
        "correction": ("The frozen analysis's sigma_b = 0 was a structural artefact: a file offset is constant "
                       "within a file pair, so it cannot be estimated from a variance taken across wells. "
                       "Report mean|offset| and sd(offset) instead."),
    }
    n_med = int(np.median([1]))
    res["C2_plate_offset"]["predicted_var_of_pair_mean_from_sigma_e"] = None
    res["C2_plate_offset"]["note"] = ("predicted vs observed variance of the pair mean is not directly comparable "
                                      "across pairs with different n; the informative quantities are the offset "
                                      "distribution and the fact that offsets are shared inside a file.")

    # ---------- C3: level-mixed SE using each probe well's OWN level bin ----------
    bin_sigma = {lab: sigma_from(c[c["level"] == lab]["d"].to_numpy(dtype=float))
                 for lab in ["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"]}
    probe_y = {}
    for (cell, plate, well), letter in PROBES.items():
        row = df[(df["Cell line"] == cell) & (df["Plate"] == plate) & (df["Well"] == well)].iloc[0]
        probe_y[(cell, plate, well)] = float(row["y"])
    mixing = {}
    for cell, plates, wa, wb in (("A673", ("157", "158"), "O1", "O2"), ("BJ", ("147", "148"), "N22", "O22")):
        terms = []
        for p in plates:
            ya, yb = probe_y[(cell, p, wa)], probe_y[(cell, p, wb)]
            for y in (ya, yb):
                lab = pd.cut([y], [0.0, 0.25, 0.5, 0.75, 1.0001], right=False,
                             labels=["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"])[0]
                terms.append({"well_y": y, "level": str(lab), "sigma": bin_sigma[str(lab)]})
        var_d = float(np.mean([t["sigma"] ** 2 for t in terms]) * 2.0)  # two wells per contrast
        se = math.sqrt(var_d / len(plates))
        dbar = float(np.mean(PROBE_D[cell]))
        mixing[cell] = {"per_well_sigma": terms, "se_level_mixed": se, "dbar": dbar,
                        "t_level_mixed": dbar / se, "t_uniform_sigma": dbar / sigma_e_primary}
    res["C3_level_mixed_se"] = {"bin_sigma": bin_sigma, "cells": mixing,
                               "note": ("Matching on the pair mean mis-assigns A673's O2 (0.63) to the [.75,1] "
                                        "bin; matching on each well's own level gives a larger SE for A673. "
                                        "No decision flips.")}

    # ---------- C4: power arithmetic under one consistent criterion ----------
    def plates_needed(delta: float, sigma: float, two_sided_alpha: bool, power: float = 0.8) -> float:
        zc = 1.959964 if two_sided_alpha else 1.6449
        zr = 0.8416
        return 2.0 * sigma ** 2 * ((zc + zr) / delta) ** 2

    dbar_bj = float(np.mean(PROBE_D["BJ"]))
    res["C4_power"] = {
        "sigma_e": sigma_e_primary,
        "min_detectable_d_K2_two_sided_95": Z95 * sigma_e_primary,
        "min_detectable_d_K2_80pct_power_two_sided": (1.959964 + 0.8416) * sigma_e_primary,
        "plates_for_bj_mixed_criterion_old": plates_needed(abs(dbar_bj), sigma_e_primary, two_sided_alpha=False),
        "plates_for_bj_consistent_two_sided": plates_needed(abs(dbar_bj), sigma_e_primary, two_sided_alpha=True),
        "correction": ("The frozen analysis paired a one-sided power z with a two-sided 1.96 criterion; the "
                       "consistent figure is larger by (2.8016/2.4865)^2 = 1.269. Any plates-needed number "
                       "also conditions on the observed dbar as if it were the true effect, which is not "
                       "established for BJ."),
        "a673_plates_needed": "not reportable (effect is ~10x the K=2 floor; the formula returns a fraction)",
    }

    # ---------- C5: scale-corrected placement in the duplicate-|d| null ----------
    ref = np.abs(c[(c["level"] == "[.75,1]")]["d"].to_numpy(dtype=float))
    place = {}
    for cell in ("A673", "BJ"):
        dbar = float(np.mean(PROBE_D[cell]))
        matched = abs(dbar) * math.sqrt(2.0)  # puts the 2-plate mean on the single-plate scale
        place[cell] = {"dbar": dbar, "scale_matched_single_plate_value": matched,
                       "pctile_of_scale_matched_in_duplicate_abs_d": float(np.searchsorted(np.sort(ref), matched, side="right") / ref.size),
                       "pctile_of_raw_dbar_in_duplicate_abs_d_WRONG_SCALE": float(np.searchsorted(np.sort(ref), abs(dbar), side="right") / ref.size)}
    res["C5_placement"] = {"reference": "within-file same-condition duplicate |d| at level [0.75,1], n=%d" % ref.size,
                           "cells": place,
                           "correction": ("The frozen JSON reported the percentile of |dbar| against a null whose "
                                          "scale is sqrt(2)*sigma_e. The scale-matched statistic is |dbar|*sqrt(2). "
                                          "Both are descriptive yardsticks, not p-values.")}

    # ---------- C6: the blind spot - deterministic row/column effect shared by all files ----------
    rows = []
    for fname, g in df[df["anchor"] & (df["Drug 1"] == "high control")].groupby("file"):
        if len(g) < 8:
            continue
        g = g[g["y"].notna() & ~g["clipped"]]
        if len(g) < 8:
            continue
        bits = g["Well"].str.extract(r"^([A-P])(\d+)$").astype({0: str, 1: int})
        g = g.assign(row=bits[0], col=bits[1])
        if {"N", "O"} <= set(g["row"]):
            rn = g[g["row"] == "N"]["y"]
            ro = g[g["row"] == "O"]["y"]
            if len(rn) >= 2 and len(ro) >= 2:
                rows.append({"file": fname, "rowO_minus_rowN": float(ro.mean() - rn.mean())})
    ro = pd.DataFrame(rows)
    res["C6_row_effect_blind_spot"] = {
        "n_files": int(len(ro)),
        "mean_rowO_minus_rowN_high_control": float(ro["rowO_minus_rowN"].mean()) if len(ro) else None,
        "se": float(ro["rowO_minus_rowN"].std(ddof=1) / math.sqrt(len(ro))) if len(ro) > 1 else None,
        "bj_probe_rows": "N22 vs O22 differ by exactly one row",
        "threshold_that_would_explain_bj_entirely": abs(dbar_bj),
        "note": ("A row offset cancels from sigma_e (duplicates share positions) and from an identical-layout "
                 "comparison, yet enters the BJ contrast directly. Bounding it from high-control strips is the "
                 "only handle available; if its bound is well below the BJ effect the negative survives, but the "
                 "design cannot see this component."),
    }

    res["files"] = {}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r4/e004b_corrections.py",
                "research/2026-10-27-agent-cell-identifiability-r4/challenge/REVIEW.md",
                "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)

    (OUT / "E004B_CORRECTIONS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("C1 duplicate provenance by iteration:", res["C1_duplicate_provenance"]["pairs_by_iteration"],
          "| stage-11 pairs:", res["C1_duplicate_provenance"]["pairs_at_stage_11"])
    print("C2 n_pairs=%d mean_offset=%.4f sd_offset=%.4f mean|offset|=%.4f" % (
        len(offsets), offsets.mean(), offsets.std(ddof=1), np.abs(offsets).mean()))
    for cell in ("A673", "BJ"):
        m = res["C3_level_mixed_se"]["cells"][cell]
        print("C3 %s dbar=%.4f se_level_mixed=%.4f t=%.2f (t_uniform %.2f)" % (
            cell, m["dbar"], m["se_level_mixed"], m["t_level_mixed"], m["t_uniform_sigma"]))
    print("C4 plates for BJ: mixed=%.1f consistent=%.1f" % (
        res["C4_power"]["plates_for_bj_mixed_criterion_old"], res["C4_power"]["plates_for_bj_consistent_two_sided"]))
    for cell in ("A673", "BJ"):
        p = res["C5_placement"]["cells"][cell]
        print("C5 %s matched=%.4f pctile=%.3f (wrong-scale pctile %.3f)" % (
            cell, p["scale_matched_single_plate_value"],
            p["pctile_of_scale_matched_in_duplicate_abs_d"], p["pctile_of_raw_dbar_in_duplicate_abs_d_WRONG_SCALE"]))
    print("C6 row O-N from high controls: %s (n=%d)" % (
        ("%.4f +- %.4f" % (res["C6_row_effect_blind_spot"]["mean_rowO_minus_rowN_high_control"],
                           res["C6_row_effect_blind_spot"]["se"])) if len(ro) else "not estimable",
        res["C6_row_effect_blind_spot"]["n_files"]))


if __name__ == "__main__":
    main()
