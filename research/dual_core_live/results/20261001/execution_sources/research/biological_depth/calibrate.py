"""Cross-conformal interval check for a served rung, as written in calibration_spec.json.

File summary
- Path: research/biological_depth/calibrate.py
- Purpose: decide whether an arm's served readouts may carry CALIBRATED intervals, by checking
  cross-conformal coverage on held-out compound folds, and produce the serving table.
- Core points:
  - Residual quantiles for fold k come only from the other folds' out-of-fold residuals.
  - Strata are line x dose x structural novelty, so a novel compound is calibrated on novel ones.
  - A stratum too small for its finite-sample quantile falls back to the line x novelty pool,
    and the fallback is counted.
- Run: python research/biological_depth/calibrate.py --prepared <dir> --cv <dir> --arm <arm> --output <dir>
- Depends on: audit.py, common.py, models.py
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import common
from audit import Audit
from models import morgan, tanimoto

LEVEL = 0.8
MIN_GENES = 15
NOVELTY = 0.4


def conformal_quantile(residuals: np.ndarray, level: float = LEVEL) -> float | None:
    n = len(residuals)
    rank = math.ceil((n + 1) * level)
    return float(np.sort(residuals)[rank - 1]) if 0 < rank <= n else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    a = Audit(args.prepared, args.cv)
    pred, y = a.pred[args.arm], a.y
    sets = {name: [a.symbol_index[g] for g in genes if g in a.symbol_index]
            for name, genes in a.gene_sets.items()}
    sets = {name: idx for name, idx in sets.items() if len(idx) >= MIN_GENES}
    readouts = {"transcript_shift_norm": (lambda m: np.linalg.norm(m, axis=1))}
    for name, idx in sets.items():
        readouts[f"hallmark:{name}"] = (lambda i: (lambda m: m[:, i].mean(1)))(np.asarray(idx))
    values = {r: (fn(pred), fn(y)) for r, fn in readouts.items()}

    compounds = a.compounds
    fps = morgan(compounds.smiles.tolist(), 2048)
    folds = compounds.fold.to_numpy()
    similarity = tanimoto(fps, fps)
    novelty = {}
    for i, c in enumerate(compounds.index):
        others = folds != folds[i]
        novelty[c] = bool(similarity[i, others].max() >= NOVELTY)
    cond = a.conditions
    in_dist = cond.compound.map(novelty).to_numpy()
    fold_of = cond.fold.to_numpy()
    strata = np.array([f"{l}|{d:g}|{'in' if n else 'novel'}" for l, d, n in zip(cond.cell_line, cond.dose, in_dist)])
    pool = np.array([f"{l}|{'in' if n else 'novel'}" for l, n in zip(cond.cell_line, in_dist)])

    coverage, widths, fallbacks = {}, {}, 0
    covered_by_novelty = {"in": [], "novel": []}
    for r, (p, o) in values.items():
        hits, width = np.zeros(len(y), dtype=bool), np.zeros(len(y))
        residual = np.abs(p - o)
        for k in range(5):
            test = fold_of == k
            calib = ~test
            for s in np.unique(strata[test]):
                rows = test & (strata == s)
                q = conformal_quantile(residual[calib & (strata == s)])
                if q is None:
                    q = conformal_quantile(residual[calib & (pool == s.rsplit("|", 2)[0] + "|" + s.rsplit("|", 1)[1])])
                    fallbacks += 1
                hits[rows] = residual[rows] <= q
                width[rows] = 2 * q
        coverage[r] = float(hits.mean())
        widths[r] = float(width.mean())
        for flag in (True, False):
            covered_by_novelty["in" if flag else "novel"].append(float(hits[in_dist == flag].mean()))
    mean_cov = float(np.mean(list(coverage.values())))
    share = float(np.mean([v >= 0.70 for v in coverage.values()]))
    passed = 0.75 <= mean_cov <= 0.90 and share >= 0.90
    # Serving table: quantiles over all out-of-fold residuals, per readout and stratum.
    table = {}
    for r, (p, o) in values.items():
        residual = np.abs(p - o)
        table[r] = {s: conformal_quantile(residual[strata == s]) for s in np.unique(strata)}
    report = {"arm": args.arm, "level": LEVEL, "readouts": len(values), "novelty_threshold": NOVELTY,
              "in_distribution_conditions": int(in_dist.sum()), "novel_conditions": int((~in_dist).sum()),
              "mean_coverage": mean_cov, "share_readouts_at_or_above_0.70": share,
              "coverage_in_distribution": float(np.mean(covered_by_novelty["in"])),
              "coverage_novel": float(np.mean(covered_by_novelty["novel"])),
              "stratum_fallbacks": fallbacks, "passed": bool(passed),
              "coverage": coverage, "mean_width": widths}
    common.write_json(args.output / f"calibration_{args.arm}.json", report)
    common.write_json(args.output / f"serving_quantiles_{args.arm}.json",
                      {"level": LEVEL, "strata": "line|dose_nM|in or novel", "quantiles": table,
                       "gene_sets": {name: [a.genes.symbol[i] for i in idx] for name, idx in sets.items()}})
    print(json.dumps({k: v for k, v in report.items() if k not in ("coverage", "mean_width")}, indent=1))


if __name__ == "__main__":
    main()
