"""WS3: does peeking at the fixed-sample hypergeometric yield bound and stopping early break coverage?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/optional_stopping.py
- Purpose: the frozen certificate computes its yield bound once, after a fixed-size audit. This
  simulation asks what happens if a user instead inspects the same bound after every audited
  item (or after each of a few audit batches) and stops at the first favourable value.
- Core points: exact frozen bound (research.certified_discovery.certify.yield_lower_bound);
  labels fixed per run, audit order uniformly random; coverage = bound <= hits left untested at
  the stopping time. Simulation only: it can show a failure, it cannot prove validity.
- Run: D:/anaconda/envs/maestro/python.exe research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/optional_stopping.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4]))
from research.certified_discovery import certify as cert  # noqa: E402

DELTA = 0.1
_B: dict = {}


def bound(N, t, x):
    if (N, t, x) not in _B:
        _B[(N, t, x)] = cert.yield_lower_bound(N, t, x, DELTA)
    return _B[(N, t, x)]


def simulate(N, K, target, looks, reps, rng):
    """looks: audit sizes at which the bound is inspected; the last is the fixed design size."""
    fixed = stop = early = 0
    for _ in range(reps):
        labels = np.zeros(N, bool)
        labels[rng.choice(N, K, replace=False)] = True
        cum = np.cumsum(labels[rng.permutation(N)])
        claim = None
        for t in looks:
            x = int(cum[t - 1])
            b = bound(N, t, x)
            if t == looks[-1]:
                fixed += b <= K - x
            if claim is None and (b >= target or t == looks[-1]):
                claim = b <= K - x
                early += t < looks[-1]
        stop += claim
    return {"N": N, "K": K, "target": target, "looks": "every item" if len(looks) > 10 else looks, "reps": reps,
            "fixed_sample_coverage": fixed / reps, "optional_stopping_coverage": stop / reps, "stopped_early": early / reps}


def main() -> int:
    rng = np.random.default_rng(7)
    rows = []
    for N in (32, 64, 256):
        half = N // 2
        every = list(range(1, half + 1))
        batches = [half // 4, half // 2, 3 * half // 4, half]
        for K in sorted({2, 4, 8, max(2, N // 8), max(2, N // 4)}):
            for target in sorted({1, 2, max(1, K // 4), max(1, K // 3), max(1, K // 2)}):
                for looks in (every, batches):
                    rows.append(simulate(N, K, target, looks, 3000, rng))
    worst = min(rows, key=lambda r: r["optional_stopping_coverage"])
    below = [r for r in rows if r["optional_stopping_coverage"] < 1 - DELTA]
    out = {"delta": DELTA, "configs": len(rows), "worst": worst, "configs_below_nominal": len(below),
           "below_nominal": below, "all": rows}
    (HERE / "optional_stopping.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"configs": len(rows), "worst": worst, "configs_below_nominal": len(below)}, indent=1))
    for r in sorted(below, key=lambda r: r["optional_stopping_coverage"])[:8]:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
