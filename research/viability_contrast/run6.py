"""Dual-core run v6: two-class contrast with an anytime-valid (e-process) decision statistic.

File summary
- Path: research/viability_contrast/run6.py
- Purpose: protocol viability-contrast-6. Each held-out episode is a TWO-HYPOTHESIS class
  contrast (true class vs its nearest training-template rival); the decision statistic is
  the log-likelihood ratio between the two hypotheses with a FIXED a-priori threshold
  L = log(1/alpha), alpha = 0.05 - no tau, no calibration. Two statistic variants
  (stat_marginal: independent template Gaussians; stat_world: world5b blended predictive
  conditioned on the episode's purchased readings) cross three predictable acquisition
  rules (fixed pair-separation order, random, world-guided expected |LLR increment|),
  plus a label-blind realised-reading oracle ceiling, masked/shuffled controls, a
  no-winsorization sensitivity arm, and the v2-v5 calibrated-tau stopping comparator on
  the world_world trajectories. Gate v6: empirical Type-I behaviour (G1), dual-core
  information-cost value (G2), calibration-free power (G3); definitions in protocol6.json.
- Interfaces / data: reads the frozen pack via prepare.load_pack(); writes
  outputs/viability_contrast_20261008/run6/{episodes.csv, summary.json, gate.json,
  world_fit.json}.
- Depends on: research/viability_contrast/{protocol6.json, prepare.py, qualify.py,
  qualify2.py, world5b.py}

Registered implementation details (consistent with protocol6.json's inheritance list):
- Calibration-half worlds for the taucal comparator inherit the full-fold rank/weight
  (threshold-transfer assumption carried over from v2-v5; basis refitted per half).
- stat_world LLR increments use the same |z| <= 3 winsorization as stat_marginal, for
  comparability; the exact-martingale sensitivity arm is marginal and unwinsorized.
- The masked control mirrors v5 semantics: LLR increments use the compound's REAL
  readings while the world posterior sees ANOTHER held-out compound's readings at the
  same positions (tests compound-specificity of the world channel alone). The shuffled
  control replaces everything (label-breaking; measures empirical Type-I behaviour).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

from . import prepare, qualify, qualify2, world5b

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20261008/run6"
KEY = "viability-contrast-6"
BUDGET = 16
ALPHA = 0.05
ETHRESH = float(np.log(1.0 / ALPHA))
TAU_GRID = (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0)
TAU_MAX_WRONG = qualify2.TAU_MAX_WRONG
TAU_MIN_DECIDED = qualify2.TAU_MIN_DECIDED
MIN_JOINT_CELLS = 20
DRAWS = 10_000
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)
Z_QUANT = np.array([-2.0, -1.33, -0.67, 0.0, 0.67, 1.33, 2.0])
Q_W = np.exp(-0.5 * Z_QUANT**2)
Q_W = Q_W / Q_W.sum()
MIN_VAR = world5b.MIN_VAR
STATS = ("marg", "world")
ACQS = ("fixed", "random", "world")


def sha(text: str) -> str:
    return qualify2.sha(text)


def cp_ucb95(wrong: int, n: int) -> float | None:
    """One-sided Clopper-Pearson 95 percent upper bound on a wrong rate."""
    if n == 0:
        return None
    return float(beta_dist.ppf(0.95, wrong + 1, n - wrong))


# ------------------------------------------------------------------ pair setup
def class_pair_templates(med, scale, valid, med_p, scale_p, pool_arr, ci, cj):
    """(mean, sd) predictive per class restricted to the pool, with pooled fallback."""
    m = np.where(valid, med, med_p[None, :])[:, pool_arr]
    s = np.where(valid, scale, scale_p[None, :])[:, pool_arr]
    return (m[ci], s[ci]), (m[cj], s[cj])


def pair_separation(m1, s1, m2, s2):
    """Standardised per-line separation of two classes over the pool."""
    both = np.isfinite(m1) & np.isfinite(m2)
    sep = np.abs(m1 - m2) / np.maximum((s1 + s2) / 2.0, 0.05)
    return np.where(both, sep, np.nan), both


def select_rival(med, scale, valid, pool_arr, classes, ci):
    """Nearest class to ci by mean pool separation (training templates only)."""
    best, best_d = None, np.inf
    for cj in range(len(classes)):
        if cj == ci:
            continue
        sep, both = pair_separation(
            np.where(valid, med, np.nan)[ci][pool_arr],
            scale[ci][pool_arr],
            np.where(valid, med, np.nan)[cj][pool_arr],
            scale[cj][pool_arr])
        if both.sum() < MIN_JOINT_CELLS:
            continue
        d = float(np.nanmean(sep))
        if d < best_d - 1e-12 or (abs(d - best_d) <= 1e-12 and best is not None
                                  and sha(f"{KEY}|rival|{classes[ci]}|{classes[cj]}")
                                  < sha(f"{KEY}|rival|{classes[ci]}|{classes[best]}")):
            best, best_d = cj, d
    return best, best_d


# ------------------------------------------------------------------ statistic
def ll_terms(a, m, s, winsor=True):
    """Gaussian log-density term of reading a under N(m, s^2); NaN reading -> 0."""
    if not np.isfinite(a):
        return 0.0
    z = (a - m) / s
    zz = np.minimum(z * z, 9.0) if winsor else z * z
    return float(-0.5 * zz - np.log(s) - LOG_SQRT_2PI)


# ------------------------------------------------------------------ acquisition
def fixed_order(sep, tag):
    return sorted(range(len(sep)), key=lambda j: (-(sep[j] if np.isfinite(sep[j]) else -1.0),
                                                  sha(f"{KEY}|fixed|{tag}|{j}")))


def world_pick(m1, s1, m2, s2, cand, belief, llr_now, inc_fn):
    """Line maximising the belief-expected absolute LLR increment (K=7 quadrature)."""
    best_j, best_v = None, -np.inf
    for j in cand:
        v = 0.0
        for z, qw in zip(Z_QUANT, Q_W):
            a1 = m1[j] + s1[j] * z
            a2 = m2[j] + s2[j] * z
            v += belief * qw * abs(inc_fn(a1, j)) + (1.0 - belief) * qw * abs(inc_fn(a2, j))
        if v > best_v:
            best_v, best_j = v, j
    return best_j


# ------------------------------------------------------------------ episode
def run_episode(readings, pair, acq, stat, order, rng, world=None,
                profile_readings=None, winsor=True):
    """One two-class episode. Returns (traj, decided, decided_true, measurements, qc).

    traj: list of (llr, measurements) after each purchase. `pair` = ((m1,s1),(m2,s2),
    (row_h1,row_h2)). marginals used for increments when stat == 'marg' and for the
    acq_world quadrature in that variant; when stat == 'world' the increment predictives
    come from the world's blended mean_scale() restricted to the two class rows.
    """
    (m1, s1), (m2, s2), ci_rows = pair
    n_pool = len(readings)
    purchased = np.zeros(n_pool, dtype=bool)
    if profile_readings is None:
        profile_readings = readings
    llr = 0.0
    measurements = 0
    qc = 0
    traj = []
    order_pos = 0
    decided = False
    decided_true = False
    while measurements < BUDGET:
        belief = 1.0 / (1.0 + np.exp(-llr)) if abs(llr) < 700 else (1.0 if llr > 0 else 0.0)
        belief = min(max(belief, 1e-6), 1.0 - 1e-6)
        if stat == "world" and world is not None:
            wm, ws = world.mean_scale()
            pm1, ps1 = wm[ci_rows[0]], ws[ci_rows[0]]
            pm2, ps2 = wm[ci_rows[1]], ws[ci_rows[1]]
        else:
            pm1, ps1, pm2, ps2 = m1, s1, m2, s2

        def inc_fn(a, j, _p=(pm1, ps1, pm2, ps2)):
            return ll_terms(a, _p[0][j], _p[1][j], winsor) - ll_terms(a, _p[2][j], _p[3][j], winsor)

        cand = np.where(~purchased)[0]
        if len(cand) == 0:
            break
        if acq == "fixed" or acq == "random":
            j = -1
            while order_pos < len(order):
                c = order[order_pos]
                order_pos += 1
                if not purchased[c]:
                    j = c
                    break
            if j < 0:
                break
        elif acq == "world":
            j = world_pick(pm1, ps1, pm2, ps2, cand, belief, llr, inc_fn)
        elif acq == "oracle_reading":
            vals = [(abs(ll_terms(readings[c], pm1[c], ps1[c], winsor)
                        - ll_terms(readings[c], pm2[c], ps2[c], winsor))
                     if np.isfinite(readings[c]) else -1.0) for c in cand]
            j = int(cand[int(np.argmax(vals))])
        else:
            raise ValueError(acq)
        purchased[j] = True
        measurements += 1
        a = readings[j]
        if not np.isfinite(a):
            qc += 1
        else:
            llr += inc_fn(a, j)
        if world is not None:
            pos = np.where(purchased & np.isfinite(profile_readings))[0]
            if len(pos):
                world.update(profile_readings[pos], pos)
        traj.append((llr, measurements))
        if llr >= ETHRESH:
            decided, decided_true = True, True
            break
        if llr <= -ETHRESH:
            decided, decided_true = True, False
            break
    return traj, decided, decided_true, measurements, qc


def outcome_from_traj(traj, decided, decided_true, measurements, qc):
    return {"decided": bool(decided), "correct": bool(decided and decided_true),
            "measurements": int(measurements), "qc_failures": int(qc),
            "final_llr": float(traj[-1][0]) if traj else 0.0}


def outcome_at_tau_llr(traj, tau):
    """Calibrated-tau comparator on an LLR trajectory (v2-v5 stopping rule)."""
    for llr, m in traj:
        if abs(llr) >= tau:
            return {"decided": True, "correct": bool(llr > 0), "measurements": m}
    return {"decided": False, "correct": False,
            "measurements": traj[-1][1] if traj else 0}


# ------------------------------------------------------------------ fold machinery
class FoldWorld:
    """Templates + world5b selection for one training fold (or one calibration half)."""

    def __init__(self, auc, train_by_class, train_pos, pool_arr, key, units,
                 select=True):
        med, scale, valid, med_p, scale_p = qualify2.build_templates_v2(auc, train_by_class)
        self.med, self.scale, self.valid = med, scale, valid
        self.med_p, self.scale_p = med_p, scale_p
        self.base_m = np.where(valid, med, med_p[None, :])[:, pool_arr]
        self.base_s = np.where(valid, scale, scale_p[None, :])[:, pool_arr]
        self.rank, self.weight = 8, 0.5
        self.rank_ll, self.weight_ll = {}, {}
        if select:
            self.rank, self.rank_ll = world5b.select_rank(
                auc, train_by_class, train_pos, self.base_m, self.base_s,
                pool_arr, key, units)
            center, V, tau2 = world5b.fit_basis(auc[train_pos][:, pool_arr], self.rank)
            self.weight, self.weight_ll = world5b.select_weight(
                auc, train_by_class, self.base_m, self.base_s, pool_arr, key, units,
                center, V, tau2)
        self.center, self.V, self.tau2 = world5b.fit_basis(
            auc[train_pos][:, pool_arr], self.rank)

    def make_world(self):
        return world5b.LearnedWorld(self.center, self.V, self.tau2, self.base_m,
                                    self.base_s, blend_mode="holdout",
                                    blend_w=self.weight)


def calibrate_tau(fw_half, episodes, class_rows):
    """Split-half tau calibration for the world_world trajectory comparator."""
    table = {}
    for tau in TAU_GRID:
        dec = wrong = 0
        for traj in episodes:
            out = outcome_at_tau_llr(traj, tau)
            if out["decided"]:
                dec += 1
                wrong += not out["correct"]
        table[tau] = {"decided": dec, "wrong": wrong,
                      "rate": (wrong / dec) if dec else None}
    qualifying = [tau for tau, t in table.items()
                  if t["decided"] >= TAU_MIN_DECIDED and t["rate"] is not None
                  and t["rate"] <= TAU_MAX_WRONG]
    return (min(qualifying) if qualifying else float("inf")), table


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
        fw = FoldWorld(auc, train_by_class, train_pos, pool_arr, KEY, units_arr)

        rivals = {}
        for ci in range(len(classes)):
            r, d = select_rival(fw.med, fw.scale, fw.valid, pool_arr, classes, ci)
            if r is not None:
                rivals[ci] = (r, d)

        # -------- split-half calibration episodes for the taucal comparator
        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half_of = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}
        calib_trajs = []
        for h in (0, 1):
            templ_src = [c for c in train if half_of[c] == h]
            eps_for = [c for c in train if half_of[c] != h]
            src_pos = np.array([idx[c] for c in templ_src])
            by_class_h = [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                          for ci in range(len(classes))]
            fwh = FoldWorld(auc, by_class_h, src_pos, pool_arr, KEY, units_arr,
                            select=False)
            fwh.rank, fwh.weight = fw.rank, fw.weight
            fwh.center, fwh.V, fwh.tau2 = world5b.fit_basis(
                auc[src_pos][:, pool_arr], fw.rank)
            rivals_h = {}
            for ci in range(len(classes)):
                r, d = select_rival(fwh.med, fwh.scale, fwh.valid, pool_arr, classes, ci)
                if r is not None:
                    rivals_h[ci] = (r, d)
            for c in eps_for:
                x = idx[c]
                truth = labels[x]
                if truth not in rivals_h:
                    continue
                rj, _ = rivals_h[truth]
                pair = (*class_pair_templates(fwh.med, fwh.scale, fwh.valid,
                                              fwh.med_p, fwh.scale_p, pool_arr,
                                              truth, rj), (truth, rj))
                readings = auc[x, pool_arr]
                erng = np.random.default_rng(int(sha(f"{KEY}|calib|world|{c}")[:16], 16))
                order = list(range(len(pool)))
                erng.shuffle(order)
                w = fwh.make_world()
                traj, _, _, _, _ = run_episode(readings, pair, "world", "world",
                                               order, erng, world=w)
                calib_trajs.append(traj)
        tau_cal, tau_table = calibrate_tau(None, calib_trajs, None)

        # -------- held-out episodes
        rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
        heldout_pos = np.array([idx[c] for c in heldout])
        shuffled_cols = {lj: rng.permutation(auc[heldout_pos, lj]) for lj in pool}
        mask_perm = rng.permutation(len(heldout))
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
            pair = (*class_pair_templates(fw.med, fw.scale, fw.valid,
                                          fw.med_p, fw.scale_p, pool_arr,
                                          truth, rj), (truth, rj))
            sep, _ = pair_separation(pair[0][0], pair[0][1], pair[1][0], pair[1][1])
            order_fixed = fixed_order(sep, f"{f}")
            order_random = list(range(len(pool)))
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(order_random)

            masked = heldout[mask_perm[i_held]]
            masked_readings = auc[idx[masked], pool_arr]
            shuffled_row = np.full(len(lines), np.nan)
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][int(np.where(heldout_pos == x)[0][0])]
            shuf_readings = shuffled_row[pool_arr]

            arm_specs = []
            for stat in STATS:
                for acq in ACQS:
                    arm_specs.append((f"{stat}_{acq}", stat, acq, readings, None, True))
            arm_specs.append(("oracle_reading", "marg", "oracle_reading", readings, None, True))
            arm_specs.append(("world_world_masked", "world", "world", readings,
                              masked_readings, True))
            arm_specs.append(("world_world_shuffled", "world", "world", shuf_readings,
                              shuf_readings, True))
            arm_specs.append(("marg_nowin_world", "marg", "world", readings, None, False))

            for name, stat, acq, real, prof, winsor in arm_specs:
                erng = np.random.default_rng(int(sha(f"{KEY}|{name}|{c}")[:16], 16))
                order = order_fixed if acq == "fixed" else order_random
                w = fw.make_world() if stat == "world" else None
                traj, dec, dec_true, m, qc = run_episode(
                    real, pair, acq, stat, order, erng, world=w,
                    profile_readings=prof, winsor=winsor)
                out = outcome_from_traj(traj, dec, dec_true, m, qc)
                rows.append({"fold": f, "compound": c, "unit": unit,
                             "class": classes[truth], "rival": classes[rj],
                             "rival_sep": rival_d, "arm": name, **out})
                if name == "world_world":
                    out_t = outcome_at_tau_llr(traj, tau_cal)
                    rows.append({"fold": f, "compound": c, "unit": unit,
                                 "class": classes[truth], "rival": classes[rj],
                                 "rival_sep": rival_d, "arm": "world_world_taucal",
                                 "decided": out_t["decided"], "correct": out_t["correct"],
                                 "measurements": out_t["measurements"],
                                 "qc_failures": qc, "final_llr": traj[-1][0] if traj else 0.0})
        world_fit[f] = {"rank": fw.rank, "rank_ll": {str(k): v for k, v in fw.rank_ll.items()},
                        "weight": fw.weight,
                        "weight_ll": {str(k): v for k, v in fw.weight_ll.items()},
                        "tau_cal": (None if np.isinf(tau_cal) else tau_cal),
                        "tau_table": {str(k): v for k, v in tau_table.items()},
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
    summary["episodes_per_arm"] = int((ep["arm"] == "world_world").sum())
    summary["runtime_sec"] = time.time() - t0
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    gate = evaluate_gate_v6(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "runtime_sec": summary["runtime_sec"],
                      "arms": {a: {k: v for k, v in s.items() if not k.endswith("_ci")}
                               for a, s in summary["arms"].items()},
                      "contrasts": summary["contrasts"]}, indent=1))


# ------------------------------------------------------------------ summary
def summarise(ep: pd.DataFrame) -> dict:
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
            "cp_ucb95": cp_ucb95(wrong, dec),
            "correct": float(g["correct"].mean()),
            "measurements": float(g["measurements"].mean()),
            "measurements_decided": float(g.loc[g["decided"], "measurements"].mean()) if dec else None,
            "qc_failures": float(g["qc_failures"].mean()),
            "decide_true_rate": float((g["decided"] & g["correct"]).mean()),
        }
        pu = g.groupby("unit")[["correct", "decided", "wrong", "measurements"]].mean()
        per_unit[arm] = pu
        for col, key in (("decided", "coverage_ci"), ("measurements", "measurements_ci")):
            u = pu[col].to_numpy()
            boot = [float(u[rng.integers(0, len(u), len(u))].mean()) for _ in range(DRAWS)]
            arms[arm][key] = [float(np.quantile(boot, 0.025)),
                              float(np.quantile(boot, 0.975))]

    def diff_ci(a, b, col):
        ja = per_unit[a][[col]].join(per_unit[b][[col]], rsuffix="_b", how="inner")
        d = (ja[col] - ja[f"{col}_b"]).to_numpy()
        boot = [float(d[rng.integers(0, len(d), len(d))].mean()) for _ in range(DRAWS)]
        return {"diff": float(d.mean()),
                "ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]}

    contrasts = {
        "coverage_world_world_minus_marg_random":
            diff_ci("world_world", "marg_random", "decided"),
        "measurements_world_world_minus_marg_fixed":
            diff_ci("world_world", "marg_fixed", "measurements"),
        "coverage_world_world_minus_taucal":
            diff_ci("world_world", "world_world_taucal", "decided"),
        "coverage_world_minus_marg_world":
            diff_ci("world_world", "marg_world", "decided"),
        "coverage_marg_world_minus_marg_random":
            diff_ci("marg_world", "marg_random", "decided"),
        "coverage_world_world_minus_masked":
            diff_ci("world_world", "world_world_masked", "decided"),
        "coverage_world_world_minus_world_random":
            diff_ci("world_world", "world_random", "decided"),
    }
    return {"arms": arms, "contrasts": contrasts}


def evaluate_gate_v6(summary: dict) -> dict:
    arms = summary["arms"]
    c = summary["contrasts"]
    ww = arms["world_world"]
    shuf = arms["world_world_shuffled"]
    g1 = (ww["conditional_wrong"] is not None and ww["cp_ucb95"] is not None
          and ww["conditional_wrong"] <= 0.05 and ww["cp_ucb95"] <= 0.10
          and shuf["decide_true_rate"] <= 0.10)
    g2a = (c["coverage_world_world_minus_marg_random"]["diff"] > 0
           and c["coverage_world_world_minus_marg_random"]["ci"][0] > 0)
    g2b = (c["measurements_world_world_minus_marg_fixed"]["diff"] <= 0)
    g3 = (c["coverage_world_world_minus_taucal"]["diff"] >= 0
          and (arms["world_world_taucal"]["conditional_wrong"] is None
               or ww["conditional_wrong"] <= max(
                   arms["world_world_taucal"]["conditional_wrong"], 0.05)))
    return {"checks": {"G1_validity": bool(g1),
                       "G2a_coverage_above_random": bool(g2a),
                       "G2b_cost_below_fixed": bool(g2b),
                       "G3_calibration_free": bool(g3)},
            "qualified": bool(g1 and g2a and g2b and g3)}


if __name__ == "__main__":
    main()
