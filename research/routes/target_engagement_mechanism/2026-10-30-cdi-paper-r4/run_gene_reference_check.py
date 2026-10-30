"""Pre-registered genetic-reference check for the FLT3 CDI pilot.

The check joins the existing 19Q4 PRISM pair/cell/dose response table to the
independently released 26Q1 Chronos FLT3 gene-effect row by exact DepMap_ID.
It reports descriptive concordance only; Chronos is a genetic dependency
reference, not a cellular drug-engagement measurement.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(r"D:/MAESTRO")
EP = ROOT / "research/2026-10-30-cdi-paper-r4"
PAIR = ROOT / "research/2026-10-30-cdi-r3/flt3_pair_cell_dose_observations.csv"
GENE = EP / "raw/resource_metadata/DepMap_26Q1_gene_effect_FLT3.csv"
OUT = EP / "raw/resource_metadata/gene_reference_check.json"


def rho(x: pd.Series, y: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if int(mask.sum()) < 3:
        return None
    return float(spearmanr(x[mask], y[mask]).statistic)


def main() -> None:
    usecols = [
        "cell_id",
        "pair_id",
        "dose",
        "delta_pKd",
        "delta_y",
    ]
    pairs = pd.read_csv(PAIR, usecols=usecols, low_memory=False)
    gene = pd.read_csv(GENE, low_memory=False)
    gene = gene.rename(columns={"gene_effect_FLT3": "flt3_gene_effect_26q1"})
    gene["DepMap_ID"] = gene["DepMap_ID"].astype(str)
    pairs["cell_id"] = pairs["cell_id"].astype(str)
    joined = pairs.merge(gene, left_on="cell_id", right_on="DepMap_ID", how="inner")
    if joined.empty:
        result = {
            "status": "no_exact_join",
            "pair_rows": int(len(pairs)),
            "gene_reference_rows": int(len(gene)),
            "joined_rows": 0,
            "joined_cells": 0,
            "boundary": "No genetic concordance can be assessed without exact DepMap_ID overlap.",
        }
        OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return

    # Chronos gene effect is signed: more negative means stronger inferred
    # dependency. Freeze tertiles on unique cells before joining repeated
    # pair×cell×dose rows; otherwise cells with more observed rows receive
    # extra weight in the context definition.
    cell_labels = gene[["DepMap_ID", "flt3_gene_effect_26q1"]].drop_duplicates(
        "DepMap_ID"
    )
    cell_labels["dependency_tertile"] = pd.qcut(
        cell_labels["flt3_gene_effect_26q1"],
        q=3,
        labels=["high_dependency", "mid_dependency", "low_dependency"],
        duplicates="drop",
    )
    joined = joined.drop(columns=["flt3_gene_effect_26q1"]).merge(
        cell_labels,
        left_on="cell_id",
        right_on="DepMap_ID",
        how="inner",
    )
    direct_rho = rho(joined["flt3_gene_effect_26q1"], joined["delta_y"])
    pair_dose = (
        joined.groupby(
            ["pair_id", "dose", "delta_pKd", "dependency_tertile"],
            observed=True,
        )
        .agg(mean_delta_y=("delta_y", "mean"), n_cells=("delta_y", "size"))
        .reset_index()
    )
    wide = pair_dose.pivot_table(
        index=["pair_id", "dose", "delta_pKd"],
        columns="dependency_tertile",
        values=["mean_delta_y", "n_cells"],
        aggfunc="first",
        observed=True,
    ).reset_index()
    wide.columns = [
        "_".join(str(v) for v in col if str(v) != "").strip("_")
        if isinstance(col, tuple)
        else str(col)
        for col in wide.columns
    ]
    needed = [
        "mean_delta_y_high_dependency",
        "mean_delta_y_low_dependency",
    ]
    if all(c in wide.columns for c in needed):
        wide["D_high_dependency_minus_low_dependency"] = (
            wide[needed[0]] - wide[needed[1]]
        )
        valid = wide.dropna(subset=["D_high_dependency_minus_low_dependency"])
        interaction_rho = rho(
            valid["delta_pKd"], valid["D_high_dependency_minus_low_dependency"]
        )
    else:
        valid = wide.iloc[0:0]
        interaction_rho = None

    # The same pair contributes multiple doses, so retain a pair-level summary
    # and dose-specific sensitivity instead of treating 1,109 pair×dose rows
    # as independent evidence.
    pair_summary = (
        valid.groupby(["pair_id", "delta_pKd"], observed=True)
        .agg(mean_D=("D_high_dependency_minus_low_dependency", "mean"))
        .reset_index()
    )
    pair_level_rho = rho(pair_summary["delta_pKd"], pair_summary["mean_D"])
    dose_level_rho = {
        str(dose): rho(group["delta_pKd"], group["D_high_dependency_minus_low_dependency"])
        for dose, group in valid.groupby("dose", observed=True)
    }
    cell_mean = (
        joined.groupby("cell_id", observed=True)
        .agg(
            mean_delta_y=("delta_y", "mean"),
            flt3_gene_effect_26q1=("flt3_gene_effect_26q1", "first"),
        )
        .reset_index()
    )
    cell_level_direct_rho = rho(
        cell_mean["flt3_gene_effect_26q1"], cell_mean["mean_delta_y"]
    )

    result = {
        "status": "exact_join_descriptive_only",
        "pair_rows": int(len(pairs)),
        "gene_reference_rows": int(len(gene)),
        "joined_rows": int(len(joined)),
        "joined_cells": int(joined["cell_id"].nunique()),
        "joined_pairs": int(joined["pair_id"].nunique()),
        "joined_doses": int(joined["dose"].nunique()),
        "gene_effect_range": [
            float(joined["flt3_gene_effect_26q1"].min()),
            float(joined["flt3_gene_effect_26q1"].max()),
        ],
        "spearman_gene_effect_vs_delta_y_repeated_rows": direct_rho,
        "interaction_rows_with_high_low_dependency": int(len(valid)),
        "spearman_delta_pKd_vs_D_high_dependency_minus_low_dependency_cell_frozen": interaction_rho,
        "spearman_delta_pKd_vs_pair_mean_D_cell_frozen": pair_level_rho,
        "dose_specific_spearman_delta_pKd_vs_D_cell_frozen": dose_level_rho,
        "spearman_gene_effect_vs_cell_mean_delta_y": cell_level_direct_rho,
        "tertile_definition": "qcut on 395 unique joined cells before repeated-row merge",
        "dependency_direction": "more negative Chronos gene-effect means stronger inferred dependency",
        "version_boundary": "PRISM response is 19Q4/MTS010 retrospective data; GeneEffect is DepMap 26Q1.",
        "scientific_boundary": "Genetic concordance/discordance only; no target engagement, dose-time mediation, causality, Agent advantage, or code promotion.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
