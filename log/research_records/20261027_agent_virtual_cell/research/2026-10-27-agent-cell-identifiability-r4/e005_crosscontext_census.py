"""E005: cross-context design census (metadata only, no response values used).

Pre-registered in PROTOCOL_E005.md. Answers whether the archive contains enough
comparable cross-background order comparisons for an aggregate ordinal test,
given the detectability floor calibrated in E004.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r4"
ANCHORS = {"high control", "low control"}
# columns that must never be read into this analysis
FORBIDDEN = ["Viability", "Raw count"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    header = pd.read_csv(CSV, nrows=0)
    cols = [c.strip() for c in header.columns]
    usecols = [c for c in ("Well", "Cell line", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)",
                           "Failed QC", "Iteration", "file", "Plate") if c in cols]
    assert not (set(usecols) & set(FORBIDDEN)), "response columns must not be loaded"
    df = pd.read_csv(CSV, usecols=usecols, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well", "Plate"):
        df[c] = df[c].astype(str).str.strip()
    df["Iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")

    # layout signature per file, restricted to non-anchor wells (anchor blocks are identical everywhere)
    sig = {}
    per_file_cells = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        sig[fname] = {"cell": g["Cell line"].iloc[0],
                      "iteration": int(g["Iteration"].iloc[0]) if pd.notna(g["Iteration"].iloc[0]) else -1,
                      "layout_hash": hashlib.sha1(repr(layout).encode()).hexdigest(),
                      "unit": {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}}
        per_file_cells[fname] = len(layout)
    sig_df = pd.DataFrame([{k: v for k, v in s.items() if k != "unit"} | {"file": f} for f, s in sig.items()])

    layouts = defaultdict(lambda: defaultdict(list))  # (iter, hash) -> cell -> [files]
    units = {}  # (iter, hash) -> layout unit map (identical across files by construction)
    for f, s in sig.items():
        layouts[(s["iteration"], s["layout_hash"])][s["cell"]].append(f)
    layout_stats = []
    for (it, h), cells in layouts.items():
        layout_stats.append({"iteration": it, "layout_hash": h[:12], "n_cells": len(cells),
                             "n_files": sum(len(v) for v in cells.values()),
                             "files_per_cell": sorted(len(v) for v in cells.values())})
    ls = pd.DataFrame(layout_stats)

    # cross-context comparable units: (layout, well) present in >=2 cells, and count real double-drug units
    unit_rows = []
    for (it, h), cells in layouts.items():
        f0 = next(iter(cells.values()))[0]
        unit = sig[f0]["unit"]
        for well, (d1, c1, d2, c2) in unit.items():
            combo = (d1.lower() != "dmso") and (d2.lower() != "dmso")
            pair = tuple(sorted([(d1, c1), (d2, c2)]))
            unit_rows.append({"iteration": it, "layout_hash": h[:12], "well": well,
                              "n_cells": len(cells), "double_drug": combo,
                              "pair_key": pair,
                              "cells_with_two_plus_files": sum(1 for v in cells.values() if len(v) >= 2)})
    u = pd.DataFrame(unit_rows)

    def summarize(frame: pd.DataFrame, label: str) -> dict:
        multi = frame[frame["n_cells"] >= 2]
        # a cross-context comparison = unordered cell pair within a layout x unit
        cc_pairs = int((multi["n_cells"] * (multi["n_cells"] - 1) / 2).sum())
        deep = multi[multi["cells_with_two_plus_files"] >= 2]
        deep_pairs = int((deep["cells_with_two_plus_files"] * (deep["cells_with_two_plus_files"] - 1) / 2).sum())
        # unique drug-pair+dose keys that are comparable across contexts
        keys = multi["pair_key"].nunique()
        return {"label": label, "n_units": int(len(frame)), "n_units_multi_cell": int(len(multi)),
                "cross_context_unit_pairs": cc_pairs,
                "cross_context_unit_pairs_both_cells_with_2plus_files": deep_pairs,
                "n_units_both_cells_2plus_files": int(len(deep)),
                "unique_pair_dose_keys_comparable": int(keys),
                "max_cells_per_unit": int(frame["n_cells"].max()) if len(frame) else 0}

    all_u = summarize(u, "all non-anchor wells")
    combo_u = summarize(u[u["double_drug"]], "double-drug combinations only")

    # detail of the multi-cell layouts: these are the paired designs that make a cross-context test possible
    multi_cell_detail = []
    for (it, h), cells in sorted(layouts.items()):
        if len(cells) < 2:
            continue
        f0 = next(iter(cells.values()))[0]
        unit = sig[f0]["unit"]
        n_combo = sum(1 for w, (d1, c1, d2, c2) in unit.items()
                      if d1.lower() != "dmso" and d2.lower() != "dmso")
        multi_cell_detail.append({"iteration": it, "layout_hash": h[:12],
                                  "n_cells": len(cells), "cells": sorted(cells),
                                  "files_per_cell": sorted(len(v) for v in cells.values()),
                                  "n_units": len(unit), "n_double_drug_units": n_combo,
                                  "example_files": [next(iter(cells.values()))[0],
                                                    next(iter(cells.values()))[-1]]})
    multi_cell_detail.sort(key=lambda r: (-r["n_cells"], -r["n_units"]))

    out = {
        "kind": "design_metadata_census_not_a_response_analysis",
        "input_sha256": sha256(CSV),
        "response_columns_loaded": False,
        "n_files": int(sig_df["file"].nunique()),
        "n_cells": int(sig_df["cell"].nunique()),
        "n_layout_groups": int(len(ls)),
        "layout_groups_multi_cell": int((ls["n_cells"] >= 2).sum()),
        "layout_cell_count_distribution": {int(k): int(v) for k, v in ls["n_cells"].value_counts().sort_index().items()},
        "files_per_layout_distribution": {int(k): int(v) for k, v in ls["n_files"].value_counts().sort_index().items()},
        "all_non_anchor": all_u,
        "double_drug_only": combo_u, "multi_cell_layouts": multi_cell_detail,
        "interpretation_limits": [
            "Comparable units share the same drug-plate layout; cells in one layout may share a batch of plates, so pairs are not independent biological replicates.",
            "No response value was read; this cannot support any claim about which orderings actually differ.",
            "Multiplicity: cells within a layout are not randomly assigned.",
        ],
    }

    # feasibility verdict against E004 capability bound + aggregate sample-size requirement
    e004 = json.loads((OUT / "E004_RESULTS.json").read_text(encoding="utf-8"))
    sigma = e004["N1_corrected"]["sigma_e_primary_level_matched"]
    min_d_two_plates = 1.959964 * sigma
    agg = {a["true_reversal_excess_over_half"]: a["m_pairs_needed_ideal_noise"]
           for a in e004["aggregate_ordinal_sample_size"]}
    need39 = agg.get(0.2)
    verdict = {
        "sigma_e_from_e004": sigma,
        "min_detectable_d_two_plates_95pct": min_d_two_plates,
        "independent_pairs_needed_ideal_noise_excess_0.2": need39,
        "available_double_drug_cross_context_unit_pairs": combo_u["cross_context_unit_pairs"],
        "available_double_drug_pairs_both_cells_two_plus_files": combo_u["cross_context_unit_pairs_both_cells_with_2plus_files"],
        "ratio_available_over_needed": (combo_u["cross_context_unit_pairs"] / need39) if need39 else None,
        "caveat": ("Counts are opportunity counts, not independent tests: units inside one layout share plates, "
                   "and the same drug pair at the same dose appears in only a few cells. The effective independent "
                   "count is expected to be smaller than the opportunity count."),
    }
    out["feasibility_for_aggregate_ordinal_test"] = verdict
    for rel in ("research/2026-10-27-agent-cell-identifiability-r4/PROTOCOL_E005.md",
                "research/2026-10-27-agent-cell-identifiability-r4/e005_crosscontext_census.py",
                "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"):
        p = ROOT / rel
        if p.exists():
            out.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E005_RESULTS.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"files={out['n_files']} cells={out['n_cells']} layout_groups={out['n_layout_groups']} multi_cell={out['layout_groups_multi_cell']}")
    print("layout n_cells distribution:", out["layout_cell_count_distribution"])
    for lab in ("all_non_anchor", "double_drug_only"):
        d = out[lab]
        print(f"[{lab}] units={d['n_units']} multi_cell_units={d['n_units_multi_cell']} "
              f"cross_ctx_pairs={d['cross_context_unit_pairs']} "
              f"pairs_both_cells_2plus_files={d['cross_context_unit_pairs_both_cells_with_2plus_files']} "
              f"unique_keys={d['unique_pair_dose_keys_comparable']} max_cells={d['max_cells_per_unit']}")
    print("feasibility:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in verdict.items() if k != "caveat"})


if __name__ == "__main__":
    main()
