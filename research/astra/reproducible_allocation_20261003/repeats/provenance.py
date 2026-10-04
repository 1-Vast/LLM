"""Repeat provenance of the Jaaks et al. 2022 anchored screen: plate -> seeding event -> culture expansion.

File summary
- Path: research/astra/reproducible_allocation_20261003/repeats/provenance.py
- Purpose: recover and check the replicate hierarchy behind the same-condition repeats of the
  GDSC anchored screen (Jaaks et al. 2022 Nature 603:166). A plate barcode alone does not
  establish independent biological replication, so every plate of the fitted release is joined to
  the authors' raw-data plate records (figshare 19141916) and day-1 plate records (figshare
  19141919), whose per-plate fields are defined in the CancerRxGene gdscIC50 vignette
  ("GDSC raw data definitions"): DATE_CREATED = date the plate was seeded; SCAN_DATE = date of
  read-out; CELL_ID = the cell-line expansion from frozen stock (a new CELL_ID per expansion).
- Core points:
  - Raw files are read for design columns only (never INTENSITY). The fitted release is read for
    design columns plus the plate-level day-1 columns (DAY1_NORM_MEAN/SD, GROWTH_RATE,
    DOUBLING_TIME) behind an `exposed_ticket` (EXPLORATORY; no synergy outcome column is read).
  - Seeding event = (cell model, DATE_CREATED). The script checks that each seeding event has one
    day-1 plate, that the fitted DAY1 groups coincide one-to-one with seeding events, and counts
    seeding events (candidate biological repeats) and plates per event (candidate technical repeats)
    per 'anchor concentration - library - cell line' tuple against the paper's Methods
    (2-18 biological replicates, median 4; typically 3 technical per biological replicate).
  - Control and single-agent wells per plate are counted from the raw TAG column.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.repeats.provenance` writes
  `repeats/receipts/provenance.json`, `plate_hierarchy.csv`, `line_doublet_hierarchy.csv`, `line_summary.csv`;
  `... provenance --addendum` writes the post hoc design-only `provenance_addendum.json`;
  `load_plate_hierarchy()` for part B.
- Depends on: numpy, pandas; `..common.exposed_ticket`.
"""
from __future__ import annotations

import hashlib
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from ..common import JAAKS, ROOT, exposed_ticket

HERE = Path(__file__).resolve().parent
RECEIPTS = HERE / "receipts"
DOWNLOADS = ROOT / "data/external/jaaks2022_provenance"
RAW_ZIP = DOWNLOADS / "Original_screen_All_tissues_raw_data.csv.zip"
DAY1_ZIP = DOWNLOADS / "Original_screen_All_tissues_day1_data.csv.zip"
SUPP_TABLE2 = DOWNLOADS / "europepmc_supplementary/41586_2022_4437_MOESM5_ESM.xlsx"
RAW_DESIGN = ["BARCODE", "RESEARCH_PROJECT", "SCAN_ID", "DATE_CREATED", "SCAN_DATE", "CELL_ID", "MASTER_CELL_ID",
              "CELL_LINE_NAME", "SANGER_MODEL_ID", "SEEDING_DENSITY", "DRUGSET_ID", "ASSAY", "DURATION", "POSITION",
              "TAG", "DRUG_ID", "DRUG_NAME", "CONC"]
DAY1_DESIGN = ["RESEARCH_PROJECT", "BARCODE", "SCAN_ID", "DATE_CREATED", "SCAN_DATE", "MASTER_CELL_ID", "CELL_ID",
               "CELL_LINE_NAME", "SEEDING_DENSITY", "DRUGSET_ID", "ASSAY", "DURATION", "POSITION", "TAG"]
FITTED_COLUMNS = ["BARCODE", "Tissue", "CELL_LINE_NAME", "SIDM", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID",
                  "DAY1_NORM_MEAN", "DAY1_NORM_SD", "GROWTH_RATE", "DOUBLING_TIME"]
PAPER_REPEAT_LINES = {"Breast": ["AU565", "BT-474", "CAL-85-1", "HCC1937", "MFM-223"],
                      "Colon": ["HCT-15", "HT-29", "SK-CO-1", "SW620"],
                      "Pancreas": ["KP-1N", "KP-4", "MZ1-PC", "PA-TU-8988T", "SUIT-2"]}
DOCUMENTED_CONTROLS = {"NC-0 untreated": 6, "NC-1 DMSO": 126, "B blank": 28, "staurosporine": 20, "MG-132": 20}
SOURCES = {
    "paper_methods": "Jaaks et al. 2022 Nature 603:166, Methods 'Reproducibility' and 'Screening' (Europe PMC "
                     "PMC8891012 fullTextXML): 2-18 biological replicates for 4-5 lines per tissue (14 named lines), "
                     "technical replicates typically 3 per biological replicate; 'a parallel undrugged control plate "
                     "was assayed at the time of drug treatment ... day = 1 plate. This was repeated each time that a "
                     "cell line was screened.'",
    "field_definitions": "CancerRxGene/gdscIC50 vignettes/gdsc_raw_data_format.Rmd (GDSC raw data definitions): "
                         "DATE_CREATED = date the plate was seeded with cell line; SCAN_DATE = date the experiment "
                         "finished and was measured; CELL_ID = cell line expansion seeded on the plate, new CELL_ID "
                         "each time a line is expanded from frozen stocks; SEEDING_DENSITY = cells per well; "
                         "TAG NC-0 untreated, NC-1 DMSO, B blank, PCx-Dy-S positive-control titration, UN-USED.",
    "raw_plates": "figshare 19141916 Original_screen_All_tissues_raw_data.csv.zip (design columns only)",
    "day1_plates": "figshare 19141919 Original_screen_All_tissues_day1_data.csv.zip (design columns only)",
    "fitted": "figshare 16843597 original_screen_all_tissues_fitted.csv (design + plate-level day-1 columns, "
              "via exposed_ticket)",
    "supplementary_table_2": "Europe PMC PMC8891012 supplementaryFiles, 41586_2022_4437_MOESM5_ESM.xlsx: per-line "
                             "'Replicate cell line' yes/no and 'Seeding Density 1536well'",
    "peer_review_file": "41586_2022_4437_MOESM3_ESM.pdf, authors' rebuttal to referee 3 point 2: 'Each cancer-type "
                        "specific screen included 4-5 cell lines for which at least three independent biological "
                        "replicates were collected for all combinations over the duration of screening. Each "
                        "biological replicate was composed of three technical replicate plates.' Also: failed plates "
                        "were repeated where possible; 68 positive and 132 negative control wells per plate.",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _zip_csv(path: Path, columns: list[str], chunksize: int = 2_000_000) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        name = archive.namelist()[0]
        with archive.open(name) as handle:
            header = handle.readline().decode().strip().split(",")
        if "INTENSITY" in columns:
            raise ValueError("DESIGN_ONLY: INTENSITY is an outcome column")
        missing = [c for c in columns if c not in header]
        if missing:
            raise ValueError(f"MISSING_COLUMNS: {missing}")
        parts = []
        with archive.open(name) as handle:
            for chunk in pd.read_csv(handle, usecols=columns, dtype=str, chunksize=chunksize):
                parts.append(chunk.astype("category"))
    frame = pd.concat(parts, ignore_index=True)
    for column in frame.columns:
        frame[column] = frame[column].astype(str).str.strip()
    return frame


def _tag_class(tags: pd.Series) -> pd.Series:
    out = tags.str.replace(r"^A\d+-(S|C)$", r"anchor-\1", regex=True)
    out = out.str.replace(r"^L\d+-D\d+-(S|C)$", r"library-\1", regex=True)
    return out.str.replace(r"^(PC\d)-D\d+-S$", r"\1", regex=True)


def raw_plate_table(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """One row per assay plate (design fields) and the per-plate well census from TAG."""
    per_plate = raw.groupby("BARCODE")[["RESEARCH_PROJECT", "SCAN_ID", "DATE_CREATED", "SCAN_DATE", "CELL_ID",
                                         "MASTER_CELL_ID", "CELL_LINE_NAME", "SANGER_MODEL_ID", "SEEDING_DENSITY",
                                         "DRUGSET_ID", "ASSAY", "DURATION"]]
    unique = per_plate.nunique().max().to_dict()
    plates = per_plate.first().reset_index()
    wells = raw.assign(cls=_tag_class(raw["TAG"])).drop_duplicates(["BARCODE", "POSITION", "cls"])
    census = wells.groupby(["BARCODE", "cls"]).size().unstack(fill_value=0)
    positions = raw.groupby("BARCODE")["POSITION"].nunique()
    # DMSO-only positions (backfill tag without any treatment tag) are DMSO-treated untreated-equivalent wells
    tagsets = raw.groupby(["BARCODE", "POSITION"])["TAG"].agg(lambda s: "+".join(sorted(set(s))))
    dmso_only = (tagsets == "DMSO").groupby(level=0).sum()
    pc_dose = raw[raw["TAG"].str.match(r"^PC\d-D\d+-S$")].groupby(["BARCODE", "TAG"])["POSITION"].nunique()
    anchor_reps = raw[raw["TAG"].str.match(r"^A\d+-S$")].groupby(["BARCODE", "TAG"])["POSITION"].nunique()
    library_reps = raw[raw["TAG"].str.match(r"^L\d+-D\d+-S$")].groupby(["BARCODE", "TAG"])["POSITION"].nunique()
    pc_names = raw[raw["TAG"].str.match(r"^PC\d")].assign(pc=lambda d: d["TAG"].str[:3]).groupby("pc")[
        "DRUG_NAME"].agg(lambda s: sorted(set(s) - {"nan"}))

    def dist(series: pd.Series) -> dict:
        values = series.to_numpy(float)
        return {"plates_or_groups": int(values.size), "min": float(values.min()), "median": float(np.median(values)),
                "max": float(values.max()), "distinct": sorted(set(int(v) for v in values))[:12]}

    controls = {
        "plates": int(len(census)),
        "positions_per_plate": dist(positions),
        "wells_by_class_per_plate": {c: dist(census[c]) for c in census.columns},
        "dmso_only_positions_per_plate": dist(dmso_only.reindex(census.index, fill_value=0)),
        "positive_control_wells_per_dose": {tag: dist(v) for tag, v in pc_dose.groupby(level=1)},
        "positive_control_drugs": {k: v for k, v in pc_names.items()},
        "anchor_single_agent_wells_per_anchor_tag": dist(anchor_reps),
        "library_single_agent_wells_per_dose_tag": dist(library_reps),
        "documented_per_plate": DOCUMENTED_CONTROLS,
    }
    return plates, {"per_plate_field_max_distinct": unique, "controls": controls}


def day1_plate_table(day1: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    per_plate = day1.groupby("BARCODE")[["RESEARCH_PROJECT", "SCAN_ID", "DATE_CREATED", "SCAN_DATE", "CELL_ID",
                                          "MASTER_CELL_ID", "CELL_LINE_NAME", "SEEDING_DENSITY", "DRUGSET_ID",
                                          "ASSAY", "DURATION"]]
    unique = per_plate.nunique().max().to_dict()
    tags = day1.drop_duplicates(["BARCODE", "POSITION", "TAG"]).groupby(["BARCODE", "TAG"]).size().unstack(fill_value=0)
    return per_plate.first().reset_index(), {"per_plate_field_max_distinct": unique, "plates": int(len(tags)),
                                             "tag_wells_per_plate": {c: sorted(set(tags[c].tolist())) for c in tags}}


def fitted_plate_table(ticket: dict, path: Path = JAAKS) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Per-plate design + day-1 fields of the fitted release, and the design rows (no synergy outcomes)."""
    if not ticket or ticket.get("data_sha256") != sha256(path):
        raise PermissionError("TICKET_REQUIRED: exposed_ticket for the fitted release")
    rows = pd.read_csv(path, usecols=FITTED_COLUMNS, low_memory=False,
                       dtype={"BARCODE": str, "ANCHOR_ID": str, "LIBRARY_ID": str, "ANCHOR_CONC": str, "SIDM": str})
    for column in ("BARCODE", "ANCHOR_ID", "LIBRARY_ID", "SIDM", "Tissue", "CELL_LINE_NAME", "ANCHOR_CONC"):
        rows[column] = rows[column].astype(str).str.strip()
    per_plate = rows.groupby("BARCODE")
    distinct = per_plate[["Tissue", "SIDM", "CELL_LINE_NAME", "DAY1_NORM_MEAN", "DAY1_NORM_SD", "GROWTH_RATE",
                          "DOUBLING_TIME"]].nunique(dropna=False).max().to_dict()
    plates = per_plate.agg(Tissue=("Tissue", "first"), SIDM=("SIDM", "first"), line=("CELL_LINE_NAME", "first"),
                           day1_mean=("DAY1_NORM_MEAN", "first"), growth=("GROWTH_RATE", "first"),
                           rows=("LIBRARY_ID", "size")).reset_index()
    doublet = per_plate["LIBRARY_ID"].agg(lambda s: "|".join(sorted(set(s))))
    plates["doublet"] = plates["BARCODE"].map(doublet)
    plates["n_library"] = plates["doublet"].str.count(r"\|") + 1
    return plates, rows[["BARCODE", "Tissue", "SIDM", "CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]], \
        {"per_plate_field_max_distinct": {k: int(v) for k, v in distinct.items()}}


def supp_table2(path: Path = SUPP_TABLE2) -> pd.DataFrame:
    """Supplementary Table 2 (cell lines) parsed from the xlsx XML (no openpyxl in the environment)."""
    import re

    with zipfile.ZipFile(path) as archive:
        shared = archive.read("xl/sharedStrings.xml").decode("utf-8")
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    strings = ["".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)) for si in re.findall(r"<si>(.*?)</si>", shared, re.S)]
    table = []
    for row in re.findall(r"<row [^>]*>(.*?)</row>", sheet, re.S):
        cells = {}
        for col, attr, body in re.findall(r'<c r="([A-Z]+)\d+"([^>]*)>(.*?)</c>', row, re.S):
            value = re.search(r"<v>(.*?)</v>", body)
            if value is None:
                text = re.search(r"<t[^>]*>(.*?)</t>", body)
                cells[col] = text.group(1) if text else ""
            else:
                cells[col] = strings[int(value.group(1))] if 't="s"' in attr else value.group(1)
        table.append(cells)
    header = table[0]
    columns = sorted(header, key=lambda c: (len(c), c))
    return pd.DataFrame([[r.get(c, "") for c in columns] for r in table[1:]], columns=[header[c] for c in columns])


def _ordinal_groups(values: pd.Series) -> pd.Series:
    """Integer group per distinct value (rounded to 12 significant digits)."""
    key = values.map(lambda v: "nan" if pd.isna(v) else f"{float(v):.12g}")
    return key.astype("category").cat.codes


def build(ticket: dict) -> dict:
    t0 = time.perf_counter()
    raw = _zip_csv(RAW_ZIP, RAW_DESIGN)
    raw_plates, raw_info = raw_plate_table(raw)
    del raw
    day1 = _zip_csv(DAY1_ZIP, DAY1_DESIGN)
    day1_plates, day1_info = day1_plate_table(day1)
    del day1
    fitted, design_rows, fitted_info = fitted_plate_table(ticket)
    read_seconds = time.perf_counter() - t0

    plates = fitted.merge(raw_plates, on="BARCODE", how="left", validate="one_to_one")
    unmatched = int(plates["DATE_CREATED"].isna().sum())
    plates["seeded"] = pd.to_datetime(plates["DATE_CREATED"]).dt.tz_convert(None)
    plates["scanned"] = pd.to_datetime(plates["SCAN_DATE"]).dt.tz_convert(None)
    plates["days_seed_to_read"] = (plates["scanned"] - plates["seeded"]).dt.days
    name_match = int((plates["line"] == plates["CELL_LINE_NAME"]).sum())
    sidm_match = int((plates["SIDM"] == plates["SANGER_MODEL_ID"]).sum())

    # day-1 plates: one per (line, seeding date)?
    d1 = day1_plates.assign(seeded=pd.to_datetime(day1_plates["DATE_CREATED"]).dt.tz_convert(None),
                            scanned=pd.to_datetime(day1_plates["SCAN_DATE"]).dt.tz_convert(None))
    d1["days_seed_to_read"] = (d1["scanned"] - d1["seeded"]).dt.days
    d1_per_event = d1.groupby(["CELL_LINE_NAME", "seeded"]).agg(day1_barcodes=("BARCODE", list),
                                                                 day1_cell_id=("CELL_ID", "first"),
                                                                 day1_density=("SEEDING_DENSITY", "first"))
    plates = plates.merge(d1_per_event.reset_index().rename(columns={"CELL_LINE_NAME": "line"}),
                          on=["line", "seeded"], how="left")
    plates["n_day1"] = plates["day1_barcodes"].map(lambda v: len(v) if isinstance(v, list) else 0)
    plates["day1_barcode"] = plates["day1_barcodes"].map(lambda v: v[0] if isinstance(v, list) and len(v) == 1 else None)
    plates["cell_id_matches_day1"] = plates["CELL_ID"] == plates["day1_cell_id"]
    plates["density_matches_day1"] = plates["SEEDING_DENSITY"] == plates["day1_density"]

    # Seeding events and DAY1 groups
    plates["event"] = plates["line"] + "@" + plates["seeded"].dt.strftime("%Y-%m-%d")
    plates["day1_group"] = plates["line"] + "#" + plates.groupby("line")["day1_mean"].transform(
        _ordinal_groups).astype(str)
    contingency = plates.groupby("day1_group")["event"].nunique()
    reverse = plates.groupby("event")["day1_group"].nunique()
    bijection = bool((contingency == 1).all() and (reverse == 1).all())
    growth_per_event = plates.groupby("event")["growth"].nunique()

    # barcode adjacency: day-1 barcode just below the event's assay barcodes?
    plates["barcode_int"] = plates["BARCODE"].astype(int)
    adj = plates.dropna(subset=["day1_barcode"]).groupby("event").agg(
        day1=("day1_barcode", "first"), lo=("barcode_int", "min"), hi=("barcode_int", "max"), n=("BARCODE", "size"))
    adj["day1"] = adj["day1"].astype(int)
    adj["gap"] = adj["lo"] - adj["day1"]
    adjacency = {"events": int(len(adj)), "day1_below_first_assay_barcode": int((adj["gap"] > 0).sum()),
                 "gap_1": int((adj["gap"] == 1).sum()), "gap_distribution": {
                     "min": int(adj["gap"].min()), "median": float(adj["gap"].median()), "max": int(adj["gap"].max())},
                 "assay_barcodes_contiguous_after_day1": int(((adj["hi"] - adj["day1"]) == adj["n"]).sum())}

    # per-line summary
    line_summary = plates.groupby(["Tissue", "line"]).agg(
        plates=("BARCODE", "size"), events=("event", "nunique"), day1_groups=("day1_group", "nunique"),
        cell_ids=("CELL_ID", "nunique"), doublets=("doublet", "nunique"),
        first=("seeded", "min"), last=("seeded", "max")).reset_index()
    per_doublet = plates.groupby(["Tissue", "line", "doublet"]).agg(
        plates=("BARCODE", "size"), events=("event", "nunique"), cell_ids=("CELL_ID", "nunique")).reset_index()
    line_doublet_max = per_doublet.groupby(["Tissue", "line"]).agg(max_plates_per_doublet=("plates", "max"),
                                                                    max_events_per_doublet=("events", "max"),
                                                                    median_events_per_doublet=("events", "median"))
    line_summary = line_summary.merge(line_doublet_max.reset_index(), on=["Tissue", "line"])
    multi = line_summary[line_summary["median_events_per_doublet"] >= 2]
    repeat_lines = sorted(multi["line"].tolist())
    paper_lines = sorted(sum(PAPER_REPEAT_LINES.values(), []))

    # hierarchy table per (line, doublet, event)
    hier = plates.groupby(["Tissue", "line", "doublet", "event"]).agg(
        seeded=("seeded", "first"), scanned=("scanned", "first"), plates=("BARCODE", "size"),
        barcodes=("BARCODE", lambda s: "|".join(sorted(s, key=int))), cell_id=("CELL_ID", "first"),
        day1_barcode=("day1_barcode", "first"), density=("SEEDING_DENSITY", "first"),
        drugsets=("DRUGSET_ID", lambda s: "|".join(sorted(set(s))))).reset_index()

    # tuple-level replicate counts (anchor conc - library - line) in the paper's repeat lines
    rows = design_rows.merge(plates[["BARCODE", "event"]], on="BARCODE")
    rows = rows[rows["CELL_LINE_NAME"].isin(paper_lines)]
    tuples = rows.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]).agg(
        bio=("event", "nunique"), plates=("BARCODE", "nunique"), rows=("BARCODE", "size"))
    tech = rows.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID", "event"])["BARCODE"].nunique()
    multi_t = tuples[tuples["bio"] >= 2]
    tuple_counts = {
        "tuples_in_repeat_lines": int(len(tuples)),
        "tuples_with_ge2_events": int(len(multi_t)),
        "events_per_tuple_ge2": {"min": int(multi_t["bio"].min()), "median": float(multi_t["bio"].median()),
                                 "max": int(multi_t["bio"].max()),
                                 "histogram": {int(k): int(v) for k, v in multi_t["bio"].value_counts().sort_index().items()}},
        "events_per_tuple_all": {"min": int(tuples["bio"].min()), "median": float(tuples["bio"].median()),
                                 "max": int(tuples["bio"].max())},
        "plates_per_tuple_event": {"min": int(tech.min()), "median": float(tech.median()), "max": int(tech.max()),
                                   "histogram": {int(k): int(v) for k, v in tech.value_counts().sort_index().items()}},
        "rows_per_tuple_plate_max": int((rows.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID",
                                                       "BARCODE"]).size()).max()),
        "paper": "2-18 biological replicates, median 4, per anchor concentration-library-cell line tuple; "
                 "technical replicates typically 3 per biological replicate",
    }
    other = rows  # noqa: F841  (kept for clarity)
    nonrepeat = plates[~plates["line"].isin(paper_lines)]
    nonrepeat_events_per_doublet = nonrepeat.groupby(["line", "doublet"])["event"].nunique()
    nonrepeat_plates_per_doublet = nonrepeat.groupby(["line", "doublet"]).size()

    supp = supp_table2()
    flagged = sorted(supp.loc[supp["Replicate cell line"].str.lower() == "yes", "Cell line"].tolist())
    density = plates.groupby("line")["SEEDING_DENSITY"].agg(lambda s: sorted(set(s)))
    supp_density = dict(zip(supp["Cell line"], supp["Seeding Density 1536well"]))
    density_mismatch = {line: {"raw": d, "supp_table_2": supp_density.get(line)} for line, d in density.items()
                        if [str(supp_density.get(line))] != d}
    checks = {
        "supp_table2_replicate_lines": flagged,
        "supp_table2_replicate_lines_equal_paper_lines": flagged == sorted(sum(PAPER_REPEAT_LINES.values(), [])),
        "seeding_density_raw_vs_supp_table2_mismatches": density_mismatch,
        "fitted_plates": int(len(fitted)), "raw_assay_plates": int(len(raw_plates)),
        "day1_plates": int(len(day1_plates)), "fitted_plates_unmatched_in_raw": unmatched,
        "line_name_matches": name_match, "sidm_matches": sidm_match,
        "fitted_plates_with_exactly_one_day1_plate": int((plates["n_day1"] == 1).sum()),
        "fitted_plates_with_no_day1_plate": int((plates["n_day1"] == 0).sum()),
        "fitted_plates_with_multiple_day1_plates": int((plates["n_day1"] > 1).sum()),
        "seeding_events": int(plates["event"].nunique()), "day1_groups_fitted": int(plates["day1_group"].nunique()),
        "day1_groups_equal_seeding_events_one_to_one": bijection,
        "day1_groups_spanning_several_events": int((contingency > 1).sum()),
        "events_spanning_several_day1_groups": int((reverse > 1).sum()),
        "events_with_one_growth_rate": int((growth_per_event == 1).sum()),
        "cell_id_equal_to_day1_cell_id": int(plates["cell_id_matches_day1"].sum()),
        "seeding_density_equal_to_day1": int(plates["density_matches_day1"].sum()),
        "days_seed_to_read_assay": {int(k): int(v) for k, v in plates["days_seed_to_read"].value_counts().items()},
        "days_seed_to_read_day1": {int(k): int(v) for k, v in d1["days_seed_to_read"].value_counts().items()},
        "cell_id_constant_within_event": bool((plates.groupby("event")["CELL_ID"].nunique() == 1).all()),
        "events_per_cell_id_in_repeat_lines": {
            line: {cid: int(n) for cid, n in g.groupby("CELL_ID")["event"].nunique().items()}
            for line, g in plates[plates["line"].isin(paper_lines)].groupby("line")},
        "barcode_adjacency": adjacency,
        "lines_with_median_ge2_events_per_doublet": repeat_lines,
        "paper_repeat_lines": paper_lines,
        "inferred_repeat_lines_equal_paper_lines": repeat_lines == paper_lines,
        "non_repeat_lines_events_per_doublet": {int(k): int(v) for k, v in
                                                nonrepeat_events_per_doublet.value_counts().sort_index().items()},
        "non_repeat_lines_plates_per_doublet": {int(k): int(v) for k, v in
                                                nonrepeat_plates_per_doublet.value_counts().sort_index().items()},
    }
    return {"plates": plates, "hierarchy": hier, "line_summary": line_summary, "per_doublet": per_doublet,
            "checks": checks, "tuple_counts": tuple_counts, "raw_info": raw_info, "day1_info": day1_info,
            "fitted_info": fitted_info, "read_seconds": round(read_seconds, 1)}


def status_from(checks: dict, tuples: dict) -> dict:
    """Decision rule (written before running): see `STATUS_RULE`."""
    documented_fields = (checks["fitted_plates_unmatched_in_raw"] == 0 and checks["sidm_matches"] == checks["fitted_plates"]
                         and checks["cell_id_constant_within_event"])
    day1_link = checks["fitted_plates_with_exactly_one_day1_plate"] == checks["fitted_plates"] and \
        checks["day1_groups_equal_seeding_events_one_to_one"]
    counts_match = (tuples["events_per_tuple_ge2"]["min"] == 2 and tuples["events_per_tuple_ge2"]["max"] == 18
                    and tuples["events_per_tuple_ge2"]["median"] == 4.0
                    and tuples["plates_per_tuple_event"]["median"] == 3.0
                    and checks["inferred_repeat_lines_equal_paper_lines"])
    plate_to_event = "AUTHENTICATED" if documented_fields and day1_link else (
        "CORROBORATED_NOT_AUTHENTICATED" if documented_fields or day1_link else "UNKNOWN")
    event_is_bio = "CORROBORATED_NOT_AUTHENTICATED" if counts_match and plate_to_event != "UNKNOWN" else "UNKNOWN"
    return {"plate_to_seeding_event_and_culture_expansion": plate_to_event,
            "seeding_event_equals_papers_biological_replicate": event_is_bio,
            "documented_fields_complete": documented_fields, "day1_link_complete": day1_link,
            "paper_counts_reproduced": counts_match}


STATUS_RULE = (
    "Plate -> (seeding event, culture expansion) is AUTHENTICATED when every fitted plate is found in the authors' "
    "raw plate records with one DATE_CREATED and one CELL_ID (fields defined by CancerRxGene gdscIC50) AND every "
    "plate has exactly one day-1 plate of the same line and seeding date AND the fitted DAY1 groups equal seeding "
    "events one-to-one; CORROBORATED_NOT_AUTHENTICATED if only one of the two holds; else UNKNOWN. The paper never "
    "publishes a plate -> 'biological replicate' table, so 'seeding event = the paper's biological replicate' can at "
    "most be CORROBORATED_NOT_AUTHENTICATED: it is so labelled when the event counts per tuple reproduce the Methods "
    "(range 2-18, median 4; plates per event median 3) and the multi-event lines are exactly the 14 named lines.")


def load_plate_hierarchy(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or RECEIPTS / "plate_hierarchy.csv", dtype={"BARCODE": str, "day1_barcode": str})


def main() -> int:
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    ticket = exposed_ticket("repeat provenance: plate-level design and day-1 columns (DAY1_NORM_MEAN/SD, GROWTH_RATE, "
                            "DOUBLING_TIME) only; no synergy outcome column", "repeats")
    out = build(ticket)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    keep = ["BARCODE", "Tissue", "line", "SIDM", "doublet", "n_library", "rows", "event", "day1_group", "seeded",
            "scanned", "days_seed_to_read", "CELL_ID", "SEEDING_DENSITY", "DRUGSET_ID", "RESEARCH_PROJECT",
            "SCAN_ID", "day1_barcode", "n_day1"]
    for name in ("plate_hierarchy.csv", "line_doublet_hierarchy.csv", "line_summary.csv"):
        if (RECEIPTS / name).exists():
            raise FileExistsError(f"NO_OVERWRITE: {name}")
    out["plates"][keep].sort_values(["Tissue", "line", "seeded", "BARCODE"]).to_csv(
        RECEIPTS / "plate_hierarchy.csv", index=False)
    out["hierarchy"].to_csv(RECEIPTS / "line_doublet_hierarchy.csv", index=False)
    out["line_summary"].to_csv(RECEIPTS / "line_summary.csv", index=False)
    status = status_from(out["checks"], out["tuple_counts"])
    paper_lines = out["checks"]["paper_repeat_lines"]
    hier = out["hierarchy"]
    rep = hier[hier["line"].isin(paper_lines)]
    table = []
    for (tissue, line, doublet), g in rep.groupby(["Tissue", "line", "doublet"]):
        table.append({"tissue": tissue, "line": line, "doublet": doublet, "groups": int(len(g)),
                      "plates_per_group": g["plates"].astype(int).tolist(),
                      "seeding_dates": g["seeded"].dt.strftime("%Y-%m-%d").tolist(),
                      "cell_ids": g["cell_id"].tolist(), "day1_barcodes": g["day1_barcode"].tolist()})
    receipt = {
        "label": "EXPLORATORY (exposed data); design and plate-level fields only",
        "started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ticket": ticket,
        "status": status["plate_to_seeding_event_and_culture_expansion"],
        "status_components": status, "status_rule": STATUS_RULE,
        "hierarchy": "cell line > culture expansion (CELL_ID; new ID per expansion from frozen stock) > seeding event "
                     "(DATE_CREATED, one day-1 plate, read 4 days after seeding) > assay plate (BARCODE; one library "
                     "doublet x all anchors, single combination replicate per plate) > wells",
        "independence_label": None,  # filled below
        "sources": SOURCES,
        "inputs": {"raw_zip": {"path": str(RAW_ZIP.relative_to(ROOT)), "sha256": sha256(RAW_ZIP)},
                   "day1_zip": {"path": str(DAY1_ZIP.relative_to(ROOT)), "sha256": sha256(DAY1_ZIP)},
                   "fitted": {"path": str(JAAKS.relative_to(ROOT)), "sha256": ticket["data_sha256"]}},
        "checks": out["checks"], "tuple_replicate_counts": out["tuple_counts"],
        "controls_per_plate": out["raw_info"]["controls"],
        "raw_per_plate_field_max_distinct": out["raw_info"]["per_plate_field_max_distinct"],
        "day1_info": out["day1_info"], "fitted_info": out["fitted_info"],
        "repeat_line_hierarchy": table,
        "files": ["repeats/receipts/plate_hierarchy.csv", "repeats/receipts/line_doublet_hierarchy.csv",
                  "repeats/receipts/line_summary.csv"],
        "read_seconds": out["read_seconds"],
    }
    shared = sum(1 for v in out["checks"]["events_per_cell_id_in_repeat_lines"].values() if len(v) == 1)
    receipt["independence_label"] = (
        "Same-condition repeats in different seeding events are separate seedings on different dates, each with its "
        "own day-1 plate, dosing and read-out (the paper's 'biological replicates'); "
        f"in {shared} of 14 repeat lines all events come from ONE culture expansion (one CELL_ID), so they are "
        "repeated passages of one expansion, not independent frozen stocks. Plates within one seeding event share "
        "seeding, cell suspension, dates and day-1 reference: technical repeats, never independent units.")
    target = RECEIPTS / "provenance.json"
    if target.exists():
        raise FileExistsError("NO_OVERWRITE: provenance.json")
    target.write_text(json.dumps(receipt, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "components": status, "checks": out["checks"],
                      "tuples": out["tuple_counts"]}, indent=1, default=str))
    return 0


def addendum() -> dict:
    """POST HOC design-only diagnostics written after provenance.json (never edits it)."""
    from research.astra.feedback_validation_20261003.jaaks import DESIGN_COLUMNS, _read

    plates = load_plate_hierarchy()
    plates["seeded"] = pd.to_datetime(plates["seeded"])
    plates["scanned"] = pd.to_datetime(plates["scanned"])
    local_day = lambda t: pd.to_datetime(t.dt.tz_localize("UTC").dt.tz_convert("Europe/London").dt.date)  # noqa: E731
    london = (local_day(plates["scanned"]) - local_day(plates["seeded"])).dt.days
    rows = _read(JAAKS, DESIGN_COLUMNS).merge(plates[["BARCODE", "event"]], on="BARCODE")
    paper_lines = sorted(sum(PAPER_REPEAT_LINES.values(), []))
    rep = rows[rows["CELL_LINE_NAME"].isin(paper_lines)]
    anchor_events = rep.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC"])["event"].nunique()
    combo = rep.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"])
    combo_events = combo["event"].nunique()
    combo_plates = combo["BARCODE"].nunique()
    no_day1 = plates[plates["n_day1"] == 0].groupby(["line", "event"]).size()
    extra = sorted(set(plates.groupby(["line", "doublet"])["event"].nunique().groupby(level=0).median()
                       .loc[lambda s: s >= 2].index) - set(paper_lines))
    extra_detail = {}
    for line in extra:
        g = plates[plates["line"] == line]
        extra_detail[line] = {"plates": int(len(g)), "events": int(g["event"].nunique()),
                              "doublets": int(g["doublet"].nunique()),
                              "events_per_doublet": {int(k): int(v) for k, v in
                                                     g.groupby("doublet")["event"].nunique().value_counts().items()}}
    hier = pd.read_csv(RECEIPTS / "line_doublet_hierarchy.csv", dtype=str)
    hier["plates"] = hier["plates"].astype(int)
    hrep = hier[hier["line"].isin(paper_lines)]
    return {
        "label": "POST HOC addendum (design-only), written after provenance.json; provenance.json and its "
                 "pre-specified status are unchanged",
        "plates_without_public_day1_plate": {
            "plates": int(no_day1.sum()), "events": int(len(no_day1)),
            "events_list": [f"{e}" for (_, e) in no_day1.index],
            "note": "no day-1 plate of the same line within +-72 h in the public day-1 file (not a time-zone artefact); "
                    "these events still carry their own distinct DAY1_NORM_MEAN in the fitted release, so the "
                    "DAY1-group = seeding-event identity holds for all 606 events"},
        "seed_to_read_days_london_calendar": {int(k): int(v) for k, v in london.value_counts().items()},
        "seed_to_read_note": "the 38 plates with 3 days in UTC are seeded at 00:00Z (GMT) and read at 23:00Z (BST) "
                             "or similar: 4 calendar days in Europe/London",
        "replicate_counts_vs_paper": {
            "combination_tuples_events": {"min": int(combo_events.min()), "median": float(combo_events.median()),
                                          "max": int(combo_events.max()),
                                          "median_among_ge2": float(combo_events[combo_events >= 2].median())},
            "combination_tuples_plates": {"min": int(combo_plates.min()), "median": float(combo_plates.median()),
                                          "max": int(combo_plates.max())},
            "anchor_concentration_events_per_line": {"min": int(anchor_events.min()),
                                                     "median": float(anchor_events.median()),
                                                     "max": int(anchor_events.max())},
            "plates_per_line_doublet_event": {int(k): int(v) for k, v in hrep["plates"].value_counts().sort_index().items()},
            "doublets_with_a_three_plate_event_per_line": {k: int(v) for k, v in
                                                           hrep[hrep["plates"] == 3].groupby("line")["doublet"].nunique().items()},
            "reading": "Seeding events reproduce the documented minimum (2) and median (4) biological replicates per "
                       "combination tuple; the documented maximum 18 equals the largest number of seeding events per "
                       "anchor concentration in a line (AU565, single-agent anchor wells are on every plate), not per "
                       "combination tuple (max 5). 'Typically 3 technical replicates per biological replicate' "
                       "(peer-review file: 'three technical replicate plates') is NOT reproduced for combinations: "
                       "most (line, doublet, event) cells hold 1 plate; 3-plate events exist for 2-5 doublets per line."},
        "multi_event_lines_not_flagged_in_supp_table_2": extra_detail,
        "multi_event_note": "these lines are not 'Replicate cell line' in Supplementary Table 2; the peer-review file "
                            "states failed plates were repeated where possible, which would create such repeats; "
                            "they are not used as repeat lines here",
        "screen_round_structure": "in the repeat lines each seeding event covers about half of a line's doublets (6-7 "
                                  "of 13-14 in colon/pancreas), so two neighbouring events form one pass over the menu; "
                                  "per doublet, its events are different passes",
    }


def write_addendum() -> int:
    # v1 (provenance_addendum.json) subtracted tz-aware midnights across the BST change and reported 3 days for
    # 38 plates; v2 compares Europe/London calendar dates (deviation D4).
    target = RECEIPTS / "provenance_addendum_v2.json"
    if target.exists():
        raise FileExistsError("NO_OVERWRITE: provenance_addendum_v2.json")
    result = addendum()
    target.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, indent=1, default=str)[:4000])
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(write_addendum() if sys.argv[1:] == ["--addendum"] else main())
