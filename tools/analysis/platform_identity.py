"""Cross-platform feature-axis identity check before a world model is fed another platform's cells.

Each line shared by a reference platform (the model's training data, on the model's input axis)
and a query platform (projected onto that axis) should be most similar to itself. Profiles are
centred across lines within each platform. For every shared query line, the check ranks the true
reference line among all reference lines by Pearson correlation. The null permutes the feature
order of the reference profiles.

Passing establishes that the projected axis and the line identities agree. It does **not**
establish that perturbation responses transport. In ``research/astra/kinetic_horizon_20261010``,
MIX-Seq control profiles matched their Tahoe line 18 of 18 times (null top-1 rate 0.03). Yet the
same lines' observed drug-response deviations agreed only at r of 0.13 or less across the two
platforms, and frozen STATE forecasts had no line-specific skill there.
Refusals: ``TOO_FEW_SHARED_LINES``; ``AXIS_IDENTITY_FAILED``.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np

MIN_SHARED = 5
MIN_TOP1 = 0.8


def identity_test(reference: Mapping[str, np.ndarray], query: Mapping[str, np.ndarray], *, n_null: int = 200,
                  seed: int = 0, min_shared: int = MIN_SHARED, min_top1: float = MIN_TOP1) -> dict:
    ref_ids = sorted(reference)
    shared = sorted(set(ref_ids) & set(query))
    if len(shared) < min_shared:
        return {"passed": False, "refusal": "TOO_FEW_SHARED_LINES", "shared": len(shared)}
    R = np.array([np.asarray(reference[i], dtype=float) for i in ref_ids])
    Q = np.array([np.asarray(query[i], dtype=float) for i in sorted(query)])
    if R.shape[1] != Q.shape[1]:
        raise ValueError("reference and query profiles must share one feature axis")
    R = R - R.mean(0)
    Qc = Q - Q.mean(0)
    qpos = {i: k for k, i in enumerate(sorted(query))}

    def top1(Rm: np.ndarray) -> tuple[float, list]:
        Rn = (Rm - Rm.mean(1, keepdims=True)) / (Rm.std(1, keepdims=True) + 1e-12)
        ranks = []
        for i in shared:
            q = Qc[qpos[i]]
            qn = (q - q.mean()) / (q.std() + 1e-12)
            sims = Rn @ qn / len(qn)
            ranks.append(int((sims > sims[ref_ids.index(i)]).sum()) + 1)
        return float(np.mean(np.array(ranks) == 1)), ranks

    observed, ranks = top1(R)
    rng = np.random.default_rng(seed)
    null = np.array([top1(R[:, rng.permutation(R.shape[1])])[0] for _ in range(n_null)])
    passed = bool(observed >= min_top1 and observed > np.quantile(null, 0.99))
    return {"passed": passed, "refusal": None if passed else "AXIS_IDENTITY_FAILED", "shared": len(shared),
            "top1": observed, "ranks": dict(zip(shared, ranks)), "null_top1_mean": float(null.mean()),
            "null_top1_q99": float(np.quantile(null, 0.99))}
