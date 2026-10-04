"""Design-only plate layout of a Jaaks-format release for resource accounting (no outcome column).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/layout.py
- Purpose: everything the resources workstream needs that is NOT an outcome: the builder-order menu
  (pairs with both orientations designed), per-orientation design plates, rows and barcodes, the
  native plate composition (one line x one library doublet x all anchors per plate), the library
  doublets ("components") that define a native plate-set action, and the seeding event behind every
  plate (from the earlier study's provenance receipt, design fields only).
- Core points:
  - Reads only `jaaks.DESIGN_COLUMNS` through the frozen `jaaks._read`; never the outcome columns.
  - The menu is built exactly like the frozen builder's (sorted (s, v, SIDM), S x V pairs with both
    orientations present). The builder's QC excluded 0 of 296,707 rows, so on Jaaks this equals the
    builder menu; `check_against_panels` asserts it after the outcome read.
  - Line index = position of the SIDM in the per-tissue sorted line tuple of the menu (the builder's
    `lines`), as the frozen contract v2 tie-break requires.
  - Controls per plate: documented 200; raw layout 216 fixed (6 NC-0, 114 NC-1, 28 blank, 34 MG-132,
    34 staurosporine) + 0/10/38 DMSO-only positions (median 10), i.e. 216-254
    (`reproducible_allocation_20261003/repeats/receipts/provenance.json`).
- Interfaces: `read_design`, `build_layout`, `Layout`, `TissueLayout`, `CONTROL_VARIANTS`,
  `load_events`.
- Depends on: numpy, pandas; the frozen `research.astra.feedback_validation_20261003.jaaks`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.feedback_validation_20261003 import jaaks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PLATE_HIERARCHY = ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/plate_hierarchy.csv"
PROVENANCE = ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/provenance.json"

ROLES = ("SV", "VS")
ROLE_INDEX = {"SV": 0, "VS": 1}
DOSES, ANCHOR_CONCS = 7, 2
WELLS_PER_PLATE_MEASUREMENT = DOSES * ANCHOR_CONCS          # 14 combination wells per orientation per plate
PLATE_WELLS = 1536
ANCHOR_SINGLE_WELLS = 5 * 2                                  # 5 reps x 2 anchor concentrations
LIBRARY_SINGLE_WELLS = 4 * 7                                 # 4 reps x 7 library doses
CONTROLS_DOCUMENTED = 200                                    # 6 untreated + 126 DMSO + 28 blank + 20 + 20
CONTROLS_RAW_FIXED = 6 + 114 + 28 + 34 + 34                  # 216: identical on every raw plate
CONTROL_VARIANTS = {"documented_200": 200, "raw_min_216": 216, "raw_median_226": 226, "raw_max_254": 254}
MIN_DAYS_PER_ROUND = 4


@dataclass
class TissueLayout:
    tissue: str
    code: int
    lines: tuple                 # builder lines tuple: sorted SIDM of the tissue menu
    side: dict                   # drug -> 'S' | 'V' (frozen split)
    components: list             # sorted library-drug components (doublets), jaaks._doublets order
    comp_of: dict                # library drug -> component index
    s: np.ndarray                # per menu row (builder order)
    v: np.ndarray
    sidm: np.ndarray
    c: np.ndarray                # line index per menu row
    pair_id: np.ndarray          # (s, v) identity within the tissue

    def rows_of(self, line_index: int) -> np.ndarray:
        return np.flatnonzero(self.c == line_index)


@dataclass
class Layout:
    tissues: dict                                   # tissue -> TissueLayout
    orient: dict                                    # (tissue, sidm, anchor, library) -> (plates, rows, barcodes)
    plate: dict                                     # barcode -> {tissue, sidm, comp, rows, anchors, libs}
    line_comp: dict                                 # (tissue, sidm, comp) -> tuple of barcodes
    comp_orients: dict                              # (tissue, sidm, comp) -> {(anchor, library): rows}
    events: dict = field(default_factory=dict)      # barcode -> seeding event id
    source: str = ""
    summary: dict = field(default_factory=dict)


def read_design(path: Path) -> pd.DataFrame:
    """Design columns only, through the frozen builder's reader."""
    return jaaks._read(path, jaaks.DESIGN_COLUMNS)


def load_events(path: Path = PLATE_HIERARCHY) -> dict:
    """barcode -> seeding event (line@date) from the earlier provenance receipt (design fields only)."""
    if not Path(path).is_file():
        return {}
    h = pd.read_csv(path, dtype=str)
    return {str(b).strip(): str(e) for b, e in zip(h["BARCODE"], h["event"])}


def build_layout(path: Path, events: dict | None = None) -> Layout:
    d = read_design(path)
    orient_g = d.groupby(["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID"])["BARCODE"]
    plates = orient_g.nunique()
    rows = orient_g.size()
    barcodes = orient_g.agg(lambda s: tuple(sorted(set(s))))
    orient = {k: (int(p), int(r), b) for k, p, r, b in
              zip(plates.index, plates.to_numpy(), rows.to_numpy(), barcodes.to_numpy())}
    tissues: dict = {}
    plate: dict = {}
    line_comp: dict = {}
    comp_orients: dict = {}
    for tissue, g in d.groupby("Tissue"):
        side = jaaks.split_drugs(tissue, g)
        components = jaaks._doublets(g)
        comp_of = {x: i for i, comp in enumerate(components) for x in comp}
        a_side, l_side = g["ANCHOR_ID"].map(side), g["LIBRARY_ID"].map(side)
        cross = g[a_side.notna() & l_side.notna() & (a_side != l_side)]
        s_anch = cross["ANCHOR_ID"].map(side) == "S"
        o = pd.DataFrame({"s": np.where(s_anch, cross["ANCHOR_ID"], cross["LIBRARY_ID"]),
                          "v": np.where(s_anch, cross["LIBRARY_ID"], cross["ANCHOR_ID"]),
                          "SIDM": cross["SIDM"].to_numpy(), "sa": s_anch.to_numpy()})
        both = o.groupby(["s", "v", "SIDM"])["sa"].nunique()
        menu = both[both == 2].index.sort_values()
        ms = np.array(menu.get_level_values(0), dtype=object)
        mv = np.array(menu.get_level_values(1), dtype=object)
        msidm = np.array(menu.get_level_values(2), dtype=object)
        lines = tuple(sorted(set(msidm)))
        li = {x: i for i, x in enumerate(lines)}
        keys = np.array([f"{a}|{b}" for a, b in zip(ms, mv)], dtype=object)
        _, pair_id = np.unique(keys, return_inverse=True)
        tissues[tissue] = TissueLayout(tissue, jaaks.TISSUE_CODE[tissue], lines, side, components, comp_of,
                                       ms, mv, msidm, np.array([li[x] for x in msidm], np.int64),
                                       pair_id.astype(np.int64))
        g = g.assign(comp=g["LIBRARY_ID"].map(comp_of))
        pb = g.groupby("BARCODE").agg(sidm=("SIDM", "first"), lines=("SIDM", "nunique"), comp=("comp", "first"),
                                      comps=("comp", "nunique"), rows=("SIDM", "size"),
                                      anchors=("ANCHOR_ID", "nunique"), libs=("LIBRARY_ID", "nunique"))
        if int(pb["lines"].max()) != 1 or int(pb["comps"].max()) != 1:
            raise AssertionError(f"{tissue}: a plate holds several lines or several library components")
        for b, r in pb.iterrows():
            plate[str(b)] = {"tissue": tissue, "sidm": r["sidm"], "comp": int(r["comp"]), "rows": int(r["rows"]),
                             "anchors": int(r["anchors"]), "libs": int(r["libs"])}
        for (sidm, comp), sub in g.groupby(["SIDM", "comp"]):
            line_comp[(tissue, sidm, int(comp))] = tuple(sorted(set(sub["BARCODE"])))
            comp_orients[(tissue, sidm, int(comp))] = {
                (a, b): int(n) for (a, b), n in sub.groupby(["ANCHOR_ID", "LIBRARY_ID"]).size().items()}
    ev = load_events() if events is None else events
    summary = {"rows": int(len(d)), "plates": int(d["BARCODE"].nunique()),
               "menu_pair_x_line": {t: int(tl.s.size) for t, tl in tissues.items()},
               "lines": {t: len(tl.lines) for t, tl in tissues.items()},
               "components": {t: len(tl.components) for t, tl in tissues.items()},
               "plates_with_event": int(sum(1 for b in plate if b in ev))}
    return Layout(tissues, orient, plate, line_comp, comp_orients, ev, str(path), summary)


def event_of(layout: Layout, barcode: str) -> str:
    """Seeding event of a plate; plates without a provenance record count as their own event."""
    return layout.events.get(barcode, f"{layout.plate[barcode]['sidm']}@plate:{barcode}")


def check_against_panels(layout: Layout, panels: dict, candidates: dict) -> dict:
    """After the outcome read: the design-derived menu must equal the frozen builder's menu exactly."""
    out = {}
    for tissue, tl in layout.tissues.items():
        cand = candidates[tissue]
        if list(cand["line_sidm"]) != list(tl.lines):
            raise AssertionError(f"{tissue}: builder lines differ from the design layout")
        pairs = [tuple(p) for p in cand["pairs_s_v"]]
        if pairs != list(zip(tl.s.tolist(), tl.v.tolist())):
            raise AssertionError(f"{tissue}: builder menu differs from the design menu")
        for role in ROLES:
            lib = panels[f"{tissue}_{role}"].library
            if not np.array_equal(np.asarray(lib.c), tl.c):
                raise AssertionError(f"{tissue}_{role}: line index per menu row differs")
        out[tissue] = {"menu": int(tl.s.size), "lines": len(tl.lines), "identical": True}
    return out
