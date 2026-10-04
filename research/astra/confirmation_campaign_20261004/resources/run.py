"""Resources workstream driver: custom and native frontiers with stopping, accounting and scheduler headroom.

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/run.py
- Purpose: execute `resources/plan.json`. Stage `hd` (allowed before design/selection.json): HD
  development targets only (history = other HD lines), every predictor, design-independent frontier
  over the contract fp grid. Stage `eval` (only after design/selection.json exists; its sha256 is
  recorded): E targets (history = all HD lines), every predictor plus the selected C* and fp*.
- Core points:
  - Outcomes only through `common.exposed_ticket(purpose, "resources")` and the frozen
    `jaaks.build_panels`; the design-derived menu is asserted equal to the builder's.
  - Custom frontier: P1/P2/P3 (contract v2) at cap percent cp in {10, 20, 30, 40} (cp = 20 is the
    contract cap), measurement cap; wells cap at cp = 20; spend-all REFERENCE variants (terminal
    screens) at cp = 20 to show what stopping saves. Accounting per campaign (`account_custom`).
  - Native frontier: N1/N2/N3 at caps of {5..100}% of the line's menu-relevant release plates.
  - Scheduler headroom: verification capacity binding, unused cap at stop, per-campaign hindsight
    split, screen-vs-verify index crossings including the pipeline diagnostic p_sv/(c_s + p_s c_v),
    round-2 oracle screens under P3.
  - Results go to resources/results/<stage>_<timestamp>/ (never overwritten).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.resources.run --stage hd|eval
  [--dry DIR] [--workers N]`.
- Depends on: numpy, pandas; frozen jaaks builder; common.py; layout/frontier/native modules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from research.astra.feedback_validation_20261003 import jaaks
from research.certified_discovery.screens import sha256

from . import frontier as fr
from . import native as nt
from .layout import CONTROL_VARIANTS, MIN_DAYS_PER_ROUND, build_layout, check_against_panels

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
SELECTION = STUDY / "design/selection.json"
STATUS = ("EXPLORATORY: Jaaks et al. 2022 was opened by feedback_validation_20261003; resources frontier and "
          "accounting replay under campaign contract v2; no verdict")
CUSTOM_CP = (10, 20, 30, 40)
HEADROOM_PREDS = ("S", "S_both", "R")
TAU = 0.05
CHOICE_FREQUENCY_MIN = 0.10

_LAYOUT = None


# ---------------------------------------------------------------------------- per-unit work
def _flat_custom(acc: dict) -> dict:
    t = acc["total"]
    out = {k: t[k] for k in fr.BASIC}
    for name in CONTROL_VARIANTS:
        c = t[f"custom_{name}"]
        out[f"plates_{name}"] = c["plates"]
        out[f"control_wells_{name}"] = c["control_wells"]
        out[f"single_agent_wells_{name}"] = c["single_anchor_wells"] + c["single_library_wells"]
        out[f"empty_wells_{name}"] = c["empty_wells"]
        out[f"joint_plates_{name}"] = acc["custom_joint_plates_diagnostic"][name]
    for b in ("screen", "verify"):
        x = acc["by_branch"][b]
        out[f"{b}_plates_documented_200"] = x["custom_documented_200"]["plates"]
        out[f"{b}_combination_wells"] = x["combination_wells"]
        out[f"{b}_native_plates_touched"] = x["native_plates_touched"]
    return out


CAMPAIGN_FIELDS = ("cap", "spent", "unused_cap", "screens", "screen_hits", "verifications", "verification_hits",
                   "confirmed", "joint_hits_menu", "missed_never_screened", "missed_screened_not_verified",
                   "unverified_screen_hits", "final_round_screens", "final_round_screen_hits", "rounds_used",
                   "last_round", "min_days", "screen_units", "verify_units")


def custom_configs(preds):
    for pred in preds:
        for cp in CUSTOM_CP:
            yield (pred, 1, None, "measurement", cp, False)
            for fp in fr.FP_GRID:
                yield (pred, 2, fp, "measurement", cp, False)
            yield (pred, 3, None, "measurement", cp, False)
        yield (pred, 1, None, "wells", 20, False)
        for fp in fr.FP_GRID:
            yield (pred, 2, fp, "wells", 20, False)
            yield (pred, 2, fp, "measurement", 20, True)
        yield (pred, 3, None, "wells", 20, False)
        yield (pred, 3, None, "measurement", 20, True)


def native_configs(preds, caps):
    for pred in preds:
        for pct, K in caps.items():
            yield (pred, 1, None, pct, K)
            for fp in fr.FP_GRID:
                yield (pred, 2, fp, pct, K)
            yield (pred, 3, None, pct, K)


def _headroom(u: fr.Unit, pred: str) -> dict:
    """Decision-headroom diagnostics of one campaign (outcome-aware bounds are labelled oracle)."""
    joint = u.hidden.hit_s & u.hidden.hit_v
    M = u.cap(20)
    out = {"p2": {}, "p3": {}}
    for fp in fr.FP_GRID:
        rec = fr.run_custom(u, pred, 2, fp=fp)
        r1 = rec["screens_ordered"]
        cap_v = M - rec["n1"]
        hits1 = rec["screen_hits"]
        joint1 = int(sum(joint[i] for i in r1))
        out["p2"][fp] = {"confirmed": rec["confirmed"], "hits1": hits1, "cap_v": cap_v,
                         "binding": int(hits1 > cap_v), "excess": max(0, hits1 - cap_v),
                         "unused": rec["unused_cap"], "stop_with_unused": int(rec["unused_cap"] > 0),
                         "oracle_verify_confirmed": min(joint1, cap_v), "n1_zero": int(rec["n1"] == 0)}
    rec = fr.run_custom(u, pred, 3)
    n2 = rec["per_round"][1]["screens"] if len(rec["per_round"]) > 1 else 0
    orc = fr.run_custom(u, pred, 3, round2_screen_score=joint.astype(float), round2_count=n2)
    r1 = set(rec["screens_ordered"][:rec["n1"]])
    pending = [i for i in r1 if u.hidden.hit_s[i]]
    unscreened = [i for i in range(u.n) if i not in r1]
    cap_after_r1 = M - rec["n1"]
    res = rec["reserve"] or {}
    cross = {}
    for kind in ("measurement", "wells"):
        cs = np.ones(u.n) if kind == "measurement" else 14.0 * u.plates_s
        cv = np.ones(u.n) if kind == "measurement" else 14.0 * u.plates_v
        if pending and unscreened:
            v_min = min(u.p_vs[j] / cv[j] for j in pending)
            s_max = max(u.p_sv[i] / cs[i] for i in unscreened)
            pipe_max = max(u.p_sv[i] / (cs[i] + u.p_s[i] * cv[i]) for i in unscreened)
            cross[kind] = {"index": int(s_max > v_min), "pipeline": int(pipe_max > v_min),
                           "v_min": float(v_min), "s_max": float(s_max), "pipe_max": float(pipe_max)}
        else:
            cross[kind] = {"index": 0, "pipeline": 0, "v_min": None, "s_max": None, "pipe_max": None}
    r2 = rec["per_round"][1] if len(rec["per_round"]) > 1 else {"screens": 0, "verifications": 0}
    out["p3"] = {"confirmed": rec["confirmed"], "oracle_round2_confirmed": orc["confirmed"],
                 "hits1": len(pending), "cap_after_r1": cap_after_r1, "binding": int(len(pending) > cap_after_r1),
                 "round2_screens": r2["screens"], "has_round2_screen": int(r2["screens"] > 0),
                 "B2": res.get("B2"), "B2_zero": int(res.get("B2", 0) == 0), "unused": rec["unused_cap"],
                 "stop_with_unused": int(rec["unused_cap"] > 0), "crossing": cross}
    return out


def work_unit(args) -> dict:
    u, preds, do_custom, do_native, do_headroom, jsonl_preds = args
    layout = _LAYOUT
    t0 = time.perf_counter()
    custom_rows, native_rows, jsonl, nat_jsonl = [], [], [], []
    if do_custom:
        for pred, rounds, fp, kind, cp, term in custom_configs(preds):
            rec = fr.run_custom(u, pred, rounds, fp=fp, cap_kind=kind, cp=cp, terminal=term)
            acc = fr.account_custom(u, rec, layout)
            row = {"pred": pred, "rounds": rounds, "fp": fp, "cap_kind": kind, "cp": cp, "terminal": term,
                   "tissue": u.tissue, "line": u.sidm, "role": u.role, "n1": rec["n1"], "n_menu": u.n, "M": rec["M"]}
            row.update({f: rec[f] for f in CAMPAIGN_FIELDS})
            row.update(_flat_custom(acc))
            custom_rows.append(row)
            if pred in jsonl_preds and kind == "measurement" and cp == 20 and not term:
                jsonl.append({k: rec[k] for k in ("tissue", "line", "group", "role", "pred", "rounds", "fp", "n_menu",
                                                   "M", "n1", "screens_ordered", "screen_hits", "verifies_ordered",
                                                   "verification_hits", "confirmed", "spent", "rounds_used",
                                                   "last_round", "unused_cap", "per_round", "reserve")})
    if do_native:
        view = nt.native_view(u, layout)
        caps = nt.native_caps(view)
        for pred, rounds, fp, pct, K in native_configs(preds, caps):
            rec = nt.run_native(u, view, pred, rounds, K, fp=fp)
            acc = nt.account_native(u, view, rec, layout)
            row = {"pred": pred, "rounds": rounds, "fp": fp, "pct": pct, "tissue": u.tissue, "line": u.sidm,
                   "role": u.role}
            row.update({k: v for k, v in rec.items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
            row.update({f"acc_{k}": v for k, v in acc["total"].items()})
            native_rows.append(row)
            if pred in jsonl_preds:
                nat_jsonl.append({k: rec[k] for k in ("tissue", "line", "role", "pred", "rounds", "fp", "cap_plates",
                                                       "plate_starts", "confirmed", "bought", "rounds_used")} | {"pct": pct})
    head = {}
    if do_headroom:
        for pred in preds:
            if pred in HEADROOM_PREDS or pred.startswith("C") or pred == "L_v":
                head[pred] = _headroom(u, pred)
    return {"key": (u.tissue, u.sidm, u.role), "custom": custom_rows, "native": native_rows, "jsonl": jsonl,
            "native_jsonl": nat_jsonl, "headroom": head, "seconds": time.perf_counter() - t0}


def _init(layout):
    global _LAYOUT
    _LAYOUT = layout


# ---------------------------------------------------------------------------- aggregation
def aggregate(rows: list[dict], keys: tuple, skip=("tissue", "line", "role")) -> list[dict]:
    """Group campaigns by config; line value = mean over roles; totals = sums over lines; days mean/max."""
    groups: dict = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in keys)].append(r)
    out = []
    for cfg, rs in groups.items():
        lines: dict = defaultdict(lambda: defaultdict(float))
        numeric = [k for k, v in rs[0].items() if k not in keys and k not in skip and isinstance(v, (int, float))
                   and not isinstance(v, bool) and v is not None]
        for r in rs:
            slot = lines[(r["tissue"], r["line"])]
            slot["_n"] += 1
            for k in numeric:
                if r.get(k) is not None:
                    slot[k] += 0.5 * float(r[k])
        if any(v["_n"] != 2 for v in lines.values()):
            raise AssertionError(f"config {cfg}: a line lacks a role")
        row = dict(zip(keys, cfg))
        row["lines"] = len(lines)
        row["campaigns"] = len(rs)
        for k in numeric:
            row[k] = float(sum(v[k] for v in lines.values()))
        days = [r["min_days"] for r in rs]
        row["mean_min_days_per_campaign"] = float(np.mean(days))
        row["max_min_days"] = int(max(days))
        row["mean_rounds_used_per_campaign"] = float(np.mean([r["rounds_used"] for r in rs]))
        row["campaigns_n1_zero"] = int(sum(1 for r in rs if r.get("n1") == 0))
        row["campaigns_with_unused_cap"] = int(sum(1 for r in rs if r.get("unused_cap", 0) > 0))
        out.append(row)
    return out


def pareto(rows: list[dict], resource: str) -> list[dict]:
    pts = sorted(rows, key=lambda r: (r[resource], -r["confirmed"]))
    front, best = [], -1.0
    for r in pts:
        if r["confirmed"] > best:
            front.append(r)
            best = r["confirmed"]
    return front


def per_line(rows: list[dict], keys: tuple, fields=("confirmed", "spent", "plates_documented_200",
                                                     "native_plates_touched", "min_days")) -> dict:
    out: dict = {}
    for r in rows:
        cfg = "|".join(str(r[k]) for k in keys)
        slot = out.setdefault(cfg, {}).setdefault(f"{r['tissue']}|{r['line']}", defaultdict(float))
        for f in fields:
            if f in r and r[f] is not None:
                slot[f] += 0.5 * float(r[f])
    return {c: {l: dict(v) for l, v in d.items()} for c, d in out.items()}


def summarize_headroom(head: dict, preds, fp_focus) -> dict:
    out = {}
    for pred in preds:
        units = [h[pred] for h in head.values() if pred in h]
        if not units:
            continue
        n = len(units)
        p2 = {}
        for fp in fr.FP_GRID:
            xs = [x["p2"][fp] for x in units]
            conf = sum(x["confirmed"] for x in xs)
            orc = sum(x["oracle_verify_confirmed"] for x in xs)
            p2[fp] = {"campaigns": n, "binding_campaigns": sum(x["binding"] for x in xs),
                      "binding_fraction": sum(x["binding"] for x in xs) / n,
                      "excess_hits_total": sum(x["excess"] for x in xs),
                      "stop_with_unused_campaigns": sum(x["stop_with_unused"] for x in xs),
                      "unused_cap_total": sum(x["unused"] for x in xs),
                      "n1_zero_campaigns": sum(x["n1_zero"] for x in xs),
                      "confirmed_campaign_sum": conf, "oracle_verify_order_confirmed_campaign_sum": orc,
                      "oracle_verify_order_relative_gain": (orc / conf - 1) if conf else None}
        best = sum(max(x["p2"][fp]["confirmed"] for fp in fr.FP_GRID) for x in units)
        p3 = [x["p3"] for x in units]
        c3 = sum(x["confirmed"] for x in p3)
        o3 = sum(x["oracle_round2_confirmed"] for x in p3)
        out[pred] = {
            "campaigns": n,
            "p2_by_fp": p2,
            "p2_hindsight_best_fp_per_campaign_confirmed_sum": best,
            "p2_hindsight_relative_gain_vs_fp": {fp: (best / p2[fp]["confirmed_campaign_sum"] - 1)
                                                 if p2[fp]["confirmed_campaign_sum"] else None for fp in fr.FP_GRID},
            "p3": {"confirmed_campaign_sum": c3, "oracle_round2_screens_confirmed_campaign_sum": o3,
                   "oracle_round2_relative_gain": (o3 / c3 - 1) if c3 else None,
                   "campaigns_with_round2_screen": sum(x["has_round2_screen"] for x in p3),
                   "campaigns_B2_zero": sum(x["B2_zero"] for x in p3),
                   "campaigns_hits_exceed_round2_capacity": sum(x["binding"] for x in p3),
                   "campaigns_stop_with_unused": sum(x["stop_with_unused"] for x in p3),
                   "unused_cap_total": sum(x["unused"] for x in p3),
                   "crossing_index_measurement": sum(x["crossing"]["measurement"]["index"] for x in p3),
                   "crossing_pipeline_measurement": sum(x["crossing"]["measurement"]["pipeline"] for x in p3),
                   "crossing_index_wells": sum(x["crossing"]["wells"]["index"] for x in p3),
                   "crossing_pipeline_wells": sum(x["crossing"]["wells"]["pipeline"] for x in p3),
                   "campaigns_with_pending_and_unscreened": sum(1 for x in p3 if x["crossing"]["measurement"]["v_min"] is not None)},
        }
        rule = {}
        for fp in fr.FP_GRID:
            f = p2[fp]
            choice = max(f["binding_fraction"], out[pred]["p3"]["crossing_pipeline_measurement"] / n)
            bound = max(f["oracle_verify_order_relative_gain"] or 0.0,
                        out[pred]["p2_hindsight_relative_gain_vs_fp"][fp] or 0.0)
            rule[fp] = {"choice_frequency": choice, "oracle_bound_relative": bound,
                        "result": "SCHEDULER_ARM_INDICATED" if (choice >= CHOICE_FREQUENCY_MIN and bound >= TAU)
                        else "SCHEDULER_ARM_NOT_INDICATED"}
        out[pred]["scheduler_rule_by_fp"] = rule
        out[pred]["scheduler_rule_definition"] = (
            f"INDICATED iff choice_frequency >= {CHOICE_FREQUENCY_MIN} and oracle_bound_relative >= {TAU}; "
            "choice_frequency = max(P2 campaigns whose round-1 hits exceed the verification capacity M - n1, "
            "P3 campaigns with a pipeline-index crossing at the round-2 decision); oracle_bound_relative = max(P2 "
            "perfect verification order, P2 per-campaign hindsight-best fp) relative to the rule's yield")
        if fp_focus is not None and fp_focus in rule:
            out[pred]["scheduler_rule_at_fp_star"] = dict(rule[fp_focus], fp=fp_focus)
    return out


# ---------------------------------------------------------------------------- entry point
def _environment() -> dict:
    import pandas
    return {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": np.__version__,
            "pandas": pandas.__version__, "executable": sys.executable, "cpu_count": os.cpu_count()}


def code_hashes() -> dict:
    return {f"resources/{p.name}": sha256(p) for p in sorted(HERE.glob("*.py"))}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", choices=("hd", "eval"), required=True)
    parser.add_argument("--dry", type=Path, default=None, help="synthetic Jaaks-format release; outputs there")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--c-star", default=None, help="eval: C* as written in design/selection.json")
    parser.add_argument("--fp-star", type=int, default=None, help="eval: integer fp* from design/selection.json")
    parser.add_argument("--r-fp", type=int, default=None, help="eval: R's own HD-selected fp (H2)")
    args = parser.parse_args(argv)
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    t0 = time.perf_counter()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    selection = None
    if args.dry is not None:
        source = jaaks.synthetic_release(args.dry / "synthetic_release.csv")
        ticket = {"freeze_sha256": "DRY_RUN_NOT_A_VAULT", "data_sha256": sha256(source)}
        out_dir = args.dry / f"{args.stage}_{stamp}"
        events = {}
    else:
        from ..common import JAAKS, exposed_ticket
        if not (HERE / "plan.json").is_file():
            raise SystemExit("write resources/plan.json first")
        plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
        current = code_hashes()
        for name, digest in plan["code_sha256"].items():
            if current.get(name) != digest:
                raise SystemExit(f"REFUSED: {name} changed since plan.json (deviation must be recorded first)")
        if args.stage == "eval":
            if not SELECTION.is_file():
                raise SystemExit("REFUSED: design/selection.json does not exist; E outcomes are not used before it")
            selection = json.loads(SELECTION.read_text(encoding="utf-8"))
            selection["_sha256"] = sha256(SELECTION)
        source = JAAKS
        out_dir = HERE / "results" / f"{args.stage}_{stamp}"
        events = None
        ticket = exposed_ticket(f"resources stage {args.stage}: custom/native frontier with stopping, accounting and "
                                f"scheduler headroom (resources/plan.json)", "resources")
    if out_dir.exists():
        raise SystemExit(f"REFUSED: {out_dir} exists")
    out_dir.mkdir(parents=True)
    t_build = time.perf_counter()
    panels, report, candidates = jaaks.build_panels(ticket, source)
    layout = build_layout(source, events={} if events is not None else None)
    menu_check = check_against_panels(layout, panels, candidates)
    if args.dry is not None:
        part = {t: {"E": list(tl.lines[:len(tl.lines) // 2]), "HD": list(tl.lines[len(tl.lines) // 2:])}
                for t, tl in layout.tissues.items()}
    else:
        from ..common import partition
        part = partition()
    group = "HD" if args.stage == "hd" else "E"
    units = fr.build_units(layout, panels, part, groups=(group,))
    build_seconds = time.perf_counter() - t_build
    preds = fr.ALL_SCORES
    c_star, fp_star, r_fp = args.c_star, args.fp_star, args.r_fp
    if args.stage == "eval" and args.dry is None:
        text = json.dumps(selection)
        if c_star is None or fp_star is None or c_star not in fr.PREDICTORS or f'"{c_star}"' not in text                 or str(fp_star) not in text:
            raise SystemExit("REFUSED: pass --c-star and --fp-star exactly as written in design/selection.json")
    jsonl_preds = ("S", "S_both", "R") + ((c_star,) if c_star else ())
    print(f"built {len(units)} {group} units in {build_seconds:.1f}s; workers {args.workers}", flush=True)
    t_run = time.perf_counter()
    tasks = [(u, preds, True, True, True, jsonl_preds) for u in units]
    results = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers, initializer=_init, initargs=(layout,)) as ex:
            for res in ex.map(work_unit, tasks, chunksize=2):
                results.append(res)
    else:
        _init(layout)
        results = [work_unit(t) for t in tasks]
    run_seconds = time.perf_counter() - t_run
    custom = [r for res in results for r in res["custom"]]
    native = [r for res in results for r in res["native"]]
    head = {res["key"]: res["headroom"] for res in results}
    ckeys = ("pred", "rounds", "fp", "cap_kind", "cp", "terminal")
    nkeys = ("pred", "rounds", "fp", "pct")
    t_agg = time.perf_counter()
    custom_tab = aggregate(custom, ckeys)
    native_tab = aggregate(native, nkeys)
    resources = ("spent", "combination_wells", "plates_documented_200", "control_wells_documented_200",
                 "single_agent_wells_documented_200", "mean_min_days_per_campaign", "native_plates_touched",
                 "seeding_events_touched")
    fronts = {}
    for pred in preds:
        rows = [r for r in custom_tab if r["pred"] == pred and r["cap_kind"] == "measurement" and not r["terminal"]]
        fronts[pred] = {res: [{k: r[k] for k in ckeys + ("confirmed", res)} for r in pareto(rows, res)]
                        for res in resources}
    nat_resources = ("plate_starts", "acc_seeding_events", "acc_combination_wells_on_plates",
                     "acc_control_wells_documented_200", "acc_single_agent_wells", "mean_min_days_per_campaign")
    nat_fronts = {pred: {res: [{k: r[k] for k in nkeys + ("confirmed", res)} for r in
                               pareto([r for r in native_tab if r["pred"] == pred], res)] for res in nat_resources}
                  for pred in preds}
    fp_focus = int(fp_star) if fp_star is not None else None
    head_summary = summarize_headroom(head, preds, fp_focus)
    agg_seconds = time.perf_counter() - t_agg
    with open(out_dir / "campaigns_custom_p_cp20.jsonl", "w", encoding="utf-8", newline="\n") as h:
        for res in results:
            for r in res["jsonl"]:
                h.write(json.dumps(r, default=int) + "\n")
    with open(out_dir / "campaigns_native.jsonl", "w", encoding="utf-8", newline="\n") as h:
        for res in results:
            for r in res["native_jsonl"]:
                h.write(json.dumps(r, default=int) + "\n")
    primary_keys = [k for k in ckeys]
    lines_tab = per_line([r for r in custom if r["cap_kind"] == "measurement" and r["cp"] == 20 and not r["terminal"]],
                         tuple(primary_keys))
    finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    manifest = {"status": STATUS, "stage": args.stage, "group": group, "started": started, "finished": finished,
                "ticket": ticket, "source": str(source), "build_report": report, "menu_check": menu_check,
                "layout_summary": layout.summary, "units": len(units), "lines": len({(u.tissue, u.sidm) for u in units}),
                "predictors": list(preds), "selection": selection, "C_star": c_star, "fp_star": fp_star,
                "R_own_fp": r_fp, "code_sha256": code_hashes(),
                "plan_sha256": sha256(HERE / "plan.json") if (HERE / "plan.json").is_file() else None,
                "wall_seconds": {"build": round(build_seconds, 2), "campaigns": round(run_seconds, 2),
                                 "aggregation": round(agg_seconds, 2), "total": round(time.perf_counter() - t0, 2),
                                 "unit_cpu_seconds_sum": round(sum(r["seconds"] for r in results), 2)},
                "environment": _environment(), "workers": args.workers}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    (out_dir / "custom_frontier.json").write_text(json.dumps({"status": STATUS, "keys": ckeys, "table": custom_tab,
                                                              "pareto": fronts}, indent=1, default=str), encoding="utf-8")
    (out_dir / "native_frontier.json").write_text(json.dumps({"status": STATUS, "keys": nkeys, "table": native_tab,
                                                              "pareto": nat_fronts}, indent=1, default=str), encoding="utf-8")
    (out_dir / "headroom.json").write_text(json.dumps({"status": STATUS, "summary": head_summary,
                                                       "fp_focus": fp_focus}, indent=1, default=str), encoding="utf-8")
    (out_dir / "per_line_cp20.json").write_text(json.dumps(lines_tab, default=str), encoding="utf-8")
    print(f"{group}: {len(custom)} custom and {len(native)} native campaigns; total {manifest['wall_seconds']['total']}s")
    print(f"outputs in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
