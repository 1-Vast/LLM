"""Check dose-exact endpoint reference covers using design projection only."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/az_design"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def covers(records, same_plate):
    grouped = defaultdict(list)
    for r in records:
        key = tuple(r[f] for f in ["member", "project", "cell", "stock"])
        if same_plate:
            key += (r["plate"],)
        grouped[key].append(r)
    witnesses = []
    for group in grouped.values():
        by_drug = defaultdict(list)
        for r in group:
            for drug in r["axes"]:
                by_drug[drug].append(r)
        for r in group:
            pair = tuple(sorted(r["axes"]))
            if len(pair) != 2:
                raise ValueError("Two distinct source drug IDs required")
            matches = []
            for drug in pair:
                compatible = [p["key"] for p in by_drug[drug]
                              if tuple(sorted(p["axes"])) != pair
                              and r["axes"][drug] <= p["axes"][drug]]
                matches.append(min(compatible) if compatible else None)
            witnesses.append({"target": r["key"], "member": r["member"], "cell": r["cell"],
                              "pair": pair, "reference_axis_A": matches[0], "reference_axis_B": matches[1],
                              "eligible_two_bundles": all(x is not None for x in matches)})
    return sorted(witnesses, key=lambda r: r["target"])


def summary(witnesses):
    by_member = defaultdict(lambda: {"all_matrices": 0, "eligible_matrices": 0})
    cells, pairs, pair_cells = set(), set(), set()
    missing = [0, 0]
    for r in witnesses:
        by_member[r["member"]]["all_matrices"] += 1
        for i, field in enumerate(["reference_axis_A", "reference_axis_B"]):
            missing[i] += r[field] is None
        if r["eligible_two_bundles"]:
            by_member[r["member"]]["eligible_matrices"] += 1
            cells.add(r["cell"])
            pairs.add(tuple(r["pair"]))
            pair_cells.add((r["cell"], tuple(r["pair"])))
    return {"all_matrices": len(witnesses), "eligible_matrices": sum(r["eligible_two_bundles"] for r in witnesses),
            "eligible_source_cell_models": len(cells), "eligible_source_pairs": len(pairs),
            "eligible_pair_cell_units": len(pair_cells), "missing_axis_A": missing[0], "missing_axis_B": missing[1],
            "by_member": dict(by_member)}


def main():
    then = time.monotonic()
    if (OUT / "EDGE_COVER.json").exists():
        raise RuntimeError("Do not overwrite a completed scan")
    projection = OUT / "DESIGN_MATRICES.jsonl"
    census = json.loads((OUT / "CENSUS.json").read_text(encoding="utf-8"))
    assert sha(projection) == census["design_projection_sha256"]
    records = []
    with projection.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if len(row["metadata"]) != 1:
                raise ValueError("Conflicting matrix metadata")
            m = row["metadata"][0]
            axes = {}
            for axis in [1, 2]:
                values = {Decimal(d[f"lib{axis}_conc"]) for d in row["dose_pairs"]}
                if not all(v.is_finite() and v >= 0 for v in values):
                    raise ValueError("Invalid design concentration")
                axes[m[f"lib{axis}_drug_id"]] = values
            records.append({"key": (row["member"], row["PROJECT_ID"], row["BARCODE"], row["cmatrix"]),
                            "member": row["member"], "project": row["PROJECT_ID"],
                            "cell": m["MASTER_CELL_ID"], "stock": m["CELL_ID"], "plate": row["BARCODE"], "axes": axes})
    results = {}
    for label, same_plate in [("same_plate", True), ("same_stock_across_plates", False)]:
        witnesses = covers(records, same_plate)
        path = OUT / ("EDGE_WITNESSES_" + label + ".jsonl")
        with path.open("w", encoding="utf-8", newline="\n") as sink:
            for r in witnesses:
                sink.write(json.dumps(r, separators=(",", ":")) + "\n")
        results[label] = dict(summary(witnesses), witnesses_sha256=sha(path))
    result = {"code_sha256": sha(Path(__file__)), "protocol_sha256": sha(OUT.parent / "AZ_EDGE_COVER_PROTOCOL.md"),
              "projection_sha256": sha(projection), "elapsed_seconds": time.monotonic()-then,
              "response_zip_read": False, "target_numeric_use": False, "scopes": results}
    (OUT / "EDGE_COVER.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
