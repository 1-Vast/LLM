"""Which cells to profile when a certified virtual cell fills the rest of a compound x line map."""
from __future__ import annotations

import numpy as np


def _check(open_cells: np.ndarray, kappa: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    open_cells = np.asarray(open_cells, bool)
    kappa = np.asarray(kappa, dtype=float)
    if open_cells.ndim != 2 or kappa.shape != (open_cells.shape[1], open_cells.shape[1]):
        raise ValueError("AXIS_MISMATCH: cells are compounds x lines and kappa is lines x lines")
    return open_cells, kappa


def sparse_transfer_design(open_cells: np.ndarray, kappa: np.ndarray, wells: int, *, seed: int = 0) -> np.ndarray:
    """Up to ``wells`` cells: each pass gives every compound (random order) its best open hub line."""
    open_cells, kappa = _check(open_cells, kappa)
    if type(wells) is not int or wells < 0:
        raise ValueError("wells must be a non-negative integer")
    rng = np.random.default_rng(seed)
    hubs = np.argsort(-kappa.mean(axis=1), kind="stable")
    chosen = np.zeros_like(open_cells)
    while chosen.sum() < wells and (open_cells & ~chosen).any():
        for i in rng.permutation(open_cells.shape[0]):
            if chosen.sum() >= wells:
                break
            free = open_cells[i] & ~chosen[i]
            if free.any():
                chosen[i, next(t for t in hubs if free[t])] = True
    return chosen


def profiling_value(p: np.ndarray, ecos: np.ndarray, rho: np.ndarray, open_cells: np.ndarray, kappa: np.ndarray,
                    gamma: float) -> np.ndarray:
    """Expected map-utility gain of profiling each open cell (-inf for closed cells)."""
    open_cells, kappa = _check(open_cells, kappa)
    p, ecos, rho = (np.asarray(x, dtype=float) for x in (p, ecos, rho))
    if not (p.shape == ecos.shape == rho.shape == open_cells.shape):
        raise ValueError("AXIS_MISMATCH: certificates must be compounds x lines")
    g2 = gamma ** 2
    direct = p * (1 - ecos)
    transfer = np.zeros_like(p)
    for t in range(p.shape[1]):
        e_after = np.sqrt(g2 + np.maximum(rho, kappa[t][None, :]) ** 2 * (1 - g2))
        gain = np.where(open_cells, p * np.clip(e_after - ecos, 0, None), 0.0)
        gain[:, t] = 0.0
        transfer[:, t] = gain.sum(1)
    return np.where(open_cells, direct + transfer, -np.inf)


def plan_batch(p: np.ndarray, ecos: np.ndarray, rho: np.ndarray, open_cells: np.ndarray, kappa: np.ndarray,
               gamma: float, k: int, *, seed: int = 0) -> np.ndarray:
    """Up to ``k`` cells by sequential greedy value; after each pick the compound's certificates are
    raised as if that line had been profiled, so one compound's transfer gain is not counted twice."""
    if type(k) is not int or k < 0:
        raise ValueError("k must be a non-negative integer")
    remaining, kappa = _check(open_cells, kappa)
    remaining = remaining.copy()
    rho = np.array(rho, dtype=float)
    ecos = np.array(ecos, dtype=float)
    chosen = np.zeros_like(remaining)
    jitter = 1e-9 * np.random.default_rng(seed).random(remaining.shape)   # reproducible tie-breaking
    g2 = gamma ** 2
    for _ in range(k):
        v = profiling_value(p, ecos, rho, remaining, kappa, gamma) + jitter
        if not np.isfinite(v).any():
            break
        i, t = np.unravel_index(int(np.argmax(v)), v.shape)
        chosen[i, t] = True
        remaining[i, t] = False
        rho[i] = np.maximum(rho[i], kappa[t])
        ecos[i] = np.maximum(ecos[i], np.sqrt(g2 + rho[i] ** 2 * (1 - g2)))
    return chosen
