"""Strict verifier: exit 1 on any missing evidence or inconsistency; INCOMPLETE if mandatory files are absent.

Checks: source freeze and config; predecessor-package preservation; stream/arm/budget/checkpoint coverage; every logged read equals the world's recorded read and every utility is
recomputed from the world truth; query legality; library identity (every row names the fingerprint of the stored library for its arm and checkpoint); EVERY campaign row
(tasks, anchors, transplants) is re-executed from the stored library / plan JSON / student arrays against its own logged reads and must reproduce the same queries and nominations;
plan artifact identity (content + history hashes); lifecycle statuses re-derived from stored comparisons; candidate caps; resource sums; the stage ledger; and the summary is recomputed
from the stored run files. Usage: python pi_verify.py [RUN_DIR] [--allow-subset]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
REQUIRED = ["CONFIG.json", "FREEZE.json", "PROTOCOL.md", "REPORT.md", "SUMMARY.json", "PRESERVED_BEFORE.json", "INVENTORY_CHECK.json", "RUN/LEDGER.json"]
EPS = 1e-9


def agent_for(arm, c, B, z, plans, partner_plans, M, PL):
    on = M.Lib.from_arrays(z, f"on|{c}|")
    off = M.Lib.from_arrays(z, f"off|{c}|")

    def plan(key, src=plans, force=False):
        pj = src.get(key)
        return None if pj is None else PL.Plan.from_json(pj, force=force)
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
        st = PL.Student.from_arrays(z, f"stu|{c}|", on.fingerprint()) if f"stu|{c}|left" in z.files else None
        return on, (st if st is not None else M.Kg1()), B
    if arm in ("f0_plan", "f1_plan", "f1_plan_re"):
        pl = plan(f"{arm}|{c}|{B}")
        return (off if arm == "f0_plan" else on), (pl if pl is not None else M.Kg1()), B
    if arm == "f1_plan_nobranch":
        pl = plan(f"f1_plan|{c}|{B}")
        return on, (pl.collapsed() if pl is not None else M.Kg1()), B
    if arm == "f1_plan_xplant":
        pl = plan(f"f1_plan|{c}|{B}", partner_plans, force=True)
        return on, (pl if pl is not None else M.Kg1()), B
    raise ValueError(arm)


def verify(run_dir, here=HERE, subset=False):
    import pi_freeze as FZ
    import pi_model as M
    import pi_plan as PL
    import pi_run as R
    import pi_stats as ST
    import pi_world as W
    problems = []

    def need(cond, msg):
        if not cond:
            problems.append(msg)
    run_dir = Path(run_dir)
    missing = [f for f in REQUIRED if not (here / f).exists()] if not subset else []
    if not list((run_dir / "streams").glob("*.json.gz")):
        missing.append("RUN/streams/*.json.gz")
    if missing:
        return ["missing mandatory evidence: " + m for m in missing], {}
    cfg = json.loads((here / "CONFIG.json").read_text(encoding="utf-8")) if (here / "CONFIG.json").exists() else {}
    if not subset:
        problems += FZ.check()
        frozen = json.loads((here / "FREEZE.json").read_text(encoding="utf-8"))
        need(frozen["config"] == cfg, "CONFIG.json differs from the frozen configuration")
        problems += FZ.preserve_check()
        led = json.loads((run_dir.parent / "LEDGER.json").read_text(encoding="utf-8"))
        for stage in ("eval", "xplant"):
            need(stage in led, f"stage '{stage}' missing from the ledger")
    streams, xp = ST.load(run_dir)
    expected = {f"{k}_{s}" for k in cfg["streams"]["kinds"] for s in cfg["streams"]["seeds"]} if not subset else set(streams)
    need(set(streams) == expected, f"stream coverage: missing {sorted(expected - set(streams))}, unexpected {sorted(set(streams) - expected)}")
    need(set(xp) == set(streams), "transplant coverage differs from the stream set")
    stats = {"rows_replayed": 0, "plan_rows": 0}
    cap = cfg["budget"]["cap_candidates_per_generation"] if cfg else 12
    wall = 0.0
    for sid, d in streams.items():
        stream = W.make_stream(d["kind"], d["seed"])
        sc = stream["schedule"]
        z = np.load(run_dir / "models" / f"{sid}.npz", allow_pickle=False)
        partner = None
        if sid in xp:
            partner = next((o for o in streams.values() if o["kind"] == d["kind"] and o["seed"] != d["seed"]), None)
            need(partner is not None and xp[sid]["partner"] == partner["sid"], f"{sid}: transplant partner mismatch")
        rows = d["rows"] + (xp[sid]["rows"] if sid in xp else [])
        seen = set()
        fps = {(c, m): M.Lib.from_arrays(z, f"{m}|{c}|").fingerprint() for c in range(4) for m in ("on", "off")}
        # ---- generation records
        need(len(d["generations"]) == 4, f"{sid}: generations != 4")
        for g in d["generations"]:
            c = g["ckpt"]
            need(g["lib_on_fp"] == fps[(c, "on")] and g["lib_off_fp"] == fps[(c, "off")], f"{sid}/ckpt{c}: stored library fingerprint disagrees with the record")
            for m in ("on", "off"):
                f = g["factors"][m]
                need(f["n_candidates"] <= cap, f"{sid}/ckpt{c}/factors_{m}: {f['n_candidates']} candidates exceed {cap}")
                need(f["n_candidates"] == len(f["records"]), f"{sid}/ckpt{c}/factors_{m}: candidate count differs from records")
                for r in f["records"]:
                    ok = r["gain"] >= cfg["lifecycle"]["eps_val"] and r["wins"] > r["losses"] and r["wins"] >= 2
                    need((r["status"] == "demonstrated") == ok, f"{sid}/ckpt{c}/factors_{m}: status disagrees with the library promotion rule")
            for key, r in g["plans"].items():
                need(r["n_candidates"] <= cap, f"{sid}/ckpt{c}/{key}: {r['n_candidates']} candidates exceed {cap}")
                need(r["n_candidates"] == len(r["candidates"]), f"{sid}/ckpt{c}/{key}: candidate count differs from records")
                if r["status"] == "demonstrated":
                    v = r["vs_incumbent"]
                    need(v["gain"] >= cfg["lifecycle"]["eps_val"] and v["wins"] > v["losses"] and v["wins"] >= 1, f"{sid}/ckpt{c}/{key}: promoted without meeting the plan rule")
                arm, B = key.split("|")
                pj = d["plans"].get(f"{arm}|{c}|{B}")
                need((pj is None) == (r["deployed"] is None), f"{sid}/ckpt{c}/{key}: deployment record differs from the stored plan artifact")
                if pj is not None:
                    need(pj["pid"] == r["deployed"], f"{sid}/ckpt{c}/{key}: stored plan id differs from the deployed id")
                    try:
                        PL.Plan.from_json(pj)
                    except AssertionError as e:
                        problems.append(f"{sid}/ckpt{c}/{key}: {e}")
                    need(pj["history"]["lib_fp"] == (fps[(c, "off")] if arm == "f0_plan" else fps[(c, "on")]), f"{sid}/ckpt{c}/{key}: plan bound to a library other than the deployed one")
        # ---- every row
        for r in rows:
            where = f"{sid}/{r['arm']}/B{r['budget_arm']}/{r['role']}/bg{r['bg']}"
            key = (r["arm"], r["role"], r["budget_arm"], r["bg"], r["ckpt"])
            need(key not in seen, f"{where}: duplicated row")
            seen.add(key)
            qs = r["queries"]
            bg = stream["bgs"][r["bg"]]
            need(len({q[0] for q in qs}) == len(qs) == r["n_spent"], f"{where}: query log inconsistent with n_spent")
            need(r["n_spent"] <= (0 if r["arm"] == "prior" else r["budget_arm"]), f"{where}: spent above the budget")
            need(all(bg["y"][p] == y for p, y in qs), f"{where}: a logged read differs from the world's recorded read")
            nom = r["nominated"]
            need(len(nom) == len(set(nom)) == M.K_SHORT and all(0 <= q < W.P for q in nom), f"{where}: nominations not 5 unique valid pairs")
            need(abs(float(np.mean(bg["T"][nom])) - r["utility"]) < EPS and abs(float(np.sort(bg["T"])[-5:].mean()) - r["oracle"]) < EPS, f"{where}: utility/oracle not reproduced from the world")
            if r["role"] == "task":
                need(r["bg"] in sc["batches"][r["batch"] - 1], f"{where}: task background not in its batch")
            else:
                need(r["bg"] in sc["A_old"][r["ckpt"]], f"{where}: anchor not in its checkpoint set")
            # identity + replay from stored artifacts and logged reads only
            part = partner["plans"] if (partner and r["arm"] == "f1_plan_xplant") else {}
            try:
                lib, agent, Bu = agent_for(r["arm"], r["ckpt"], r["budget_arm"], z, d["plans"], part, M, PL)
            except AssertionError as e:
                need(False, f"{where}: stored artifact rejected ({e})")
                continue
            exp_fp = None if lib is None else lib.fingerprint()
            need(r["lib_fp"] == exp_fp, f"{where}: row used library {r['lib_fp']} but the stored library is {exp_fp}")
            ytab = np.full(W.P, np.nan)
            for p, y in qs:
                ytab[p] = y
            camp = M.Camp(bg["a"], ytab, T=None)
            try:
                rr = M.run_campaign(lib, camp, Bu, agent, arm=r["arm"])
            except KeyError:
                need(False, f"{where}: replay requested a read that was not logged")
                continue
            need(rr["queries"] == qs and rr["nominated"] == nom, f"{where}: replay from the stored artifact does not reproduce the logged queries/nominations")
            need(rr.get("plan_id") == r.get("plan_id") and rr.get("branch") == r.get("branch"), f"{where}: plan id / branch differs on replay")
            stats["rows_replayed"] += 1
            if r["arm"] == "f1_plan" and r.get("plan_applicable"):
                stats["plan_rows"] += 1
        # per-stream coverage: every arm covers every later task in each budget and every anchor
        arms = R.ARMS + R.XARMS
        for arm in arms:
            for B in R.BUDGETS if arm not in ("prior",) else R.BUDGETS:
                have = {r["bg"] for r in rows if r["arm"] == arm and r["role"] == "task" and r["budget_arm"] == B}
                need(have == {i for b in sc["batches"] for i in b}, f"{sid}: arm {arm} B{B} does not cover all 16 task backgrounds")
            if arm not in ("prior", "exploit", "f1_plan_xplant"):
                have = {r["bg"] for r in rows if r["arm"] == arm and r["role"] == "anchor"}
                need(have == {i for b in sc["A_old"] for i in b}, f"{sid}: arm {arm} does not cover the retention anchors")
        res = d["resources"]
        need(res["counts"]["cand_f1_plan"] == sum(g["plans"][f"f1_plan|{B}"]["n_candidates"] for g in d["generations"] for B in R.BUDGETS), f"{sid}: f1_plan candidate total inconsistent")
        need(res["counts"]["cand_factors_on"] == sum(g["factors"]["on"]["n_candidates"] for g in d["generations"]), f"{sid}: factor candidate total inconsistent")
        need(sum(res["meters"].values()) <= res["cpu_s"] + 1e-6, f"{sid}: metered CPU exceeds total process CPU")
        wall += res["wall_s"] + 0.0
    wall_total = wall + sum(x["cpu_s"] for x in xp.values())
    if cfg:
        need(wall_total <= cfg["budget"]["elapsed_minutes"] * 60, f"elapsed {wall_total / 60:.1f} min exceeds the {cfg['budget']['elapsed_minutes']} minute ceiling")
    if not subset:
        fresh = ST.build_summary(run_dir)
        stored = json.loads((here / "SUMMARY.json").read_text(encoding="utf-8"))
        diff = ST.diff_summaries(fresh, stored)
        need(not diff, f"SUMMARY.json is not reproduced from the stored run files: {diff[:5]}")
    stats["elapsed_s"] = wall_total
    return list(dict.fromkeys(problems)), stats


def main(argv=None):
    a = argv or sys.argv[1:]
    run = Path(a[0]) if a and not a[0].startswith("--") else HERE / "RUN" / "eval"
    problems, stats = verify(run, subset="--allow-subset" in a)
    if problems:
        print("VERIFY FAILED:" if stats else "VERIFY INCOMPLETE:")
        for p in problems[:40]:
            print(" -", p)
        return 1
    print(f"VERIFY OK: {stats['rows_replayed']} rows re-executed from stored artifacts, {stats['plan_rows']} applicable plan invocations, elapsed {stats['elapsed_s'] / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
