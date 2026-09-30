"""Virtual-cell causal ablation: the same episodes with the channel on, masked and permuted.

File summary
- Path: research/external_validation/paired_ablation.py
- Purpose: measure whether the virtual cell's predictions change which measurement is bought, and
  whether the changed choices end in better terminal decisions, for the MAESTRO selector and for
  the magnitude tie-break.
- Core points:
  - A switch is an episode whose action sequence (or stop) differs between the two arms.
  - Differences are paired on identical episodes and clustered by the independent unit; the
    switched-episode differences answer "when it changes the choice, is the choice better?".
  - The rule is the protocol's: no action change, or no terminal gain from the changes, means an
    acquisition value of zero whatever the prediction metrics say.
- Depends on: statistics.py, pandas
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import statistics as S

PAIRS = (("maestro_vc", "maestro_masked"), ("maestro_vc", "maestro_vc_permuted"),
         ("magnitude", "cost_only"), ("magnitude", "magnitude_permuted"))
METRICS = ("correct", "wrong", "measurements", "days")


def ablation(frame: pd.DataFrame, unit: str) -> dict:
    out = {}
    key = ["compound", "h1", "h2"]
    for left, right in PAIRS:
        a = frame[frame.policy == left].set_index(key)
        b = frame[frame.policy == right].set_index(key).reindex(a.index)
        first = a.first_action != b.first_action
        anystep = a.actions != b.actions
        entry = {"episodes": int(len(a)), "first_step_switch_rate": float(first.mean()),
                 "any_step_switch_rate": float(anystep.mean()),
                 "left_used_vc_rate": float(a.used_vc.astype(bool).mean())}
        entry["overall"] = {m: S.paired(frame, left, right, m, unit) for m in METRICS}
        switched = a.index[anystep.to_numpy()]
        if len(switched):
            sub = frame.set_index(key).loc[switched].reset_index()
            sub = sub[sub.policy.isin((left, right))]
            entry["switched"] = {m: S.paired(sub, left, right, m, unit) for m in METRICS}
        else:
            entry["switched"] = None
        c = entry["overall"]["correct"]
        entry["acquisition_value"] = ("zero: the channel never changed an action" if not anystep.any() else
                                      "zero: changed actions without a terminal gain" if c["ci"][0] <= 0 else
                                      "positive")
        out[f"{left} vs {right}"] = entry
    return out


def prediction_diagnostics(diagnostics: pd.DataFrame) -> dict:
    """Secondary: profile cosine of the virtual cell and ridge against the training-target mean."""
    out = {}
    for (dataset, tier), group in diagnostics.groupby(["dataset", "tier"]):
        entry = {}
        for subset, rows in (("all", group), ("detected", group[group.detected])):
            per = {"rows": int(len(rows))}
            for label in ("vc", "ridge", "train_mean"):
                column = f"cos_{label}"
                if column in rows:
                    per[f"mean_cosine_{label}"] = float(rows[column].mean())
            for label in ("vc", "ridge"):
                both = rows.dropna(subset=[f"cos_{label}", "cos_train_mean"])
                if len(both):
                    delta = both[f"cos_{label}"] - both.cos_train_mean
                    blocks = delta.groupby(both.compound).agg(["sum", "size"])
                    index = S.draws(len(blocks))
                    boot = blocks["sum"].to_numpy()[index].sum(1) / blocks["size"].to_numpy()[index].sum(1)
                    per[f"{label}_minus_train_mean"] = {"difference": float(delta.mean()),
                                                        "ci": np.quantile(boot, [.025, .975]).tolist(),
                                                        "rows": int(len(both))}
            if "norm_vc" in rows:
                both = rows.dropna(subset=["norm_vc"])
                if len(both) > 3:
                    per["magnitude_spearman_vc"] = float(both.norm_vc.rank().corr(both.measured_norm.rank()))
            entry[subset] = per
        out[f"{dataset}|{tier}"] = entry
    return out
