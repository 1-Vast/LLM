"""Project a pinned combination archive into design records, without target use."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/az_design"
FIELDS = "PROJECT_ID PROJECT_NAME BARCODE DRUGSET_ID CELL_LINE_NAME MASTER_CELL_ID COSMIC_ID CELL_ID TISSUE CANCER_TYPE POSITION lib1 lib1_dose lib1_drug_id lib1_conc lib2 lib2_dose lib2_drug_id lib2_conc treatment cmatrix".split()
KEY = "PROJECT_ID BARCODE cmatrix".split()
DOSE = "lib1_dose lib1_conc lib2_dose lib2_conc".split()
META = [f for f in FIELDS if f not in KEY + DOSE + ["POSITION"]]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def project(stream, progress=False):
    reader = csv.reader(stream)
    header = next(reader)
    index = {f: header.index(f) for f in FIELDS}
    bundles = {}
    for n, raw in enumerate(reader, 1):
        if len(raw) != len(header):
            raise ValueError(f"CSV width mismatch at row {n}; no row content disclosed")
        row = {f: raw[index[f]] for f in FIELDS}
        key = tuple(row[f] for f in KEY)
        if key not in bundles:
            bundles[key] = {"metadata": set(), "doses": Counter(), "positions": Counter(), "rows": 0}
        b = bundles[key]
        b["metadata"].add(tuple(row[f] for f in META))
        b["doses"][tuple(row[f] for f in DOSE)] += 1
        b["positions"][row["POSITION"]] += 1
        b["rows"] += 1
        if progress and n % 250000 == 0:
            print(json.dumps({"design_rows_scanned": n, "matrix_keys": len(bundles)}), flush=True)
    records = []
    for key, b in sorted(bundles.items()):
        records.append(dict(zip(KEY, key), rows=b["rows"],
                            metadata=[dict(zip(META, values)) for values in sorted(b["metadata"])],
                            dose_pairs=[dict(zip(DOSE, values), count=count) for values, count in sorted(b["doses"].items())],
                            positions=dict(sorted(b["positions"].items()))))
    return records


def summarize(records):
    cells = defaultdict(lambda: defaultdict(set))
    pairs = defaultdict(set)
    percell = defaultdict(set)
    stocks = set()
    treatments = Counter()
    drugs = set()
    rows = 0
    conflicts = []
    duplicate_positions = 0
    duplicate_doses = 0
    sizes = Counter()
    for r in records:
        rows += r["rows"]
        sizes[len(r["dose_pairs"])] += 1
        duplicate_positions += sum(v - 1 for v in r["positions"].values())
        duplicate_doses += sum(d["count"] - 1 for d in r["dose_pairs"])
        if len(r["metadata"]) != 1:
            conflicts.append({k: r[k] for k in ["member"] + KEY})
        for m in r["metadata"]:
            cell = m["MASTER_CELL_ID"]
            pair = tuple(sorted([m["lib1_drug_id"], m["lib2_drug_id"]]))
            drugs.update(pair)
            pairs[pair].add(cell)
            percell[cell].add(pair)
            stocks.add((cell, m["CELL_ID"]))
            for field in ["CELL_LINE_NAME", "COSMIC_ID", "TISSUE", "CANCER_TYPE", "CELL_ID"]:
                cells[cell][field].add(m[field])
            treatments[m["treatment"]] += 1
    order = sorted(pairs, key=lambda pair: (-len(pairs[pair]), pair))
    top = order[:64]
    intersection = sorted(set.intersection(*(pairs[p] for p in top))) if len(top) == 64 else []
    cancer = defaultdict(set)
    for cell, meta in cells.items():
        for label in meta["CANCER_TYPE"]:
            cancer[label].add(cell)
    return {
        "released_rows": rows, "matrix_keys": len(records), "source_cell_models": len(cells),
        "source_drug_ids": len(drugs), "source_unordered_pairs": len(pairs),
        "pair_cell_model_units": sum(map(len, pairs.values())), "cell_model_stock_units": len(stocks),
        "treatments_per_metadata_variant": dict(treatments),
        "matrix_identity_conflicts": conflicts, "duplicate_positions_within_matrix": duplicate_positions,
        "duplicate_dose_pairs_within_matrix": duplicate_doses, "dose_surface_size_counts": dict(sorted(sizes.items())),
        "drug_ids": sorted(drugs),
        "pair_coverage": [{"pair": list(p), "n_cell_models": len(pairs[p])} for p in order],
        "cell_coverage": [{"cell_model": c, "n_pairs": len(percell[c])} for c in sorted(percell)],
        "cell_metadata": {c: {k: sorted(v) for k, v in meta.items()} for c, meta in sorted(cells.items())},
        "cancer_type_cell_counts": {k: len(v) for k, v in sorted(cancer.items())},
        "descriptive_top64_pairs": [list(p) for p in top],
        "descriptive_top64_common_cell_models": intersection,
        "top64_is_not_a_frozen_experiment": True,
    }


def main():
    then = time.monotonic()
    output = OUT / "DESIGN_MATRICES.jsonl"
    if output.exists():
        raise RuntimeError("Existing census output; do not silently overwrite")
    headers = json.loads((OUT / "HEADERS.json").read_text(encoding="utf-8"))
    archive = OUT / "matrix_well_stats_GDSC_007_010_plus_Spiper1.zip"
    assert sha(archive) == headers["archive_sha256"]
    binding = {"utc": datetime.now(timezone.utc).isoformat(), "code_sha256": sha(Path(__file__)),
               "protocol_sha256": sha(OUT.parent / "AZ_METADATA_PROJECTION.md"),
               "archive_sha256": headers["archive_sha256"], "allowed_fields": FIELDS,
               "target_numeric_use": False, "source_response_byte_contact": True}
    (OUT / "CENSUS_STARTED.json").write_text(json.dumps(binding, indent=2), encoding="utf-8")
    all_records = []
    by_member = {}
    with zipfile.ZipFile(archive) as source, output.open("w", encoding="utf-8", newline="\n") as sink:
        for entry in headers["members"]:
            if "header" not in entry:
                continue
            with source.open(entry["name"]) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                records = project(stream, progress=True)
            for r in records:
                r["member"] = entry["name"]
                sink.write(json.dumps(r, separators=(",", ":")) + "\n")
            by_member[entry["name"]] = summarize(records)
            all_records.extend(records)
            print(json.dumps({"member_complete": entry["name"], "matrices": len(records)}), flush=True)
    result = dict(binding, elapsed_seconds=time.monotonic()-then,
                  design_projection_sha256=sha(output), overall=summarize(all_records), by_member=by_member)
    (OUT / "CENSUS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result["overall"][k] for k in ["released_rows", "matrix_keys", "source_cell_models", "source_drug_ids", "source_unordered_pairs", "pair_cell_model_units"]}), flush=True)
    print(json.dumps({"matrix_identity_conflicts": len(result["overall"]["matrix_identity_conflicts"])}), flush=True)


if __name__ == "__main__":
    main()
