"""Per-pair (custom-layout) campaign engine with stopping and full physical accounting (contract v2).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/frontier.py
- Purpose: replay 1-, 2- and 3-round confirmation campaigns of one target line and role assignment
  under the frozen campaign contract v2 (`protocol/campaign_contract.json`), with an explicit
  stopping rule (no unverifiable final-round screens), and charge every purchase in measurements,
  dose points, combination wells, custom 1536-well plate starts (documented 200 and raw 216-254
  controls per plate), shared single-agent wells, native plates and seeding events touched, failures,
  unused cap, rounds used and minimum days.
- Core points (all mirrored from contract v2, integer arithmetic):
  - Cap: M = ceil(cp x menu / 100) measurements (cp = 20 -> (menu + 4) // 5); wells
    W = ceil(Fraction(M) x sum(c_s + c_v) / (2 menu)), c = 14 x design plates.
  - Order: lexsort((rank, -round(score, 12))), rank from default_rng([20261004, tissue code, line
    index, role index]).permutation(menu) with rank[perm[k]] = k.
  - P1: both orientations of the first M // 2 pairs (1 round).
  - P2: n1 = ((100 - fp) M) // 100 screens; round 2 verifies round-1 hits in verify order while
    spent < M; no round-2 screens. Wells: round-1 budget ((100 - fp) W) // 100, greedy skip.
  - P3: (M + 1) // 2 screens; round 2 v2 = min(hits, M - n_r1) verifications, then screens accepted
    iff (k + 1) + ceil(round(sum p_s, 12)) <= B2, stop at first failure; round 3 verifies round-2 hits.
  - Predictors: shrunk history rates and label means (k0 = 2) on H = menu rows of hist(t) in the
    role panel (E rows never in H). Oracle = true joint call (headroom only).
  - `terminal=True` is a REFERENCE that spends the leftover cap on final-round screens (the old
    replays' behaviour) to show what stopping saves; it is never an evaluated arm.
- Interfaces: `Unit`, `Lab`, `build_units`, `role_arrays`, `history_scores`, `run_custom`,
  `account_custom`, `pack_custom`, `line_values`, constants `PREDICTORS`, `FP_GRID`.
- Depends on: numpy; `layout.py` (design only). Outcomes enter only through `Hidden`/`Lab`.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from .layout import (ANCHOR_SINGLE_WELLS, CONTROL_VARIANTS, DOSES, LIBRARY_SINGLE_WELLS, MIN_DAYS_PER_ROUND,
                     PLATE_WELLS, ROLE_INDEX, ROLES, WELLS_PER_PLATE_MEASUREMENT, Layout, event_of)

SEED = 20261004
K0 = 2.0
FP_GRID = tuple(range(10, 61, 5))
PREDICTORS = ("S", "S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod", "R")
ALL_SCORES = PREDICTORS + ("oracle",)


# ---------------------------------------------------------------------------- data structures
@dataclass
class Hidden:
    """Outcomes of one line x role; only `Lab` reads them, and only for purchases."""

    hit_s: np.ndarray
    hit_v: np.ndarray
    y_s: np.ndarray
    y_v: np.ndarray


class Lab:
    def __init__(self, hidden: Hidden):
        self._h = hidden
        self.log: list[tuple[int, list[int], list[int]]] = []

    def reveal(self, r: int, screens, verifies) -> tuple[dict, dict]:
        self.log.append((r, [int(i) for i in screens], [int(i) for i in verifies]))
        return ({int(i): bool(self._h.hit_s[i]) for i in screens}, {int(i): bool(self._h.hit_v[i]) for i in verifies})


@dataclass
class Unit:
    """Public facts of one campaign (target line x role assignment)."""

    tissue: str
    code: int
    sidm: str
    line_index: int
    role: str
    group: str                       # 'E' | 'HD' | other label
    rows: np.ndarray                 # tissue menu rows of this line (builder order)
    rank: np.ndarray                 # tie-break rank (contract v2)
    scores: dict                     # predictor -> (screen score, verify score)
    p_s: np.ndarray                  # shrunk history screen-call rate of the role (P3 reserve)
    p_v: np.ndarray
    p_sv: np.ndarray
    p_vs: np.ndarray
    plates_s: np.ndarray             # design plates (pre-QC) behind each orientation
    plates_v: np.ndarray
    rows_s: np.ndarray               # exported design rows (plate x anchor concentration)
    rows_v: np.ndarray
    qc_s: np.ndarray                 # builder QC-passing plates (None in design-only use)
    qc_v: np.ndarray
    orient_s: list                   # (anchor, library)
    orient_v: list
    barcodes_s: list
    barcodes_v: list
    comp_s: np.ndarray               # native component (library doublet) holding the orientation
    comp_v: np.ndarray
    history_lines: tuple = ()
    hidden: Hidden | None = field(default=None, repr=False)

    @property
    def n(self) -> int:
        return int(self.rows.size)

    @property
    def role_index(self) -> int:
        return ROLE_INDEX[self.role]

    def cap(self, cp: int = 20) -> int:
        return -(-cp * self.n // 100)

    def wells_cap(self, cp: int = 20) -> int:
        tot = int((WELLS_PER_PLATE_MEASUREMENT * (self.plates_s + self.plates_v)).sum())
        return math.ceil(Fraction(self.cap(cp)) * Fraction(tot, 2 * self.n)) if self.n else 0


def tie_rank(code: int, line_index: int, role_index: int, n: int) -> np.ndarray:
    perm = np.random.default_rng([SEED, code, line_index, role_index]).permutation(n)
    rank = np.empty(n, np.int64)
    rank[perm] = np.arange(n)
    return rank


def order_by(score: np.ndarray, rank: np.ndarray) -> np.ndarray:
    return np.lexsort((rank, -np.round(np.asarray(score, float), 12)))


# ---------------------------------------------------------------------------- predictors (contract v2)
def role_arrays(panels: dict, tissue: str) -> dict:
    """Per menu row of the tissue: both orientations' labels, calls and builder QC plates, per role."""
    sv, vs = panels[f"{tissue}_SV"], panels[f"{tissue}_VS"]
    yA, yB = np.asarray(sv.library.y, float), np.asarray(vs.library.y, float)
    hA, hB = np.asarray(sv.screen_hit, bool), np.asarray(vs.screen_hit, bool)
    if not (np.array_equal(hB, np.asarray(sv.valid_hit, bool)) and np.array_equal(hA, np.asarray(vs.valid_hit, bool))
            and np.allclose(yB, np.asarray(sv.valid_y, float)) and np.allclose(yA, np.asarray(vs.valid_y, float))):
        raise AssertionError(f"{tissue}: SV verification is not the VS screen measurement")
    if np.any(sv.valid_missing) or np.any(vs.valid_missing):
        raise AssertionError("verification outcome missing inside the menu")
    qA = np.asarray(sv.library.cost_points) // WELLS_PER_PLATE_MEASUREMENT
    qB = np.asarray(vs.library.cost_points) // WELLS_PER_PLATE_MEASUREMENT
    return {"SV": {"y_s": yA, "y_v": yB, "h_s": hA, "h_v": hB, "qc_s": qA, "qc_v": qB},
            "VS": {"y_s": yB, "y_v": yA, "h_s": hB, "h_v": hA, "qc_s": qB, "qc_v": qA}}


def history_scores(arr: dict, pair_id: np.ndarray, hist_mask: np.ndarray, target_rows: np.ndarray) -> dict:
    """Contract v2 shrunk history quantities for the target rows (H = rows with hist_mask)."""
    H = np.asarray(hist_mask, bool)
    pid = pair_id[H]
    npairs = int(pair_id.max()) + 1
    n = np.bincount(pid, minlength=npairs).astype(float)
    sh = arr["h_s"][H].astype(float)
    vh = arr["h_v"][H].astype(float)
    joint = sh * vh
    ys, yv = arr["y_s"][H].astype(float), arr["y_v"][H].astype(float)

    def shrink(x: np.ndarray) -> np.ndarray:
        pooled = float(x.mean()) if x.size else 0.0
        return (np.bincount(pid, weights=x, minlength=npairs) + K0 * pooled) / (n + K0)

    p_s, p_v, p_sv = shrink(sh), shrink(vh), shrink(joint)
    S, L_v, S_both = shrink(ys), shrink(yv), shrink((ys + yv) / 2.0)
    pooled_vs = float(joint.sum() / sh.sum()) if sh.sum() > 0 else (float(vh.mean()) if vh.size else 0.0)
    p_vs = (np.bincount(pid, weights=joint, minlength=npairs) + K0 * pooled_vs) / (
        np.bincount(pid, weights=sh, minlength=npairs) + K0)
    t = pair_id[target_rows]
    q = {k: v[t] for k, v in dict(p_s=p_s, p_v=p_v, p_sv=p_sv, p_vs=p_vs, S=S, L_v=L_v, S_both=S_both).items()}
    q["scores"] = {
        "S": (q["S"], q["S"]), "S_both": (q["S_both"], q["S_both"]), "L_v": (q["L_v"], q["L_v"]),
        "C_s": (q["p_s"], q["p_s"]), "C_v": (q["p_v"], q["p_v"]),
        "C_mean": ((q["p_s"] + q["p_v"]) / 2.0, q["p_v"]), "C_prod": (q["p_s"] * q["p_v"], q["p_v"]),
        "R": (q["p_sv"], q["p_vs"])}
    return q


def build_units(layout: Layout, panels: dict, partition: dict, *, groups=("E", "HD"),
                all_lines_loo: bool = False) -> list[Unit]:
    """Units for every line of the requested partition groups and both roles.

    History (contract v2 H1): E target -> all HD lines of the tissue; HD target -> other HD lines.
    `all_lines_loo=True` is the registered all-lines leave-one-line-out sensitivity (every other line).
    """
    units: list[Unit] = []
    for tissue in sorted(layout.tissues):
        tl = layout.tissues[tissue]
        part = partition[tissue]
        hd = set(part["HD"])
        e = set(part["E"])
        arrs = role_arrays(panels, tissue)
        for group in groups:
            for sidm in sorted(part[group]):
                li = tl.lines.index(sidm)
                rows = tl.rows_of(li)
                if all_lines_loo:
                    hist = tuple(x for x in tl.lines if x != sidm)
                else:
                    hist = tuple(sorted(hd - {sidm}))
                    if set(hist) & e:
                        raise AssertionError("an E line entered history")
                hmask = np.isin(tl.sidm, list(hist))
                if hmask[rows].any():
                    raise AssertionError("target rows entered history")
                for role in ROLES:
                    a = arrs[role]
                    q = history_scores(a, tl.pair_id, hmask, rows)
                    hidden = Hidden(a["h_s"][rows].copy(), a["h_v"][rows].copy(), a["y_s"][rows].copy(),
                                    a["y_v"][rows].copy())
                    joint = (hidden.hit_s & hidden.hit_v).astype(float)
                    scores = dict(q["scores"])
                    scores["oracle"] = (joint, joint)
                    units.append(make_unit(layout, tissue, sidm, role, group, scores, q, hidden,
                                           a["qc_s"][rows], a["qc_v"][rows], hist))
    return units


def make_unit(layout: Layout, tissue: str, sidm: str, role: str, group: str, scores: dict, q: dict,
              hidden: Hidden | None, qc_s=None, qc_v=None, hist=()) -> Unit:
    tl = layout.tissues[tissue]
    li = tl.lines.index(sidm)
    rows = tl.rows_of(li)
    s, v = tl.s[rows], tl.v[rows]
    fwd, bwd = list(zip(s.tolist(), v.tolist())), list(zip(v.tolist(), s.tolist()))   # (anchor, library)
    o_s, o_v = (fwd, bwd) if role == "SV" else (bwd, fwd)
    info_s = [layout.orient[(tissue, sidm, a, b)] for a, b in o_s]
    info_v = [layout.orient[(tissue, sidm, a, b)] for a, b in o_v]
    bs, bv = [x[2] for x in info_s], [x[2] for x in info_v]
    if any(set(x) & set(y) for x, y in zip(bs, bv)):
        raise AssertionError("screen and verification orientations share a plate")
    comp_s = np.array([tl.comp_of[b] for _, b in o_s], np.int64)
    comp_v = np.array([tl.comp_of[b] for _, b in o_v], np.int64)
    n = rows.size
    return Unit(tissue=tissue, code=tl.code, sidm=sidm, line_index=li, role=role, group=group, rows=rows,
                rank=tie_rank(tl.code, li, ROLE_INDEX[role], n), scores=scores, p_s=q["p_s"], p_v=q["p_v"],
                p_sv=q["p_sv"], p_vs=q["p_vs"], plates_s=np.array([x[0] for x in info_s], np.int64),
                plates_v=np.array([x[0] for x in info_v], np.int64),
                rows_s=np.array([x[1] for x in info_s], np.int64), rows_v=np.array([x[1] for x in info_v], np.int64),
                qc_s=None if qc_s is None else np.asarray(qc_s, np.int64),
                qc_v=None if qc_v is None else np.asarray(qc_v, np.int64),
                orient_s=o_s, orient_v=o_v, barcodes_s=bs, barcodes_v=bv, comp_s=comp_s, comp_v=comp_v,
                history_lines=tuple(hist), hidden=hidden)


# ---------------------------------------------------------------------------- campaign engine
def _costs(u: Unit, cap_kind: str, cp: int) -> tuple[np.ndarray, np.ndarray, int]:
    if cap_kind == "measurement":
        return np.ones(u.n, np.int64), np.ones(u.n, np.int64), u.cap(cp)
    if cap_kind == "wells":
        return (WELLS_PER_PLATE_MEASUREMENT * u.plates_s, WELLS_PER_PLATE_MEASUREMENT * u.plates_v, u.wells_cap(cp))
    raise ValueError(cap_kind)


def _greedy(order, cost, budget: int) -> tuple[list[int], int]:
    """Take actions in order; one that does not fit is skipped and the next tried."""
    take, used = [], 0
    for i in order:
        c = int(cost[i])
        if used + c <= budget:
            take.append(int(i))
            used += c
    return take, used


def run_custom(u: Unit, pred: str, rounds: int, *, fp: int | None = None, cap_kind: str = "measurement",
               cp: int = 20, terminal: bool = False, lab: Lab | None = None,
               round2_screen_score: np.ndarray | None = None, round2_count: int | None = None) -> dict:
    """One campaign. rounds: 1 = P1 paired, 2 = P2 fixed split, 3 = P3 verify-hits with reserve.

    `round2_screen_score` (P3 diagnostics only, e.g. the round-2 oracle) replaces the screen order of the
    round-2 screens; round 1 and the verify order are unchanged. With `round2_count` the round-2 screens are
    the first `round2_count` unscreened candidates of that order (the contract's gate oracle: same count),
    otherwise the reserve rule decides how many.
    """
    lab = lab or Lab(u.hidden)
    cs, cv, cap = _costs(u, cap_kind, cp)
    unit_cost = cap_kind == "measurement"
    s_score, v_score = u.scores[pred]
    s_order = order_by(s_score, u.rank)
    s_order_r2 = s_order if round2_screen_score is None else order_by(round2_screen_score, u.rank)
    v_rank = np.empty(u.n, np.int64)
    v_rank[order_by(v_score, u.rank)] = np.arange(u.n)
    screened = np.zeros(u.n, bool)
    verified = np.zeros(u.n, bool)
    hit = np.zeros(u.n, bool)
    vhit = np.zeros(u.n, bool)
    s_round = np.zeros(u.n, np.int64)
    v_round = np.zeros(u.n, np.int64)
    spent = 0
    per_round: list[dict] = []
    n1 = None
    reserve_info = None

    def buy(r: int, screens: list[int], verifies: list[int], available: int) -> None:
        nonlocal spent
        for j in verifies:
            if r != 1 or rounds != 1:
                if not (screened[j] and hit[j] and s_round[j] < r and not verified[j]):
                    raise AssertionError("illegal verification")
        sres, vres = lab.reveal(r, screens, verifies)
        for i in screens:
            screened[i], s_round[i], hit[i] = True, r, sres[i]
        for j in verifies:
            verified[j], v_round[j], vhit[j] = True, r, vres[j]
        ss, vs_ = int(sum(cs[i] for i in screens)), int(sum(cv[j] for j in verifies))
        spent += ss + vs_
        per_round.append({"round": r, "available": int(available), "screens": len(screens),
                          "verifications": len(verifies), "screen_spent": ss, "verify_spent": vs_,
                          "unused_in_round": int(available - ss - vs_)})

    def pending_in_verify_order(max_round: int) -> np.ndarray:
        idx = np.flatnonzero(screened & hit & ~verified & (s_round <= max_round))
        return idx[np.argsort(v_rank[idx], kind="stable")]

    if rounds == 1:                                                    # P1 paired
        if unit_cost:
            pairs = [int(i) for i in s_order[:cap // 2]]
        else:
            pairs, _ = _greedy(s_order, cs + cv, cap)
        buy(1, pairs, pairs, cap)
        n1 = len(pairs)
    elif rounds == 2:                                                  # P2 fixed split
        if fp is None:
            raise ValueError("P2 needs fp")
        if unit_cost:
            n1 = ((100 - fp) * cap) // 100
            r1 = [int(i) for i in s_order[:n1]]
        else:
            budget1 = ((100 - fp) * cap) // 100
            r1, _ = _greedy(s_order, cs, budget1)
            n1 = len(r1)
        buy(1, r1, [], cap)
        todo = pending_in_verify_order(1)
        if unit_cost:
            v2 = [int(j) for j in todo[:cap - spent]]
        else:
            v2, _ = _greedy(todo, cv, cap - spent)
        extra = []
        if terminal:
            left = cap - spent - int(sum(cv[j] for j in v2))
            extra, _ = _greedy([i for i in s_order if not screened[i]], cs, left)
        if v2 or extra:
            buy(2, extra, v2, cap - spent)
    elif rounds == 3:                                                  # P3 verify-hits, reserve, round 3
        if unit_cost:
            n_r1 = (cap + 1) // 2
            r1 = [int(i) for i in s_order[:n_r1]]
        else:
            r1, _ = _greedy(s_order, cs, (cap + 1) // 2)
        n1 = len(r1)
        buy(1, r1, [], cap)
        todo = pending_in_verify_order(1)
        if unit_cost:
            v2 = [int(j) for j in todo[:cap - spent]]
        else:
            v2, _ = _greedy(todo, cv, cap - spent)
        B2 = cap - spent - int(sum(cv[j] for j in v2))
        acc, used, res = [], 0, 0.0
        for j in s_order_r2:
            if screened[j]:
                continue
            if round2_count is not None:
                if len(acc) >= round2_count:
                    break
                acc.append(int(j))
                used += int(cs[j])
                res += float(u.p_s[j]) * float(cv[j])
                continue
            new_res = res + float(u.p_s[j]) * float(cv[j])
            if used + int(cs[j]) + math.ceil(round(new_res, 12)) <= B2:
                acc.append(int(j))
                used += int(cs[j])
                res = new_res
            else:
                break
        if used > B2:
            raise AssertionError("round-2 screens exceed B2")
        reserve_info = {"B2": int(B2), "accepted": len(acc), "reserve": round(res, 12)}
        avail2 = cap - spent
        if v2 or acc:
            buy(2, acc, v2, avail2)
        todo3 = np.array([j for j in pending_in_verify_order(2) if s_round[j] == 2], np.int64)
        if unit_cost:
            v3 = [int(j) for j in todo3[:cap - spent]]
        else:
            v3, _ = _greedy(todo3, cv, cap - spent)
        extra = []
        if terminal:
            left = cap - spent - int(sum(cv[j] for j in v3))
            extra, _ = _greedy([i for i in s_order if not screened[i]], cs, left)
        if v3 or extra:
            buy(3, extra, v3, cap - spent)
    else:
        raise ValueError(rounds)
    if spent > cap:
        raise AssertionError("cap exceeded")
    return _score(u, pred, rounds, fp, cap_kind, cp, terminal, cap, n1, lab, screened, verified, hit, vhit,
                  s_round, v_round, spent, per_round, cs, cv, reserve_info)


def _score(u, pred, rounds, fp, cap_kind, cp, terminal, cap, n1, lab, screened, verified, hit, vhit, s_round,
           v_round, spent, per_round, cs, cv, reserve_info) -> dict:
    h = u.hidden
    joint_true = h.hit_s & h.hit_v
    confirmed_mask = screened & verified & hit & vhit
    if not np.array_equal(confirmed_mask, screened & verified & joint_true):
        raise AssertionError("revealed calls differ from the hidden outcomes")
    used_rounds = sorted({r for r, s, v in lab.log if s or v})
    last = int(used_rounds[-1]) if used_rounds else 0
    final_screens = screened & (s_round == rounds)
    if rounds > 1 and not terminal and final_screens.any():
        raise AssertionError("screen bought in the final round")
    screens_ordered = [i for r, s, _ in lab.log for i in s]
    verifies_ordered = [i for r, _, v in lab.log for i in v]
    purchases = [[r, "screen", i] for r, s, _ in lab.log for i in s] + [[r, "verify", i] for r, _, v in lab.log for i in v]
    purchases.sort(key=lambda p: (p[0], p[1] != "screen"))
    return {
        "tissue": u.tissue, "line": u.sidm, "group": u.group, "role": u.role, "pred": pred, "rounds": rounds,
        "fp": fp, "cap_kind": cap_kind, "cp": cp, "terminal_reference": terminal, "n_menu": u.n, "M": u.cap(cp),
        "cap": int(cap), "n1": n1, "spent": int(spent), "unused_cap": int(cap - spent),
        "screens": int(screened.sum()), "screen_hits": int((screened & hit).sum()),
        "verifications": int(verified.sum()), "verification_hits": int((verified & vhit).sum()),
        "confirmed": int(confirmed_mask.sum()),
        "joint_hits_menu": int(joint_true.sum()),
        "missed_never_screened": int((~screened & joint_true).sum()),
        "missed_screened_not_verified": int((screened & ~verified & joint_true).sum()),
        "unverified_screen_hits": int((screened & hit & ~verified).sum()),
        "final_round_screens": int(final_screens.sum()),
        "final_round_screen_hits": int((final_screens & hit).sum()),
        "rounds_used": len(used_rounds), "last_round": last, "min_days": MIN_DAYS_PER_ROUND * last,
        "deadline_days": MIN_DAYS_PER_ROUND * rounds,
        "screen_units": int(cs[screened].sum()), "verify_units": int(cv[verified].sum()),
        "per_round": per_round, "reserve": reserve_info,
        "screens_ordered": screens_ordered, "verifies_ordered": verifies_ordered, "purchases": purchases,
    }


# ---------------------------------------------------------------------------- physical accounting
def pack_custom(items: list[tuple], controls: int = 200) -> dict:
    """Custom 1536-well plates: items (anchor, library, replicate plates, conflict key).

    Identical algorithm to reproducible_allocation_20261003 `replay.pack_custom` (replicate layer k on
    its own plates, first fit in (library, anchor) order, single agents per plate) with the control
    wells per plate as a parameter.
    """
    capacity = PLATE_WELLS - controls
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
                if plate["used"] + need <= capacity and (key is None or key not in plate["k"]):
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
            out["control_wells"] += controls
            out["single_anchor_wells"] += plate["sa"]
            out["single_library_wells"] += plate["sl"]
            out["combination_wells"] += plate["c"]
            out["empty_wells"] += capacity - plate["used"]
    return out


BASIC = ("orientation_measurements", "dose_points", "combination_wells", "combination_wells_builder_qc",
         "combination_wells_exported_rows", "replicate_plate_measurements", "failed_measurements",
         "native_plates_touched", "seeding_events_touched", "native_combination_wells_on_touched_plates")


def _zero() -> dict:
    d = {k: 0 for k in BASIC}
    for name in CONTROL_VARIANTS:
        d[f"custom_{name}"] = {"plates": 0, "control_wells": 0, "single_anchor_wells": 0, "single_library_wells": 0,
                               "combination_wells": 0, "empty_wells": 0}
    return d


def add_into(acc: dict, d: dict, w: float = 1.0) -> None:
    for k, v in d.items():
        if isinstance(v, dict):
            add_into(acc.setdefault(k, {}), v, w)
        elif isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool):
            acc[k] = acc.get(k, 0.0) + w * float(v)


def account_custom(u: Unit, rec: dict, layout: Layout) -> dict:
    """Resources of one campaign by round and branch (custom per-pair plates; native/events first touch)."""
    groups: dict[tuple[int, str], list[int]] = defaultdict(list)
    for r, branch, i in rec["purchases"]:
        groups[(r, branch)].append(int(i))
    out = {"total": _zero(), "by_branch": {"screen": _zero(), "verify": _zero()}, "by_round": {}}
    touched, events = set(), set()
    for (r, branch) in sorted(groups, key=lambda k: (k[0], k[1] != "screen")):
        idx = groups[(r, branch)]
        side = "s" if branch == "screen" else "v"
        orient, dp = getattr(u, f"orient_{side}"), getattr(u, f"plates_{side}")
        rw, bc, qc = getattr(u, f"rows_{side}"), getattr(u, f"barcodes_{side}"), getattr(u, f"qc_{side}")
        m = _zero()
        m["orientation_measurements"] = len(idx)
        m["dose_points"] = WELLS_PER_PLATE_MEASUREMENT * len(idx)
        m["combination_wells"] = WELLS_PER_PLATE_MEASUREMENT * int(sum(dp[i] for i in idx))
        if qc is not None:
            m["combination_wells_builder_qc"] = WELLS_PER_PLATE_MEASUREMENT * int(sum(qc[i] for i in idx))
            m["failed_measurements"] = int(sum(qc[i] == 0 for i in idx))
        m["combination_wells_exported_rows"] = DOSES * int(sum(rw[i] for i in idx))
        m["replicate_plate_measurements"] = int(sum(dp[i] for i in idx))
        items = [(orient[i][0], orient[i][1], int(dp[i]), None) for i in idx]
        for name, ctrl in CONTROL_VARIANTS.items():
            m[f"custom_{name}"] = pack_custom(items, ctrl)
        new = set().union(*[set(bc[i]) for i in idx]) - touched if idx else set()
        touched |= new
        m["native_plates_touched"] = len(new)
        m["native_combination_wells_on_touched_plates"] = DOSES * sum(layout.plate[b]["rows"] for b in new)
        ev = {event_of(layout, b) for b in new} - events
        events |= ev
        m["seeding_events_touched"] = len(ev)
        slot = out["by_round"].setdefault(str(r), {"screen": _zero(), "verify": _zero()})
        add_into(slot[branch], m)
        add_into(out["by_branch"][branch], m)
        add_into(out["total"], m)
    joint = {name: 0 for name in CONTROL_VARIANTS}
    for r in sorted({k[0] for k in groups}):
        items = []
        for branch in ("screen", "verify"):
            side = "s" if branch == "screen" else "v"
            orient, dp = getattr(u, f"orient_{side}"), getattr(u, f"plates_{side}")
            items += [(orient[i][0], orient[i][1], int(dp[i]), i) for i in groups.get((r, branch), [])]
        for name, ctrl in CONTROL_VARIANTS.items():
            joint[name] += pack_custom(items, ctrl)["plates"]
    out["custom_joint_plates_diagnostic"] = joint
    out["min_days"] = rec["min_days"]
    out["rounds_used"] = rec["rounds_used"]
    return out


# ---------------------------------------------------------------------------- aggregation
def line_values(records: list[dict], fields: tuple) -> dict:
    """(tissue, line) -> field -> mean over the two role assignments."""
    out: dict = {}
    for rec in records:
        slot = out.setdefault((rec["tissue"], rec["line"]), defaultdict(float))
        for f in fields:
            slot[f] += 0.5 * float(rec[f])
        slot["_roles"] += 1
    for k, v in out.items():
        if v["_roles"] != 2:
            raise AssertionError(f"line {k} lacks a role assignment")
    return out
