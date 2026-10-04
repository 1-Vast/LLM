"""EXPLORATORY confirmation campaigns: predictors, P2/P3 policies, campaign logs and inference (design workstream).

File summary
- Path: research/astra/confirmation_campaign_20261004/design/campaign.py
- Purpose: implement the frozen campaign contract v2 (`protocol/campaign_contract.json`) on the frozen
  Jaaks 2022 builder panels: shrunk two-orientation history predictors (R, S_both, L_v, C_s, C_v,
  C_mean, C_prod, S, oracle), the shared tie-break, the two-round fixed split P2 (measurement or
  combination-well cap) and the three-round verify-hits P3 with its exact reserve rule, per-round
  campaign logs (frozen-prediction hash, purchases, reveals, scores, update), menu metrics
  (concordance AUC, Brier / log loss), the registered tissue-stratified line bootstrap, the
  decision rule, a two-way line x pair bootstrap and the power analysis for R - C*.
- Core points:
  - Jaaks 2022 was already opened: everything computed with it is EXPLORATORY.
  - History rows H for target t, role r: every menu row of panel <tissue>_<r> whose line is in
    hist(t). Callers pass a `TissueData` view from which the target and every E line (or, for the
    all-lines sensitivity, only the target) have been removed; `make_target` asserts it.
  - The `Lab` holds a campaign's hidden outcomes, reveals only purchases at the end of a round and
    refuses illegal purchases (re-screens, verifying an unscreened / same-round / non-hit pair,
    screens in the final round, spending above the cap).
  - Integer arithmetic: M = (menu + 4) // 5; n1 = ((100 - fp) x M) // 100; P3 round 1 = (M + 1) // 2;
    W = ceil(Fraction(M) x sum(c_s + c_v) / (2 x menu)). Orders = np.lexsort((rank, -round(score, 12))).
- Interfaces: `TissueData`, `build_tissues`, `restrict`, `history_quantities`, `predictor_scores`,
  `Target`, `make_target`, `truth_of`, `Lab`, `run_p2`, `run_p3`, `menu_metrics`, `line_values`,
  `arm_table`, `boot_contrast`, `decision`, `two_way`, `power_analysis`, `jsonable`, `sha256_file`.
- Depends on: numpy; scipy (rankdata). Panels come from the frozen
  `research.astra.feedback_validation_20261003.jaaks.build_panels` (not imported here).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata

STATUS = ("EXPLORATORY: Jaaks et al. 2022 was opened by feedback_validation_20261003 and analysed by "
          "reproducible_allocation_20261003; development and evaluation on exposed data, not confirmation")
TISSUES = ("Breast", "Colon", "Pancreas")
TISSUE_CODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
ROLES = ("SV", "VS")
ROLE_INDEX = {"SV": 0, "VS": 1}
SEED = 20261004
K0 = 2.0
FP_GRID = tuple(range(10, 61, 5))
SIMPLE = ("S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod")
PREDICTORS = ("R",) + SIMPLE + ("S",)
ORACLE = "oracle"
ARMS = PREDICTORS + (ORACLE,)
PROBABILITY_ARMS = {"R": "p_sv", "C_prod": "p_s x p_v"}
TAU = 0.05
RESAMPLES = 10_000
CLIP = 1e-6
DECIMALS = 12
WELLS_PER_PLATE = 14
DAYS_PER_ROUND = 4


class IllegalPurchase(RuntimeError):
    """A policy tried to buy something the contract does not allow."""


# ============================================================================ data
@dataclass
class TissueData:
    """One tissue's menu rows (builder order) with both role assignments' outcomes and costs."""

    tissue: str
    code: int
    lines: tuple                      # the builder's per-tissue lines tuple (never a subset)
    c: np.ndarray                     # line index per menu row
    pid: np.ndarray                   # unordered pair id per menu row (tissue-wide)
    pairs: list                       # [s, v] per menu row
    arrays: dict                      # role -> {y_s, h_s, y_v, h_v}
    cost: dict | None = None          # role -> {cost_s, cost_v}: 14 x design plates (pre-QC)
    barcodes: dict | None = None      # role -> {screen: [tuple], verify: [tuple]} design plates
    present_lines: frozenset = field(default_factory=frozenset)

    @property
    def n_rows(self) -> int:
        return int(self.c.size)


def build_tissues(panels: dict, candidates: dict, design: dict | None = None) -> dict[str, TissueData]:
    """Builder panels -> per-tissue data with condition-identity checks (VS = swapped SV, same rows)."""
    out: dict[str, TissueData] = {}
    for tissue in sorted({p.stratum for p in panels.values()}):
        sv, vs = panels[f"{tissue}_SV"], panels[f"{tissue}_VS"]
        lib = sv.library
        for arr in ("a", "b", "c"):
            if not np.array_equal(getattr(lib, arr), getattr(vs.library, arr)):
                raise AssertionError(f"CONDITION_IDENTITY: {tissue} SV and VS menus differ in {arr}")
        checks = {"VS screen label = SV verification label": np.array_equal(vs.library.y, sv.valid_y),
                  "VS verification label = SV screen label": np.array_equal(vs.valid_y, lib.y),
                  "VS screen call = SV verification call": np.array_equal(vs.screen_hit, sv.valid_hit),
                  "VS verification call = SV screen call": np.array_equal(vs.valid_hit, sv.screen_hit)}
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            raise AssertionError(f"CONDITION_IDENTITY: {tissue}: {bad}")
        if np.any(sv.valid_missing) or np.any(vs.valid_missing):
            raise AssertionError("verification outcomes missing in the menu")
        if list(candidates[tissue]["line_sidm"]) != list(lib.lines):
            raise AssertionError(f"{tissue}: candidates line order differs from the builder lines tuple")
        pairs = [list(p) for p in candidates[tissue]["pairs_s_v"]]
        if len(pairs) != len(lib):
            raise AssertionError(f"{tissue}: candidates pairs differ from the menu")
        n_drugs = len(lib.drugs)
        _, pid = np.unique(lib.a.astype(np.int64) * n_drugs + lib.b, return_inverse=True)
        arrays = {}
        for role, panel in (("SV", sv), ("VS", vs)):
            arrays[role] = {"y_s": panel.library.y.astype(float).copy(), "h_s": panel.screen_hit.astype(bool).copy(),
                            "y_v": panel.valid_y.astype(float).copy(), "h_v": panel.valid_hit.astype(bool).copy()}
            if not (np.all(np.isfinite(arrays[role]["y_s"])) and np.all(np.isfinite(arrays[role]["y_v"]))):
                raise AssertionError("non-finite menu label")
        cost = barcodes = None
        if design is not None:
            cost, barcodes = {}, {}
            for role in ROLES:
                cs, cv, bs, bv = [], [], [], []
                for row, (s, v) in enumerate(pairs):
                    sidm = lib.lines[int(lib.c[row])]
                    fwd, back = (s, v), (v, s)                    # (anchor, library)
                    o_s, o_v = (fwd, back) if role == "SV" else (back, fwd)
                    info_s = design["orient"][(tissue, sidm, o_s[0], o_s[1])]
                    info_v = design["orient"][(tissue, sidm, o_v[0], o_v[1])]
                    cs.append(WELLS_PER_PLATE * int(info_s[0]))
                    cv.append(WELLS_PER_PLATE * int(info_v[0]))
                    bs.append(tuple(info_s[2]))
                    bv.append(tuple(info_v[2]))
                    if set(info_s[2]) & set(info_v[2]):
                        raise AssertionError("screen and verification orientations share a plate")
                cost[role] = {"cost_s": np.array(cs, np.int64), "cost_v": np.array(cv, np.int64)}
                barcodes[role] = {"screen": bs, "verify": bv}
            if not (np.array_equal(cost["SV"]["cost_s"], cost["VS"]["cost_v"])
                    and np.array_equal(cost["SV"]["cost_v"], cost["VS"]["cost_s"])):
                raise AssertionError("CONDITION_IDENTITY: role costs are not swapped")
        out[tissue] = TissueData(tissue, TISSUE_CODE[tissue], tuple(lib.lines), lib.c.astype(np.int64).copy(),
                                 pid.astype(np.int64), pairs, arrays, cost, barcodes,
                                 frozenset(lib.lines[k] for k in np.unique(lib.c)))
    return out


def restrict(T: TissueData, keep_lines) -> TissueData:
    """View with only the rows of `keep_lines` (both role assignments); line indices and pair ids unchanged."""
    keep_lines = set(keep_lines)
    unknown = keep_lines - set(T.lines)
    if unknown:
        raise ValueError(f"unknown lines {sorted(unknown)}")
    idx = [T.lines.index(s) for s in sorted(keep_lines)]
    mask = np.isin(T.c, idx)
    rows = np.flatnonzero(mask)
    arrays = {r: {k: v[rows].copy() for k, v in a.items()} for r, a in T.arrays.items()}
    cost = None if T.cost is None else {r: {k: v[rows].copy() for k, v in a.items()} for r, a in T.cost.items()}
    barcodes = None if T.barcodes is None else {r: {k: [v[i] for i in rows] for k, v in a.items()}
                                                 for r, a in T.barcodes.items()}
    return TissueData(T.tissue, T.code, T.lines, T.c[rows].copy(), T.pid[rows].copy(), [T.pairs[i] for i in rows],
                      arrays, cost, barcodes, frozenset(T.lines[k] for k in np.unique(T.c[rows])))


# ============================================================================ predictors
def history_quantities(H: TissueData, role: str, target_pid: np.ndarray) -> dict[str, np.ndarray]:
    """Contract v2 pooled quantities on H (all pairs) and k0 = 2 shrinkage per pair, at the target's pairs."""
    if H.n_rows == 0:
        raise ValueError("empty history")
    A = H.arrays[role]
    pid = H.pid
    size = int(max(pid.max(), np.max(target_pid))) + 1
    hs, hv = A["h_s"].astype(float), A["h_v"].astype(float)
    joint = hs * hv
    ys, yv = A["y_s"].astype(float), A["y_v"].astype(float)
    n = np.bincount(pid, minlength=size).astype(float)

    def shrunk(z: np.ndarray) -> np.ndarray:
        pooled = float(z.mean())
        return (np.bincount(pid, weights=z, minlength=size) + K0 * pooled) / (n + K0)

    pooled_vs = float(joint.sum() / hs.sum()) if hs.sum() > 0 else float(hv.mean())
    n_s = np.bincount(pid, weights=hs, minlength=size)
    n_j = np.bincount(pid, weights=joint, minlength=size)
    p_v_s = (n_j + K0 * pooled_vs) / (n_s + K0)
    out = {"p_s": shrunk(hs), "p_v": shrunk(hv), "p_sv": shrunk(joint), "p_v_s": p_v_s,
           "S_both": shrunk((ys + yv) / 2.0), "L_v": shrunk(yv), "S": shrunk(ys)}
    t = np.asarray(target_pid, np.int64)
    res = {k: v[t].copy() for k, v in out.items()}
    res["n_hist"] = n[t].copy()
    return res


def predictor_scores(q: dict) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """predictor -> (screen score, verify score), contract v2."""
    return {"R": (q["p_sv"], q["p_v_s"]),
            "S_both": (q["S_both"], q["S_both"]),
            "L_v": (q["L_v"], q["L_v"]),
            "C_s": (q["p_s"], q["p_s"]),
            "C_v": (q["p_v"], q["p_v"]),
            "C_mean": ((q["p_s"] + q["p_v"]) / 2.0, q["p_v"]),
            "C_prod": (q["p_s"] * q["p_v"], q["p_v"]),
            "S": (q["S"], q["S"])}


def tie_rank(code: int, line_index: int, role_index: int, n: int) -> np.ndarray:
    perm = np.random.default_rng([SEED, int(code), int(line_index), int(role_index)]).permutation(n)
    rank = np.empty(n, np.int64)
    rank[perm] = np.arange(n)
    return rank


def menu_order(score: np.ndarray, rank: np.ndarray) -> np.ndarray:
    """Full-menu order: descending score rounded to 12 decimals, ties by the shared rank."""
    score = np.asarray(score, float)
    if not np.all(np.isfinite(score)):
        raise ValueError("non-finite score")
    return np.lexsort((rank, -np.round(score, DECIMALS)))


def score_hash(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(np.round(np.asarray(a, float), DECIMALS), dtype="<f8").tobytes())
        h.update(b"|")
    return h.hexdigest()


@dataclass
class Target:
    """Public information of one campaign (target line x role assignment); no target outcome inside."""

    tissue: str
    code: int
    sidm: str
    line_index: int
    role: str
    role_index: int
    rows: np.ndarray                   # menu rows in the full tissue data (builder order)
    pid: np.ndarray
    n: int
    M: int
    W: int | None
    cost_s: np.ndarray | None
    cost_v: np.ndarray | None
    rank: np.ndarray
    q: dict                            # history quantities at the target's pairs
    scores: dict                       # predictor -> (screen, verify)
    history_lines: tuple
    barcodes_s: list | None = None
    barcodes_v: list | None = None

    @property
    def p_s(self) -> np.ndarray:
        return self.q["p_s"]

    def order(self, score) -> np.ndarray:
        return menu_order(score, self.rank)


def cap_M(n: int) -> int:
    return (int(n) + 4) // 5


def make_target(full: TissueData, H: TissueData, sidm: str, role: str, *, allowed_history,
                forbidden=()) -> Target:
    """Campaign context for (sidm, role) with history view H; asserts the history-row contract."""
    li = full.lines.index(sidm)
    hist_lines = tuple(sorted(H.present_lines))
    if sidm in H.present_lines:
        raise AssertionError(f"LEAK: target line {sidm} in its own history")
    if set(hist_lines) & set(forbidden):
        raise AssertionError(f"LEAK: forbidden lines in history: {sorted(set(hist_lines) & set(forbidden))}")
    if not set(hist_lines) <= set(allowed_history):
        raise AssertionError("history lines outside the allowed set")
    if H.tissue != full.tissue or H.lines != full.lines:
        raise AssertionError("history view from another tissue")
    rows = np.flatnonzero(full.c == li)
    n = int(rows.size)
    if n == 0:
        raise ValueError(f"empty menu for {sidm}")
    pid = full.pid[rows].copy()
    q = history_quantities(H, role, pid)
    M = cap_M(n)
    cost_s = cost_v = None
    W = None
    bs = bv = None
    if full.cost is not None:
        cost_s = full.cost[role]["cost_s"][rows].copy()
        cost_v = full.cost[role]["cost_v"][rows].copy()
        W = int(math.ceil(Fraction(M) * Fraction(int(cost_s.sum() + cost_v.sum()), 2 * n)))
        bs = [full.barcodes[role]["screen"][i] for i in rows]
        bv = [full.barcodes[role]["verify"][i] for i in rows]
    return Target(full.tissue, full.code, sidm, li, role, ROLE_INDEX[role], rows, pid, n, M, W, cost_s, cost_v,
                  tie_rank(full.code, li, ROLE_INDEX[role], n), q, predictor_scores(q), hist_lines, bs, bv)


def subset_target(tg: Target, positions: np.ndarray) -> Target:
    """Campaign restricted to menu positions (same-condition diagnostic); relative tie order preserved."""
    pos = np.asarray(positions, np.int64)
    n = int(pos.size)
    q = {k: v[pos].copy() for k, v in tg.q.items()}
    return Target(tg.tissue, tg.code, tg.sidm, tg.line_index, tg.role, tg.role_index, tg.rows[pos].copy(),
                  tg.pid[pos].copy(), n, cap_M(n), None, None, None, tg.rank[pos].copy(), q, predictor_scores(q),
                  tg.history_lines, None, None)


def truth_of(full: TissueData, tg: Target) -> dict:
    """Hidden outcomes of a campaign (for the Lab and for post-campaign scoring only)."""
    A = full.arrays[tg.role]
    return {k: A[k][tg.rows].copy() for k in ("y_s", "h_s", "y_v", "h_v")}


def oracle_scores(truth: dict) -> tuple[np.ndarray, np.ndarray]:
    joint = (truth["h_s"] & truth["h_v"]).astype(float)
    return joint, joint.copy()


def arm_scores(tg: Target, arm: str, truth: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    if arm == ORACLE:
        if truth is None:
            raise ValueError("oracle needs the truth (headroom reference only)")
        return oracle_scores(truth)
    return tg.scores[arm]


# ============================================================================ lab and state
class Lab:
    """Hidden outcomes of one campaign: reveals purchases at the end of a round; refuses illegal purchases."""

    def __init__(self, truth: dict, cost_s: np.ndarray, cost_v: np.ndarray, cap: int, deadline: int):
        self._y_s = np.asarray(truth["y_s"], float).copy()
        self._h_s = np.asarray(truth["h_s"], bool).copy()
        self._y_v = np.asarray(truth["y_v"], float).copy()
        self._h_v = np.asarray(truth["h_v"], bool).copy()
        n = self._y_s.size
        self.cs, self.cv = np.asarray(cost_s, np.int64), np.asarray(cost_v, np.int64)
        self.cap, self.deadline = int(cap), int(deadline)
        self.screen_round = np.zeros(n, np.int64)
        self.verify_round = np.zeros(n, np.int64)
        self.hit_seen = np.zeros(n, bool)
        self.spent = 0
        self.round = 0
        self.log: list = []

    def run_round(self, r: int, screens, verifies) -> dict:
        screens, verifies = [int(i) for i in screens], [int(i) for i in verifies]
        if r <= self.round or r > self.deadline:
            raise IllegalPurchase(f"round {r} after round {self.round} or beyond the deadline {self.deadline}")
        if screens and r == self.deadline:
            raise IllegalPurchase("screens in the final round cannot be verified before the deadline")
        if len(set(screens)) != len(screens) or len(set(verifies)) != len(verifies):
            raise IllegalPurchase("duplicate purchase in one round")
        for i in screens:
            if self.screen_round[i]:
                raise IllegalPurchase(f"re-screen of {i}")
        for i in verifies:
            if not (0 < self.screen_round[i] < r):
                raise IllegalPurchase(f"verify of {i} without an earlier-round screen")
            if not self.hit_seen[i]:
                raise IllegalPurchase(f"verify of {i} whose revealed screen call was not synergistic")
            if self.verify_round[i]:
                raise IllegalPurchase(f"re-verify of {i}")
        cost = int(self.cs[screens].sum()) + int(self.cv[verifies].sum())
        if self.spent + cost > self.cap:
            raise IllegalPurchase(f"spend {self.spent + cost} exceeds the cap {self.cap}")
        self.spent += cost
        self.round = r
        out = {"screens": [[i, float(self._y_s[i]), bool(self._h_s[i])] for i in screens],
               "verifies": [[i, float(self._y_v[i]), bool(self._h_v[i])] for i in verifies]}
        for i in screens:
            self.screen_round[i] = r
            self.hit_seen[i] = self._h_s[i]
        for i in verifies:
            self.verify_round[i] = r
        self.log.append((r, screens, verifies))
        return out


class State:
    """What the campaign knows: purchases and the outcomes they revealed."""

    def __init__(self, n: int):
        self.screened = np.zeros(n, bool)
        self.screen_round = np.zeros(n, np.int64)
        self.y = np.full(n, np.nan)
        self.hit = np.zeros(n, bool)
        self.verified = np.zeros(n, bool)
        self.verify_round = np.zeros(n, np.int64)
        self.valid = np.zeros(n, bool)
        self.spent = 0

    def update(self, r: int, reveals: dict, cs: np.ndarray, cv: np.ndarray) -> None:
        for i, y, h in reveals["screens"]:
            self.screened[i], self.screen_round[i], self.y[i], self.hit[i] = True, r, y, h
            self.spent += int(cs[i])
        for i, _, h in reveals["verifies"]:
            self.verified[i], self.verify_round[i], self.valid[i] = True, r, h
            self.spent += int(cv[i])

    def summary(self) -> dict:
        return {"screened": int(self.screened.sum()), "screen_hits": int((self.screened & self.hit).sum()),
                "verified": int(self.verified.sum()), "confirmed": int((self.verified & self.hit & self.valid).sum()),
                "spent": int(self.spent)}


def _costs(tg: Target, unit: str) -> tuple[np.ndarray, np.ndarray, int]:
    if unit == "measurement":
        one = np.ones(tg.n, np.int64)
        return one, one.copy(), tg.M
    if unit == "wells":
        if tg.cost_s is None:
            raise ValueError("wells cap needs design costs")
        return tg.cost_s, tg.cost_v, int(tg.W)
    raise ValueError(unit)


def _greedy_skip(order, cost: np.ndarray, budget: int) -> list[int]:
    take, used = [], 0
    for i in order:
        c = int(cost[i])
        if used + c <= budget:
            take.append(int(i))
            used += c
    return take


def _do_round(r: int, lab: Lab, st: State, screens, verifies, cs, cv, pred_hash: str, screen_score, verify_score,
              cap: int, logs: list, extra: dict | None = None) -> None:
    entry = {"round": r, "predictions_sha256": pred_hash, "cap_remaining_before": int(cap - st.spent),
             "screens": [int(i) for i in screens], "verifies": [int(i) for i in verifies]}
    if extra:
        entry.update(extra)
    if screens or verifies:
        reveals = lab.run_round(r, screens, verifies)
        # scored before the update: the frozen predictions of the revealed items against their outcomes
        sh = [h for _, _, h in reveals["screens"]]
        vh = [h for _, _, h in reveals["verifies"]]
        entry["reveals"] = reveals
        entry["scored"] = {
            "screen_hits": int(sum(sh)), "verify_hits": int(sum(vh)),
            "mean_frozen_screen_score": float(np.mean([screen_score[i] for i in screens])) if screens else None,
            "mean_frozen_verify_score": float(np.mean([verify_score[i] for i in verifies])) if verifies else None}
        st.update(r, reveals, cs, cv)
    else:
        entry["reveals"] = None
        entry["scored"] = None
    entry["update"] = st.summary()
    logs.append(entry)


def _record(tg: Target, truth: dict, st: State, lab: Lab, logs: list, arm: str, policy: str, unit: str,
            cap: int, cs, cv, **extra) -> dict:
    """Post-campaign scoring (truth joined only after the deadline)."""
    sh, vh = np.asarray(truth["h_s"], bool), np.asarray(truth["h_v"], bool)
    joint = sh & vh
    screens = [i for r, s, _ in lab.log for i in s]
    verifies = [i for r, _, v in lab.log for i in v]
    if not np.array_equal(st.hit[st.screened], sh[st.screened]) or not np.array_equal(st.valid[st.verified],
                                                                                         vh[st.verified]):
        raise AssertionError("revealed outcomes differ from truth")
    confirmed = int((st.verified & st.hit & st.valid).sum())
    if confirmed != int((st.verified & joint).sum()):
        raise AssertionError("observed confirmations differ from truth")
    used = sorted({r for r, s, v in lab.log if s or v})
    rec = {"arm": arm, "policy": policy, "unit": unit, "tissue": tg.tissue, "line": tg.sidm,
           "line_index": tg.line_index, "role": tg.role, "n_menu": tg.n, "M": tg.M, "W": tg.W, "cap": int(cap),
           "screens": screens, "screen_rounds": [int(st.screen_round[i]) for i in screens],
           "screen_hits": [i for i in screens if sh[i]], "verifies": verifies,
           "verification_hits": [i for i in verifies if vh[i]],
           "n_screens": len(screens), "n_screen_hits": int(sh[screens].sum()) if screens else 0,
           "n_verifications": len(verifies), "n_verification_hits": int(vh[verifies].sum()) if verifies else 0,
           "confirmed": confirmed, "spent": int(st.spent), "unused": int(cap - st.spent),
           "spent_screen": int(cs[screens].sum()) if screens else 0,
           "spent_verify": int(cv[verifies].sum()) if verifies else 0,
           "menu_joint_hits": int(joint.sum()),
           "missed_unscreened": int((~st.screened & joint).sum()),
           "missed_screened_not_verified": int((st.screened & joint & ~st.verified).sum()),
           "unverified_screen_hits": int((st.screened & sh & ~st.verified).sum()),
           "rounds_used": len(used), "last_round": int(used[-1]) if used else 0,
           "min_days": DAYS_PER_ROUND * len(used),
           "dose_points": WELLS_PER_PLATE * (len(screens) + len(verifies))}
    if tg.cost_s is not None:
        rec["combination_wells"] = int(tg.cost_s[screens].sum() + tg.cost_v[verifies].sum()) if (screens or verifies) else 0
    if tg.barcodes_s is not None:
        plates = set()
        for i in screens:
            plates |= set(tg.barcodes_s[i])
        for i in verifies:
            plates |= set(tg.barcodes_v[i])
        rec["native_plates"] = sorted(plates)
        rec["n_native_plates"] = len(plates)
    rec.update(extra)
    rec["rounds"] = logs
    return rec


# ============================================================================ policies
def run_p2(tg: Target, truth: dict, arm: str, fp: int, unit: str = "measurement") -> dict:
    """P2: round 1 screens the first n1 of the screen order; round 2 verifies round-1 hits in verify order."""
    if fp not in FP_GRID:
        raise ValueError(f"fp {fp} not in the registered grid")
    cs, cv, cap = _costs(tg, unit)
    screen_score, verify_score = arm_scores(tg, arm, truth)
    s_order, v_order = tg.order(screen_score), tg.order(verify_score)
    pred = score_hash(screen_score, verify_score)
    lab, st, logs = Lab(truth, cs, cv, cap, deadline=2), State(tg.n), []
    if unit == "measurement":
        n1 = ((100 - fp) * tg.M) // 100
        screens = [int(i) for i in s_order[:n1]]
        budget1 = n1
    else:
        budget1 = ((100 - fp) * cap) // 100
        screens = _greedy_skip(s_order, cs, budget1)
        n1 = len(screens)
    _do_round(1, lab, st, screens, [], cs, cv, pred, screen_score, verify_score, cap, logs,
              {"round1_budget": int(budget1)})
    hits = [int(i) for i in v_order if st.screened[i] and st.hit[i]]
    if unit == "measurement":
        verifies = hits[:max(0, cap - st.spent)]
    else:
        verifies = _greedy_skip(hits, cv, cap - st.spent)
    _do_round(2, lab, st, [], verifies, cs, cv, pred, screen_score, verify_score, cap, logs)
    return _record(tg, truth, st, lab, logs, arm, "P2", unit, cap, cs, cv, fp=int(fp), n1=int(n1),
                   n1_zero=int(n1 == 0), pending_hits_unverified=int(len(hits) - len(verifies)))


def p3_reserve_screens(candidates, p_s: np.ndarray, B2: int) -> list[int]:
    """Accept j iff (k + 1) + ceil(round(sum p_s over accepted + j, 12)) <= B2; stop at the first failure."""
    take, acc = [], 0.0
    if B2 <= 0:
        return take
    for j in candidates:
        total = acc + float(p_s[j])
        if (len(take) + 1) + math.ceil(round(total, DECIMALS)) <= B2:
            take.append(int(j))
            acc = total
        else:
            break
    return take


def run_p3(tg: Target, truth: dict, arm: str, round2_order=None, round2_count: int | None = None,
           arm_label: str | None = None) -> dict:
    """P3 (measurement cap, 3 rounds). `round2_order(state) -> (order, predictions)` replaces the static
    screen order for round-2 screens only (feedback diagnostics); `round2_count` fixes the number of
    round-2 screens (gate oracle with the same count). Verify order and reserve p_s never change."""
    cs, cv, cap = _costs(tg, "measurement")
    screen_score, verify_score = arm_scores(tg, arm, truth)
    s_order, v_order = tg.order(screen_score), tg.order(verify_score)
    pred = score_hash(screen_score, verify_score)
    lab, st, logs = Lab(truth, cs, cv, cap, deadline=3), State(tg.n), []
    n_r1 = (tg.M + 1) // 2
    _do_round(1, lab, st, [int(i) for i in s_order[:n_r1]], [], cs, cv, pred, screen_score, verify_score, cap, logs)
    hits1 = [int(i) for i in v_order if st.screened[i] and st.hit[i]]
    v2 = min(len(hits1), tg.M - n_r1)
    verifies2 = hits1[:v2]
    B2 = tg.M - n_r1 - v2
    pred2, extra = pred, {"B2": int(B2)}
    score2 = screen_score
    if round2_order is None:
        order2 = s_order
    else:
        order2, prediction = round2_order(st)
        pred2 = score_hash(prediction, verify_score)
        score2 = prediction
        extra["round2_predictions_sha256"] = score_hash(prediction)
    cand = [int(j) for j in order2 if not st.screened[j]]
    if round2_count is None:
        screens2 = p3_reserve_screens(cand, tg.p_s, B2)
    else:
        screens2 = cand[:int(round2_count)]
        if len(screens2) > B2:
            raise IllegalPurchase("round-2 count exceeds B2")
    _do_round(2, lab, st, screens2, verifies2, cs, cv, pred2, score2, verify_score, cap, logs, extra)
    hits2 = [int(i) for i in v_order if st.screened[i] and st.hit[i] and st.screen_round[i] == 2]
    verifies3 = hits2[:max(0, cap - st.spent)]
    _do_round(3, lab, st, [], verifies3, cs, cv, pred, screen_score, verify_score, cap, logs)
    return _record(tg, truth, st, lab, logs, arm_label or arm, "P3", "measurement", cap, cs, cv, n_r1=int(n_r1),
                   v2=int(v2), B2=int(B2), round2_screens=len(screens2),
                   round2_screen_hits=int(sum(bool(truth["h_s"][j]) for j in screens2)))


# ============================================================================ menu metrics
def auc(score: np.ndarray, y: np.ndarray) -> float | None:
    """AUC of the rounded score against a binary outcome; ties 0.5; None if 0 or all positives."""
    y = np.asarray(y, bool)
    pos, neg = int(y.sum()), int((~y).sum())
    if pos == 0 or neg == 0:
        return None
    r = rankdata(np.round(np.asarray(score, float), DECIMALS))
    return float((r[y].sum() - pos * (pos + 1) / 2.0) / (pos * neg))


def prob_scores(p: np.ndarray, y: np.ndarray) -> dict:
    p = np.clip(np.asarray(p, float), CLIP, 1 - CLIP)
    y = np.asarray(y, float)
    return {"brier": float(np.mean((p - y) ** 2)),
            "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
            "mean_pred": float(p.mean()), "observed_rate": float(y.mean()),
            "calibration_in_the_large": float(p.mean() - y.mean())}


def menu_metrics(tg: Target, truth: dict) -> dict:
    joint = np.asarray(truth["h_s"], bool) & np.asarray(truth["h_v"], bool)
    out = {"tissue": tg.tissue, "line": tg.sidm, "role": tg.role, "n_menu": tg.n, "menu_joint_hits": int(joint.sum()),
           "concordance": {}, "probability": {}}
    for arm in ARMS:
        s, _ = arm_scores(tg, arm, truth)
        out["concordance"][arm] = auc(s, joint)
    out["probability"]["R"] = prob_scores(tg.scores["R"][0], joint)
    out["probability"]["C_prod"] = prob_scores(tg.scores["C_prod"][0], joint)
    return out


# ============================================================================ aggregation
NUMERIC = ("cap", "spent", "unused", "spent_screen", "spent_verify", "n_screens", "n_screen_hits", "n_verifications",
           "n_verification_hits", "confirmed", "menu_joint_hits", "missed_unscreened", "missed_screened_not_verified",
           "unverified_screen_hits", "rounds_used", "min_days", "dose_points", "combination_wells", "n_native_plates",
           "n_seeding_events", "n1_zero", "round2_screens", "round2_screen_hits", "pending_hits_unverified")


def line_values(records: list[dict]) -> dict[tuple[str, str], dict]:
    """(tissue, line) -> field -> mean over the line's role assignments (never two units)."""
    by: dict = {}
    for r in records:
        by.setdefault((r["tissue"], r["line"]), []).append(r)
    out = {}
    for key, recs in by.items():
        roles = sorted(r["role"] for r in recs)
        if roles != ["SV", "VS"]:
            raise AssertionError(f"{key}: role assignments {roles}")
        out[key] = {f: float(np.mean([r[f] for r in recs])) for f in NUMERIC if all(f in r for r in recs)}
        out[key]["by_role_confirmed"] = {r["role"]: r["confirmed"] for r in recs}
    return out


def sort_keys(keys) -> list[tuple[str, str]]:
    return sorted(keys, key=lambda k: (TISSUES.index(k[0]) if k[0] in TISSUES else 99, k[0], k[1]))


def arm_table(lv: dict, keys: list) -> dict:
    tot = {f: float(sum(lv[k][f] for k in keys)) for f in NUMERIC if all(f in lv[k] for k in keys)}
    n = len(keys)
    tot["lines"] = n
    tot["mean_confirmed_per_line"] = tot["confirmed"] / n if n else None
    tot["confirmation_rate"] = tot["confirmed"] / tot["n_verifications"] if tot.get("n_verifications") else None
    tot["first_screen_yield"] = tot["n_screen_hits"] / tot["n_screens"] if tot.get("n_screens") else None
    for f in ("rounds_used", "min_days", "n_native_plates", "n_seeding_events"):
        if f in tot:
            tot[f"mean_{f}_per_line"] = tot[f] / n if n else None
    tot["by_tissue_confirmed"] = {}
    for k in keys:
        tot["by_tissue_confirmed"][k[0]] = tot["by_tissue_confirmed"].get(k[0], 0.0) + lv[k]["confirmed"]
    tot["by_role_confirmed"] = {r: float(sum(lv[k]["by_role_confirmed"][r] for k in keys)) for r in ROLES}
    return tot


# ============================================================================ inference
def boot_indices(keys: list, resamples: int = RESAMPLES, seed: int = SEED) -> list[np.ndarray]:
    """Registered scheme: rng = default_rng(seed); keys sorted by SIDM within tissue; for b: for tissue in order:
    rng.integers(0, n_t, n_t). Returns resample index arrays into `keys` (which must be sorted)."""
    if list(keys) != sort_keys(keys):
        raise ValueError("keys must be sorted (tissue order, SIDM)")
    groups = [np.array([j for j, k in enumerate(keys) if k[0] == t]) for t in TISSUES]
    extra = sorted({k[0] for k in keys} - set(TISSUES))
    groups += [np.array([j for j, k in enumerate(keys) if k[0] == t]) for t in extra]
    groups = [g for g in groups if g.size]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(resamples):
        out.append(np.concatenate([g[rng.integers(0, g.size, g.size)] for g in groups]))
    return out


def boot_contrast(x: np.ndarray, y: np.ndarray, keys: list, idx: list[np.ndarray] | None = None) -> dict:
    """x - y over lines: absolute mean per-line difference and relative gain sum(x)/sum(y) - 1, 95% percentile."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    idx = boot_indices(keys) if idx is None else idx
    d = x - y
    rel = np.full(len(idx), np.nan)
    absd = np.empty(len(idx))
    zero = 0
    for b, ii in enumerate(idx):
        sy = y[ii].sum()
        absd[b] = d[ii].mean()
        if sy == 0:
            zero += 1
        else:
            rel[b] = x[ii].sum() / sy - 1.0
    fin = np.isfinite(rel)
    out = {"lines": int(x.size), "sum_x": float(x.sum()), "sum_y": float(y.sum()),
           "mean_x": float(x.mean()) if x.size else None, "mean_y": float(y.mean()) if y.size else None,
           "mean_diff": float(d.mean()) if d.size else None,
           "mean_diff_ci": [float(v) for v in np.percentile(absd, [2.5, 97.5])],
           "relative_gain": float(x.sum() / y.sum() - 1.0) if y.sum() else None,
           "relative_gain_ci": [float(v) for v in np.percentile(rel[fin], [2.5, 97.5])] if fin.any() else None,
           "resamples": len(idx), "resamples_zero_denominator": int(zero),
           "better": int((d > 0).sum()), "worse": int((d < 0).sum()), "tied": int((d == 0).sum())}
    return out


def decision(c: dict, tau: float = TAU) -> dict:
    """Contract v2 decision rule on the 95% interval [L, U] of the relative gain (EXPLORATORY_ prefix)."""
    use = "relative"
    if c["resamples_zero_denominator"] > 0.01 * c["resamples"] or c["relative_gain_ci"] is None:
        use = "absolute (tau x mean comparator yield)"
        L, U = c["mean_diff_ci"]
        t = tau * c["mean_y"]
    else:
        L, U = c["relative_gain_ci"]
        t = tau
    if U < 0:
        cat, action = "HARM", "STOP"
    elif L <= 0:
        cat, action = ("WORTHWHILE_EXCLUDED", "STOP (worthwhile benefit ruled out)") if U < t else \
            ("UNRESOLVED", "MODIFY: no claim; more or qualified data needed")
    elif U < t:
        cat, action = "SMALL_BENEFIT", "R is a free development-grade default; STOP pursuing confirmation"
    elif L > t:
        cat, action = "WORTHWHILE", "CONTINUE: freeze a confirmatory protocol for an untouched source, conditional on data qualification"
    else:
        cat, action = "BENEFIT_DETECTED", "CONTINUE: freeze a confirmatory protocol for an untouched source, conditional on data qualification"
    return {"verdict": f"EXPLORATORY_{cat}", "action": action, "interval_used": use, "L": float(L), "U": float(U),
            "threshold": float(t), "tau_relative": tau}


def two_way(mats_x: dict, mats_y: dict, keys: list, resamples: int = RESAMPLES, seed: int = SEED + 1) -> dict:
    """Lines (within tissue) x pairs (within tissue) bootstrap of sum(x)/sum(y) - 1.

    mats_*: tissue -> (lines_of_tissue x pairs_of_tissue) confirmed counts (0.5 per role); rows follow `keys`
    order within the tissue. rng = default_rng(seed); for b: for tissue: line idx, then pair multiplicities."""
    tissues = [t for t in TISSUES if t in mats_x] + sorted(set(mats_x) - set(TISSUES))
    rng = np.random.default_rng(seed)
    rel = np.full(resamples, np.nan)
    for b in range(resamples):
        sx = sy = 0.0
        for t in tissues:
            X, Y = mats_x[t], mats_y[t]
            nl, npairs = X.shape
            li = rng.integers(0, nl, nl)
            w = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs).astype(float)
            sx += float((X[li] @ w).sum())
            sy += float((Y[li] @ w).sum())
        rel[b] = sx / sy - 1.0 if sy else np.nan
    fin = np.isfinite(rel)
    return {"relative_gain_ci": [float(v) for v in np.percentile(rel[fin], [2.5, 97.5])], "resamples": resamples,
            "seed": seed, "zero_denominator": int((~fin).sum())}


def pair_matrices(records: list[dict], targets: dict, keys: list) -> dict:
    """tissue -> lines x pairs matrix of confirmed pairs (0.5 per role); pairs indexed by tissue pair id."""
    lines_by = {t: [k for k in keys if k[0] == t] for t in {k[0] for k in keys}}
    keyset = set(keys)
    pid_of = {(t, sidm, role): tg.pid for (t, sidm, role), tg in targets.items() if (t, sidm) in keyset}
    pairs_by: dict = {t: set() for t in lines_by}
    for (t, _, _), pid in pid_of.items():
        pairs_by[t] |= {int(p) for p in pid}
    pair_index = {t: {p: j for j, p in enumerate(sorted(ps))} for t, ps in pairs_by.items()}
    mats = {t: np.zeros((len(lines_by[t]), len(pair_index[t]))) for t in lines_by}
    row_of = {k: lines_by[k[0]].index(k) for k in keys}
    for r in records:
        k = (r["tissue"], r["line"])
        if k not in row_of:
            continue
        pid = pid_of[(r["tissue"], r["line"], r["role"])]
        for i in r["verification_hits"]:
            if i in r["screen_hits"]:
                mats[k[0]][row_of[k], pair_index[k[0]][int(pid[i])]] += 0.5
    return mats


def _strata_sizes(n: int, base: dict[str, int]) -> dict[str, int]:
    total = sum(base.values())
    raw = {t: n * v / total for t, v in base.items()}
    out = {t: int(math.floor(v)) for t, v in raw.items()}
    rest = n - sum(out.values())
    for t in sorted(raw, key=lambda t: -(raw[t] - out[t]))[:rest]:
        out[t] += 1
    return out


def power_analysis(d: np.ndarray, y: np.ndarray, strata: np.ndarray, *, base_sizes: dict[str, int],
                   ns=(61, 64, 100, 125, 150, 200, 250, 300, 400, 500, 750, 1000),
                   effects=(-0.05, 0.0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20), sims: int = 4000,
                   tau: float = TAU, seed: int = SEED) -> dict:
    """Power / precision of the relative gain sum(R)/sum(C*) - 1 from development per-line values.

    Per-line structure kept: z_l = d_l - G y_l (G = development ratio); a scenario with true relative effect
    delta uses d' = z + delta x y. Analytic: delta-method SE of the ratio; simulation: tissue-stratified
    resampling of development lines at size n, 95% delta-method interval per simulated study."""
    d, y, strata = np.asarray(d, float), np.asarray(y, float), np.asarray(strata)
    G = float(d.sum() / y.sum())
    z = d - G * y
    sd_rel1 = float(np.std(z, ddof=1) / y.mean())          # SE x sqrt(n) of the ratio (unstratified)
    z975 = float(norm.ppf(0.975))
    analytic, simulated = {}, {}
    rng = np.random.default_rng(seed)
    groups = {t: np.flatnonzero(strata == t) for t in np.unique(strata)}
    for n in ns:
        se = sd_rel1 / math.sqrt(n)
        analytic[str(n)] = {"se_relative": se, "ci_half_width": z975 * se,
                            "by_effect": {f"{e:+.3f}": {"P_L_gt_0": float(norm.cdf(e / se - z975)),
                                                         "P_L_gt_tau": float(norm.cdf((e - tau) / se - z975)),
                                                         "P_U_lt_tau": float(norm.cdf((tau - e) / se - z975))}
                                          for e in effects}}
        sizes = _strata_sizes(n, base_sizes)
        sim_eff = {}
        for e in effects:
            dd = z + e * y
            hits = np.zeros(3)
            widths = np.empty(sims)
            for s in range(sims):
                ii = np.concatenate([groups[t][rng.integers(0, groups[t].size, sizes[t])] for t in sizes
                                     if t in groups and sizes[t] > 0])
                xs, ys_ = dd[ii], y[ii]
                g = xs.sum() / ys_.sum()
                zz = xs - g * ys_
                se_s = np.std(zz, ddof=1) / (ys_.mean() * math.sqrt(ii.size))
                lo, hi = g - z975 * se_s, g + z975 * se_s
                hits += [lo > 0, lo > tau, hi < tau]
                widths[s] = hi - lo
            sim_eff[f"{e:+.3f}"] = {"P_L_gt_0": float(hits[0] / sims), "P_L_gt_tau": float(hits[1] / sims),
                                    "P_U_lt_tau": float(hits[2] / sims), "median_ci_width": float(np.median(widths))}
        simulated[str(n)] = {"strata_sizes": sizes, "by_effect": sim_eff}
    return {"development_relative_gain": G, "development_lines": int(d.size), "sd_influence_relative_per_sqrt_line": sd_rel1,
            "mean_comparator_yield_per_line": float(y.mean()), "tau": tau, "analytic_delta_method": analytic,
            "simulation": {"sims": sims, "seed": seed, "interval": "95% delta-method per simulated study",
                           "results": simulated},
            "notes": ["true effect scenarios keep the development per-line deviations z = d - G y",
                      "demonstrating L > tau needs a true effect above tau; no claim of 80% power at delta = tau",
                      "the development contrast uses C* selected on the same HD lines (winner's curse favours C*)"]}


# ============================================================================ utilities
def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k) if not isinstance(k, tuple) else "|".join(map(str, k)): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, (set, frozenset)):
        return sorted(jsonable(v) for v in obj)
    return obj


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj, *, overwrite: bool = False) -> str:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"NO_OVERWRITE: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(obj), indent=1), encoding="utf-8")
    return sha256_file(path)
