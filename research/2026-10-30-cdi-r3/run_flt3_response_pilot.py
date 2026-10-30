"""Exploratory FLT3 cross-scale response association pilot.

This is deliberately smaller than the proposed CDI system.  It tests whether a
descriptive, same-target Kd contrast adds any held-out predictive information to
PRISM secondary viability responses after matching screen, nominal dose and cell.
It does not identify target mediation, cellular engagement, or Agent advantage.
"""
from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


ROOT = Path(r"D:/MAESTRO")
EP = ROOT / "research/2026-10-30-cdi-r3"
TARGET = "CHEMBL1974"
SCREEN = "MTS010"  # fixed before reading response values; technical redo status retained


def main() -> None:
    ident = pd.read_csv(EP / "prism_structure_identity_candidates.csv", low_memory=False)
    ident = ident[ident["mapping_status"].eq("exact_structure")].copy()
    ident["chembl_id"] = ident["exact_chembl_ids"].str.split(";").str[0]

    kd = pd.read_csv(ROOT / "data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv", low_memory=False)
    exact = kd[
        kd["target_chembl_id"].eq(TARGET)
        & kd["standard_relation"].eq("=")
        & kd["molecule_chembl_id"].isin(set(ident["chembl_id"]))
    ].copy()
    kd_min = exact.groupby("molecule_chembl_id")["standard_value"].min().to_dict()
    molecules = sorted(kd_min)
    broad_map = ident[ident["chembl_id"].isin(molecules)].groupby("chembl_id")["broad_id"].apply(list).to_dict()
    target_broads = sorted({b for xs in broad_map.values() for b in xs})

    tr = pd.read_csv(
        ROOT / "data/external/prism_19q4/raw/secondary-screen-replicate-treatment-info.csv",
        usecols=["column_name", "broad_id", "screen_id", "perturbation_type", "dose"],
        low_memory=False,
    )
    tr = tr[
        tr["broad_id"].isin(target_broads)
        & tr["screen_id"].eq(SCREEN)
        & tr["perturbation_type"].eq("experimental_treatment")
    ].copy()
    tr["chembl_id"] = tr["broad_id"].map({b: m for m, bs in broad_map.items() for b in bs})
    header = pd.read_csv(ROOT / "data/external/prism_19q4/raw/secondary-screen-logfold-change.csv", nrows=0).columns
    tr = tr[tr["column_name"].isin(set(header))].copy()
    raw_time_labels = sorted({m.upper() for value in tr["column_name"].astype(str) for m in re.findall(r"(?i)\d+H", value)})
    response_cols = sorted(tr["column_name"].unique())
    response = pd.read_csv(
        ROOT / "data/external/prism_19q4/raw/secondary-screen-logfold-change.csv",
        usecols=[header[0], *response_cols],
        index_col=0,
        dtype={c: np.float32 for c in response_cols},
        low_memory=False,
    )
    # Aggregate all same-molecule/batch columns into one cell×dose observation;
    # column count is retained and never treated as biological replication.
    long_parts = []
    for (chembl_id, dose), sub in tr.groupby(["chembl_id", "dose"], sort=False):
        vals = response[list(sub["column_name"])].mean(axis=1, skipna=True)
        long_parts.append(pd.DataFrame({"cell_id": response.index.astype(str), "chembl_id": chembl_id, "dose": float(dose), "y": vals.values, "n_treatment_columns": int(len(sub))}))
    obs = pd.concat(long_parts, ignore_index=True)
    obs = obs.dropna(subset=["y"])
    obs["pKd_nM"] = obs["chembl_id"].map({m: -np.log10(v) for m, v in kd_min.items()})

    # Independent background context: baseline FLT3 expression and lineage.
    exp = pd.read_csv(ROOT / "data/external/depmap_19q4/CCLE_expression.csv", usecols=["Unnamed: 0", "FLT3 (2322)"], low_memory=False)
    exp = exp.rename(columns={"Unnamed: 0": "cell_id", "FLT3 (2322)": "flt3_expression"})
    sample = pd.read_csv(ROOT / "data/external/depmap_19q4/sample_info.csv", usecols=["DepMap_ID", "lineage", "lineage_subtype"], low_memory=False)
    sample = sample.rename(columns={"DepMap_ID": "cell_id"})
    obs = obs.merge(exp, on="cell_id", how="left").merge(sample, on="cell_id", how="left")
    obs = obs.dropna(subset=["flt3_expression"])
    # Tertiles are frozen from the baseline expression table before pair outcome aggregation.
    obs["context_tertile"] = pd.qcut(obs["flt3_expression"], q=3, labels=["low", "mid", "high"], duplicates="drop")

    # Drug-pair contrasts within the same nominal dose and cell.
    pair_parts = []
    for dose, sub in obs.groupby("dose", sort=False):
        present = sorted(set(sub["chembl_id"]))
        for a, b in combinations(present, 2):
            aa = sub[sub["chembl_id"].eq(a)][["cell_id", "y", "flt3_expression", "context_tertile", "lineage", "lineage_subtype", "n_treatment_columns"]].rename(columns={"y": "y_a", "n_treatment_columns": "n_cols_a"})
            bb = sub[sub["chembl_id"].eq(b)][["cell_id", "y", "n_treatment_columns"]].rename(columns={"y": "y_b", "n_treatment_columns": "n_cols_b"})
            merged = aa.merge(bb, on="cell_id", how="inner")
            if merged.empty:
                continue
            merged["chembl_a"] = a
            merged["chembl_b"] = b
            merged["dose"] = dose
            merged["delta_y"] = merged["y_a"] - merged["y_b"]
            merged["delta_pKd"] = -np.log10(kd_min[a]) - (-np.log10(kd_min[b]))
            merged["pair_id"] = a + "__" + b
            pair_parts.append(merged)
    pairs = pd.concat(pair_parts, ignore_index=True) if pair_parts else pd.DataFrame()
    if pairs.empty:
        raise SystemExit("No matched A/B cell observations")

    # Pair×dose descriptive context contrast (high minus low expression tertile).
    grouped = pairs.groupby(["pair_id", "dose", "delta_pKd", "context_tertile"], observed=True).agg(mean_delta_y=("delta_y", "mean"), n_cells=("delta_y", "size")).reset_index()
    wide = grouped.pivot_table(index=["pair_id", "dose", "delta_pKd"], columns="context_tertile", values=["mean_delta_y", "n_cells"], aggfunc="first").reset_index()
    wide.columns = ["_".join([str(x) for x in c if str(x) != ""]).strip("_") if isinstance(c, tuple) else str(c) for c in wide.columns]
    if "mean_delta_y_high" in wide and "mean_delta_y_low" in wide:
        wide["D_high_minus_low"] = wide["mean_delta_y_high"] - wide["mean_delta_y_low"]
    else:
        wide["D_high_minus_low"] = np.nan

    valid_d = wide.dropna(subset=["D_high_minus_low"])
    rho_d, p_d = spearmanr(valid_d["delta_pKd"], valid_d["D_high_minus_low"]) if len(valid_d) >= 3 else (np.nan, np.nan)
    pair_mean = pairs.groupby(["pair_id", "delta_pKd"], as_index=False).agg(mean_delta_y=("delta_y", "mean"), n_cells=("delta_y", "size"))
    rho_mean, p_mean = spearmanr(pair_mean["delta_pKd"], pair_mean["mean_delta_y"]) if len(pair_mean) >= 3 else (np.nan, np.nan)

    # Fixed grouped CV: ordinary context/dose model versus adding affinity contrast.
    pairs["log10_dose"] = np.log10(pairs["dose"].astype(float))
    pairs["pair_group"] = pairs["pair_id"]
    pairs["delta_pKd_x_expr"] = pairs["delta_pKd"] * pairs["flt3_expression"]
    features_base = ["flt3_expression", "log10_dose"]
    features_cdi = ["flt3_expression", "log10_dose", "delta_pKd", "delta_pKd_x_expr"]
    # Screen is fixed to MTS010 in this pilot, so no screen dummy is needed.
    cv_rows = []
    for name, features in [("context_only", features_base), ("context_plus_relative_kd", features_cdi)]:
        X = pairs[features].astype(float).to_numpy()
        y = pairs["delta_y"].to_numpy(float)
        groups = pairs["pair_group"].to_numpy()
        gkf = GroupKFold(n_splits=5)
        pred = np.full(len(y), np.nan)
        for train, test in gkf.split(X, y, groups):
            model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
            model.fit(X[train], y[train])
            pred[test] = model.predict(X[test])
        cv_rows.append({"model": name, "n_rows": int(len(y)), "n_pairs": int(pairs.pair_id.nunique()), "rmse": float(np.sqrt(mean_squared_error(y, pred))), "r2": float(r2_score(y, pred)), "spearman": float(spearmanr(y, pred).statistic)})

    pairs.to_csv(EP / "flt3_pair_cell_dose_observations.csv", index=False)
    wide.to_csv(EP / "flt3_context_contrasts.csv", index=False)
    summary = {
        "target": TARGET,
        "screen": SCREEN,
        "screen_note": "PRISM MTS010 is documented as a technical redo. Treatment column labels contain the raw token(s) listed below, but the local README/audit does not provide a separately structured exposure-time/preparation field.",
        "raw_column_time_labels": raw_time_labels,
        "mapped_molecules_with_exact_kd": int(len(molecules)),
        "mapped_broad_ids": int(len(target_broads)),
        "response_columns": int(len(response_cols)),
        "cell_dose_observations": int(len(obs)),
        "pair_cell_dose_rows": int(len(pairs)),
        "pair_count": int(pairs.pair_id.nunique()),
        "context_contrast_rows_with_high_low": int(len(valid_d)),
        "spearman_pair_mean_delta_pKd_vs_delta_y": {"rho": float(rho_mean), "pvalue_descriptive": float(p_mean)},
        "spearman_delta_pKd_vs_D_high_minus_low": {"rho": float(rho_d), "pvalue_descriptive": float(p_d)},
        "grouped_cv": cv_rows,
        "data_boundary": "Retrospective predictive association only. Kd is lysate/kinobead apparent binding; PRISM is DMSO-relative viability. The raw column label is retained, but structured exposure-time/preparation and cellular engagement or genetic perturbation are unavailable. Technical columns were averaged within molecule×dose×cell and are not biological replicate counts.",
        "stop_rule": "No target-mediated, causal, prospective Agent, or code-promotion claim is allowed from this pilot; a positive association only gates a future intervention study.",
    }
    (EP / "flt3_response_pilot.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
