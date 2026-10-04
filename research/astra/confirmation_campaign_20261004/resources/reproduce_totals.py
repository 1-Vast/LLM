"""Reproduce the earlier allocation study's resource totals from its receipts only (no outcome read).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/reproduce_totals.py
- Purpose: step 1(a) of the resources workstream. Re-sum the per-campaign records of
  `reproducible_allocation_20261003/allocation/results/lines.jsonl`, compare with that study's
  `replay.json` tables and `receipts/accounting.json`, and independently re-pack every purchase into
  custom 1536-well plates and native plates from the release's DESIGN columns (no outcome column, no
  ticket). Separates caps from actual consumption: unavoidable odd residues of paired arms and
  unverifiable terminal screens inside "spent".
- Core points: the earlier study's files are read, never written. Output
  `resources/receipts/reproduced_totals.json` (refuses to overwrite).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.resources.reproduce_totals`.
- Depends on: numpy, pandas; `layout.py`, `frontier.py` (design-only use).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .frontier import CONTROL_VARIANTS, make_unit, pack_custom
from .layout import PLATE_HIERARCHY, PROVENANCE, ROLES, build_layout

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ALLOC = ROOT / "research/astra/reproducible_allocation_20261003/allocation"
LINES = ALLOC / "results/lines.jsonl"
REPLAY = ALLOC / "results/replay.json"
ACCOUNTING = ALLOC / "receipts/accounting.json"
EXPLORATION = ROOT / "research/astra/direction_exploration_20261004_v1/EXPLORATION_RECEIPT.json"
CANDIDATES = ROOT / "research/astra/feedback_validation_20261003/results/jaaks_primary/candidates.json"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
OUT = HERE / "receipts/reproduced_totals.json"
FOCUS = ("verify_hits_terminal", "fixed_split_dev", "fixed_split_dev_R1", "paired_full", "paired_full_R1",
         "verify_hits_terminal_R1", "verify_hits_terminal_R2")
FIELDS = ("budget", "spent", "remainder", "remainder_unavoidable", "remainder_avoidable", "screens",
          "verifications", "screen_hits", "verified_hits", "confirmed", "terminal_screens", "terminal_screen_hits",
          "unverified_screen_hits", "missed_unverified_validated")
SCHEDULED = {"screen_only": 4, "paired_full": 4, "verify_hits_terminal": 5, "fixed_split_dev": 5,
             "conf_per_cost": 5, "feedback_verify_hits": 5, "feedback_paired": 4, "verify_hits_noterminal": 4,
             "verify_hits_terminal_R1": 2, "verify_hits_terminal_R2": 3, "screen_only_R1": 1, "paired_full_R1": 1,
             "fixed_split_dev_R1": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _design_units(layout) -> dict:
    units = {}
    for tissue, tl in layout.tissues.items():
        for sidm in tl.lines:
            n = int(tl.rows_of(tl.lines.index(sidm)).size)
            z = np.zeros(n)
            q = {"p_s": z, "p_v": z, "p_sv": z, "p_vs": z}
            for role in ROLES:
                units[(tissue, sidm, role)] = make_unit(layout, tissue, sidm, role, "design", {"none": (z, z)}, q, None)
    return units


def _repack(u, rec: dict, layout, events: dict) -> dict:
    groups = defaultdict(list)
    for r, branch, i in rec["purchases"]:
        groups[(r, branch)].append(int(i))
    out = {"custom": {name: {"screen": 0, "verify": 0} for name in CONTROL_VARIANTS},
           "custom_terminal_round_screen_plates_200": 0, "native_first_touch": 0, "native_union": 0,
           "seeding_events_union": 0, "combination_wells": 0, "terminal_screen_combination_wells": 0}
    touched = set()
    last = max((k[0] for k in groups), default=0)
    for (r, branch), idx in groups.items():
        side = "s" if branch == "screen" else "v"
        orient, dp = getattr(u, f"orient_{side}"), getattr(u, f"plates_{side}")
        items = [(orient[i][0], orient[i][1], int(dp[i]), None) for i in idx]
        for name, ctrl in CONTROL_VARIANTS.items():
            out["custom"][name][branch] += pack_custom(items, ctrl)["plates"]
        wells = 14 * int(sum(dp[i] for i in idx))
        out["combination_wells"] += wells
        if branch == "screen" and r == last and rec["terminal_screens"]:
            out["custom_terminal_round_screen_plates_200"] += pack_custom(items, 200)["plates"]
            out["terminal_screen_combination_wells"] += wells
        for i in idx:
            touched |= set(getattr(u, f"barcodes_{side}")[i])
    out["native_union"] = len(touched)
    out["seeding_events_union"] = len({events.get(b, b) for b in touched})
    return out


def days_receipt() -> dict:
    h = pd.read_csv(PLATE_HIERARCHY, dtype=str)
    seeded = pd.to_datetime(h["seeded"])
    scanned = pd.to_datetime(h["scanned"])
    naive = (scanned.dt.normalize() - seeded.dt.normalize()).dt.days
    # timestamps are local midnights stored as 00:00 (GMT) or 23:00 of the previous day (BST)
    local = lambda t: (t + pd.to_timedelta((t.dt.hour == 23).astype(int), unit="h")).dt.normalize()
    calendar = (local(scanned) - local(seeded)).dt.days
    straddle = h[naive != calendar]
    return {"source": str(PLATE_HIERARCHY.relative_to(ROOT)), "source_sha256": sha(PLATE_HIERARCHY),
            "plates": int(len(h)), "seeding_events": int(h["event"].nunique()),
            "naive_date_difference_days": {str(k): int(v) for k, v in naive.value_counts().sort_index().items()},
            "local_calendar_days": {str(k): int(v) for k, v in calendar.value_counts().sort_index().items()},
            "plates_differing": int(len(straddle)),
            "differing_seeding_dates": sorted(set(h.loc[naive != calendar, "seeded"].str[:10])),
            "note": ("38 plates seeded at 00:00 and read at 23:00 three dates later straddle the UK change to summer "
                     "time (2017-03-26, 2018-03-25): the timestamps are local midnights, so every plate is read "
                     "4 calendar days after seeding. Minimum elapsed days = 4 per used round (assay only)."),
            "minimum_days_per_round": 4}


def controls_receipt() -> dict:
    p = json.loads(PROVENANCE.read_text(encoding="utf-8"))["controls_per_plate"]
    w = p["wells_by_class_per_plate"]
    fixed = {k: int(w[k]["max"]) for k in ("NC-0", "NC-1", "B", "PC1", "PC2")}
    dmso = p["dmso_only_positions_per_plate"]
    return {"source": str(PROVENANCE.relative_to(ROOT)), "source_sha256": sha(PROVENANCE),
            "documented_per_plate": p["documented_per_plate"], "documented_total": 200,
            "raw_fixed_per_plate": fixed, "raw_fixed_total": int(sum(fixed.values())),
            "raw_dmso_only_positions": {"min": dmso["min"], "median": dmso["median"], "max": dmso["max"],
                                        "distinct": dmso["distinct"]},
            "raw_total_range": [int(sum(fixed.values()) + dmso["min"]), int(sum(fixed.values()) + dmso["max"])],
            "raw_unused_positions_per_plate": int(w["UN-USED"]["max"]),
            "custom_model_variants": CONTROL_VARIANTS,
            "note": "per-plate DMSO-only counts are not in the receipts; the custom model is reported at 200, 216, 226 "
                    "(raw median) and 254 controls per plate"}


def main(argv=None) -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists and is never overwritten")
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    layout = build_layout(JAAKS)
    cand = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    for tissue, tl in layout.tissues.items():
        if [tuple(p) for p in cand[tissue]["pairs_s_v"]] != list(zip(tl.s.tolist(), tl.v.tolist())) or \
                list(cand[tissue]["line_sidm"]) != list(tl.lines):
            raise AssertionError(f"{tissue}: design menu differs from the builder's candidates receipt")
    units = _design_units(layout)
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    acc = json.loads(ACCOUNTING.read_text(encoding="utf-8"))
    expl = json.loads(EXPLORATION.read_text(encoding="utf-8"))["resources"]
    sums = {u: defaultdict(lambda: defaultdict(float)) for u in ("measurement", "physical")}
    odd = {}
    lines_seen = defaultdict(set)
    with open(LINES, encoding="utf-8") as handle:
        for raw in handle:
            rec = json.loads(raw)
            unit, arm = rec["unit"], rec["arm"]
            key = (rec["tissue"], rec["line"], rec["replicate"])
            lines_seen[(unit, arm)].add((rec["tissue"], rec["line"]))
            s = sums[unit][arm]
            for f in FIELDS:
                s[f] += 0.5 * rec[f]
            s["rounds_with_purchases"] += 0.5 * rec["rounds_with_purchases"] / 125
            u = units[key]
            if u.n != rec["menu"]:
                raise AssertionError(f"menu size differs for {key}")
            if unit == "measurement" and arm == "paired_full_R1":
                odd[(rec["tissue"], rec["line"])] = rec["budget"] % 2
            rp = _repack(u, rec, layout, layout.events)
            for name in CONTROL_VARIANTS:
                for b in ("screen", "verify"):
                    s[f"custom_plates_{name}_{b}"] += 0.5 * rp["custom"][name][b]
            for f in ("custom_terminal_round_screen_plates_200", "native_union", "seeding_events_union",
                      "combination_wells", "terminal_screen_combination_wells"):
                s[f] += 0.5 * rp[f]
    checks, table = [], {}
    for unit in ("measurement", "physical"):
        rt = replay["units"][unit]["table"]
        ra = acc["units"][unit]
        table[unit] = {}
        for arm, s in sorted(sums[unit].items()):
            row = {f: s[f] for f in FIELDS}
            for f in FIELDS:
                if f in rt[arm] and abs(rt[arm][f] - s[f]) > 1e-9:
                    checks.append(f"{unit}/{arm}/{f}: lines {s[f]} vs table {rt[arm][f]}")
            for name in CONTROL_VARIANTS:
                row[f"custom_plates_{name}"] = s[f"custom_plates_{name}_screen"] + s[f"custom_plates_{name}_verify"]
                row[f"custom_plates_{name}_by_branch"] = {b: s[f"custom_plates_{name}_{b}"] for b in ("screen", "verify")}
                row[f"custom_control_wells_{name}"] = CONTROL_VARIANTS[name] * row[f"custom_plates_{name}"]
            rec_plates = ra[arm]["by_branch"]["screen"]["custom_plates"] + ra[arm]["by_branch"]["verify"]["custom_plates"]
            if abs(rec_plates - row["custom_plates_documented_200"]) > 1e-9:
                checks.append(f"{unit}/{arm}: custom plates repacked {row['custom_plates_documented_200']} vs receipt {rec_plates}")
            if abs(ra[arm]["total"]["native_plates"] - s["native_union"]) > 1e-9:
                checks.append(f"{unit}/{arm}: native union {s['native_union']} vs receipt {ra[arm]['total']['native_plates']}")
            if abs(ra[arm]["total"]["combination_wells"] - s["combination_wells"]) > 1e-9:
                checks.append(f"{unit}/{arm}: wells {s['combination_wells']} vs receipt {ra[arm]['total']['combination_wells']}")
            row["native_plates_touched"] = s["native_union"]
            row["seeding_events_touched"] = s["seeding_events_union"]
            row["combination_wells"] = s["combination_wells"]
            row["receipt_custom_plates_200"] = rec_plates
            row["receipt_native_plates"] = ra[arm]["total"]["native_plates"]
            row["receipt_combination_wells"] = ra[arm]["total"]["combination_wells"]
            row["scheduled_rounds"] = SCHEDULED[arm]
            row["min_protocol_days"] = 4 * SCHEDULED[arm]
            row["mean_rounds_with_purchases"] = s["rounds_with_purchases"]
            row["cap_minus_spent"] = row["budget"] - row["spent"]
            row["endpoint_eligible_consumption"] = row["spent"] - row["terminal_screens"] if unit == "measurement" else None
            row["terminal_screen_custom_plates_200"] = s["custom_terminal_round_screen_plates_200"]
            row["terminal_screen_combination_wells"] = s["terminal_screen_combination_wells"]
            row["lines"] = len(lines_seen[(unit, arm)])
            table[unit][arm] = row
    m = table["measurement"]
    expl_checks = {}
    for arm, e in expl.items():
        r = m[arm]
        pairs = {"budget": (e["budget"], r["budget"]), "spent": (e["spent"], r["spent"]),
                 "confirmed": (e["confirmed"], r["confirmed"]), "terminal_screens": (e["terminal_screens"], r["terminal_screens"]),
                 "custom_plates": (e["custom_plates"], r["custom_plates_documented_200"]),
                 "native_plates": (e["native_plates"], r["native_plates_touched"]),
                 "scheduled_rounds": (e["scheduled_rounds"], r["scheduled_rounds"]),
                 "min_protocol_days": (e["min_protocol_days"], r["min_protocol_days"])}
        expl_checks[arm] = {k: {"exploration_receipt": a, "reproduced": b, "equal": abs(a - b) < 1e-9}
                            for k, (a, b) in pairs.items()}
    focus = {arm: {k: m[arm][k] for k in ("budget", "spent", "cap_minus_spent", "remainder_unavoidable",
                                          "remainder_avoidable", "screens", "verifications", "screen_hits", "confirmed",
                                          "terminal_screens", "terminal_screen_hits", "endpoint_eligible_consumption",
                                          "combination_wells", "terminal_screen_combination_wells",
                                          "custom_plates_documented_200", "custom_plates_raw_min_216",
                                          "custom_plates_raw_median_226", "custom_plates_raw_max_254",
                                          "terminal_screen_custom_plates_200", "native_plates_touched",
                                          "seeding_events_touched", "scheduled_rounds", "min_protocol_days")}
             for arm in FOCUS}
    out = {
        "status": "EXPLORATORY receipt reproduction (no outcome read: receipts of reproducible_allocation_20261003 and "
                  "design columns of the Jaaks release only)",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "started": started,
        "sources_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (LINES, REPLAY, ACCOUNTING, EXPLORATION, CANDIDATES)},
        "design_read": {"file": str(JAAKS.relative_to(ROOT)), "columns": "jaaks.DESIGN_COLUMNS only (no outcome column)",
                        "summary": layout.summary},
        "all_checks_passed": not checks, "check_failures": checks,
        "budget_facts": {"sum_M_per_line": int(sum(int(u.cap(20)) for k, u in units.items() if k[2] == "SV")),
                         "lines_with_odd_M": int(sum(odd.values())), "lines": len(odd),
                         "note": "paired arms buy whole pairs: an odd M leaves 1 unavoidable unit per role (48 lines)"},
        "focus_measurement_version": focus,
        "exploration_receipt_comparison": expl_checks,
        "cap_versus_consumption": {
            "equal_caps": "every arm had the same cap: 3,958 orientation measurements (sum over 125 lines of M)",
            "paired_full_R1": "spent 3,910: 48 units unavoidable (odd M, pair-only actions), 0 avoidable",
            "fixed_split_dev_R1": "spent the whole cap, but 789.5 of it were terminal screens bought in round 2 that "
                                  "could never be verified: endpoint-eligible consumption 3,168.5",
            "verify_hits_terminal": "spent the whole cap in 5 rounds, 84 terminal screens: endpoint-eligible 3,874",
            "verify_hits_terminal_R1": "2 rounds, 197.5 terminal screens: endpoint-eligible 3,760.5",
            "caution": "subtracting terminal screens is receipt arithmetic, not a stopping replay; the explicit replay "
                       "with stopping is in the resources frontier (results/)"},
        "days": days_receipt(),
        "controls": controls_receipt(),
        "tables": table,
        "wall_seconds": round(time.perf_counter() - t0, 2),
        "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"all_checks_passed": out["all_checks_passed"], "failures": checks[:10],
                      "focus": {a: {k: focus[a][k] for k in ("spent", "confirmed", "terminal_screens",
                                                              "custom_plates_documented_200", "native_plates_touched")}
                                for a in FOCUS}}, indent=1))
    print(f"wall {out['wall_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
