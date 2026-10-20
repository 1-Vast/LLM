"""One stream = one independent world. All arms see the same released data on the same timeline; they differ only in what they do with it.

Timeline (shared): H0 released. For b = 1..4: every arm runs the campaigns of batch b with the library it deployed after batch b-1 (batch 1: base library);
the batch is then fully released to every arm (shared source-data release); library arms search on cells released before batch b, validate on batch b (not used in any
candidate fit), deploy/retire, and refit the survivor on everything released. Anchor backgrounds (A_old, A_new) are never released and are evaluated at each checkpoint.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import iv_conv as V  # noqa: E402
import iv_core as C  # noqa: E402
import iv_search as S  # noqa: E402
import iv_worlds as W  # noqa: E402
from svc_world import realized_utility  # noqa: E402

BUDGET = 4
CURVE_BUDGETS = (2, 8)
LIB_ARMS = {                       # name -> (search mode, policy adaptation)
    "inh_kg": ("inherit", False),   # library evolution ON,  policy adaptation OFF
    "inh_pol": ("inherit", True),   # library evolution ON,  policy adaptation ON
    "rst_kg": ("restart", False),   # same envelope, nothing inherited
    "fix_kg": ("once", False),      # library evolution OFF (structure fixed after the first search, parameters refit), policy OFF
    "fix_pol": ("once", True),      # library evolution OFF, policy adaptation ON
}
POLICY_ARMS = {"inh_bald": "bald", "inh_var": "variance", "inh_rand": "random", "inh_exploit": "exploit"}   # inh_kg library, other acquisition rule
ABLATIONS = ("inh_del_all", "inh_del_old")
STATIC_ARMS = ("prior", "direct", "lat_aopt", "lat_var", "broadcap_bald", "broadcap_transplant", "gbm_var", "gbm_ucb", "gbm_exploit")
ANCHOR_ARMS = ("inh_kg", "inh_pol", "rst_kg", "fix_kg", "fix_pol", "inh_del_all", "prior", "direct", "lat_aopt", "broadcap_bald")
DECISIVE_TRACE = ("inh_kg", "inh_pol", "rst_kg", "fix_kg")


def tmask(static):
    cls = static.pair_class
    m = np.zeros(static.n, bool)
    for c in np.unique(cls):
        ix = np.nonzero(cls == c)[0]
        m[ix[::2]] = True
    return m


def fo_probes(static, mask, cell, sid, B):
    rng = np.random.default_rng(S.seed_of("fo", sid, cell))
    return [int(p) for p in rng.choice(np.nonzero(mask)[0], size=B, replace=False)]


def pack_fits(fits):
    out = {}
    for f in fits:
        pre = f.program.pid
        out[pre + "|sigma"] = f.sigma
        if f.states is not None:
            out[pre + "|states"] = np.asarray(f.states)
            out[pre + "|logprior"] = f.logprior
            out[pre + "|mu"] = f.mu
        if f.V is not None:
            out[pre + "|V"] = f.V
        out[pre + "|meta"] = np.array(json.dumps({"kind": f.program.kind, "k": f.program.k, "gates": list(f.program.gates), "conj": [list(c) for c in f.program.conj], "version": f.version}))
        if f.gates:
            for gid, g in f.gates.items():
                out[f"{pre}|gate|{gid}|beta"] = g.beta
                out[f"{pre}|gate|{gid}|b"] = g.b
                out[f"{pre}|gate|{gid}|pi"] = np.array(g.pi)
                out[f"{pre}|gate|{gid}|scope"] = np.array(g.scope)
    return out


def compact_trace(tr):
    out = []
    for t in tr:
        d = {k: t[k] for k in ("probe", "kg_score", "stop", "fixed", "stopped_at_step", "alternative_action") if k in t}
        if "program_weights" in t:
            d["program_weights_before"] = {k: round(v, 4) for k, v in t["program_weights"].items()}
            d["competing_predictions"] = {k: {a: round(b, 4) for a, b in v.items()} for k, v in t["competing_predictions_for_probe"].items()}
            d["alternatives"] = t["alternatives"]
            d["nominations_that_could_change"] = t["nominations_that_could_change"]
        if "after" in t:
            d["program_weights_after"] = {k: round(v, 4) for k, v in t["after"]["program_weights"].items()}
            d["unresolved_mismatch"] = bool(t["after"]["mismatch"])
        out.append(d)
    return out


def task_row(arm, contract, kind, cell, gen, r, camp, nom, bel, tr, policy, programs, keep_trace, seconds):
    row = {"arm": arm, "contract": contract, "role": kind, "cell": cell, "gen": gen, "utility": r["utility"], "oracle": r["oracle"], "regret": r["regret"],
           "nominated": [int(x) for x in nom], "n_spent": camp.spent, "policy": policy, "programs": programs, "seconds": round(seconds, 4),
           "probes": [int(p) for p in camp.queried], "values": [camp.queried[p] for p in camp.queried]}
    if bel is not None:
        row["final_program_weights"] = {k: round(v, 4) for k, v in bel.program_weights().items()}
    if keep_trace and tr is not None:
        row["trace"] = compact_trace(tr)
    return row


def run_stream(kind: str, seed: int, decoupled: bool, out_dir: Path, cfg: dict | None = None, stream: dict | None = None, sid_override: str | None = None):
    cfg = cfg or {}
    B = cfg.get("budget", BUDGET)
    sid = sid_override or f"{kind}_{seed}{'_dec' if decoupled else ''}"
    out_path = out_dir / "streams" / f"{sid}.json.gz"
    if out_path.exists():
        raise FileExistsError(f"stage output exists, refusing a second evaluation: {out_path}")
    t_start = time.perf_counter()
    s = stream if stream is not None else W.make_stream(kind, seed, decoupled=decoupled)
    w, sched = s["world"], s["schedule"]
    st = w.static
    mask_T = tmask(st)
    libs = {name: S.Library() for name in LIB_ARMS}
    rel = list(sched["H0"])
    rows, gen_records, models, priors = [], {}, {}, {}
    seconds = {}
    anchors = {"A_old": sched.get("A_old", []), "A_new": sched.get("A_new", [])}

    def add_seconds(arm, dt):
        seconds[arm] = seconds.get(arm, 0.0) + dt

    def do_task(arm, contract, role, cell, gen, M, fits, policy, programs, mask=None, fixed=None, keep=False, budget=None):
        t0 = time.perf_counter()
        r, camp, nom, bel, tr = S.run_task(w, st, cell, M, fits, policy, B if budget is None else budget, contract, mask, S.seed_of("task", sid, cell), fixed_probes=fixed)
        dt = time.perf_counter() - t0
        add_seconds(arm, dt)
        rows.append(task_row(arm, contract if fixed is None else "FO", role, cell, gen, r, camp, nom, bel, tr, policy, programs, keep and arm in DECISIVE_TRACE, dt))

    def prog_ids(fits):
        return [f.program.pid + (":" + ",".join(f.program.gates) if f.program.gates else "") for f in fits if f.program.kind == "gate"]

    for b in range(1, len(sched["batches"]) + 1):
        batch = sched["batches"][b - 1]
        Mrel = C.build_models(w, rel, st)
        priors[f"b{b}"] = {"pm": Mrel.prior.pm, "w": Mrel.prior.w, "fbar": Mrel.prior.fbar, "cells": list(rel)}
        # ---- campaigns of batch b
        arm_fits = {}
        for name, lib in libs.items():
            t0 = time.perf_counter()
            fits = S.make_fits(lib, Mrel, lib.deployed, lib.gates, lib.rank)
            add_seconds(name, time.perf_counter() - t0)
            arm_fits[name] = (fits, lib.policy)
            if name in DECISIVE_TRACE:
                models[f"{name}|b{b}"] = pack_fits(fits)
            for cell in batch:
                do_task(name, "E", "task", cell, b, Mrel, fits, lib.policy, prog_ids(fits), keep=True)
                do_task(name, "T", "task", cell, b, Mrel, fits, lib.policy, prog_ids(fits), mask=mask_T)
                do_task(name, "FO", "task", cell, b, Mrel, fits, lib.policy, prog_ids(fits), mask=mask_T, fixed=fo_probes(st, mask_T, cell, sid, B))
        base_fits, _ = arm_fits["inh_kg"]
        # budget-utility curve (secondary): the same deployed libraries at other budgets
        N0 = C.fit_program(C.Program("N", "null"), Mrel, {})
        c3b = C.fit_program(C.Program("C3", "cont", k=3), Mrel, {})
        for bud in CURVE_BUDGETS:
            for cell in batch:
                for name in ("inh_kg", "rst_kg"):
                    fits_, pol_ = arm_fits[name]
                    do_task(f"{name}@B{bud}", "E", "task", cell, b, Mrel, fits_, pol_, [], budget=bud)
                do_task(f"lat_aopt@B{bud}", "E", "task", cell, b, Mrel, [N0, c3b], "aopt", [], budget=bud)
                do_task(f"direct@B{bud}", "E", "task", cell, b, Mrel, [N0], "exploit", [], budget=bud)
        for name, pol in POLICY_ARMS.items():
            for cell in batch:
                do_task(name, "E", "task", cell, b, Mrel, base_fits, pol, prog_ids(base_fits))
                do_task(name, "T", "task", cell, b, Mrel, base_fits, pol, prog_ids(base_fits), mask=mask_T)
        dep = libs["inh_kg"].deployed
        # ablations: delete the deployed procedure / the older inherited gates
        del_all = [f for f in base_fits if f.program.kind != "gate"]
        old_fits = base_fits
        if dep is not None and len(dep.gates) >= 2:
            gmax = max(libs["inh_kg"].gates[g].gen for g in dep.gates)
            keep_ids = tuple(g for g in dep.gates if libs["inh_kg"].gates[g].gen == gmax)
            if len(keep_ids) < len(dep.gates):
                p2 = C.Program(dep.pid + "_new", "gate", gates=keep_ids, conj=tuple(c for c in dep.conj if all(x in keep_ids for x in c)))
                gf = C.fit_program(p2, Mrel, libs["inh_kg"].gates)
                old_fits = del_all + ([gf] if gf is not None else [])
        for cell in batch:
            do_task("inh_del_all", "E", "task", cell, b, Mrel, del_all, "kg", [])
            do_task("inh_del_old", "E", "task", cell, b, Mrel, old_fits, "kg", prog_ids(old_fits))
        # ---- static comparators
        N_ = C.fit_program(C.Program("N", "null"), Mrel, {})
        U_ = C.fit_program(C.Program("U", "unexplained"), Mrel, {})
        c3 = C.fit_program(C.Program("C3", "cont", k=3), Mrel, {})
        broad = [N_, U_] + [C.fit_program(C.Program(f"C{k}", "cont", k=k), Mrel, {}) for k in (1, 2, 3, 4, 6)]
        trans = list(broad)
        if dep is not None:
            gf = C.fit_program(dep, Mrel, libs["inh_kg"].gates)
            if gf is not None:
                trans.append(gf)
        t0 = time.perf_counter()
        gbm_E = V.train_gbm(w, st, Mrel, rel, None, S.seed_of("gbmE", sid, b))
        add_seconds("gbm_var", time.perf_counter() - t0)
        gbm_T = V.train_gbm(w, st, Mrel, rel, mask_T, S.seed_of("gbmT", sid, b))
        for cell in batch:
            seed_c = S.seed_of("task", sid, cell)
            for contract, mask in (("E", None), ("T", mask_T)):
                pool = np.ones(st.n, bool) if mask is None else ~mask
                camp0 = w.campaign(cell, 1)
                z1 = Mrel.prior.z1(camp0.Aref, camp0.amin, camp0.amax)
                t0 = time.perf_counter()
                camp = w.campaign(cell, 0, probe_mask=mask)
                nom = C.top_k(np.where(pool, camp.Aref + z1, -np.inf))
                r = realized_utility(w, camp, nom, pool)
                rows.append(task_row("prior", contract, "task", cell, b, r, camp, nom, None, None, "none", [], False, time.perf_counter() - t0))
                if contract == "E":
                    do_task("direct", "E", "task", cell, b, Mrel, [N_], "exploit", [])
                do_task("lat_aopt", contract, "task", cell, b, Mrel, [N_, c3], "aopt", [], mask=mask)
                do_task("lat_var", contract, "task", cell, b, Mrel, [N_, c3], "variance", [], mask=mask)
                do_task("broadcap_bald", contract, "task", cell, b, Mrel, broad, "bald", [], mask=mask)
                do_task("broadcap_transplant", contract, "task", cell, b, Mrel, trans, "bald", prog_ids(trans), mask=mask)
                gm = gbm_E if mask is None else gbm_T
                for pol in ("gbm_var", "gbm_ucb", "gbm_exploit"):
                    if pol == "gbm_exploit" and contract == "T":
                        continue
                    t0 = time.perf_counter()
                    r, camp, nom, tr = V.gbm_campaign(w, st, cell, Mrel, gm, pol, B, contract, mask, seed_c)
                    dt = time.perf_counter() - t0
                    add_seconds(pol, dt)
                    rows.append(task_row(pol, contract, "task", cell, b, r, camp, nom, None, None, pol, [], False, dt))
            # fixed-observation rows for static comparators
            fx = fo_probes(st, mask_T, cell, sid, B)
            for name, fl, pol in (("lat_aopt", [N_, c3], "aopt"), ("broadcap_bald", broad, "bald"), ("broadcap_transplant", trans, "bald")):
                do_task(name, "FO", "task", cell, b, Mrel, fl, pol, prog_ids(fl) if name == "broadcap_transplant" else [], mask=mask_T, fixed=fx)
            r0 = None
            camp0 = w.campaign(cell, 0, probe_mask=mask_T)
            z10 = Mrel.prior.z1(camp0.Aref, camp0.amin, camp0.amax)
            nom0 = C.top_k(np.where(~mask_T, camp0.Aref + z10, -np.inf))
            rows.append(task_row("prior", "FO", "task", cell, b, realized_utility(w, camp0, nom0, ~mask_T), camp0, nom0, None, None, "none", [], False, 0.0))
        # ---- release batch b to every arm; library arms search, validate, deploy/retire, refit
        for name, lib in libs.items():
            mode, pol_adapt = LIB_ARMS[name]
            t0 = time.perf_counter()
            if mode == "inherit":
                rec = S.evolve("inherit", lib, w, st, f"{sid}|{name}", b, list(rel), batch, list(rel) + batch, B, pol_adapt, S.CAND_PER_GEN, search=True)
            elif mode == "restart":
                rec = S.evolve("restart", lib, w, st, f"{sid}|{name}", b, list(rel), batch, list(rel) + batch, B, pol_adapt, S.CAND_PER_GEN * b, search=True)
            else:
                rec = S.evolve("inherit", lib, w, st, f"{sid}|{name}", b, list(rel), batch, list(rel) + batch, B, pol_adapt, S.CAND_PER_GEN, search=(b == 1))
            add_seconds(name, time.perf_counter() - t0)
            gen_records.setdefault(name, []).append(rec)
        rel = rel + batch
        # ---- checkpoint on never-released anchors, with what is actually deployed now (after validation / rollback)
        Mnew = C.build_models(w, rel, st)
        N2 = C.fit_program(C.Program("N", "null"), Mnew, {})
        U2 = C.fit_program(C.Program("U", "unexplained"), Mnew, {})
        c32 = C.fit_program(C.Program("C3", "cont", k=3), Mnew, {})
        broad2 = [N2, U2] + [C.fit_program(C.Program(f"C{k}", "cont", k=k), Mnew, {}) for k in (1, 2, 3, 4, 6)]
        for role, acells in anchors.items():
            for cell in acells:
                for name in ANCHOR_ARMS:
                    t0 = time.perf_counter()
                    if name in libs:
                        lib = libs[name]
                        fits = S.make_fits(lib, Mnew, lib.deployed, lib.gates, lib.rank)
                        do_task(name, "E", role, cell, b, Mnew, fits, lib.policy, prog_ids(fits))
                    elif name == "inh_del_all":
                        lib = libs["inh_kg"]
                        do_task(name, "E", role, cell, b, Mnew, S.make_fits(lib, Mnew, None, None, lib.rank), lib.policy, [])
                    elif name == "prior":
                        camp = w.campaign(cell, 0)
                        z1 = Mnew.prior.z1(camp.Aref, camp.amin, camp.amax)
                        nom = C.top_k(camp.Aref + z1)
                        rows.append(task_row("prior", "E", role, cell, b, realized_utility(w, camp, nom), camp, nom, None, None, "none", [], False, 0.0))
                    elif name == "direct":
                        do_task(name, "E", role, cell, b, Mnew, [N2], "exploit", [])
                    elif name == "lat_aopt":
                        do_task(name, "E", role, cell, b, Mnew, [N2, c32], "aopt", [])
                    else:
                        do_task(name, "E", role, cell, b, Mnew, broad2, "bald", [])
        # the anchors at checkpoint b are tagged with gen=b
        if cfg.get("log", False):
            print(sid, "batch", b, "done", round(time.perf_counter() - t_start, 1), flush=True)
    resources = {"seconds_by_arm": {k: round(v, 3) for k, v in seconds.items()}, "wall_seconds": round(time.perf_counter() - t_start, 3),
                 "candidate_evals": {n: l.n_candidate_evals for n, l in libs.items()}, "validation_replays": {n: l.n_val_replays for n, l in libs.items()},
                 "released_cells": len(rel), "pairs_per_cell": int(st.n), "released_wells": len(rel) * int(st.n), "deployment_probes_per_task": B,
                 "n_task_rows": len(rows)}
    final_libs = {n: l.snapshot() for n, l in libs.items()}
    payload = {"sid": sid, "kind": kind, "seed": seed, "decoupled": decoupled, "budget": B, "schedule": sched, "rows": rows, "generation_records": gen_records,
               "final_libraries": final_libs, "resources": resources}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, default=lambda a: np.asarray(a).tolist())
    mp = out_dir / "models" / f"{sid}.npz"
    mp.parent.mkdir(parents=True, exist_ok=True)
    flat = {}
    for key, d in models.items():
        for k, v in d.items():
            flat[f"{key}|{k}"] = np.asarray(v)
    for key, d in priors.items():
        for k, v in d.items():
            flat[f"prior|{key}|{k}"] = np.asarray(v)
    np.savez_compressed(mp, **flat)
    tmp.replace(out_path)
    return sid, resources


def _job(a):
    kind, seed, dec, out_dir, cfg = a
    try:
        return run_stream(kind, seed, dec, Path(out_dir), cfg)
    except FileExistsError as e:
        return str(e), None


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--kinds", default="null,lowrank,alias,compose")
    ap.add_argument("--seeds", default="1-24")
    ap.add_argument("--decoupled", default="alias,compose")
    ap.add_argument("--procs", type=int, default=26)
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split("-"))
    jobs = [(k, sd, False, a.out, {}) for k in a.kinds.split(",") for sd in range(lo, hi + 1)]
    jobs += [(k, sd, True, a.out, {}) for k in a.decoupled.split(",") if k for sd in range(lo, hi + 1)]
    t0 = time.time()
    with Pool(a.procs) as p:
        for sid, res in p.imap_unordered(_job, jobs):
            print(sid, None if res is None else res["wall_seconds"], round(time.time() - t0, 1), flush=True)
