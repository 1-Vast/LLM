"""Arm runner for one (world, contract, budget, seed): baselines, evolving arms, inheritance ablations and diagnostics.

All arms share: the same released history at each checkpoint, the same anchor/test tasks, the same pool and shortlist size,
and the same query budget. Evolving arms also share the candidate cap (12 per generation, 3 generations).
"""
from __future__ import annotations

import copy
import time

import numpy as np

import svc_evolution as E
import svc_programs as P
from svc_world import World

DELTA_ACC = 0.0015


def arm_spec_arm(spec, name):
    return {"kind": "program", "spec": spec, "name": name}


def with_repr_of(evolved, base):
    s = copy.deepcopy(base)
    s["phi"], s["f"] = copy.deepcopy(evolved["phi"]), copy.deepcopy(evolved["f"])
    return s


def with_q_of(evolved, base):
    s = copy.deepcopy(base)
    s["Q"] = copy.deepcopy(evolved["Q"])
    return s


def run_condition(world: World, kind: str, B: int, contract: str, seed: int, *, delta_acc: float = DELTA_ACC, generations: int = 3) -> dict:
    t_start = time.perf_counter()
    static = world.static
    cells = E.split_cells(world.cells, kind)
    memo = E.Memo(world)
    fc = {}
    base = P.base_spec()
    out = {"world": world.label, "contract": contract, "budget": B, "seed": seed, "cells": {k: list(v) for k, v in cells.items()}, "delta_acc": delta_acc}

    # ---- evolving arms (same candidate cap and generations)
    arms_cfg = {"evo_full": (E.REPR_OPS + E.PROC_OPS, True), "evo_repr": (E.REPR_OPS, True), "evo_proc": (E.PROC_OPS, True), "evo_noinherit": (E.REPR_OPS + E.PROC_OPS, False)}
    libs, incumbents, records, finals = {}, {}, {}, {}
    for name, (ops, inherit) in arms_cfg.items():
        lib, inc, recs, final_cells = E.evolve(name, world, memo, static, cells, seed, B, contract, ops, inherit=inherit, delta_acc=delta_acc, generations=generations, fitted_cache=fc)
        libs[name], incumbents[name], records[name], finals[name] = lib, inc, recs, final_cells
    final_cells = finals["evo_full"]
    out["library"] = {n: [{k: v for k, v in e.items()} for e in libs[n].entries] for n in libs}
    out["generation_records"] = {n: [{k: v for k, v in r.items() if k != "candidate_specs"} for r in records[n]] for n in records}
    out["final_program"] = {n: incumbents[n]["id"] for n in incumbents}

    # ---- fixed arms
    fixed = E.baseline_arms()
    fixed["random_probe"] = arm_spec_arm({**base, "Q": [{"kind": "probe", "frac": 0.5, "rule": "random", "cond": None}, {"kind": "confirm", "frac": 0.5}]}, "random_probe")
    fixed = {k: ({**v, "name": k}) for k, v in fixed.items()}
    if contract == "T":
        fixed.pop("direct")

    # ---- inheritance diagnostics built from evo_full's lineage
    full_lib = libs["evo_full"]
    gen1_id = records["evo_full"][0]["incumbent_after"]
    gen1_spec = full_lib.get(gen1_id)["spec"]
    final_spec = incumbents["evo_full"]["spec"]
    diag_arms = {
        "frozen_library": ("frozen", gen1_spec),                       # fit on the gen-1 history, never updated
        "parameter_only": ("final", gen1_spec),                        # gen-1 structure, parameters refit on all history
        "transplant_repr_into_gbm": ("final", {**base, "phi": copy.deepcopy(final_spec["phi"]), "f": {"type": "gbm", "inter": [], "lam": 3.0}}),
        "evolved_Q_on_base_repr": ("final", with_q_of(final_spec, base)),
        "evolved_repr_on_base_Q": ("final", with_repr_of(final_spec, base)),
    }

    # ---- checkpoint curve on the common anchor tasks, final test
    hist_by_g = {0: list(cells["H0"])}
    for g in (1, 2, 3):
        hist_by_g[g] = hist_by_g[g - 1] + list(cells[f"D{g}"])
    ckpt = {}
    evo_specs_by_g = {n: {0: base, **{g: full_spec_at(libs[n], records[n], g) for g in (1, 2, 3)}} for n in arms_cfg}
    for g in range(4):
        row = {}
        for name, arm in fixed.items():
            row[name] = [r["utility"] for r in E.evaluate(arm, world, memo, static, cells["A"], hist_by_g[g], B, seed, contract, fitted_cache=fc)]
        for name in arms_cfg:
            arm = arm_spec_arm(evo_specs_by_g[name][g], name)
            row[name] = [r["utility"] for r in E.evaluate(arm, world, memo, static, cells["A"], hist_by_g[g], B, seed, contract, fitted_cache=fc)]
        ckpt[g] = row
    out["anchor_checkpoints"] = {str(g): v for g, v in ckpt.items()}

    test = {}
    detail = {}
    final_arms = dict(fixed)
    for name in arms_cfg:
        final_arms[name] = arm_spec_arm(incumbents[name]["spec"], name)
    for name, (mode, spec) in diag_arms.items():
        final_arms[name] = arm_spec_arm(spec, name)
    for name, arm in final_arms.items():
        hist_cells = hist_by_g[1] if name == "frozen_library" else hist_by_g[3]
        res = E.evaluate(arm, world, memo, static, cells["T"], hist_cells, B, seed, contract, fitted_cache=fc)
        test[name] = [r["utility"] for r in res]
        detail[name] = [{"cell": r["cell"], "utility": r["utility"], "oracle": r["oracle"], "unqueried_only": r["unqueried_only_utility"], "n_nominated_queried": r["n_nominated_queried"],
                         "spent": r["spent"], "nominated": r["nominated"]} for r in res]
    # labelled hindsight superset (diagnostic only; selects on the test tasks)
    cand_specs = [s for r in records["evo_full"] for s in r["candidate_specs"]] + [full_lib.get(i)["spec"] for i in [e["id"] for e in full_lib.entries]]
    best, best_u = None, -1
    for spec in cand_specs:
        u = [r["utility"] for r in E.evaluate(arm_spec_arm(spec, "hindsight"), world, memo, static, cells["T"], hist_by_g[3], B, seed, contract, fitted_cache=fc)]
        if np.mean(u) > best_u:
            best, best_u = u, float(np.mean(u))
    test["hindsight_superset_DIAGNOSTIC"] = best
    out["test"] = test
    out["test_detail"] = detail
    out["oracle_test"] = [d["oracle"] for d in detail["refit"]]
    out["n_candidates_evaluated_hindsight"] = len(cand_specs)
    out["compute_seconds"] = time.perf_counter() - t_start
    out["clock_by_arm"] = dict(E.CLOCK.t)
    return out


def full_spec_at(lib, records, g):
    return lib.get(records[min(g, len(records)) - 1]["incumbent_after"])["spec"]
