"""Metadata-only census for the certified-discovery Gate 0 / Gate 1 study.

Reads layout and identity fields only. No response field (INTENSITY, inhibition,
lib*_y, lib*_yhat, HSA*, Bliss*, or any fitted synergy value) is converted, stored or
summarised here. AZ rows whose MASTER_CELL_ID is not one of the 320 exposed cells of the
2026-10-22 paid-reference design are discarded immediately after CSV tokenisation.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261023/certified_discovery_gates"
AZ_ZIP = ROOT / "data/external/research_sources/20261022/intervention_program_renewal/az_design/matrix_well_stats_GDSC_007_010_plus_Spiper1.zip"
AZ_ZIP_SHA = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
AZ_MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
AZ_DESIGN = ROOT / "log/20261022/az_paid_reference_gate/DESIGN.json"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare"
JAAKS_ORIGINAL = JAAKS / "Original screen_All tissues_fitted data.csv"
JAAKS_VALIDATION = JAAKS / "Validation screen_All tissues_fitted data.csv"
JAAKS_RAW = JAAKS / "Original_screen_All_tissues_raw_data.csv.zip"
AZ_META = ["PROJECT_ID", "BARCODE", "DRUGSET_ID", "MASTER_CELL_ID", "CELL_ID", "POSITION",
           "lib1_dose", "lib1_drug_id", "lib1_conc", "lib2_dose", "lib2_drug_id", "lib2_conc",
           "treatment", "cmatrix"]
JAAKS_META = ["BARCODE", "COMBI_ID", "Tissue", "SIDM", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def distribution(values):
    return {str(k): v for k, v in sorted(Counter(values).items(), key=lambda kv: float(kv[0]))}


def az_census():
    assert sha(AZ_ZIP) == AZ_ZIP_SHA, "pinned AZ archive hash mismatch"
    roles = json.loads(AZ_DESIGN.read_text(encoding="utf-8"))["role_cells"]
    exposed = set(roles["train"]) | set(roles["validation"]) | set(roles["test"])
    reserve = set(roles["reserve"])
    assert len(exposed) == 320 and len(reserve) == 413 and not exposed & reserve
    skipped = Counter()
    matrices = {}
    with zipfile.ZipFile(AZ_ZIP) as archive, archive.open(AZ_MEMBER) as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
        header = next(reader)
        ix = {name: i for i, name in enumerate(header)}
        master_ix = ix["MASTER_CELL_ID"]
        for row in reader:
            master = row[master_ix]
            if master not in exposed:
                skipped["reserve" if master in reserve else "unassigned"] += 1
                continue
            meta = {name: row[ix[name]] for name in AZ_META}
            key = (meta["BARCODE"], meta["cmatrix"])
            m = matrices.setdefault(key, {"master": master, "cell_id": meta["CELL_ID"], "drugset": meta["DRUGSET_ID"],
                                          "drugs": set(), "c1": set(), "c2": set(), "wells": 0, "treatment": set()})
            m["drugs"].add((meta["lib1_drug_id"], meta["lib2_drug_id"]))
            m["c1"].add(meta["lib1_conc"])
            m["c2"].add(meta["lib2_conc"])
            m["treatment"].add(meta["treatment"])
            m["wells"] += 1
    shapes = Counter(f"{len(m['c1'])}x{len(m['c2'])}" for m in matrices.values())
    multi_drug = sum(len(m["drugs"]) > 1 for m in matrices.values())
    by_unit = defaultdict(list)
    for (barcode, cmatrix), m in matrices.items():
        if len(m["drugs"]) != 1:
            continue
        a, b = next(iter(m["drugs"]))
        by_unit[(m["master"], tuple(sorted((a, b))))].append((barcode, cmatrix))
    plates_per_unit = Counter(len({b for b, _ in v}) for v in by_unit.values())
    within_plate = sum(len(v) > len({b for b, _ in v}) for v in by_unit.values())
    return {
        "member": AZ_MEMBER, "archive_sha256": AZ_ZIP_SHA,
        "rows_skipped_before_any_field_use": dict(skipped),
        "exposed_cells_seen": len({m["master"] for m in matrices.values()}),
        "matrices": len(matrices), "matrices_with_more_than_one_drug_pair": multi_drug,
        "treatment_values": sorted(set().union(*(m["treatment"] for m in matrices.values()))),
        "wells_per_matrix": distribution(m["wells"] for m in matrices.values()),
        "dose_grid_shapes": dict(shapes.most_common()),
        "cell_pair_units": len(by_unit),
        "distinct_plates_per_cell_pair_unit": {str(k): v for k, v in sorted(plates_per_unit.items())},
        "units_with_two_or_more_matrices_on_one_plate": within_plate,
        "response_fields_converted": [],
    }


def jaaks_fitted_census():
    original = pd.read_csv(JAAKS_ORIGINAL, usecols=JAAKS_META, dtype=str)
    validation = pd.read_csv(JAAKS_VALIDATION, usecols=JAAKS_META, dtype=str)
    unit = ["SIDM", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]
    out = {}
    for name, d in (("original", original), ("validation", validation)):
        per_unit = d.groupby(unit).BARCODE.nunique()
        out[name] = {"rows": len(d), "plates": d.BARCODE.nunique(), "lines": d.SIDM.nunique(),
                     "anchors": d.ANCHOR_ID.nunique(), "libraries": d.LIBRARY_ID.nunique(),
                     "combinations": d.COMBI_ID.nunique(), "units": len(per_unit),
                     "plates_per_unit": {str(k): int(v) for k, v in per_unit.value_counts().sort_index().items()}}
    vu = validation.groupby(unit).BARCODE.nunique()
    ou = set(map(tuple, original[unit].drop_duplicates().values))
    pool = [k for k, n in vu.items() if k in ou and n >= 2]
    out["validation_units_in_original"] = int(sum(k in ou for k in vu.index))
    out["pool_units_with_2plus_validation_plates"] = len(pool)
    out["pool_units_with_3plus_validation_plates"] = int(sum(1 for k, n in vu.items() if k in ou and n >= 3))
    out["plate_overlap_original_validation"] = len(set(original.BARCODE) & set(validation.BARCODE))
    return out


def norm_tag(tag):
    tag = re.sub(r"^A\d+", "Ak", tag)
    tag = re.sub(r"^L\d+", "Lk", tag)
    tag = re.sub(r"-D\d+", "-Dd", tag)
    return re.sub(r"^PC\d+", "PCk", tag)


def jaaks_raw_census():
    plates = defaultdict(lambda: defaultdict(list))
    plate_meta = {}
    with zipfile.ZipFile(JAAKS_RAW) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = next(reader)
            ix = {name: i for i, name in enumerate(header)}
            for row in reader:
                barcode = row[ix["BARCODE"]]
                plates[barcode][row[ix["POSITION"]]].append(row[ix["TAG"]])
                plate_meta.setdefault(barcode, (row[ix["MASTER_CELL_ID"]], row[ix["DRUGSET_ID"]], row[ix["RESEARCH_PROJECT"]]))
    nc, lib_reps, anchor_reps, patterns = [], [], [], Counter()
    for barcode, wells in plates.items():
        counts = Counter()
        lib_single = Counter()
        anchor_single = Counter()
        for tags in wells.values():
            pattern = tuple(sorted(norm_tag(t) for t in tags))
            patterns[pattern] += 1
            counts[pattern] += 1
            for t in tags:
                if re.match(r"^L\d+-D\d+-S$", t):
                    lib_single[t] += 1
                if re.match(r"^A\d+-S$", t):
                    anchor_single[t] += 1
        nc.append(counts[("NC-1",)])
        lib_reps.extend(lib_single.values())
        anchor_reps.extend(anchor_single.values())
    min_lib = min(lib_reps) if lib_reps else 0
    typical_lib = Counter(lib_reps).most_common(1)[0][0] if lib_reps else 0
    return {"member": "Original_screen_All_tissues_raw_data.csv", "plates": len(plates),
            "projects": dict(Counter(m[2] for m in plate_meta.values())),
            "well_patterns": {"|".join(p): c for p, c in patterns.most_common(15)},
            "nc1_wells_per_plate": distribution(nc),
            "library_single_replicates_per_dose": distribution(lib_reps),
            "anchor_single_replicates": distribution(anchor_reps),
            "design_based_cap_nats_per_plate_read_typical": math.log(typical_lib + 1),
            "design_based_cap_note": ("A within-plate rank bet of one combination well against r replicate single-agent "
                                      "wells can multiply wealth by at most r+1. Validation-screen raw wells are not on disk, "
                                      "so design-based reads exist only for original-screen plates."),
            "min_library_single_replicates": min_lib,
            "response_fields_converted": []}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parts = sys.argv[1:] or ["az", "jaaks_fitted", "jaaks_raw"]
    target = OUT / "CENSUS.json"
    census = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    census["code_sha256"] = sha(Path(__file__))
    if "az" in parts:
        census["az_gdsc007_exposed"] = az_census()
    if "jaaks_fitted" in parts:
        census["jaaks_fitted"] = jaaks_fitted_census()
    if "jaaks_raw" in parts:
        census["jaaks_raw_original"] = jaaks_raw_census()
    target.write_text(json.dumps(census, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in census.items() if k != "code_sha256"}, indent=1)[:6000])


if __name__ == "__main__":
    main()
