"""Dual-core run v5b: corrected world, registered fusion variants, decomposed oracles.

File summary
- Path: research/viability_contrast/run5b.py
- Purpose: protocol viability-contrast-5b. Re-runs the v5 grid under the C1 variance
  correction (world5b) with three fusion rules (precision / holdout / off), decomposes
  the ceiling into oracle_reading (true readings, no label) and oracle_label (label,
  no true readings), and reports Clopper-Pearson one-sided 95% upper bounds next to the
  v5 point-estimate rule (tau_emp vs tau_ucb). Acquisition rules, episodes, folds,
  menus, budget, validator and tau grid are inherited unchanged from the frozen v5
  (run5 functions are imported, not copied; the calibration split-half assignment is
  keyed by the v5 hash so the halves are identical). v5 arms are imported from the
  frozen v5 outputs for cross-run comparison; v3/v4 arms arrive through that file.
- Interfaces / data: reads the frozen pack, prepare5.load_genetic() and run5's
  episodes.csv; writes outputs/viability_contrast_20260928/run5b/{episodes.csv,
  summary.json, gate.json, world_fit.json}.
- Depends on: research/viability_contrast/{protocol5b.json, prepare.py, prepare5.py,
  qualify.py, qualify2.py, run5.py, world5b.py}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

from . import prepare, prepare5, qualify, qualify2, run5, world5b

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/run5b"
RUN5 = ROOT / "outputs/viability_contrast_20260928/run5"
KEY = "viability-contrast-5b"
HALF_KEY = "viability-contrast-5"   # preserves the v5 calibration split halves
BUDGET = 16
RULES = run5.RULES
TAU_GRID = run5.TAU_GRID5
Z_QUANT = run5.Z_QUANT
Q_W = run5.Q_W
LOG_SQRT_2PI = run5.LOG_SQRT_2PI
BLEND_ARMS = [f"planner_{b}_{r}" for b in ("precision", "holdout") for r in RULES]
REALISTIC = BLEND_ARMS + ["planner_off_mi"]
IMPORTED_ARMS = run5.IMPORTED_ARMS + [f"planner_learned_{r}" for r in RULES] + [
    f"planner_learned_{r}_{c}" for r in RULES for c in ("masked", "shuffled")]
ORACLE_ARMS = ("oracle_reading", "oracle_label")


def sha(text: str) -> str:
    return qualify2.sha(text)


def cp_ucb(wrong: int, decided: int):
    """Clopper-Pearson one-sided 95% upper bound on the wrong rate (protocol5b C4)."""
    if decided == 0:
        return None
    return float(beta_dist.ppf(0.95, wrong + 1, decided - wrong))


# ------------------------------------------------------------------ oracle runners
def run_oracle_episode(mode, truth, T, val_m, val_s, budget=BUDGET):
    """Episode runner for the decomposed ceilings (protocol5b C3).

    mode "reading": sees T (all classes' true future terms), not the label; buys the
    candidate whose realised update maximises the top1-top2 score margin.
    mode "label": sees the label, not T; buys the candidate maximising the expected
    margin of the true class over the best other class under the true class's own
    template predictive; can be charged QC failures like any realistic arm.
    Trajectory rows match qualify2.outcome_at_tau.
    """
    n_classes = T.shape[0]
    scores = np.zeros(n_classes)
    purchased = np.zeros(T.shape[1], dtype=bool)
    traj = []
    measurements = 0
    while measurements < budget:
        if mode == "reading":
            cand = np.where(np.isfinite(T[0]) & ~purchased)[0]
            if len(cand) == 0:
                break
            after = scores[:, None] + T[:, cand]
            part = np.partition(after, -2, axis=0)
            margin = part[-1] - part[-2]
            pick = int(np.argmax(margin))
            ties = np.where(margin == margin[pick])[0]
            if len(ties) > 1:
                pick = min(ties, key=lambda jj: sha(f"{KEY}|or|{int(cand[jj])}"))
            j = int(cand[pick])
        else:
            cand = np.where(~purchased)[0]
            if len(cand) == 0:
                break
            mu_t = val_m[truth, cand]
            sd_t = val_s[truth, cand]
            a = mu_t[None, :] + sd_t[None, :] * Z_QUANT[:, None]              # (K, C)
            z = (a[:, None, :] - val_m[None, :, cand]) / val_s[None, :, cand]
            t = (-0.5 * np.minimum(z * z, 9.0) - np.log(val_s[None, :, cand])
                 - LOG_SQRT_2PI)                                              # (K, H, C)
            after = scores[None, :, None] + t
            true_after = after[:, truth, :]
            wrong_max = np.max(np.delete(after, truth, axis=1), axis=1)
            exp_margin = (Q_W[:, None] * (true_after - wrong_max)).sum(axis=0)
            pick = int(np.argmax(exp_margin))
            ties = np.where(exp_margin == exp_margin[pick])[0]
            if len(ties) > 1:
                pick = min(ties, key=lambda jj: sha(f"{KEY}|ol|{int(cand[jj])}"))
            j = int(cand[pick])
        purchased[j] = True
        measurements += 1
        col = T[:, j]
        if not np.isfinite(col[0]):
            top = int(np.argmax(scores))
            rest = np.delete(scores, top)
            traj.append((float(scores[top] - rest.max()), top, measurements, True))
            continue
        scores = scores + col
        top = int(np.argmax(scores))
        rest = np.delete(scores, top)
        traj.append((float(scores[top] - rest.max()), top, measurements, False))
    return traj


# ------------------------------------------------------------------ calibration
def _select_from_table(table, rule):
    """rule 'emp': v5 point-estimate screening; rule 'ucb': strict CP-bound rule."""
    qualifying = []
    for tau, t in table.items():
        if t["decided"] < qualify2.TAU_MIN_DECIDED:
            continue
        if rule == "emp" and t["rate"] is not None and t["rate"] <= qualify2.TAU_MAX_WRONG:
            qualifying.append(tau)
        if rule == "ucb" and t["ucb"] is not None and t["ucb"] <= qualify2.TAU_MAX_WRONG:
            qualifying.append(tau)
    return min(qualifying) if qualifying else float("inf")


def _tau_table(episodes):
    table = {}
    for tau in TAU_GRID:
        dec = wrong = 0
        for traj, truth in episodes:
            out = qualify2.outcome_at_tau(traj, truth, tau)
            if out["decided"]:
                dec += 1
                wrong += not out["correct"]
        table[tau] = {"decided": dec, "wrong": wrong,
                      "rate": (wrong / dec) if dec else None,
                      "ucb": cp_ucb(wrong, dec)}
    return table


def calibrate_planner_arm(blend, rule, train, labels, idx, classes, auc, pool_arr,
                          half_of, rank, weight, genetic_ctx):
    """Split-half calibration trajectories for one realistic arm (world5b world)."""
    calib = []
    for h in (0, 1):
        templ_src = [c for c in train if half_of[c] == h]
        eps_for = [c for c in train if half_of[c] != h]
        mh, shh, vh, mph, sph = qualify2.build_templates_v2(
            auc, [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                  for ci in range(len(classes))])
        val_mh = np.where(vh, mh, mph[None, :])[:, pool_arr]
        val_sh = np.where(vh, shh, sph[None, :])[:, pool_arr]
        src_pos = np.array([idx[c] for c in templ_src])
        center_h, V_h, tau2_h = world5b.fit_basis(auc[src_pos][:, pool_arr], rank)
        gen_h = genetic_ctx(src_pos) if genetic_ctx else None
        for c in eps_for:
            x = idx[c]
            truth = labels[x]
            rng = np.random.default_rng(int(sha(f"{KEY}|calib|{blend}|{rule}|{c}")[:16], 16))
            world = world5b.LearnedWorld(center_h, V_h, tau2_h, val_mh, val_sh,
                                         blend_mode=blend, blend_w=weight)
            traj, _, _ = run5.run_planner_v5(world, val_mh, val_sh, auc[x, pool_arr],
                                             rule, rng, genetic=gen_h)
            calib.append((traj, truth))
    table = _tau_table(calib)
    return _select_from_table(table, "emp"), _select_from_table(table, "ucb"), table


def calibrate_oracle_arm(mode, train, labels, idx, classes, auc, pool_arr, half_of):
    """Split-half calibration trajectories for one decomposed ceiling arm."""
    calib = []
    for h in (0, 1):
        templ_src = [c for c in train if half_of[c] == h]
        eps_for = [c for c in train if half_of[c] != h]
        mh, shh, vh, mph, sph = qualify2.build_templates_v2(
            auc, [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                  for ci in range(len(classes))])
        val_mh = np.where(vh, mh, mph[None, :])[:, pool_arr]
        val_sh = np.where(vh, shh, sph[None, :])[:, pool_arr]
        for c in eps_for:
            x = idx[c]
            truth = labels[x]
            T = qualify2.term_matrix(auc[x], mh, shh, vh, mph, sph, pool_arr)
            calib.append((run_oracle_episode(mode, truth, T, val_mh, val_sh), truth))
    table = _tau_table(calib)
    return _select_from_table(table, "emp"), _select_from_table(table, "ucb"), table


def main():
    pack = prepare.load_pack()
    gen = prepare5.load_genetic()
    auc, compounds, lines = pack["auc"], pack["compounds"], pack["lines"]
    meta, folds, menu = pack["meta"], pack["folds"], pack["menu"]
    classes = menu["classes"]
    class_index = {c: i for i, c in enumerate(classes)}
    idx = pack["index"]
    line_index = pack["line_index"]
    labels = np.full(len(compounds), -1)
    for c in compounds:
        lab = meta.loc[c, "moa_main"]
        if lab in class_index:
            labels[idx[c]] = class_index[lab]
    pool = [line_index[l] for l in menu["pool_lines"] if l in line_index]
    pool_arr = np.asarray(pool)
    units_arr = meta["unit"].to_numpy()

    pos_to_deprow = {int(p): i for i, p in enumerate(gen["pool_pos"])}
    gene_idx = {g: j for j, g in enumerate(gen["genes"])}
    class_gene = gen["class_gene"]

    def genetic_ctx(src_pos):
        """Per-fold (or half) genetic channel, inherited unchanged from v5 (frozen fit)."""
        kept = {}
        gene_of_class = {}
        for ci, cname in enumerate(classes):
            g = class_gene.get(cname)
            gene_of_class[ci] = g if g in gene_idx else None
            if gene_of_class[ci] is None:
                continue
            members = [p for p in src_pos if labels[p] == ci]
            fit = world5b.fit_genetic(auc, gen["dep"], gen["pool_pos"], members,
                                      gene_idx[gene_of_class[ci]])
            if fit is not None and fit[3] > 0.0:
                kept[ci] = (fit[0], fit[1], fit[2])
        return {"kept": kept, "gene_of_class": gene_of_class, "gene_idx": gene_idx,
                "dep": gen["dep"], "dep_med": gen["dep_med"], "dep_mad": gen["dep_mad"],
                "pos_to_deprow": pos_to_deprow}

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
        med, scale, valid, med_p, scale_p = qualify2.build_templates_v2(auc, train_by_class)
        base_m = np.where(valid, med, med_p[None, :])
        base_s = np.where(valid, scale, scale_p[None, :])
        val_m = base_m[:, pool_arr]
        val_s = base_s[:, pool_arr]
        rank, rank_ll = world5b.select_rank(auc, train_by_class, train_pos,
                                            base_m[:, pool_arr], base_s[:, pool_arr],
                                            pool_arr, KEY, units_arr)
        center, V, tau2 = world5b.fit_basis(auc[train_pos][:, pool_arr], rank)
        weight, weight_ll = world5b.select_weight(auc, train_by_class,
                                                  base_m[:, pool_arr], base_s[:, pool_arr],
                                                  pool_arr, KEY, units_arr, center, V, tau2)

        # unconditional genetic channel report (frozen fit, documented baseline flaw)
        gctx_full = genetic_ctx(train_pos)
        gen_report = {}
        for ci, cname in enumerate(classes):
            g = gctx_full["gene_of_class"].get(ci)
            if g is None:
                continue
            members = [p for p in train_pos if labels[p] == ci]
            fit = world5b.fit_genetic(auc, gen["dep"], gen["pool_pos"], members, gene_idx[g])
            if fit is not None:
                gen_report[cname] = {"gene": g, "beta": fit[1], "delta_ll": fit[3],
                                     "n_pairs": fit[4], "kept": ci in gctx_full["kept"]}

        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half_of = {c: int(sha(f"{HALF_KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}

        # calibration per arm
        tau_emp, tau_ucb, tau_tables = {}, {}, {}
        for arm in REALISTIC:
            if arm == "planner_off_mi":
                blend, rule = "off", "mi"
            else:
                _, blend, rule = arm.split("_", 2)
            tau_emp[arm], tau_ucb[arm], tau_tables[arm] = calibrate_planner_arm(
                blend, rule, train, labels, idx, classes, auc, pool_arr, half_of,
                rank, weight, None)
        for mode in ORACLE_ARMS:
            short = mode.replace("oracle_", "")
            tau_emp[mode], tau_ucb[mode], tau_tables[mode] = calibrate_oracle_arm(
                short, train, labels, idx, classes, auc, pool_arr, half_of)

        # gated phase G5: folds with at least one finite realistic tau_emp
        g5_active = any(np.isfinite(tau_emp[a]) for a in REALISTIC)
        if g5_active:
            arm = "planner_holdout_mi_genetic"
            tau_emp[arm], tau_ucb[arm], tau_tables[arm] = calibrate_planner_arm(
                "holdout", "mi", train, labels, idx, classes, auc, pool_arr, half_of,
                rank, weight, genetic_ctx)

        # held-out episodes
        rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
        heldout_pos = np.array([idx[c] for c in heldout])
        shuffled_cols = {lj: rng.permutation(auc[heldout_pos, lj]) for lj in pool}
        mask_perm = rng.permutation(len(heldout))
        for i_held, c in enumerate(heldout):
            x = idx[c]
            truth = labels[x]
            if truth < 0:
                continue
            unit = str(meta.loc[c, "unit"])
            readings = auc[x, pool_arr]
            masked = heldout[mask_perm[i_held]]
            masked_readings = auc[idx[masked], pool_arr]
            shuffled_row = np.full(len(lines), np.nan)
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][i_held]
            shuf_readings = shuffled_row[pool_arr]
            for arm in REALISTIC:
                if arm == "planner_off_mi":
                    blend, rule = "off", "mi"
                else:
                    _, blend, rule = arm.split("_", 2)
                variants = ((arm, readings, readings),
                            (f"{arm}_masked", readings, masked_readings),
                            (f"{arm}_shuffled", shuf_readings, shuf_readings))
                for name, real, prof_in in variants:
                    erng = np.random.default_rng(int(sha(f"{KEY}|{name}|{c}")[:16], 16))
                    world = world5b.LearnedWorld(center, V, tau2, val_m, val_s,
                                                 blend_mode=blend, blend_w=weight)
                    traj, tops, n_gen = run5.run_planner_v5(world, val_m, val_s, real,
                                                            rule, erng,
                                                            profile_readings=prof_in)
                    out = qualify2.outcome_at_tau(traj, truth, tau_emp[arm])
                    out_u = qualify2.outcome_at_tau(traj, truth, tau_ucb[arm])
                    out["forecast_wrong_at_decision"] = (tops[out["measurements"] - 1]
                                                         if out["decided"] and out["measurements"]
                                                         else None)
                    rows.append({"fold": f, "compound": c, "unit": unit,
                                 "class": classes[truth], "arm": name,
                                 "tau": tau_emp[arm], "tau_ucb": tau_ucb[arm],
                                 "genetic_purchases": n_gen,
                                 "ucb_decided": out_u["decided"],
                                 "ucb_correct": out_u["correct"], **out})
            # decomposed ceilings on the full-fold term matrix
            T = qualify2.term_matrix(auc[x], med, scale, valid, med_p, scale_p, pool_arr)
            for mode in ORACLE_ARMS:
                short = mode.replace("oracle_", "")
                traj = run_oracle_episode(short, truth, T, val_m, val_s)
                out = qualify2.outcome_at_tau(traj, truth, tau_emp[mode])
                out_u = qualify2.outcome_at_tau(traj, truth, tau_ucb[mode])
                rows.append({"fold": f, "compound": c, "unit": unit,
                             "class": classes[truth], "arm": mode,
                             "tau": tau_emp[mode], "tau_ucb": tau_ucb[mode],
                             "genetic_purchases": 0,
                             "ucb_decided": out_u["decided"],
                             "ucb_correct": out_u["correct"], **out})
            if g5_active:
                arm = "planner_holdout_mi_genetic"
                for name, prof_in in ((arm, readings), (f"{arm}_masked", masked_readings)):
                    erng = np.random.default_rng(int(sha(f"{KEY}|{name}|{c}")[:16], 16))
                    world = world5b.LearnedWorld(center, V, tau2, val_m, val_s,
                                                 blend_mode="holdout", blend_w=weight)
                    traj, tops, n_gen = run5.run_planner_v5(world, val_m, val_s, readings,
                                                            "mi", erng,
                                                            profile_readings=prof_in,
                                                            genetic=gctx_full)
                    out = qualify2.outcome_at_tau(traj, truth, tau_emp[arm])
                    out_u = qualify2.outcome_at_tau(traj, truth, tau_ucb[arm])
                    rows.append({"fold": f, "compound": c, "unit": unit,
                                 "class": classes[truth], "arm": name,
                                 "tau": tau_emp[arm], "tau_ucb": tau_ucb[arm],
                                 "genetic_purchases": n_gen,
                                 "ucb_decided": out_u["decided"],
                                 "ucb_correct": out_u["correct"], **out})
        world_fit[f] = {"rank": rank, "rank_ll": {str(k): v for k, v in rank_ll.items()},
                        "weight": weight,
                        "weight_ll": {str(k): v for k, v in weight_ll.items()},
                        "tau_emp": {a: (None if np.isinf(t) else t)
                                    for a, t in tau_emp.items()},
                        "tau_ucb": {a: (None if np.isinf(t) else t)
                                    for a, t in tau_ucb.items()},
                        "tau_table": {a: {str(k): v for k, v in tb.items()}
                                      for a, tb in tau_tables.items()},
                        "g5_active": bool(g5_active),
                        "genetic_channel": gen_report}

    ep_new = pd.DataFrame(rows)
    ep5 = pd.read_csv(RUN5 / "episodes.csv")
    imported = ep5[ep5["arm"].isin(IMPORTED_ARMS)]
    ep = pd.concat([imported, ep_new], ignore_index=True)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = qualify.summarise(ep)
    summary["folds"] = world_fit
    summary["budget"] = BUDGET
    summary["episodes"] = int((ep["arm"] == "oracle").sum())
    summary["classes"] = len(classes)
    summary["units"] = int(ep["unit"].nunique())
    arms = summary["arms"]
    realistic_present = [a for a in REALISTIC if a in arms]
    best = max(realistic_present, key=lambda a: arms[a]["correct"]) if realistic_present else None
    summary["best_realistic"] = best
    summary["contrasts"] = {}
    for a in realistic_present:
        summary["contrasts"][f"{a}_minus_reference"] = (
            arms[a]["correct"] - arms["planner_reference"]["correct"])
        if f"{a}_masked" in arms:
            summary["contrasts"][f"{a}_minus_masked"] = (
                arms[a]["correct"] - arms[f"{a}_masked"]["correct"])
    summary["contrasts"]["holdout_mi_minus_off_mi"] = (
        arms["planner_holdout_mi"]["correct"] - arms["planner_off_mi"]["correct"])
    summary["contrasts"]["holdout_mi_minus_precision_mi"] = (
        arms["planner_holdout_mi"]["correct"] - arms["planner_precision_mi"]["correct"])
    summary["contrasts"]["mi_minus_margin_holdout"] = (
        arms["planner_holdout_mi"]["correct"] - arms["planner_holdout_margin"]["correct"])
    summary["contrasts"]["oracle_reading_minus_best"] = (
        arms["oracle_reading"]["correct"] - arms[best]["correct"])
    summary["contrasts"]["oracle_full_minus_reading"] = (
        arms["oracle"]["correct"] - arms["oracle_reading"]["correct"])
    summary["contrasts"]["oracle_full_minus_label"] = (
        arms["oracle"]["correct"] - arms["oracle_label"]["correct"])
    summary["contrasts"]["oracle_reading_minus_label"] = (
        arms["oracle_reading"]["correct"] - arms["oracle_label"]["correct"])
    if "planner_holdout_mi_genetic" in arms:
        g = arms["planner_holdout_mi_genetic"]
        summary["contrasts"]["genetic_minus_mi"] = (
            g["correct"] - arms["planner_holdout_mi"]["correct"])
        sub = ep[ep["arm"] == "planner_holdout_mi_genetic"]
        summary["genetic_purchase_rate"] = float((sub["genetic_purchases"] > 0).mean())
        summary["genetic_purchases_mean"] = float(sub["genetic_purchases"].mean())
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT / "world_fit.json").write_text(json.dumps(world_fit, indent=1), encoding="utf-8")
    gate = evaluate_gate_v5b(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "best_realistic": best,
                      "contrasts": summary["contrasts"],
                      "tau_emp": {f: i["tau_emp"] for f, i in world_fit.items()},
                      "weights": {f: i["weight"] for f, i in world_fit.items()},
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in arms.items()}}, indent=1))


def evaluate_gate_v5b(summary: dict) -> dict:
    arms = summary["arms"]
    best = summary["best_realistic"]
    finite = [a for a in REALISTIC
              if any(f["tau_emp"].get(a) is not None for f in summary["folds"].values())]
    checks = {
        "any_realistic_finite_tau_emp": len(finite) > 0,
        "oracle_reading_gt_best_realistic": (
            summary["contrasts"]["oracle_reading_minus_best"] > 0 if best else False),
        "shuffled_coverage_le_0.10": all(
            arms[f"{a}_shuffled"]["coverage"] <= 0.10
            for a in REALISTIC if f"{a}_shuffled" in arms),
    }
    return {"checks": checks, "finite_tau_emp_arms": finite,
            "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
