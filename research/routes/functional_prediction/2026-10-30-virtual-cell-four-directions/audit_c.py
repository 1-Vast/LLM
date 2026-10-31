"""Acquire original C metadata/data and census identities without decoding counts."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
SOURCES = PROJECT / "data/external/virtual_cell_four_directions_20261030/longitudinal"


def main():
    record = json.loads((SOURCES / "zenodo_record.json").read_text(encoding="utf-8"))
    files = []
    for item in sorted(record["files"], key=lambda x: x["key"]):
        name = item["key"]
        path = SOURCES / name
        reused = False
        if name == "HTS001.csv":
            path = ROOT.parent / "2026-10-29-functional-joint-discovery/sources/root/hts001_raw.body"
            reused = True
        if not path.exists():
            request = urllib.request.Request(item["links"]["self"], headers={"User-Agent": "MAESTRO-research/0.1"})
            started = time.monotonic()
            with urllib.request.urlopen(request, timeout=25) as response, path.open("xb") as stream:
                while chunk := response.read(512 * 1024):
                    stream.write(chunk)
                    if stream.tell() > item["size"] or time.monotonic() - started > 90:
                        raise RuntimeError("Source download exceeded declared size/time")
        raw = path.read_bytes()
        assert len(raw) == item["size"], name
        assert "md5:" + hashlib.md5(raw).hexdigest() == item["checksum"], name
        info = {"name": name, "path": str(path), "bytes": len(raw), "md5": hashlib.md5(raw).hexdigest(),
                "sha256": hashlib.sha256(raw).hexdigest(), "reused_local_source": reused,
                "url": item["links"]["self"], "count_values_decoded": 0}
        del raw
        rows = 0
        trajectories = {}
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            allowed = [x for x in header if x != "cell.count"]
            index = {x: header.index(x) for x in allowed}
            for row in reader:
                rows += 1
                meta = {x: row[i] for x, i in index.items()}
                key = tuple(meta[x] for x in ["cell.line", "upid", "well", "drug1", "drug1.conc"])
                trajectories.setdefault(key, []).append(float(meta["time"]))
        cells = {}
        for (cell, plate, well, drug, dose), grid in trajectories.items():
            entry = cells.setdefault(cell, {"plates": set(), "drugs": set(), "wells": 0, "control_wells": 0, "time_grids": set(), "doses": {}})
            entry["plates"].add(plate)
            entry["drugs"].add(drug)
            entry["wells"] += 1
            entry["control_wells"] += drug == "control"
            entry["time_grids"].add(tuple(sorted(grid)))
            entry["doses"].setdefault(drug, collections.Counter())[dose] += 1
        for entry in cells.values():
            entry["plates"] = sorted(entry["plates"])
            entry["drugs"] = sorted(entry["drugs"])
            entry["time_grids"] = [list(g) for g in sorted(entry["time_grids"])]
        info.update({"columns": header, "rows": rows, "trajectories": len(trajectories), "cells": cells})
        files.append(info)
        print(json.dumps({k: info[k] for k in ["name", "bytes", "sha256", "columns", "rows", "trajectories"]}))
        print(json.dumps({c: {"plates": v["plates"], "drugs": len(v["drugs"]), "wells": v["wells"], "controls": v["control_wells"], "time_range": [min(v["time_grids"][0]), max(v["time_grids"][0])], "n_time_grids": len(v["time_grids"])} for c,v in cells.items()}))
    result = {"files": files, "unique_sha256": len({f["sha256"] for f in files}), "interpretation": "File identity and metadata only; no experimental independence certified."}
    (ROOT / "audit_c_metadata.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
