"""E004 v2: paired-readout noise floor and detectability of the E003 order crossing.

Implements PROTOCOL.md plus PROTOCOL_AMENDMENT_001.md (validity correction after
discovering definitional normalisation anchors in the archive). Both the naive
all-well estimate and the corrected level-matched estimate are reported.

Reads only the already-downloaded public PAIR_SCREEN.csv. No new data, no LLM.

Decomposition, given y(f,w) = mu(cond) + b_f + e(f,w):
  N1 within-file same-condition duplicate wells -> sigma_e (well-level noise).
  N2 across-file identical-layout replicate files -> sigma_b (plate/date offset).
A probe contrast a-b measured inside one file cancels b_f exactly, so
  SE(mean d over K files) = sigma_e * sqrt(2/K).
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
EXPECT_SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"
ANCHORS = {"high control", "low control"}
Z95 = 1.959964
Z_POWER80 = 1.6449 + 0.8416  # one-sided alpha 0.05, power 0.80

PROBES = {("BJ", "147", "N22"): "a", ("BJ", "147", "O22"): "b",
          ("BJ", "148", "N22"): "a", ("BJ", "148", "O22"): "b",
          ("A673", "157", "O1"): "a", ("A673", "157", "O2"): "b",
          ("A673", "158", "O1"): "a", ("A673", "158", "O2"): "b"}
EXPECT_PAIR = {"a": ("Axitinib", 0.1, "Dexrazoxane", 0.1),
               "b": ("Axitinib", 0.1, "Lestaurtinib", 0.1)}
E003_D = {"A673": [0.3031358885017420, 0.25181593150184634],
          "BJ": [-0.020518039445069247, -0.04855241780648001]}
KEY = ["Drug 1", "Conc 1 (uM)", "Drug 2", "Conc 2 (uM)"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well", "Plate"):
        df[c] = df[c].astype(str).str.strip()
    df["Iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["clipped"] = (df["y"] == 0.0) | (df["y"] == 1.0)
    return df


def within_file_pairs(df: pd.DataFrame, drop_anchor: bool, drop_clipped: bool) -> pd.DataFrame:
    d = df[~df["anchor"]] if drop_anchor else df
    rows = []
    for fname, g in d.groupby("file", sort=True):
        cell = g["Cell line"].iloc[0]
        for k, sub in g.groupby(KEY, sort=False, dropna=False):
            if len(sub) < 2:
                continue
            sub = sub[~sub["failed_qc"] & sub["y"].notna()]
            if drop_clipped:
                sub = sub[~sub["clipped"]]
            for (_, r1), (_, r2) in itertools.combinations(sub.iterrows(), 2):
                rows.append({"file": fname, "cell": cell, "group_n": len(sub), "w1": str(r1["Well"]), "w2": str(r2["Well"]),
                             "d": float(r1["y"] - r2["y"]),
                             "mean_y": float((r1["y"] + r2["y"]) / 2.0),
                             "combo": (str(k[0]).lower() != "dmso") and (str(k[2]).lower() != "dmso"),
                             "d1": k[0], "c1": k[1], "d2": k[2], "c2": k[3]})
    return pd.DataFrame(rows)


def sigma_from(d: np.ndarray) -> float:
    return float(np.std(d, ddof=1) / math.sqrt(2.0)) if d.size > 2 else float("nan")


def parse_well(well: str) -> tuple[int, int]:
    """'N22' -> (row_index, col_index). A-P rows, 1-24 columns in this archive."""
    w = str(well).strip().upper()
    row = ord(w[0]) - ord("A")
    col = int(w[1:]) - 1
    return row, col


def level_bin(mean_y: np.ndarray):
    return pd.cut(mean_y, [0.0, 0.25, 0.5, 0.75, 1.0001], right=False,
                  labels=["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    digest = sha256(CSV)
    assert digest == EXPECT_SHA, f"input hash mismatch {digest}"
    df = load()

    audit = {"input": {"path": str(CSV), "sha256": digest, "bytes": CSV.stat().st_size},
             "n_rows": int(len(df)), "n_files": int(df["file"].nunique()),
             "n_cells": int(df["Cell line"].nunique()),
             "n_anchor_rows": int(df["anchor"].sum()),
             "n_clipped_rows": int(df["clipped"].sum()),
             "n_failed_qc": int(df["failed_qc"].sum()),
             "rows_per_file_median": float(df.groupby("file").size().median()),
             "wells_per_file_median": float(df.groupby("file")["Well"].nunique().median())}

    # ---- naive (protocol as first written): all wells, all values ----
    naive = within_file_pairs(df, drop_anchor=False, drop_clipped=False)
    exact_frac_naive = float(np.mean(np.abs(naive["d"].to_numpy()) < 1e-9))
    anchor_share = None
    if len(naive):
        anchor_keys = naive[naive["d1"].isin(ANCHORS) | naive["d2"].isin(ANCHORS)]
        anchor_share = float(len(anchor_keys) / len(naive))

    # ---- corrected: anchors and clipped values removed ----
    clean = within_file_pairs(df, drop_anchor=True, drop_clipped=True)
    combo = clean[clean["combo"]]
    dc = clean["d"].to_numpy(dtype=float)
    dcc = combo["d"].to_numpy(dtype=float)

    by_level = []
    clean = clean.assign(level=level_bin(clean["mean_y"].to_numpy()))
    combo = combo.assign(level=level_bin(combo["mean_y"].to_numpy()))
    for lab in ["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"]:
        s = clean[clean["level"] == lab]["d"].to_numpy(dtype=float)
        sc = combo[combo["level"] == lab]["d"].to_numpy(dtype=float)
        by_level.append({"level": lab, "n_pairs_all_treated": int(s.size),
                         "sigma_e_all_treated": sigma_from(s),
                         "n_pairs_double_drug": int(sc.size),
                         "sigma_e_double_drug": sigma_from(sc),
                         "abs_d_median": float(np.median(np.abs(s))) if s.size else None,
                         "abs_d_q90": float(np.quantile(np.abs(s), 0.9)) if s.size else None})

    probe_level = clean[clean["level"] == "[.75,1]"]
    probe_level_combo = combo[combo["level"] == "[.75,1]"]
    sigma_e_primary = sigma_from(probe_level["d"].to_numpy(dtype=float))
    sigma_e_primary_combo = sigma_from(probe_level_combo["d"].to_numpy(dtype=float))
    sigma_e_global = sigma_from(dc)
    sigma_e_naive = sigma_from(naive["d"].to_numpy(dtype=float))

    # did the duplicate pairs sit close together? spatial proximity could deflate sigma_e
    pos = []
    for _, r in probe_level.iterrows():
        try:
            (r1, c1), (r2, c2) = parse_well(r["w1"]), parse_well(r["w2"])
        except Exception:
            continue
        pos.append((abs(c1 - c2), r["d"]))
    pos = pd.DataFrame(pos, columns=["dc", "d"])
    positional = {"n_pairs": int(len(pos))}
    for lab, sub in (("same_column", pos[pos["dc"] == 0]), ("adjacent_column", pos[pos["dc"] == 1]),
                     ("dc_ge_2", pos[pos["dc"] >= 2])):
        positional[lab] = {"n": int(len(sub)), "sigma_e": sigma_from(sub["d"].to_numpy(dtype=float))}
    separated = pos[pos["dc"] >= 2]["d"].to_numpy(dtype=float)
    positional["note"] = ("Replicate wells are mostly 1 column apart; further-separated pairs scatter "
                          "more, so sigma_e is a mildly favourable (small) estimate for a contrast "
                          "measured at distant positions.")

    # ---- N2: across-file identical-layout replicate pairs (anchors/clipped removed) ----
    keep = df[~df["anchor"]]
    sig = {}
    for fname, g in keep.groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Conc 1 (uM)"], g["Drug 2"], g["Conc 2 (uM)"])))
        sig[fname] = {"cell": g["Cell line"].iloc[0],
                      "iteration": int(g["Iteration"].iloc[0]) if pd.notna(g["Iteration"].iloc[0]) else -1,
                      "layout_hash": hashlib.sha1(repr(layout).encode()).hexdigest(), "n_wells": len(g)}
    sig_df = pd.DataFrame.from_dict(sig, orient="index").rename_axis("file").reset_index()
    groups = [(k, sub.reset_index(drop=True))
              for k, sub in sig_df.groupby(["cell", "iteration", "layout_hash", "n_wells"], sort=True)]
    pairs = [(k, sub) for k, sub in groups if len(sub) == 2]
    plate_stats = []
    for _key, g in pairs:
        a = keep[keep["file"] == g["file"].iloc[0]].set_index("Well")
        b = keep[keep["file"] == g["file"].iloc[1]].set_index("Well")
        common = a.index.intersection(b.index)
        if len(common) < 5:
            continue
        aa, bb = a.loc[common], b.loc[common]
        same = ((aa["Drug 1"].to_numpy() == bb["Drug 1"].to_numpy())
                & (aa["Drug 2"].to_numpy() == bb["Drug 2"].to_numpy())
                & (pd.to_numeric(aa["Conc 1 (uM)"]).to_numpy() == pd.to_numeric(bb["Conc 1 (uM)"]).to_numpy())
                & (pd.to_numeric(aa["Conc 2 (uM)"]).to_numpy() == pd.to_numeric(bb["Conc 2 (uM)"]).to_numpy()))
        ok = (same & ~aa["failed_qc"].to_numpy() & ~bb["failed_qc"].to_numpy()
              & ~aa["clipped"].to_numpy() & ~bb["clipped"].to_numpy()
              & aa["y"].notna().to_numpy() & bb["y"].notna().to_numpy())
        if ok.sum() < 5:
            continue
        dd = bb["y"].to_numpy()[ok] - aa["y"].to_numpy()[ok]
        plate_stats.append({"n": int(ok.sum()), "mean": float(dd.mean()), "sd": float(dd.std(ddof=1))})
    ps = pd.DataFrame(plate_stats)
    sd_delta_plate = float(ps["sd"].mean()) if len(ps) else float("nan")
    var_b = sd_delta_plate ** 2 / 2.0 - sigma_e_primary ** 2
    n2 = {"layout_groups": len(groups), "replicate_pairs": len(pairs),
          "pairs_used": int(len(ps)),
          "n_wells_median": int(ps["n"].median()) if len(ps) else 0,
          "mean_abs_plate_offset": float(ps["mean"].abs().mean()) if len(ps) else None,
          "sd_of_within_pair_delta_across_plates": sd_delta_plate,
          "sigma_b_plate_offset": float(math.sqrt(var_b)) if var_b > 0 else 0.0,
          "note": ("sigma_e and sigma_b are reported separately: a within-plate a-vs-b contrast "
                   "cancels the plate offset b_f, so sigma_e is the relevant noise for E003.")}

    # ---- probe reconstruction ----
    probe_rows = []
    for (cell, plate, well), letter in PROBES.items():
        sel = df[(df["Cell line"] == cell) & (df["Plate"] == plate) & (df["Well"] == well)]
        assert len(sel) == 1, f"{cell} {plate} {well} -> {len(sel)} rows"
        r = sel.iloc[0]
        got = (r["Drug 1"], float(r["Conc 1 (uM)"]), r["Drug 2"], float(r["Conc 2 (uM)"]))
        exp = EXPECT_PAIR[letter]
        assert sorted([got[0], got[2]]) == sorted([exp[0], exp[2]])
        assert sorted([got[1], got[3]]) == sorted([exp[1], exp[3]])
        assert int(r["Iteration"]) == 11
        probe_rows.append({"cell": cell, "plate": plate, "well": well, "probe": letter,
                           "y": float(r["y"]), "raw_count": float(r["Raw count"]) if pd.notna(r["Raw count"]) else None,
                           "failed_qc": bool(r["failed_qc"]), "file": r["file"],
                           "pair": f"{got[0]} {got[1]}uM + {got[2]} {got[3]}uM"})

    per_plate = []
    for cell, (p1, p2, wa, wb) in {"A673": ("157", "158", "O1", "O2"),
                                   "BJ": ("147", "148", "N22", "O22")}.items():
        for plate in (p1, p2):
            a = next(p for p in probe_rows if p["cell"] == cell and p["plate"] == plate and p["well"] == wa)
            b = next(p for p in probe_rows if p["cell"] == cell and p["plate"] == plate and p["well"] == wb)
            per_plate.append({"cell": cell, "plate": plate, "d": a["y"] - b["y"],
                              "y_a": a["y"], "y_b": b["y"], "mean_y": (a["y"] + b["y"]) / 2.0,
                              "any_qc": a["failed_qc"] or b["failed_qc"]})

    def evaluate(sigma: float) -> dict:
        out = {}
        for cell in ("A673", "BJ"):
            ds = [p["d"] for p in per_plate if p["cell"] == cell]
            dbar = float(np.mean(ds))
            se = sigma * math.sqrt(2.0 / len(ds))
            t = dbar / se if se > 0 else float("inf")
            out[cell] = {
                "d_per_plate": ds, "dbar": dbar, "se_dbar": se, "t": t,
                "p_two_sided_normal": float(2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))),
                "ci95": [dbar - Z95 * se, dbar + Z95 * se],
                "detectable_at_1p96se": bool(abs(dbar) >= Z95 * se),
                "repeat_sign_consistent": bool(all(x > 0 for x in ds) or all(x < 0 for x in ds)),
                "plates_needed_80pct_power_onesided": (2.0 * sigma ** 2 * Z_POWER80 ** 2 / dbar ** 2) if dbar else None,
                "e003_reported": E003_D[cell],
            }
        crossing = bool(out["A673"]["detectable_at_1p96se"] and out["BJ"]["detectable_at_1p96se"])
        return {"sigma_e_used": sigma, "cells": out,
                "crossing_supported": crossing,
                "decision": "h007_crossing_supported" if crossing else "h007_crossing_not_established"}

    tests_naive = evaluate(sigma_e_naive)
    tests_primary = evaluate(sigma_e_primary)
    tests_combo = evaluate(sigma_e_primary_combo)
    tests_global = evaluate(sigma_e_global)

    # can the probe's OWN two plates bound sigma? (1 df only; shown to be uninformative)
    internal = {}
    for cell in ("A673", "BJ"):
        ds = tests_primary["cells"][cell]["d_per_plate"]
        gap = abs(ds[0] - ds[1])
        sd_gap = 2.0 * sigma_e_primary            # Var(d1-d2) = 4 sigma^2
        p_ge = math.erfc(gap / (sd_gap * math.sqrt(2.0)))   # two-sided normal tail
        internal[cell] = {
            "plate_gap": gap,
            "implied_sigma_point_estimate": gap / 2.0,
            "implied_sigma_95_interval_1df": [gap / math.sqrt(4 * 3.841), gap / math.sqrt(4 * 0.00098)],
            "p_gap_at_least_observed_under_primary_sigma": p_ge,
            "note": ("One degree of freedom: the implied interval spans an order of magnitude, so the probe's "
                     "internal agreement cannot revise sigma; under the primary sigma the observed gap is an "
                     "ordinary draw.")}

    # empirical, parameter-free placement of the probe contrasts in the duplicate-|d| distribution
    ref_abs = np.abs(probe_level["d"].to_numpy(dtype=float))
    ref_abs_combo = np.abs(probe_level_combo["d"].to_numpy(dtype=float))
    empirical = {}
    for cell in ("A673", "BJ"):
        dbar = tests_primary["cells"][cell]["dbar"]
        empirical[cell] = {
            "abs_dbar": abs(dbar),
            "pctile_in_level_matched_duplicate_abs_d": float(np.searchsorted(np.sort(ref_abs), abs(dbar), side="right") / ref_abs.size),
            "pctile_in_level_matched_double_drug_duplicate_abs_d": float(np.searchsorted(np.sort(ref_abs_combo), abs(dbar), side="right") / ref_abs_combo.size),
            "P_duplicate_abs_d_at_least_this": float((ref_abs >= abs(dbar)).mean()),
        }

    capability = [{"K_plates": k, "se_dbar": sigma_e_primary * math.sqrt(2.0 / k),
                   "min_detectable_abs_d_95pct": Z95 * sigma_e_primary * math.sqrt(2.0 / k),
                   "min_detectable_abs_d_80pct_power": Z_POWER80 * sigma_e_primary * math.sqrt(2.0 / k)}
                  for k in (2, 3, 4, 6, 8, 12)]

    # ---- robustness: cell-specific noise at the probe readout level ----
    per_cell = []
    for cell, sub in probe_level.groupby("cell"):
        d = sub["d"].to_numpy(dtype=float)
        if d.size >= 30:
            per_cell.append({"cell": cell, "n_pairs": int(d.size), "sigma_e": sigma_from(d)})
    per_cell.sort(key=lambda r: r["sigma_e"])
    bj_need = abs(tests_primary["cells"]["BJ"]["dbar"]) / Z95
    cells_quiet_enough = [r["cell"] for r in per_cell if r["sigma_e"] <= bj_need]
    robustness = {
        "sigma_needed_for_bj_significance": bj_need,
        "per_cell_level_matched_sigma_e": per_cell,
        "n_cells_present": len(per_cell),
        "cells_quiet_enough_to_make_bj_significant": cells_quiet_enough,
        "cells_quiet_enough_count": len(cells_quiet_enough),
        "interpretation": ("For the BJ contrast to reach the pre-registered 95% criterion, the well-level "
                           "sigma would have to be at most this value. Compare with the per-cell estimates."),
    }

    # ideal-noise lower bound on the number of independent pair comparisons needed to
    # detect an excess reversal rate over 0.5 (signed-rank style aggregate, no measurement noise)
    agg = []
    for excess in (0.1, 0.2, 0.3):
        for power_z in (Z_POWER80,):
            m = (power_z / (2 * excess)) ** 2
            agg.append({"true_reversal_excess_over_half": excess, "m_pairs_needed_ideal_noise": float(m),
                        "note": "ideal-noise lower bound; per-pair measurement noise requires more pairs"})

    result = {
        "kind": "readout_noise_calibration_and_detectability_diagnostic",
        "audit": audit,
        "N1_naive_all_wells": {"n_pairs": int(len(naive)), "sigma_e": sigma_e_naive,
                               "exact_equal_fraction": exact_frac_naive,
                               "share_of_pairs_involving_normalisation_anchors": anchor_share,
                               "delta_abs_median": float(np.median(np.abs(naive["d"].to_numpy()))),
                               "delta_mad_sd": float(1.4826 * np.median(np.abs(naive["d"].to_numpy() - np.median(naive["d"].to_numpy())))),
                               "validity": "INVALID as a noise estimate: definitional y=1.0/0.0 anchor wells dominate"},
        "N1_corrected": {"n_pairs": int(len(clean)), "n_files": int(clean["file"].nunique()),
                         "n_conditions": int(clean[["file", "d1", "c1", "d2", "c2"]].drop_duplicates().shape[0]),
                         "n_double_drug_pairs": int(len(combo)),
                         "sigma_e_pooled_all_treated": sigma_e_global,
                         "sigma_e_pooled_double_drug": sigma_from(dcc),
                         "delta_abs_median": float(np.median(np.abs(dc))),
                         "delta_abs_q90": float(np.quantile(np.abs(dc), 0.90)),
                         "delta_abs_q95": float(np.quantile(np.abs(dc), 0.95)),
                         "delta_abs_q99": float(np.quantile(np.abs(dc), 0.99)),
                         "by_level": by_level,
                         "primary_definition": "level-matched to probe wells: mean_y in [0.75,1]",
                         "sigma_e_primary_level_matched": sigma_e_primary,
                         "sigma_e_primary_level_matched_double_drug": sigma_e_primary_combo,
                         "n_pairs_primary": int(len(probe_level)),
                         "n_cells_primary": int(probe_level["cell"].nunique())},
        "N2_across_file_replicates": n2,
        "probe_wells": probe_rows,
        "per_plate_differences": per_plate,
        "tests": {"primary_level_matched": tests_primary,
                  "sensitivity_double_drug_only": tests_combo,
                  "sensitivity_pooled_all_levels": tests_global,
                  "invalid_naive_estimate": tests_naive},
        "empirical_placement_noise_model_free": empirical,
        "decision": tests_primary["decision"],
        "capability_bound": capability,
        "robustness": robustness, "positional_sensitivity": positional, "probe_internal_consistency": internal,
        "aggregate_ordinal_sample_size": agg,
        "limits": [
            "Within-plate technical duplicates only; not independent cultures; cross-date variation excluded, so sigma_e is a lower bound on total technical error.",
            "Author QC flagged duplicate pairs differing by >0.5 viability; those wells are excluded from the estimate.",
            "No target-engagement or genetic-perturbation reference; no mechanism, death-rate or clinical-safety conclusion.",
            "Metadata-to-chemical-identity mapping unauthenticated; same nominal dose is not shared biological action.",
            "Not a policy comparison: no acquisition strategy is evaluated here.",
            "The 4 probe wells are a fixed, author-selected panel; no randomisation over plates.",
        ]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r4/PROTOCOL.md",
                "research/2026-10-27-agent-cell-identifiability-r4/PROTOCOL_AMENDMENT_001.md",
                "research/2026-10-27-agent-cell-identifiability-r4/e004_noise_calibration.py",
                "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"):
        p = ROOT / rel
        if p.exists():
            result.setdefault("files", {})[rel] = sha256(p)

    (OUT / "E004_RESULTS.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"rows={audit['n_rows']} files={audit['n_files']} cells={audit['n_cells']} anchors={audit['n_anchor_rows']}")
    print(f"NAIVE  n={len(naive)} sigma_e={sigma_e_naive:.4f} exact={exact_frac_naive:.3f} anchor_share={anchor_share}  [INVALID]")
    print(f"CLEAN  n={len(clean)} sigma_e_pooled={sigma_e_global:.4f} | double-drug n={len(combo)} sigma_e={sigma_from(dcc):.4f}")
    print(f"PRIMARY level-matched n={len(probe_level)} sigma_e={sigma_e_primary:.4f} | double-drug n={len(probe_level_combo)} sigma_e={sigma_e_primary_combo:.4f}")
    print(f"N2 replicate pairs={n2['replicate_pairs']} used={n2['pairs_used']} sd_plate_delta={sd_delta_plate:.4f} sigma_b={n2['sigma_b_plate_offset']:.4f}")
    for name, t in (("PRIMARY", tests_primary), ("COMBO-ONLY", tests_combo), ("POOLED", tests_global), ("NAIVE-INVALID", tests_naive)):
        a, b = t["cells"]["A673"], t["cells"]["BJ"]
        print(f"[{name}] sigma={t['sigma_e_used']:.4f} | A673 d={a['dbar']:.4f} t={a['t']:.2f} CI={['%.3f'%x for x in a['ci95']]} | BJ d={b['dbar']:.4f} t={b['t']:.2f} p={b['p_two_sided_normal']:.3f} CI={['%.3f'%x for x in b['ci95']]} -> {t['decision']}")
    for cell in ("A673", "BJ"):
        e = empirical[cell]
        print(f"empirical {cell}: |d|={e['abs_dbar']:.4f} pctile(level-matched dup)={e['pctile_in_level_matched_duplicate_abs_d']:.3f} P(dup>=this)={e['P_duplicate_abs_d_at_least_this']:.3f}")
    for c in capability:
        print(f"  K={c['K_plates']:2d} SE={c['se_dbar']:.4f} min|d|95%={c['min_detectable_abs_d_95pct']:.4f} min|d|80%={c['min_detectable_abs_d_80pct_power']:.4f}")
    print("DECISION:", tests_primary["decision"])


if __name__ == "__main__":
    main()
