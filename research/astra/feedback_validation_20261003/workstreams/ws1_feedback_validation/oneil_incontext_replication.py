"""WS1 step 3e: does the in-context (feedback) component replicate on O'Neil's independent repeat batch?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/oneil_incontext_replication.py
- Purpose: for the 315 repeat-batch experiments (21 pairs x 15 lines, re-measured combinations
  AND single agents), compare how well the static prior and the in-context component (posterior
  minus prior, leave-one-out over the line's other primary rows) predict the primary label versus
  the independent repeat label. Slopes are scale-calibrated against the prior's slope, and
  intervals bootstrap the 15 lines (5,000 resamples, seed 20261003).
- Interfaces: run the file with PYTHONPATH="src;.".
- Depends on: numpy, research.certified_discovery (frozen; imported only).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import screens  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig  # noqa: E402


def stats(rows):
    prior, post, prim, rep = np.array(rows).T
    ic = post - prior
    X = np.column_stack([np.ones_like(prior), prior, ic])
    bp = np.linalg.lstsq(X, prim, rcond=None)[0]
    br = np.linalg.lstsq(X, rep, rcond=None)[0]
    return {
        "r_prior_primary": np.corrcoef(prior, prim)[0, 1], "r_prior_repeat": np.corrcoef(prior, rep)[0, 1],
        "r_post_primary": np.corrcoef(post, prim)[0, 1], "r_post_repeat": np.corrcoef(post, rep)[0, 1],
        "gain_r_primary": np.corrcoef(post, prim)[0, 1] - np.corrcoef(prior, prim)[0, 1],
        "gain_r_repeat": np.corrcoef(post, rep)[0, 1] - np.corrcoef(prior, rep)[0, 1],
        "coef_prior_primary": bp[1], "coef_ic_primary": bp[2], "coef_prior_repeat": br[1], "coef_ic_repeat": br[2],
        "ic_transfer_ratio": (br[2] / br[1]) / (bp[2] / bp[1]),
    }


def main() -> int:
    lib = load_library(CACHE / "oneil_v1.npz")
    _, experiments = screens._oneil_experiments()
    di = {n: i for i, n in enumerate(lib.drugs)}
    li = {n: i for i, n in enumerate(lib.lines)}
    key = {(int(a), int(b), int(c)): k for k, (a, b, c) in enumerate(zip(lib.a, lib.b, lib.c))}
    repeat = defaultdict(list)
    for e in experiments:
        if e["batch"] == "3" and e["y"] is not None:
            i, j = sorted((di[e["a"]], di[e["b"]]))
            repeat[key[(i, j, li[e["line"]])]].append(e["y"])
    by_line = defaultdict(list)
    for c in sorted({int(lib.c[r]) for r in repeat}):
        world = TransferWorld(lib, c, WorldConfig())
        truth = lib.y[world.rows]
        pos = {int(r): k for k, r in enumerate(world.rows)}
        for r in [r for r in repeat if lib.c[r] == c]:
            k = pos[r]
            others = np.delete(np.arange(world.rows.size), k)
            mean, _ = world.posterior(others, truth[others])
            by_line[c].append((world.prior_target[k], mean[k], lib.y[r], np.mean(repeat[r])))
    allrows = [x for v in by_line.values() for x in v]
    point = {k: round(float(v), 3) for k, v in stats(allrows).items()}
    rng = np.random.default_rng(20261003)
    keys = sorted(by_line)
    draws = defaultdict(list)
    for _ in range(5000):
        pick = rng.integers(0, len(keys), len(keys))
        s = stats([x for i in pick for x in by_line[keys[i]]])
        for k, v in s.items():
            draws[k].append(v)
    ci = {k: [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)] for k, v in draws.items()}
    out = {"n": len(allrows), "lines": len(keys), "point": point, "ci_bootstrap_lines": ci,
           "reading": "ic_transfer_ratio = (repeat coefficient of the in-context component / repeat coefficient of the prior) "
                      "divided by the same ratio on the primary label; 1 = the feedback component replicates as well as the "
                      "history prior, 0 = it does not replicate at all. V is a synergy-enriched, pair-selected block."}
    (HERE / "receipts" / "step3e_incontext_replication.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
