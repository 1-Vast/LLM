"""Qualification run for the viability-contrast task (protocol viability-contrast-1).

File summary
- Path: research/viability_contrast/qualify.py
- Purpose: E-DATA1-style qualification of task T1 before any dual-core arm is built.
  Computes per-fold templates and the validator's k (training folds only, exact
  leave-one-unit-out), then runs the registered arms (oracle, fixed_informative, random, and
  both shuffled controls) on identical episodes with identical validator, menu and budget.
  Reports the registered qualification gate.
- Interfaces / data: reads the frozen pack via prepare.load_pack(); writes
  outputs/viability_contrast_20260928/qualify/{episodes.csv, summary.json, gate.json}.
- Depends on: research/viability_contrast/{protocol.json, prepare.py}
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/qualify"
KEY = "viability-contrast-1"
K_GRID = (2.5, 3.0, 3.5, 4.0)
K_TARGET = 0.02
MIN_TEMPLATE_READINGS = 5
BUDGET = 16
DRAWS = 10_000


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------ templates
def build_templates(auc, idx_by_class):
    """Median and scaled MAD per (class, line) over each class's compound indices.

    A (class, line) template exists only with >= MIN_TEMPLATE_READINGS readings.
    """
    n_classes = len(idx_by_class)
    n_lines = auc.shape[1]
    med = np.full((n_classes, n_lines), np.nan)
    scale = np.full((n_classes, n_lines), np.nan)
    valid = np.zeros((n_classes, n_lines), dtype=bool)
    for ci, idxs in enumerate(idx_by_class):
        if not idxs:
            continue
        block = auc[np.asarray(idxs)]
        for lj in range(n_lines):
            v = block[:, lj]
            v = v[np.isfinite(v)]
            if len(v) < MIN_TEMPLATE_READINGS:
                continue
            m = np.median(v)
            s = max(1.4826 * np.median(np.abs(v - m)), 0.05)
            med[ci, lj] = m
            scale[ci, lj] = s
            valid[ci, lj] = True
    return med, scale, valid


def select_k(auc, idx_by_class):
    """Exact leave-one-unit-out per-reading wrong-elimination rate per k.

    For each (class, line) the class's readings are sorted once; removing the i-th
    sorted value is the exact leave-one-out template for the compound that held it.
    Rates pool every (training compound, line) reading, mirroring the episode rule.
    """
    counts = {k: [0, 0] for k in K_GRID}
    for idxs in idx_by_class:
        if not idxs:
            continue
        arr = np.asarray(idxs)
        block = auc[arr]
        for lj in range(block.shape[1]):
            col = block[:, lj]
            fin = np.isfinite(col)
            v = np.sort(col[fin])
            n = len(v)
            if n < MIN_TEMPLATE_READINGS + 1:
                continue
            for i in range(n):
                rest = np.delete(v, i)
                m = np.median(rest)
                s = max(1.4826 * np.median(np.abs(rest - m)), 0.05)
                a = v[i]
                for k in K_GRID:
                    counts[k][1] += 1
                    if abs(a - m) > k * s:
                        counts[k][0] += 1
    rates = {k: (c[0] / c[1] if c[1] else float("nan")) for k, c in counts.items()}
    chosen = None
    for k in K_GRID:
        if np.isfinite(rates[k]) and rates[k] <= K_TARGET:
            chosen = k
            break
    if chosen is None:
        chosen = K_GRID[-1]
    return chosen, rates


# ------------------------------------------------------------------ episode engine
def elimination_mask(a, lj, med, scale, valid, k, surv):
    """Boolean mask over classes eliminated by reading a at line lj."""
    if not np.isfinite(a):
        return np.zeros(med.shape[0], dtype=bool)
    return surv & valid[:, lj] & (np.abs(a - med[:, lj]) > k * scale[:, lj])


def run_episode(arm, truth, auc_row, med, scale, valid, k, budget, fixed_order, random_order):
    n_classes = med.shape[0]
    surv = np.ones(n_classes, dtype=bool)
    measurements = 0
    qc_failures = 0
    purchased = np.zeros(auc_row.shape[0], dtype=bool)
    reason = "budget"
    order_pos = 0
    while measurements < budget and surv.sum() > 1:
        if arm == "oracle":
            best_lj = -1
            best_key = None
            cand = np.where(np.isfinite(auc_row) & ~purchased)[0]
            for lj in cand:
                elim = elimination_mask(auc_row[lj], lj, med, scale, valid, k, surv)
                n_elim = int(elim.sum())
                if n_elim == 0:
                    key = (0, 0, 0, -int(sha(f"{KEY}|oracle|{lj}"), 16))
                else:
                    wrong = int(elim.sum()) - int(elim[truth])
                    key = (wrong, not bool(elim[truth]), n_elim,
                           -int(sha(f"{KEY}|oracle|{lj}"), 16))
                if best_key is None or key > best_key:
                    best_key = key
                    best_lj = lj
            if best_lj < 0:
                reason = "menu_exhausted"
                break
            lj = best_lj
        else:
            order = fixed_order if arm == "fixed_informative" else random_order
            lj = -1
            while order_pos < len(order):
                cand = order[order_pos]
                order_pos += 1
                if not purchased[cand]:
                    lj = cand
                    break
            if lj < 0:
                reason = "menu_exhausted"
                break
        purchased[lj] = True
        measurements += 1
        a = auc_row[lj]
        if not np.isfinite(a):
            qc_failures += 1
            continue
        surv &= ~elimination_mask(a, lj, med, scale, valid, k, surv)
    n_surv = int(surv.sum())
    if n_surv == 1:
        chosen = int(np.argmax(surv))
        return {"decided": True, "correct": bool(chosen == truth), "chosen": chosen,
                "measurements": measurements, "qc_failures": qc_failures,
                "reason": "decided", "survivors": 1}
    if n_surv == 0:
        reason = "contradiction"
    return {"decided": False, "correct": False, "chosen": -1,
            "measurements": measurements, "qc_failures": qc_failures,
            "reason": reason, "survivors": n_surv}


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

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    fold_summaries = {}
    for f in sorted(folds, key=int):
        heldout = folds[f]
        heldout_set = set(heldout)
        train_pos = [idx[c] for c in compounds if c not in heldout_set and labels[idx[c]] >= 0]
        idx_by_class_train = [[p for p in train_pos if labels[p] == ci] for ci in range(len(classes))]
        med, scale, valid = build_templates(auc, idx_by_class_train)
        k, k_rates = select_k(auc, idx_by_class_train)
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
        fixed_order = sorted(pool, key=lambda l: (-sep[l], sha(f"{KEY}|fixed|{lines[l]}")))
        fold_summaries[f] = {"k": k, "k_rates": {str(kk): vv for kk, vv in k_rates.items()},
                             "heldout": len(heldout)}

        rng = np.random.default_rng(int(sha(f"{KEY}|shuffle|{f}")[:16], 16))
        heldout_pos = np.array([idx[c] for c in heldout])
        shuffled_cols = {}
        for lj in pool:
            shuffled_cols[lj] = rng.permutation(auc[heldout_pos, lj])

        for c in heldout:
            x = idx[c]
            truth = labels[x]
            if truth < 0:
                continue
            unit = meta.loc[c, "unit"]
            rng_order = list(pool)
            np.random.default_rng(int(sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rng_order)
            for arm in ("oracle", "fixed_informative", "random"):
                r = run_episode(arm, truth, auc[x], med, scale, valid, k,
                                BUDGET, fixed_order, rng_order)
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, **r})
            shuffled_row = np.full(len(lines), np.nan)
            xi = int(np.where(heldout_pos == x)[0][0])
            for lj in pool:
                shuffled_row[lj] = shuffled_cols[lj][xi]
            for arm, base in (("oracle_shuffled", "oracle"), ("fixed_shuffled", "fixed_informative")):
                r = run_episode(base, truth, shuffled_row, med, scale, valid, k,
                                BUDGET, fixed_order, rng_order)
                rows.append({"fold": f, "compound": c, "unit": unit, "class": classes[truth],
                             "arm": arm, **r})

    ep = pd.DataFrame(rows)
    ep.to_csv(OUT / "episodes.csv", index=False)
    summary = summarise(ep)
    summary["folds"] = fold_summaries
    summary["budget"] = BUDGET
    summary["episodes"] = int((ep["arm"] == "oracle").sum())
    summary["classes"] = len(classes)
    summary["units"] = int(ep["unit"].nunique())
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    gate = evaluate_gate(summary)
    (OUT / "gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    print(json.dumps({"gate": gate, "diffs": summary["diffs"],
                      "arms": {a: {k: v for k, v in s.items() if k != "correct_ci"}
                               for a, s in summary["arms"].items()}}, indent=1))


def summarise(ep: pd.DataFrame) -> dict:
    rng = np.random.default_rng(int(sha(f"{KEY}|boot")[:16], 16))
    arms = {}
    per_arm_unit = {}
    for arm, g in ep.groupby("arm"):
        g = g.copy()
        g["wrong"] = g["decided"] & ~g["correct"]
        per_unit = g.groupby("unit")[["correct", "decided", "wrong", "measurements"]].mean()
        per_arm_unit[arm] = per_unit
        decided = g["decided"].sum()
        wrong = g["wrong"].sum()
        arms[arm] = {
            "correct": float(g["correct"].mean()),
            "coverage": float(g["decided"].mean()),
            "conditional_wrong": float(wrong / decided) if decided else float("nan"),
            "measurements": float(g["measurements"].mean()),
            "qc_failures": float(g["qc_failures"].mean()),
            "contradiction_rate": float((g["reason"] == "contradiction").mean()),
        }
        u = per_unit["correct"].to_numpy()
        boot = [float(u[rng.integers(0, len(u), len(u))].mean()) for _ in range(DRAWS)]
        arms[arm]["correct_ci"] = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    diffs = {}
    for a, b in (("oracle", "fixed_informative"), ("fixed_informative", "random"),
                 ("oracle", "random")):
        if a not in per_arm_unit or b not in per_arm_unit:
            continue
        ja = per_arm_unit[a][["correct"]].join(per_arm_unit[b][["correct"]], rsuffix="_b", how="inner")
        d = (ja["correct"] - ja["correct_b"]).to_numpy()
        boot = [float(d[rng.integers(0, len(d), len(d))].mean()) for _ in range(DRAWS)]
        diffs[f"{a}-{b}"] = float(d.mean())
        diffs[f"{a}-{b}_ci"] = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    return {"arms": arms, "diffs": diffs}


def evaluate_gate(summary: dict) -> dict:
    d = summary["diffs"]
    arms = summary["arms"]
    checks = {
        "oracle_minus_fixed_ge_0.05": d.get("oracle-fixed_informative", 0) >= 0.05,
        "fixed_minus_random_ge_0.02": d.get("fixed_informative-random", 0) >= 0.02,
        "oracle_conditional_wrong_le_0.10": arms["oracle"]["conditional_wrong"] <= 0.10,
        "episodes_ge_400": summary["episodes"] >= 400,
        "classes_ge_20": summary["classes"] >= 20,
        "shuffled_oracle_below_fixed": arms.get("oracle_shuffled", {}).get("correct", 1.0)
        < arms["fixed_informative"]["correct"],
    }
    return {"checks": checks, "qualified": all(checks.values())}


if __name__ == "__main__":
    main()
