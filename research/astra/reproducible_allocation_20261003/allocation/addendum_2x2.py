"""EXPLORATORY post hoc 2x2: which part of conf_per_cost's lead is predictor and which is scheduler.

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/addendum_2x2.py
- Purpose: conf_per_cost changed two things at once relative to verify_hits_terminal: the
  predictor (reproducibility-aware history) and the scheduler (one value-ordered pass over
  verify and screen actions). This addendum crosses the two predictors with the two schedulers
  on the same lines, budgets and seeds (`plan_addendum_2.json`, written before the run).
- Core points:
  - Predictor S: new screens ordered by history_mean; p_s = history screen-call rate (screen
    orientation only); P(v|s) = one pooled panel base rate. Predictor R: new screens ordered by
    p_sv; P(v|s) pair-specific (other lines' both orientations).
  - Scheduler V = verify_hits_terminal; scheduler I = conf_per_cost's index scheduler. Both
    reserve ceil(sum p_s x c_v) in round R and add a verification-first terminal round.
  - S+V and R+I must reproduce replay.simulate's verify_hits_terminal and conf_per_cost purchase
    for purchase; mismatches are counted and reported.
  - Counts how often a pending screen hit stayed unverified in a round because an accepted screen
    action came before it in the round's priority order (impossible under V).
  - Jaaks was already opened: EXPLORATORY and post hoc; outcomes only via a new
    `exposed_ticket(..., "allocation")` and the frozen builder.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.allocation.addendum_2x2
  [--dry DIR]`; `simulate_cell`, `predictor_arrays`, `base_rate`, `CELLS`.
- Depends on: numpy; the allocation replay module and frozen modules it imports.
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

from . import replay as rp

HERE = Path(__file__).resolve().parent
STATUS = ("EXPLORATORY, POST HOC (plan_addendum_2.json, defined after the main replay was seen): Jaaks was already "
          "opened; predictor x scheduler decomposition, no verdict")
CELLS = (("S", "V"), ("R", "V"), ("S", "I"), ("R", "I"))
REFERENCE = {("S", "V"): rp.Spec("verify_hits_terminal", "static", "verify_hits", terminal=True),
             ("R", "I"): rp.Spec("conf_per_cost", "history_value", "conf_per_cost", terminal=True)}
COUNTERS = ("deferred_by_priority", "deferred_hits", "unverified_while_screening")


def base_rate(line: rp.Line) -> float:
    """Pooled P(validation call | screen call) over the history lines of the line's panel."""
    hist = line.world.history_rows
    sh = line.panel.screen_hit[hist]
    sv = sh & line.panel.valid_hit[hist]
    return float(sv.sum() / sh.sum()) if sh.sum() else 0.0


def predictor_arrays(line: rp.Line, predictor: str, base: float | None = None) -> dict:
    """screen_key orders new screens under V; screen_prob / verify_prob are the I values before cost."""
    if predictor == "S":
        b = base_rate(line) if base is None else float(base)
        return {"screen_key": line.static, "screen_prob": line.p_s * b, "verify_prob": np.full(line.n, b),
                "p_s": line.p_s, "base": b}
    if predictor == "R":
        return {"screen_key": line.p_sv, "screen_prob": line.p_sv, "verify_prob": line.p_vs, "p_s": line.p_s,
                "base": None}
    raise ValueError(predictor)


def _screen_order(line, key, available, rng):
    cand = np.flatnonzero(available)
    return cand[np.lexsort((rng.random(cand.size), -line.static[cand], -key[cand]))]


def simulate_cell(line: rp.Line, predictor: str, scheduler: str, unit: str = "measurement",
                  base: float | None = None) -> dict:
    t0 = time.perf_counter()
    n = line.n
    if unit == "measurement":
        cs = cv = np.ones(n, np.int64)
        budget = line.M
    else:
        cs, cv = line.cost_s.astype(np.int64), line.cost_v.astype(np.int64)
        budget = line.W
    P = predictor_arrays(line, predictor, base)
    R = rp.ROUNDS
    rng = np.random.default_rng(line.index)
    lab, st = rp.Lab(line), rp.State(n)
    per = -(-budget // R)
    nominal = [min((r + 1) * per, budget) for r in range(R)]
    counts = {"deferred_by_priority": 0, "unverified_while_screening": 0}
    deferred_hits: set[int] = set()
    rounds = []

    def close_round(r, pending, screens, verifies, first_screen_pos, position):
        ver = set(verifies)
        for j in pending:
            if j in ver:
                continue
            if screens:
                counts["unverified_while_screening"] += 1
            if first_screen_pos is not None and position.get(j, 10 ** 9) > first_screen_pos:
                counts["deferred_by_priority"] += 1
                deferred_hits.add(int(j))

    for r in range(R + 1):
        terminal = r == R
        cap = (budget if terminal else nominal[r]) - st.spent
        reserve_on = r == R - 1
        pending = np.flatnonzero(st.screened & st.hit & ~st.verified)
        screens, verifies, used = [], [], 0
        first_screen_pos, position = None, {}
        if scheduler == "V":
            verifies, used = rp._fit(rp._todo_by_label(st), cv, cap)
            if cap - used > 0:
                order = _screen_order(line, P["screen_key"], ~st.screened, rng)
                if reserve_on:
                    screens, u = rp._fit_reserve(order, cs, cv, P["p_s"], cap - used)
                else:
                    screens, u = rp._fit(order, cs, cap - used)
                used += u
        elif scheduler == "I" and not terminal:
            if cap > 0:
                todo = pending
                new = np.flatnonzero(~st.screened)
                items = np.r_[todo, new].astype(int)
                is_verify = np.r_[np.ones(todo.size, bool), np.zeros(new.size, bool)]
                value = np.r_[P["verify_prob"][todo] / cv[todo], P["screen_prob"][new] / cs[new]]
                order = np.lexsort((rng.random(items.size), -line.static[items], -value))
                reserve = 0.0
                for pos, k in enumerate(order):
                    i = int(items[k])
                    if is_verify[k]:
                        position[i] = pos
                        c, extra = int(cv[i]), 0.0
                    else:
                        c, extra = int(cs[i]), (float(P["p_s"][i]) * float(cv[i]) if reserve_on else 0.0)
                    if used + c + (rp._ceil(reserve + extra) if reserve_on else 0) <= cap:
                        if is_verify[k]:
                            verifies.append(i)
                        else:
                            screens.append(i)
                            if first_screen_pos is None:
                                first_screen_pos = pos
                        used += c
                        reserve += extra
                        if used + (rp._ceil(reserve) if reserve_on else 0) >= cap:
                            break
                for pos, k in enumerate(order):          # positions of pending hits beyond the break
                    if is_verify[k]:
                        position.setdefault(int(items[k]), pos)
        elif scheduler == "I" and terminal:
            if cap > 0:
                todo = pending[np.lexsort((rng.random(pending.size), -line.static[pending],
                                           -(P["verify_prob"][pending] / cv[pending])))]
                verifies, used = rp._fit(todo, cv, cap)
                if cap - used > 0:
                    new = np.flatnonzero(~st.screened)
                    order = new[np.lexsort((rng.random(new.size), -line.static[new],
                                            -(P["screen_prob"][new] / cs[new])))]
                    screens, u = rp._fit(order, cs, cap - used)
                    used += u
        else:
            raise ValueError(scheduler)
        close_round(r + 1, pending, screens, verifies, first_screen_pos, position)
        if screens or verifies:
            st.update(r + 1, screens, verifies, lab.run_round(r + 1, screens, verifies), cs, cv)
        rounds.append({"round": r + 1, "available": int(cap), "screen_spent": int(sum(cs[i] for i in screens)),
                       "verify_spent": int(sum(cv[i] for i in verifies)), "unused": int(cap - used)})
    spec = rp.Spec(f"{predictor}+{scheduler}", "static", "verify_hits" if scheduler == "V" else "conf_per_cost",
                   terminal=True)
    rec = rp._score(line, spec, unit, budget, st, lab, rounds, cs, cv, time.perf_counter() - t0)
    rec.update(counts)
    rec["deferred_hits"] = len(deferred_hits)
    rec["base_rate"] = P["base"]
    return rec


FIELDS = rp.ENDPOINTS + COUNTERS


def _summarise(lines: list[rp.Line], unit: str) -> dict:
    keys = sorted({(L.tissue, L.sidm) for L in lines})
    strata = np.array([k[0] for k in keys])
    per_line = {c: {k: {f: 0.0 for f in FIELDS} for k in keys} for c in CELLS}
    checks = {f"{p}+{s}": {"compared": 0, "mismatched": 0} for p, s in REFERENCE}
    seconds = {c: 0.0 for c in CELLS}
    bases = []
    for L in lines:
        key = (L.tissue, L.sidm)
        for cell in CELLS:
            rec = simulate_cell(L, cell[0], cell[1], unit)
            seconds[cell] += rec["seconds"]
            for f in FIELDS:
                per_line[cell][key][f] += 0.5 * rec[f]
            if cell == ("S", "V"):
                bases.append(rec["base_rate"])
            if cell in REFERENCE:
                ref = rp.simulate(L, REFERENCE[cell], unit)
                slot = checks[f"{cell[0]}+{cell[1]}"]
                slot["compared"] += 1
                slot["mismatched"] += int(ref["purchases"] != rec["purchases"])
    table = {}
    for cell in CELLS:
        tot = {f: float(sum(per_line[cell][k][f] for k in keys)) for f in FIELDS}
        tot["confirmation_rate"] = tot["confirmed"] / tot["verified_hits"] if tot["verified_hits"] else None
        tot["unverified_hits_excluding_terminal_screens"] = tot["unverified_screen_hits"] - tot["terminal_screen_hits"]
        tot["mean_last_round"] = tot.pop("last_round") / len(keys)
        tot["mean_rounds_with_purchases"] = tot.pop("rounds_with_purchases") / len(keys)
        tot["by_tissue_confirmed"] = {t: float(sum(per_line[cell][k]["confirmed"] for k in keys if k[0] == t))
                                      for t in sorted(set(strata))}
        tot["wall_seconds"] = round(seconds[cell], 3)
        table[f"{cell[0]}+{cell[1]}"] = tot
    arr = {f"{c[0]}+{c[1]}": np.array([per_line[c][k]["confirmed"] for k in keys]) for c in CELLS}
    contrasts = {
        "predictor_under_V__RV_minus_SV": contrast(arr["R+V"], arr["S+V"], strata),
        "predictor_under_I__RI_minus_SI": contrast(arr["R+I"], arr["S+I"], strata),
        "scheduler_under_S__SI_minus_SV": contrast(arr["S+I"], arr["S+V"], strata),
        "scheduler_under_R__RI_minus_RV": contrast(arr["R+I"], arr["R+V"], strata),
        "interaction__(RI-SI)-(RV-SV)": dict(contrast(arr["R+I"] + arr["S+V"], arr["S+I"] + arr["R+V"], strata),
                                            note="sum_x - sum_y and mean_diff are the interaction; relative_gain "
                                                 "is relative to (S+I)+(R+V) and is not a gain"),
        "combined__RI_minus_SV": contrast(arr["R+I"], arr["S+V"], strata),
    }
    return {"table": table, "contrasts": contrasts, "reproduction_checks": checks,
            "base_rate_SV_records": {"min": float(min(bases)), "max": float(max(bases)),
                                     "mean": float(np.mean(bases))},
            "per_line_confirmed": {k2: {f"{k[0]}|{k[1]}": per_line[c][k]["confirmed"] for k in keys}
                                   for k2, c in ((f"{c[0]}+{c[1]}", c) for c in CELLS)}}


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
        target = args.dry / "addendum_2x2.json"
    else:
        target = HERE / "results/addendum_2x2.json"
        if target.exists():
            raise SystemExit(f"REFUSED: {target} exists and is never overwritten")
        if not (HERE / "plan_addendum_2.json").exists():
            raise SystemExit("write plan_addendum_2.json first")
        source = JAAKS
        ticket = exposed_ticket("allocation addendum 2 (post hoc): predictor x scheduler 2x2 "
                                "(plan_addendum_2.json)", "allocation")
    t_build = time.perf_counter()
    panels, report, candidates = jaaks.build_panels(ticket, source)
    lines = rp.build_lines(panels, candidates, rp.load_design(source))
    build_seconds = time.perf_counter() - t_build
    out = {"status": STATUS, "ticket": ticket, "plan": "plan_addendum_2.json",
           "plan_sha256": sha256(HERE / "plan_addendum_2.json"), "started": started, "versions": {}}
    for unit in ("measurement", "physical"):
        tu = time.perf_counter()
        out["versions"][unit] = _summarise(lines, unit)
        out["versions"][unit]["wall_seconds"] = round(time.perf_counter() - tu, 2)
        print(unit, json.dumps({c: {f: out["versions"][unit]["table"][c][f] for f in
                                    ("confirmed", "screen_hits", "verifications", "deferred_by_priority")}
                                for c in out["versions"][unit]["table"]}),
              out["versions"][unit]["reproduction_checks"])
    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    out["wall_seconds"] = {"total": round(time.perf_counter() - t0, 2), "build": round(build_seconds, 2)}
    out["bootstrap"] = {"resamples": RESAMPLES, "seed": SEED, "unit": "line (mean of SV and VS)", "strata": "tissue"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"wrote {target} in {out['wall_seconds']['total']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
