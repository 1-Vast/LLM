"""EXPLORATORY follow-up (after the verdict): screening versus verification at matched measurements.

File summary
- Path: research/astra/feedback_validation_20261003/followup_verification.py
- Purpose: the registered result showed that feedback raises screen calls but not validated
  discoveries. A lab cannot see the validation call unless it pays for it. This follow-up asks how
  a fixed number of measurements per line should be split between screening new pairs and
  verifying screen hits (measuring the same pair again in the other orientation, on disjoint
  plates), and whether feedback ranking helps once verification is paid for.
- Core points:
  - Jaaks panels are already opened by the registered run: EXPLORATORY; the plan
    (`receipts/followup_verification_plan.json`) is written before the run.
  - Budget: M = ceil(0.20 x menu) measurements per line in 4 rounds (the primary wells).
  - Policies (ranking = static history_mean or feedback posterior on screen labels only):
    `screen_only` (no verification), `verify_hits` (each round first verifies earlier
    unverified screen hits, then screens new pairs; the last round verifies first),
    `paired` (every purchase measures both orientations; half as many pairs).
  - Endpoint: verified discoveries = pairs measured in both orientations and synergistic in both.
    Also reported: hidden validated discoveries among screen hits (what a screen-only claim
    would be worth) and measurements spent on verification.
- Interfaces: `python -m research.astra.feedback_validation_20261003.followup_verification`.
- Depends on: numpy; study, jaaks, run, verdict (bootstrap), frozen TransferWorld.
"""
from __future__ import annotations

import json
import math
import time

import numpy as np

from research.certified_discovery import agent
from research.certified_discovery.world import TransferWorld

from .jaaks import RELEASE, build_panels
from .run import FREEZE, HERE, ROOT, VAULT_LOG
from .study import WORLD, Posterior
from .verdict import contrast

PLAN = HERE / "receipts/followup_verification_plan.json"
FRACTION, ROUNDS = 0.20, 4


def policy_run(world: TransferWorld, panel, rank: str, mode: str, seed: int) -> dict:
    rows = world.rows
    n = rows.size
    total = int(math.ceil(FRACTION * n))
    batch = int(math.ceil(total / ROUNDS))
    y = world.lib.y[rows]
    screen = panel.screen_hit[rows]
    valid = panel.valid_hit[rows]
    post = Posterior(world)
    rng = np.random.default_rng(seed)
    screened = np.zeros(n, bool)
    verified = np.zeros(n, bool)
    spent = verify_spent = 0
    for r in range(ROUNDS):
        budget = min(batch, total - spent)
        idx = np.flatnonzero(screened)
        scores = world.X_target[:, 0] if rank == "static" else post.predict(idx, y[idx], "full")
        if mode == "verify_hits":
            todo = np.flatnonzero(screened & screen & ~verified)
            todo = todo[np.argsort(-y[todo], kind="stable")][:budget]
            verified[todo] = True
            budget -= todo.size
            spent += todo.size
            verify_spent += todo.size
        if budget <= 0:
            continue
        if mode == "paired":
            k = budget // 2
            if k == 0:
                continue
            chosen = agent._top(scores, ~screened, k, rng)
            screened[chosen] = True
            verified[chosen] = True
            spent += 2 * k
            verify_spent += k
        else:
            chosen = agent._top(scores, ~screened, budget, rng)
            screened[chosen] = True
            spent += budget
    return {"measurements": int(spent), "verification_measurements": int(verify_spent),
            "pairs_screened": int(screened.sum()), "screen_hits": int((screened & screen).sum()),
            "verified_discoveries": int((verified & screen & valid).sum()),
            "hidden_validated_among_screen_hits": int((screened & screen & valid).sum())}


def main() -> int:
    from tools.datasets.combination_screens import open_vault

    if not PLAN.exists():
        raise SystemExit("write the plan first")
    ticket = open_vault(FREEZE, VAULT_LOG, purpose="EXPLORATORY follow-up: screening vs verification (after verdict)",
                        source=RELEASE, root=ROOT)
    panels, _, _ = build_panels(ticket, RELEASE)
    started = time.time()
    arms = [(rank, mode) for rank in ("static", "feedback") for mode in ("screen_only", "verify_hits", "paired")]
    units: dict = {}
    for name, panel in panels.items():
        for line in range(len(panel.library.lines)):
            world = TransferWorld(panel.library, line, WORLD)
            key = (panel.stratum, panel.library.lines[line])
            slot = units.setdefault(key, {f"{a}_{m}": [] for a, m in arms})
            for rank, mode in arms:
                slot[f"{rank}_{mode}"].append(policy_run(world, panel, rank, mode, line))
    keys = sorted(units)
    strata = np.array([k[0] for k in keys])
    fields = ("measurements", "verification_measurements", "pairs_screened", "screen_hits", "verified_discoveries",
              "hidden_validated_among_screen_hits")
    table = {arm: {f: np.array([np.mean([r[f] for r in units[k][arm]]) for k in keys]) for f in fields}
             for arm in units[keys[0]]}
    out = {"status": "EXPLORATORY follow-up on opened Jaaks panels (after the registered verdict)", "ticket": ticket,
           "units": len(keys), "totals": {a: {f: float(v[f].sum()) for f in fields} for a, v in table.items()},
           "contrasts": {}, "wall_seconds": round(time.time() - started, 1)}
    v = {a: table[a]["verified_discoveries"] for a in table}
    out["contrasts"]["static_verify_hits_minus_static_paired"] = contrast(v["static_verify_hits"], v["static_paired"], strata)
    out["contrasts"]["feedback_verify_hits_minus_static_verify_hits"] = contrast(v["feedback_verify_hits"],
                                                                                  v["static_verify_hits"], strata)
    out["contrasts"]["feedback_paired_minus_static_paired"] = contrast(v["feedback_paired"], v["static_paired"], strata)
    path = HERE / "results/followup_verification.json"
    path.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"totals": out["totals"], "contrasts": out["contrasts"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
