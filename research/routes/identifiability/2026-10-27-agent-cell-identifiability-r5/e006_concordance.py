"""E006: cross-context order concordance with a noise-calibrated null, and the
detectable-pair subset.

Pre-registered in PROTOCOL_E006.md (frozen before any real response was summarised
by this experiment). Reads only PAIR_SCREEN.csv.

Design in one paragraph: within a layout, every cell was measured on the same set of
drug-pair units, with 1-2 replicate plates per cell. Under M0 (shared order + per-cell
strictly increasing distortion) the within-cell rank vector is identical across cells;
noise is what makes observed ranks disagree. So we build a parametric bootstrap that
keeps each cell's own (de-noised) profile shape, enforces a shared rank vector, and adds
back noise at the measured level. Observed concordance is then compared with that null.
Two statistics: S1 = mean Spearman rho across cell pairs; S2 = sign concordance on unit
pairs whose profile separation exceeds the noise-derived detectability floor.
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

B_NULL = 1000
B_POWER = 400
PI_GRID = (0.1, 0.2, 0.3, 0.5)
PAIRS_PER_CELLPAIR = 300      # fixed subsample of detectable pairs (common random numbers)
MIN_UNITS = 50
MIN_CELLS = 3
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
    df["clipped"] = (df["y"] == 0.0) | (df["y"] == 1.0)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    return df


def build_layouts(df: pd.DataFrame):
    """Return layouts = {(iteration, hash): {'cells': {cell: [files]}, 'unit': {well: key}, 'combo': {well: bool}}}."""
    sig = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        unit = {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}
        combo = {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso") for w, (d1, c1, d2, c2) in unit.items()}
        sig[fname] = {"cell": g["Cell line"].iloc[0],
                      "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                      "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                      "unit": unit, "combo": combo}
    layouts = {}
    for f, s in sig.items():
        key = (s["iteration"], s["h"])
        lay = layouts.setdefault(key, {"cells": {}, "unit": s["unit"], "combo": s["combo"]})
        lay["cells"].setdefault(s["cell"], []).append(f)
    return layouts


def cell_unit_matrix(df: pd.DataFrame, files: list[str], units: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Mean viability per unit and the per-cell replicate count, from the given files."""
    sub = df[df["file"].isin(files)].copy()
    sub = sub[~sub["anchor"] & ~sub["failed_qc"] & sub["y"].notna() & ~sub["clipped"]]
    sub = sub[sub["Well"].isin(units)]
    if sub.empty:
        return np.full(len(units), np.nan), np.zeros(len(units))
    g = sub.groupby("Well")["y"].agg(["mean", "count"])
    y = g["mean"].reindex(units).to_numpy(dtype=float)
    k = g["count"].reindex(units).fillna(0).to_numpy(dtype=float)
    return y, k


def rank_rows(a: np.ndarray) -> np.ndarray:
    """Row-wise average ranks (ties averaged). a: (n_rows, n_cols) -> ranks."""
    order = np.argsort(a, axis=1, kind="mergesort")
    ranks = np.empty_like(a, dtype=float)
    rows = np.arange(a.shape[0])[:, None]
    ranks[rows, order] = np.arange(1, a.shape[1] + 1, dtype=float)[None, :]
    # average ties per row
    for i in range(a.shape[0]):
        row = a[i]
        if np.unique(row).size == row.size:
            continue
        _, inv, counts = np.unique(row, return_inverse=True, return_counts=True)
        sums = np.zeros(counts.size)
        np.add.at(sums, inv, ranks[i])
        ranks[i] = (sums / counts)[inv]
    return ranks


def stats_for_layout(Y: np.ndarray, pair_idx: np.ndarray | None) -> tuple[float, float, int]:
    """Y: (n_cells, n_units) measured values. Returns (fisher_z_mean, concordance, n_pairs_used)."""
    n_cells = Y.shape[0]
    if n_cells < 2:
        return float("nan"), float("nan"), 0
    R = rank_rows(Y)
    Z = R - R.mean(axis=1, keepdims=True)
    sd = Z.std(axis=1, keepdims=True)
    sd[sd == 0] = np.inf
    Z = Z / sd
    C = (Z @ Z.T) / Y.shape[1]
    iu = np.triu_indices(n_cells, 1)
    rho = np.clip(C[iu], -0.999999, 0.999999)
    z = np.arctanh(rho)
    fz = float(z.mean())
    if pair_idx is None or len(pair_idx[0]) == 0:
        return fz, float("nan"), 0
    i, j = pair_idx
    conc = []
    for a in range(n_cells):
        for b in range(a + 1, n_cells):
            sa = np.sign(Y[a, i] - Y[a, j])
            sb = np.sign(Y[b, i] - Y[b, j])
            agree = (sa == sb)
            conc.append(float(agree.mean()))
    return fz, float(np.mean(conc)), int(i.shape[0])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == EXPECT_SHA
    df = load()
    layouts = build_layouts(df)

    rng = np.random.default_rng(SEED)

    picked = []
    for (it, h), lay in layouts.items():
        if len(lay["cells"]) < MIN_CELLS:
            continue
        cells = sorted(lay["cells"])
        units = [u for u in sorted(lay["unit"]) if lay["combo"][u]]
        # keep only units present (non-missing) in every cell
        Ys, Ks = [], []
        for c in cells:
            y, k = cell_unit_matrix(df, lay["cells"][c], units)
            Ys.append(y)
            Ks.append(k)
        Y = np.vstack(Ys)
        K = np.vstack(Ks)
        ok = (~np.isnan(Y)).all(axis=0) & (K > 0).all(axis=0)
        if ok.sum() < MIN_UNITS:
            continue
        picked.append({"iteration": it, "hash": h[:12], "cells": cells, "units": [u for u, o in zip(units, ok) if o],
                       "Y": Y[:, ok], "K": K[:, ok], "files": lay["cells"]})

    summary = []
    for p in picked:
        k2 = p["K"] == 2
        # sigma_w from cells with exactly two files: sd across units of (f1 - f2) / sqrt(2)
        sigmas = []
        for ci, c in enumerate(p["cells"]):
            if p["K"][ci].max() != 2 or p["K"][ci].min() != 2:
                continue
            files = p["files"][c]
            a, _ = cell_unit_matrix(df, [files[0]], p["units"])
            b, _ = cell_unit_matrix(df, [files[1]], p["units"])
            d = a - b
            d = d[~np.isnan(d)]
            if d.size >= 20:
                sigmas.append(float(np.std(d, ddof=1) / math.sqrt(2.0)))
        p["sigma"] = float(np.median(sigmas)) if sigmas else float("nan")
        p["n_sigma_cells"] = len(sigmas)
        p["sigma_all"] = sigmas

    pooled_sigma = float(np.median([p["sigma"] for p in picked if np.isfinite(p["sigma"])]))
    for p in picked:
        if not np.isfinite(p["sigma"]):
            p["sigma"] = pooled_sigma
            p["sigma_source"] = "pooled"
        else:
            p["sigma_source"] = "layout"

    # ---- reference order, de-noised cell profiles, detectable pair subsample ----
    for p in picked:
        Y, K, s = p["Y"], p["K"], p["sigma"]
        R = rank_rows(Y).mean(axis=0)
        order = np.argsort(R)
        n = Y.shape[1]
        prof = np.empty((Y.shape[0], n))
        for ci in range(Y.shape[0]):
            v = np.sort(Y[ci])
            lam = math.sqrt(max(0.0, 1.0 - (s ** 2 / K[ci].mean()) / max(np.var(v), 1e-12)))
            prof[ci, order] = v.mean() + lam * (v - v.mean())
        p["profile"] = prof
        p["order"] = order
        p["R"] = R
        pooled = prof.mean(axis=0)
        thr = 2.0 * math.sqrt(2.0) * s
        # candidate unit pairs separated by at least the floor on the pooled profile
        cand = np.argwhere(np.abs(pooled[:, None] - pooled[None, :]) >= thr)
        cand = cand[cand[:, 0] < cand[:, 1]]
        if cand.shape[0] > PAIRS_PER_CELLPAIR:
            sel = rng.choice(cand.shape[0], PAIRS_PER_CELLPAIR, replace=False)
            cand = cand[sel]
        p["pair_idx"] = (cand[:, 0], cand[:, 1]) if cand.size else None
        p["n_candidate_pairs"] = int(cand.shape[0]) if cand.size else 0
        p["floor"] = thr

    used = [p for p in picked if p["pair_idx"] is not None]
    n_units_total = sum(p["Y"].shape[1] for p in used)
    n_cellpairs_total = sum(p["Y"].shape[0] * (p["Y"].shape[0] - 1) // 2 for p in used)

    # ---- observed ----
    obs_per_layout = []
    for p in used:
        fz, conc, npair = stats_for_layout(p["Y"], p["pair_idx"])
        obs_per_layout.append({"iteration": p["iteration"], "layout": p["hash"], "n_cells": p["Y"].shape[0],
                              "n_units": p["Y"].shape[1], "sigma_w": p["sigma"], "sigma_source": p["sigma_source"],
                              "spearman_fisher_z": fz, "spearman_backtransformed": float(np.tanh(fz)),
                              "concordance_detectable_pairs": conc, "n_pairs_used": npair,
                              "n_candidate_pairs_available": p["n_candidate_pairs"],
                              "detectability_floor": p["floor"],
                              "cell_files": {c: len(p["files"][c]) for c in p["cells"]}})
    S1_obs = float(np.average([o["spearman_fisher_z"] for o in obs_per_layout],
                              weights=[o["n_cells"] * (o["n_cells"] - 1) // 2 for o in obs_per_layout]))
    S2_obs = float(np.average([o["concordance_detectable_pairs"] for o in obs_per_layout],
                              weights=[o["n_pairs_used"] for o in obs_per_layout]))

    # ---- simulation engine ----
    def simulate(pi: float | None, b: int, profiles_mode: str = "cell"):
        """Return arrays of S1, S2 for b simulated datasets. pi=None -> M0."""
        z1 = np.empty(b)
        z2 = np.empty(b)
        for it in range(b):
            fz_list, fz_w, conc_list, conc_w = [], [], [], []
            for p in used:
                Y0, K, s = p["Y"], p["K"], p["sigma"]
                nc, nu = Y0.shape
                if profiles_mode == "cell":
                    prof = p["profile"]
                else:
                    pooled = p["profile"].mean(axis=0)
                    prof = np.tile(pooled, (nc, 1))
                # positions: M0 -> identity; alternative -> swap a pi fraction within each cell
                Ysim = np.empty_like(prof)
                for ci in range(nc):
                    pos = np.arange(nu)
                    if pi:
                        m = int(round(pi * nu))
                        if m >= 2:
                            idx = rng.choice(nu, m, replace=False)
                            perm = rng.permutation(idx)
                            pos[idx] = perm
                    sigma_c = s / math.sqrt(K[ci].mean())
                    Ysim[ci] = prof[ci, pos] + rng.normal(0.0, sigma_c, nu)
                fz, conc, npair = stats_for_layout(Ysim, p["pair_idx"])
                w = nc * (nc - 1) // 2
                fz_list.append(fz * w)
                fz_w.append(w)
                conc_list.append(conc * npair)
                conc_w.append(npair)
            z1[it] = sum(fz_list) / sum(fz_w)
            z2[it] = sum(conc_list) / sum(conc_w)
        return z1, z2

    null1, null2 = simulate(None, B_NULL)
    _, null2b = simulate(None, B_NULL // 2, profiles_mode="pooled")  # sensitivity: common profile

    def pval(null: np.ndarray, obs: float) -> float:
        return float((1 + np.sum(null <= obs)) / (null.size + 1))

    p1 = pval(null1, S1_obs)
    p2 = pval(null2, S2_obs)
    crit1 = float(np.quantile(null1, 0.05))
    crit2 = float(np.quantile(null2, 0.05))

    power = []
    for pi in PI_GRID:
        a1, a2 = simulate(pi, B_POWER)
        power.append({"pi": pi,
                      "power_S1": float(np.mean(a1 < crit1)),
                      "power_S2": float(np.mean(a2 < crit2)),
                      "mean_S1": float(a1.mean()), "mean_S2": float(a2.mean())})

    m0_sensitivity = {
        "cell_specific_profiles": {"mean": float(null1.mean()), "sd": float(null1.std())},
        "pooled_profile_S2": {"mean": float(null2b.mean()), "sd": float(null2b.std()),
                              "p_value_for_observed_S2": pval(null2b, S2_obs)},
    }

    h008 = bool(p1 < 0.05 or p2 < 0.05)
    pow20 = next((p_ for p_ in power if p_["pi"] == 0.2), None)
    h009 = bool(pow20 and pow20["power_S2"] >= pow20["power_S1"] + 0.10 and float(np.mean(null2 < crit2)) <= 0.10)

    if h008:
        decision_A = "context_specific_order_detected_at_aggregate_resolution"
    elif pow20 and max(pow20["power_S1"], pow20["power_S2"]) >= 0.8:
        decision_A = "m0_not_rejected_and_test_was_powerful_enough"
    else:
        decision_A = "underpowered_no_claim"

    res = {
        "kind": "noise_calibrated_cross_context_order_concordance_test",
        "protocol": "PROTOCOL_E006.md (frozen before this run)",
        "audit": {"n_rows": int(len(df)), "n_files": int(df["file"].nunique()),
                  "n_cells": int(df["Cell line"].nunique()),
                  "input_sha256": sha256(CSV),
                  "layouts_total": len(layouts),
                  "layouts_eligible_ge3cells_ge50units": len(picked),
                  "layouts_used_with_detectable_pairs": len(used),
                  "units_total": int(n_units_total), "cell_pairs_total": int(n_cellpairs_total),
                  "B_null": B_NULL, "B_power": B_POWER, "seed": SEED},
        "sigma_w": {"pooled_median": pooled_sigma,
                    "per_layout": {f"{p['iteration']}/{p['hash']}": p["sigma"] for p in picked},
                    "n_cells_with_two_files": {f"{p['iteration']}/{p['hash']}": p["n_sigma_cells"] for p in picked},
                    "note": "estimated inside each layout from the two replicate files (identical layout), so no cross-format borrowing"},
        "observed": {"S1_fisher_z_pooled": S1_obs, "S1_backtransformed": float(np.tanh(S1_obs)),
                     "S2_concordance_pooled": S2_obs, "per_layout": obs_per_layout},
        "null_M0": {"S1": {"mean": float(null1.mean()), "sd": float(null1.std()),
                           "q05": crit1, "q50": float(np.quantile(null1, 0.5)), "q95": float(np.quantile(null1, 0.95))},
                    "S2": {"mean": float(null2.mean()), "sd": float(null2.std()),
                           "q05": crit2, "q50": float(np.quantile(null2, 0.5)), "q95": float(np.quantile(null2, 0.95))}},
        "p_values": {"S1": p1, "S2": p2},
        "power": power,
        "null_sensitivity": m0_sensitivity,
        "decisions": {"H008_context_specific_order_detected": h008, "H009_detectable_subset_better": h009,
                      "claim_A": decision_A,
                      "claim_B": "supported" if h009 else "not supported -> stop B"},
        "limits": [
            "The 18 layouts are the author's Project_Validation plates, already used by an earlier round as scoring endpoints; this is a secondary/descriptive test, not independent confirmation.",
            "Layouts share drug plates and screening dates; cell pairs inside a layout are not independent, so the pooled p-value is a summary, not a population inference.",
            "The M0 bootstrap conditions on the observed rank-average order and on per-cell profile shapes; under strong discordance that order is itself smeared (sensitivity with a common pooled profile is reported).",
            "Functional readout only: normalised metabolic viability. No death rate, selectivity, target engagement, genetic-perturbation reference or clinical claim.",
            "No predictor is trained and no acquisition policy is compared in this experiment.",
        ]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r5/PROTOCOL_E006.md",
                "research/2026-10-27-agent-cell-identifiability-r5/CANDIDATE_I003.md",
                "research/2026-10-27-agent-cell-identifiability-r5/e006_concordance.py",
                "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"):
        pth = ROOT / rel
        if pth.exists():
            res.setdefault("files", {})[rel] = sha256(pth)
    (OUT / "E006_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"eligible layouts={len(picked)} used={len(used)} units={n_units_total} cell_pairs={n_cellpairs_total}")
    print("sigma_w pooled median=%.4f" % pooled_sigma)
    print("observed S1 (fisher z)=%.4f -> rho=%.4f ; S2 concordance=%.4f" % (S1_obs, math.tanh(S1_obs), S2_obs))
    print("M0 null S1: mean=%.4f sd=%.4f q05=%.4f | S2: mean=%.4f sd=%.4f q05=%.4f" % (
        null1.mean(), null1.std(), crit1, null2.mean(), null2.std(), crit2))
    print("p(S1)=%.4f p(S2)=%.4f" % (p1, p2))
    for pw in power:
        print("  pi=%.1f power S1=%.3f S2=%.3f | mean S1=%.4f S2=%.4f" % (
            pw["pi"], pw["power_S1"], pw["power_S2"], pw["mean_S1"], pw["mean_S2"]))
    print("H008:", h008, "| H009:", h009, "| claim A:", decision_A)


if __name__ == "__main__":
    main()
