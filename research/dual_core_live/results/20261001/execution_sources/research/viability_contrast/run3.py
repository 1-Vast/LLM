"""Dual-core run for the viability-contrast task (protocol viability-contrast-3).

File summary
- Path: research/viability_contrast/run3.py
- Purpose: the dual-core grid. A world-model-guided greedy planner (agent) runs against the
  abstaining floor arms and the clairvoyant ceiling on identical episodes, menus, budgets and
  the v2 score-margin validator; the virtual cell enters through the planner's predictive
  (reference templates vs structural neighbour channel), with masked-structure and
  shuffled-reading controls. Per-arm tau is calibrated on training-fold split halves exactly
  as in v2. Reports coverage, conditional wrong, correct, the world-channel contrasts, and the
  decision-forecast calibration on the episodes each arm decided.
- Interfaces / data: reads the frozen pack via prepare.load_pack(); writes
  outputs/viability_contrast_20260928/run3/{episodes.csv, summary.json, gate.json, world_fit.json}.
- Depends on: research/viability_contrast/{protocol3.json, prepare.py, qualify.py, qualify2.py, world3.py}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify, qualify2, world3

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/run3"
KEY = "viability-contrast-3"
BUDGET = 16
TOP_H = 8
Z_QUANT = np.array([-2.0, -1.33, -0.67, 0.0, 0.67, 1.33, 2.0])
Q_W = np.exp(-0.5 * Z_QUANT**2)
Q_W = Q_W / Q_W.sum()
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)


def sha(text: str) -> str:
    return qualify2.sha(text)


# ------------------------------------------------------------------ planner
def run_planner(world_mean, world_scale, val_m, val_s, readings, budget=BUDGET):
    """Greedy expected-margin planner episode.

    world_mean/world_scale/val_m/val_s: (n_classes, n_pool); readings: (n_pool,) with NaN
    where the pair has no measured curve (a purchase there is a charged QC failure).
    Returns (trajectory, forecast_wrong_per_step); trajectory rows are
    (margin, top, measurements, qc) matching qualify2.outcome_at_tau.
    """
    n_pool = len(readings)
    n_classes = val_m.shape[0]
    scores = np.zeros(n_classes)
    purchased = np.zeros(n_pool, dtype=bool)
    traj = []
    tops = []
    measurements = 0
    while measurements < budget:
        w = np.exp(scores - scores.max())
        w /= w.sum()
        top_idx = np.argsort(-w)[:TOP_H]
        w_top = w[top_idx] / w[top_idx].sum()
        cand = np.where(~purchased)[0]
        mu = world_mean[top_idx][:, cand]
        sd = world_scale[top_idx][:, cand]
        a = mu[:, None, None, :] + sd[:, None, None, :] * Z_QUANT[None, :, None, None]
        z = (a - val_m[None, None, :, cand]) / val_s[None, None, :, cand]
        t = -0.5 * np.minimum(z * z, 9.0) - np.log(val_s[None, None, :, cand]) - LOG_SQRT_2PI
        after = scores[None, None, :, None] + t
        part = np.partition(after, -2, axis=2)
        margin = part[:, :, -1, :] - part[:, :, -2, :]
        w_hk = (w_top[:, None] * Q_W[None, :])[:, :, None]
        exp_margin = (margin * w_hk).sum(axis=(0, 1))
        j = int(cand[int(np.argmax(exp_margin))])
        purchased[j] = True
        measurements += 1
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
    return traj, tops


# ------------------------------------------------------------------ main
def main():
    pack = prepare.load_pack()
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
    pos_of_line = {lj: p for p, lj in enumerate(pool)}
    smiles = pd.read_csv(prepare.OUT / "smiles.csv").set_index("compound")["smiles"].to_dict()
    units_arr = meta["unit"].to_numpy()
    fps = world3.FingerprintCache({c: smiles[c] for c in compounds})

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
        val_m = np.where(valid, med, med_p[None, :])[:, pool_arr]
        val_s = np.where(valid, scale, scale_p[None, :])[:, pool_arr]
        fixed_full = qualify2.separation_order(med, scale, valid, pool, lines, "full")
        fixed_full_pos = [pos_of_line[l] for l in fixed_full]

        # structural channel on full training
        sims_train = np.stack([fps.similarity(c, train) for c in train])
        train_units = np.array([units_arr[p] for p in train_pos])
        NN_train = world3.neighbour_matrix(auc, train_pos, sims_train, train_units, train_units)
        lam = world3.fit_lambda(auc, train_by_class, train_pos, NN_train,
                                med, scale, valid, med_p, scale_p)

        # calibration split halves
        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}
        calib_traj = {a: [] for a in ("oracle", "fixed_informative", "random",
                                      "planner_reference", "planner_structural")}
        for h in (0, 1):
            templ_src = [c for c in train if half[c] == h]
            eps_for = [c for c in train if half[c] != h]
            mh, sh, vh, mph, sph = qualify2.build_templates_v2(
                auc, [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                      for ci in range(len(classes))])
            val_mh = np.where(vh, mh, mph[None, :])[:, pool_arr]
            val_sh = np.where(vh, sh, sph[None, :])[:, pool_arr]
            fixed_h = qualify2.separation_order(mh, sh, vh, pool, lines, f"half{h}")
            fixed_h_pos = [pos_of_line[l] for l in fixed_h]
            src_pos = np.array([idx[c] for c in templ_src])
            for c in eps_for:
                x = idx[c]
                truth = labels[x]
                T = qualify2.term_matrix(auc[x], mh, sh, vh, mph, sph, pool_arr)
                rng_order = list(range(len(pool)))
                np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
                for arm in ("oracle", "fixed_informative", "random"):
                    traj = qualify2.run_episode_v2(arm, truth, T, pool_arr, fixed_h_pos, rng_order)
                    calib_traj[arm].append((traj, truth))
                # planner arms under the half templates
                sim_x = fps.similarity(c, templ_src)
                src_units = np.array([units_arr[p] for p in src_pos])
                NN_x = world3.neighbour_matrix(auc, src_pos, sim_x[None, :],
                                               np.array([units_arr[x]]), src_units)
                ref_m, ref_s = val_mh, val_sh
                str_m = np.where(np.isfinite(NN_x[0])[None, :],
                                 (1 - lam) * ref_m + lam * NN_x[0][None, :], ref_m)
                readings = auc[x, pool_arr]
                traj, _ = run_planner(ref_m, ref_s, val_mh, val_sh, readings)
                calib_traj["planner_reference"].append((traj, truth))
                traj, _ = run_planner(str_m, ref_s, val_mh, val_sh, readings)
                calib_traj["planner_structural"].append((traj, truth))

        tau_of = {}
        tau_table = {}
        for arm, episodes in calib_traj.items():
            table = {}
            for tau in qualify2.TAU_GRID:
                dec = wrong = 0
                for traj, truth in episodes:
                    out = qualify2.outcome_at_tau(traj, truth, tau)
                    if out["decided"]:
                        dec += 1
                        wrong += not out["correct"]
                table[tau] = {"decided": dec, "wrong": wrong,
                              "rate": (wrong / dec) if dec else None}
            qualifying = [tau for tau, t in table.items()
                          if t["decided"] >= qualify2.TAU_MIN_DECIDED and t["rate"] is not None
                          and t["rate"] <= qualify2.TAU_MAX_WRONG]
            tau_of[arm] = min(qualifying) if qualifying else float("inf")
            tau_table[arm] = {str(k): v for k, v in table.items()}
        tau_of["planner_masked"] = tau_of["planner_structural"]
        tau_of["planner_shuffled"] = tau_of["planner_reference"]

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
            T = qualify2.term_matrix(auc[x], med, scale, valid, med_p, scale_p, pool_arr)
            rng_order = list(range(len(pool)))
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
            for arm in ("oracle", "fixed_informative", "random"):
                traj = qualify2.run_episode_v2(arm, truth, T, pool_arr, fixed_full_pos, rng_order)
                out = qualify2.outcome_at_tau(traj, truth, tau_of[arm])
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, "tau": tau_of[arm], **out})
            # planner arms
            sim_x = fps.similarity(c, train)
            NN_x = world3.neighbour_matrix(auc, train_pos, sim_x[None, :],
                                           np.array([units_arr[x]]), train_units)
            ref_m, ref_s = val_m, val_s
            str_m = np.where(np.isfinite(NN_x[0])[None, :],
                             (1 - lam) * ref_m + lam * NN_x[0][None, :], ref_m)
            masked_compound = heldout[mask_perm[i_held]]
            sim_m = fps.similarity(masked_compound, train)
            NN_m = world3.neighbour_matrix(auc, train_pos, sim_m[None, :],
                                           np.array([units_arr[idx[masked_compound]]]), train_units)
            msk_m = np.where(np.isfinite(NN_m[0])[None, :],
                             (1 - lam) * ref_m + lam * NN_m[0][None, :], ref_m)
            readings = auc[x, pool_arr]
            for arm, wm in (("planner_reference", ref_m), ("planner_structural", str_m),
                            ("planner_masked", msk_m)):
                traj, tops = run_planner(wm, ref_s, val_m, val_s, readings)
                out = qualify2.outcome_at_tau(traj, truth, tau_of[arm])
                out["forecast_wrong_at_decision"] = (tops[out["measurements"] - 1]
                                                     if out["decided"] and out["measurements"] else None)
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, "tau": tau_of[arm], **out})
            # shuffled readings with the reference world
            shuffled_row = np.full(len(lines), np.nan)
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][i_held]
            traj, tops = run_planner(ref_m, ref_s, val_m, val_s, shuffled_row[pool_arr])
            out = qualify2.outcome_at_tau(traj, truth, tau_of["planner_shuffled"])
            rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                         "arm": "planner_shuffled", "tau": tau_of["planner_shuffled"], **out})
        world_fit[f] = {"lambda": lam, "tau": {a: (None if np.isinf(t) else t)
                                               for a, t in tau_of.items()},
                        "tau_table": tau_table}

    ep = pd.DataFrame(rows)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = qualify.summarise(ep)
    summary["folds"] = world_fit
    summary["budget"] = BUDGET
    summary["episodes"] = int((ep["arm"] == "oracle").sum())
    summary["classes"] = len(classes)
    summary["units"] = int(ep["unit"].nunique())
    # world-channel contrasts
    arms = summary["arms"]
    summary["contrasts"] = {
        "structural_minus_reference": arms["planner_structural"]["correct"] - arms["planner_reference"]["correct"],
        "structural_minus_masked": arms["planner_structural"]["correct"] - arms["planner_masked"]["correct"],
        "reference_minus_floor": arms["planner_reference"]["correct"] - max(
            arms["fixed_informative"]["correct"], arms["random"]["correct"]),
        "oracle_minus_reference": arms["oracle"]["correct"] - arms["planner_reference"]["correct"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT / "world_fit.json").write_text(json.dumps(world_fit, indent=1), encoding="utf-8")
    gate = evaluate_gate_v3(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "contrasts": summary["contrasts"],
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in arms.items()}}, indent=1))


def evaluate_gate_v3(summary: dict) -> dict:
    arms = summary["arms"]
    ref = arms["planner_reference"]
    checks = {
        "planner_reference_coverage_ge_0.30": ref["coverage"] >= 0.30,
        "planner_reference_conditional_wrong_le_0.05": ref["conditional_wrong"] <= 0.05,
        "planner_shuffled_coverage_le_0.10": arms["planner_shuffled"]["coverage"] <= 0.10,
        "planner_shuffled_correct_le_half": arms["planner_shuffled"]["correct"]
        <= 0.5 * ref["correct"],
        "floors_abstain": arms["fixed_informative"]["coverage"] <= 0.05
        and arms["random"]["coverage"] <= 0.05,
    }
    return {"checks": checks, "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
