"""Selector variant A (development round 2, superseded; kept so its disclosed runs reproduce).

File summary
- Path: research/context_transfer_20261017/procedure_variant_a.py
- Purpose: the first source-verified selector. Rank and procedure were chosen jointly by the
  highest inner mean hits over a menu of {no bridge, exploit-first, lookahead, lookahead with
  model-averaged repair} x rank; any strictly positive bridge gain switched to a bridge.
- Core points:
  - Superseded by procedure.py ("evidence" rule) after the AML-shaped proxy showed that this rule
    follows inner noise (choices flip between folds; the selector fell below a fixed Virtual Cell).
  - Used only by power.py configurations `v1_auto_w16_b4`, `v2_auto_w16_b4`, `s_v2_auto_w16_b4`.
- Interfaces: `auto_records(domain, fid, budget, k_bridge, abs_gate, min_measured, impute_iters)`.
"""
from __future__ import annotations

import numpy as np

import replay
from procedure import _inner_split, inner_domain

RANKS = (5, 10, 20, 40)
ROUNDS = {"vc0": 1, "b_exploit": 2, "maestro": 2, "maestro_bma": 2}
INF = float("inf")
MENU = ("vc0", "b_exploit", "maestro", "maestro_bma")


def _run(domain, budget, k_bridge, rank, fid, filt, abs_gate, min_measured, impute_iters):
    return replay.run(domain, budget, k_bridge, arms=("vc0", "b_exploit", "maestro"), rank=rank,
                      repair_threshold=INF, abs_gate=abs_gate, min_measured=min_measured,
                      maestro_rule="lookahead", fold_ids=fid, context_filter=filt,
                      repair_grid=(INF,), impute_iters=impute_iters)


def select(domain, src, budget, k_bridge, abs_gate, min_measured, impute_iters=0, salt="procedure"):
    inner = inner_domain(domain, src, abs_gate, min_measured)
    fid, filt = _inner_split(inner, False, None, salt)
    table = {}
    for r in RANKS:
        recs = _run(inner, budget, k_bridge, r, fid, filt, abs_gate, min_measured, impute_iters)
        table[r] = {p: float(np.mean([x[p] for x in recs])) for p in MENU}
    flat = [(table[r][p], r, p) for r in RANKS for p in MENU]
    best_none = max((v, -r, r, p) for v, r, p in flat if ROUNDS[p] == 1)
    best_bridge = max((v, -r, r, p) for v, r, p in flat if ROUNDS[p] == 2)
    pick = best_bridge if best_bridge[0] > best_none[0] else best_none
    return {"rank": int(pick[2]), "procedure": pick[3], "inner_mean_hits": table,
            "bridge_gain_inner": float(best_bridge[0] - best_none[0])}


def auto_records(domain, fid, budget, k_bridge, abs_gate, min_measured, impute_iters=0):
    out, choices = {}, {}
    for k in sorted(set(fid.tolist())):
        src = np.flatnonzero(fid != k)
        ch = select(domain, src, budget, k_bridge, abs_gate, min_measured, impute_iters, salt=f"procedure:{k}")
        choices[int(k)] = ch
        for r in _run(domain, budget, k_bridge, ch["rank"], fid, fid == k, abs_gate, min_measured, impute_iters):
            out[r["context"]] = {"auto": r[ch["procedure"]], "auto_procedure": ch["procedure"],
                                 "auto_rank": ch["rank"], "auto_rounds": ROUNDS[ch["procedure"]]}
    return out, choices
