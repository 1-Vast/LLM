"""Descriptive paired summaries computed from stored results only (no refit, no outcome access)."""
from __future__ import annotations

import numpy as np

CONTRASTS = {
    "A_same_history": [("evo_repr", "refit"), ("evo_repr", "gbm_multitask"), ("evo_repr", "latent_fingerprint"), ("evo_repr", "adequate_interaction"),
                       ("evo_noinherit", "refit"), ("capacity_gbm", "refit")],
    "B_acquisition": [("evo_proc", "refit"), ("evo_proc", "random_probe"), ("evo_proc", "matrix_completion_aopt"), ("evo_proc", "direct"),
                      ("refit", "random_probe"), ("matrix_completion_aopt", "refit")],
    "C_full_loop": [("evo_full", "refit"), ("evo_full", "evo_repr"), ("evo_full", "evo_proc"), ("evo_full", "bayes_voi_joint"),
                    ("evo_full", "capacity_gbm"), ("evo_full", "matrix_completion_aopt"), ("evo_full", "direct")],
    "D_inheritance": [("evo_full", "evo_noinherit"), ("evo_full", "frozen_library"), ("evo_full", "parameter_only"),
                      ("evo_full", "transplant_repr_into_gbm"), ("evo_full", "evolved_Q_on_base_repr"), ("evo_full", "evolved_repr_on_base_Q"),
                      ("hindsight_superset_DIAGNOSTIC", "evo_full")],
}


def per_cell(results, arm):
    """Mean over seeds of the per-cell test utility. results: list of run_condition outputs sharing contract/budget."""
    if not all(arm in r["test"] for r in results):
        return None
    return np.mean([r["test"][arm] for r in results], axis=0)


def describe(d):
    d = np.asarray(d, float)
    return {"n_cells": int(len(d)), "mean": float(d.mean()), "median": float(np.median(d)), "min": float(d.min()), "max": float(d.max()),
            "wins": int((d > 1e-12).sum()), "losses": int((d < -1e-12).sum()), "ties": int((abs(d) <= 1e-12).sum()),
            "sd_cells": float(d.std(ddof=1)) if len(d) > 1 else None}


def contrasts(results):
    out = {}
    for q, pairs in CONTRASTS.items():
        for a, b in pairs:
            ua, ub = per_cell(results, a), per_cell(results, b)
            if ua is None or ub is None:
                continue
            out[f"{q}:{a}-{b}"] = describe(ua - ub)
    full, proc, repr_, ref = (per_cell(results, k) for k in ("evo_full", "evo_proc", "evo_repr", "refit"))
    out["C_full_loop:interaction_(full-proc)-(repr-refit)"] = describe((full - proc) - (repr_ - ref))
    return out


def arm_means(results):
    arms = results[0]["test"].keys()
    m = {a: float(per_cell(results, a).mean()) for a in arms if per_cell(results, a) is not None}
    m["oracle"] = float(np.mean([r["oracle_test"] for r in results]))
    return m


def anchor_curve(results):
    arms = results[0]["anchor_checkpoints"]["0"].keys()
    cur = {}
    for a in arms:
        cur[a] = [float(np.mean([np.mean(r["anchor_checkpoints"][str(g)][a]) for r in results])) for g in range(4)]
    return cur


def group(all_results):
    """Group stored condition outputs by (world label base, contract, budget)."""
    g = {}
    for r in all_results:
        g.setdefault((r["world_group"], r["contract"], r["budget"]), []).append(r)
    return g


def label(c, delta_use, control=None):
    """Pre-registered development label for the primary contrast evo_full - refit."""
    if c is None:
        return "NOT_RUN"
    n = c["n_cells"]
    ok = c["mean"] >= delta_use and c["wins"] >= 0.6 * n
    if control is not None and control["mean"] >= 0.5 * c["mean"] and c["mean"] > 0:
        return "ANCHOR_CONFOUNDED" if ok else "NOT_SUPPORTED"
    if ok:
        return "SUPPORTED_DEV"
    if c["mean"] < 0.5 * delta_use:
        return "NOT_SUPPORTED"
    return "INCONCLUSIVE"
