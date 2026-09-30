"""Forecast-level evaluation: calibration, hypothesis discrimination and prior quality of the case memory.

File summary
- Path: research/scientific_case_memory/evaluate_case_retrieval.py
- Purpose: score what each world forecast, before any reading, against the reading that was realised,
  over every (held-out compound, condition, contrast) of every episode. This is where calibration,
  discrimination, robustness strata and the value of failure cases can be measured with enough items
  to see effects the terminal decision cannot show.
- Core points:
  - An item holds two branches (the forecast if h1 is true, if h2 is true), the realised label and the
    truth (evaluator side). Only the truth branch is scored against the realised label; the other
    branch enters the discrimination score.
  - Metrics per world: negative log-likelihood of the realised label; Brier and ECE of the
    wrong-elimination event (the reading that removes the true hypothesis); the observed-to-forecast
    ratio of that event; and hypothesis discrimination, the mean of
    `log p(y | h_true) - log p(y | h_other)`, which is exactly zero for a forecast that is the same under
    both hypotheses (the scalar control).
  - Comparisons are paired over identical items and clustered by independent unit
    (`external_validation.statistics`-style bootstrap: 2,000 draws, seed 20260927). A world that
    refuses an item is dropped for every world, so no comparison mixes item sets.
  - Strata: structural novelty (nearest training neighbour below or above the registered floor 0.40);
    misled neighbour (nearest neighbour similar enough to matter and of a different class than the
    truth) against aligned neighbour; observed reading kind.
  - Prior quality: the retrieved hypothesis prior is scored as a forecast of which hypothesis is true,
    by log-loss against the uniform prior and by the share of informative priors that favour the truth.
- Interfaces: `LABELS`, `load_items`, `item_frame`, `world_metrics`, `paired_metric`, `strata_table`,
  `prior_quality`, `calibration_curve`
- Depends on: numpy, pandas, research/external_validation/statistics.py (draw scheme reproduced locally)
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

LABELS = ("profile_matches_h1", "profile_matches_h2", "profile_unresolved", "no_detectable_response", "quality_failed")
SEED = 20260927
DRAWS = 2000
FLOOR = 0.40
EPS = 1e-9


def load_items(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(Path(directory).glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)
    return rows


def item_frame(rows: list[dict], worlds: list[str]) -> pd.DataFrame:
    """One row per item and world with the truth-branch and other-branch vectors flattened to scalars."""
    out = []
    for r in rows:
        if any(r["worlds"].get(w) is None for w in worlds):
            continue
        yi = LABELS.index(r["y"])
        truth_is_h1 = r["truth"] == r["h1"]
        for w in worlds:
            entry = r["worlds"][w]
            p_t = np.asarray(entry["h1" if truth_is_h1 else "h2"], dtype=float)
            p_o = np.asarray(entry["h2" if truth_is_h1 else "h1"], dtype=float)
            wrong_idx = 1 if truth_is_h1 else 0  # the reading that matches the other hypothesis removes the truth
            out.append({
                "dataset": r["dataset"], "tier": str(r["tier"]), "fold": r["fold"], "compound": r["compound"],
                "unit": f"{r['dataset']}:{r['unit']}", "key": r["key"], "world": w, "y": yi,
                "nll": -float(np.log(max(p_t[yi], EPS))), "lr": float(np.log(max(p_t[yi], EPS)) - np.log(max(p_o[yi], EPS))),
                "p_wrong": float(p_t[wrong_idx]), "y_wrong": float(yi == wrong_idx),
                "p_correct": float(p_t[0 if truth_is_h1 else 1]), "y_correct": float(yi == (0 if truth_is_h1 else 1)),
                "eliminating": float(yi in (0, 1)), "nn_similarity": r.get("nn_similarity"),
                "nn_aligned": (r.get("nn_class") == r["truth"]) if r.get("nn_class") else None,
                "support_truth": entry["support"][0 if truth_is_h1 else 1]})
    return pd.DataFrame(out)


def _units(frame: pd.DataFrame):
    codes, uniq = pd.factorize(frame["unit"])
    return codes, len(uniq)


def bootstrap_mean(values: np.ndarray, unit_codes: np.ndarray, n_units: int, *, seed: int = SEED,
                   draws: int = DRAWS) -> list[float]:
    sums = np.bincount(unit_codes, weights=values, minlength=n_units)
    counts = np.bincount(unit_codes, minlength=n_units).astype(float)
    index = np.random.default_rng(seed).integers(n_units, size=(draws, n_units))
    boot = sums[index].sum(1) / np.maximum(counts[index].sum(1), 1e-12)
    return np.quantile(boot, [0.025, 0.975]).tolist()


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    idx = np.minimum((p * bins).astype(int), bins - 1)
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(total)


def world_metrics(frame: pd.DataFrame, world: str) -> dict:
    f = frame[frame.world == world]
    if f.empty:
        return {}
    codes, n = _units(f)
    return {"world": world, "items": int(len(f)), "units": int(n),
            "nll": float(f.nll.mean()), "nll_ci": bootstrap_mean(f.nll.to_numpy(), codes, n),
            "discrimination": float(f.lr.mean()), "discrimination_ci": bootstrap_mean(f.lr.to_numpy(), codes, n),
            "brier_wrong": float(((f.p_wrong - f.y_wrong) ** 2).mean()), "ece_wrong": ece(f.p_wrong.to_numpy(), f.y_wrong.to_numpy()),
            "mean_p_wrong": float(f.p_wrong.mean()), "observed_wrong": float(f.y_wrong.mean()),
            "wrong_ratio_observed_over_forecast": float(f.y_wrong.mean() / max(f.p_wrong.mean(), EPS)),
            "brier_correct": float(((f.p_correct - f.y_correct) ** 2).mean())}


def paired_metric(frame: pd.DataFrame, a: str, b: str, metric: str) -> dict:
    """Mean of `metric` for world a minus world b over identical items, unit-clustered."""
    left = frame[frame.world == a].reset_index(drop=True)
    right = frame[frame.world == b].reset_index(drop=True)
    if len(left) != len(right):
        raise ValueError("worlds scored different item sets")
    delta = left[metric].to_numpy() - right[metric].to_numpy()
    codes, n = _units(left)
    return {"a": a, "b": b, "metric": metric, "difference": float(delta.mean()),
            "ci": bootstrap_mean(delta, codes, n), "items": int(len(left)), "units": int(n)}


def strata_table(frame: pd.DataFrame, worlds: list[str], metric: str = "nll") -> list[dict]:
    """Mean `metric` per world within novelty and neighbour-alignment strata."""
    rows = []
    novelty = np.where(frame.nn_similarity.isna(), "no_structure", np.where(frame.nn_similarity < FLOOR, "novel", "familiar"))
    misled = np.where(frame.nn_similarity.isna() | (frame.nn_similarity < FLOOR), "no_close_neighbour",
                      np.where(frame.nn_aligned.fillna(False).astype(bool), "aligned_neighbour", "misled_neighbour"))
    for name, labels in (("novelty", novelty), ("neighbour", misled)):
        for stratum in sorted(set(labels)):
            sub = frame[labels == stratum]
            for w in worlds:
                s = sub[sub.world == w]
                if s.empty:
                    continue
                codes, n = _units(s)
                rows.append({"stratum_family": name, "stratum": stratum, "world": w, "items": int(len(s)), "units": int(n),
                             metric: float(s[metric].mean()), f"{metric}_ci": bootstrap_mean(s[metric].to_numpy(), codes, n),
                             "discrimination": float(s.lr.mean()), "observed_wrong": float(s.y_wrong.mean()),
                             "mean_p_wrong": float(s.p_wrong.mean())})
    return rows


def calibration_curve(frame: pd.DataFrame, world: str, bins: int = 10) -> list[dict]:
    f = frame[frame.world == world]
    if f.empty:
        return []
    p, y = f.p_wrong.to_numpy(), f.y_wrong.to_numpy()
    idx = np.minimum((p * bins).astype(int), bins - 1)
    return [{"bin": b, "n": int((idx == b).sum()), "forecast": float(p[idx == b].mean()), "observed": float(y[idx == b].mean())}
            for b in range(bins) if (idx == b).any()]


def prior_quality(rows: list[dict]) -> dict:
    """Score the retrieved hypothesis prior (`prior_h1` on each item's first row) against the truth."""
    seen, losses, informative, favours, uniform = set(), [], 0, 0, 0
    units = []
    for r in rows:
        p1 = r.get("prior_h1")
        if p1 is None:
            continue
        key = (r["dataset"], r["tier"], r["fold"], r["compound"], r["h1"], r["h2"])
        if key in seen:
            continue
        seen.add(key)
        p_truth = p1 if r["truth"] == r["h1"] else 1.0 - p1
        losses.append(-np.log(max(p_truth, EPS)))
        units.append(f"{r['dataset']}:{r['unit']}")
        if abs(p1 - 0.5) > 0.05:
            informative += 1
            favours += int(p_truth > 0.5)
        uniform += 1
    if not losses:
        return {}
    df = pd.DataFrame({"unit": units, "loss": losses})
    codes, n = _units(df)
    return {"episodes": len(losses), "log_loss": float(np.mean(losses)), "log_loss_ci": bootstrap_mean(np.asarray(losses), codes, n),
            "uniform_log_loss": float(np.log(2.0)), "informative_share": informative / uniform,
            "informative_favours_truth": favours / max(informative, 1)}
