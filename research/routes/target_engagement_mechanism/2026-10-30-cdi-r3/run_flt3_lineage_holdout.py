"""Secondary fixed split for virtual-cell background transfer."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


EP = Path(r"D:/MAESTRO/research/2026-10-30-cdi-r3")


def main() -> None:
    df = pd.read_csv(EP / "flt3_pair_cell_dose_observations.csv", low_memory=False)
    df["log10_dose"] = np.log10(df["dose"].astype(float))
    df["delta_pKd_x_expr"] = df["delta_pKd"] * df["flt3_expression"]
    models = {
        "context_only": ["flt3_expression", "log10_dose"],
        "context_plus_relative_kd": ["flt3_expression", "log10_dose", "delta_pKd", "delta_pKd_x_expr"],
    }
    rows = []
    for name, cols in models.items():
        X = df[cols].astype(float).to_numpy()
        y = df["delta_y"].astype(float).to_numpy()
        groups = df["lineage"].fillna("UNKNOWN").to_numpy()
        pred = np.full(len(df), np.nan)
        splitter = GroupKFold(n_splits=5)
        for train, test in splitter.split(X, y, groups):
            pipe = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
            pipe.fit(X[train], y[train])
            pred[test] = pipe.predict(X[test])
        rows.append({
            "model": name,
            "split": "lineage_group_5fold",
            "n_rows": int(len(df)),
            "n_lineages": int(df["lineage"].nunique(dropna=True)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "r2": float(r2_score(y, pred)),
            "spearman": float(spearmanr(y, pred).statistic),
        })
    out = {"results": rows, "boundary": "Lineage holdout tests predictive transfer across observed background labels only; it does not identify target mediation, exposure effects, or Agent advantage."}
    (EP / "flt3_lineage_holdout.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
