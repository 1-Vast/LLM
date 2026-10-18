"""Build a `Campaign` from an exposed PRISM fold (construction only; no outcome is read here).

File summary
- Path: research/observable_state_20261018/real_adapter.py
- `build_campaign(fold, camp_idx)`: prior mean `fold.prior`, covariance `V V^T + diag(D)` of the repository World, probe
  noise variance `world.s2` (scalar; the oracle's noise is heteroscedastic, the same simplification the predecessor used),
  contexts = pools in the fixed A-optimal order (`bench.pool_order`), admissible lines `fold.avail`.
- `observe_for(fold, oracle, idx)`: wraps `Oracle.observe` for campaign-local compound ids.
- `truth_for(fold, idx)`: the hidden event matrix, for the GRADER only. Never pass it to a policy or to the agent.
- Importing this module puts the feedback-propagation and indication-triage studies on sys.path (read-only reuse).
- Running a campaign with this adapter on any fold is Phase 1/2 work and follows the protocol's role gating.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FP = HERE.parent / "feedback_propagation_20261018"
sys.path.insert(0, str(FP))
import bench  # noqa: E402

from campaign import Campaign  # noqa: E402


def build_campaign(fold, camp_idx, *, reads_per_compound=3, rounds=3, max_contexts=None) -> tuple:
    idx = np.asarray(camp_idx, int)
    W = fold.world
    S = W.V @ W.V.T + np.diag(W.D)
    order = bench.pool_order(fold)
    pools = order if max_contexts is None else order[:max_contexts]
    contexts = [bench.pool_lines(fold, p) for p in pools]
    camp = Campaign(m0=fold.prior[idx].copy(), S=S, noise_var=float(W.s2), contexts=contexts, avail=fold.avail.copy(),
                    G=np.asarray(fold.G, float), reads_per_compound=reads_per_compound, rounds=rounds, seed_context=0)
    return camp, list(range(len(contexts)))


def observe_for(oracle, idx):
    idx = np.asarray(idx, int)

    def f(i, lines):
        return oracle.observe(int(idx[i]), lines)

    return f


def truth_for(fold, camp_idx):
    return fold.hidden.truth[np.asarray(camp_idx, int)]
