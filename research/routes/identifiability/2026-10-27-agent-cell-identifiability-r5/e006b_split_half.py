"""E006 (amended): is cross-context rank disagreement larger than within-cell replicate
disagreement?  Split-half ceiling vs cross-cell concordance.

Protocol: PROTOCOL_E006.md as amended by PROTOCOL_AMENDMENT_003.md.
  - keep clipped values (Viability is censored at 1.0; 17.9% of double-drug rows)
  - drop cells whose QC-failed fraction exceeds 20%
  - pairwise-complete unit sets, fixed subsample of 60 units x 50 redraws per comparison
  - ceiling: tau between the two replicate files of the same cell
  - test: paired sign test of tau_cross against the two cells' tau_half, across cell pairs
No response-dependent selection of layouts, cells, units or thresholds.
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
EXPECT_SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"

MIN_UNITS = 50
MIN_CELLS = 3
QC_DROP_FRAC = 0.20
N_SUB = 60
N_REDRAW = 50
N_BOOT = 2000
SEED = 20261027


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
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    return df


def layout_map(df: pd.DataFrame) -> dict:
    out = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        unit = {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}
        combo = {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso") for w, (d1, c1, d2, c2) in unit.items()}
        out[fname] = {"cell": g["Cell line"].iloc[0],
                      "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                      "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                      "unit": unit, "combo": combo,
                      "qc_frac": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in out.items():
        groups.setdefault((s["iteration"], s["h"]), {"cells": {}, "unit": s["unit"], "combo": s["combo"]})
        groups[(s["iteration"], s["h"])]["cells"].setdefault(s["cell"], []).append(f)
    return groups, out


def file_vector(df: pd.DataFrame, fname: str, units: list[str]) -> np.ndarray:
    sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
    s = sub.drop_duplicates("Well").set_index("Well")["y"]
    return s.reindex(units).to_numpy(dtype=float)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def concordance(ya: np.ndarray, yb: np.ndarray, floor: float, idx=None) -> tuple[float, int]:
    """Fraction of unit pairs agreeing in sign between two measurement vectors,
    restricted to pairs whose gap exceeds `floor` in BOTH vectors."""
    n = ya.size
    i, j = np.triu_indices(n, 1)
    if idx is not None:
        i, j = i[idx], j[idx]
    ga = np.abs(ya[i] - ya[j])
    gb = np.abs(yb[i] - yb[j])
    keep = (ga >= floor) & (gb >= floor)
    if keep.sum() == 0:
        return float("nan"), 0
    sa = np.sign(ya[i][keep] - ya[j][keep])
    sb = np.sign(yb[i][keep] - yb[j][keep])
    return float(np.mean(sa == sb)), int(keep.sum())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == EXPECT_SHA
    df = load()
    groups, per_file = layout_map(df)
    rng = np.random.default_rng(SEED)

    dropped = {"layouts_lt3cells": 0, "layouts_lt_units": 0, "cells_qc_dropped": []}
    layouts = []
    for (it, h), lay in groups.items():
        cells_all = sorted(lay["cells"])
        if len(cells_all) < MIN_CELLS:
            dropped["layouts_lt3cells"] += 1
            continue
        cells = []
        for c in cells_all:
            qc = max(per_file[f]["qc_frac"] for f in lay["cells"][c])
            if qc > QC_DROP_FRAC:
                dropped["cells_qc_dropped"].append({"layout": f"{it}/{h[:12]}", "cell": c, "qc_frac": round(qc, 3)})
            else:
                cells.append(c)
        if len(cells) < MIN_CELLS:
            dropped["layouts_lt3cells"] += 1
            continue
        units = [u for u in sorted(lay["unit"]) if lay["combo"][u]]
        layouts.append({"iteration": it, "hash": h[:12], "cells": cells,
                        "files": {c: lay["cells"][c] for c in cells}, "units": units})

    per_layout = []
    all_cellpairs = []
    for L in layouts:
        units = L["units"]
        F = {c: [file_vector(df, f, units) for f in L["files"][c]] for c in L["cells"]}
        avail = {c: np.sum([~np.isnan(v) for v in F[c]], axis=0) > 0 for c in L["cells"]}
        n_units_ge = int(np.sum(np.all(np.vstack([avail[c] for c in L["cells"]]), axis=0)))
        if n_units_ge < 20:
            dropped["layouts_lt_units"] += 1
            continue
        # sigma_w per layout from cells with two files (gap variance across units)
        sig = []
        for c in L["cells"]:
            if len(F[c]) == 2:
                d = F[c][0] - F[c][1]
                d = d[~np.isnan(d)]
                if d.size >= 20:
                    sig.append(float(np.std(d, ddof=1) / math.sqrt(2.0)))
        sigma = float(np.median(sig)) if sig else float("nan")
        floor = 2.0 * math.sqrt(2.0) * sigma if np.isfinite(sigma) else float("nan")

        # fixed subsample indices over unit slots (common random numbers)
        sub_idx = [rng.choice(len(units), N_SUB, replace=False) for _ in range(N_REDRAW)]
        pair_sub = [rng.choice(len(units) * (len(units) - 1) // 2,
                               min(3000, len(units) * (len(units) - 1) // 2), replace=False)
                    for _ in range(N_REDRAW)]

        def tau_between(va: np.ndarray, vb: np.ndarray) -> tuple[float, float, float, int]:
            """Mean Spearman over redraws and mean detectable-pair concordance."""
            rhos, concs, npair = [], [], []
            for k in range(N_REDRAW):
                idx = sub_idx[k]
                ok = ~np.isnan(va[idx]) & ~np.isnan(vb[idx])
                if ok.sum() < 20:
                    continue
                rhos.append(spearman(va[idx][ok], vb[idx][ok]))
            for k in range(N_REDRAW):
                c_, n_ = concordance(va, vb, floor, pair_sub[k])
                if np.isfinite(c_):
                    concs.append(c_)
                    npair.append(n_)
            return (float(np.nanmean(rhos)) if rhos else float("nan"),
                    float(np.nanmean(concs)) if concs else float("nan"),
                    float(np.mean(npair)) if npair else 0.0,
                    len(rhos))

        half = {}
        for c in L["cells"]:
            if len(F[c]) >= 2:
                t, cc, npair, nr = tau_between(F[c][0], F[c][1])
                half[c] = {"tau": t, "conc": cc, "n_pairs": npair}
        cross = []
        for a_idx in range(len(L["cells"])):
            for b_idx in range(a_idx + 1, len(L["cells"])):
                ca, cb = L["cells"][a_idx], L["cells"][b_idx]
                ts, cs = [], []
                for fa in F[ca]:
                    for fb in F[cb]:
                        t, cc, npair, nr = tau_between(fa, fb)
                        ts.append(t)
                        cs.append(cc)
                # agreement expected from the two cells' own ceilings
                ceil = [half[c]["tau"] for c in (ca, cb) if c in half]
                rec = {"layout": f"{L['iteration']}/{L['hash']}", "cell_a": ca, "cell_b": cb,
                       "tau_cross": float(np.nanmean(ts)), "conc_cross": float(np.nanmean(cs)),
                       "tau_half_mean": float(np.mean(ceil)) if ceil else float("nan"),
                       "n_ceilings": len(ceil)}
                cross.append(rec)
                all_cellpairs.append(rec)

        per_layout.append({"iteration": L["iteration"], "layout": L["hash"], "n_cells": len(L["cells"]),
                           "cells": L["cells"], "n_units": len(units), "n_units_in_all_cells": n_units_ge,
                           "sigma_w": sigma, "detectability_floor": floor,
                           "tau_half": {c: half[c]["tau"] for c in half},
                           "conc_half": {c: half[c]["conc"] for c in half},
                           "n_half_cells": len(half),
                           "tau_cross_mean": float(np.nanmean([r["tau_cross"] for r in cross])) if cross else None,
                           "conc_cross_mean": float(np.nanmean([r["conc_cross"] for r in cross])) if cross else None,
                           "n_cellpairs": len(cross)})

    cp = pd.DataFrame(all_cellpairs)
    paired = cp.dropna(subset=["tau_cross", "tau_half_mean"]).copy()
    paired["diff"] = paired["tau_half_mean"] - paired["tau_cross"]
    paired["conc_diff"] = paired["conc_cross"] - paired["conc_cross"]  # placeholder, replaced below

    n_pos = int((paired["diff"] > 0).sum())
    n_tot = int(len(paired))
    # exact-ish two-sided sign test
    from math import comb
    k = min(n_pos, n_tot - n_pos)
    p_sign = float(min(1.0, 2 * sum(comb(n_tot, i) for i in range(k + 1)) / (2 ** n_tot))) if n_tot else float("nan")

    # cluster bootstrap over cells for the median difference
    cells = sorted(set(paired["cell_a"]) | set(paired["cell_b"]))
    boots = []
    for _ in range(N_BOOT):
        pick = set(rng.choice(cells, size=len(cells), replace=True))
        sel = paired[paired["cell_a"].isin(pick) & paired["cell_b"].isin(pick)]
        if len(sel) >= 2:
            boots.append(float(np.median(sel["diff"])))
    boots = np.asarray(boots)

    conc_pairs = cp.dropna(subset=["conc_cross"])
    conc_half_vals = {c: v for L in per_layout for c, v in L["conc_half"].items()}
    res = {
        "kind": "split_half_ceiling_vs_cross_context_rank_concordance",
        "protocol": ["PROTOCOL_E006.md", "PROTOCOL_AMENDMENT_003.md"],
        "audit": {"input_sha256": sha256(CSV), "n_rows": int(len(df)), "n_files": int(df["file"].nunique()),
                  "layouts_total": len(groups), "layouts_analysed": len(per_layout),
                  "dropped": {"layouts_with_fewer_than_3_cells_after_qc": dropped["layouts_lt3cells"],
                              "layouts_with_fewer_than_20_common_units": dropped["layouts_lt_units"],
                              "cells_dropped_for_qc": dropped["cells_qc_dropped"]},
                  "clipping": {"max_viability": float(df["y"].max()), "n_at_ceiling_total": int((df["y"] == 1.0).sum()),
                               "double_drug_rows": int((~df["anchor"] & ~df["dmso"]).sum()),
                               "double_drug_at_ceiling_frac": float((df.loc[~df["anchor"] & ~df["dmso"], "y"] == 1.0).mean())},
                  "N_SUB": N_SUB, "N_REDRAW": N_REDRAW, "N_BOOT": N_BOOT, "seed": SEED},
        "per_layout": per_layout,
        "cellpair_comparisons": paired[["layout", "cell_a", "cell_b", "tau_cross", "tau_half_mean", "diff"]].to_dict("records"),
        "primary": {"statistic": "tau_half_mean - tau_cross per cell pair",
                    "n_cellpairs": n_tot, "n_positive": n_pos, "frac_positive": (n_pos / n_tot) if n_tot else None,
                    "median_diff": float(paired["diff"].median()) if n_tot else None,
                    "mean_diff": float(paired["diff"].mean()) if n_tot else None,
                    "sign_test_p_two_sided": p_sign,
                    "bootstrap_median_diff_ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots.size else None,
                    "bootstrap_n": int(boots.size)},
        "secondary_concordance": {
            "median_conc_half": float(np.median(list(conc_half_vals.values()))) if conc_half_vals else None,
            "median_conc_cross": float(np.median(conc_pairs["conc_cross"])) if len(conc_pairs) else None,
            "median_conc_diff_cross_minus_half": float(np.median(conc_pairs["conc_cross"])) - float(np.median(list(conc_half_vals.values()))) if len(conc_pairs) and conc_half_vals else None,
            "note": "concordance restricted to unit pairs whose gap exceeds 2*sqrt(2)*sigma_w in BOTH compared vectors",
        },
        "decisions": {},
        "limits": [
            "The layouts are the Project_Validation plate family already used as scoring endpoints by an earlier round: secondary/descriptive, not independent confirmation.",
            "Viability is censored at 1.0 (17.9% of double-drug rows), so ties are structural; Spearman uses average ranks and monotone saturation is allowed by the shared-order model.",
            "Cells within a layout share drug plates and dates, so cell pairs are not independent; the sign test treats them as exchangeable units of comparison and is reported with a cluster bootstrap instead of a population p-value.",
            "Functional readout only; no death rate, selectivity, target engagement, genetic-perturbation reference or clinical claim.",
            "No predictor is trained and no acquisition policy is compared here.",
        ],
    }
    d = res["decisions"]
    d["H008_prime_cross_below_ceiling"] = bool(p_sign < 0.05 and float(paired["diff"].median()) > 0)
    d["claim_A"] = ("cross_context_order_differs_beyond_measurement_noise"
                    if d["H008_prime_cross_below_ceiling"] else "not_established")
    conc_ok = res["secondary_concordance"]["median_conc_diff_cross_minus_half"]
    d["H009_prime_detectable_pairs_also_disagree"] = bool(conc_ok is not None and conc_ok < -0.02)
    d["claim_B"] = ("detectable_pairs_carry_the_disagreement" if d["H009_prime_detectable_pairs_also_disagree"]
                    else "disagreement_is_confined_to_sub_noise_pairs_or_absent")
    for rel in ("research/2026-10-27-agent-cell-identifiability-r5/PROTOCOL_E006.md",
                "research/2026-10-27-agent-cell-identifiability-r5/PROTOCOL_AMENDMENT_003.md",
                "research/2026-10-27-agent-cell-identifiability-r5/e006b_split_half.py",
                "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"):
        pth = ROOT / rel
        if pth.exists():
            res.setdefault("files", {})[rel] = sha256(pth)
    (OUT / "E006_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"layouts analysed={len(per_layout)} dropped={dropped['layouts_lt3cells']} cells_qc={len(dropped['cells_qc_dropped'])}")
    for L in per_layout:
        print("  it=%-2s cells=%-2d units=%-3d sigma=%.4f floor=%.3f half_cells=%d tau_half_med=%.3f tau_cross=%.3f conc_half_med=%.3f conc_cross=%.3f" % (
            L["iteration"], L["n_cells"], L["n_units"], L["sigma_w"], L["detectability_floor"], L["n_half_cells"],
            float(np.median(list(L["tau_half"].values()))) if L["tau_half"] else float("nan"),
            L["tau_cross_mean"] if L["tau_cross_mean"] is not None else float("nan"),
            float(np.median(list(L["conc_half"].values()))) if L["conc_half"] else float("nan"),
            L["conc_cross_mean"] if L["conc_cross_mean"] is not None else float("nan")))
    print("PRIMARY: n=%d positive=%d (%.2f) median_diff=%.3f sign_p=%.4g CI=%s" % (
        n_tot, n_pos, (n_pos / n_tot) if n_tot else float("nan"),
        float(paired["diff"].median()) if n_tot else float("nan"), p_sign,
        res["primary"]["bootstrap_median_diff_ci95"]))
    print("CONCORDANCE: half=%.3f cross=%.3f diff=%.3f" % (
        res["secondary_concordance"]["median_conc_half"] or float("nan"),
        res["secondary_concordance"]["median_conc_cross"] or float("nan"),
        res["secondary_concordance"]["median_conc_diff_cross_minus_half"] or float("nan")))
    print("DECISIONS:", json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
