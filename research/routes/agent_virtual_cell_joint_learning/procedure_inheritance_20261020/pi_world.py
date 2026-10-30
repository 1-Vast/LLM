"""Synthetic development worlds (generator fixed before any scored run; none is a model of real pharmacology).

P = 66 drug-pair units. Each background has a public reference a (monotherapy-style prediction) and a hidden truth T = a + kappa*L_regime + eta.
Reads return T + 0.02*z with a fixed noise table, so the SAME read of the same pair in the same background is identical for every arm.
A released background is fully measured (its whole recorded vector is available to learning); a task background is only readable through queries.

Kinds (regime structure):
  alias   regimes 1,2 share marker pair m1, regimes 3,4 share marker m2; each regime also lifts its own 6-pair effect set. Two-level identification is possible.
  chain   four regimes with disjoint effect sets and no shared marker; identification is a sequential decision list.
  novel   as alias, but batch 4 contains a regime 5 that was never released before (tests the unknown exit).
  null    no regime effect at all (false-positive control).
Schedule: H0 = 8 released backgrounds (regimes 0,1,2); batch 1 introduces regime 3 (x2), batch 2 regime 4 (x2); batches 3,4 mix all; A_old = 4 never-released
backgrounds per checkpoint drawn from the oldest regimes (retention anchors).
"""
from __future__ import annotations

import numpy as np

P = 66
N_DRUG = 12
NOISE_M = 0.02
ETA = 0.03
NUIS = 0.04
KINDS = ("alias", "chain", "novel", "null")


def _pairs():
    return [(i, j) for i in range(N_DRUG) for j in range(i + 1, N_DRUG)]


def make_stream(kind: str, seed: int):
    assert kind in KINDS
    rng = np.random.default_rng(seed)
    perm = rng.permutation(P)
    base = rng.uniform(0.2, 0.6, P)
    sets = {r: perm[6 * (r - 1):6 * r] for r in range(1, 6)}
    markers = {1: int(perm[30]), 2: int(perm[31]), 3: int(perm[32])}
    prof = {0: np.zeros(P)}
    for r in range(1, 6):
        v = np.zeros(P)
        v[sets[r]] = rng.uniform(0.30, 0.45, 6)
        prof[r] = v
    if kind in ("alias", "novel"):
        prof[1][markers[1]] = prof[2][markers[1]] = 0.35
        prof[3][markers[2]] = prof[4][markers[2]] = 0.35
        prof[5][markers[3]] = 0.35
    if kind == "null":
        prof = {r: np.zeros(P) for r in prof}
    sched_rng = np.random.default_rng(seed + 7919)

    def draw(allowed, forced=()):
        lst = list(forced) + [int(x) for x in sched_rng.choice(allowed, 4 - len(forced))]
        return [int(x) for x in sched_rng.permutation(lst)]

    h0 = [0, 1, 2, 1, 2, 0, 1, 2]
    batches_reg = [draw([0, 1, 2], (3, 3)), draw([0, 1, 2, 3], (4, 4)), draw([0, 1, 2, 3, 4]), draw([0, 1, 2, 3, 4])]
    if kind == "novel":
        batches_reg[3] = draw([0, 1, 2, 3, 4], (5, 5))
    anchors_reg = [[int(x) for x in sched_rng.permutation([0, 1, 2, 1])] for _ in range(4)]
    regs = h0 + [r for b in batches_reg for r in b] + [r for b in anchors_reg for r in b]
    n_bg = len(regs)
    bgs = {}
    for i, r in enumerate(regs):
        g = np.random.default_rng([seed, 1000 + i])
        a = base + g.normal(0, NUIS, P)
        kappa = g.uniform(0.7, 1.1)
        T = a + kappa * prof[r] + g.normal(0, ETA, P)
        z = g.standard_normal(P)
        bgs[i] = {"regime": r, "a": a, "T": T, "y": T + NOISE_M * z}
    ids = list(range(n_bg))
    sched = {"H0": ids[:8], "batches": [ids[8 + 4 * b:12 + 4 * b] for b in range(4)], "A_old": [ids[24 + 4 * b:28 + 4 * b] for b in range(4)]}
    return {"kind": kind, "seed": seed, "P": P, "pairs": _pairs(), "bgs": bgs, "schedule": sched}


def public(stream, i):
    return stream["bgs"][i]["a"]


def released_residuals(stream, ids):
    """Fully measured released backgrounds: (E, A, Y) with E = recorded read - public reference. Uses only the ids it is given."""
    A = np.stack([stream["bgs"][i]["a"] for i in ids])
    Y = np.stack([stream["bgs"][i]["y"] for i in ids])
    return Y - A, A, Y
