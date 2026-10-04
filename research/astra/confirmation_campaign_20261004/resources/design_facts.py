"""Design-only facts behind the prespecified caps (no outcome column, no ticket).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/design_facts.py
- Purpose: record, before any outcome read of this workstream, the design quantities from which the
  frontier grid and the native caps are chosen: menu sizes, M and W inputs, native plate-set actions per
  line (components, plates, seeding events), menu orientations per plate set, off-menu measurements,
  and the native caps in plate starts at every grid percentage.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.resources.design_facts`
  (writes resources/receipts/design_facts.json; refuses to overwrite).
- Depends on: layout.py, frontier.py (make_unit, design-only), native.py (native_view, native_caps).
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from . import native as nt
from .frontier import make_unit
from .layout import ROLES, build_layout

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
PARTITION = HERE.parent / "protocol/partition.json"
OUT = HERE / "receipts/design_facts.json"


def _q(x) -> dict:
    a = np.asarray(x, float)
    return {"n": int(a.size), "sum": float(a.sum()), "min": float(a.min()), "median": float(np.median(a)),
            "mean": float(a.mean()), "max": float(a.max())}


def main(argv=None) -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    t0 = time.perf_counter()
    layout = build_layout(JAAKS)
    part = json.loads(PARTITION.read_text(encoding="utf-8"))["split"]
    per_line = {}
    by_group = {"E": [], "HD": []}
    for tissue, tl in layout.tissues.items():
        for sidm in tl.lines:
            n = int(tl.rows_of(tl.lines.index(sidm)).size)
            z = np.zeros(n)
            q = {"p_s": z, "p_v": z, "p_sv": z, "p_vs": z}
            group = "E" if sidm in part[tissue]["E"] else "HD"
            rec = {"tissue": tissue, "group": group, "menu": n}
            for role in ROLES:
                u = make_unit(layout, tissue, sidm, role, group, {"none": (z, z)}, q, None)
                view = nt.native_view(u, layout)
                rec[role] = {"M": u.cap(20), "W": u.wells_cap(20), "menu_plates": view["menu_plates"],
                             "screen_components": len(view["screen_comps"]),
                             "verify_components": len(view["verify_comps"]),
                             "screen_plates": int(sum(view["comps"][k]["cost"] for k in view["screen_comps"])),
                             "verify_plates": int(sum(view["comps"][k]["cost"] for k in view["verify_comps"])),
                             "menu_orientations_per_screen_component": float(np.mean(
                                 [len(view["comps"][k]["pairs"]) for k in view["screen_comps"]])),
                             "off_menu_orientations_on_menu_plates": int(sum(
                                 view["comps"][k]["off_menu_same_side"] + view["comps"][k]["off_menu_cross_not_menu"]
                                 for k in view["screen_comps"] + view["verify_comps"])),
                             "seeding_events_behind_menu_plates": len({e for k in view["screen_comps"] + view["verify_comps"]
                                                                      for e in view["comps"][k]["events"]}),
                             "native_caps": nt.native_caps(view),
                             "plates_per_component": dict(Counter(view["comps"][k]["cost"] for k in
                                                                  view["screen_comps"] + view["verify_comps"]))}
            if rec["SV"]["menu_plates"] != rec["VS"]["menu_plates"]:
                raise AssertionError("menu plates differ between roles")
            per_line[f"{tissue}|{sidm}"] = rec
            by_group[group].append(rec)
    summary = {}
    for group, recs in by_group.items():
        summary[group] = {
            "lines": len(recs), "menu": _q([r["menu"] for r in recs]), "M": _q([r["SV"]["M"] for r in recs]),
            "W": _q([r["SV"]["W"] for r in recs]), "menu_plates": _q([r["SV"]["menu_plates"] for r in recs]),
            "seeding_events_behind_menu_plates": _q([r["SV"]["seeding_events_behind_menu_plates"] for r in recs]),
            "menu_orientations_per_screen_plate_set_SV": _q([r["SV"]["menu_orientations_per_screen_component"] for r in recs]),
            "native_caps_sum_by_pct": {pct: int(sum(r["SV"]["native_caps"][pct] for r in recs)) for pct in nt.NATIVE_PCT_GRID},
            "menu_below_10": sum(1 for r in recs if r["menu"] < 10),
            "M_odd": sum(1 for r in recs if r["SV"]["M"] % 2)}
    out = {"status": "design-only (jaaks.DESIGN_COLUMNS; plate_hierarchy receipt events); written before any outcome "
                     "read of the resources workstream",
           "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "layout_summary": layout.summary,
           "native_pct_grid": list(nt.NATIVE_PCT_GRID), "summary": summary, "per_line": per_line,
           "wall_seconds": round(time.perf_counter() - t0, 2)}
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
