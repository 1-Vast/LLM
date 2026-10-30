"""Stream runner. One stream = one synthetic world, 4 generations (checkpoints 0..3), every arm on identical backgrounds, query tables, budgets and shortlist rule.

Write-once outputs per stream: streams/<sid>.json.gz (every campaign row with its complete query/observation log, every generation record, resource meters, plan artifacts)
and models/<sid>.npz (every fitted library and student exactly as deployed). Phase 2 (`run_xplant`) evaluates the plan-transplant arm from the partner stream's saved plans.
Arms (all share pi_model's response family): prior, exploit | f0_kg1 f1_kg1 f1_kg2 f1_distill | f0_plan f1_plan f1_plan_re f1_plan_nobranch | f1_plan_xplant (phase 2).
f0/f1 = response-factor inheritance OFF/ON. Plan arms inherit an executable plan (ON) or rebuild it every generation (re = restart).
"""
from __future__ import annotations

import gzip
import json
import time
from pathlib import Path

import numpy as np

import pi_factors as F
import pi_model as M
import pi_plan as PL
import pi_world as W

HERE = Path(__file__).resolve().parent
BUDGETS = (3, 4)
ANCHOR_B = 4
ARMS = ["prior", "exploit", "f0_kg1", "f1_kg1", "f1_kg2", "f1_distill", "f0_plan", "f1_plan", "f1_plan_re", "f1_plan_nobranch"]
XARMS = ["f1_plan_xplant"]


def sid_of(kind, seed):
    return f"{kind}_{seed}"


def _j(obj):
    def conv(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    return json.dumps(obj, default=conv)


def write_gz(path, obj):
    path = Path(path)
    if path.exists():
        raise SystemExit(f"{path} exists: outputs are write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(_j(obj))


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def campaign_for(stream, bg, arm_lib, agent, B, arm, tag):
    d = stream["bgs"][bg]
    camp = M.Camp(d["a"], d["y"], T=d["T"])
    row = M.run_campaign(arm_lib, camp, B, agent, arm=arm, tag=dict(tag, bg=int(bg), B=int(B), regime=int(d["regime"])))
    return row


def arm_agents(arm, c, B, state):
    """(library, agent) for an arm at checkpoint c, budget B."""
    on, off = state["lib_on"], state["lib_off"]
    if arm == "prior":
        return None, M.Exploit(), 0
    if arm == "exploit":
        return None, M.Exploit(), B
    if arm == "f0_kg1":
        return off, M.Kg1(), B
    if arm == "f1_kg1":
        return on, M.Kg1(), B
    if arm == "f1_kg2":
        return on, M.Kg2(), B
    if arm == "f1_distill":
        st = state["student"]
        return on, (st if st is not None else M.Kg1()), B
    if arm in ("f0_plan", "f1_plan", "f1_plan_re", "f1_plan_nobranch"):
        pl = {"f0_plan": state["plan_f0"][B], "f1_plan": state["plan_on"][B], "f1_plan_re": state["plan_re"][B],
              "f1_plan_nobranch": None if state["plan_on"][B] is None else state["plan_on"][B].collapsed()}[arm]
        return (off if arm == "f0_plan" else on), (pl if pl is not None else M.Kg1()), B
    raise ValueError(arm)


def run_stream(kind, seed, out_dir, smoke=False):
    out_dir = Path(out_dir)
    sid = sid_of(kind, seed)
    sp, mp = out_dir / "streams" / f"{sid}.json.gz", out_dir / "models" / f"{sid}.npz"
    if sp.exists() or mp.exists():
        raise SystemExit(f"{sid}: outputs exist; write-once")
    t_wall, t_cpu = time.perf_counter(), time.process_time()
    stream = W.make_stream(kind, seed)
    sc = stream["schedule"]
    rows, gens, arrays, plans_json = [], [], {}, {}
    meters = {"factors_on": 0.0, "factors_off": 0.0, "plan_f1_plan": 0.0, "plan_f0_plan": 0.0, "plan_f1_plan_re": 0.0, "distill_teacher": 0.0, "distill_fit_total": 0.0,
              "anchors": 0.0, "tasks": 0.0}
    counts = {"cand_factors_on": 0, "cand_factors_off": 0, "cand_f1_plan": 0, "cand_f0_plan": 0, "cand_f1_plan_re": 0, "replays_factors_on": 0, "replays_factors_off": 0,
              "replays_f1_plan": 0, "replays_f0_plan": 0, "replays_f1_plan_re": 0, "teacher_decisions": 0}
    prev_on = None
    inc = {"plan_on": {B: None for B in BUDGETS}, "plan_f0": {B: None for B in BUDGETS}}
    arch = {"plan_on": {B: [] for B in BUDGETS}, "plan_f0": {B: [] for B in BUDGETS}}
    teacher_cache = {}
    for c in range(4):
        ids = sc["H0"] + [i for b in sc["batches"][:c] for i in b]
        E, A, Y = W.released_residuals(stream, ids)
        t = time.process_time()
        fon = F.learn("on", prev_on, E, A, ids)
        meters["factors_on"] += time.process_time() - t
        t = time.process_time()
        fof = F.learn("off", None, E, A, ids)
        meters["factors_off"] += time.process_time() - t
        prev_on = fon["labels"]
        counts["cand_factors_on"] += fon["n_candidates"]
        counts["cand_factors_off"] += fof["n_candidates"]
        counts["replays_factors_on"] += fon["n_replays"]
        counts["replays_factors_off"] += fof["n_replays"]
        lab_on = np.array([fon["labels"][i] for i in ids])
        lab_off = np.array([fof["labels"][i] for i in ids])
        val_ids = sc["batches"][c - 1] if c >= 1 else sc["H0"][4:]
        state = {"lib_on": fon["lib"], "lib_off": fof["lib"], "plan_on": {}, "plan_f0": {}, "plan_re": {}}
        grec = {"ckpt": c, "released": [int(i) for i in ids], "val_ids": [int(i) for i in val_ids],
                "factors": {"on": {k: fon[k] for k in ("records", "n_candidates", "n_replays", "cpu_s", "n_regimes")},
                            "off": {k: fof[k] for k in ("records", "n_candidates", "n_replays", "cpu_s", "n_regimes")}},
                "lib_on_fp": fon["lib"].fingerprint(), "lib_off_fp": fof["lib"].fingerprint(), "plans": {}}
        for pre, lib_, lab_ in (("on", fon["lib"], lab_on), ("off", fof["lib"], lab_off)):
            arrays.update({f"{pre}|{c}|{k}": v for k, v in lib_.arrays().items()})
        for B in BUDGETS:
            for arm, mode, lib_, lab_, key in (("f1_plan", "on", fon["lib"], lab_on, "plan_on"), ("f0_plan", "on", fof["lib"], lab_off, "plan_f0"),
                                               ("f1_plan_re", "restart", fon["lib"], lab_on, None)):
                t = time.process_time()
                incumbent = inc[key][B] if key else None
                archive = arch[key][B] if key else []
                pl, new_arch, rec = PL.learn_plan(mode, lib_, lab_, ids, E, A, Y, B, val_ids, incumbent, archive)
                meters[f"plan_{arm}"] += time.process_time() - t
                counts[f"cand_{arm}"] += rec["n_candidates"]
                counts[f"replays_{arm}"] += rec["n_replays"]
                if key:
                    inc[key][B], arch[key][B] = pl, new_arch
                    state[key][B] = pl
                else:
                    state["plan_re"][B] = pl
                grec["plans"][f"{arm}|{B}"] = rec
                plans_json[f"{arm}|{c}|{B}"] = None if pl is None else pl.to_json()
        # amortised-policy baseline: teacher = two-step lookahead on all released backgrounds under the deployed library
        A_d = {int(i): A[r] for r, i in enumerate(ids)}
        R_d = {int(i): Y[r] for r, i in enumerate(ids)}
        t = time.process_time()
        st, trows, cpu_t, ndec = PL.train_student(fon["lib"], A_d, R_d, ids)
        meters["distill_teacher"] += time.process_time() - t
        counts["teacher_decisions"] += ndec
        state["student"] = st
        grec["student"] = None if st is None else {"sha": st.sha, "cpu_s": cpu_t, "teacher_decisions": ndec}
        if st is not None:
            arrays.update(st.arrays(f"stu|{c}|"))
        # anchors (retention): never-released old-regime backgrounds, deployed state only, B=4, logged but never used for fitting
        t = time.process_time()
        for arm in ARMS:
            if arm in ("prior", "exploit"):
                continue
            lib_, agent, Bu = arm_agents(arm, c, ANCHOR_B, state)
            for bg in sc["A_old"][c]:
                rows.append(campaign_for(stream, bg, lib_, agent, Bu, arm, {"role": "anchor", "ckpt": c, "batch": 0, "contract": "E", "budget_arm": ANCHOR_B}))
        meters["anchors"] += time.process_time() - t
        # tasks of batch c+1
        t = time.process_time()
        for arm in ARMS:
            for B in BUDGETS:
                lib_, agent, Bu = arm_agents(arm, c, B, state)
                for bg in sc["batches"][c]:
                    rows.append(campaign_for(stream, bg, lib_, agent, Bu, arm, {"role": "task", "ckpt": c, "batch": c + 1, "contract": "E", "budget_arm": B}))
        meters["tasks"] += time.process_time() - t
        gens.append(grec)
    res = {"wall_s": time.perf_counter() - t_wall, "cpu_s": time.process_time() - t_cpu, "meters": meters, "counts": counts}
    obj = {"sid": sid, "kind": kind, "seed": seed, "rows": rows, "generations": gens, "plans": plans_json, "resources": res, "schedule": sc,
           "regimes": {int(i): int(stream["bgs"][i]["regime"]) for i in stream["bgs"]}}
    mp.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(mp, **arrays)
    write_gz(sp, obj)
    return obj


def run_xplant(kind, seed, partner_seed, out_dir):
    out_dir = Path(out_dir)
    sid = sid_of(kind, seed)
    path = out_dir / "streams" / f"{sid}.xplant.json.gz"
    if path.exists():
        raise SystemExit(f"{path} exists; write-once")
    own = read_gz(out_dir / "streams" / f"{sid}.json.gz")
    partner = read_gz(out_dir / "streams" / f"{sid_of(kind, partner_seed)}.json.gz")
    z = np.load(out_dir / "models" / f"{sid}.npz", allow_pickle=False)
    stream = W.make_stream(kind, seed)
    sc = stream["schedule"]
    rows, t0 = [], time.process_time()
    for c in range(4):
        lib = M.Lib.from_arrays(z, f"on|{c}|")
        for B in BUDGETS:
            pj = partner["plans"].get(f"f1_plan|{c}|{B}")
            pl = None if pj is None else PL.Plan.from_json(pj, force=True)
            for bg in sc["batches"][c]:
                row = campaign_for(stream, bg, lib, pl if pl is not None else M.Kg1(), B, "f1_plan_xplant", {"role": "task", "ckpt": c, "batch": c + 1, "contract": "E", "budget_arm": B,
                                                                                                                 "transplant_from": sid_of(kind, partner_seed)})
                rows.append(row)
    write_gz(path, {"sid": sid, "partner": sid_of(kind, partner_seed), "rows": rows, "cpu_s": time.process_time() - t0})
