"""Dual-core run v4: the profile-conditioned world channel (protocol viability-contrast-4).

File summary
- Path: research/viability_contrast/run4.py
- Purpose: test whether the compound-level channel of the virtual cell lets the planner
  certify decisions on this task. The planner is v3's greedy expected-margin rule with a
  ProfileWorld whose predictive updates after every purchase; controls are the masked-profile
  and shuffled-readings arms; every non-profile arm is imported unchanged from the frozen v3
  run (identical code path, folds and templates). Tau for planner_profile is calibrated on
  training-fold split halves exactly as in v2/v3.
- Interfaces / data: reads the frozen pack and run3's episodes.csv; writes
  outputs/viability_contrast_20260928/run4/{episodes.csv, summary.json, gate.json, world_fit.json}.
- Depends on: research/viability_contrast/{protocol4.json, prepare.py, qualify.py, qualify2.py,
  run3.py, world3.py, world4.py}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify, qualify2, world4

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/run4"
RUN3 = ROOT / "outputs/viability_contrast_20260928/run3"
KEY = "viability-contrast-4"
BUDGET = 16
TOP_H = 8
Z_QUANT = np.array([-2.0, -1.33, -0.67, 0.0, 0.67, 1.33, 2.0])
Q_W = np.exp(-0.5 * Z_QUANT**2)
Q_W = Q_W / Q_W.sum()
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)


def sha(text: str) -> str:
    return qualify2.sha(text)


def run_planner_v4(world: world4.ProfileWorld, val_m, val_s, readings,
                   profile_readings=None, budget=BUDGET):
    """Greedy expected-margin planner with a profile-updated world.

    profile_readings: what the profile channel sees (defaults to the real readings; the
    masked arm passes another compound's readings). Score updates always use the real
    readings. Returns (trajectory, forecast_wrong_per_step).
    """
    if profile_readings is None:
        profile_readings = readings
    n_pool = len(readings)
    n_classes = val_m.shape[0]
    scores = np.zeros(n_classes)
    purchased = np.zeros(n_pool, dtype=bool)
    traj = []
    tops = []
    measurements = 0
    while measurements < budget:
        wm, ws = world.mean_scale()
        w = np.exp(scores - scores.max())
        w /= w.sum()
        top_idx = np.argsort(-w)[:TOP_H]
        w_top = w[top_idx] / w[top_idx].sum()
        cand = np.where(~purchased)[0]
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
        j = int(cand[int(np.argmax(exp_margin))])
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
    return traj, tops


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
        med, scale, valid, med_p, scale_p = qualify2.build_templates_v2(auc, train_by_class)
        val_m = np.where(valid, med, med_p[None, :])[:, pool_arr]
        val_s = np.where(valid, scale, scale_p[None, :])[:, pool_arr]
        beta, beta_ll = world4.fit_beta(auc, train_by_class, train_pos, units_arr,
                                        med, scale, valid, med_p, scale_p, pool_arr)

        # calibration on split halves
        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}
        calib_traj = []
        for h in (0, 1):
            templ_src = [c for c in train if half[c] == h]
            eps_for = [c for c in train if half[c] != h]
            mh, sh, vh, mph, sph = qualify2.build_templates_v2(
                auc, [[idx[c] for c in templ_src if labels[idx[c]] == ci]
                      for ci in range(len(classes))])
            val_mh = np.where(vh, mh, mph[None, :])[:, pool_arr]
            val_sh = np.where(vh, sh, sph[None, :])[:, pool_arr]
            src_pos = np.array([idx[c] for c in templ_src])
            for c in eps_for:
                x = idx[c]
                truth = labels[x]
                world = world4.ProfileWorld(auc[src_pos][:, pool_arr], beta, val_mh, val_sh)
                readings = auc[x, pool_arr]
                traj, _ = run_planner_v4(world, val_mh, val_sh, readings)
                calib_traj.append((traj, truth))
        tau_of = {"planner_profile": None}
        table = {}
        for tau in qualify2.TAU_GRID:
            dec = wrong = 0
            for traj, truth in calib_traj:
                out = qualify2.outcome_at_tau(traj, truth, tau)
                if out["decided"]:
                    dec += 1
                    wrong += not out["correct"]
            table[tau] = {"decided": dec, "wrong": wrong, "rate": (wrong / dec) if dec else None}
        qualifying = [tau for tau, t in table.items()
                      if t["decided"] >= qualify2.TAU_MIN_DECIDED and t["rate"] is not None
                      and t["rate"] <= qualify2.TAU_MAX_WRONG]
        tau_profile = min(qualifying) if qualifying else float("inf")

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
            for arm, prof_in in (("planner_profile", readings),
                                 ("planner_profile_masked", masked_readings),
                                 ("planner_profile_shuffled", shuffled_row[pool_arr])):
                world = world4.ProfileWorld(auc[train_pos][:, pool_arr], beta, val_m, val_s)
                real = shuffled_row[pool_arr] if arm == "planner_profile_shuffled" else readings
                traj, tops = run_planner_v4(world, val_m, val_s, real, profile_readings=prof_in)
                out = qualify2.outcome_at_tau(traj, truth, tau_profile)
                out["forecast_wrong_at_decision"] = (tops[out["measurements"] - 1]
                                                     if out["decided"] and out["measurements"] else None)
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, "tau": tau_profile, **out})
        world_fit[f] = {"beta": beta, "beta_ll": {str(k): v for k, v in beta_ll.items()},
                        "tau_profile": (None if np.isinf(tau_profile) else tau_profile),
                        "tau_table": {str(k): v for k, v in table.items()}}

    ep_new = pd.DataFrame(rows)
    ep3 = pd.read_csv(RUN3 / "episodes.csv")
    imported = ep3[ep3["arm"].isin(["oracle", "planner_reference", "fixed_informative",
                                    "random", "planner_shuffled"])]
    ep = pd.concat([imported, ep_new], ignore_index=True)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = qualify.summarise(ep)
    summary["folds"] = world_fit
    summary["budget"] = BUDGET
    summary["episodes"] = int((ep["arm"] == "oracle").sum())
    summary["classes"] = len(classes)
    summary["units"] = int(ep["unit"].nunique())
    arms = summary["arms"]
    summary["contrasts"] = {
        "profile_minus_reference": arms["planner_profile"]["correct"] - arms["planner_reference"]["correct"],
        "profile_minus_masked": arms["planner_profile"]["correct"] - arms["planner_profile_masked"]["correct"],
        "oracle_minus_profile": arms["oracle"]["correct"] - arms["planner_profile"]["correct"],
        "profile_coverage": arms["planner_profile"]["coverage"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT / "world_fit.json").write_text(json.dumps(world_fit, indent=1), encoding="utf-8")
    gate = evaluate_gate_v4(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "contrasts": summary["contrasts"],
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in arms.items()}}, indent=1))


def evaluate_gate_v4(summary: dict) -> dict:
    arms = summary["arms"]
    prof = arms["planner_profile"]
    checks = {
        "profile_coverage_ge_0.30": prof["coverage"] >= 0.30,
        "profile_conditional_wrong_le_0.05": (prof["conditional_wrong"] == prof["conditional_wrong"]
                                             and prof["conditional_wrong"] <= 0.05),
        "profile_minus_reference_gt_0": summary["contrasts"]["profile_minus_reference"] > 0,
        "profile_minus_masked_gt_0": summary["contrasts"]["profile_minus_masked"] > 0,
        "profile_shuffled_coverage_le_0.10": arms["planner_profile_shuffled"]["coverage"] <= 0.10,
    }
    return {"checks": checks, "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
