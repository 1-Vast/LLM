"""Evaluation of stored held-out predictions: decision metrics on the contested pool, probability scores, and molecular intervention-response skill."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from sklearn.metrics import average_precision_score, roc_auc_score
import ptv_tasks as T


def load_preds(rundir: Path, stage: str, variant: str, seed=0, helds=None):
    """Concatenate held-out predictions; returns DataFrame (cell, perts, lab, single, p) and dict of arrays per row."""
    rows = []
    for f in sorted(Path(rundir).glob(f"{stage}_*_{variant}_s{seed}.npz")):
        z = np.load(f, allow_pickle=True)
        d = pd.DataFrame({"cell": z["cell"], "perts": z["perts"], "y": z["lab"], "single": z["single"], "p": z["p"]})
        d["_file"] = f.name; d["_i"] = np.arange(len(d)); rows.append(d)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def calib_slope(p, y):
    from sklearn.linear_model import LogisticRegression
    z = np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
    if len(set(y)) < 2: return np.nan
    m = LogisticRegression(C=1e6, max_iter=1000).fit(z[:, None], y); return float(m.coef_[0, 0])


def background_metrics(df: pd.DataFrame, train_singles: pd.DataFrame, k=T.K_NOM, score="p"):
    """df: singles of ONE held-out background with labels and a score column. Returns dict of metrics on all drugs and on the contested pool."""
    d = df[df.single & df.y.notna()].set_index("perts")
    out = {"n": len(d), "prevalence": float(d.y.mean())}
    if d.y.nunique() > 1:
        out["auroc_all"] = float(roc_auc_score(d.y, d[score])); out["auprc_all"] = float(average_precision_score(d.y, d[score]))
    out["brier_all"] = brier(d[score].values, d.y.values)
    pool = T.contested_pool(train_singles, list(d.index))
    out["pool_n"] = len(pool)
    if len(pool) >= k + 1:
        dp = d.loc[pool]
        out["prec_at_k_pool"] = T.precision_at_k(dp[score], dp.y, k)
        out["pool_prevalence"] = float(dp.y.mean())
        out["oracle_prec_pool"] = float(min(1.0, dp.y.sum() / k))
        if dp.y.nunique() > 1:
            out["auroc_pool"] = float(roc_auc_score(dp.y, dp[score])); out["auprc_pool"] = float(average_precision_score(dp.y, dp[score]))
        out["brier_pool"] = brier(dp[score].values, dp.y.values)
    return out
