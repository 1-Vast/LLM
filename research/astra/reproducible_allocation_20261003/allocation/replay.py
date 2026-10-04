"""EXPLORATORY repaired replay: screening versus verification at a conserved budget, with physical accounting.

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/replay.py
- Purpose: repair the exploratory follow-up of the feedback-validation study
  (`feedback_validation_20261003/followup_verification.py`, never modified). That comparison let
  the paired policy lose capacity every round, counted an orientation access as one measurement
  instead of wells, and never verified final-round screen hits. This module first reproduces the
  original totals from the original code path and splits paired underuse into unavoidable and
  avoidable parts, then replays every scheduler at a conserved budget with carry-over, a terminal
  verification round and branch-specific resource accounting under two plate models.
- Core points:
  - Jaaks 2022 was already opened: everything here is EXPLORATORY. Outcomes are read only through
    `common.exposed_ticket(..., "allocation")` and the frozen `jaaks.build_panels`; plate counts,
    barcodes and native-plate composition come from design columns only (`jaaks._read`).
  - Unit of inference: the cell line (mean of the SV and VS swap replicates), stratified by tissue.
  - Budget: M = ceil(0.20 x menu) orientation measurements (primary) or W = ceil(M x mean
    orientation cost) combination wells (physical; a purchase costs 14 x design plates). Cumulative
    nominal capacity N_r = min(r x ceil(B/R), B); unused capacity carries forward; actions are taken
    greedily in priority order, skipping what does not fit. Paired leaves at most 1 unit.
  - Results of a round arrive at its end (`Lab` reveals only purchased labels). Verify-first
    schedulers reserve, in the last screening round, ceil(sum p_s x c_v) for a verification-only
    terminal round (p_s = history screen-call probability); capacity left after terminal
    verification buys terminal screens (unverifiable, reported separately).
  - Arms: screen_only, paired_full, verify_hits_terminal (+ no-terminal reference), fixed_split
    (fraction selected leave-one-tissue-out), conf_per_cost (historical P(screen and valid)/cost and
    P(valid | screen)/cost), random and feedback rankings, and time-compressed variants.
  - Accounting by round and branch: orientation measurements, dose points, combination wells,
    replicate plates, QC exclusions, failures; custom 1536-well plates (200 controls, single agents
    per plate) and native Jaaks plates touched. Unknown prices, labour, days and capacity are null.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.allocation.replay
  [--dry DIR]`; `Line`, `Spec`, `Lab`, `simulate`, `account`, `pack_custom`, `original_campaign`.
- Depends on: numpy, pandas (design read); frozen research.certified_discovery and
  research.astra.feedback_validation_20261003 (imported only); the study's `common.py`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from research.certified_discovery import agent
from research.certified_discovery.screens import sha256
from research.certified_discovery.world import TransferWorld
from research.astra.feedback_validation_20261003 import followup_verification as original
from research.astra.feedback_validation_20261003 import jaaks
from research.astra.feedback_validation_20261003.study import WORLD, Posterior
from research.astra.feedback_validation_20261003.verdict import RESAMPLES, SEED, contrast

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
PRIOR = ROOT / "research/astra/feedback_validation_20261003"
PUBLISHED = PRIOR / "results/followup_verification.json"
PRIMARY_VERDICT = PRIOR / "results/jaaks_primary/verdict.json"
STATUS = ("EXPLORATORY: Jaaks et al. 2022 was already opened by feedback_validation_20261003; "
          "repaired replay, not confirmation, no verdict")

FRACTION, ROUNDS = 0.20, 4
RANDOM_SEEDS = 20
F_GRID = tuple(round(0.05 * k, 2) for k in range(11))
DOSES, ANCHOR_CONCS = 7, 2
WELLS_PER_PLATE_MEASUREMENT = DOSES * ANCHOR_CONCS          # 14 combination wells per plate
PLATE_WELLS = 1536
CONTROLS = {"untreated": 6, "dmso": 126, "blank": 28, "staurosporine": 20, "mg132": 20}
CONTROL_WELLS = sum(CONTROLS.values())                      # 200
ANCHOR_SINGLE_WELLS = 5 * 2                                  # 5 reps x 2 anchor concentrations
LIBRARY_SINGLE_WELLS = 4 * 7                                 # 4 reps x 7 library doses
CUSTOM_CAPACITY = PLATE_WELLS - CONTROL_WELLS
MIN_DAYS_PER_ROUND = 4                                       # 24 h attachment + 72 h exposure
VERIFY_SCHEDULERS = ("verify_hits", "conf_per_cost", "fixed_split")


# ---------------------------------------------------------------------------- data structures
@dataclass
class Line:
    """One target line in one swap replicate: hidden outcomes, costs, history and orientation identity."""

    tissue: str
    replicate: str
    sidm: str
    index: int                       # line index in the panel (tie-break seed, as originally)
    y: np.ndarray                    # screen label (hidden until the screen is bought)
    screen_hit: np.ndarray
    valid_hit: np.ndarray
    cost_s: np.ndarray               # combination wells of the screen orientation (14 x design plates)
    cost_v: np.ndarray               # combination wells of the verification orientation
    p_s: np.ndarray                  # history P(screen call)
    p_sv: np.ndarray                 # history P(screen call and validation call)
    p_vs: np.ndarray                 # history P(validation call | screen call)
    static: np.ndarray               # history_mean ranking
    orient_s: list = field(default_factory=list)    # (anchor, library) of the screen orientation
    orient_v: list = field(default_factory=list)
    plates_s: np.ndarray | None = None               # design plates
    plates_v: np.ndarray | None = None
    qc_plates_s: np.ndarray | None = None            # QC-passing plates (frozen builder)
    qc_plates_v: np.ndarray | None = None
    rows_s: np.ndarray | None = None                 # exported design rows (anchor conc x plate)
    rows_v: np.ndarray | None = None
    barcodes_s: list = field(default_factory=list)
    barcodes_v: list = field(default_factory=list)
    feedback: object = None                          # callable(idx, values) -> scores
    world: object = None
    panel: object = None

    @property
    def n(self) -> int:
        return int(self.y.size)

    @property
    def M(self) -> int:
        return int(math.ceil(FRACTION * self.n))

    @property
    def W(self) -> int:
        total = int(self.cost_s.sum() + self.cost_v.sum())
        return int(-(-self.M * total // (2 * self.n)))


@dataclass(frozen=True)
class Spec:
    name: str
    ranking: str                     # static | feedback | random | history_value
    scheduler: str                   # screen_only | paired | verify_hits | fixed_split | conf_per_cost
    terminal: bool = False
    rounds: int = ROUNDS
    f: float = 0.0
    seed: int = 0


class Lab:
    """Holds a line's hidden outcomes; reveals them only for purchases, at the end of the round."""

    def __init__(self, line: Line):
        self._y, self._sh, self._vh = line.y, line.screen_hit, line.valid_hit
        self.log: list[tuple[int, list[int], list[int]]] = []

    def run_round(self, r: int, screens: list[int], verifies: list[int]):
        self.log.append((r, list(screens), list(verifies)))
        return ({i: (float(self._y[i]), bool(self._sh[i])) for i in screens},
                {i: bool(self._vh[i]) for i in verifies})


class State:
    """What the campaign knows: purchases and the labels they revealed."""

    def __init__(self, n: int):
        self.screened = np.zeros(n, bool)
        self.verified = np.zeros(n, bool)
        self.y = np.full(n, np.nan)
        self.hit = np.zeros(n, bool)
        self.valid = np.zeros(n, bool)
        self.screen_round = np.full(n, -1)
        self.verify_round = np.full(n, -1)
        self.spent = 0

    def update(self, r: int, screens, verifies, revealed, cs, cv) -> None:
        s_res, v_res = revealed
        for i in screens:
            self.screened[i] = True
            self.screen_round[i] = r
            self.y[i], self.hit[i] = s_res[i]
            self.spent += int(cs[i])
        for i in verifies:
            self.verified[i] = True
            self.verify_round[i] = r
            self.valid[i] = v_res[i]
            self.spent += int(cv[i])


# ---------------------------------------------------------------------------- selection helpers
def _order(scores: np.ndarray, available: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Priority order with the frozen `agent._top` tie-break (one rng draw per available candidate)."""
    candidates = np.flatnonzero(available)
    return candidates[np.lexsort((rng.random(candidates.size), -scores[candidates]))]


def _fit(order, cost: np.ndarray, cap: int) -> tuple[list[int], int]:
    """Greedy in priority order; an action that does not fit is skipped and the next one tried."""
    take, used = [], 0
    if cap <= 0:
        return take, 0
    for i in order:
        c = int(cost[i])
        if used + c <= cap:
            take.append(int(i))
            used += c
            if used == cap:
                break
    return take, used


def _ceil(x: float) -> int:
    return int(math.ceil(x - 1e-9))


def _fit_reserve(order, cs, cv, p_s, cap: int) -> tuple[list[int], int]:
    """Last screening round: keep ceil(sum p_s x c_v) of the accepted screens free for the terminal round."""
    take, used, reserve = [], 0, 0.0
    if cap <= 0:
        return take, 0
    for i in order:
        extra = float(p_s[i]) * float(cv[i])
        if used + int(cs[i]) + _ceil(reserve + extra) <= cap:
            take.append(int(i))
            used += int(cs[i])
            reserve += extra
            if used + _ceil(reserve) >= cap:
                break
    return take, used


def _todo_by_label(st: State) -> np.ndarray:
    todo = np.flatnonzero(st.screened & st.hit & ~st.verified)
    return todo[np.argsort(-st.y[todo], kind="stable")]


def _ranker(line: Line, spec: Spec):
    if spec.ranking in ("static", "history_value"):
        return lambda idx, values: line.static
    if spec.ranking == "feedback":
        if line.feedback is None:
            raise ValueError("feedback ranking needs line.feedback")
        return line.feedback
    if spec.ranking == "random":
        return agent.RandomArm(line.n, spec.seed).scores
    raise ValueError(spec.ranking)


def _index_round(line: Line, st: State, cs, cv, cap: int, reserve_on: bool, rng) -> tuple[list, list, int]:
    """conf_per_cost: one greedy pass over verify and screen actions ranked by history value per cost."""
    todo = np.flatnonzero(st.screened & st.hit & ~st.verified)
    new = np.flatnonzero(~st.screened)
    items = np.r_[todo, new].astype(int)
    verify = np.r_[np.ones(todo.size, bool), np.zeros(new.size, bool)]
    value = np.r_[line.p_vs[todo] / cv[todo], line.p_sv[new] / cs[new]]
    order = np.lexsort((rng.random(items.size), -line.static[items], -value))
    screens, verifies, used, reserve = [], [], 0, 0.0
    for k in order:
        i = int(items[k])
        if verify[k]:
            c, extra = int(cv[i]), 0.0
        else:
            c, extra = int(cs[i]), (float(line.p_s[i]) * float(cv[i]) if reserve_on else 0.0)
        if used + c + (_ceil(reserve + extra) if reserve_on else 0) <= cap:
            (verifies if verify[k] else screens).append(i)
            used += c
            reserve += extra
            if used + (_ceil(reserve) if reserve_on else 0) >= cap:
                break
    return screens, verifies, used


# ---------------------------------------------------------------------------- one campaign
def simulate(line: Line, spec: Spec, unit: str = "measurement") -> dict:
    """Run one arm on one line; returns purchases, per-round capacity use and scored endpoints."""
    t0 = time.perf_counter()
    n = line.n
    if unit == "measurement":
        cs = cv = np.ones(n, np.int64)
        budget = line.M
    elif unit == "physical":
        cs, cv = line.cost_s.astype(np.int64), line.cost_v.astype(np.int64)
        budget = line.W
    else:
        raise ValueError(unit)
    R, sched = spec.rounds, spec.scheduler
    rng = np.random.default_rng(spec.seed if spec.ranking == "random" else line.index)
    rank = _ranker(line, spec)
    lab, st = Lab(line), State(n)
    screen_budget = budget - (int(math.floor(spec.f * budget + 1e-9)) if sched == "fixed_split" else 0)
    per = -(-screen_budget // R)
    nominal = [min((r + 1) * per, screen_budget) for r in range(R)]
    rounds = []
    for r in range(R):
        cap = nominal[r] - st.spent
        last = r == R - 1
        reserve_on = spec.terminal and last and sched in ("verify_hits", "conf_per_cost")
        screens, verifies, used = [], [], 0
        if sched in ("screen_only", "fixed_split"):
            if cap > 0:
                idx = np.flatnonzero(st.screened)
                screens, used = _fit(_order(rank(idx, st.y[idx]), ~st.screened, rng), cs, cap)
        elif sched == "paired":
            if cap > 0:
                idx = np.flatnonzero(st.screened)
                screens, used = _fit(_order(rank(idx, st.y[idx]), ~st.screened, rng), cs + cv, cap)
                verifies = list(screens)
        elif sched == "verify_hits":
            idx = np.flatnonzero(st.screened)
            scores = rank(idx, st.y[idx])
            verifies, used = _fit(_todo_by_label(st), cv, cap)
            if cap - used > 0:
                order = _order(scores, ~st.screened, rng)
                fit = _fit_reserve(order, cs, cv, line.p_s, cap - used) if reserve_on else _fit(order, cs, cap - used)
                screens, u = fit
                used += u
        elif sched == "conf_per_cost":
            if cap > 0:
                screens, verifies, used = _index_round(line, st, cs, cv, cap, reserve_on, rng)
        else:
            raise ValueError(sched)
        if screens or verifies:
            st.update(r + 1, screens, verifies, lab.run_round(r + 1, screens, verifies), cs, cv)
        rounds.append({"round": r + 1, "available": int(cap), "screen_spent": int(sum(cs[i] for i in screens)),
                       "verify_spent": int(sum(cv[i] for i in verifies)), "unused": int(cap - used)})
    if spec.terminal and sched in VERIFY_SCHEDULERS:
        cap = budget - st.spent
        screens, verifies, used = [], [], 0
        if cap > 0:
            if sched == "conf_per_cost":
                todo = np.flatnonzero(st.screened & st.hit & ~st.verified)
                todo = todo[np.lexsort((rng.random(todo.size), -line.static[todo], -(line.p_vs[todo] / cv[todo])))]
            else:
                todo = _todo_by_label(st)
            verifies, used = _fit(todo, cv, cap)
            if cap - used > 0:
                if sched == "conf_per_cost":
                    new = np.flatnonzero(~st.screened)
                    order = new[np.lexsort((rng.random(new.size), -line.static[new], -(line.p_sv[new] / cs[new])))]
                else:
                    idx = np.flatnonzero(st.screened)
                    order = _order(rank(idx, st.y[idx]), ~st.screened, rng)
                screens, u = _fit(order, cs, cap - used)
                used += u
        if screens or verifies:
            st.update(R + 1, screens, verifies, lab.run_round(R + 1, screens, verifies), cs, cv)
        rounds.append({"round": R + 1, "available": int(cap), "screen_spent": int(sum(cs[i] for i in screens)),
                       "verify_spent": int(sum(cv[i] for i in verifies)), "unused": int(cap - used)})
    return _score(line, spec, unit, budget, st, lab, rounds, cs, cv, time.perf_counter() - t0)


def _score(line, spec, unit, budget, st, lab, rounds, cs, cv, seconds) -> dict:
    sh, vh = line.screen_hit, line.valid_hit
    screened, verified = st.screened, st.verified
    if spec.scheduler == "paired":
        avail = cs + cv
        avail = avail[~screened]
    else:
        avail = cs[~screened]
        if spec.scheduler in VERIFY_SCHEDULERS:
            avail = np.r_[avail, cv[screened & st.hit & ~verified]]
    remainder = int(budget - st.spent)
    min_cost = int(avail.min()) if avail.size else None
    if remainder == 0:
        klass = "none"
    elif min_cost is None or remainder < min_cost:
        klass = "unavoidable"
    else:
        klass = "avoidable"
    observed = int((verified & screened & st.hit & st.valid).sum())
    truth = int((verified & screened & sh & vh).sum())
    if observed != truth:
        raise AssertionError("observed confirmations differ from truth")
    terminal = st.screen_round == spec.rounds + 1
    purchases = [[r, "screen", i] for r, s, _ in lab.log for i in s] + \
                [[r, "verify", i] for r, _, v in lab.log for i in v]
    purchases.sort(key=lambda p: (p[0], p[1] != "screen", p[2]))
    used_rounds = sorted({r for r, s, v in lab.log if s or v})
    return {
        "arm": spec.name, "unit": unit, "tissue": line.tissue, "replicate": line.replicate, "line": line.sidm,
        "seed": spec.seed if spec.ranking == "random" else line.index, "menu": line.n, "budget": int(budget),
        "spent": int(st.spent), "remainder": remainder, "remainder_class": klass, "min_available_cost": min_cost,
        "remainder_unavoidable": remainder if klass == "unavoidable" else 0,
        "remainder_avoidable": remainder if klass == "avoidable" else 0,
        "screen_units": int(cs[screened].sum()), "verify_units": int(cv[verified].sum()),
        "screens": int(screened.sum()), "screen_hits": int((screened & sh).sum()),
        "verifications": int(verified.sum()), "verified_hits": int((verified & screened & sh).sum()),
        "confirmed": observed,
        "hidden_validated_screen_hits": int((screened & sh & vh).sum()),
        "missed_unverified_validated": int((screened & sh & vh & ~verified).sum()),
        "unverified_screen_hits": int((screened & sh & ~verified).sum()),
        "validated_never_screened": int((~screened & sh & vh).sum()),
        "terminal_screens": int(terminal.sum()), "terminal_screen_hits": int((terminal & sh).sum()),
        "rounds_with_purchases": len(used_rounds), "last_round": int(used_rounds[-1]) if used_rounds else 0,
        "rounds": rounds, "purchases": purchases, "seconds": seconds,
    }


ENDPOINTS = ("budget", "spent", "remainder", "remainder_unavoidable", "remainder_avoidable", "screen_units",
             "verify_units", "screens", "screen_hits", "verifications", "verified_hits", "confirmed",
             "hidden_validated_screen_hits", "missed_unverified_validated", "unverified_screen_hits",
             "validated_never_screened", "terminal_screens", "terminal_screen_hits", "rounds_with_purchases",
             "last_round")


# ---------------------------------------------------------------------------- physical accounting
def pack_custom(items: list[tuple]) -> dict:
    """Custom 1536-well plates for one line: items (anchor, library, replicate plates, conflict key).

    Replicate layer k holds every measurement with >= k plates (replicates never share a plate);
    first-fit in (library, anchor) order; 200 control wells per plate; single agents per plate.
    Two items with the same non-None conflict key never share a plate.
    """
    out = {"plates": 0, "control_wells": 0, "single_anchor_wells": 0, "single_library_wells": 0,
           "combination_wells": 0, "empty_wells": 0}
    if not items:
        return out
    for k in range(1, max(int(it[2]) for it in items) + 1):
        layer = sorted((it for it in items if int(it[2]) >= k), key=lambda t: (str(t[1]), str(t[0]), str(t[3])))
        plates: list[dict] = []
        for anchor, library, _, key in layer:
            for plate in plates:
                need = WELLS_PER_PLATE_MEASUREMENT + (0 if anchor in plate["a"] else ANCHOR_SINGLE_WELLS) + (
                    0 if library in plate["l"] else LIBRARY_SINGLE_WELLS)
                if plate["used"] + need <= CUSTOM_CAPACITY and (key is None or key not in plate["k"]):
                    break
            else:
                plate = {"used": 0, "a": set(), "l": set(), "k": set(), "sa": 0, "sl": 0, "c": 0}
                plates.append(plate)
            if anchor not in plate["a"]:
                plate["a"].add(anchor)
                plate["sa"] += ANCHOR_SINGLE_WELLS
                plate["used"] += ANCHOR_SINGLE_WELLS
            if library not in plate["l"]:
                plate["l"].add(library)
                plate["sl"] += LIBRARY_SINGLE_WELLS
                plate["used"] += LIBRARY_SINGLE_WELLS
            plate["c"] += WELLS_PER_PLATE_MEASUREMENT
            plate["used"] += WELLS_PER_PLATE_MEASUREMENT
            if key is not None:
                plate["k"].add(key)
        for plate in plates:
            out["plates"] += 1
            out["control_wells"] += CONTROL_WELLS
            out["single_anchor_wells"] += plate["sa"]
            out["single_library_wells"] += plate["sl"]
            out["combination_wells"] += plate["c"]
            out["empty_wells"] += CUSTOM_CAPACITY - plate["used"]
    return out


def _zero() -> dict:
    keys = ("orientation_measurements", "dose_points", "combination_wells", "combination_wells_builder_qc",
            "combination_wells_exported_rows", "replicate_plate_measurements", "qc_excluded_replicate_plates",
            "failed_measurements", "custom_plates", "custom_control_wells", "custom_single_anchor_wells",
            "custom_single_library_wells", "custom_combination_wells", "custom_empty_wells", "native_plates",
            "native_combination_wells", "native_purchased_combination_wells", "native_single_agent_wells",
            "native_control_wells", "native_empty_wells")
    return {k: 0 for k in keys}


def _add(acc: dict, d: dict, w: float = 1.0) -> None:
    for k, v in d.items():
        if isinstance(v, dict):
            _add(acc.setdefault(k, {}), v, w)
        elif isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) and v is not None:
            acc[k] = acc.get(k, 0.0) + w * float(v)


def account(line: Line, camp: dict, native: dict) -> dict:
    """Resources of one campaign by round and branch under the custom and native plate models."""
    groups: dict[tuple[int, str], list[int]] = defaultdict(list)
    for r, branch, i in camp["purchases"]:
        groups[(r, branch)].append(i)
    out = {"total": _zero(), "by_branch": {"screen": _zero(), "verify": _zero()}, "by_round": {}}
    touched: set = set()
    for (r, branch) in sorted(groups, key=lambda k: (k[0], k[1] != "screen")):
        idx = groups[(r, branch)]
        side = "s" if branch == "screen" else "v"
        orient = getattr(line, f"orient_{side}")
        dp, qp = getattr(line, f"plates_{side}"), getattr(line, f"qc_plates_{side}")
        rw, bc = getattr(line, f"rows_{side}"), getattr(line, f"barcodes_{side}")
        m = _zero()
        m["orientation_measurements"] = len(idx)
        m["dose_points"] = WELLS_PER_PLATE_MEASUREMENT * len(idx)
        m["combination_wells"] = WELLS_PER_PLATE_MEASUREMENT * int(sum(dp[i] for i in idx))
        m["combination_wells_builder_qc"] = WELLS_PER_PLATE_MEASUREMENT * int(sum(qp[i] for i in idx))
        m["combination_wells_exported_rows"] = DOSES * int(sum(rw[i] for i in idx))
        m["replicate_plate_measurements"] = int(sum(dp[i] for i in idx))
        m["qc_excluded_replicate_plates"] = int(sum(dp[i] - qp[i] for i in idx))
        m["failed_measurements"] = int(sum(qp[i] == 0 for i in idx))
        custom = pack_custom([(orient[i][0], orient[i][1], int(dp[i]), None) for i in idx])
        for k, v in custom.items():
            m[f"custom_{k}"] = v
        new = set().union(*[set(bc[i]) for i in idx]) - touched
        touched |= new
        m["native_plates"] = len(new)
        for b in new:
            rows, anchors, libs = native[b]
            singles = ANCHOR_SINGLE_WELLS * anchors + LIBRARY_SINGLE_WELLS * libs
            m["native_combination_wells"] += DOSES * rows
            m["native_single_agent_wells"] += singles
            m["native_control_wells"] += CONTROL_WELLS
            m["native_empty_wells"] += max(0, PLATE_WELLS - CONTROL_WELLS - singles - DOSES * rows)
        m["native_purchased_combination_wells"] = DOSES * int(sum(rw[i] for i in idx))
        out["by_round"].setdefault(str(r), {"screen": _zero(), "verify": _zero()})
        _add(out["by_round"][str(r)][branch], m)
        _add(out["by_branch"][branch], m)
        _add(out["total"], m)
    joint = 0
    for r in sorted({k[0] for k in groups}):
        items = []
        for branch in ("screen", "verify"):
            side = "s" if branch == "screen" else "v"
            orient, dp = getattr(line, f"orient_{side}"), getattr(line, f"plates_{side}")
            items += [(orient[i][0], orient[i][1], int(dp[i]), i) for i in groups.get((r, branch), [])]
        joint += pack_custom(items)["plates"]
    out["custom_joint_plates_diagnostic"] = joint
    return out


# ---------------------------------------------------------------------------- the original follow-up
def original_campaign(world: TransferWorld, panel, rank: str, mode: str, seed: int) -> dict:
    """Instrumented copy of the original `policy_run` (same arithmetic, same rng use) that records purchases."""
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
    purchases, per_round = [], []
    for r in range(ROUNDS):
        budget = min(batch, total - spent)
        info = {"round": r + 1, "budget": int(budget), "lost": 0}
        per_round.append(info)
        idx = np.flatnonzero(screened)
        scores = world.X_target[:, 0] if rank == "static" else post.predict(idx, y[idx], "full")
        if mode == "verify_hits":
            todo = np.flatnonzero(screened & screen & ~verified)
            todo = todo[np.argsort(-y[todo], kind="stable")][:budget]
            verified[todo] = True
            purchases += [[r + 1, "verify", int(i)] for i in todo]
            budget -= todo.size
            spent += todo.size
            verify_spent += todo.size
        if budget <= 0:
            continue
        if mode == "paired":
            k = budget // 2
            info["lost"] = int(budget - 2 * k)
            if k == 0:
                continue
            chosen = agent._top(scores, ~screened, k, rng)
            screened[chosen] = True
            verified[chosen] = True
            purchases += [[r + 1, "screen", int(i)] for i in chosen] + [[r + 1, "verify", int(i)] for i in chosen]
            spent += 2 * k
            verify_spent += k
        else:
            chosen = agent._top(scores, ~screened, budget, rng)
            screened[chosen] = True
            purchases += [[r + 1, "screen", int(i)] for i in chosen]
            spent += budget
    round_of = {i: r for r, b, i in purchases if b == "screen"}
    final_unverified = [i for i in np.flatnonzero(screened & screen & ~verified)]
    return {"measurements": int(spent), "verification_measurements": int(verify_spent),
            "pairs_screened": int(screened.sum()), "screen_hits": int((screened & screen).sum()),
            "verified_discoveries": int((verified & screen & valid).sum()),
            "hidden_validated_among_screen_hits": int((screened & screen & valid).sum()),
            "M": total, "batch": batch, "per_round": per_round, "purchases": purchases,
            "unverified_hits_by_screen_round": {str(r): int(sum(round_of[i] == r for i in final_unverified))
                                                for r in range(1, ROUNDS + 1)},
            "unverified_hidden_validated": int((screened & screen & valid & ~verified).sum())}


ORIGINAL_FIELDS = ("measurements", "verification_measurements", "pairs_screened", "screen_hits",
                   "verified_discoveries", "hidden_validated_among_screen_hits")


def reconcile(lines: list[Line], published: dict | None) -> dict:
    """Reproduce the original totals through the original code path and classify paired underuse."""
    arms = [(rank, mode) for rank in ("static", "feedback") for mode in ("screen_only", "verify_hits", "paired")]
    totals = {f"{a}_{m}": defaultdict(float) for a, m in arms}
    mine = {f"{a}_{m}": defaultdict(float) for a, m in arms}
    wells = {f"{a}_{m}": defaultdict(float) for a, m in arms}
    underuse = defaultdict(float)
    per_line: dict = {}
    mismatches = 0
    for L in lines:
        key = f"{L.tissue}|{L.sidm}"
        for rank, mode in arms:
            arm = f"{rank}_{mode}"
            ref = original.policy_run(L.world, L.panel, rank, mode, L.index)
            rec = original_campaign(L.world, L.panel, rank, mode, L.index)
            if any(ref[f] != rec[f] for f in ORIGINAL_FIELDS):
                mismatches += 1
            for f in ORIGINAL_FIELDS:
                totals[arm][f] += 0.5 * ref[f]
                mine[arm][f] += 0.5 * rec[f]
            for r, branch, i in rec["purchases"]:
                side = "s" if branch == "screen" else "v"
                wells[arm][f"{branch}_wells_builder_qc"] += 0.5 * WELLS_PER_PLATE_MEASUREMENT * float(
                    getattr(L, f"qc_plates_{side}")[i])
                wells[arm][f"{branch}_wells_design"] += 0.5 * WELLS_PER_PLATE_MEASUREMENT * float(
                    getattr(L, f"plates_{side}")[i])
                wells[arm][f"{branch}_measurements"] += 0.5
            if mode == "verify_hits":
                for r, v in rec["unverified_hits_by_screen_round"].items():
                    wells[arm][f"unverified_screen_hits_from_round_{r}"] += 0.5 * v
                wells[arm]["unverified_hidden_validated"] += 0.5 * rec["unverified_hidden_validated"]
            if mode == "paired" and rank == "static":
                lost = rec["M"] - rec["measurements"]
                unavoidable = rec["M"] % 2
                underuse["lost"] += 0.5 * lost
                underuse["unavoidable_odd_total"] += 0.5 * unavoidable
                underuse["avoidable_per_round"] += 0.5 * (lost - unavoidable)
                slot = per_line.setdefault(key, {"tissue": L.tissue, "line": L.sidm, "menu": L.n, "M": rec["M"],
                                                 "batch": rec["batch"], "round_budgets": [x["budget"] for x in rec["per_round"]],
                                                 "round_lost": [x["lost"] for x in rec["per_round"]],
                                                 "lost": lost, "unavoidable": unavoidable,
                                                 "avoidable": lost - unavoidable})
                if slot["lost"] != lost:
                    raise AssertionError("paired loss differs between replicates")
    out = {"status": STATUS, "original_code_path": "followup_verification.policy_run (imported, unmodified)",
           "lines": len({(L.tissue, L.sidm) for L in lines}),
           "reproduced_totals": {a: dict(v) for a, v in totals.items()},
           "instrumented_copy_totals": {a: dict(v) for a, v in mine.items()},
           "instrumented_copy_mismatched_runs": mismatches,
           "paired_underuse_static": dict(underuse),
           "paired_underuse_lines_with_loss": sum(1 for v in per_line.values() if v["lost"]),
           "paired_underuse_lines_odd_M": sum(1 for v in per_line.values() if v["unavoidable"]),
           "paired_underuse_by_line": per_line,
           "original_arms_by_branch": {a: dict(v) for a, v in wells.items()}}
    if published is not None:
        pt = published["totals"]
        out["matches_published"] = all(abs(pt[a][f] - totals[a][f]) < 1e-9 for a in pt for f in ORIGINAL_FIELDS)
        out["published_totals"] = pt
    return out


# ---------------------------------------------------------------------------- data assembly
def history_probabilities(world: TransferWorld, panel) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Shrunk per-pair rates in the other lines of the same panel (same tissue, same replicate)."""
    hist = world.history_rows
    pid = world.pair_id
    n_pairs = int(pid.max()) + 1
    sh = panel.screen_hit.astype(float)
    sv = (panel.screen_hit & panel.valid_hit).astype(float)
    k0 = world.config.shrink
    n = np.bincount(pid[hist], minlength=n_pairs).astype(float)
    ns = np.bincount(pid[hist], weights=sh[hist], minlength=n_pairs)
    nsv = np.bincount(pid[hist], weights=sv[hist], minlength=n_pairs)
    base_s = float(sh[hist].mean()) if hist.size else 0.0
    base_sv = float(sv[hist].mean()) if hist.size else 0.0
    base_vs = float(sv[hist].sum() / sh[hist].sum()) if sh[hist].sum() else 0.0
    p_s = (ns + k0 * base_s) / (n + k0)
    p_sv = (nsv + k0 * base_sv) / (n + k0)
    p_vs = (nsv + k0 * base_vs) / (ns + k0)
    t = pid[world.rows]
    return p_s[t], p_sv[t], p_vs[t]


def load_design(path: Path) -> dict:
    """Design columns only: per (tissue, line, anchor, library) plates, rows, barcodes; per-plate composition."""
    d = jaaks._read(path, jaaks.DESIGN_COLUMNS)
    keys = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID"]
    g = d.groupby(keys)["BARCODE"]
    plates = g.nunique()
    rows = g.size()
    barcodes = g.agg(lambda s: tuple(sorted(set(s))))
    orient = {k: (int(p), int(r), b) for k, p, r, b in zip(plates.index, plates.to_numpy(), rows.to_numpy(),
                                                             barcodes.to_numpy())}
    pb = d.groupby("BARCODE").agg(rows=("SIDM", "size"), anchors=("ANCHOR_ID", "nunique"),
                                  libs=("LIBRARY_ID", "nunique"), lines=("SIDM", "nunique"))
    native = {b: (int(r), int(a), int(lb)) for b, r, a, lb in zip(pb.index, pb["rows"], pb["anchors"], pb["libs"])}
    concs = d.groupby(["BARCODE", "ANCHOR_ID", "LIBRARY_ID"])["ANCHOR_CONC"].nunique()
    return {"orient": orient, "native": native,
            "summary": {"rows": int(len(d)), "plates": int(d["BARCODE"].nunique()),
                        "lines_per_plate_max": int(pb["lines"].max()),
                        "orientation_plates_with_one_anchor_conc": int((concs == 1).sum()),
                        "orientation_plates": int(concs.size)}}


def build_lines(panels: dict, candidates: dict, design: dict) -> list[Line]:
    lines: list[Line] = []
    for tissue in sorted({p.stratum for p in panels.values()}):
        sv, vs = panels[f"{tissue}_SV"], panels[f"{tissue}_VS"]
        for arr in ("a", "b", "c"):
            if not np.array_equal(getattr(sv.library, arr), getattr(vs.library, arr)):
                raise AssertionError(f"{tissue}: SV and VS menus differ in {arr}")
        pairs = candidates[tissue]["pairs_s_v"]
        if list(candidates[tissue]["line_sidm"]) != list(sv.library.lines):
            raise AssertionError(f"{tissue}: line order differs from the candidates file")
        for rep, panel, other in (("SV", sv, vs), ("VS", vs, sv)):
            lib = panel.library
            if np.any(panel.valid_missing):
                raise AssertionError("validation outcomes missing in the menu")
            for li, sidm in enumerate(lib.lines):
                world = TransferWorld(lib, li, WORLD)
                rows = world.rows
                orient_s, orient_v = [], []
                for g in rows:
                    s, v = pairs[g]
                    forward, backward = (s, v), (v, s)          # (anchor, library)
                    orient_s.append(forward if rep == "SV" else backward)
                    orient_v.append(backward if rep == "SV" else forward)
                info_s = [design["orient"][(tissue, sidm, a, b)] for a, b in orient_s]
                info_v = [design["orient"][(tissue, sidm, a, b)] for a, b in orient_v]
                plates_s = np.array([x[0] for x in info_s])
                plates_v = np.array([x[0] for x in info_v])
                qc_s = lib.cost_points[rows] // WELLS_PER_PLATE_MEASUREMENT
                qc_v = other.library.cost_points[rows] // WELLS_PER_PLATE_MEASUREMENT
                if np.any(qc_s > plates_s) or np.any(qc_v > plates_v):
                    raise AssertionError("QC-passing plates exceed design plates")
                bs = [x[2] for x in info_s]
                bv = [x[2] for x in info_v]
                if any(set(a) & set(b) for a, b in zip(bs, bv)):
                    raise AssertionError("screen and verification orientations share a plate")
                p_s, p_sv, p_vs = history_probabilities(world, panel)
                post = Posterior(world)
                lines.append(Line(
                    tissue=tissue, replicate=rep, sidm=sidm, index=li, y=lib.y[rows].astype(float),
                    screen_hit=panel.screen_hit[rows].astype(bool), valid_hit=panel.valid_hit[rows].astype(bool),
                    cost_s=WELLS_PER_PLATE_MEASUREMENT * plates_s, cost_v=WELLS_PER_PLATE_MEASUREMENT * plates_v,
                    p_s=p_s, p_sv=p_sv, p_vs=p_vs, static=world.X_target[:, 0].copy(), orient_s=orient_s,
                    orient_v=orient_v, plates_s=plates_s, plates_v=plates_v, qc_plates_s=np.asarray(qc_s),
                    qc_plates_v=np.asarray(qc_v), rows_s=np.array([x[1] for x in info_s]),
                    rows_v=np.array([x[1] for x in info_v]), barcodes_s=bs, barcodes_v=bv,
                    feedback=(lambda idx, values, p=post: p.predict(idx, values, "full")), world=world, panel=panel))
    return lines


# ---------------------------------------------------------------------------- arms and tables
BASE = (
    Spec("screen_only", "static", "screen_only"),
    Spec("paired_full", "static", "paired"),
    Spec("verify_hits_terminal", "static", "verify_hits", terminal=True),
    Spec("verify_hits_noterminal", "static", "verify_hits"),
    Spec("conf_per_cost", "history_value", "conf_per_cost", terminal=True),
    Spec("feedback_verify_hits", "feedback", "verify_hits", terminal=True),
    Spec("feedback_paired", "feedback", "paired"),
    Spec("verify_hits_terminal_R1", "static", "verify_hits", terminal=True, rounds=1),
    Spec("verify_hits_terminal_R2", "static", "verify_hits", terminal=True, rounds=2),
    Spec("screen_only_R1", "static", "screen_only", rounds=1),
    Spec("paired_full_R1", "static", "paired", rounds=1),
)
RANDOM = tuple(Spec("random_verify_hits", "random", "verify_hits", terminal=True, seed=s) for s in range(RANDOM_SEEDS)) + \
    tuple(Spec("random_paired", "random", "paired", seed=s) for s in range(RANDOM_SEEDS))
GRID = tuple(Spec(f"fixed_split_f{f:.2f}", "static", "fixed_split", terminal=True, f=f) for f in F_GRID)
TABLE_ARMS = ("screen_only", "paired_full", "verify_hits_terminal", "fixed_split_dev", "conf_per_cost",
              "random_verify_hits", "feedback_verify_hits", "feedback_paired", "verify_hits_noterminal",
              "random_paired", "verify_hits_terminal_R1", "verify_hits_terminal_R2", "screen_only_R1",
              "paired_full_R1", "fixed_split_dev_R1")
SCHEDULED_ROUNDS = {"screen_only": 4, "paired_full": 4, "verify_hits_terminal": 5, "fixed_split_dev": 5,
                    "conf_per_cost": 5, "random_verify_hits": 5, "feedback_verify_hits": 5, "feedback_paired": 4,
                    "verify_hits_noterminal": 4, "random_paired": 4, "verify_hits_terminal_R1": 2,
                    "verify_hits_terminal_R2": 3, "screen_only_R1": 1, "paired_full_R1": 1, "fixed_split_dev_R1": 2}
MIN_ROUNDS_INFORMATION = {"screen_only": 1, "paired_full": 1, "fixed_split_dev": 2,
                          "note": "static non-adaptive arms need no feedback between screening rounds; their "
                                  "time-compressed R1 variants are run to check the outcome is unchanged"}


def _line_values(records: list[tuple[str, dict, float]]) -> dict:
    """line key -> endpoint -> weighted mean (weights 1/2 per replicate, 1/seeds for random arms)."""
    out: dict = {}
    for key, rec, w in records:
        slot = out.setdefault(key, defaultdict(float))
        for f in ENDPOINTS:
            slot[f] += w * rec[f]
    return out


def _table(values: dict, keys: list) -> dict:
    tot = {f: float(sum(values[k][f] for k in keys)) for f in ENDPOINTS}
    for f in ("rounds_with_purchases", "last_round"):        # per-line means, not sums
        tot[f"mean_{f}"] = tot.pop(f) / len(keys)
    tot["first_screen_yield"] = tot["screen_hits"] / tot["screens"] if tot["screens"] else None
    tot["confirmation_rate"] = tot["confirmed"] / tot["verified_hits"] if tot["verified_hits"] else None
    tot["diagnostic_confirmed_per_unit_spent"] = tot["confirmed"] / tot["spent"] if tot["spent"] else None
    tot["by_tissue_confirmed"] = {}
    for k in keys:
        tot["by_tissue_confirmed"][k[0]] = tot["by_tissue_confirmed"].get(k[0], 0.0) + values[k]["confirmed"]
    return tot


def run_replay(lines: list[Line], native: dict, units=("measurement", "physical"), log=print) -> dict:
    keys = sorted({(L.tissue, L.sidm) for L in lines})
    tissues = sorted({k[0] for k in keys})
    strata = np.array([k[0] for k in keys])
    out: dict = {"units": {}, "lines": len(keys), "line_records": []}
    for unit in units:
        t_unit = time.perf_counter()
        records: dict[str, list] = defaultdict(list)
        seconds: dict[str, float] = defaultdict(float)
        camps: dict[tuple, dict] = {}
        for L in lines:
            key = (L.tissue, L.sidm)
            for spec in BASE + GRID + RANDOM:
                rec = simulate(L, spec, unit)
                w = 0.5 / (RANDOM_SEEDS if spec.ranking == "random" else 1)
                records[spec.name].append((key, rec, w))
                seconds[spec.name] += rec["seconds"]
                camps[(spec.name, L.tissue, L.sidm, L.replicate, rec["seed"])] = rec
        grid_values = {s.name: _line_values(records[s.name]) for s in GRID}
        grid = {s.name: {t: float(sum(grid_values[s.name][k]["confirmed"] for k in keys if k[0] == t))
                         for t in tissues} for s in GRID}
        chosen = {}
        for t in tissues:
            dev = [sum(grid[s.name][u] for u in tissues if u != t) for s in GRID]
            chosen[t] = F_GRID[int(np.argmax(dev))]
        for L in lines:
            f = chosen[L.tissue]
            name = f"fixed_split_f{f:.2f}"
            rec = dict(camps[(name, L.tissue, L.sidm, L.replicate, L.index)], arm="fixed_split_dev")
            records["fixed_split_dev"].append(((L.tissue, L.sidm), rec, 0.5))
            seconds["fixed_split_dev"] += rec["seconds"]
            camps[("fixed_split_dev", L.tissue, L.sidm, L.replicate, L.index)] = rec
            spec = Spec("fixed_split_dev_R1", "static", "fixed_split", terminal=True, rounds=1, f=f)
            rec1 = simulate(L, spec, unit)
            records[spec.name].append(((L.tissue, L.sidm), rec1, 0.5))
            seconds[spec.name] += rec1["seconds"]
            camps[(spec.name, L.tissue, L.sidm, L.replicate, L.index)] = rec1
        values = {arm: _line_values(records[arm]) for arm in TABLE_ARMS}
        table = {arm: _table(values[arm], keys) for arm in TABLE_ARMS}
        for arm in TABLE_ARMS:
            table[arm]["scheduled_rounds"] = SCHEDULED_ROUNDS[arm]
            table[arm]["min_protocol_days"] = MIN_DAYS_PER_ROUND * SCHEDULED_ROUNDS[arm]
            table[arm]["wall_seconds"] = round(seconds[arm], 3)
            table[arm]["max_last_round"] = int(max(r["last_round"] for _, r, _ in records[arm]))
        # accounting
        t_acc = time.perf_counter()
        accounting: dict = {}
        line_by = {(L.tissue, L.sidm, L.replicate): L for L in lines}
        for arm in TABLE_ARMS:
            acc: dict = {}
            failures = 0
            for key, rec, w in records[arm]:
                L = line_by[(key[0], key[1], rec["replicate"])]
                a = account(L, rec, native)
                failures += a["total"]["failed_measurements"]
                _add(acc, a, w)
            acc["campaign"] = {f: table[arm][f] for f in ("budget", "spent", "remainder", "remainder_unavoidable",
                                                          "remainder_avoidable", "screen_units", "verify_units")}
            acc["unused_by_round"] = {}
            for key, rec, w in records[arm]:
                for x in rec["rounds"]:
                    slot = acc["unused_by_round"].setdefault(str(x["round"]), defaultdict(float))
                    for f in ("available", "screen_spent", "verify_spent", "unused"):
                        slot[f] += w * x[f]
            acc["unused_by_round"] = {r: dict(acc["unused_by_round"][r]) for r in sorted(acc["unused_by_round"], key=int)}
            acc["by_round"] = {r: acc["by_round"][r] for r in sorted(acc.get("by_round", {}), key=int)}
            acc["rounds"] = {"scheduled": SCHEDULED_ROUNDS[arm], "mean_rounds_with_purchases":
                             table[arm]["mean_rounds_with_purchases"], "mean_last_round": table[arm]["mean_last_round"],
                             "max_last_round": table[arm]["max_last_round"],
                             "min_protocol_days": MIN_DAYS_PER_ROUND * SCHEDULED_ROUNDS[arm],
                             "other_days": None}
            acc["failed_measurements_unweighted_campaigns"] = int(failures)
            acc["wall_seconds_simulation"] = round(seconds[arm], 3)
            accounting[arm] = acc
        acc_seconds = time.perf_counter() - t_acc
        # contrasts
        def arr(arm: str) -> np.ndarray:
            return np.array([values[arm][k]["confirmed"] for k in keys])

        best = "verify_hits_terminal" if table["verify_hits_terminal"]["confirmed"] >= table["paired_full"]["confirmed"] \
            else "paired_full"
        fb = {"verify_hits_terminal": "feedback_verify_hits", "paired_full": "feedback_paired"}
        contrasts = {
            "C1_verify_hits_terminal_minus_paired_full": contrast(arr("verify_hits_terminal"), arr("paired_full"), strata),
            "C2_verify_hits_terminal_minus_fixed_split_dev": contrast(arr("verify_hits_terminal"), arr("fixed_split_dev"), strata),
            "C3_verify_hits_terminal_minus_conf_per_cost": contrast(arr("verify_hits_terminal"), arr("conf_per_cost"), strata),
            "C4_feedback_minus_static_under_best_scheduler": dict(
                contrast(arr(fb[best]), arr(best), strata), best_scheduler=best),
            "C4b_feedback_minus_static_under_other_scheduler": dict(
                contrast(arr(fb[[s for s in fb if s != best][0]]), arr([s for s in fb if s != best][0]), strata),
                scheduler=[s for s in fb if s != best][0]),
            "C5_verify_hits_terminal_minus_random_verify_hits": contrast(arr("verify_hits_terminal"), arr("random_verify_hits"), strata),
            "C6_verify_hits_terminal_minus_verify_hits_noterminal": contrast(arr("verify_hits_terminal"), arr("verify_hits_noterminal"), strata),
        }
        grid_totals = {f"{f:.2f}": {"by_tissue": grid[f"fixed_split_f{f:.2f}"],
                                    "total": float(sum(grid[f"fixed_split_f{f:.2f}"].values()))} for f in F_GRID}
        out["units"][unit] = {
            "budget": "M orientation measurements" if unit == "measurement" else "W combination wells (14 x design plates per purchase)",
            "table": table, "contrasts": contrasts,
            "fixed_split_selection": {"rule": "leave-one-tissue-out on static confirmed discoveries; ties -> smaller f",
                                      "chosen_f": chosen, "grid": grid_totals,
                                      "in_sample_best_f_diagnostic": F_GRID[int(np.argmax([grid_totals[f'{f:.2f}']['total'] for f in F_GRID]))]},
            "per_line_confirmed": {arm: {f"{k[0]}|{k[1]}": values[arm][k]["confirmed"] for k in keys} for arm in TABLE_ARMS},
            "accounting": accounting,
            "wall_seconds": {"simulation_and_tables": round(time.perf_counter() - t_unit - acc_seconds, 2),
                             "accounting": round(acc_seconds, 2)},
        }
        for arm in TABLE_ARMS:
            if arm.startswith("random"):
                continue
            for key, rec, w in records[arm]:
                out["line_records"].append({k: v for k, v in rec.items() if k != "rounds"} | {"rounds": rec["rounds"]})
        log(f"[{unit}] done in {time.perf_counter() - t_unit:.1f}s; chosen f {chosen}; best scheduler {best}")
    return out


# ---------------------------------------------------------------------------- entry point
def _environment() -> dict:
    import pandas
    return {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": np.__version__,
            "pandas": pandas.__version__, "executable": sys.executable, "cwd": os.getcwd()}


def main(argv=None) -> int:
    from ..common import JAAKS, exposed_ticket

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry", type=Path, default=None, help="synthetic Jaaks-format release; outputs to this dir")
    args = parser.parse_args(argv)
    started = time.time()
    t0 = time.perf_counter()
    if args.dry is not None:
        out_dir = args.dry
        source = jaaks.synthetic_release(out_dir / "synthetic_release.csv")
        ticket = {"freeze_sha256": "DRY_RUN_NOT_A_VAULT", "data_sha256": sha256(source)}
        results_dir = receipts_dir = out_dir
        published = None
    else:
        source = JAAKS
        results_dir, receipts_dir = HERE / "results", HERE / "receipts"
        targets = [results_dir / "reconciliation.json", results_dir / "replay.json", results_dir / "lines.jsonl",
                   receipts_dir / "accounting.json"]
        existing = [str(p) for p in targets if p.exists()]
        if existing:
            raise SystemExit(f"REFUSED: outputs exist and are never overwritten: {existing}")
        if not (HERE / "plan.json").exists():
            raise SystemExit("write plan.json first")
        published = json.loads(PUBLISHED.read_text(encoding="utf-8"))
        ticket = exposed_ticket("allocation Phase 1: reproduce the original follow-up totals and run the repaired "
                                "budget-conserving replay (plan.json)", "allocation")
    results_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir.mkdir(parents=True, exist_ok=True)
    t_build = time.perf_counter()
    panels, report, candidates = jaaks.build_panels(ticket, source)
    design = load_design(source)
    lines = build_lines(panels, candidates, design)
    build_seconds = time.perf_counter() - t_build
    print(f"built {len(lines)} line-replicates in {build_seconds:.1f}s")
    t_rec = time.perf_counter()
    rec = reconcile(lines, published)
    rec["wall_seconds"] = round(time.perf_counter() - t_rec, 2)
    if args.dry is None:
        primary = json.loads(PRIMARY_VERDICT.read_text(encoding="utf-8"))["primary"]["totals"]["history_mean"]
        rec["cross_check_primary_history_mean_wells"] = {
            "primary_verdict_wells": primary["wells"],
            "static_screen_only_builder_wells": rec["original_arms_by_branch"]["static_screen_only"].get("screen_wells_builder_qc")}
    rec["ticket"] = ticket
    rec["sum_M"] = int(sum(L.M for L in lines if L.replicate == "SV"))
    rec["sum_W"] = int(sum(L.W for L in lines if L.replicate == "SV"))
    print(json.dumps({"reproduced": {a: rec["reproduced_totals"][a] for a in ("static_verify_hits", "static_paired")},
                      "matches_published": rec.get("matches_published"), "underuse": rec["paired_underuse_static"]},
                     indent=1))
    replay = run_replay(lines, design["native"])
    (results_dir / "reconciliation.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    line_records = replay.pop("line_records")
    with open(results_dir / "lines.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for r in line_records:
            handle.write(json.dumps(r, default=str) + "\n")
    accounting = {u: replay["units"][u].pop("accounting") for u in replay["units"]}
    finished = time.time()
    manifest = {"status": STATUS, "ticket": ticket, "source": str(source), "source_sha256": ticket["data_sha256"],
                "build_report": report, "design_summary": design["summary"],
                "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
                "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(finished)),
                "wall_seconds_total": round(time.perf_counter() - t0, 2), "wall_seconds_build": round(build_seconds, 2),
                "environment": _environment(), "bootstrap": {"resamples": RESAMPLES, "seed": SEED},
                "random_seeds": RANDOM_SEEDS, "f_grid": list(F_GRID), "plan_sha256": sha256(HERE / "plan.json")}
    replay_out = {"status": STATUS, "manifest": manifest, **replay,
                  "min_rounds_by_information_flow": MIN_ROUNDS_INFORMATION}
    (results_dir / "replay.json").write_text(json.dumps(replay_out, indent=1, default=str), encoding="utf-8")
    acc_out = {
        "status": STATUS,
        "definitions": {
            "orientation_measurement": "one pair-orientation in one line with all its replicate plates in the release",
            "dose_points": f"{DOSES} library doses x {ANCHOR_CONCS} anchor concentrations = {WELLS_PER_PLATE_MEASUREMENT} per orientation measurement",
            "combination_wells": "14 x design plates (primary physical cost; ex ante)",
            "combination_wells_builder_qc": "14 x QC-passing plates (the frozen builder's charge)",
            "combination_wells_exported_rows": "7 x exported design rows (one row = plate x anchor concentration)",
            "qc_excluded_replicate_plates": "design plates - QC-passing plates (lower bound on replicate plates whose rows for that orientation were excluded by QC; the builder counts max over anchor concentrations)",
            "failed_measurements": "purchased orientation measurements with no QC-passing plate (0 by menu construction)",
            "custom_plate_model": {"plate_wells": PLATE_WELLS, "control_wells_per_plate": CONTROLS,
                                   "single_agent_wells": {"per_distinct_anchor": ANCHOR_SINGLE_WELLS,
                                                          "per_distinct_library_drug": LIBRARY_SINGLE_WELLS},
                                   "packing": "per arm x line x replicate x round x branch; replicate layers on separate plates; first-fit in (library, anchor) order; one line per plate",
                                   "joint_packing_diagnostic": "custom_joint_plates_diagnostic: both branches of a round share plates, never both orientations of one pair"},
            "native_plate_model": "native plate = one line x all anchors x one library doublet (design barcode); a purchase requires all its native plates; plates counted once at first touch; combination wells 7 x rows on the plate; singles 10 per anchor + 28 per library drug; 200 controls. Per-pair purchases are not physically separable in this layout: the other measurements on a touched plate are produced but not credited.",
            "waiting": f"protocol minimum {MIN_DAYS_PER_ROUND} days per round (24 h attachment + 72 h exposure); other days unknown",
            "aggregation": "per line: mean over SV and VS (and over 20 seeds for random arms); summed over 125 lines",
        },
        "units": accounting,
        "unknown": {"price_per_well_or_plate": None, "labour": None, "culture_capacity": None,
                    "days_beyond_protocol_minimum": None, "custom_layout_feasibility": None,
                    "reasons": {"price_per_well_or_plate": "no price is published with the release",
                                "labour": "no staffing or hands-on time is recorded",
                                "culture_capacity": "cell expansion and maximum plates per day are not recorded",
                                "days_beyond_protocol_minimum": "dispensing, readout, fitting, decision and culture times are not recorded",
                                "custom_layout_feasibility": "a model; no custom 1536-well layout was run by the authors"}},
        "computation": {"wall_seconds_total": manifest["wall_seconds_total"],
                        "by_unit": {u: replay["units"][u]["wall_seconds"] for u in replay["units"]}},
    }
    (receipts_dir / "accounting.json").write_text(json.dumps(acc_out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({u: {a: {f: replay["units"][u]["table"][a][f] for f in ("spent", "confirmed", "screens", "verifications")}
                          for a in TABLE_ARMS[:9]} for u in replay["units"]}, indent=1))
    print(f"total wall {manifest['wall_seconds_total']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
