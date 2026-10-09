"""Dual-core run v8: LMM marginal LLR + conformal risk-control certification.

File summary
- Path: research/viability_contrast/run8.py
- Purpose: protocol viability-contrast-8. Statistic: joint marginal LLR under a
  compound-level random effect (a = m_c + b + e, b ~ N(0, tau_c^2), rank-1 O(1)
  updates; tau_c^2 by robust median-of-covariance MoM on training residuals).
  Stopping: (S_eprocess) fixed a-priori threshold log(20); (S_crc) threshold
  lambda selected per arm on calibration episodes by conformal risk control
  (loss = decided-and-wrong, monotone in lambda, B = 1; coverage-maximising among
  safe lambdas); S_ltt reported alongside. Acquisition: ginfo (information-gain
  order), world (world5b-guided), random, oracle ceiling; shuffled control.
  Pilot phase: fold 0 only (PILOT=True); global: all folds.
- Interfaces / data: reads the frozen pack; writes
  outputs/viability_contrast_20261008/run8{,_pilot}/{episodes.csv, summary.json,
  gate.json, world_fit.json}.
- Depends on: research/viability_contrast/{protocol8.json, prepare.py, qualify.py,
  qualify2.py, world5b.py, run6.py, run7.py}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify2, run6, run7, world5b

ROOT = Path(__file__).resolve().parents[2]
KEY = "viability-contrast-8"
BUDGET = 16
ALPHA = 0.05
ETHRESH = float(np.log(1.0 / ALPHA))
Z_CLIP = 3.0
DRAWS = 10_000
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)
LAMBDA_GRID = np.exp(np.linspace(np.log(0.5), np.log(12.0), 21))
TAU_FLOOR = 0.0


def sha(text: str) -> str:
    return qualify2.sha(text)


# ------------------------------------------------------------------ tau2 (MoM)
def estimate_tau2(auc, train_pos, labels, med, scale, valid, med_p, scale_p,
                  pool_arr, n_classes):
    """Per-class compound random-effect variance by robust median-of-covariance.

    M = mean_i r_i r_i' - diag(s_c^2) over pool lines (raw units, winsorized
    residuals at |z| <= 3 in z-space, mapped back by s_c); tau_c^2 =
    max(0, median of the off-diagonal of M). Class-pooled fallback for thin
    classes; also returns the pooled tau2 for the information flag.
    """
    m = np.where(valid, med, med_p[None, :])
    s = np.where(valid, scale, scale_p[None, :])
    block = auc[train_pos][:, pool_arr]
    lab = labels[train_pos]
    z = (block - m[lab][:, :]) / s[lab][:, :]
    z = np.clip(z, -Z_CLIP, Z_CLIP)
    n_lines = len(pool_arr)
    tau2 = np.zeros(n_classes)
    iu = np.triu_indices(n_lines, k=1)
    pooled_off = []
    for ci in range(n_classes):
        rows = np.where(lab == ci)[0]
        if len(rows) < 6:
            continue
        R = z[rows] * s[ci][None, :]                    # raw residuals (n_i, L)
        S = np.zeros((n_lines, n_lines))
        C = np.zeros((n_lines, n_lines))
        for i in range(len(rows)):
            ri = R[i]
            ok = np.isfinite(ri)
            rr = np.where(ok, ri, 0.0)
            S += np.outer(rr, rr)
            C += np.outer(ok.astype(float), ok.astype(float))
        with np.errstate(invalid="ignore", divide="ignore"):
            M = S / np.maximum(C, 1.0) - np.diag(s[ci] ** 2)
        good = C[iu] >= 6
        if good.sum() == 0:
            continue
        off = M[iu][good]
        off = off[np.isfinite(off)]
        if len(off) == 0:
            continue
        tau2[ci] = max(float(np.median(off)), TAU_FLOOR)
        pooled_off.append(off)
    pooled_tau2 = float(np.median(np.concatenate(pooled_off))) if pooled_off else 0.0
    pooled_tau2 = max(pooled_tau2, TAU_FLOOR)
    return tau2, pooled_tau2


# ------------------------------------------------------------------ LMM LLR
def lmm_neg2logf(a, m, s, tau2):
    """-2 log marginal density under N(m, diag(s^2) + tau2 * 11'), z winsorized."""
    ok = np.isfinite(a)
    if ok.sum() == 0:
        return 0.0, 0
    aj, mj, sj = a[ok], m[ok], s[ok]
    r = np.clip((aj - mj) / sj, -Z_CLIP, Z_CLIP)
    U = float(np.sum(1.0 / sj ** 2))
    W = float(np.sum(r / sj))
    Q = float(np.sum(r * r))
    t = len(aj)
    val = (t * np.log(2.0 * np.pi) + np.sum(2.0 * np.log(sj))
           + np.log1p(tau2 * U) + Q - tau2 * W * W / (1.0 + tau2 * U))
    return float(val), t


# ------------------------------------------------------------------ episode
def run_episode_v8(readings, pair, tau2_pair, acq, order, world=None):
    """One two-class episode. Returns (llr_traj, increments, measurements, qc).

    llr_traj: list of (llr, measurements); increments: realised per-reading
    Huber increments (for the oracle analysis); acquisition by ginfo order,
    random order, world-guided, or oracle (acq == 'oracle_reading').
    """
    (m1, s1), (m2, s2), _ = pair
    t1, t2 = tau2_pair
    bought = np.zeros(len(readings), dtype=bool)
    purchased_pos = []
    measurements = 0
    qc = 0
    traj = []
    order_pos = 0
    while measurements < BUDGET:
        llr_now = traj[-1][0] if traj else 0.0
        belief = 1.0 / (1.0 + np.exp(-llr_now)) if abs(llr_now) < 700 else (
            1.0 if llr_now > 0 else 0.0)
        belief = min(max(belief, 1e-6), 1.0 - 1e-6)
        if world is not None:
            if purchased_pos:
                pos = np.array(purchased_pos)
                world.update(readings[pos], pos)
            wm, ws = world.mean_scale()
            pm1, ps1 = wm[pair[2][0]], ws[pair[2][0]]
            pm2, ps2 = wm[pair[2][1]], ws[pair[2][1]]
        else:
            pm1, ps1, pm2, ps2 = m1, s1, m2, s2

        cand = np.where(~bought)[0]
        if len(cand) == 0:
            break
        if acq in ("ginfo", "random"):
            j = -1
            while order_pos < len(order):
                c = order[order_pos]
                order_pos += 1
                if not bought[c]:
                    j = c
                    break
            if j < 0:
                break
        elif acq == "world":
            def inc_fn(a, jj, _p=(pm1, ps1, pm2, ps2)):
                return run7.huber_inc(a, jj, _p[0], _p[1], _p[2], _p[3])
            j = run6.world_pick(pm1, ps1, pm2, ps2, cand, belief, llr_now, inc_fn)
        elif acq == "oracle_reading":
            vals = [(abs(run7.huber_inc(readings[c], c, m1, s1, m2, s2))
                     if np.isfinite(readings[c]) else -1.0) for c in cand]
            j = int(cand[int(np.argmax(vals))])
        else:
            raise ValueError(acq)

        bought[j] = True
        measurements += 1
        if not np.isfinite(readings[j]):
            qc += 1
        else:
            purchased_pos.append(j)
        pos = np.array(purchased_pos, dtype=int)
        a_vec = readings[pos] if len(pos) else np.array([])
        n1, _ = lmm_neg2logf(a_vec, m1[pos], s1[pos], t1)
        n2, _ = lmm_neg2logf(a_vec, m2[pos], s2[pos], t2)
        traj.append((0.5 * (n2 - n1), measurements))
    return traj, measurements, qc


# ------------------------------------------------------------------ stopping
def outcome_eprocess(traj):
    for llr, m in traj:
        if llr >= ETHRESH:
            return {"decided": True, "correct": True, "measurements": m}
        if llr <= -ETHRESH:
            return {"decided": True, "correct": False, "measurements": m}
    return {"decided": False, "correct": False,
            "measurements": traj[-1][1] if traj else 0}


def outcome_at_lambda(traj, lam, truth_sign=1):
    for llr, m in traj:
        if llr >= lam:
            return {"decided": True, "correct": True, "measurements": m}
        if llr <= -lam:
            return {"decided": True, "correct": False, "measurements": m}
    return {"decided": False, "correct": False,
            "measurements": traj[-1][1] if traj else 0}


def crc_lambda(calib_trajs, alpha=ALPHA):
    """Conformal risk control: smallest grid lambda with bounded empirical risk;
    coverage-maximising among safe lambdas. Loss = decided AND wrong."""
    n = len(calib_trajs)
    bound = ((n + 1) / n) * alpha - 1.0 / n
    safe = []
    for lam in LAMBDA_GRID:
        losses = []
        cov = 0
        for traj in calib_trajs:
            out = outcome_at_lambda(traj, lam)
            losses.append(1.0 if (out["decided"] and not out["correct"]) else 0.0)
            cov += out["decided"]
        r = float(np.mean(losses))
        if r <= bound:
            safe.append((float(lam), cov / n, r))
    if not safe:
        return None, []
    best = max(safe, key=lambda x: x[1])
    return best[0], safe


def ltt_lambda(calib_trajs, alpha=ALPHA, delta=0.05):
    """Learn-Then-Test for the conditional risk P(wrong | decided) <= alpha.

    Hoeffding p-values per lambda for the mean of g_i = 1{wrong and decided} -
    alpha * 1{decided} <= 0; Bonferroni over the grid; smallest non-rejected.
    """
    n = len(calib_trajs)
    k = len(LAMBDA_GRID)
    chosen = None
    for lam in LAMBDA_GRID:
        g = []
        for traj in calib_trajs:
            out = outcome_at_lambda(traj, lam)
            g.append((1.0 if (out["decided"] and not out["correct"]) else 0.0)
                     - alpha * (1.0 if out["decided"] else 0.0))
        gm = float(np.mean(g))
        # Hoeffding p-value for E[g] > 0 with g in [-1-alpha, 1]
        rng_width = 2.0 + alpha
        p = float(np.exp(-2.0 * n * max(gm, 0.0) ** 2 / rng_width ** 2))
        if p <= delta / k:
            continue  # rejected: risk too high... keep scanning
        chosen = float(lam)
        break
    return chosen


# ------------------------------------------------------------------ info flag
def info_budget(pair, tau_pool, top=16):
    (m1, s1), (m2, s2), _ = pair
    d = (m1 - m2) ** 2
    denom = 2.0 * (s1 ** 2 + s2 ** 2 + 2.0 * max(tau_pool, 1e-6))
    g = np.where(np.isfinite(d), d / denom, 0.0)
    g = np.nan_to_num(g, nan=0.0)
    return float(np.sum(np.sort(g)[-top:]))


# ------------------------------------------------------------------ fold run
def run_fold(f, pack, labels, pool_arr, classes, out_rows, world_fit):
    auc, compounds, lines = pack["auc"], pack["compounds"], pack["lines"]
    meta, folds, menu = pack["meta"], pack["folds"], pack["menu"]
    idx = pack["index"]
    units_arr = meta["unit"].to_numpy()
    heldout = folds[f]
    heldout_set = set(heldout)
    train = [c for c in compounds if c not in heldout_set and labels[idx[c]] >= 0]
    train_pos = np.array([idx[c] for c in train])
    train_by_class = [[idx[c] for c in train if labels[idx[c]] == ci]
                      for ci in range(len(classes))]
    fw = run6.FoldWorld(auc, train_by_class, train_pos, pool_arr, KEY, units_arr)
    tau2, tau_pool = estimate_tau2(auc, train_pos, labels, fw.med, fw.scale,
                                   fw.valid, fw.med_p, fw.scale_p, pool_arr,
                                   len(classes))
    rivals = {}
    for ci in range(len(classes)):
        r, d = run6.select_rival(fw.med, fw.scale, fw.valid, pool_arr, classes, ci)
        if r is not None:
            rivals[ci] = (r, d)

    unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
    half_of = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}

    def pair_for(ci, rj, fw_):
        return (*run6.class_pair_templates(fw_.med, fw_.scale, fw_.valid,
                                           fw_.med_p, fw_.scale_p, pool_arr,
                                           ci, rj), (ci, rj))

    # -------- calibration episodes (split halves) per acquisition policy
    calib = {a: [] for a in ("ginfo", "world", "random")}
    for h in (0, 1):
        templ_src = [c for c in train if half_of[c] == h]
        eps_for = [c for c in train if half_of[c] != h]
        src_pos = np.array([idx[c] for c in templ_src])
        by_class_h = [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                      for ci in range(len(classes))]
        fwh = run6.FoldWorld(auc, by_class_h, src_pos, pool_arr, KEY, units_arr,
                             select=False)
        fwh.rank, fwh.weight = fw.rank, fw.weight
        fwh.center, fwh.V, fwh.tau2 = world5b.fit_basis(auc[src_pos][:, pool_arr],
                                                        fw.rank)
        rivals_h = {}
        for ci in range(len(classes)):
            r, d = run6.select_rival(fwh.med, fwh.scale, fwh.valid, pool_arr,
                                     classes, ci)
            if r is not None:
                rivals_h[ci] = (r, d)
        for c in eps_for:
            truth = labels[idx[c]]
            if truth not in rivals_h:
                continue
            x = idx[c]
            readings_full = auc[x, pool_arr]
            rj, _ = rivals_h[truth]
            pair = pair_for(truth, rj, fwh)
            sep, _ = run6.pair_separation(pair[0][0], pair[0][1], pair[1][0], pair[1][1])
            g_order = sorted(range(len(pool_arr)),
                             key=lambda j: (-((pair[0][0][j] - pair[1][0][j]) ** 2
                                              / max(2.0 * (pair[0][1][j] ** 2
                                                           + pair[1][1][j] ** 2
                                                           + 2.0 * max(tau_pool, 1e-6)), 1e-12)),
                                            sha(f"{KEY}|ginfo|{j}")))
            rng_order = list(range(len(pool_arr)))
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
            for acq, order in (("ginfo", g_order), ("world", rng_order),
                               ("random", rng_order)):
                w = fwh.make_world() if acq == "world" else None
                traj, _, _ = run_episode_v8(readings_full, pair, (tau2[truth], tau2[rj]),
                                            acq, order, world=w)
                calib[acq].append(traj)

    lam_crc = {a: crc_lambda(calib[a]) for a in calib}
    lam_ltt = {a: ltt_lambda(calib[a]) for a in ("ginfo", "world")}

    # -------- held-out episodes
    rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
    heldout_pos = np.array([idx[c] for c in heldout])
    shuffled_cols = {lj: rng.permutation(auc[heldout_pos, lj]) for lj in pool_arr}
    skipped = 0
    for i_held, c in enumerate(heldout):
        x = idx[c]
        truth = labels[x]
        if truth < 0 or truth not in rivals:
            skipped += 1
            continue
        rj, rival_d = rivals[truth]
        unit = str(meta.loc[c, "unit"])
        readings = auc[x, pool_arr]
        pair = pair_for(truth, rj, fw)
        ib = info_budget(pair, tau_pool)
        sep, _ = run6.pair_separation(pair[0][0], pair[0][1], pair[1][0], pair[1][1])
        g_order = sorted(range(len(pool_arr)),
                         key=lambda j: (-((pair[0][0][j] - pair[1][0][j]) ** 2
                                          / max(2.0 * (pair[0][1][j] ** 2
                                                       + pair[1][1][j] ** 2
                                                       + 2.0 * max(tau_pool, 1e-6)), 1e-12)),
                                        sha(f"{KEY}|ginfo|{j}")))
        rng_order = list(range(len(pool_arr)))
        np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
        shuffled_row = np.full(len(lines), np.nan)
        for lj in pool_arr:
            shuffled_row[lj] = shuffled_cols[lj][int(np.where(heldout_pos == x)[0][0])]
        shuf_readings = shuffled_row[pool_arr]

        arm_specs = [("lmm_ginfo", "ginfo", readings, False),
                     ("lmm_world", "world", readings, False),
                     ("lmm_random", "random", readings, False),
                     ("lmm_ginfo_shuffled", "ginfo", shuf_readings, True),
                     ("oracle_lmm", "oracle_reading", readings, False)]
        for name, acq, real, is_shuf in arm_specs:
            order = g_order if acq == "ginfo" else rng_order
            w = fw.make_world() if acq == "world" else None
            traj, m_tot, qc = run_episode_v8(real, pair, (tau2[truth], tau2[rj]),
                                             acq, order, world=w)
            base = {"fold": f, "compound": c, "unit": unit,
                    "class": classes[truth], "rival": classes[rj],
                    "rival_sep": rival_d, "info_budget": ib,
                    "qc_failures": int(qc)}
            out_e = outcome_eprocess(traj)
            out_rows.append({**base, "arm": name, "stopping": "eprocess", **out_e})
            if not is_shuf and acq in lam_crc and lam_crc[acq][0] is not None:
                out_c = outcome_at_lambda(traj, lam_crc[acq][0])
                out_rows.append({**base, "arm": name, "stopping": "crc", **out_c})
            if is_shuf:
                out_c = outcome_at_lambda(traj, lam_crc["ginfo"][0]
                                          if lam_crc["ginfo"][0] is not None else ETHRESH)
                out_rows.append({**base, "arm": name, "stopping": "crc", **out_c})
    world_fit[f] = {"rank": fw.rank, "weight": fw.weight, "tau_pool": tau_pool,
                    "tau2_median": float(np.median(tau2)),
                    "lam_crc": {a: v[0] for a, v in lam_crc.items()},
                    "lam_ltt": lam_ltt,
                    "heldout": len(heldout), "skipped_no_rival": skipped,
                    "calib_episodes": {a: len(calib[a]) for a in calib}}


# ------------------------------------------------------------------ summary
def summarise(ep):
    rng = np.random.default_rng(int(sha(f"{KEY}|boot")[:16], 16))
    arms = {}
    per_unit = {}
    for (arm, stop), g in ep.groupby(["arm", "stopping"]):
        g = g.copy()
        g["wrong_dec"] = g["decided"] & ~g["correct"]
        dec = int(g["decided"].sum())
        wrong = int(g["wrong_dec"].sum())
        key = f"{arm}__{stop}"
        arms[key] = {
            "episodes": int(len(g)),
            "coverage": float(g["decided"].mean()),
            "decided": dec,
            "wrong": wrong,
            "conditional_wrong": float(wrong / dec) if dec else None,
            "wrong_decision_rate": float(g["wrong_dec"].mean()),
            "cp_ucb95_wrong_dec": run6.cp_ucb95(wrong, len(g)),
            "cp_ucb95_cond": run6.cp_ucb95(wrong, dec),
            "correct": float(g["correct"].mean()),
            "measurements": float(g["measurements"].mean()),
            "cc_per_measurement": float(g["correct"].sum() / max(g["measurements"].sum(), 1)),
            "decide_true_rate": float((g["decided"] & g["correct"]).mean()),
            "info_budget_median": float(g["info_budget"].median()),
        }
        per_unit[key] = g.groupby("unit")[["correct", "decided", "wrong_dec",
                                           "measurements"]].mean()
        u = per_unit[key]["decided"].to_numpy()
        boot = [float(u[rng.integers(0, len(u), len(u))].mean()) for _ in range(DRAWS)]
        arms[key]["coverage_ci"] = [float(np.quantile(boot, 0.025)),
                                    float(np.quantile(boot, 0.975))]

    def diff_ci(a, b, col):
        ja = per_unit[a][[col]].join(per_unit[b][[col]], rsuffix="_b", how="inner")
        d = (ja[col] - ja[f"{col}_b"]).to_numpy()
        boot = [float(d[rng.integers(0, len(d), len(d))].mean()) for _ in range(DRAWS)]
        return {"diff": float(d.mean()),
                "ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]}

    contrasts = {
        "coverage_world_minus_random__crc": diff_ci("lmm_world__crc", "lmm_random__crc", "decided"),
        "coverage_world_minus_random__eprocess": diff_ci("lmm_world__eprocess", "lmm_random__eprocess", "decided"),
    }
    # information-flag analysis
    low = ep[ep["info_budget"] < 4.0]
    high = ep[ep["info_budget"] >= 4.0]
    flag = {}
    for label, sub in (("low", low), ("high", high)):
        g = sub[sub["arm"] == "lmm_ginfo"]
        if len(g):
            gg = g[g["stopping"] == "crc"]
            flag[label] = {"episodes": int(len(gg)),
                           "coverage_crc": float(gg["decided"].mean()) if len(gg) else None}
    return {"arms": arms, "contrasts": contrasts, "info_flag": flag}


def evaluate_gate(summary, phase):
    arms = summary["arms"]
    g = arms.get("lmm_ginfo__crc", {})
    ge = arms.get("lmm_ginfo__eprocess", {})
    sh = arms.get("lmm_ginfo_shuffled__crc", {})
    if phase == "pilot":
        p1 = (g.get("wrong_decision_rate") is not None
              and g["wrong_decision_rate"] <= 0.05
              and (g["cp_ucb95_wrong_dec"] or 1.0) <= 0.15
              and g["coverage"] >= 0.20)
        p2 = (ge.get("conditional_wrong") is not None
              and ge["conditional_wrong"] <= 0.05
              and sh.get("decide_true_rate", 1.0) <= 0.10)
        p3 = (summary["contrasts"]["coverage_world_minus_random__eprocess"]["diff"] >= 0)
        return {"checks": {"P1_crc_valid": bool(p1), "P2_model_valid": bool(p2),
                           "P3_dual_core": bool(p3)},
                "proceed_to_global": bool(p1)}
    g1 = (arms.get("lmm_ginfo__crc", {}).get("wrong_decision_rate", 1.0) <= 0.05
          and (arms.get("lmm_ginfo__crc", {}).get("cp_ucb95_wrong_dec") or 1.0) <= 0.10
          and arms.get("lmm_world__crc", {}).get("wrong_decision_rate", 1.0) <= 0.05
          and (arms.get("lmm_world__crc", {}).get("cp_ucb95_wrong_dec") or 1.0) <= 0.10
          and arms.get("lmm_ginfo__crc", {}).get("coverage", 0.0) >= 0.20)
    g2 = (ge.get("conditional_wrong") is not None and ge["conditional_wrong"] <= 0.05
          and (ge.get("cp_ucb95_cond") or 1.0) <= 0.10
          and sh.get("decide_true_rate", 1.0) <= 0.10)
    g3 = (summary["contrasts"]["coverage_world_minus_random__crc"]["diff"] > 0
          and summary["contrasts"]["coverage_world_minus_random__crc"]["ci"][0] > 0)
    low = summary["info_flag"].get("low", {})
    g4 = (low.get("coverage_crc") is not None and low["coverage_crc"] <= 0.30)
    return {"checks": {"G1_crc_valid": bool(g1), "G2_model_valid": bool(g2),
                       "G3_dual_core": bool(g3), "G4_information_flag": bool(g4)},
            "qualified": bool(g1 and g3)}


def main():
    t0 = time.time()
    pilot = "--pilot" in sys.argv
    out = ROOT / ("outputs/viability_contrast_20261008/run8_pilot" if pilot
                  else "outputs/viability_contrast_20261008/run8")
    pack = prepare.load_pack()
    compounds, lines = pack["compounds"], pack["lines"]
    meta, folds, menu = pack["meta"], pack["folds"], pack["menu"]
    classes = menu["classes"]
    class_index = {c: i for i, c in enumerate(classes)}
    idx = pack["index"]
    labels = np.full(len(compounds), -1)
    for c in compounds:
        lab = meta.loc[c, "moa_main"]
        if lab in class_index:
            labels[idx[c]] = class_index[lab]
    pool = [pack["line_index"][l] for l in menu["pool_lines"] if l in pack["line_index"]]
    pool_arr = np.asarray(pool)

    out.mkdir(parents=True, exist_ok=True)
    rows = []
    world_fit = {}
    fold_list = ["0"] if pilot else sorted(folds, key=int)
    for f in fold_list:
        run_fold(f, pack, labels, pool_arr, classes, rows, world_fit)
    ep = pd.DataFrame(rows)
    ep.to_csv(out / "episodes.csv", index=False)
    summary = summarise(ep)
    summary["folds"] = world_fit
    summary["phase"] = "pilot" if pilot else "global"
    summary["runtime_sec"] = time.time() - t0
    gate = evaluate_gate(summary, summary["phase"])
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (out / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "runtime_sec": summary["runtime_sec"],
                      "arms": {a: {k: v for k, v in s.items() if not k.endswith("_ci")}
                               for a, s in summary["arms"].items()},
                      "contrasts": summary["contrasts"],
                      "info_flag": summary["info_flag"]}, indent=1))


if __name__ == "__main__":
    main()
