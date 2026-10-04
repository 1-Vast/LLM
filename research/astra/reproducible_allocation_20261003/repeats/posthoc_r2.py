"""Correction receipt: what the registered post-hoc 'cross-orientation R^2' computed (EXPLORATORY).

File summary
- Path: research/astra/reproducible_allocation_20261003/repeats/posthoc_r2.py
- Purpose: recompute, line by line, the statistic of the frozen
  `feedback_validation_20261003/posthoc_mechanism.py` (SV drug-in-line effects predicting the VS
  residuals) and place next to it (a) the squared-error R^2 about the residual mean,
  1 - SSE / SST, and (b) the skill against no correction, 1 - SSE / sum(res^2). The registered code
  used 1 - var(res - fitted) / var(res), which ignores the mean error (an explained-variance ratio):
  SSE/n = var(e) + mean(e)^2, so variance-ratio = squared-error R^2 + mean(e)^2 / var(res).
- Core points:
  - Uses the frozen `effects` function and the frozen TransferWorld (context off); imported unchanged.
  - Outcome access only after `exposed_ticket` (EXPLORATORY).
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.repeats.posthoc_r2`
  writes `repeats/receipts/posthoc_r2_check.json` (refuses to overwrite).
- Depends on: numpy; frozen feedback-validation modules; `..common.exposed_ticket`.
"""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

from research.astra.feedback_validation_20261003 import jaaks
from research.astra.feedback_validation_20261003.posthoc_mechanism import effects
from research.astra.feedback_validation_20261003.study import WORLD
from research.certified_discovery.world import TransferWorld

HERE = Path(__file__).resolve().parent
TARGET = HERE / "receipts" / "posthoc_r2_check.json"
REGISTERED = HERE.parents[1] / "feedback_validation_20261003" / "results" / "posthoc_mechanism.json"
_P: dict = {}


def statistics(res: np.ndarray, fitted: np.ndarray) -> dict:
    e = res - fitted
    sse, sst, ss0 = float(e @ e), float(((res - res.mean()) ** 2).sum()), float(res @ res)
    var_ratio = 1.0 - np.var(e) / np.var(res) if np.var(res) > 0 else np.nan
    return {"registered_variance_ratio": float(var_ratio),
            "squared_error_r2": 1.0 - sse / sst if sst > 0 else np.nan,
            "skill_vs_no_correction": 1.0 - sse / ss0 if ss0 > 0 else np.nan,
            "mean_error_sq_over_var": float(e.mean() ** 2 / np.var(res)) if np.var(res) > 0 else np.nan}


def _init(panels) -> None:
    global _P
    _P = panels


def _line(args: tuple[str, int]) -> dict:
    tissue, line = args
    sv, vs = _P[f"{tissue}_SV"], _P[f"{tissue}_VS"]
    w1, w2 = TransferWorld(sv.library, line, WORLD), TransferWorld(vs.library, line, WORLD)
    e1, res1, _ = effects(w1)
    e2, res2, _ = effects(w2)
    cross = statistics(res2, w2.Z_target[:, 1:] @ e1)
    in_sv = statistics(res1, w1.Z_target @ np.r_[0.0, e1] + _offset(w1))
    return {"tissue": tissue, "line": sv.library.lines[line], "cross": cross, "in_sample_sv": in_sv}


def _offset(world: TransferWorld) -> np.ndarray:
    """In-sample fitted values of the registered `effects` include the line offset (column 0)."""
    rows = world.rows
    resid = world.lib.y[rows] - world.prior_target
    Z = world.Z_target
    cov = np.linalg.inv(world.A_inv + Z.T @ Z / world.s_noise)
    eff = cov @ (Z.T @ resid) / world.s_noise
    return Z[:, :1] @ eff[:1]


def main() -> int:
    from ..common import exposed_ticket

    if TARGET.exists():
        raise FileExistsError("NO_OVERWRITE: posthoc_r2_check.json")
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    ticket = exposed_ticket("post-hoc R^2 correction receipt: recompute posthoc_mechanism cross-orientation "
                            "statistic and squared-error R^2", "repeats")
    panels, _, _ = jaaks.build_panels(ticket)
    tasks = [(t, i) for t in ("Breast", "Colon", "Pancreas") for i in range(len(panels[f"{t}_SV"].library.lines))]
    with ProcessPoolExecutor(max_workers=20, initializer=_init, initargs=(panels,)) as pool:
        rows = list(pool.map(_line, tasks))
    registered = json.loads(REGISTERED.read_text(encoding="utf-8"))["tissues"]
    tissues = {}
    for t in ("Breast", "Colon", "Pancreas"):
        rs = [r for r in rows if r["tissue"] == t]
        med = {k: float(np.nanmedian([r["cross"][k] for r in rs])) for k in rs[0]["cross"]}
        med_in = {k: float(np.nanmedian([r["in_sample_sv"][k] for r in rs])) for k in rs[0]["in_sample_sv"]}
        tissues[t] = {"lines": len(rs), "median_cross_orientation": med, "median_in_sample_sv": med_in,
                      "registered_median_cross_orientation_r2": registered[t]["median_cross_orientation_r2"],
                      "registered_median_in_sample_r2_SV": registered[t]["median_in_sample_r2_SV"],
                      "reproduces_registered_cross": bool(abs(med["registered_variance_ratio"]
                                                              - registered[t]["median_cross_orientation_r2"]) < 1e-9),
                      "reproduces_registered_in_sample": bool(abs(med_in["registered_variance_ratio"]
                                                                  - registered[t]["median_in_sample_r2_SV"]) < 1e-9)}
    receipt = {
        "label": "EXPLORATORY correction receipt (exposed data)", "started": started,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ticket": ticket,
        "what_registered_code_computed": "1 - np.var(res - fitted) / np.var(res) (posthoc_mechanism.py, both the "
                                         "in-sample and the cross-orientation 'R2'): np.var subtracts the mean, so "
                                         "this is an explained-variance ratio that ignores the mean error; it is "
                                         "not the squared-error R^2",
        "identity": "variance_ratio = squared_error_r2 + mean(e)^2 / var(res), with e = res - fitted",
        "definitions": {"squared_error_r2": "1 - sum((res - fitted)^2) / sum((res - mean(res))^2)",
                        "skill_vs_no_correction": "1 - sum((res - fitted)^2) / sum(res^2): improvement over "
                                                  "predicting the VS label by its prior alone (fitted = 0)"},
        "tissues": tissues,
        "per_line": rows,
        "note": "The registered drug-effect correlations compare shrunken posterior estimates; with the bipartite "
                "S x V menu the drug effects are identified only up to a constant shift between the S and V sets, "
                "so these correlations are not correlations of physical drug effects.",
        "seconds": round(time.perf_counter() - t0, 1),
    }

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, float) and not np.isfinite(o):
            return None
        return o

    TARGET.write_text(json.dumps(clean(receipt), indent=1), encoding="utf-8")
    print(json.dumps(clean(tissues), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
