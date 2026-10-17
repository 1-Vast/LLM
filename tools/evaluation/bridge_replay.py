"""Equal-query retrospective replay of bridged context transfer on any context x item matrix.

File summary
- Path: tools/evaluation/bridge_replay.py
- Purpose: answer "would the dual core have found more selective hits in held-out contexts at
  this query budget?" for a new domain, from a complete retrospective screen. One query (the
  code's "well") is one archived response summary, such as a 7-dose AUC profile. It uses the
  promoted modules only (`virtual_cell.bridged_transfer`, `agent.bridge_design`,
  `agent.procedure_selection`).
- Core points:
  - Input NPZ keys:
    - ``Y``: contexts x items, lower = stronger effect, NaN = unmeasured;
    - ``X``: contexts x basal features, NaN rows = no features;
    - ``contexts``, ``groups`` (dependence clusters, for example patients) and ``items``.
  - Outer folds are by group (hashed). Each outer fold:
    - fits the Virtual Cell on source contexts;
    - selects rank and procedure by `procedure_selection.select_procedure` on source contexts
      only;
    - grades every arm on held-out contexts against the endpoint of the full matrix.
  - Arms:
    - ``item``: source event rate;
    - ``vc0``: Virtual Cell, no bridge;
    - ``b_exploit`` and ``b_lookahead``: bridged campaigns at the selected rank (``b_lookahead``
      uses the corrected rule; the confirmed study used ``lookahead_v1``);
    - ``selected``: the agent's choice;
    - ``oracle``: the ceiling.
  - Each arm reports its mean hits, wasted queries and assay rounds.
  - A query on an unmeasured pair is spent and is never a hit. This is an archive-query task: the
    model's availability weight is historical archive coverage, not assay feasibility.
  - The selector's inner statistics are heuristics (see `agent.procedure_selection`), and the
    lookahead and event scores are approximations (see `virtual_cell.bridged_transfer`).
  - The selected-procedure comparison is paired over the same held-out contexts. Bootstrap
    intervals are over groups.
  - This is a planning aid on exposed data, not a confirmation.
- Interfaces: `replay(domain, budget, k_bridge, ...)`;
  `python -m tools.evaluation.bridge_replay domain.npz --budget 16 --k-bridge 4 --out replay.json`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from agent.bridge_design import run_campaign
from agent.procedure_selection import ROUNDS, hash_folds, hash_unit, select_procedure
from virtual_cell.bridged_transfer import BridgedTransferModel, selective_events

ARMS = ("item", "vc0", "b_exploit", "b_lookahead", "selected", "oracle")


def _bootstrap(diff, groups, draws=2000, seed=20261017):
    labels, inv = np.unique(np.asarray(groups), return_inverse=True)
    sums, sizes = np.bincount(inv, weights=diff), np.bincount(inv)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(labels), size=(draws, len(labels)))
    boots = sums[pick].sum(1) / sizes[pick].sum(1)
    return [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]


def replay(domain: dict, budget: int, k_bridge: int, abs_gate=None, min_measured: int = 100, impute_iters: int = 15,
           ranks=(5, 10, 20, 40), n_folds: int = 5, salt: str = "bridge-replay") -> dict:
    Y = np.asarray(domain["Y"], dtype=float)
    X = np.asarray(domain["X"], dtype=float)
    contexts, groups, items = (np.asarray(domain[k]) for k in ("contexts", "groups", "items"))
    events, _ = selective_events(Y, abs_gate, min_measured)
    fid = hash_folds(groups, salt, n_folds)
    order = hash_unit(items, "tie")
    rows, choices = [], {}
    for k in range(n_folds):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        if len(tgt) == 0:
            continue
        ch = select_procedure(Y[src], X[src], contexts[src], groups[src], items, budget, k_bridge,
                              abs_gate=abs_gate, min_measured=min_measured, impute_iters=impute_iters,
                              ranks=ranks, by_group=True, salt=f"procedure:{k}")
        choices[k] = ch.as_dict()
        model = BridgedTransferModel(rank=ch.rank, abs_gate=abs_gate, min_measured=min_measured,
                                     impute_iters=impute_iters).fit(Y[src], X[src])
        for c in tgt:
            x = X[c] if np.isfinite(X[c]).all() else None

            def measure(idx, c=c):
                return Y[c, idx]

            rec = {"context": str(contexts[c]), "group": str(groups[c]), "fold": k,
                   "oracle": int(min(budget, events[c].sum()))}
            item_wells = np.argsort(-(model.measured_rate * model.source_event_rate + order * 1e-12))[:budget]
            rec["item"] = int(events[c][item_wells].sum())
            rec["item_wasted"] = int((~np.isfinite(Y[c, item_wells])).sum())
            for arm, rule in (("vc0", None), ("b_exploit", "exploit"), ("b_lookahead", "lookahead")):
                camp = run_campaign(model, x, measure, budget, k_bridge if rule else 0, rule, order)
                rec[arm] = int(events[c][camp.wells].sum())
                rec[arm + "_wasted"] = camp.wasted
            rec["selected"] = rec[ch.procedure]
            rec["selected_rounds"] = ROUNDS[ch.procedure]
            rows.append(rec)
    g = [r["group"] for r in rows]
    out = {"budget": budget, "k_bridge": k_bridge, "contexts": len(rows), "groups": len(set(g)),
           "mean_hits": {a: float(np.mean([r[a] for r in rows])) for a in ARMS},
           "wasted_wells": {a: float(np.mean([r[a + "_wasted"] for r in rows])) for a in ARMS[:4]},
           "selected_rounds": float(np.mean([r["selected_rounds"] for r in rows])), "choices": choices,
           "contrasts": {}}
    for a, b in (("selected", "vc0"), ("selected", "b_exploit"), ("selected", "b_lookahead"), ("vc0", "item")):
        d = np.array([r[a] - r[b] for r in rows], float)
        out["contrasts"][f"{a}-{b}"] = {"mean": float(d.mean()), "ci95_group_bootstrap": _bootstrap(d, g)}
    out["records"] = rows
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("domain", help="NPZ with Y, X, contexts, groups, items")
    ap.add_argument("--budget", type=int, required=True)
    ap.add_argument("--k-bridge", type=int, required=True)
    ap.add_argument("--abs-gate", type=float)
    ap.add_argument("--min-measured", type=int, default=100)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with np.load(a.domain, allow_pickle=False) as z:
        domain = {k: z[k] for k in ("Y", "X", "contexts", "groups", "items")}
    out = replay(domain, a.budget, a.k_bridge, a.abs_gate, a.min_measured)
    Path(a.out).write_bytes((json.dumps(out, indent=1, default=float) + "\n").encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("contexts", "groups", "mean_hits", "selected_rounds", "contrasts")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
