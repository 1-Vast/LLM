"""Post-freeze stages: api | programs | summary. They read frozen configuration and stored results; none of them changes frozen code."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import svc_evolution as E  # noqa: E402
import svc_programs as P  # noqa: E402
import svc_study as S  # noqa: E402
import svc_summarize as SM  # noqa: E402
import svc_world as W  # noqa: E402
from svc_run import check_frozen, read_json, real_world, write_json  # noqa: E402


def stage_api():
    """Secondary arm: API-proposed typed candidates in the evolution loop (primary real condition, seed 0, one run)."""
    import svc_llm as llm_arm
    fr = check_frozen()
    prim = fr["config"]["primary"]
    contract, B, seed = prim["contract"], prim["budget"], 0
    w = real_world()
    static = w.static
    cells = E.split_cells(w.cells, "real")
    memo, fc = E.Memo(w), {}
    proposer = llm_arm.ApiProposer(static, seed, contract, B)
    lib, inc, recs, final_cells = E.evolve("evo_api", w, memo, static, cells, seed, B, contract, E.REPR_OPS + E.PROC_OPS, inherit=True,
                                           delta_acc=S.DELTA_ACC, fitted_cache=fc, candidate_fn=proposer.candidates)
    hist_all = list(final_cells)
    res = E.evaluate(S.arm_spec_arm(inc["spec"], "evo_api"), w, memo, static, cells["T"], hist_all, B, seed, contract, fitted_cache=fc)
    stored = read_json("REAL_RESULTS.json")
    ref = next(r for r in stored["results"] if r["world_group"] == "oneil" and r["contract"] == contract and r["budget"] == B and r["seed"] == seed)
    api_u = np.array([r["utility"] for r in res])
    out = {"condition": {"contract": contract, "budget": B, "seed": seed}, "api_ledger": proposer.ledger(),
           "generation_records": [{k: v for k, v in r.items() if k != "candidate_specs"} for r in recs], "library": lib.entries, "final_program": inc["id"],
           "test_utility_mean": float(api_u.mean()), "refit_test_mean": float(np.mean(ref["test"]["refit"])), "evo_full_test_mean": float(np.mean(ref["test"]["evo_full"])),
           "paired_vs_refit": SM.describe(api_u - np.array(ref["test"]["refit"])), "paired_vs_evo_full": SM.describe(api_u - np.array(ref["test"]["evo_full"])),
           "accepted_rejected": [{"gen": r["gen"], "accepted": r.get("accepted"), "candidates": r["candidates"]} for r in recs]}
    write_json("API_RESULTS.json", out)
    return out


def stage_summary():
    out = {}
    head = read_json("DEV_HEADROOM.json") if (HERE / "DEV_HEADROOM.json").exists() else None
    for name, key in (("SYNTHETIC_RESULTS.json", "synthetic"), ("REAL_RESULTS.json", "real")):
        if not (HERE / name).exists():
            continue
        data = read_json(name)
        groups = SM.group(data["results"])
        tab = {}
        for (grp, contract, B), rs in sorted(groups.items()):
            tab[f"{grp}|{contract}|B{B}"] = {"n_runs": len(rs), "arm_means": SM.arm_means(rs), "contrasts": SM.contrasts(rs), "anchor_curve": SM.anchor_curve(rs),
                                           "final_programs": [r["final_program"] for r in rs], "accepted_by_generation": [{n: [g.get("accepted") for g in gs] for n, gs in r["generation_records"].items()} for r in rs]}
        out[key] = {"conditions": tab, "compute_seconds": data["compute_seconds"]}
    if "real" in out and head:
        labels = {}
        for row in head["rows"]:
            k = f"oneil|{row['contract']}|B{row['budget']}"
            kc = f"oneil_anchor_only|{row['contract']}|B{row['budget']}"
            conds = out["real"]["conditions"]
            c = conds.get(k, {}).get("contrasts", {}).get("C_full_loop:evo_full-refit")
            cc = conds.get(kc, {}).get("contrasts", {}).get("C_full_loop:evo_full-refit")
            delta = 0.25 * row["headroom_after_best_baseline"]
            opp = row["headroom_after_best_baseline"] >= 0.005
            labels[k] = {"delta_use": delta, "headroom": row["headroom_after_best_baseline"], "contrast": c, "control": cc,
                         "label": SM.label(c, delta, cc) if opp else "NO_DECISION_OPPORTUNITY"}
        out["labels"] = labels
        out["primary_condition"] = f"oneil|{head['primary']['contract']}|B{head['primary']['budget']}"
    write_json("SUMMARY.json", out)
    return out

NL = chr(10)


def stage_programs():
    """Serialise the primary-condition programs with ancestry; reload them and record a prediction-equality receipt (refits one program, uses no new outcomes beyond the exported environment)."""
    fr = check_frozen()
    prim = fr["config"]["primary"]
    stored = read_json("REAL_RESULTS.json")
    run = next(r for r in stored["results"] if r["world_group"] == "oneil" and r["contract"] == prim["contract"] and r["budget"] == prim["budget"] and r["seed"] == 0)
    outdir = HERE / "PROGRAMS"
    outdir.mkdir(exist_ok=True)
    w = real_world()
    static = w.static
    cells = E.split_cells(w.cells, "real")
    hist_cells = cells["H0"] + cells["D1"] + cells["D2"] + cells["D3"]
    hist = w.history(hist_cells)
    cache = P.HistoryCache(hist)
    receipts = {}
    for arm, entries in run["library"].items():
        ids = {e["id"]: e for e in entries}
        lib_doc = {"arm": arm, "condition": {k: run[k] for k in ("contract", "budget", "seed")}, "final_program": run["final_program"][arm], "programs": []}
        for e in entries:
            lib_doc["programs"].append({**e, "omega": E.omega_of(e, static), "ancestry": lineage(ids, e["id"])})
        (outdir / f"library_{arm}.json").write_text(json.dumps(lib_doc, indent=1, default=float) + NL, encoding="utf-8")
        final_id = run["final_program"][arm]
        spec = ids[final_id]["spec"]
        fit = P.fit_program(spec, hist, cache, static, prim["budget"], 0, transfer=False)
        doc = fit.to_json()
        path = outdir / f"fitted_{arm}_{final_id}.json"
        path.write_text(json.dumps(doc) + NL, encoding="utf-8")
        reloaded = P.Fitted.from_json(json.loads(path.read_text(encoding="utf-8")))
        cell = cells["T"][0]
        rec = {}
        for tag, f in (("original", fit), ("reloaded", reloaded)):
            camp = w.campaign(cell, prim["budget"])
            out = P.run_program(f, static, camp, np.random.default_rng(1))
            rec[tag] = {"nominated": out["nominated"], "pred_sha256": hashlib.sha256(np.round(out["final_prediction"], 12).tobytes()).hexdigest()}
        rec["equal"] = rec["original"] == rec["reloaded"]
        rec["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        rec["history_version"] = fit.history_version
        receipts[f"{arm}:{final_id}"] = rec
    write_json("SERIALIZATION_RECEIPT.json", {"note": "fitted for contract E (no probe mask); the transfer contract refits per held-out cell from the same spec", "receipts": receipts})
    return receipts


def lineage(ids, pid):
    chain = []
    while pid is not None:
        e = ids[pid]
        chain.append({"id": pid, "op": e["op"], "gen": e["gen"], "status": e["status"]})
        pid = e["parent"]
    return chain[::-1]


def stage_example():
    """Worked example: two released-to-test backgrounds, two competing programs, predictions recorded before the probes."""
    fr = check_frozen()
    prim = fr["config"]["primary"]
    contract, B = prim["contract"], prim["budget"]
    stored = read_json("REAL_RESULTS.json")
    run = next(r for r in stored["results"] if r["world_group"] == "oneil" and r["contract"] == contract and r["budget"] == B and r["seed"] == 0)
    w = real_world()
    static = w.static
    cells = E.split_cells(w.cells, "real")
    hist_cells = cells["H0"] + cells["D1"] + cells["D2"] + cells["D3"]
    hist = w.history(hist_cells)
    cache = P.HistoryCache(hist)
    lib = run["library"]["evo_full"]
    final_id = run["final_program"]["evo_full"]
    final = next(e for e in lib if e["id"] == final_id)
    competing = {"refit": P.base_spec()}
    if final["parent"] is not None:
        competing["final_evo_full"] = final["spec"]
    else:                                                          # nothing retained: contrast with the best REJECTED candidate of generation 1
        cands = run["generation_records"]["evo_full"][0]["candidates"]
        if cands:
            competing["rejected_best_candidate"] = max(cands, key=lambda c: c["gain"])["spec"]
    out = {"condition": {"contract": contract, "budget": B, "seed": 0}, "incumbent": final_id, "cells": []}
    for cell in cells["T"][:2]:
        probe, pool = E.task_masks(static, cell, 0, contract)
        entry = {"cell": cell, "programs": {}}
        for name, spec in competing.items():
            if spec is None:
                continue
            fit = P.fit_program(spec, hist, cache, static, B, 0, transfer=(contract == "T"), probe_mask=probe)
            camp = w.campaign(cell, B, probe_mask=probe)
            prior = camp.Aref + cache.full.z1(camp.Aref, camp.amin, camp.amax)
            pre = [int(p) for p in W.shortlist(prior, pool, W.SHORTLIST_K)]
            res = P.run_program(fit, static, camp, np.random.default_rng(E.stable_int("run", cell, 0)), pool_mask=pool, transfer=(contract == "T"))
            u_pre = W.realized_utility(w, w.campaign(cell, 0), pre, pool)["utility"]
            u_post = W.realized_utility(w, camp, res["nominated"], pool)["utility"]
            entry["programs"][name] = {"spec": spec, "recorded_before_query": {"shortlist": [static.pair_names[p] for p in pre], "predicted_utility": float(prior[pre].mean())},
                                       "measurement_plan": [{"stage": s["stage"], "n": s["n"]} for s in res["stage_log"]],
                                       "probed_pairs": [static.pair_names[p] for p in res["probed"]],
                                       "state_after_probes": [float(v) for v in res["z"]], "state_entries": P.entries_of(spec),
                                       "shortlist_after": [static.pair_names[p] for p in res["nominated"]], "predicted_utility_after": float(res["final_prediction"][res["nominated"]].mean()),
                                       "pairs_changed_by_the_probes": len(set(pre) - set(res["nominated"])),
                                       "realized_utility_before_state_update": u_pre, "realized_utility_after": u_post}
        out["cells"].append(entry)
    write_json("WORKED_EXAMPLE.json", out)
    return out


if __name__ == "__main__":
    stage = sys.argv[1]
    {"api": stage_api, "programs": stage_programs, "example": stage_example, "summary": stage_summary}[stage]()
