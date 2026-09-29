"""Dual-core run v5: learned world x non-margin acquisition x gated genetic tier.

File summary
- Path: research/viability_contrast/run5.py
- Purpose: protocol viability-contrast-5. Three acquisition rules (margin = v4 control,
  mi = expected class-entropy reduction, thompson = sampled-class margin) on the SAME
  world5 learned-completion channel, each with masked and shuffled controls; per-arm tau
  calibration on training-fold split halves over the extended tau grid; the phase-G5
  genetic tier runs per fold only when a realistic arm reaches a finite tau in that
  fold's calibration (protocol5.json). Every non-v5 arm is imported unchanged from the
  frozen v3/v4 outputs. The genetic channel fit is computed and reported unconditionally.
- Interfaces / data: reads the frozen pack, prepare5.load_genetic() and run4's
  episodes.csv; writes outputs/viability_contrast_20260928/run5/{episodes.csv,
  summary.json, gate.json, world_fit.json}.
- Depends on: research/viability_contrast/{protocol5.json, prepare.py, prepare5.py,
  qualify.py, qualify2.py, run4.py, world5.py}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, prepare5, qualify, qualify2, world5

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/run5"
RUN4 = ROOT / "outputs/viability_contrast_20260928/run4"
KEY = "viability-contrast-5"
BUDGET = 16
TOP_H = 8
TAU_GRID5 = (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0)
GENETIC_TOP_LINES = 20
RULES = ("margin", "mi", "thompson")
Z_QUANT = np.array([-2.0, -1.33, -0.67, 0.0, 0.67, 1.33, 2.0])
Q_W = np.exp(-0.5 * Z_QUANT**2)
Q_W = Q_W / Q_W.sum()
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)
IMPORTED_ARMS = ["oracle", "planner_reference", "fixed_informative", "random",
                 "planner_shuffled", "planner_profile", "planner_profile_masked",
                 "planner_profile_shuffled"]
REALISTIC = [f"planner_learned_{r}" for r in RULES]


def sha(text: str) -> str:
    return qualify2.sha(text)


# ------------------------------------------------------------------ acquisition
def _softmax_top(scores):
    w = np.exp(scores - scores.max())
    w /= w.sum()
    top_idx = np.argsort(-w)[:TOP_H]
    w_top = w[top_idx] / w[top_idx].sum()
    return w, top_idx, w_top


def _margin_pick(wm, ws, scores, top_idx, w_top, cand, val_m, val_s):
    """The v4 greedy expected-margin rule, ported unchanged (Goodhart control)."""
    mu = wm[top_idx][:, cand]
    sd = ws[top_idx][:, cand]
    a = mu[:, None, None, :] + sd[:, None, None, :] * Z_QUANT[None, :, None, None]
    z = (a - val_m[None, None, :, cand]) / val_s[None, None, :, cand]
    t = -0.5 * np.minimum(z * z, 9.0) - np.log(val_s[None, None, :, cand]) - LOG_SQRT_2PI
    after = scores[None, None, :, None] + t
    part = np.partition(after, -2, axis=2)
    margin = part[:, :, -1, :] - part[:, :, -2, :]
    w_hk = (w_top[:, None] * Q_W[None, :])[:, :, None]
    exp_margin = (margin * w_hk).sum(axis=(0, 1))
    return int(cand[int(np.argmax(exp_margin))])


def _mi_values(mu, sd, w_top):
    """Expected class-entropy reduction per candidate column of (mu, sd): (H, C)."""
    a = mu[:, None, :] + sd[:, None, :] * Z_QUANT[None, :, None]      # (H, K, C)
    lp = (np.log(w_top)[:, None, None, None]
          - 0.5 * ((a[:, :, None, :] - mu[None, None, :, :]) / sd[None, None, :, :]) ** 2
          - np.log(sd[None, None, :, :]))                            # (H, K, H, C)
    lp = lp - lp.max(axis=2, keepdims=True)
    p = np.exp(lp)
    p /= p.sum(axis=2, keepdims=True)
    ent = -(p * np.log(np.maximum(p, 1e-300))).sum(axis=2)           # (H, K, C)
    w_hk = (w_top[:, None] * Q_W[None, :])[:, :, None]
    cond = (ent * w_hk).sum(axis=(0, 1))
    h0 = -(w_top * np.log(np.maximum(w_top, 1e-300))).sum()
    return h0 - cond


def _mi_pick(wm, ws, top_idx, w_top, cand):
    mu = wm[top_idx][:, cand]
    sd = ws[top_idx][:, cand]
    mi = _mi_values(mu, sd, w_top)
    return int(cand[int(np.argmax(mi))]), mi


def _thompson_pick(wm, ws, scores, w, cand, val_m, val_s, rng):
    chat = int(rng.choice(len(w), p=w))
    mu = wm[chat, cand]
    sd = ws[chat, cand]
    a = mu[None, :] + sd[None, :] * Z_QUANT[:, None]
    z = (a[:, None, :] - val_m[None, :, cand]) / val_s[None, :, cand]
    t = -0.5 * np.minimum(z * z, 9.0) - np.log(val_s[None, :, cand]) - LOG_SQRT_2PI
    after = scores[None, :, None] + t
    rest_max = np.max(np.delete(after, chat, axis=1), axis=1)
    margin = after[:, chat, :] - rest_max
    exp_margin = (margin * Q_W[:, None]).sum(axis=0)
    return int(cand[int(np.argmax(exp_margin))])


# ------------------------------------------------------------------ genetic tier
def _blend_at(world, j, gen_override=None):
    """Blended (mu, sd) over classes at pool position j, with optional extra genetic
    overrides {class_index: (mean, var)} applied on top of the world's state."""
    bm = world.base_mean[:, j].copy()
    bv = world.base_scale[:, j] ** 2
    gm = world.gen_mean[:, j]
    gv = world.gen_var[:, j]
    has = np.isfinite(gm)
    bm[has] = gm[has]
    bv[has] = gv[has]
    if gen_override:
        for ci, (m, v) in gen_override.items():
            bm[ci] = m
            bv[ci] = max(v, world5.MIN_VAR)
    if world.p_mean is None:
        return bm, np.sqrt(bv)
    pv = world.p_var[j]
    pm = world.p_mean[j]
    prec = 1.0 / bv + 1.0 / pv
    return (bm / bv + pm / pv) / prec, np.sqrt(1.0 / prec)


def _genetic_pick(world, top_idx, w_top, cand, mi, cand_pos, genetic, purchased_dep):
    """One-step value-of-information score for genetic actions (protocol5.json G5).

    Returns (action, score) with action = (pool_position, gene) or (None, 0.0). Only the
    top GENETIC_TOP_LINES candidates by viability MI and top-H classes with a kept
    genetic model form the menu.
    """
    if genetic is None or len(cand) == 0:
        return (None, None), 0.0
    order = np.argsort(-mi)[:GENETIC_TOP_LINES]
    best = None
    best_score = 0.0
    mi_star = float(mi[order[0]])
    for oi in order:
        j = int(cand[oi])
        if j not in genetic["pos_to_deprow"]:
            continue
        row = genetic["pos_to_deprow"][j]
        for ci in top_idx:
            gene = genetic["gene_of_class"].get(int(ci))
            if gene is None or int(ci) not in genetic["kept"] or (j, gene) in purchased_dep:
                continue
            alpha, beta, sigma2 = genetic["kept"][int(ci)]
            gi = genetic["gene_idx"][gene]
            dm, dd = genetic["dep_med"][gi], genetic["dep_mad"][gi]
            d_q = dm + dd * Z_QUANT
            vals = []
            for d in d_q:
                mu_j, sd_j = _blend_at(world, j, {int(ci): (alpha + beta * d, sigma2)})
                mi_j = _mi_values(mu_j[top_idx][:, None], sd_j[top_idx][:, None], w_top)[0]
                vals.append(max(float(mi_j), mi_star))
            score = float(np.dot(vals, Q_W)) - mi_star
            if score > best_score:
                best_score = score
                best = (j, gene)
    return (best if best is not None else (None, None)), best_score


# ------------------------------------------------------------------ planner
def run_planner_v5(world, val_m, val_s, readings, rule, rng, profile_readings=None,
                   genetic=None, budget=BUDGET):
    """The planner skeleton (v3/v4) with a v5 world and a rule from RULES.

    genetic: None or the per-fold genetic context (phase G5 arms; rule must be "mi").
    Returns (trajectory, forecast_wrong_per_step, genetic_purchases).
    """
    if profile_readings is None:
        profile_readings = readings
    n_pool = len(readings)
    n_classes = val_m.shape[0]
    scores = np.zeros(n_classes)
    purchased = np.zeros(n_pool, dtype=bool)
    purchased_dep = set()
    traj = []
    tops = []
    measurements = 0
    n_genetic = 0
    while measurements < budget:
        wm, ws = world.mean_scale()
        w, top_idx, w_top = _softmax_top(scores)
        cand = np.where(~purchased)[0]
        if rule == "margin":
            j = _margin_pick(wm, ws, scores, top_idx, w_top, cand, val_m, val_s)
        elif rule == "mi":
            j, _ = _mi_pick(wm, ws, top_idx, w_top, cand)
        else:
            j = _thompson_pick(wm, ws, scores, w, cand, val_m, val_s, rng)
        if genetic is not None:
            _, mi = _mi_pick(wm, ws, top_idx, w_top, cand)
            (gj, gene), gscore = _genetic_pick(world, top_idx, w_top, cand, mi,
                                               None, genetic, purchased_dep)
            if gj is not None and gscore > 0.0 and gscore > float(mi.max()):
                row = genetic["pos_to_deprow"][gj]
                d = genetic["dep"][row, genetic["gene_idx"][gene]]
                for ci, g in genetic["gene_of_class"].items():
                    if g == gene and ci in genetic["kept"]:
                        alpha, beta, sigma2 = genetic["kept"][ci]
                        world.reveal_genetic(ci, gj, alpha + beta * d, sigma2)
                purchased_dep.add((gj, gene))
                measurements += 1
                n_genetic += 1
                top = int(np.argmax(scores))
                rest = np.delete(scores, top)
                traj.append((float(scores[top] - rest.max()), top, measurements, False))
                wb = np.exp(scores - scores.max())
                tops.append(float(1.0 - (wb / wb.sum()).max()))
                continue
        purchased[j] = True
        measurements += 1
        pos = np.where(purchased)[0]
        world.update(profile_readings[pos], pos)
        a_real = readings[j]
        if not np.isfinite(a_real):
            top = int(np.argmax(scores))
            rest = np.delete(scores, top)
            traj.append((float(scores[top] - rest.max()), top, measurements, True))
            tops.append(float(1.0 - w.max()))
            continue
        zr = (a_real - val_m[:, j]) / val_s[:, j]
        tr = -0.5 * np.minimum(zr * zr, 9.0) - np.log(val_s[:, j]) - LOG_SQRT_2PI
        scores = scores + tr
        top = int(np.argmax(scores))
        rest = np.delete(scores, top)
        traj.append((float(scores[top] - rest.max()), top, measurements, False))
        wb = np.exp(scores - scores.max())
        tops.append(float(1.0 - (wb / wb.sum()).max()))
    return traj, tops, n_genetic


def make_world(center, V, tau2, val_m, val_s):
    return world5.LearnedWorld(center, V, tau2, val_m, val_s)


def calibrate_arm(rule, basis_full, train, labels, idx, classes, auc, pool_arr,
                  half_of, units_arr, rank, genetic_ctx):
    """Split-half calibration trajectories for one realistic arm."""
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
        center_h, V_h, tau2_h = world5.fit_basis(auc[src_pos][:, pool_arr], rank)
        gen_h = genetic_ctx(src_pos) if genetic_ctx else None
        for c in eps_for:
            x = idx[c]
            truth = labels[x]
            rng = np.random.default_rng(int(sha(f"{KEY}|calib|{rule}|{c}")[:16], 16))
            world = make_world(center_h, V_h, tau2_h, val_mh, val_sh)
            traj, _, _ = run_planner_v5(world, val_mh, val_sh, auc[x, pool_arr], rule,
                                        rng, genetic=gen_h)
            calib.append((traj, truth))
    table = {}
    for tau in TAU_GRID5:
        dec = wrong = 0
        for traj, truth in calib:
            out = qualify2.outcome_at_tau(traj, truth, tau)
            if out["decided"]:
                dec += 1
                wrong += not out["correct"]
        table[tau] = {"decided": dec, "wrong": wrong, "rate": (wrong / dec) if dec else None}
    qualifying = [tau for tau, t in table.items()
                  if t["decided"] >= qualify2.TAU_MIN_DECIDED and t["rate"] is not None
                  and t["rate"] <= qualify2.TAU_MAX_WRONG]
    return (min(qualifying) if qualifying else float("inf")), table


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
        """Per-fold (or half) genetic channel: per-class OLS kept if it helps."""
        kept = {}
        gene_of_class = {}
        for ci, cname in enumerate(classes):
            g = class_gene.get(cname)
            gene_of_class[ci] = g if g in gene_idx else None
            if gene_of_class[ci] is None:
                continue
            members = [p for p in src_pos if labels[p] == ci]
            fit = world5.fit_genetic(auc, gen["dep"], gen["pool_pos"], members,
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
        rank, rank_ll = world5.select_rank(auc, train_by_class, train_pos, base_m[:, pool_arr],
                                           base_s[:, pool_arr], pool_arr, KEY, units_arr)
        center, V, tau2 = world5.fit_basis(auc[train_pos][:, pool_arr], rank)

        # unconditional genetic channel report (fit on the full training fold)
        gctx_full = genetic_ctx(train_pos)
        gen_report = {}
        for ci, cname in enumerate(classes):
            g = gctx_full["gene_of_class"].get(ci)
            if g is None:
                continue
            members = [p for p in train_pos if labels[p] == ci]
            fit = world5.fit_genetic(auc, gen["dep"], gen["pool_pos"], members,
                                     gene_idx[g])
            if fit is not None:
                gen_report[cname] = {"gene": g, "beta": fit[1], "delta_ll": fit[3],
                                     "n_pairs": fit[4], "kept": ci in gctx_full["kept"]}

        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half_of = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}

        # calibration per realistic arm
        tau_of, tau_tables = {}, {}
        for rule in RULES:
            arm = f"planner_learned_{rule}"
            tau_of[arm], tau_tables[arm] = calibrate_arm(
                rule, None, train, labels, idx, classes, auc, pool_arr, half_of,
                units_arr, rank, None)
        # gated phase G5: folds with at least one finite realistic tau
        g5_active = any(np.isfinite(t) for t in tau_of.values())
        if g5_active:
            tau_of["planner_learned_mi_genetic"], tau_tables["planner_learned_mi_genetic"] = \
                calibrate_arm("mi", None, train, labels, idx, classes, auc, pool_arr,
                              half_of, units_arr, rank, genetic_ctx)

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
            for rule in RULES:
                arm = f"planner_learned_{rule}"
                variants = ((arm, readings, readings),
                            (f"{arm}_masked", readings, masked_readings),
                            (f"{arm}_shuffled", shuf_readings, shuf_readings))
                for name, real, prof_in in variants:
                    erng = np.random.default_rng(int(sha(f"{KEY}|{name}|{c}")[:16], 16))
                    world = make_world(center, V, tau2, val_m, val_s)
                    traj, tops, n_gen = run_planner_v5(world, val_m, val_s, real, rule,
                                                       erng, profile_readings=prof_in)
                    out = qualify2.outcome_at_tau(traj, truth, tau_of[arm])
                    out["forecast_wrong_at_decision"] = (tops[out["measurements"] - 1]
                                                         if out["decided"] and out["measurements"]
                                                         else None)
                    rows.append({"fold": f, "compound": c, "unit": unit,
                                 "class": classes[truth], "arm": name, "tau": tau_of[arm],
                                 "genetic_purchases": n_gen, **out})
            if g5_active:
                arm = "planner_learned_mi_genetic"
                for name, prof_in in ((arm, readings), (f"{arm}_masked", masked_readings)):
                    erng = np.random.default_rng(int(sha(f"{KEY}|{name}|{c}")[:16], 16))
                    world = make_world(center, V, tau2, val_m, val_s)
                    traj, tops, n_gen = run_planner_v5(world, val_m, val_s, readings, "mi",
                                                       erng, profile_readings=prof_in,
                                                       genetic=gctx_full)
                    out = qualify2.outcome_at_tau(traj, truth, tau_of[arm])
                    out["forecast_wrong_at_decision"] = (tops[out["measurements"] - 1]
                                                         if out["decided"] and out["measurements"]
                                                         else None)
                    rows.append({"fold": f, "compound": c, "unit": unit,
                                 "class": classes[truth], "arm": name, "tau": tau_of[arm],
                                 "genetic_purchases": n_gen, **out})
        world_fit[f] = {"rank": rank, "rank_ll": {str(k): v for k, v in rank_ll.items()},
                        "tau": {a: (None if np.isinf(t) else t) for a, t in tau_of.items()},
                        "tau_table": {a: {str(k): v for k, v in tb.items()}
                                      for a, tb in tau_tables.items()},
                        "g5_active": bool(g5_active),
                        "genetic_channel": gen_report}

    ep_new = pd.DataFrame(rows)
    ep4 = pd.read_csv(RUN4 / "episodes.csv")
    imported = ep4[ep4["arm"].isin(IMPORTED_ARMS)]
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
    summary["contrasts"] = {
        f"{a}_minus_reference": arms[a]["correct"] - arms["planner_reference"]["correct"]
        for a in realistic_present
    }
    summary["contrasts"].update({
        f"{a}_minus_masked": arms[a]["correct"] - arms[f"{a}_masked"]["correct"]
        for a in realistic_present
    })
    summary["contrasts"]["mi_minus_margin"] = (
        arms["planner_learned_mi"]["correct"] - arms["planner_learned_margin"]["correct"])
    summary["contrasts"]["thompson_minus_margin"] = (
        arms["planner_learned_thompson"]["correct"] - arms["planner_learned_margin"]["correct"])
    summary["contrasts"]["oracle_minus_best"] = arms["oracle"]["correct"] - arms[best]["correct"]
    if "planner_learned_mi_genetic" in arms:
        g = arms["planner_learned_mi_genetic"]
        summary["contrasts"]["genetic_minus_mi"] = g["correct"] - arms["planner_learned_mi"]["correct"]
        sub = ep[ep["arm"] == "planner_learned_mi_genetic"]
        summary["genetic_purchase_rate"] = float((sub["genetic_purchases"] > 0).mean())
        summary["genetic_purchases_mean"] = float(sub["genetic_purchases"].mean())
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT / "world_fit.json").write_text(json.dumps(world_fit, indent=1), encoding="utf-8")
    gate = evaluate_gate_v5(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "best_realistic": best,
                      "contrasts": summary["contrasts"],
                      "tau": {f: i["tau"] for f, i in world_fit.items()},
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in arms.items()}}, indent=1))


def evaluate_gate_v5(summary: dict) -> dict:
    arms = summary["arms"]
    best = summary["best_realistic"]
    certifying = []
    for a in [x for x in arms if x in REALISTIC]:
        s = arms[a]
        finite_tau = any(t is not None for t in
                         (f["tau"].get(a) for f in summary["folds"].values()))
        if (finite_tau and s["conditional_wrong"] == s["conditional_wrong"]
                and s["conditional_wrong"] <= 0.05 and s["coverage"] >= 0.20):
            certifying.append(a)
    checks = {
        "any_realistic_certifies": len(certifying) > 0,
        "best_minus_reference_gt_0": (
            summary["contrasts"][f"{best}_minus_reference"] > 0 if best else False),
        "best_minus_masked_gt_0": (
            summary["contrasts"][f"{best}_minus_masked"] > 0 if best else False),
        "shuffled_coverage_le_0.10": all(
            arms[f"{a}_shuffled"]["coverage"] <= 0.10 for a in REALISTIC if f"{a}_shuffled" in arms),
    }
    return {"checks": checks, "certifying_arms": certifying,
            "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
