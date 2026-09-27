"""Task headroom, decision-changeable units and statistical power: is a task fit to judge an agent?

File summary
- Path: research/protocol_v2/headroom.py
- Purpose: before any agent is compared with the fixed expert order on a task, measure how much
  any policy could gain there, and how many independent units a practically meaningful gain would
  need. A task whose headroom is below twice the pre-registered practical effect (MPIE) cannot be
  the primary benchmark: a +0.02 claim there is impossible by construction, not merely unshown.
- Core points:
  - Headroom is paired, on identical episodes: oracle minus fixed, for correct decisions and for
    unpriced utility (+1 / -2 / 0). The oracle reads hidden outcomes and is a bound, never a
    competitor. It never decides wrongly, so utility headroom also counts the fixed order's wrong
    decisions an oracle would avoid by deferring.
  - Decision-changeable units: the share of independent units in which at least one legal
    sequence (the oracle's) ends in a different terminal decision from the fixed order's.
  - Power: the standard error of the paired correct difference of a realistic candidate (the
    current planner, `belief`) against fixed, from the unit-cluster bootstrap. Minimum detectable
    effect at the current n: 2.80 standard errors (two-sided 5%, 80% power). Units required for
    the MPIE: n x (2.80 x SE / MPIE)^2.
  - Gate (pre-registered in `protocol.json`): a task is `eligible_primary` if the headroom
    estimate is at least 2 x MPIE and the lower 95% bound at least MPIE. It is `powered` if the
    units required for the MPIE do not exceed the units available.
- Run: python -m research.protocol_v2.headroom --records DIR_OR_FILE [--records ...] --out FILE
- Interfaces: `task_headroom`, `headroom_table`, `gate`
- Depends on: records.py, research/external_validation/statistics.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from research.external_validation import statistics as S

from . import records as RC

MPIE = 0.02
Z_POWER = 1.959964 + 0.841621
ARMS = ("fixed", "oracle", "belief", "anchored", "random_legal", "myopic_edv")


def _paired(frame, left, right, metric):
    sub = frame[frame.arm.isin((left, right))].copy()
    sub["policy"] = sub.arm
    sub["compound"] = sub.fold.astype(str) + ":" + sub.compound
    return S.paired(sub, left, right, metric, "unit")


def gate(headroom: dict, power: dict | None, *, mpie: float = MPIE) -> dict:
    estimate, low = headroom["difference"], headroom["ci"][0]
    eligible = estimate >= 2 * mpie and low >= mpie
    powered = bool(power) and power.get("units_required_for_mpie") is not None and \
        power["units_required_for_mpie"] <= power["units"]
    return {"eligible_primary": bool(eligible), "powered": bool(powered),
            "status": ("eligible_and_powered" if eligible and powered else
                       "eligible_underpowered" if eligible else "ineligible_low_headroom"),
            "rule": f"headroom >= {2 * mpie:g} and lower bound >= {mpie:g}; units required <= units available"}


def task_headroom(frame, *, candidate: str = "belief", mpie: float = MPIE) -> dict:
    """Headroom, changeable units and power for one task's records (one tier, all folds)."""
    arms = set(frame.arm)
    if not {"fixed", "oracle"} <= arms:
        raise ValueError("headroom needs the fixed and oracle arms on the same episodes")
    fixed = frame[frame.arm == "fixed"].set_index("episode")
    oracle = frame[frame.arm == "oracle"].set_index("episode").reindex(fixed.index)
    changed = (oracle.final != fixed.final)
    gain = (oracle.correct > fixed.correct)
    per_unit = changed.groupby(fixed.unit).any()
    gain_unit = gain.groupby(fixed.unit).any()
    out = {"units": int(fixed.unit.nunique()), "episodes": int(len(fixed)),
           "oracle_correct": float(oracle.correct.mean()), "fixed_correct": float(fixed.correct.mean()),
           "fixed_wrong": float(fixed.wrong.mean()), "oracle_deferred": float(oracle.deferred.mean()),
           "headroom_correct": _paired(frame, "oracle", "fixed", "correct"),
           "headroom_utility": _paired(frame, "oracle", "fixed", "utility"),
           "decision_changeable_unit_share": float(per_unit.mean()),
           "correct_gainable_unit_share": float(gain_unit.mean()),
           "decision_changeable_episode_share": float(changed.mean())}
    power = None
    if candidate in arms:
        diff = _paired(frame, candidate, "fixed", "correct")
        se = (diff["ci"][1] - diff["ci"][0]) / (2 * 1.959964)
        power = {"candidate": candidate, "difference": diff["difference"], "ci": diff["ci"], "se": se,
                 "units": diff["units"], "mde_at_current_n": Z_POWER * se,
                 "units_required_for_mpie": (int(np.ceil(diff["units"] * (Z_POWER * se / mpie) ** 2))
                                             if se > 0 else None)}
    out["power"] = power
    out["gate"] = gate(out["headroom_correct"], power, mpie=mpie)
    return out


def headroom_table(frame, *, candidate: str = "belief", mpie: float = MPIE) -> dict:
    out = {}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        out[f"{dataset}:{tier}"] = task_headroom(g, candidate=candidate, mpie=mpie)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", action="append", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--candidate", default="belief")
    args = parser.parse_args()
    tables = {}
    for path in args.records:
        frame = RC.load(path, ARMS)
        tables.update(headroom_table(frame, candidate=args.candidate))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(json.dumps(tables, indent=1).encode("utf-8"))
    for name, t in tables.items():
        h = t["headroom_correct"]
        p = t["power"] or {}
        print(f"{name}: units {t['units']} headroom {h['difference']:+.3f} [{h['ci'][0]:+.3f},{h['ci'][1]:+.3f}] "
              f"changeable {t['decision_changeable_unit_share']:.2f} mde {p.get('mde_at_current_n', float('nan')):.3f} "
              f"n_req {p.get('units_required_for_mpie')} -> {t['gate']['status']}")


if __name__ == "__main__":
    main()
