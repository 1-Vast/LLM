"""Summary tables of the resources stages, read from written outputs only (no outcome access).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/summarize.py
- Purpose: post-run summary (plan_addendum_1.json): the custom 1/2/3-round frontier with cap versus
  consumption and every resource, the stopping effect against the spend-all reference, the cap-percent
  and wells-cap versions, the native-plate frontier, Pareto fronts, the scheduler-headroom diagnostic,
  the comparison with the earlier receipts and an exact cross-check against the design workstream's
  per-campaign files (read-only).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.resources.summarize HD_DIR EVAL_DIR`
  writes resources/results/summary_<timestamp>/summary.json (never overwrites).
- Depends on: json, gzip; the result folders of run.py; design/results (read-only); receipts.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
PREDS = ("S", "S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod", "R", "oracle")
FOCUS = ("S", "S_both", "C_mean", "R", "oracle")
CUSTOM_FIELDS = ("lines", "campaigns", "cap", "spent", "unused_cap", "confirmed", "screens", "screen_hits",
                 "verifications", "verification_hits", "missed_never_screened", "missed_screened_not_verified",
                 "final_round_screens", "dose_points", "combination_wells", "combination_wells_builder_qc",
                 "plates_documented_200", "plates_raw_min_216", "plates_raw_median_226", "plates_raw_max_254",
                 "joint_plates_documented_200", "control_wells_documented_200", "control_wells_raw_min_216",
                 "control_wells_raw_median_226", "control_wells_raw_max_254", "single_agent_wells_documented_200",
                 "single_agent_wells_raw_max_254", "native_plates_touched", "seeding_events_touched",
                 "failed_measurements", "mean_min_days_per_campaign", "max_min_days", "mean_rounds_used_per_campaign",
                 "campaigns_n1_zero", "campaigns_with_unused_cap")
NATIVE_FIELDS = ("lines", "campaigns", "cap_plates", "plate_starts", "unused_cap", "confirmed", "confirmed_screen_first",
                 "confirmed_same_round", "confirmed_verification_first", "screen_orientations", "screen_hits",
                 "verification_orientations", "verifications_of_unscreened_pairs", "screen_hits_never_verified",
                 "acc_seeding_events", "acc_combination_wells_on_plates", "acc_menu_combination_wells_credited",
                 "acc_off_menu_orientation_measurements", "acc_off_menu_same_side", "acc_off_menu_cross_not_menu",
                 "acc_single_agent_wells", "acc_control_wells_documented_200", "acc_control_wells_raw_min_216",
                 "acc_control_wells_raw_max_254", "mean_min_days_per_campaign", "max_min_days",
                 "mean_rounds_used_per_campaign")


def _load(d: Path) -> dict:
    return {"custom": json.loads((d / "custom_frontier.json").read_text(encoding="utf-8")),
            "native": json.loads((d / "native_frontier.json").read_text(encoding="utf-8")),
            "headroom": json.loads((d / "headroom.json").read_text(encoding="utf-8")),
            "manifest": json.loads((d / "manifest.json").read_text(encoding="utf-8"))}


def _c(tab, pred, rounds, fp=None, kind="measurement", cp=20, term=False) -> dict:
    for r in tab:
        if (r["pred"], r["rounds"], r["fp"], r["cap_kind"], r["cp"], r["terminal"]) == (pred, rounds, fp, kind, cp, term):
            return r
    raise KeyError((pred, rounds, fp, kind, cp, term))


def _n(tab, pred, rounds, fp, pct) -> dict:
    for r in tab:
        if (r["pred"], r["rounds"], r["fp"], r["pct"]) == (pred, rounds, fp, pct):
            return r
    raise KeyError((pred, rounds, fp, pct))


def _pick(r: dict, fields) -> dict:
    return {k: r.get(k) for k in fields}


def custom_tables(res: dict, fp: int) -> dict:
    tab = res["custom"]["table"]
    main = {p: {"P1_1round": _pick(_c(tab, p, 1), CUSTOM_FIELDS),
                f"P2_2rounds_fp{fp}": _pick(_c(tab, p, 2, fp), CUSTOM_FIELDS),
                "P3_3rounds": _pick(_c(tab, p, 3), CUSTOM_FIELDS),
                f"REFERENCE_P2_spend_all_fp{fp}": _pick(_c(tab, p, 2, fp, term=True), CUSTOM_FIELDS),
                "REFERENCE_P3_spend_all": _pick(_c(tab, p, 3, term=True), CUSTOM_FIELDS)} for p in PREDS}
    grid = {p: {f: _pick(_c(tab, p, 2, f), ("confirmed", "spent", "unused_cap", "screens", "verifications",
                                            "combination_wells", "plates_documented_200", "native_plates_touched",
                                            "seeding_events_touched", "mean_min_days_per_campaign", "campaigns_n1_zero"))
                for f in range(10, 61, 5)} for p in PREDS}
    cps = {p: {cp: {"P1": _pick(_c(tab, p, 1, cp=cp), ("cap", "spent", "confirmed", "combination_wells",
                                                      "plates_documented_200", "native_plates_touched",
                                                      "mean_min_days_per_campaign")),
                    f"P2_fp{fp}": _pick(_c(tab, p, 2, fp, cp=cp), ("cap", "spent", "confirmed", "combination_wells",
                                                                   "plates_documented_200", "native_plates_touched",
                                                                   "mean_min_days_per_campaign")),
                    "P3": _pick(_c(tab, p, 3, cp=cp), ("cap", "spent", "confirmed", "combination_wells",
                                                      "plates_documented_200", "native_plates_touched",
                                                      "mean_min_days_per_campaign"))}
                for cp in (10, 20, 30, 40)} for p in PREDS}
    wells = {p: {"P1_wells_ext": _pick(_c(tab, p, 1, kind="wells"), CUSTOM_FIELDS),
                 f"P2_wells_fp{fp}": _pick(_c(tab, p, 2, fp, kind="wells"), CUSTOM_FIELDS),
                 "P3_wells_ext": _pick(_c(tab, p, 3, kind="wells"), CUSTOM_FIELDS)} for p in PREDS}
    stop = {}
    for p in PREDS:
        stop[p] = {}
        for label, a, b in ((f"P2_fp{fp}", _c(tab, p, 2, fp), _c(tab, p, 2, fp, term=True)),
                             ("P3", _c(tab, p, 3), _c(tab, p, 3, term=True))):
            stop[p][label] = {"confirmed_stop": a["confirmed"], "confirmed_spend_all": b["confirmed"],
                              **{f"saved_{k}": b[k] - a[k] for k in ("spent", "combination_wells", "plates_documented_200",
                                                                      "plates_raw_max_254", "joint_plates_documented_200",
                                                                      "control_wells_documented_200",
                                                                      "control_wells_raw_max_254",
                                                                      "single_agent_wells_documented_200",
                                                                      "native_plates_touched", "seeding_events_touched",
                                                                      "screens")},
                              "mean_days_stop": a["mean_min_days_per_campaign"],
                              "mean_days_spend_all": b["mean_min_days_per_campaign"],
                              "relative_saving_spent": (b["spent"] - a["spent"]) / b["spent"],
                              "relative_saving_plates_200": (b["plates_documented_200"] - a["plates_documented_200"])
                              / b["plates_documented_200"]}
    rel = {}
    for label, getter in (("P1", lambda p: _c(tab, p, 1)), (f"P2_fp{fp}", lambda p: _c(tab, p, 2, fp)),
                          ("P3", lambda p: _c(tab, p, 3)), (f"P2_wells_fp{fp}", lambda p: _c(tab, p, 2, fp, kind="wells"))):
        rel[label] = {p: getter(p)["confirmed"] for p in PREDS}
    return {"main_cp20": main, "p2_fp_grid_cp20": grid, "cap_percent": cps, "wells_cap": wells,
            "stopping_vs_spend_all": stop, "confirmed_by_policy": rel,
            "pareto": {p: res["custom"]["pareto"][p] for p in FOCUS}}


def native_tables(res: dict, fp: int) -> dict:
    tab = res["native"]["table"]
    out = {}
    for p in PREDS:
        out[p] = {}
        for pct in (5, 10, 15, 20, 30, 40, 50, 75, 100):
            out[p][pct] = {"N1": _pick(_n(tab, p, 1, None, pct), NATIVE_FIELDS),
                           f"N2_fp{fp}": _pick(_n(tab, p, 2, fp, pct), NATIVE_FIELDS),
                           "N3": _pick(_n(tab, p, 3, None, pct), NATIVE_FIELDS)}
    return {"by_pred_pct": out, "pareto": {p: res["native"]["pareto"][p] for p in FOCUS}}


def _design_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as h:
        return [json.loads(line) for line in h]


def cross_check(res_dir: Path, design_dir: Path, files: dict, custom_tab: list) -> dict:
    mine = {}
    with open(res_dir / "campaigns_custom_p_cp20.jsonl", encoding="utf-8") as h:
        for line in h:
            r = json.loads(line)
            mine[(r["pred"], r["rounds"], r["fp"], r["line"], r["role"])] = r
    out = {}
    for name, (rounds, unit) in files.items():
        p = design_dir / f"{name}.jsonl.gz"
        if not p.is_file():
            continue
        rows = _design_rows(p)
        n = bad = 0
        agg = defaultdict(lambda: defaultdict(float))
        for d in rows:
            key = (d["arm"], rounds, d.get("fp") if rounds == 2 else None)
            for f in ("confirmed", "spent", "n_native_plates", "n_seeding_events", "combination_wells", "min_days"):
                if f in d and d[f] is not None:
                    agg[key][f] += 0.5 * d[f]
            if unit != "measurement":
                continue
            m = mine.get((d["arm"], rounds, d.get("fp") if rounds == 2 else None, d["line"], d["role"]))
            if m is None:
                continue
            n += 1
            if (m["screens_ordered"] != d["screens"] or m["verifies_ordered"] != d["verifies"]
                    or m["confirmed"] != d["confirmed"] or m["spent"] != d["spent"]
                    or m["rounds_used"] != d["rounds_used"]):
                bad += 1
        totals = {}
        for (arm, rr, fp), v in agg.items():
            kind = "measurement" if unit == "measurement" else "wells"
            try:
                r = _c(custom_tab, arm, rr, fp, kind=kind)
            except KeyError:
                continue
            totals[f"{arm}|{rr}|{fp}"] = {
                "confirmed": [v["confirmed"], r["confirmed"]], "spent": [v["spent"], r["spent"]],
                "native_plates": [v["n_native_plates"], r["native_plates_touched"]],
                "seeding_events": [v["n_seeding_events"], r["seeding_events_touched"]],
                "combination_wells": [v["combination_wells"], r["combination_wells"]],
                "min_days": [v["min_days"], r["min_days"]]}
        diff = {k: {f: x for f, x in v.items() if abs(x[0] - x[1]) > 1e-9} for k, v in totals.items()}
        diff = {k: v for k, v in diff.items() if v}
        out[name] = {"design_file": str(p.relative_to(STUDY)), "campaigns_compared_purchase_lists": n,
                     "campaign_mismatches": bad, "configs_compared_totals": len(totals),
                     "total_differences": diff, "format": "totals as [design, resources]"}
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    hd_dir, ev_dir = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    out_dir = HERE / "results" / f"summary_{time.strftime('%Y%m%d_%H%M%S')}"
    if out_dir.exists():
        raise SystemExit(f"REFUSED: {out_dir} exists")
    hd, ev = _load(hd_dir), _load(ev_dir)
    fp = int(ev["manifest"]["fp_star"])
    c_star = ev["manifest"]["C_star"]
    sel = json.loads((STUDY / "design/selection.json").read_text(encoding="utf-8"))
    design_dev = Path(sel["results_dir"])
    design_eval = sorted((STUDY / "design/results").glob("eval_*"))[-1]
    rt = json.loads((HERE / "receipts/reproduced_totals.json").read_text(encoding="utf-8"))
    old = rt["focus_measurement_version"]
    ev_c = custom_tables(ev, fp)
    summary = {
        "status": "EXPLORATORY: Jaaks 2022 exposed; frontier/accounting summary from written outputs only",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "inputs": {"hd": str(hd_dir.relative_to(STUDY)), "eval": str(ev_dir.relative_to(STUDY)),
                   "design_dev": str(design_dev.relative_to(STUDY)) if design_dev.is_relative_to(STUDY) else str(design_dev),
                   "design_eval": str(design_eval.relative_to(STUDY)),
                   "selection_sha256": ev["manifest"]["selection"]["_sha256"], "C_star": c_star, "fp_star": fp},
        "eval_E_lines": {"custom": ev_c, "native": native_tables(ev, fp),
                         "headroom": ev["headroom"]["summary"], "manifest_wall_seconds": ev["manifest"]["wall_seconds"]},
        "development_HD_lines": {"custom": custom_tables(hd, fp), "native": native_tables(hd, fp),
                                 "headroom": hd["headroom"]["summary"],
                                 "manifest_wall_seconds": hd["manifest"]["wall_seconds"]},
        "cross_check_design": {
            "HD": cross_check(hd_dir, design_dev, {"campaigns_p2_grid": (2, "measurement"),
                                                   "campaigns_p3": (3, "measurement")}, hd["custom"]["table"]),
            "E": cross_check(ev_dir, design_eval, {"campaigns_primary": (2, "measurement"),
                                                   "campaigns_p3": (3, "measurement"),
                                                   "campaigns_wells": (2, "wells")}, ev["custom"]["table"])},
        "historical_receipts_all_125_lines": {
            a: {k: old[a][k] for k in ("budget", "spent", "confirmed", "terminal_screens", "endpoint_eligible_consumption",
                                       "combination_wells", "custom_plates_documented_200", "native_plates_touched",
                                       "seeding_events_touched", "min_protocol_days")} for a in old},
    }
    out_dir.mkdir(parents=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(f"written {out_dir / 'summary.json'}")
    cc = summary["cross_check_design"]
    print(json.dumps({g: {k: {kk: v[kk] for kk in ("campaigns_compared_purchase_lists", "campaign_mismatches",
                                                    "configs_compared_totals")} | {"n_total_diffs": len(v["total_differences"])}
                          for k, v in x.items()} for g, x in cc.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
