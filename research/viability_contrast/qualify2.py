"""Qualification run v2 for the viability-contrast task (protocol viability-contrast-2).

File summary
- Path: research/viability_contrast/qualify2.py
- Purpose: v2 qualification after the v1 gate failed (README section 3.1). Replaces hard
  elimination with a symmetric score-margin validator: every hypothesis is scored against every
  purchased reading (class template or pooled fallback), |z| winsorized at 3, decision at the
  first step whose margin clears a per-arm tau calibrated on training-fold split-halves.
  Arms, menu, budget, folds, units and bootstrap are inherited from v1 unchanged.
- Interfaces / data: reads the frozen pack via prepare.load_pack(); writes
  outputs/viability_contrast_20260928/qualify2/{episodes.csv, trajectories.npz, summary.json, gate.json}.
- Depends on: research/viability_contrast/{protocol2.json, prepare.py, qualify.py (shared helpers)}
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/qualify2"
KEY = "viability-contrast-2"
TAU_GRID = (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0)
TAU_MAX_WRONG = 0.05
TAU_MIN_DECIDED = 20
BUDGET = 16
DRAWS = 10_000
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------ templates
def build_templates_v2(auc, idx_by_class):
    """Class templates plus the pooled fallback template (all given compounds)."""
    med, scale, valid = qualify.build_templates(auc, idx_by_class)
    all_idx = np.asarray([p for idxs in idx_by_class for p in idxs])
    n_lines = auc.shape[1]
    med_p = np.full(n_lines, np.nan)
    scale_p = np.full(n_lines, np.nan)
    for lj in range(n_lines):
        v = auc[all_idx, lj]
        v = v[np.isfinite(v)]
        if len(v) < qualify.MIN_TEMPLATE_READINGS:
            continue
        m = np.median(v)
        med_p[lj] = m
        scale_p[lj] = max(1.4826 * np.median(np.abs(v - m)), 0.05)
    return med, scale, valid, med_p, scale_p


def separation_order(med, scale, valid, pool, lines, tag):
    sep = np.zeros(len(lines))
    for lj in pool:
        ok = np.where(valid[:, lj])[0]
        if len(ok) < 2:
            continue
        diffs = []
        for i in range(len(ok)):
            for j in range(i + 1, len(ok)):
                c1, c2 = ok[i], ok[j]
                diffs.append(abs(med[c1, lj] - med[c2, lj])
                             / max((scale[c1, lj] + scale[c2, lj]) / 2, 0.05))
        sep[lj] = float(np.mean(diffs)) if diffs else 0.0
    return sorted(pool, key=lambda l: (-sep[l], sha(f"{KEY}|fixed|{tag}|{lines[l]}")))


# ------------------------------------------------------------------ score engine
def term_matrix(auc_row, med, scale, valid, med_p, scale_p, pool_arr):
    """Winsorized Gaussian log-density terms T[c, j] for every class and pool line."""
    m = np.where(valid, med, med_p[None, :])
    s = np.where(valid, scale, scale_p[None, :])
    a = auc_row[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (a - m) / s
        t = -0.5 * np.minimum(z * z, 9.0) - np.log(s) - LOG_SQRT_2PI
    t[:, ~np.isfinite(auc_row)] = np.nan
    return t[:, pool_arr]


def run_episode_v2(arm, truth, T, pool_arr, fixed_order_pos, random_order_pos):
    """Run one episode on the precomputed term matrix.

    Returns the purchased pool positions and, after each purchase, the margin and the
    current argmax class. QC failures (no reading) consume budget without a score update;
    the oracle purchases only lines with a reading.
    """
    n_classes = T.shape[0]
    scores = np.zeros(n_classes)
    purchased = np.zeros(T.shape[1], dtype=bool)
    traj = []
    order_pos = 0
    measurements = 0
    while measurements < BUDGET:
        if arm == "oracle":
            cand = np.where(np.isfinite(T[0]) & ~purchased)[0]
            if len(cand) == 0:
                break
            after = scores[:, None] + T[:, cand]
            true_after = after[truth]
            wrong_max = np.max(np.delete(after, truth, axis=0), axis=0)
            margin_true = true_after - wrong_max
            best = int(np.argmax(margin_true))
            ties = np.where(margin_true == margin_true[best])[0]
            if len(ties) > 1:
                gains = T[truth, cand[ties]]
                ties = ties[np.where(gains == gains.max())[0]]
            if len(ties) > 1:
                pick = min(ties, key=lambda j: sha(f"{KEY}|oracle|{pool_arr[cand[j]]}"))
            else:
                pick = ties[0]
            j = int(cand[pick])
        else:
            order = fixed_order_pos if arm == "fixed_informative" else random_order_pos
            j = -1
            while order_pos < len(order):
                c = order[order_pos]
                order_pos += 1
                if not purchased[c]:
                    j = c
                    break
            if j < 0:
                break
        purchased[j] = True
        measurements += 1
        col = T[:, j]
        qc = not np.isfinite(col[0])
        if not qc:
            scores = scores + col
        top = int(np.argmax(scores))
        rest = np.delete(scores, top)
        margin = float(scores[top] - rest.max())
        traj.append((margin, top, measurements, qc))
    return traj


def outcome_at_tau(traj, truth, tau):
    for margin, top, measurements, qc in traj:
        if margin >= tau:
            return {"decided": True, "correct": bool(top == truth),
                    "measurements": measurements,
                    "qc_failures": int(sum(1 for _, _, _, q in traj if q)),
                    "reason": "decided"}
    return {"decided": False, "correct": False,
            "measurements": traj[-1][2] if traj else 0,
            "qc_failures": int(sum(1 for _, _, _, q in traj if q)),
            "reason": "undecided"}


# ------------------------------------------------------------------ main run
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

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    fold_info = {}
    for f in sorted(folds, key=int):
        heldout = folds[f]
        heldout_set = set(heldout)
        train = [c for c in compounds if c not in heldout_set and labels[idx[c]] >= 0]
        unit_of = {c: str(meta.loc[c, "unit"]) for c in train}
        half = {c: int(sha(f"{KEY}|calib|{unit_of[c]}")[:8], 16) % 2 for c in train}

        med, scale, valid, med_p, scale_p = build_templates_v2(
            auc, [[idx[c] for c in train if labels[idx[c]] == ci] for ci in range(len(classes))])
        fixed_full = separation_order(med, scale, valid, pool, lines, "full")
        fixed_full_pos = [pos_of_line[l] for l in fixed_full]

        # -------- calibration episodes on split halves
        calib_traj = {arm: [] for arm in ("oracle", "fixed_informative", "random")}
        for h in (0, 1):
            templ_src = [c for c in train if half[c] == h]
            eps_for = [c for c in train if half[c] != h]
            mh, sh, vh, mph, sph = build_templates_v2(
                auc, [[idx[c] for c in templ_src if labels[idx[c]] == ci] for ci in range(len(classes))])
            fixed_h = separation_order(mh, sh, vh, pool, lines, f"half{h}")
            fixed_h_pos = [pos_of_line[l] for l in fixed_h]
            for c in eps_for:
                x = idx[c]
                truth = labels[x]
                T = term_matrix(auc[x], mh, sh, vh, mph, sph, pool_arr)
                rng_order = list(range(len(pool)))
                np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
                for arm in ("oracle", "fixed_informative", "random"):
                    traj = run_episode_v2(arm, truth, T, pool_arr, fixed_h_pos, rng_order)
                    calib_traj[arm].append((traj, truth))

        # -------- tau selection per arm
        tau_of = {}
        tau_table = {}
        for arm, episodes in calib_traj.items():
            table = {}
            for tau in TAU_GRID:
                dec = 0
                wrong = 0
                for traj, truth in episodes:
                    out = outcome_at_tau(traj, truth, tau)
                    if out["decided"]:
                        dec += 1
                        wrong += not out["correct"]
                table[tau] = {"decided": dec, "wrong": wrong,
                              "rate": (wrong / dec) if dec else None}
            qualifying = [tau for tau, t in table.items()
                          if t["decided"] >= TAU_MIN_DECIDED and t["rate"] is not None
                          and t["rate"] <= TAU_MAX_WRONG]
            tau_of[arm] = min(qualifying) if qualifying else float("inf")
            tau_table[arm] = {str(k): v for k, v in table.items()}

        # -------- held-out episodes
        rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
        heldout_pos = np.array([idx[c] for c in heldout])
        shuffled_cols = {lj: rng.permutation(auc[heldout_pos, lj]) for lj in pool}
        for c in heldout:
            x = idx[c]
            truth = labels[x]
            if truth < 0:
                continue
            unit = str(meta.loc[c, "unit"])
            T = term_matrix(auc[x], med, scale, valid, med_p, scale_p, pool_arr)
            rng_order = list(range(len(pool)))
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
            for arm in ("oracle", "fixed_informative", "random"):
                traj = run_episode_v2(arm, truth, T, pool_arr, fixed_full_pos, rng_order)
                out = outcome_at_tau(traj, truth, tau_of[arm])
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, "tau": tau_of[arm], **out})
            shuffled_row = np.full(len(lines), np.nan)
            xi = int(np.where(heldout_pos == x)[0][0])
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][xi]
            Ts = term_matrix(shuffled_row, med, scale, valid, med_p, scale_p, pool_arr)
            for arm, base in (("oracle_shuffled", "oracle"), ("fixed_shuffled", "fixed_informative")):
                traj = run_episode_v2(base, truth, Ts, pool_arr, fixed_full_pos, rng_order)
                out = outcome_at_tau(traj, truth, tau_of[base])
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, "tau": tau_of[base], **out})
        fold_info[f] = {"tau": {a: (None if np.isinf(t) else t) for a, t in tau_of.items()},
                        "tau_table": tau_table, "heldout": len(heldout)}

    ep = pd.DataFrame(rows)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = qualify.summarise(ep)
    summary["folds"] = fold_info
    summary["budget"] = BUDGET
    summary["episodes"] = int((ep["arm"] == "oracle").sum())
    summary["classes"] = len(classes)
    summary["units"] = int(ep["unit"].nunique())
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    gate = evaluate_gate_v2(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "diffs": summary["diffs"],
                      "tau": {f: i["tau"] for f, i in fold_info.items()},
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in summary["arms"].items()}}, indent=1))


def evaluate_gate_v2(summary: dict) -> dict:
    d = summary["diffs"]
    arms = summary["arms"]
    checks = {
        "oracle_minus_fixed_ge_0.05": d.get("oracle-fixed_informative", 0) >= 0.05,
        "fixed_minus_random_ge_0.02": d.get("fixed_informative-random", 0) >= 0.02,
        "oracle_conditional_wrong_le_0.10": arms["oracle"]["conditional_wrong"] <= 0.10,
        "oracle_coverage_ge_0.30": arms["oracle"]["coverage"] >= 0.30,
        "shuffled_oracle_coverage_le_0.10": arms["oracle_shuffled"]["coverage"] <= 0.10,
        "shuffled_oracle_correct_le_half": arms["oracle_shuffled"]["correct"]
        <= 0.5 * arms["oracle"]["correct"],
        "episodes_ge_400": summary["episodes"] >= 400,
        "classes_ge_20": summary["classes"] >= 20,
    }
    return {"checks": checks, "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
