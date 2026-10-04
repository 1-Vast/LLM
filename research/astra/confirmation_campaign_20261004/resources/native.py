"""Native-plate campaign engine: buy whole Jaaks plate sets and credit every co-produced measurement.

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/native.py
- Purpose: the physically realisable counterpart of per-pair purchasing in the Jaaks layout. A native
  plate holds one line x one library doublet x all anchors, so a purchase cannot buy one orientation
  of one pair: it buys a plate set and produces every orientation measurement on it.
- Core points (prespecified in resources/plan.json before any outcome read of this workstream):
  - Action = (line, component): all release plates (design barcodes) of the line holding the
    component's library drugs ("doublet"; 2 Breast singletons). Cost = number of those plates (plate
    starts). For repeat lines this charges EVERY release plate behind the doublet (all seeding events),
    because the credited labels and calls are the frozen builder's, which pool all replicate rows of all
    events; a single-event action would reveal a different measurement than the one credited. Seeding
    events behind the purchased plates are reported.
  - Role SV: V-library plates carry the S-anchored (screen) orientations, S-library plates the
    verification orientations; VS reverses. Each menu orientation lives on exactly one component, a
    component is bought at most once, so every co-produced measurement is credited exactly once.
  - Endpoint: a menu pair is a confirmed discovery when its screen and verification orientations were
    both revealed by purchases before the deadline and both calls are synergistic (the contract's
    endpoint); reported by reveal order (screen first, same round, verification first). Off-menu
    measurements on bought plates (same-side pairs, cross pairs not in the menu) are legal information,
    never discoveries; counted.
  - Policies (pair-driven greedy, skip actions that do not fit the cap in plate starts):
    N1 one round: walk pairs in screen order, buy the missing screen and verification components of
    the pair if they fit. N2 two rounds (fp): round 1 screen components within ((100 - fp) K) // 100,
    round 2 only verification components that contain a pending round-1 hit, walked in verify order;
    no round-2 screens. N3 three rounds: round 1 screens within (K + 1) // 2; round 2 verification
    components for pending hits first, then screen components while plate starts + ceil(round(expected
    verification plate starts, 12)) fit K (expected = sum over unbought verification components j of
    c_j x (1 - prod(1 - p_s) over newly screened pairs whose verification sits on j)); skip, not stop;
    round 3 verification components for pending hits only.
- Interfaces: `native_view`, `run_native`, `account_native`, `native_caps`, `NATIVE_PCT_GRID`.
- Depends on: numpy; `frontier.py` (Unit, Lab, order_by); `layout.py`.
"""
from __future__ import annotations

import math

import numpy as np

from .frontier import Lab, Unit, order_by
from .layout import (ANCHOR_SINGLE_WELLS, CONTROL_VARIANTS, DOSES, LIBRARY_SINGLE_WELLS, MIN_DAYS_PER_ROUND,
                     PLATE_WELLS, Layout, event_of)

NATIVE_PCT_GRID = (5, 10, 15, 20, 30, 40, 50, 75, 100)
NATIVE_CONTROLS = {k: v for k, v in CONTROL_VARIANTS.items() if k in ("documented_200", "raw_min_216", "raw_max_254")}

_LINE_COMPS: dict = {}


def _line_comps(layout: Layout, tissue: str, sidm: str) -> list[int]:
    key = (id(layout), tissue, sidm)
    if key not in _LINE_COMPS:
        _LINE_COMPS[key] = sorted(k for (t, s, k) in layout.line_comp if t == tissue and s == sidm)
    return _LINE_COMPS[key]


def native_view(u: Unit, layout: Layout) -> dict:
    """Plate-set actions of one campaign and the menu/off-menu measurements each one produces."""
    tl = layout.tissues[u.tissue]
    comps = _line_comps(layout, u.tissue, u.sidm)
    screen_side = "V" if u.role == "SV" else "S"
    view = {"comps": {}, "screen_comps": [], "verify_comps": []}
    menu_s = {}
    menu_v = {}
    for i in range(u.n):
        menu_s.setdefault(int(u.comp_s[i]), []).append(i)
        menu_v.setdefault(int(u.comp_v[i]), []).append(i)
    menu_orients = set(u.orient_s) | set(u.orient_v)
    for k in comps:
        drugs = tl.components[k]
        sides = {tl.side.get(x) for x in drugs}
        if len(sides) != 1:
            raise AssertionError("a component spans both sides")
        side = sides.pop()
        barcodes = layout.line_comp[(u.tissue, u.sidm, k)]
        orients = layout.comp_orients[(u.tissue, u.sidm, k)]
        same_side = cross_off = 0
        same_side_rows = cross_off_rows = 0
        for (a, b), r in orients.items():
            if (a, b) in menu_orients:
                continue
            if tl.side.get(a) == tl.side.get(b):
                same_side += 1
                same_side_rows += r
            else:
                cross_off += 1
                cross_off_rows += r
        kind = "screen" if side == screen_side else "verify"
        on = menu_s.get(k, []) if kind == "screen" else menu_v.get(k, [])
        for i in on:
            bc = u.barcodes_s[i] if kind == "screen" else u.barcodes_v[i]
            if not set(bc) <= set(barcodes):
                raise AssertionError("an orientation's plates are not inside its component's plate set")
        view["comps"][k] = {"kind": kind, "cost": len(barcodes), "barcodes": barcodes, "pairs": list(on),
                            "orientations_on_plates": len(orients), "off_menu_same_side": same_side,
                            "off_menu_cross_not_menu": cross_off, "off_menu_same_side_rows": same_side_rows,
                            "off_menu_cross_rows": cross_off_rows,
                            "events": sorted({event_of(layout, b) for b in barcodes})}
        if on:
            view["screen_comps" if kind == "screen" else "verify_comps"].append(k)
    for i in range(u.n):
        if view["comps"][int(u.comp_s[i])]["kind"] != "screen" or view["comps"][int(u.comp_v[i])]["kind"] != "verify":
            raise AssertionError("orientation sits on the wrong side")
    view["menu_plates"] = int(sum(view["comps"][k]["cost"] for k in view["screen_comps"] + view["verify_comps"]))
    return view


def native_caps(view: dict, grid=NATIVE_PCT_GRID) -> dict:
    """Prespecified caps in plate starts: ceil(pct x menu-relevant release plates of the line / 100)."""
    p = view["menu_plates"]
    return {pct: -(-pct * p // 100) for pct in grid}


def run_native(u: Unit, view: dict, pred: str, rounds: int, K: int, *, fp: int | None = None,
               lab: Lab | None = None) -> dict:
    lab = lab or Lab(u.hidden)
    comps = view["comps"]
    s_order = order_by(u.scores[pred][0], u.rank)
    v_rank = np.empty(u.n, np.int64)
    v_rank[order_by(u.scores[pred][1], u.rank)] = np.arange(u.n)
    n = u.n
    s_round = np.zeros(n, np.int64)          # 0 = not revealed
    v_round = np.zeros(n, np.int64)
    hit = np.zeros(n, bool)
    vhit = np.zeros(n, bool)
    bought: dict[int, int] = {}              # component -> round
    spent = 0
    per_round: list[dict] = []
    reserve_info = None

    def pending(r: int) -> np.ndarray:
        idx = np.flatnonzero((s_round > 0) & (s_round < r) & hit & (v_round == 0))
        return idx[np.argsort(v_rank[idx], kind="stable")]

    def take(k: int, r: int, legal_check: bool) -> None:
        nonlocal spent
        if k in bought:
            raise AssertionError("component bought twice")
        if legal_check and comps[k]["kind"] == "verify":
            if not any(s_round[j] > 0 and s_round[j] < r and hit[j] and v_round[j] == 0 for j in comps[k]["pairs"]):
                raise AssertionError("verification plates bought without a pending earlier-round hit")
        bought[k] = r
        spent += comps[k]["cost"]

    def close_round(r: int, new: list[int], available: int) -> None:
        screens = sorted({i for k in new if comps[k]["kind"] == "screen" for i in comps[k]["pairs"]})
        verifies = sorted({i for k in new if comps[k]["kind"] == "verify" for i in comps[k]["pairs"]})
        if any(s_round[i] for i in screens) or any(v_round[i] for i in verifies):
            raise AssertionError("a measurement was credited twice")
        sres, vres = lab.reveal(r, screens, verifies)
        for i in screens:
            s_round[i], hit[i] = r, sres[i]
        for j in verifies:
            v_round[j], vhit[j] = r, vres[j]
        cost = int(sum(comps[k]["cost"] for k in new))
        per_round.append({"round": r, "available": int(available), "components": len(new),
                          "screen_components": sum(comps[k]["kind"] == "screen" for k in new),
                          "verify_components": sum(comps[k]["kind"] == "verify" for k in new),
                          "plate_starts": cost, "screen_orientations": len(screens),
                          "verification_orientations": len(verifies), "unused_in_round": int(available - cost)})

    def screen_pass(r: int, budget: int, new: list[int]) -> None:
        for i in s_order:
            k = int(u.comp_s[i])
            if s_round[i] or k in bought:
                continue
            if spent + comps[k]["cost"] <= budget:
                take(k, r, True)
                new.append(k)

    def verify_pass(r: int, budget: int, new: list[int]) -> None:
        for j in pending(r):
            k = int(u.comp_v[j])
            if k in bought:
                continue
            if spent + comps[k]["cost"] <= budget:
                take(k, r, True)
                new.append(k)

    if rounds == 1:
        new: list[int] = []
        for i in s_order:
            need = [k for k in dict.fromkeys((int(u.comp_s[i]), int(u.comp_v[i]))) if k not in bought]
            cost = sum(comps[k]["cost"] for k in need)
            if need and spent + cost <= K:
                for k in need:
                    take(k, 1, False)
                    new.append(k)
        close_round(1, new, K)
    elif rounds == 2:
        if fp is None:
            raise ValueError("N2 needs fp")
        new = []
        screen_pass(1, ((100 - fp) * K) // 100, new)
        close_round(1, new, K)
        avail = K - spent
        new = []
        verify_pass(2, K, new)
        if new:
            close_round(2, new, avail)
    elif rounds == 3:
        new = []
        screen_pass(1, (K + 1) // 2, new)
        close_round(1, new, K)
        avail = K - spent
        new = []
        verify_pass(2, K, new)
        newly: set[int] = set()
        accepted = 0
        res = 0.0
        for i in s_order:
            k = int(u.comp_s[i])
            if s_round[i] or k in bought:
                continue
            tentative = newly | set(comps[k]["pairs"])
            res_k = _expected_verification_plates(u, comps, bought, tentative)
            if spent + comps[k]["cost"] + math.ceil(round(res_k, 12)) <= K:
                take(k, 2, True)
                new.append(k)
                newly = tentative
                accepted += 1
                res = res_k
        reserve_info = {"accepted_screen_components": accepted, "reserve": round(res, 12)}
        if new:
            close_round(2, new, avail)
        avail = K - spent
        new = []
        verify_pass(3, K, new)
        if new:
            close_round(3, new, avail)
    else:
        raise ValueError(rounds)
    if spent > K:
        raise AssertionError("native cap exceeded")
    if rounds > 1 and any(comps[k]["kind"] == "screen" and r == rounds for k, r in bought.items()):
        raise AssertionError("screen plates bought in the final round")
    return _score_native(u, view, pred, rounds, fp, K, lab, bought, s_round, v_round, hit, vhit, spent, per_round,
                         reserve_info)


def _expected_verification_plates(u: Unit, comps: dict, bought: dict, pairs: set) -> float:
    by_comp: dict[int, float] = {}
    for i in pairs:
        j = int(u.comp_v[i])
        if j in bought:
            continue
        by_comp[j] = by_comp.get(j, 1.0) * (1.0 - float(u.p_s[i]))
    return float(sum(comps[j]["cost"] * (1.0 - q) for j, q in sorted(by_comp.items())))


def _score_native(u, view, pred, rounds, fp, K, lab, bought, s_round, v_round, hit, vhit, spent, per_round,
                  reserve_info) -> dict:
    h = u.hidden
    joint = h.hit_s & h.hit_v
    s_rev, v_rev = s_round > 0, v_round > 0
    conf = s_rev & v_rev & hit & vhit
    if not np.array_equal(conf, s_rev & v_rev & joint):
        raise AssertionError("revealed calls differ from the hidden outcomes")
    used = sorted({r for r, s, v in lab.log if s or v})
    last = int(used[-1]) if used else 0
    comps = view["comps"]
    return {
        "tissue": u.tissue, "line": u.sidm, "group": u.group, "role": u.role, "pred": pred, "rounds": rounds,
        "fp": fp, "cap_plates": int(K), "menu_plates": view["menu_plates"], "n_menu": u.n,
        "plate_starts": int(spent), "unused_cap": int(K - spent),
        "components_bought": len(bought),
        "screen_components": sum(comps[k]["kind"] == "screen" for k in bought),
        "verify_components": sum(comps[k]["kind"] == "verify" for k in bought),
        "screen_orientations": int(s_rev.sum()), "screen_hits": int((s_rev & hit).sum()),
        "verification_orientations": int(v_rev.sum()), "verification_hits": int((v_rev & vhit).sum()),
        "confirmed": int(conf.sum()),
        "confirmed_screen_first": int((conf & (s_round < v_round)).sum()),
        "confirmed_same_round": int((conf & (s_round == v_round)).sum()),
        "confirmed_verification_first": int((conf & (s_round > v_round)).sum()),
        "verifications_of_unscreened_pairs": int((v_rev & ~s_rev).sum()),
        "screens_never_verified": int((s_rev & ~v_rev).sum()),
        "screen_hits_never_verified": int((s_rev & hit & ~v_rev).sum()),
        "joint_hits_menu": int(joint.sum()), "missed": int((joint & ~conf).sum()),
        "rounds_used": len(used), "last_round": last, "min_days": MIN_DAYS_PER_ROUND * last,
        "per_round": per_round, "reserve": reserve_info,
        "bought": [[int(r), int(k)] for k, r in sorted(bought.items(), key=lambda x: (x[1], x[0]))],
    }


def account_native(u: Unit, view: dict, rec: dict, layout: Layout) -> dict:
    comps = view["comps"]
    tot = {"plate_starts": 0, "seeding_events": 0, "combination_wells_on_plates": 0, "single_agent_wells": 0,
           "menu_orientation_measurements": 0, "menu_combination_wells_credited": 0,
           "off_menu_orientation_measurements": 0, "off_menu_same_side": 0, "off_menu_cross_not_menu": 0,
           "off_menu_combination_wells": 0, "empty_wells_documented_model": 0}
    for name in NATIVE_CONTROLS:
        tot[f"control_wells_{name}"] = 0
    by_round: dict = {}
    events: set = set()
    for r, k in rec["bought"]:
        c = comps[k]
        m = {key: 0 for key in tot}
        m["plate_starts"] = c["cost"]
        ev = set(c["events"]) - events
        events |= ev
        m["seeding_events"] = len(ev)
        for b in c["barcodes"]:
            p = layout.plate[b]
            singles = ANCHOR_SINGLE_WELLS * p["anchors"] + LIBRARY_SINGLE_WELLS * p["libs"]
            m["combination_wells_on_plates"] += DOSES * p["rows"]
            m["single_agent_wells"] += singles
            for name, ctrl in NATIVE_CONTROLS.items():
                m[f"control_wells_{name}"] += ctrl
            m["empty_wells_documented_model"] += max(0, PLATE_WELLS - CONTROL_VARIANTS["documented_200"] - singles
                                                     - DOSES * p["rows"])
        m["menu_orientation_measurements"] = len(c["pairs"])
        rows = u.rows_s if c["kind"] == "screen" else u.rows_v
        m["menu_combination_wells_credited"] = DOSES * int(sum(rows[i] for i in c["pairs"]))
        m["off_menu_same_side"] = c["off_menu_same_side"]
        m["off_menu_cross_not_menu"] = c["off_menu_cross_not_menu"]
        m["off_menu_orientation_measurements"] = c["off_menu_same_side"] + c["off_menu_cross_not_menu"]
        m["off_menu_combination_wells"] = DOSES * (c["off_menu_same_side_rows"] + c["off_menu_cross_rows"])
        slot = by_round.setdefault(str(r), {"screen": None, "verify": None})
        if slot[c["kind"]] is None:
            slot[c["kind"]] = {key: 0 for key in tot}
        for key, v in m.items():
            slot[c["kind"]][key] += v
            tot[key] += v
    for r in by_round.values():
        for kind in ("screen", "verify"):
            if r[kind] is None:
                r[kind] = {key: 0 for key in tot}
    return {"total": tot, "by_round": by_round, "min_days": rec["min_days"], "rounds_used": rec["rounds_used"]}
