"""Paired increment of a correlation when evidence is added to a prior, with a unit bootstrap.

For each task (for example a drug) the score is ``r(z(prior) + z(extra), outcome) - r(prior, outcome)``,
computed on the units (for example cell lines) where prior, extra and outcome are all finite.
Both terms use the same units, which avoids the unpaired comparison found by verification in
``research/astra/kinetic_horizon_20261010``: there r(prior) used every unit but the combination only
measurable ones. The task mean is bootstrapped by resampling units, not tasks. A task with fewer than
``min_units`` paired units is excluded and named (``TOO_FEW_PAIRED_UNITS``).

The output feeds ``maestro.world_model_value.IncrementEstimate`` (point, lower, upper, units).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

MIN_UNITS = 10


def _z(x: np.ndarray) -> np.ndarray:
    sd = np.std(x)
    return (x - np.mean(x)) / sd if sd > 0 else np.zeros_like(x)


def _r(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _task_increment(prior: np.ndarray, extra: np.ndarray, outcome: np.ndarray) -> float:
    return _r(_z(prior) + _z(extra), outcome) - _r(prior, outcome)


def paired_increment(prior: np.ndarray, extra: np.ndarray, outcome: np.ndarray, *, tasks: Sequence[str] | None = None,
                     n_boot: int = 2000, seed: int = 0, min_units: int = MIN_UNITS) -> dict:
    """``prior``, ``extra`` and ``outcome`` are units x tasks arrays (NaN = unavailable)."""
    prior, extra, outcome = (np.asarray(a, dtype=float) for a in (prior, extra, outcome))
    if not (prior.shape == extra.shape == outcome.shape) or prior.ndim != 2:
        raise ValueError("prior, extra and outcome must be equal-shaped units x tasks arrays")
    n_units, n_tasks = prior.shape
    names = list(tasks) if tasks is not None else [str(j) for j in range(n_tasks)]
    finite = np.isfinite(prior) & np.isfinite(extra) & np.isfinite(outcome)
    kept = [j for j in range(n_tasks) if finite[:, j].sum() >= min_units]
    refused = {names[j]: "TOO_FEW_PAIRED_UNITS" for j in range(n_tasks) if j not in kept}
    if not kept:
        return {"point": None, "lower": None, "upper": None, "units": n_units, "per_task": {}, "refused": refused}

    def stat(rows: np.ndarray) -> float:
        vals = []
        for j in kept:
            rr = rows[finite[rows, j]]
            if len(rr) < 3:
                continue
            vals.append(_task_increment(prior[rr, j], extra[rr, j], outcome[rr, j]))
        return float(np.nanmean(vals)) if vals else float("nan")

    full = np.arange(n_units)
    per_task = {}
    for j in kept:
        rows = full[finite[:, j]]
        base = _r(prior[rows, j], outcome[rows, j])
        per_task[names[j]] = {"units": int(len(rows)), "prior_r": base,
                              "combined_r": base + _task_increment(prior[rows, j], extra[rows, j], outcome[rows, j])}
    rng = np.random.default_rng(seed)
    boots = np.array([stat(rng.integers(0, n_units, n_units)) for _ in range(n_boot)])
    point = stat(full)
    lower, upper = (float(np.nanpercentile(boots, q)) for q in (2.5, 97.5))
    return {"point": point, "lower": min(lower, point), "upper": max(upper, point), "units": int(n_units),
            "tasks_improved": int(sum(v["combined_r"] > v["prior_r"] for v in per_task.values())),
            "per_task": per_task, "refused": refused}
