"""Independent re-implementation of the primary P2 confirmation campaign (verify workstream).

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/independent_check.py
- Purpose: re-implement, from the frozen contract v2 text only (no code of the design or resources
  workstreams is imported), the P2 two-round fixed-split campaign for every predictor, the HD
  development selection of C* and fp*, and the primary E contrast R - C*; then check the design
  workstream's per-campaign records against it exactly, plus budget conservation, legality
  (poisoned unpurchased outcomes leave purchases unchanged), condition identity (verification =
  other orientation of the same pair, line and role assignment) and reproducibility.
- Core points:
  - Integer arithmetic: M = (menu + 4) // 5, n1 = ((100 - fp) * M) // 100.
  - History rows H(t, r) = menu rows of panel <tissue>_<r> on hist(t) (E target: all HD lines of
    the tissue; HD target: other HD lines). Target and E rows never enter H.
  - Shrinkage k0 = 2 towards pooled quantities over H (all pairs).
  - Tie-break: rank from default_rng([20261004, tissue_code, line_index, role_index]).permutation;
    order = lexsort((rank, -round(score, 12))).
  - Outcomes reach a policy only through `Market`, which reveals a screen call only for a bought
    screen and a verification call only for a verified earlier-round screen hit.
  - Bootstrap and verdict exactly as the contract's inference / decision rules.
- Interfaces: pure functions (`cap_m`, `n_screen`, `tie_rank`, `order`, `shrunk_scores`, `run_p2`,
  `campaign`, `bootstrap`, `verdict`), `RoleData`, `Market`, `main()`.
- Depends on: numpy; the frozen builder research/astra/feedback_validation_20261003/jaaks.py and this
  study's common.py (logged exposed ticket) in `main()` only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
TISSUES = ("Breast", "Colon", "Pancreas")
TISSUE_CODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
ROLES = ("SV", "VS")
ROLE_INDEX = {"SV": 0, "VS": 1}
SEED = 20261004
K0 = 2.0
FP_GRID = tuple(range(10, 61, 5))
SIMPLE = ("S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod")
PREDICTORS = ("R",) + SIMPLE + ("S",)
TAU = 0.05
N_BOOT = 10_000


# ----------------------------------------------------------------------------------------- arithmetic
def cap_m(n_menu: int) -> int:
    return (int(n_menu) + 4) // 5


def n_screen(fp: int, m: int) -> int:
    if fp not in FP_GRID:
        raise ValueError(f"fp must be an integer percent on the grid, got {fp!r}")
    return ((100 - int(fp)) * int(m)) // 100


def tie_rank(tissue: str, line_index: int, role: str, n: int) -> np.ndarray:
    perm = np.random.default_rng([SEED, TISSUE_CODE[tissue], int(line_index), ROLE_INDEX[role]]).permutation(n)
    rank = np.empty(n, np.int64)
    rank[perm] = np.arange(n)
    return rank


def order(score: np.ndarray, rank: np.ndarray) -> np.ndarray:
    return np.lexsort((rank, -np.round(np.asarray(score, float), 12)))


# ----------------------------------------------------------------------------------------- data
@dataclass
class RoleData:
    """One tissue x role panel as flat arrays in builder row order."""

    tissue: str
    role: str
    lines: tuple            # SIDM per line index (builder lines tuple)
    drugs: tuple
    pair: np.ndarray        # int64 code a * n_drugs + b (unordered pair)
    line: np.ndarray        # line index
    screen_hit: np.ndarray  # bool
    valid_hit: np.ndarray   # bool
    ys: np.ndarray          # screen label
    yv: np.ndarray          # verification label

    def copy(self) -> "RoleData":
        return replace(self, pair=self.pair.copy(), line=self.line.copy(), screen_hit=self.screen_hit.copy(),
                       valid_hit=self.valid_hit.copy(), ys=self.ys.copy(), yv=self.yv.copy())


def role_data(panel, tissue: str, role: str) -> RoleData:
    lib = panel.library
    nd = len(lib.drugs)
    return RoleData(tissue, role, tuple(lib.lines), tuple(lib.drugs),
                    lib.a.astype(np.int64) * nd + lib.b.astype(np.int64), lib.c.astype(np.int64),
                    np.asarray(panel.screen_hit, bool).copy(), np.asarray(panel.valid_hit, bool).copy(),
                    np.asarray(lib.y, float).copy(), np.asarray(panel.valid_y, float).copy())


# ----------------------------------------------------------------------------------------- predictors
def history_mask(rd: RoleData, target: int, hist: np.ndarray) -> np.ndarray:
    hist = np.asarray(hist, np.int64)
    return np.isin(rd.line, hist[hist != target])


def shrunk_scores(rd: RoleData, hmask: np.ndarray, rows: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """predictor -> (screen score, verify score) for target rows, from history rows only."""
    hp = rd.pair[hmask]
    s = rd.screen_hit[hmask].astype(float)
    v = rd.valid_hit[hmask].astype(float)
    j = s * v
    ys, yv = rd.ys[hmask], rd.yv[hmask]
    if not (np.isfinite(ys).all() and np.isfinite(yv).all()):
        raise ValueError("NON_FINITE_HISTORY_LABEL")
    yb = (ys + yv) / 2.0
    if hp.size == 0:
        raise ValueError("EMPTY_HISTORY")
    pooled = {"ps": float(s.mean()), "pv": float(v.mean()), "psv": float(j.mean()),
              "yb": float(yb.mean()), "yv": float(yv.mean()), "ys": float(ys.mean())}
    pooled["pvs"] = float(j.sum() / s.sum()) if s.sum() > 0 else pooled["pv"]
    uniq, inv = np.unique(hp, return_inverse=True)
    n = np.bincount(inv, minlength=uniq.size).astype(float)
    sums = {k: np.bincount(inv, weights=w, minlength=uniq.size)
            for k, w in (("s", s), ("v", v), ("j", j), ("yb", yb), ("yv", yv), ("ys", ys))}
    tp = rd.pair[rows]
    pos = np.clip(np.searchsorted(uniq, tp), 0, max(uniq.size - 1, 0))
    found = uniq[pos] == tp

    def take(arr):
        return np.where(found, arr[pos], 0.0)

    nt = take(n)
    ps = (take(sums["s"]) + K0 * pooled["ps"]) / (nt + K0)
    pv = (take(sums["v"]) + K0 * pooled["pv"]) / (nt + K0)
    psv = (take(sums["j"]) + K0 * pooled["psv"]) / (nt + K0)
    pvs = (take(sums["j"]) + K0 * pooled["pvs"]) / (take(sums["s"]) + K0)
    mb = (take(sums["yb"]) + K0 * pooled["yb"]) / (nt + K0)
    mv = (take(sums["yv"]) + K0 * pooled["yv"]) / (nt + K0)
    ms = (take(sums["ys"]) + K0 * pooled["ys"]) / (nt + K0)
    return {"R": (psv, pvs), "S_both": (mb, mb), "L_v": (mv, mv), "C_s": (ps, ps), "C_v": (pv, pv),
            "C_mean": ((ps + pv) / 2.0, pv), "C_prod": (ps * pv, pv), "S": (ms, ms),
            "_p_s": (ps, ps), "_n_hist": (nt, nt), "_pooled": pooled}


# ----------------------------------------------------------------------------------------- market and policy
class Market:
    """Holds one campaign's hidden outcomes; reveals them only for legal purchases."""

    def __init__(self, screen_hit: np.ndarray, valid_hit: np.ndarray):
        self._s = np.asarray(screen_hit, bool)
        self._v = np.asarray(valid_hit, bool)
        self.screened: dict[int, int] = {}
        self.verified: dict[int, int] = {}
        self.log: list[tuple[str, int, int]] = []

    def screen(self, i: int, rnd: int) -> bool:
        i = int(i)
        if i in self.screened:
            raise RuntimeError("ILLEGAL: re-screen")
        self.screened[i] = rnd
        self.log.append(("screen", i, rnd))
        return bool(self._s[i])

    def verify(self, i: int, rnd: int) -> bool:
        i = int(i)
        if i not in self.screened or self.screened[i] >= rnd:
            raise RuntimeError("ILLEGAL: verify without an earlier-round screen")
        if not self._s[i]:
            raise RuntimeError("ILLEGAL: verify of a screen non-hit")
        if i in self.verified:
            raise RuntimeError("ILLEGAL: re-verify")
        self.verified[i] = rnd
        self.log.append(("verify", i, rnd))
        return bool(self._v[i])


def run_p2(screen_order: np.ndarray, verify_order: np.ndarray, m: int, n1: int, market: Market) -> dict:
    """Round 1: screen the first n1 of the screen order. Round 2: verify round-1 hits in verify order
    while spent < M. No round-2 screens."""
    spent = 0
    screens = [int(i) for i in screen_order[:n1]]
    revealed = {}
    for i in screens:
        revealed[i] = market.screen(i, 1)
        spent += 1
    hits = {i for i, h in revealed.items() if h}
    verifies, vcalls = [], []
    for i in verify_order:
        if spent >= m:
            break
        i = int(i)
        if i in hits:
            vcalls.append(market.verify(i, 2))
            verifies.append(i)
            spent += 1
    if spent > m:
        raise RuntimeError("CAP_EXCEEDED")
    return {"n1": n1, "screens": screens, "screen_hits": [i for i in screens if revealed[i]],
            "verifies": verifies, "verify_hits": [i for i, c in zip(verifies, vcalls) if c],
            "confirmed": int(sum(vcalls)), "spent": spent,
            "rounds_used": 0 if n1 == 0 else (2 if verifies else 1)}


def campaign(rd: RoleData, target: int, hist: np.ndarray, predictor: str, fp: int,
             scores: dict | None = None) -> dict:
    rows = np.flatnonzero(rd.line == target)
    n_menu = int(rows.size)
    m = cap_m(n_menu)
    n1 = n_screen(fp, m)
    if scores is None:
        scores = shrunk_scores(rd, history_mask(rd, target, hist), rows)
    if predictor == "oracle":
        joint = (rd.screen_hit[rows] & rd.valid_hit[rows]).astype(float)
        s_score = v_score = joint
    else:
        s_score, v_score = scores[predictor]
    rank = tie_rank(rd.tissue, target, rd.role, n_menu)
    market = Market(rd.screen_hit[rows], rd.valid_hit[rows])
    res = run_p2(order(s_score, rank), order(v_score, rank), m, n1, market)
    nd = len(rd.drugs)

    def names(local):
        return [[rd.drugs[int(rd.pair[rows[i]] // nd)], rd.drugs[int(rd.pair[rows[i]] % nd)]] for i in local]

    res.update({"tissue": rd.tissue, "role": rd.role, "sidm": rd.lines[target], "line_index": int(target),
                "predictor": predictor, "fp": int(fp), "n_menu": n_menu, "M": m,
                "screen_pairs": names(res["screens"]), "verify_pairs": names(res["verifies"]),
                "purchase_log": market.log})
    return res


# ----------------------------------------------------------------------------------------- inference
def bootstrap(r_by_tissue: dict[str, np.ndarray], c_by_tissue: dict[str, np.ndarray], *, n_boot: int = N_BOOT,
              seed: int = SEED) -> dict:
    """Contract inference: lines sorted by SIDM within tissue (caller's order), tissue order fixed."""
    rng = np.random.default_rng(seed)
    rel, ab = np.empty(n_boot), np.empty(n_boot)
    zero = 0
    for b in range(n_boot):
        rs, cs = [], []
        for t in TISSUES:
            n_t = len(r_by_tissue[t])
            idx = rng.integers(0, n_t, n_t)
            rs.append(np.asarray(r_by_tissue[t])[idx])
            cs.append(np.asarray(c_by_tissue[t])[idx])
        r, c = np.concatenate(rs), np.concatenate(cs)
        ab[b] = float(np.mean(r - c))
        if c.sum() == 0:
            zero += 1
            rel[b] = np.nan
        else:
            rel[b] = r.sum() / c.sum() - 1.0
    r_all = np.concatenate([np.asarray(r_by_tissue[t]) for t in TISSUES])
    c_all = np.concatenate([np.asarray(c_by_tissue[t]) for t in TISSUES])
    finite = rel[np.isfinite(rel)]
    return {"point_relative": float(r_all.sum() / c_all.sum() - 1.0) if c_all.sum() else None,
            "point_absolute_per_line": float(np.mean(r_all - c_all)),
            "sum_R": float(r_all.sum()), "sum_C": float(c_all.sum()), "n_lines": int(r_all.size),
            "relative_95": [float(x) for x in np.percentile(finite, [2.5, 97.5])] if finite.size else None,
            "absolute_95": [float(x) for x in np.percentile(ab, [2.5, 97.5])],
            "zero_denominator_resamples": zero, "mean_C_per_line": float(c_all.mean())}


def verdict(lo: float, hi: float, tau: float = TAU) -> str:
    if hi < 0:
        return "EXPLORATORY_HARM"
    if hi < tau:
        return "EXPLORATORY_SMALL_BENEFIT" if lo > 0 else "EXPLORATORY_WORTHWHILE_EXCLUDED"
    if lo <= 0:
        return "EXPLORATORY_UNRESOLVED"
    return "EXPLORATORY_WORTHWHILE" if lo > tau else "EXPLORATORY_BENEFIT_DETECTED"


def verdict_from_boot(boot: dict, tau: float = TAU) -> str:
    if boot["zero_denominator_resamples"] > 0.01 * N_BOOT:
        lo, hi = boot["absolute_95"]
        scale = tau * boot["mean_C_per_line"]
        return verdict(lo / boot["mean_C_per_line"], hi / boot["mean_C_per_line"], tau) if scale > 0 else "UNDEFINED"
    lo, hi = boot["relative_95"]
    return verdict(lo, hi, tau)


# ----------------------------------------------------------------------------------------- drivers
def line_split(rd: RoleData, part: dict) -> tuple[np.ndarray, np.ndarray]:
    index = {s: i for i, s in enumerate(rd.lines)}
    e = np.array(sorted(index[s] for s in part[rd.tissue]["E"]), np.int64)
    hd = np.array(sorted(index[s] for s in part[rd.tissue]["HD"]), np.int64)
    if len(set(e) & set(hd)) or len(e) + len(hd) != len(rd.lines):
        raise ValueError("PARTITION_MISMATCH")
    return e, hd


def evaluate(rds: dict, part: dict, targets: str, predictors, fps) -> dict:
    """(predictor, fp, sidm, role) -> campaign result. targets: 'E' (history = all HD) or 'HD' (other HD)."""
    out = {}
    for (tissue, role), rd in rds.items():
        e, hd = line_split(rd, part)
        for t in (e if targets == "E" else hd):
            rows = np.flatnonzero(rd.line == t)
            sc = shrunk_scores(rd, history_mask(rd, t, hd), rows)
            for p in predictors:
                for fp in fps:
                    out[(p, int(fp), rd.lines[t], role)] = campaign(rd, int(t), hd, p, int(fp), sc)
    return out


def line_values(results: dict, predictor: str, fp: int, sidms: list[str]) -> np.ndarray:
    return np.array([(results[(predictor, fp, s, "SV")]["confirmed"] + results[(predictor, fp, s, "VS")]["confirmed"])
                     / 2.0 for s in sidms])


def development_table(dev: dict, part: dict) -> dict:
    hd = [s for t in TISSUES for s in part[t]["HD"]]
    table = {p: {fp: float(line_values(dev, p, fp, hd).sum()) for fp in FP_GRID} for p in PREDICTORS}
    best = {}
    for p in PREDICTORS:
        top = max(table[p].values())
        best[p] = min(fp for fp in FP_GRID if table[p][fp] == top)
    c_star = None
    for p in SIMPLE:                                      # ties in the listed order
        if c_star is None or table[p][best[p]] > table[c_star][best[c_star]]:
            c_star = p
    return {"table": table, "best_fp": best, "C_star": c_star, "fp_star": best[c_star], "R_own_fp": best["R"]}


def condition_identity(panels: dict) -> dict:
    out = {}
    for t in TISSUES:
        sv, vs = panels[f"{t}_SV"], panels[f"{t}_VS"]
        same_rows = (np.array_equal(sv.library.a, vs.library.a) and np.array_equal(sv.library.b, vs.library.b)
                     and np.array_equal(sv.library.c, vs.library.c) and sv.library.lines == vs.library.lines)
        out[t] = {"same_rows_and_lines": bool(same_rows),
                  "SV_verify_call_eq_VS_screen_call": bool(np.array_equal(sv.valid_hit, vs.screen_hit)),
                  "SV_screen_call_eq_VS_verify_call": bool(np.array_equal(sv.screen_hit, vs.valid_hit)),
                  "SV_verify_label_eq_VS_screen_label": bool(np.array_equal(sv.valid_y, vs.library.y)),
                  "VS_verify_label_eq_SV_screen_label": bool(np.array_equal(vs.valid_y, sv.library.y)),
                  "rows": int(sv.library.y.size)}
    return out


def poison(rd: RoleData, target: int, purchased_screens: set, purchased_verifies: set, poison_lines: np.ndarray,
           seed: int) -> RoleData:
    """Copy with every outcome the campaign did not buy replaced: unpurchased target-line outcomes and
    all rows of `poison_lines` (lines that must never be history)."""
    rng = np.random.default_rng(seed)
    out = rd.copy()
    rows = np.flatnonzero(rd.line == target)
    for k, r in enumerate(rows):
        if k not in purchased_screens:
            out.screen_hit[r] = ~out.screen_hit[r]
            out.ys[r] = rng.normal(0, 50)
        if k not in purchased_verifies:
            out.valid_hit[r] = ~out.valid_hit[r]
            out.yv[r] = rng.normal(0, 50)
    other = np.isin(rd.line, poison_lines) & (rd.line != target)
    out.screen_hit[other] = rng.random(int(other.sum())) < 0.5
    out.valid_hit[other] = rng.random(int(other.sum())) < 0.5
    out.ys[other] = rng.normal(0, 50, int(other.sum()))
    out.yv[other] = rng.normal(0, 50, int(other.sum()))
    return out


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def strip(res: dict) -> dict:
    return {k: v for k, v in res.items() if k != "purchase_log"}


def main(argv=None) -> int:          # pragma: no cover - needs the exposed release
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "receipts/verification.json"))
    ap.add_argument("--records", default=str(HERE / "receipts/verify_campaigns.jsonl"))
    ap.add_argument("--selection", default=str(STUDY / "design/selection.json"))
    ap.add_argument("--fp-star", type=int, default=None, help="fp* as written in design/selection.json")
    ap.add_argument("--c-star", default=None, help="C* as written in design/selection.json")
    ap.add_argument("--r-own-fp", type=int, default=None, help="R's own HD-best fp as written in selection.json")
    args = ap.parse_args(argv)
    out, records = Path(args.out), Path(args.records)
    for p in (out, records):
        if p.exists():
            raise SystemExit(f"REFUSE_OVERWRITE: {p}")
    sys.path.insert(0, str(ROOT))
    from research.astra.confirmation_campaign_20261004 import common
    from research.astra.feedback_validation_20261003 import jaaks

    ticket = common.exposed_ticket("independent re-implementation of P2 primary (R vs C*) and HD selection; "
                                   "legality, budget, identity, reproducibility checks", "verify")
    panels, report, _ = jaaks.build_panels(ticket)
    part = common.partition()
    selection = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    rds = {(t, r): role_data(panels[f"{t}_{r}"], t, r) for t in TISSUES for r in ROLES}
    receipt = {"owner": "verify", "evidence_status": "EXPLORATORY (Jaaks 2022 exposed)",
               "access_log_entry": {k: ticket.get(k) for k in ("logged_at", "purpose", "data_sha256", "freeze_sha256")
                                    if k in ticket},
               "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "selection_file_sha256": hashlib.sha256(Path(args.selection).read_bytes()).hexdigest(),
               "condition_identity": condition_identity(panels)}

    # 1. development selection, independently
    dev = evaluate(rds, part, "HD", PREDICTORS, FP_GRID)
    mine = development_table(dev, part)
    receipt["development_selection_independent"] = mine
    receipt["selection_file_values"] = {k: selection.get(k) for k in selection if not isinstance(selection.get(k), (dict, list))}
    fp_star = int(args.fp_star if args.fp_star is not None else selection_value(selection, "fp_star"))
    c_star = str(args.c_star if args.c_star is not None else selection_value(selection, "C_star"))
    r_own = args.r_own_fp if args.r_own_fp is not None else selection_value(selection, "R_own_fp", required=False)
    if c_star not in SIMPLE or fp_star not in FP_GRID:
        raise SystemExit(f"BAD_SELECTION: {c_star!r} {fp_star!r}")
    receipt["selection_match"] = {"C_star": c_star == mine["C_star"], "fp_star": fp_star == mine["fp_star"],
                                  "R_own_fp": (None if r_own is None else int(r_own) == mine["R_own_fp"])}

    # 2. E evaluation for every predictor at fp*, R at its own fp, twice (reproducibility)
    fps = sorted({fp_star, mine["R_own_fp"]})
    ev = evaluate(rds, part, "E", PREDICTORS + ("oracle",), fps)
    ev2 = evaluate({k: role_data(panels[f"{k[0]}_{k[1]}"], *k) for k in rds}, part, "E", PREDICTORS + ("oracle",), fps)
    d1 = digest({str(k): strip(v) for k, v in ev.items()})
    d2 = digest({str(k): strip(v) for k, v in ev2.items()})
    receipt["reproducibility"] = {"in_process_rerun_identical": d1 == d2, "e_results_digest": d1}

    # 3. budget / legality invariants on my own campaigns
    bad = [str(k) for k, v in ev.items() if v["spent"] > v["M"] or any(rnd != 1 for kind, _, rnd in v["purchase_log"] if kind == "screen")
           or any(rnd != 2 for kind, _, rnd in v["purchase_log"] if kind == "verify")
           or not set(v["verifies"]) <= set(v["screen_hits"])]
    receipt["own_invariants"] = {"campaigns": len(ev), "violations": bad}

    # 4. poisoning test on every E campaign of R and C* at fp* (and R at own fp)
    poison_fail = []
    n_poison = 0
    for (tissue, role), rd in rds.items():
        e, hd = line_split(rd, part)
        for t in e:
            for p, fp in {("R", fp_star), (c_star, fp_star), ("R", mine["R_own_fp"])}:
                ref = ev[(p, fp, rd.lines[t], role)]
                bad_rd = poison(rd, int(t), set(ref["screens"]), set(ref["verifies"]), e, seed=int(t) * 7 + ROLE_INDEX[role])
                again = campaign(bad_rd, int(t), hd, p, fp)
                n_poison += 1
                if again["purchase_log"] != ref["purchase_log"] or again["confirmed"] != ref["confirmed"]:
                    poison_fail.append(str((p, fp, rd.lines[t], role)))
    receipt["legality_poisoning"] = {"campaigns_tested": n_poison, "purchases_changed": poison_fail,
                                     "poisoned": "target-line unpurchased screen and verification calls flipped and labels "
                                                 "randomised; every other E line's rows randomised (same role panel)"}

    # 5. primary contrast and verdict from my per-line values
    def by_tissue(p, fp):
        return {t: line_values(ev, p, fp, sorted(part[t]["E"])) for t in TISSUES}

    prim = bootstrap(by_tissue("R", fp_star), by_tissue(c_star, fp_star))
    prim["verdict"] = verdict_from_boot(prim)
    receipt["primary_independent"] = {"C_star": c_star, "fp_star": fp_star, **prim}
    own = bootstrap(by_tissue("R", mine["R_own_fp"]), by_tissue(c_star, fp_star))
    receipt["own_fp_secondary_independent"] = own
    receipt["e_totals_at_fp_star"] = {p: float(sum(line_values(ev, p, fp_star, sorted(part[t]["E"])).sum() for t in TISSUES))
                                      for p in PREDICTORS + ("oracle",)}

    with records.open("x", encoding="utf-8") as fh:
        for k, v in sorted(ev.items(), key=lambda kv: str(kv[0])):
            fh.write(json.dumps(strip(v), sort_keys=True) + "\n")
    receipt["records_file"] = str(records.relative_to(ROOT)).replace("\\", "/")
    receipt["records_sha256"] = hashlib.sha256(records.read_bytes()).hexdigest()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps({k: receipt[k] for k in ("selection_match", "reproducibility", "primary_independent")}, indent=1,
                     default=str))
    return 0


def selection_value(selection: dict, key: str, required: bool = True):
    """Find a key in design/selection.json, searching one level of nesting."""
    if key in selection:
        return selection[key]
    for v in selection.values():
        if isinstance(v, dict) and key in v:
            return v[key]
    if required:
        raise KeyError(f"selection.json has no {key}")
    return None


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(main())
