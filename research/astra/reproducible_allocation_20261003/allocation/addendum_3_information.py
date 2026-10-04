"""EXPLORATORY post hoc addendum 3: information-matched static rankings under the verify-hits scheduler.

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/addendum_3_information.py
- Purpose: predictor R (history P(screen call AND validation call)) sees other lines'
  validation-orientation measurements; predictor S (history mean of the screen label) does not.
  This addendum adds static rankings that see the same history data as R but do not model
  confirmation, to separate "more history information" from "confirmation-aware ranking"
  (`plan_addendum_3.json`, written before the run).
- Core points:
  - Arms under scheduler V (verify_hits_terminal): S, R (references), S_both (shrunk history mean
    of the screen and validation labels averaged), S_valid (validation label), S_vrate
    (validation-call rate). Shrinkage k0 = 2 toward the pooled history mean; history = other lines
    of the same panel; ties by history_mean then rng, reserve on p_s for every arm.
  - S and R must reproduce verify_hits_terminal and addendum-2 R+V purchase for purchase.
  - Jaaks was already opened: EXPLORATORY and post hoc; outcomes only through a new
    `exposed_ticket(..., "allocation")` and the frozen builder.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.allocation.addendum_3_information
  [--dry DIR]`; `history_scores`, `simulate_v`, `ARMS`.
- Depends on: numpy; the allocation replay and addendum-2 modules (imported, not edited).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from research.astra.feedback_validation_20261003 import jaaks
from research.astra.feedback_validation_20261003.verdict import RESAMPLES, SEED, contrast
from research.certified_discovery.screens import sha256

from . import addendum_2x2 as ad
from . import replay as rp

HERE = Path(__file__).resolve().parent
STATUS = ("EXPLORATORY, POST HOC (plan_addendum_3.json, defined after the main replay and addendum 2 were seen): "
          "Jaaks was already opened; information-matched rankings under verify_hits_terminal, no verdict")
ARMS = ("S", "R", "S_both", "S_valid", "S_vrate")
CONTRASTS = {"R_minus_S_both": ("R", "S_both"), "R_minus_S_valid": ("R", "S_valid"),
             "R_minus_S_vrate": ("R", "S_vrate"), "S_both_minus_S": ("S_both", "S")}
SECONDARY = {"S_valid_minus_S": ("S_valid", "S"), "S_vrate_minus_S": ("S_vrate", "S")}
TABLE_FIELDS = ("budget", "spent", "remainder", "screens", "screen_hits", "verifications", "verified_hits", "confirmed",
                "hidden_validated_screen_hits", "missed_unverified_validated", "unverified_screen_hits",
                "terminal_screens", "terminal_screen_hits", "last_round")


def history_scores(line: rp.Line) -> dict:
    """Per candidate: shrunk history means over other lines of the panel (target labels never enter)."""
    world, panel = line.world, line.panel
    hist = world.history_rows
    pid = world.pair_id
    n_pairs = int(pid.max()) + 1
    k0 = world.config.shrink
    count = np.bincount(pid[hist], minlength=n_pairs).astype(float)

    def shrunk(z: np.ndarray) -> np.ndarray:
        z = np.asarray(z, float)
        if not np.all(np.isfinite(z[hist])):
            raise ValueError("non-finite history label")
        total = np.bincount(pid[hist], weights=z[hist], minlength=n_pairs)
        return ((total + k0 * float(z[hist].mean())) / (count + k0))[pid[world.rows]]

    y, vy = panel.library.y, panel.valid_y
    return {"S_recomputed": shrunk(y), "S_both": shrunk((y + vy) / 2.0), "S_valid": shrunk(vy),
            "S_vrate": shrunk(panel.valid_hit.astype(float))}


def arm_keys(line: rp.Line, scores: dict | None = None) -> dict:
    scores = history_scores(line) if scores is None else scores
    return {"S": line.static, "R": line.p_sv, "S_both": scores["S_both"], "S_valid": scores["S_valid"],
            "S_vrate": scores["S_vrate"]}


def simulate_v(line: rp.Line, key: np.ndarray, unit: str = "measurement", name: str = "V") -> dict:
    """Scheduler V (verify_hits_terminal) with new screens ordered by `key` (ties history_mean, rng)."""
    t0 = time.perf_counter()
    n = line.n
    if unit == "measurement":
        cs = cv = np.ones(n, np.int64)
        budget = line.M
    else:
        cs, cv = line.cost_s.astype(np.int64), line.cost_v.astype(np.int64)
        budget = line.W
    R = rp.ROUNDS
    rng = np.random.default_rng(line.index)
    lab, st = rp.Lab(line), rp.State(n)
    per = -(-budget // R)
    nominal = [min((r + 1) * per, budget) for r in range(R)]
    rounds = []
    for r in range(R + 1):
        cap = (budget if r == R else nominal[r]) - st.spent
        verifies, used = rp._fit(rp._todo_by_label(st), cv, cap)
        screens = []
        if cap - used > 0:
            order = ad._screen_order(line, np.asarray(key, float), ~st.screened, rng)
            if r == R - 1:
                screens, u = rp._fit_reserve(order, cs, cv, line.p_s, cap - used)
            else:
                screens, u = rp._fit(order, cs, cap - used)
            used += u
        if screens or verifies:
            st.update(r + 1, screens, verifies, lab.run_round(r + 1, screens, verifies), cs, cv)
        rounds.append({"round": r + 1, "available": int(cap), "screen_spent": int(sum(cs[i] for i in screens)),
                       "verify_spent": int(sum(cv[i] for i in verifies)), "unused": int(cap - used)})
    spec = rp.Spec(name, "static", "verify_hits", terminal=True)
    return rp._score(line, spec, unit, budget, st, lab, rounds, cs, cv, time.perf_counter() - t0)


def _summarise(lines: list[rp.Line], unit: str, keys_by_line: dict) -> dict:
    keys = sorted({(L.tissue, L.sidm) for L in lines})
    strata = np.array([k[0] for k in keys])
    per_line = {a: {k: {f: 0.0 for f in TABLE_FIELDS} for k in keys} for a in ARMS}
    checks = {"S_vs_verify_hits_terminal": {"compared": 0, "mismatched": 0},
              "R_vs_addendum2_R+V": {"compared": 0, "mismatched": 0}}
    spec_s = rp.Spec("verify_hits_terminal", "static", "verify_hits", terminal=True)
    for L in lines:
        key = (L.tissue, L.sidm)
        arm_key = keys_by_line[(L.tissue, L.replicate, L.sidm)]
        for arm in ARMS:
            rec = simulate_v(L, arm_key[arm], unit, arm)
            for f in TABLE_FIELDS:
                per_line[arm][key][f] += 0.5 * rec[f]
            if arm == "S":
                checks["S_vs_verify_hits_terminal"]["compared"] += 1
                checks["S_vs_verify_hits_terminal"]["mismatched"] += int(
                    rec["purchases"] != rp.simulate(L, spec_s, unit)["purchases"])
            if arm == "R":
                checks["R_vs_addendum2_R+V"]["compared"] += 1
                checks["R_vs_addendum2_R+V"]["mismatched"] += int(
                    rec["purchases"] != ad.simulate_cell(L, "R", "V", unit)["purchases"])
    table = {}
    for arm in ARMS:
        tot = {f: float(sum(per_line[arm][k][f] for k in keys)) for f in TABLE_FIELDS}
        tot["mean_last_round"] = tot.pop("last_round") / len(keys)
        tot["first_screen_yield"] = tot["screen_hits"] / tot["screens"] if tot["screens"] else None
        tot["confirmation_rate"] = tot["confirmed"] / tot["verified_hits"] if tot["verified_hits"] else None
        tot["by_tissue_confirmed"] = {t: float(sum(per_line[arm][k]["confirmed"] for k in keys if k[0] == t))
                                      for t in sorted(set(strata))}
        table[arm] = tot
    arr = {a: np.array([per_line[a][k]["confirmed"] for k in keys]) for a in ARMS}
    return {"table": table, "reproduction_checks": checks,
            "contrasts": {n: contrast(arr[x], arr[y], strata) for n, (x, y) in CONTRASTS.items()},
            "secondary_contrasts": {n: contrast(arr[x], arr[y], strata) for n, (x, y) in SECONDARY.items()},
            "per_line_confirmed": {a: {f"{k[0]}|{k[1]}": per_line[a][k]["confirmed"] for k in keys} for a in ARMS}}


def main(argv=None) -> int:
    from ..common import JAAKS, exposed_ticket

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry", type=Path, default=None)
    args = parser.parse_args(argv)
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if args.dry is not None:
        source = jaaks.synthetic_release(args.dry / "synthetic_release.csv")
        ticket = {"freeze_sha256": "DRY_RUN_NOT_A_VAULT", "data_sha256": sha256(source)}
        target = args.dry / "addendum_3_information.json"
    else:
        target = HERE / "results/addendum_3_information.json"
        if target.exists():
            raise SystemExit(f"REFUSED: {target} exists and is never overwritten")
        if not (HERE / "plan_addendum_3.json").exists():
            raise SystemExit("write plan_addendum_3.json first")
        source = JAAKS
        ticket = exposed_ticket("allocation addendum 3 (post hoc): information-matched static rankings under "
                                "verify_hits_terminal (plan_addendum_3.json)", "allocation")
    t_build = time.perf_counter()
    panels, _, candidates = jaaks.build_panels(ticket, source)
    lines = rp.build_lines(panels, candidates, rp.load_design(source))
    build_seconds = time.perf_counter() - t_build
    keys_by_line, max_diff = {}, 0.0
    for L in lines:
        scores = history_scores(L)
        max_diff = max(max_diff, float(np.max(np.abs(scores["S_recomputed"] - L.static))))
        keys_by_line[(L.tissue, L.replicate, L.sidm)] = arm_keys(L, scores)
    out = {"status": STATUS, "ticket": ticket, "plan": "plan_addendum_3.json",
           "plan_sha256": sha256(HERE / "plan_addendum_3.json"), "started": started,
           "check_recomputed_history_mean_max_abs_diff": max_diff, "versions": {}}
    for unit in ("measurement", "physical"):
        tu = time.perf_counter()
        out["versions"][unit] = _summarise(lines, unit, keys_by_line)
        out["versions"][unit]["wall_seconds"] = round(time.perf_counter() - tu, 2)
        print(unit, json.dumps({a: {f: out["versions"][unit]["table"][a][f] for f in
                                    ("confirmed", "screen_hits", "confirmation_rate")}
                                for a in ARMS}), out["versions"][unit]["reproduction_checks"])
    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    out["wall_seconds"] = {"total": round(time.perf_counter() - t0, 2), "build": round(build_seconds, 2)}
    out["bootstrap"] = {"resamples": RESAMPLES, "seed": SEED, "unit": "line (mean of SV and VS)", "strata": "tissue"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"wrote {target} in {out['wall_seconds']['total']}s; history-mean check {max_diff}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
