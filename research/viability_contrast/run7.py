"""Dual-core run v7: robust e-process statistics for the two-class contrast.

File summary
- Path: research/viability_contrast/run7.py
- Purpose: protocol viability-contrast-7. v6 measured the naive Gaussian LLR as
  invalid (heavy tails M1 + cross-line correlation M2). v7 evaluates three registered
  statistic families at the same fixed a-priori threshold log(1/alpha), alpha = 0.05:
  S_huber (per-line density floored at |z| = 2; the Huber/Saha-Ramdas LFD clip,
  implemented as winsorization at 2), S_corr (joint multivariate-Gaussian LR with a
  shrunk pooled residual-correlation matrix from the training fold, z clipped at 3),
  and S_bet (bounded betting e-process on tanh of the S_huber increment, predictable
  lambda). Acquisition (fixed / random / world5b-guided) and the label-blind
  oracle_reading ceiling are as in v6; shuffled controls measure empirical Type-I.
  The virtual cell guides acquisition only; no statistic uses the world (registered).
- Interfaces / data: reads the frozen pack via prepare.load_pack() and the frozen v6
  episodes for the cross-run efficiency contrast; writes
  outputs/viability_contrast_20261008/run7/{episodes.csv, summary.json, gate.json,
  world_fit.json}.
- Depends on: research/viability_contrast/{protocol7.json, prepare.py, qualify.py,
  qualify2.py, world5b.py, run6.py}
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify2, run6

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20261008/run7"
V6_EPISODES = ROOT / "outputs/viability_contrast_20261008/run6/episodes.csv"
KEY = "viability-contrast-7"
BUDGET = 16
ALPHA = 0.05
ETHRESH = float(np.log(1.0 / ALPHA))
Z_HUBER = 2.0          # S_huber density floor (Saha-Ramdas LFD clip)
Z_CORR = 3.0           # S_corr bounded-influence clip (registered approximation)
SHRINK = 0.3           # residual correlation shrinkage toward identity
EIG_FLOOR = 1e-3
MIN_CORR_OBS = 30
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)
DRAWS = 10_000
STATS_ACQS = [("huber", "fixed"), ("huber", "random"), ("huber", "world"),
              ("corr", "fixed"), ("corr", "world"),
              ("bet", "fixed"), ("bet", "world")]


def sha(text: str) -> str:
    return qualify2.sha(text)


# ------------------------------------------------------------------ increments
def huber_term(a, m, s):
    """Floored Gaussian log-density (density floored at its |z| = Z_HUBER value)."""
    if not np.isfinite(a):
        return 0.0
    z = (a - m) / s
    return float(max(-0.5 * z * z, -0.5 * Z_HUBER**2) - np.log(s) - LOG_SQRT_2PI)


def huber_inc(a, j, pm1, ps1, pm2, ps2):
    return huber_term(a, pm1[j], ps1[j]) - huber_term(a, pm2[j], ps2[j])


# ------------------------------------------------------------------ correlation
def fit_residual_correlation(auc, train_pos, labels, med, scale, valid, med_p,
                             scale_p, pool_arr):
    """Shrunk pooled residual correlation over pool lines (training compounds only).

    Residuals are winsorized at |z| = 3 against each compound's OWN class template
    (pooled fallback), pairwise-complete correlations with >= MIN_CORR_OBS
    observations, shrunk toward identity by SHRINK, eigenvalues floored.
    """
    m = np.where(valid, med, med_p[None, :])
    s = np.where(valid, scale, scale_p[None, :])
    block = auc[train_pos][:, pool_arr]
    lab = labels[train_pos]
    z = (block - m[lab][:, :]) / s[lab][:, :]
    z = np.clip(z, -3.0, 3.0)
    df = pd.DataFrame(z)
    R = df.corr(min_periods=MIN_CORR_OBS).to_numpy()
    R = np.where(np.isfinite(R), R, 0.0)
    n = R.shape[0]
    R = (1.0 - SHRINK) * R + SHRINK * np.eye(n)
    w, V = np.linalg.eigh(R)
    w = np.maximum(w, EIG_FLOOR)
    R = (V * w[None, :]) @ V.T
    d = np.sqrt(np.diag(R))
    return R / d[None, :] / d[:, None]


def joint_lr(purchased, m1, s1, m2, s2, R):
    """Joint multivariate-Gaussian LR over purchased {line: reading}, z clipped.

    log|R_J| and the normalising constants cancel between hypotheses.
    """
    J = sorted(purchased)
    t = len(J)
    if t == 0:
        return 0.0
    a = np.array([purchased[j] for j in J])
    jm1, js1 = m1[J], s1[J]
    jm2, js2 = m2[J], s2[J]
    z1 = np.clip((a - jm1) / js1, -Z_CORR, Z_CORR)
    z2 = np.clip((a - jm2) / js2, -Z_CORR, Z_CORR)
    Rj = R[np.ix_(J, J)]
    try:
        x1 = np.linalg.solve(Rj, z1)
        x2 = np.linalg.solve(Rj, z2)
    except np.linalg.LinAlgError:
        x1 = np.linalg.lstsq(Rj, z1, rcond=None)[0]
        x2 = np.linalg.lstsq(Rj, z2, rcond=None)[0]
    return float(-0.5 * (z1 @ x1 - z2 @ x2) - np.log(js1).sum() + np.log(js2).sum())


# ------------------------------------------------------------------ episode
def run_episode_v7(readings, pair, stat, acq, order, world=None, R=None):
    """One two-class episode under a v7 statistic. Returns (traj, decided,
    decided_true, measurements, qc). traj holds (statistic_value, measurements)."""
    (m1, s1), (m2, s2), _ = pair
    purchased = {}
    bought = np.zeros(len(readings), dtype=bool)
    value = 0.0
    e_plus = 1.0
    e_minus = 1.0
    bs = []
    measurements = 0
    qc = 0
    traj = []
    order_pos = 0
    decided = False
    decided_true = False
    while measurements < BUDGET:
        if stat == "bet":
            belief = e_plus / (e_plus + e_minus)
        else:
            belief = 1.0 / (1.0 + np.exp(-value)) if abs(value) < 700 else (
                1.0 if value > 0 else 0.0)
        belief = min(max(belief, 1e-6), 1.0 - 1e-6)
        if world is not None:
            pos = np.array(sorted(purchased))
            if len(pos):
                world.update(np.array([readings[j] for j in pos]), pos)
            wm, ws = world.mean_scale()
            pm1, ps1 = wm[pair[2][0]], ws[pair[2][0]]
            pm2, ps2 = wm[pair[2][1]], ws[pair[2][1]]
        else:
            pm1, ps1, pm2, ps2 = m1, s1, m2, s2

        cand = np.where(~bought)[0]
        if len(cand) == 0:
            break
        if acq in ("fixed", "random"):
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
                return huber_inc(a, jj, _p[0], _p[1], _p[2], _p[3])
            j = run6.world_pick(pm1, ps1, pm2, ps2, cand, belief, value, inc_fn)
        elif acq == "oracle_reading":
            vals = [(abs(huber_inc(readings[c], c, m1, s1, m2, s2))
                     if np.isfinite(readings[c]) else -1.0) for c in cand]
            j = int(cand[int(np.argmax(vals))])
        else:
            raise ValueError(acq)

        bought[j] = True
        measurements += 1
        a = readings[j]
        if not np.isfinite(a):
            qc += 1
        else:
            purchased[j] = a
            if stat == "huber" or acq == "oracle_reading":
                value += huber_inc(a, j, m1, s1, m2, s2)
            elif stat == "corr":
                value = joint_lr(purchased, m1, s1, m2, s2, R)
            elif stat == "bet":
                b = float(np.tanh(huber_inc(a, j, m1, s1, m2, s2) / 2.0))
                lam_p = float(np.clip(2.0 * np.mean(bs), 0.0, 0.9)) if bs else 0.5
                lam_m = float(np.clip(-2.0 * np.mean(bs), 0.0, 0.9)) if bs else 0.5
                e_plus *= 1.0 + lam_p * b
                e_minus *= 1.0 - lam_m * b
                bs.append(b)
            else:
                raise ValueError(stat)
        if stat == "bet":
            traj.append((float(np.log(max(e_plus, 1e-300))), measurements))
            if e_plus >= 1.0 / ALPHA:
                decided, decided_true = True, True
                break
            if e_minus >= 1.0 / ALPHA:
                decided, decided_true = True, False
                break
        else:
            traj.append((value, measurements))
            if value >= ETHRESH:
                decided, decided_true = True, True
                break
            if value <= -ETHRESH:
                decided, decided_true = True, False
                break
    return traj, decided, decided_true, measurements, qc


# ------------------------------------------------------------------ summary
def summarise(ep):
    rng = np.random.default_rng(int(sha(f"{KEY}|boot")[:16], 16))
    arms = {}
    per_unit = {}
    for arm, g in ep.groupby("arm"):
        g = g.copy()
        g["wrong"] = g["decided"] & ~g["correct"]
        dec = int(g["decided"].sum())
        wrong = int(g["wrong"].sum())
        arms[arm] = {
            "episodes": int(len(g)),
            "coverage": float(g["decided"].mean()),
            "decided": dec,
            "wrong": wrong,
            "conditional_wrong": float(wrong / dec) if dec else None,
            "cp_ucb95": run6.cp_ucb95(wrong, dec),
            "correct": float(g["correct"].mean()),
            "measurements": float(g["measurements"].mean()),
            "cc_per_measurement": float(g["correct"].sum() / g["measurements"].sum()),
            "qc_failures": float(g["qc_failures"].mean()),
            "decide_true_rate": float((g["decided"] & g["correct"]).mean()),
        }
        per_unit[arm] = g.groupby("unit")[["correct", "decided", "wrong",
                                           "measurements"]].mean()
        u = per_unit[arm]["decided"].to_numpy()
        boot = [float(u[rng.integers(0, len(u), len(u))].mean()) for _ in range(DRAWS)]
        arms[arm]["coverage_ci"] = [float(np.quantile(boot, 0.025)),
                                    float(np.quantile(boot, 0.975))]

    def diff_ci(a, b, col):
        ja = per_unit[a][[col]].join(per_unit[b][[col]], rsuffix="_b", how="inner")
        d = (ja[col] - ja[f"{col}_b"]).to_numpy()
        boot = [float(d[rng.integers(0, len(d), len(d))].mean()) for _ in range(DRAWS)]
        return {"diff": float(d.mean()),
                "ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]}

    contrasts = {
        "coverage_huber_world_minus_random": diff_ci("huber_world", "huber_random", "decided"),
        "coverage_corr_world_minus_fixed": diff_ci("corr_world", "corr_fixed", "decided"),
        "wrong_corr_world_minus_huber_world": {
            "diff": (arms["corr_world"]["conditional_wrong"] or 0.0)
                    - (arms["huber_world"]["conditional_wrong"] or 0.0)},
    }
    return {"arms": arms, "contrasts": contrasts}


def evaluate_gate_v7(summary, v6_cc):
    arms = summary["arms"]
    c = summary["contrasts"]
    g1_arms = {}
    for a in ("huber_world", "corr_world"):
        s = arms[a]
        g1_arms[a] = bool(
            s["conditional_wrong"] is not None and s["cp_ucb95"] is not None
            and s["conditional_wrong"] <= 0.05 and s["cp_ucb95"] <= 0.10
            and arms[f"{a}_shuffled"]["decide_true_rate"] <= 0.10)
    g1 = all(g1_arms.values())
    g2 = (c["coverage_huber_world_minus_random"]["diff"] > 0
          and c["coverage_huber_world_minus_random"]["ci"][0] > 0)
    g3 = arms["huber_world"]["cc_per_measurement"] >= v6_cc
    return {"checks": {"G1_validity": g1, "G1_per_arm": g1_arms,
                       "G2_dual_core": bool(g2), "G3_efficiency": bool(g3)},
            "v6_marg_fixed_cc_per_measurement": v6_cc,
            "qualified": bool(g1 and g2 and g3)}


# ------------------------------------------------------------------ main run
def main():
    t0 = time.time()
    pack = prepare.load_pack()
    auc, compounds, lines = pack["auc"], pack["compounds"], pack["lines"]
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
    units_arr = meta["unit"].to_numpy()

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    world_fit = {}
    for f in sorted(folds, key=int):
        heldout = folds[f]
        heldout_set = set(heldout)
        train = [c for c in compounds if c not in heldout_set and labels[idx[c]] >= 0]
        train_pos = np.array([idx[c] for c in train])
        train_by_class = [[idx[c] for c in train if labels[idx[c]] == ci]
                          for ci in range(len(classes))]
        fw = run6.FoldWorld(auc, train_by_class, train_pos, pool_arr, KEY, units_arr)
        R = fit_residual_correlation(auc, train_pos, labels, fw.med, fw.scale,
                                     fw.valid, fw.med_p, fw.scale_p, pool_arr)
        rivals = {}
        for ci in range(len(classes)):
            r, d = run6.select_rival(fw.med, fw.scale, fw.valid, pool_arr, classes, ci)
            if r is not None:
                rivals[ci] = (r, d)

        rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
        heldout_pos = np.array([idx[c] for c in heldout])
        shuffled_cols = {lj: rng.permutation(auc[heldout_pos, lj]) for lj in pool}
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
            pair = (*run6.class_pair_templates(fw.med, fw.scale, fw.valid,
                                               fw.med_p, fw.scale_p, pool_arr,
                                               truth, rj), (truth, rj))
            sep, _ = run6.pair_separation(pair[0][0], pair[0][1], pair[1][0], pair[1][1])
            order_fixed = run6.fixed_order(sep, f"{f}")
            order_random = list(range(len(pool)))
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(order_random)
            shuffled_row = np.full(len(lines), np.nan)
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][int(np.where(heldout_pos == x)[0][0])]
            shuf_readings = shuffled_row[pool_arr]

            arm_specs = [(f"{s}_{a}", s, a, readings) for s, a in STATS_ACQS]
            arm_specs += [(f"{s}_world_shuffled", s, "world", shuf_readings)
                          for s in ("huber", "corr", "bet")]
            arm_specs += [("oracle_huber", "huber", "oracle_reading", readings)]

            for name, stat, acq, real in arm_specs:
                order = order_fixed if acq == "fixed" else order_random
                w = fw.make_world() if acq == "world" else None
                traj, dec, dec_true, m, qc = run_episode_v7(
                    real, pair, stat, acq, order, world=w, R=R)
                rows.append({"fold": f, "compound": c, "unit": unit,
                             "class": classes[truth], "rival": classes[rj],
                             "rival_sep": rival_d, "arm": name,
                             "decided": bool(dec), "correct": bool(dec and dec_true),
                             "measurements": int(m), "qc_failures": int(qc),
                             "final_value": float(traj[-1][0]) if traj else 0.0})
        world_fit[f] = {"rank": fw.rank, "weight": fw.weight,
                        "rivals": {classes[ci]: {"rival": classes[rivals[ci][0]],
                                                 "sep": rivals[ci][1]}
                                   for ci in rivals},
                        "heldout": len(heldout), "skipped_no_rival": skipped}

    ep = pd.DataFrame(rows)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = summarise(ep)
    summary["folds"] = world_fit
    summary["budget"] = BUDGET
    summary["ethresh"] = ETHRESH
    summary["z_huber"] = Z_HUBER
    summary["shrink"] = SHRINK
    summary["episodes_per_arm"] = int((ep["arm"] == "huber_world").sum())
    summary["runtime_sec"] = time.time() - t0

    v6 = pd.read_csv(V6_EPISODES)
    v6f = v6[v6["arm"] == "marg_fixed"]
    v6_cc = float(v6f["correct"].sum() / v6f["measurements"].sum())

    gate = evaluate_gate_v7(summary, v6_cc)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "runtime_sec": summary["runtime_sec"],
                      "arms": {a: {k: v for k, v in s.items() if not k.endswith("_ci")}
                               for a, s in summary["arms"].items()},
                      "contrasts": summary["contrasts"]}, indent=1))


if __name__ == "__main__":
    main()
