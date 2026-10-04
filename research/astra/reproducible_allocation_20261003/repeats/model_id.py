"""Phase 2 (EXPLORATORY): does purchased-screen feedback predict an independent measurement?

File summary
- Path: research/astra/reproducible_allocation_20261003/repeats/model_id.py
- Purpose: identify the scalar correction `validation prediction = V0 + lambda x F` of `repeats/plan.json`
  on the already-opened Jaaks 2022 screen, for two independent targets reported separately:
  (i) the same-condition repeat (same orientation, a later seeding event; 14 repeat lines) and
  (ii) the registered role-swapped validation (all 125 lines). Lambda is fitted on development lines
  only (leave-one-repeat-line-out for (i), 5 tissue-stratified line folds for (ii)); a target line's
  validation / repeat labels are never used to fit anything applied to that line.
- Core points:
  - V0 = shrunk history mean of the validation label (k0 = 2); S0 = frozen TransferWorld static prior;
    F_U = TransferWorld posterior mean (purchased screen labels) - S0 for unpurchased candidates;
    F_P = y_screen - S0 for purchased candidates. lambda = sum_l a_l / sum_l b_l over development lines.
  - Arms, metrics, folds, strongest-baseline selection and the stop rule follow plan.json.
  - Event labels (target i) use the Phase 1 plate -> seeding-event table and the authors' QC/call rule.
  - Development worlds are built on libraries from which the evaluation lines were removed.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.repeats.model_id [--workers N]`;
  `... model_id --key-results results/phase2_<stamp>` writes `receipts/phase2_key_results.json`;
  `event_table`, `event_arrays`, `unit_table`, `fit_lambda`, `predictions`, `unit_metrics`, `shrunk_mean`.
- Depends on: numpy, pandas, scikit-learn; the frozen feedback-validation `jaaks`, `study`, `verdict`
  modules and `research.certified_discovery` (imported, never edited); `..common.exposed_ticket`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import pandas as pd

from research.astra.feedback_validation_20261003 import jaaks
from research.astra.feedback_validation_20261003.study import WORLD, Panel
from research.certified_discovery import agent
from research.certified_discovery.world import TransferWorld

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
K0 = 2.0
FOLD_SEED = 20261004
N_FOLDS = 5
PURCHASE = 0.20
ROUND1 = 0.10
TOPK = 0.10
VERIFY = 0.25
MIN_ELIGIBLE = 20
RANDOM_SEEDS = (0, 1, 2, 3, 4)
LAMBDA_TOL = 0.10
BOOT = 2000
EPS = 1e-6
REPEAT_LINES = ("AU565", "BT-474", "CAL-85-1", "HCC1937", "MFM-223", "HCT-15", "HT-29", "SK-CO-1", "SW620",
                "KP-1N", "KP-4", "MZ1-PC", "PA-TU-8988T", "SUIT-2")
SCHEMES = ("chrono", "reverse")
U_CONT = ("U_V0", "U_lambda", "U_lambda1", "U_screen_post", "U_screen_static")
P_CONT = ("P_V0", "P_lambda", "P_lambda1", "P_screen")
U_PROB = ("p_pair",)
P_PROB = ("p_pair", "p_cond", "p_cond_pair")
U_BASELINES = ("U_V0", "U_lambda1", "U_screen_post", "U_screen_static")
P_BASELINES = ("P_V0", "P_lambda1", "P_screen")
YIELD_ARMS = ("history_mean", "U_V0", "U_lambda", "U_screen_post")


# ----------------------------------------------------------------------------------------------- labels
def event_table(ticket: dict, plates: pd.DataFrame, path: Path = jaaks.RELEASE) -> pd.DataFrame:
    """Per (tissue, line, anchor, library, seeding event): authors' QC, label and call within the event."""
    if not ticket or ticket.get("data_sha256") != jaaks.sha256(path):
        raise PermissionError("TICKET_REQUIRED: event_table needs an exposed_ticket for this file")
    raw = jaaks._read(path, jaaks.DESIGN_COLUMNS + jaaks.OUTCOME_COLUMNS)
    qc_fail = (raw["SYNERGY_RMSE"] > jaaks.RMSE_MAX) | (raw["LIBRARY_RMSE"] > jaaks.RMSE_MAX)
    missing = raw["Synergy"].isna() | raw["SYNERGY_DELTA_EMAX"].isna() | raw["SYNERGY_OBS_EMAX"].isna()
    frame = raw[~qc_fail & ~missing].merge(plates[["BARCODE", "event", "seeded"]], on="BARCODE", how="left")
    if frame["event"].isna().any():
        raise ValueError("UNMAPPED_PLATES: rows without a seeding event")
    frame["syn"] = frame["Synergy"].astype(str).str.strip().str.upper().map(
        {"TRUE": 1.0, "FALSE": 0.0, "1": 1.0, "0": 0.0, "1.0": 1.0, "0.0": 0.0})
    if frame["syn"].isna().any():
        raise ValueError("UNPARSEABLE_SYNERGY")
    keys = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID", "event"]
    per_conc = frame.groupby(keys + ["ANCHOR_CONC"]).agg(syn=("syn", "mean"), demax=("SYNERGY_DELTA_EMAX", "mean"),
                                                         seeded=("seeded", "first")).reset_index()
    per_conc["call"] = per_conc["syn"] >= 0.5
    per = per_conc.groupby(keys).agg(hit=("call", "any"), y=("demax", "max"), seeded=("seeded", "first"),
                                     concs=("call", "size")).reset_index()
    per["y"] = 100.0 * per["y"]
    return per


def event_arrays(panels: dict[str, Panel], candidates: dict, events: pd.DataFrame,
                 repeat_sidms: set[str]) -> dict[str, dict[str, dict[str, np.ndarray]]]:
    """panel -> scheme -> {y1, h1, y2, h2, y3, h3} over the panel's library rows (NaN outside repeat lines).

    Screen orientation of replicate SV = S drug anchored, V drug titrated; VS = the reverse. R1/R2/R3 are the
    first three seeding events of that ordered combination in date order ('chrono') or reverse date order."""
    events = events[events["SIDM"].isin(repeat_sidms)]
    by_key = {k: g.sort_values("seeded") for k, g in events.groupby(["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID"])}
    out: dict = {}
    for name, panel in panels.items():
        lib = panel.library
        tissue = panel.stratum
        pairs = candidates[tissue]["pairs_s_v"]
        n = len(lib)
        arrays = {s: {k: np.full(n, np.nan) for k in ("y1", "h1", "y2", "h2", "y3", "h3")} for s in SCHEMES}
        for row in range(n):
            sidm = lib.lines[int(lib.c[row])]
            if sidm not in repeat_sidms:
                continue
            s, v = pairs[row]
            anchor, library = (s, v) if panel.replicate == "SV" else (v, s)
            g = by_key.get((tissue, sidm, anchor, library))
            if g is None:
                continue
            ys, hs = g["y"].to_numpy(float), g["hit"].to_numpy(bool).astype(float)
            for scheme in SCHEMES:
                order = np.arange(len(g)) if scheme == "chrono" else np.arange(len(g))[::-1]
                for rank, j in enumerate(order[:3], start=1):
                    arrays[scheme][f"y{rank}"][row] = ys[j]
                    arrays[scheme][f"h{rank}"][row] = hs[j]
        out[name] = arrays
    return out


# ----------------------------------------------------------------------------------------------- helpers
def shrunk_mean(pid_hist: np.ndarray, values: np.ndarray, pid_target: np.ndarray, k0: float = K0) -> np.ndarray:
    """(sum + k0 * mu) / (n + k0) per pair over history rows; mu = mean of the (finite) history values."""
    keep = np.isfinite(values)
    pid_hist, values = pid_hist[keep], values[keep]
    size = int(max(pid_hist.max(initial=0), pid_target.max(initial=0))) + 1
    total = np.bincount(pid_hist, weights=values, minlength=size)
    count = np.bincount(pid_hist, minlength=size).astype(float)
    mu = float(values.mean()) if values.size else 0.0
    return ((total + k0 * mu) / (count + k0))[pid_target]


def pooled_conditional(screen_hist: np.ndarray, valid_hist: np.ndarray) -> dict[bool, float]:
    keep = np.isfinite(screen_hist) & np.isfinite(valid_hist)
    s, v = screen_hist[keep] > 0.5, valid_hist[keep] > 0.5
    base = float(v.mean()) if v.size else 0.0
    return {c: (float(v[s == c].mean()) if (s == c).any() else base) for c in (False, True)}


def pair_conditional(pid_hist, screen_hist, valid_hist, pid_target, screen_target, toward: dict[bool, float],
                     k0: float = K0) -> np.ndarray:
    """Pair-specific P(valid call | screen call) over history rows, shrunk toward `toward[call]`."""
    keep = np.isfinite(screen_hist) & np.isfinite(valid_hist)
    pid_hist, s, v = pid_hist[keep], screen_hist[keep] > 0.5, valid_hist[keep] > 0.5
    size = int(max(pid_hist.max(initial=0), pid_target.max(initial=0))) + 1
    st = np.nan_to_num(np.asarray(screen_target, float)) > 0.5
    out = np.empty(st.size)
    for c in (False, True):
        sel = s == c
        hits = np.bincount(pid_hist[sel], weights=v[sel].astype(float), minlength=size)
        count = np.bincount(pid_hist[sel], minlength=size).astype(float)
        rate = (hits + k0 * toward[c]) / (count + k0)
        out[st == c] = rate[pid_target[st == c]]
    return out


def posterior_correction(world: TransferWorld, measured: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Frozen TransferWorld posterior mean minus its prior mean (full mode), for every candidate."""
    if measured.size == 0:
        return np.zeros(world.rows.size)
    mean, _ = world.posterior(measured, values)
    return mean - world.prior_target


def top(scores: np.ndarray, available: np.ndarray, k: int, seed) -> np.ndarray:
    """Frozen agent._top tie-break (random among equal scores, seeded)."""
    return agent._top(np.asarray(scores, float), np.asarray(available, bool), int(k), np.random.default_rng(seed))


# ----------------------------------------------------------------------------------------------- units
_PANELS: dict[str, Panel] = {}
_EVENTS: dict = {}


def _init(panels, events) -> None:
    global _PANELS, _EVENTS
    _PANELS, _EVENTS = panels, events


def unit_table(spec: dict, panels: dict | None = None, events: dict | None = None) -> dict:
    """Per-candidate quantities for one (target, panel, line, excluded lines) world; nothing is fitted here.

    The only target-line labels used are the purchased screen measurements (fed to the posterior); validation
    labels are stored for later scoring only."""
    panels = _PANELS if panels is None else panels
    events = _EVENTS if events is None else events
    t0 = time.perf_counter()
    panel = panels[spec["panel"]]
    lib = panel.library
    line = int(spec["line"])
    excluded = np.asarray(spec.get("exclude", ()), int)
    mask = ~np.isin(lib.c, excluded)
    keep = np.flatnonzero(mask)
    sub = lib.subset(mask, f"{lib.name}_dev") if excluded.size else lib
    world = TransferWorld(sub, line, WORLD)
    rows = world.rows
    orig = keep[rows]
    hist = np.flatnonzero(sub.c != line)
    hist_orig = keep[hist]
    pid = world.pair_id
    S0 = world.prior_target.copy()
    hm = world.X_target[:, 0].copy()
    out = {"spec": spec, "line_name": lib.lines[line], "stratum": panel.stratum, "replicate": panel.replicate,
           "n_rows": int(rows.size), "s_noise": world.s_noise, "s_drug": world.s_drug, "s_line": world.s_line,
           "schemes": {}}
    schemes = SCHEMES if spec["target"] == "i" else ("pooled",)
    for scheme in schemes:
        if spec["target"] == "ii":
            y_s = sub.y[rows].copy()
            s_hit = panel.screen_hit[orig].astype(float)
            v = panel.valid_y[orig].astype(float)
            v_hit = panel.valid_hit[orig].astype(float)
            v3 = np.full(rows.size, np.nan)
            v3_hit = np.full(rows.size, np.nan)
            V0 = shrunk_mean(pid[hist], panel.valid_y[hist_orig].astype(float), pid[rows])
            p_pair = shrunk_mean(pid[hist], panel.valid_hit[hist_orig].astype(float), pid[rows])
            sh, vh = panel.screen_hit[hist_orig].astype(float), panel.valid_hit[hist_orig].astype(float)
            pooled = pooled_conditional(sh, vh)
            p_cond_pair = pair_conditional(pid[hist], sh, vh, pid[rows], s_hit, pooled)
        else:
            ev = events[spec["panel"]][scheme]
            y_s, s_hit = ev["y1"][orig], ev["h1"][orig]
            v, v_hit, v3, v3_hit = ev["y2"][orig], ev["h2"][orig], ev["y3"][orig], ev["h3"][orig]
            V0 = hm.copy()                                     # same orientation: history mean of the pooled label
            p_pair = shrunk_mean(pid[hist], panel.screen_hit[hist_orig].astype(float), pid[rows])
            h1_all, h2_all = [], []                            # other repeat lines of all tissues, same replicate
            for name, p in panels.items():
                if p.replicate != panel.replicate:
                    continue
                e = events[name][scheme]
                ok = np.ones(len(p.library), bool)
                if name == spec["panel"]:
                    ok = ~np.isin(p.library.c, np.r_[excluded, line])
                sel = ok & np.isfinite(e["h1"]) & np.isfinite(e["h2"])
                h1_all.append(e["h1"][sel])
                h2_all.append(e["h2"][sel])
            pooled = pooled_conditional(np.concatenate(h1_all), np.concatenate(h2_all))
            e = events[spec["panel"]][scheme]                  # pair-specific: same-tissue repeat history lines
            p_cond_pair = pair_conditional(pid[hist], e["h1"][hist_orig], e["h2"][hist_orig], pid[rows], s_hit, pooled)
        p_cond = np.where(np.nan_to_num(s_hit) > 0.5, pooled[True], pooled[False])
        eligible = np.isfinite(y_s) & np.isfinite(v)
        n_el = int(eligible.sum())
        rec: dict = {"n_eligible": n_el}
        if n_el < MIN_ELIGIBLE:
            rec["skipped"] = f"fewer than {MIN_ELIGIBLE} eligible candidates"
            out["schemes"][scheme] = rec
            continue
        k = int(math.ceil(PURCHASE * n_el))
        k1 = int(math.ceil(ROUND1 * n_el))
        bought = np.zeros(rows.size, bool)
        bought[top(hm, eligible, k, line)] = True
        r1 = np.zeros(rows.size, bool)
        r1[top(hm, eligible, k1, line)] = True
        y_fill = np.where(np.isfinite(y_s), y_s, 0.0)
        F_U = posterior_correction(world, np.flatnonzero(bought), y_fill[bought])
        F_U10 = posterior_correction(world, np.flatnonzero(r1), y_fill[r1])
        random_sets = []
        for seed in RANDOM_SEEDS:
            rb = np.zeros(rows.size, bool)
            rb[np.random.default_rng([seed, line, 7]).choice(np.flatnonzero(eligible), k, replace=False)] = True
            random_sets.append({"bought": rb, "F_U": posterior_correction(world, np.flatnonzero(rb), y_fill[rb])})
        rec.update({"eligible": eligible, "S0": S0, "hm": hm, "V0": V0, "y_s": y_s, "s_hit": s_hit, "v": v,
                    "v_hit": v_hit, "v3": v3, "v3_hit": v3_hit, "p_pair": p_pair, "p_cond": p_cond,
                    "p_cond_pair": p_cond_pair, "p_cond_pooled": pooled, "bought": bought, "r1": r1, "F_U": F_U,
                    "F_U10": F_U10, "F_P": y_fill - S0, "random": random_sets, "pair_id": pid[rows], "seed": line})
        out["schemes"][scheme] = rec
    out["seconds"] = round(time.perf_counter() - t0, 3)
    return out


def _task(spec: dict) -> dict:
    return unit_table(spec)


# ----------------------------------------------------------------------------------------------- views
def view(rec: dict, purchase: str, seed_index: int | None = None) -> dict:
    """Candidate sets and corrections for one purchase scheme ('primary' or a random seed)."""
    eligible = rec["eligible"]
    if purchase == "primary":
        bought, F_U = rec["bought"], rec["F_U"]
    else:
        r = rec["random"][seed_index]
        bought, F_U = r["bought"], r["F_U"]
    return {"U": eligible & ~bought, "P": eligible & bought, "F_U": F_U, "F_P": rec["F_P"], "bought": bought}


def fit_parts(rec: dict, estimand: str, purchase: str, seed_index: int | None, target_key: str = "v",
              correction: str | None = None) -> tuple[float, float, int]:
    """Line-unit pieces a = mean F * (v - V0), b = mean F^2 over the estimand's candidates."""
    vw = view(rec, purchase, seed_index)
    if correction == "F_U10":
        cand, F = rec["eligible"] & ~rec["r1"], rec["F_U10"]
    else:
        cand, F = vw[estimand], vw["F_U" if estimand == "U" else "F_P"]
    y = rec[target_key]
    cand = cand & np.isfinite(y)
    if not cand.any():
        return np.nan, np.nan, 0
    resid = y[cand] - rec["V0"][cand]
    return float(np.mean(F[cand] * resid)), float(np.mean(F[cand] ** 2)), int(cand.sum())


def fit_lambda(units: list[dict], estimand: str, purchase: str, seed_index: int | None, scheme: str,
               correction: str | None = None, boot: int = BOOT) -> dict:
    """Least-squares lambda over development lines (each line weighted equally); line bootstrap by tissue."""
    per_line: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for u in units:
        rec = u["schemes"].get(scheme, {})
        if "eligible" not in rec:
            continue
        a, b, n = fit_parts(rec, estimand, purchase, seed_index, correction=correction)
        if n:
            per_line.setdefault((u["stratum"], u["line_name"]), []).append((a, b))
    keys = sorted(per_line)
    A = np.array([np.mean([x[0] for x in per_line[k]]) for k in keys])
    B = np.array([np.mean([x[1] for x in per_line[k]]) for k in keys])
    strata = np.array([k[0] for k in keys])
    lam = float(A.sum() / B.sum()) if B.sum() > 0 else 0.0
    rng = np.random.default_rng(FOLD_SEED)
    draws = np.empty(boot)
    for i in range(boot):
        idx = np.concatenate([rng.choice(np.flatnonzero(strata == s), (strata == s).sum(), replace=True)
                              for s in np.unique(strata)])
        draws[i] = A[idx].sum() / B[idx].sum() if B[idx].sum() > 0 else 0.0
    lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
    near = bool(abs(lam) < LAMBDA_TOL or (lo <= 0.0 <= hi))
    return {"lambda": lam, "ci": [lo, hi], "dev_lines": len(keys), "near_zero": near}


def predictions(rec: dict, estimand: str, lam: float, purchase: str = "primary", seed_index: int | None = None) -> dict:
    vw = view(rec, purchase, seed_index)
    V0, S0 = rec["V0"], rec["S0"]
    if estimand == "U":
        F = vw["F_U"]
        return {"U_V0": V0, "U_lambda": V0 + lam * F, "U_lambda1": V0 + F, "U_screen_post": S0 + F,
                "U_screen_static": S0, "p_pair": rec["p_pair"]}
    F = vw["F_P"]
    return {"P_V0": V0, "P_lambda": V0 + lam * F, "P_lambda1": V0 + F, "P_screen": rec["y_s"],
            "p_pair": rec["p_pair"], "p_cond": rec["p_cond"], "p_cond_pair": rec["p_cond_pair"],
            "hits_then_screen": 1000.0 * np.nan_to_num(rec["s_hit"]) + np.nan_to_num(rec["y_s"]) / 1000.0}


# ----------------------------------------------------------------------------------------------- metrics
def concordance(pred: np.ndarray, y: np.ndarray) -> float:
    n = y.size
    if n < 2:
        return np.nan
    iu = np.triu_indices(n, 1)
    dy = np.sign(y[:, None] - y[None, :])[iu]
    dp = np.sign(pred[:, None] - pred[None, :])[iu]
    m = dy != 0
    if not m.any():
        return np.nan
    return float(((dp[m] == dy[m]).sum() + 0.5 * (dp[m] == 0).sum()) / m.sum())


def pearson(pred: np.ndarray, y: np.ndarray) -> float:
    if pred.size < 3 or np.std(pred) == 0 or np.std(y) == 0:
        return np.nan
    return float(np.corrcoef(pred, y)[0, 1])


def logloss(p: np.ndarray, hit: np.ndarray) -> float:
    p = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(hit * np.log(p) + (1 - hit) * np.log(1 - p)))


class Mapping:
    """2-parameter logistic map from a continuous prediction to P(validation call), fitted on development."""

    def __init__(self, x: np.ndarray, hit: np.ndarray):
        from sklearn.linear_model import LogisticRegression

        self.constant = None
        if np.unique(hit).size < 2 or np.std(x) == 0:
            self.constant = float(np.clip(hit.mean() if hit.size else 0.5, EPS, 1 - EPS))
            return
        self.model = LogisticRegression(C=1e6, max_iter=1000).fit(x.reshape(-1, 1), hit.astype(int))

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if self.constant is not None:
            return np.full(x.size, self.constant)
        return self.model.predict_proba(x.reshape(-1, 1))[:, 1]


def unit_metrics(rec: dict, estimand: str, lam: float, maps: dict, purchase: str = "primary",
                 seed_index: int | None = None, target_key: str = "v") -> dict:
    """Per-unit metrics of every arm on the estimand's candidates with a finite target."""
    vw = view(rec, purchase, seed_index)
    y, hit = rec[target_key], rec[target_key + "_hit"]
    cand = vw[estimand] & np.isfinite(y)
    preds = predictions(rec, estimand, lam, purchase, seed_index)
    out: dict = {"n": int(cand.sum())}
    if cand.sum() < 3:
        return out
    yc, hc = y[cand], hit[cand]
    n_el = int(rec["eligible"].sum())
    for arm, score in preds.items():
        s = score[cand]
        m: dict = {"concordance": concordance(s, yc), "pearson": pearson(s, yc)}
        if arm.startswith(("U_", "P_")) and arm != "hits_then_screen":
            m["mse"] = float(np.mean((s - yc) ** 2))
            p = maps[arm](s) if arm in maps else None
        else:
            p = s if arm.startswith("p_") else None
        if p is not None:
            m["logloss"] = logloss(p, hc)
            m["brier"] = float(np.mean((p - hc) ** 2))
        if estimand == "U":
            k = int(math.ceil(TOPK * n_el))
            picks = top(score, cand, min(k, int(cand.sum())), rec["seed"])
            m["topk_valid_rate"] = float(np.mean(hit[picks]))
        else:
            mm = int(math.ceil(VERIFY * int(vw["bought"].sum())))
            picks = top(score, cand, min(mm, int(cand.sum())), rec["seed"])
            m["verified_confirmed"] = float(np.sum((np.nan_to_num(rec["s_hit"][picks]) > 0.5) & (hit[picks] > 0.5)))
        out[arm] = m
    return out


def yield_metrics(rec: dict, lam10: float, target_key: str = "v") -> dict:
    """Round 1 = top 10% by history mean (shared); round 2 = next 10% by each arm from round-1 labels."""
    eligible, r1 = rec["eligible"], rec["r1"]
    k2 = int(math.ceil(ROUND1 * int(eligible.sum())))
    avail = eligible & ~r1
    F = rec["F_U10"]
    scores = {"history_mean": rec["hm"], "U_V0": rec["V0"], "U_lambda": rec["V0"] + lam10 * F,
              "U_screen_post": rec["S0"] + F}
    hit = rec[target_key + "_hit"]
    out = {}
    for arm, s in scores.items():
        picks = top(s, avail, min(k2, int(avail.sum())), rec["seed"])
        ok = np.isfinite(hit[picks])
        out[arm] = {"validated_round2": float(np.sum((np.nan_to_num(rec["s_hit"][picks]) > 0.5) & (hit[picks] > 0.5))),
                    "valid_calls_round2": float(np.nansum(hit[picks])), "scored": int(ok.sum())}
    return out


# ----------------------------------------------------------------------------------------------- folds
def folds_ii(panels: dict[str, Panel]) -> dict[str, int]:
    """line SIDM -> fold, 5 folds per tissue (seeded permutation of the sorted lines)."""
    fold = {}
    for tissue, code in jaaks.TISSUE_CODE.items():
        names = sorted({sidm for p in panels.values() if p.stratum == tissue for sidm in p.library.lines})
        order = np.random.default_rng([FOLD_SEED, code]).permutation(len(names))
        for rank, i in enumerate(order):
            fold[names[i]] = rank % N_FOLDS
    return fold


def specs_for(panels: dict[str, Panel], repeat_sidms: set[str]) -> tuple[list[dict], dict]:
    """All unique world specs, and the fold maps: target -> fold -> {'dev': [keys], 'eval': [keys]}."""
    unique: dict[tuple, dict] = {}

    def add(target, name, line, exclude) -> tuple:
        key = (target, name, int(line), tuple(sorted(int(x) for x in exclude)))
        unique.setdefault(key, {"target": target, "panel": name, "line": int(line), "exclude": list(key[3])})
        return key

    fold = folds_ii(panels)
    plan: dict = {"ii": {}, "i": {}}
    for k in range(N_FOLDS):
        entry = {"dev": [], "eval": []}
        for name, p in panels.items():
            out_idx = [i for i, sidm in enumerate(p.library.lines) if fold[sidm] == k]
            for i, sidm in enumerate(p.library.lines):
                if fold[sidm] == k:
                    entry["eval"].append(add("ii", name, i, ()))
                else:
                    entry["dev"].append(add("ii", name, i, out_idx))
        plan["ii"][k] = entry
    repeat = [(name, i, sidm) for name, p in panels.items() for i, sidm in enumerate(p.library.lines)
              if sidm in repeat_sidms]
    for sidm in sorted(repeat_sidms):
        entry = {"dev": [], "eval": []}
        for name, i, other in repeat:
            if other == sidm:
                entry["eval"].append(add("i", name, i, ()))
        for name, i, other in repeat:
            if other == sidm:
                continue
            p = panels[name]
            same = [j for j, s in enumerate(p.library.lines) if s == sidm]
            entry["dev"].append(add("i", name, i, same))
        plan["i"][sidm] = entry
    return list(unique.values()), {"plan": plan, "fold_ii": fold, "keys": {k: v for k, v in unique.items()}}


def key_of(spec: dict) -> tuple:
    return (spec["target"], spec["panel"], int(spec["line"]), tuple(sorted(int(x) for x in spec["exclude"])))


# ----------------------------------------------------------------------------------------------- analysis
def _line_mean(records: list[tuple[tuple[str, str], float]]) -> dict[tuple[str, str], float]:
    acc: dict = {}
    for key, value in records:
        if value is not None and np.isfinite(value):
            acc.setdefault(key, []).append(value)
    return {k: float(np.mean(v)) for k, v in acc.items()}


def analyse_cell(units: dict, fold_plan: dict, target: str, scheme: str, purchase: str,
                 target_key: str = "v") -> dict:
    """lambda per fold (U, P, U10), dev-selected strongest baselines, per-line evaluation metrics."""
    seeds = list(range(len(RANDOM_SEEDS))) if purchase == "random" else [None]
    folds_out, per_unit = {}, []
    for fold, entry in fold_plan.items():
        dev = [units[k] for k in entry["dev"]]
        ev = [units[k] for k in entry["eval"]]
        fold_rec: dict = {}
        for si in seeds:
            tag = "primary" if si is None else f"seed{si}"
            lam = {e: fit_lambda(dev, e, purchase if si is not None else "primary", si, scheme) for e in ("U", "P")}
            if si is None:
                lam["U10"] = fit_lambda(dev, "U", "primary", None, scheme, correction="F_U10")
            maps, strongest = {}, {}
            for e, conts, base, probs in (("U", U_CONT, U_BASELINES, U_PROB), ("P", P_CONT, P_BASELINES, P_PROB)):
                xs = {a: [] for a in conts + probs}
                hs, ys = [], []
                dev_mse = {a: [] for a in conts}
                dev_ll = {a: [] for a in probs}
                for u in dev:
                    rec = u["schemes"].get(scheme, {})
                    if "eligible" not in rec:
                        continue
                    vw = view(rec, "primary" if si is None else purchase, si)
                    cand = vw[e] & np.isfinite(rec["v"])
                    if not cand.any():
                        continue
                    pr = predictions(rec, e, lam[e]["lambda"], "primary" if si is None else purchase, si)
                    for a in conts:
                        xs[a].append(pr[a][cand])
                        dev_mse[a].append(((u["stratum"], u["line_name"]), float(np.mean((pr[a][cand] - rec["v"][cand]) ** 2))))
                    for a in probs:
                        xs[a].append(pr[a][cand])
                        dev_ll[a].append(((u["stratum"], u["line_name"]), logloss(pr[a][cand], rec["v_hit"][cand])))
                    hs.append(rec["v_hit"][cand])
                hit = np.concatenate(hs) if hs else np.zeros(0)
                for a in conts:
                    maps[(e, a)] = Mapping(np.concatenate(xs[a]) if xs[a] else np.zeros(0), hit)
                mse_line = {a: _line_mean(dev_mse[a]) for a in conts}
                mean_mse = {a: float(np.mean(list(mse_line[a].values()))) for a in conts}
                strongest[e] = min(base, key=lambda a: mean_mse[a])
                # calls: probability arms and mapped continuous baselines, by development log loss
                ll = {a: float(np.mean(list(_line_mean(dev_ll[a]).values()))) for a in probs}
                for a in base:
                    vals = []
                    for u in dev:
                        rec = u["schemes"].get(scheme, {})
                        if "eligible" not in rec:
                            continue
                        vw = view(rec, "primary" if si is None else purchase, si)
                        cand = vw[e] & np.isfinite(rec["v"])
                        if cand.any():
                            pr = predictions(rec, e, lam[e]["lambda"], "primary" if si is None else purchase, si)
                            vals.append(((u["stratum"], u["line_name"]), logloss(maps[(e, a)](pr[a][cand]), rec["v_hit"][cand])))
                    ll[a] = float(np.mean(list(_line_mean(vals).values())))
                strongest[e + "_calls"] = min(ll, key=ll.get)
                fold_rec.setdefault(tag, {})[e] = {"lambda": lam[e], "dev_mse": mean_mse, "strongest": strongest[e],
                                                   "dev_logloss": ll, "strongest_calls": strongest[e + "_calls"]}
            if si is None:
                fold_rec[tag]["U10"] = {"lambda": lam["U10"]}
            for u in ev:
                rec = u["schemes"].get(scheme, {})
                if "eligible" not in rec:
                    continue
                if target_key == "v3" and not np.isfinite(rec["v3"]).any():
                    continue
                row = {"fold": str(fold), "seed": tag, "stratum": u["stratum"], "line": u["line_name"],
                       "replicate": u["replicate"]}
                for e in ("U", "P"):
                    mp = {a: maps[(e, a)] for a in (U_CONT if e == "U" else P_CONT)}
                    row[e] = unit_metrics(rec, e, lam[e]["lambda"], mp, "primary" if si is None else purchase, si,
                                          target_key)
                    row[e]["strongest"] = fold_rec[tag][e]["strongest"]
                    row[e]["strongest_calls"] = fold_rec[tag][e]["strongest_calls"]
                if si is None:
                    row["yield"] = yield_metrics(rec, lam["U10"]["lambda"], target_key)
                per_unit.append(row)
        folds_out[str(fold)] = fold_rec
    return {"folds": folds_out, "units": per_unit}


def line_table(per_unit: list[dict], estimand: str, arm: str, metric: str) -> dict[tuple[str, str], float]:
    vals = []
    for r in per_unit:
        m = r[estimand].get(arm, {}) if estimand in ("U", "P") else r.get("yield", {}).get(arm, {})
        if arm == "STRONGEST":
            m = r[estimand].get(r[estimand]["strongest"], {})
        if arm == "STRONGEST_CALLS":
            m = r[estimand].get(r[estimand]["strongest_calls"], {})
        vals.append(((r["stratum"], r["line"]), m.get(metric)))
    return _line_mean(vals)


def contrasts(per_unit: list[dict], estimand: str, model: str, comparators: list[str], metrics: list[str]) -> dict:
    from research.astra.feedback_validation_20261003.verdict import contrast

    out = {}
    for metric in metrics:
        x = line_table(per_unit, estimand, model, metric)
        res = {}
        for comp in comparators:
            y = line_table(per_unit, estimand, comp, metric)
            keys = sorted(set(x) & set(y))
            if len(keys) < 3:
                continue
            xs = np.array([x[k] for k in keys])
            ys = np.array([y[k] for k in keys])
            strata = np.array([k[0] for k in keys])
            c = contrast(xs, ys, strata)
            res[comp] = {"model_mean": float(xs.mean()), "comparator_mean": float(ys.mean()),
                         "mean_diff": c["mean_diff"], "mean_diff_ci": c["mean_diff_ci"], "lines": c["lines"],
                         "better": c["better"], "worse": c["worse"]}
        out[metric] = res
    return out


def arm_means(per_unit: list[dict], estimand: str, arms: tuple[str, ...], metrics: tuple[str, ...]) -> dict:
    out = {}
    for arm in arms:
        out[arm] = {}
        for metric in metrics:
            t = line_table(per_unit, estimand, arm, metric)
            if t:
                out[arm][metric] = {"mean_over_lines": float(np.mean(list(t.values()))), "lines": len(t)}
    return out


def calibration(units: dict, fold_plan: dict, cell: dict, target: str, scheme: str, target_key: str = "v") -> dict:
    """Pooled evaluation calibration (primary purchase): OLS intercept/slope for continuous arms; ECE for probs."""
    out = {}
    for e, conts, probs in (("U", U_CONT, U_PROB), ("P", P_CONT, P_PROB)):
        xs = {a: [] for a in conts + probs}
        ys, hs = [], []
        for fold, entry in fold_plan.items():
            lam = cell["folds"][str(fold)]["primary"][e]["lambda"]["lambda"]
            for k in entry["eval"]:
                rec = units[k]["schemes"].get(scheme, {})
                if "eligible" not in rec:
                    continue
                vw = view(rec, "primary")
                cand = vw[e] & np.isfinite(rec[target_key])
                pr = predictions(rec, e, lam)
                for a in conts + probs:
                    xs[a].append(pr[a][cand])
                ys.append(rec[target_key][cand])
                hs.append(rec[target_key + "_hit"][cand])
        if not ys:
            continue
        y, h = np.concatenate(ys), np.concatenate(hs)
        res = {}
        for a in conts:
            x = np.concatenate(xs[a])
            slope = float(np.polyfit(x, y, 1)[0]) if np.std(x) > 0 else np.nan
            res[a] = {"calibration_slope": slope, "calibration_intercept": float(np.mean(y) - slope * np.mean(x))
                      if np.isfinite(slope) else np.nan, "mean_pred_minus_obs": float(np.mean(x) - np.mean(y))}
        for a in probs:
            p = np.concatenate(xs[a])
            bins = np.clip((p * 10).astype(int), 0, 9)
            ece = sum(abs(p[bins == b].mean() - h[bins == b].mean()) * (bins == b).mean() for b in range(10)
                      if (bins == b).any())
            res[a] = {"ece_10bins": float(ece), "mean_pred_minus_obs": float(p.mean() - h.mean())}
        out[e] = {"candidates": int(y.size), "arms": res}
    return out


def stop_decision(cell: dict, estimand: str) -> dict:
    lams = [f["primary"][estimand]["lambda"] for f in cell["folds"].values()]
    near = sum(1 for l in lams if l["near_zero"])
    model = "U_lambda" if estimand == "U" else "P_lambda"
    c = contrasts(cell["units"], estimand, model, ["STRONGEST"], ["mse"])["mse"].get("STRONGEST")
    beats = bool(c is not None and c["mean_diff_ci"][1] < 0)
    fires = bool(near >= len(lams) / 2 or not beats)
    return {"folds": len(lams), "folds_lambda_near_zero": near, "lambda_values": [l["lambda"] for l in lams],
            "beats_strongest_simple_baseline_mse": beats, "contrast_vs_strongest_mse": c, "stop_rule_fires": fires}


# ----------------------------------------------------------------------------------------------- main
def _environment() -> dict:
    import scipy
    import sklearn

    return {"python": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
            "pandas": pd.__version__}


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    return obj


def analyse_all(units: dict, meta: dict) -> tuple[dict, list[dict]]:
    """Every pre-specified cell of plan.json: primary and sensitivity analyses."""
    cells_out: dict = {}
    cells = [("ii", "pooled", "primary", "v"), ("ii", "pooled", "random", "v"),
             ("i", "chrono", "primary", "v"), ("i", "chrono", "primary", "v3"), ("i", "chrono", "random", "v"),
             ("i", "reverse", "primary", "v"), ("i", "reverse", "primary", "v3")]
    all_units = []
    for target, scheme, purchase, tk in cells:
        name = f"{target}|{scheme}|{purchase}|{'R3' if tk == 'v3' else ('R2' if target == 'i' else 'swap')}"
        cell = analyse_cell(units, meta["plan"][target], target, scheme, purchase, tk)
        res = {"folds": cell["folds"],
               "U": {"means": arm_means(cell["units"], "U", U_CONT + U_PROB + ("STRONGEST", "STRONGEST_CALLS"),
                                        ("mse", "pearson", "concordance", "logloss", "brier", "topk_valid_rate")),
                     "contrasts": contrasts(cell["units"], "U", "U_lambda",
                                            list(U_BASELINES) + ["STRONGEST"],
                                            ["mse", "pearson", "concordance", "logloss", "brier", "topk_valid_rate"]),
                     "contrasts_calls_vs_prob": contrasts(cell["units"], "U", "U_lambda", ["p_pair", "STRONGEST_CALLS"],
                                                          ["logloss", "brier", "concordance", "topk_valid_rate"])},
               "P": {"means": arm_means(cell["units"], "P", P_CONT + P_PROB + ("hits_then_screen", "STRONGEST",
                                                                               "STRONGEST_CALLS"),
                                        ("mse", "pearson", "concordance", "logloss", "brier", "verified_confirmed")),
                     "contrasts": contrasts(cell["units"], "P", "P_lambda", list(P_BASELINES) + ["STRONGEST"],
                                            ["mse", "pearson", "concordance", "logloss", "brier", "verified_confirmed"]),
                     "contrasts_calls_vs_prob": contrasts(cell["units"], "P", "P_lambda",
                                                          ["p_pair", "p_cond", "p_cond_pair", "hits_then_screen",
                                                           "STRONGEST_CALLS"],
                                                          ["logloss", "brier", "concordance", "verified_confirmed"])}}
        if purchase == "primary":
            res["yield"] = {"means": {a: {m: float(np.mean(list(line_table(cell["units"], "yield", a, m).values())))
                                          for m in ("validated_round2", "valid_calls_round2")} for a in YIELD_ARMS},
                            "contrasts": {m: contrasts_yield(cell["units"], m) for m in
                                          ("validated_round2", "valid_calls_round2")}}
            res["calibration"] = calibration(units, meta["plan"][target], cell, target, scheme, tk)
            res["stop_rule"] = {e: stop_decision(cell, e) for e in ("U", "P")}
        cells_out[name] = res
        for r in cell["units"]:
            all_units.append(dict(r, cell=name))
    return cells_out, all_units


def run(workers: int, out: Path) -> dict:
    from ..common import exposed_ticket
    from .provenance import load_plate_hierarchy

    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    ticket = exposed_ticket("Phase 2 scalar feedback correction (plan.json): registered panels + event-level labels "
                            "of the 14 repeat lines", "repeats")
    panels, report, candidates = jaaks.build_panels(ticket)
    plates = load_plate_hierarchy()
    repeat_sidms = set(plates.loc[plates["line"].isin(REPEAT_LINES), "SIDM"].unique())
    if len(repeat_sidms) != 14:
        raise ValueError("REPEAT_LINES: expected 14 SIDMs")
    events_df = event_table(ticket, plates)
    events = event_arrays(panels, candidates, events_df, repeat_sidms)
    t_build = time.perf_counter() - t0
    specs, meta = specs_for(panels, repeat_sidms)
    t1 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(panels, events)) as pool:
        results = list(pool.map(_task, specs, chunksize=4))
    units = {key_of(r["spec"]): r for r in results}
    t_units = time.perf_counter() - t1
    t2 = time.perf_counter()
    summary: dict = {"label": "EXPLORATORY (exposed data); plan: repeats/plan.json", "started": started,
                     "ticket": ticket}
    summary["cells"], all_units = analyse_all(units, meta)
    t_analysis = time.perf_counter() - t2
    summary["timing_seconds"] = {"build_panels_and_events": round(t_build, 1), "worlds": round(t_units, 1),
                                 "analysis": round(t_analysis, 1), "total": round(time.perf_counter() - t0, 1),
                                 "unique_worlds": len(specs), "workers": workers,
                                 "sum_world_seconds": round(sum(r["seconds"] for r in results), 1)}
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    summary["build_report"] = report
    summary["skipped_units"] = [{"spec": r["spec"], "scheme": s, "reason": v["skipped"]} for r in results
                                for s, v in r["schemes"].items() if "skipped" in v]
    summary["eligible_counts_eval_i"] = {f"{r['line_name']}|{r['replicate']}|{s}": v["n_eligible"]
                                         for r in results if r["spec"]["target"] == "i" and not r["spec"]["exclude"]
                                         for s, v in r["schemes"].items()}
    summary["fold_ii"] = meta["fold_ii"]
    summary["environment"] = _environment()
    out.mkdir(parents=True, exist_ok=False)
    (out / "summary.json").write_text(json.dumps(_jsonable(summary), indent=1), encoding="utf-8")
    with open(out / "unit_metrics.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for r in all_units:
            handle.write(json.dumps(_jsonable(r)) + "\n")
    return summary


def contrasts_yield(per_unit: list[dict], metric: str) -> dict:
    from research.astra.feedback_validation_20261003.verdict import contrast

    x = line_table(per_unit, "yield", "U_lambda", metric)
    out = {}
    for comp in ("history_mean", "U_V0", "U_screen_post"):
        y = line_table(per_unit, "yield", comp, metric)
        keys = sorted(set(x) & set(y))
        xs, ys = np.array([x[k] for k in keys]), np.array([y[k] for k in keys])
        c = contrast(xs, ys, np.array([k[0] for k in keys]))
        out[comp] = {"model_sum": float(xs.sum()), "comparator_sum": float(ys.sum()), "mean_diff": c["mean_diff"],
                     "mean_diff_ci": c["mean_diff_ci"], "relative_gain": c["relative_gain"],
                     "relative_gain_ci": c["relative_gain_ci"], "lines": c["lines"]}
    return out


def key_results(run_dir: Path) -> dict:
    """Compact receipt of the pre-specified primary cells (and sensitivities) from a finished run's summary.json."""
    s = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    out = {"label": "EXPLORATORY (exposed data); extracted from " + run_dir.name + "/summary.json",
           "source_sha256": jaaks.sha256(run_dir / "summary.json"), "cells": {}}
    for name, c in s["cells"].items():
        cell: dict = {"lambda": {}}
        for e in ("U", "P", "U10"):
            vals = [(f, tag, t[e]["lambda"]) for f, fr in c["folds"].items() for tag, t in fr.items() if e in t]
            if vals:
                lam = [v[2]["lambda"] for v in vals]
                cell["lambda"][e] = {"per_fold": {f"{f}|{tag}": v for f, tag, v in vals}, "min": min(lam),
                                     "median": float(np.median(lam)), "max": max(lam),
                                     "folds_near_zero": sum(v[2]["near_zero"] for v in vals)}
        for e in ("U", "P"):
            cell[e] = {"means": c[e]["means"], "contrasts": c[e]["contrasts"],
                       "contrasts_calls_vs_prob": c[e]["contrasts_calls_vs_prob"]}
        for k in ("stop_rule", "yield", "calibration"):
            if k in c:
                cell[k] = c[k]
        out["cells"][name] = cell
    out["timing_seconds"] = s["timing_seconds"]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--out", type=str, default="")
    parser.add_argument("--key-results", type=str, default="", help="finished run directory: write receipts/phase2_key_results.json")
    args = parser.parse_args(argv)
    if args.key_results:
        target = HERE / "receipts" / "phase2_key_results.json"
        if target.exists():
            raise FileExistsError("NO_OVERWRITE: phase2_key_results.json")
        target.write_text(json.dumps(_jsonable(key_results(Path(args.key_results))), indent=1), encoding="utf-8")
        print("written:", target)
        return 0
    out = Path(args.out) if args.out else RESULTS / f"phase2_{time.strftime('%Y%m%d_%H%M%S')}"
    summary = run(args.workers, out)
    brief = {name: {"stop_rule": c.get("stop_rule"), "lambda": {f: {e: c["folds"][f]["primary"][e]["lambda"]["lambda"]
                                                                    for e in ("U", "P")} for f in c["folds"]
                                                                if "primary" in c["folds"][f]}}
             for name, c in summary["cells"].items()}
    print(json.dumps(_jsonable(brief), indent=1)[:6000])
    print(json.dumps(summary["timing_seconds"]))
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
