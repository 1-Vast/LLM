"""Fixed negative control: permute relative-Kd labels at the drug-pair level."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


EP = Path(r"D:/MAESTRO/research/2026-10-30-cdi-r3")


def cv_rmse(df: pd.DataFrame, pdk: np.ndarray, splits: list[tuple[np.ndarray, np.ndarray]]) -> float:
    X = np.column_stack([
        df["flt3_expression"].to_numpy(float),
        np.log10(df["dose"].to_numpy(float)),
        pdk,
        pdk * df["flt3_expression"].to_numpy(float),
    ])
    y = df["delta_y"].to_numpy(float)
    pred = np.full(len(df), np.nan)
    for train, test in splits:
        pipe = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
        pipe.fit(X[train], y[train])
        pred[test] = pipe.predict(X[test])
    return float(np.sqrt(mean_squared_error(y, pred)))


def main() -> None:
    df = pd.read_csv(EP / "flt3_pair_cell_dose_observations.csv", low_memory=False)
    groups = df["pair_id"].to_numpy()
    splitter = GroupKFold(n_splits=5)
    splits = list(splitter.split(np.zeros(len(df)), df["delta_y"].to_numpy(float), groups))
    pair_table = df[["pair_id", "delta_pKd"]].drop_duplicates("pair_id").sort_values("pair_id")
    observed = cv_rmse(df, df["delta_pKd"].to_numpy(float), splits)
    rng = np.random.default_rng(20261030)
    null = []
    for _ in range(20):
        shuffled = pair_table["delta_pKd"].to_numpy(float).copy()
        rng.shuffle(shuffled)
        mapping = dict(zip(pair_table["pair_id"], shuffled))
        null.append(cv_rmse(df, df["pair_id"].map(mapping).to_numpy(float), splits))
    arr = np.asarray(null)
    out = {
        "observed_rmse": observed,
        "null_rmse": null,
        "null_mean": float(arr.mean()),
        "null_sd": float(arr.std(ddof=1)),
        "null_min": float(arr.min()),
        "null_max": float(arr.max()),
        "permutations": 20,
        "seed": 20261030,
        "boundary": "Pair-level label permutation is a negative-control sensitivity check for this retrospective predictor. It does not validate causal mediation, target engagement, biological replication, prospective Agent benefit, or novelty.",
    }
    (EP / "flt3_pair_label_permutation.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
