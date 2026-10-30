"""Q002 metadata only; never access the response column."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time

import psutil

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "metadata_qualification.json"
if OUTPUT.exists():
    raise SystemExit("Existing metadata result; no automatic replay")
start, cpu = time.monotonic(), time.process_time()
source = ROOT.parent / "2026-10-29-functional-joint-discovery/sources/root/hts001_raw.body"
raw = source.read_bytes()
assert len(raw) == 3039472
assert hashlib.md5(raw).hexdigest() == "a5959a38166685707e840369ce34d74d"
assert hashlib.sha256(raw).hexdigest() == "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617"
del raw
fields = ["drug1", "drug1.conc", "drug1.units", "cell.line", "upid", "well", "time"]
traces, rows = {}, 0
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.reader(stream)
    header = next(reader)
    indices = {name: header.index(name) for name in fields}
    for number, row in enumerate(reader, start=2):
        rows += 1
        if row[indices["drug1"]] != "control":
            continue
        meta = {name: row[index] for name, index in indices.items()}
        assert Decimal(meta["drug1.conc"]) == 0
        key = (meta["cell.line"], meta["upid"], meta["well"])
        traces.setdefault(key, []).append({"source_row": number, "time": meta["time"]})
        if rows % 1000 == 0:
            assert time.monotonic() - start <= 60 and time.process_time() - cpu <= 30
            assert psutil.Process().memory_info().peak_wset <= 256 * 1024**2

cells = {}
for (cell, plate, well), points in sorted(traces.items()):
    points.sort(key=lambda item: Decimal(item["time"]))
    assert len({p["time"] for p in points}) == len(points)
    cell_info = cells.setdefault(cell, {"plates": [], "wells": [], "time_grids": [], "trajectories": []})
    if plate not in cell_info["plates"]:
        cell_info["plates"].append(plate)
    cell_info["wells"].append(well)
    grid = [p["time"] for p in points]
    if grid not in cell_info["time_grids"]:
        cell_info["time_grids"].append(grid)
    cell_info["trajectories"].append({"plate": plate, "well": well, "points": points})

result = {"scope": "metadata_roster_no_count_access", "source_sha256": "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617",
          "allowed_columns_accessed": fields, "source_rows": rows, "control_trajectories": len(traces),
          "cells": cells, "count_values_accessed": 0,
          "independent_culture_or_technical_nesting_certified": False,
          "cpu_seconds": time.process_time() - cpu, "wall_seconds": time.monotonic() - start,
          "peak_working_set_bytes": psutil.Process().memory_info().peak_wset,
          "protocol_sha256": hashlib.sha256((ROOT / "metadata_protocol.md").read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"controls": len(traces), "counts_accessed": 0,
                  "cells": {c: {"plates": v["plates"], "n_wells": len(v["wells"]),
                                "n_grids": len(v["time_grids"]),
                                "pre36": [x for x in v["time_grids"][0] if Decimal(x) < 36],
                                "pre72": [x for x in v["time_grids"][0] if Decimal(x) < 72]}
                            for c, v in cells.items()}}))
