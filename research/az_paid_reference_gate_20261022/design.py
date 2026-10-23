"""Metadata-only query/target partition and fixed cell-model roles."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "log/20261022/intervention_program_renewal/az_design"
OUT = ROOT / "log/20261022/az_paid_reference_gate"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def matrix_key(r):
    return (r["member"], r["PROJECT_ID"], r["BARCODE"], r["cmatrix"])


def keyed(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    if (OUT / "DESIGN.json").exists():
        raise RuntimeError("Existing design must not be overwritten")
    source = OLD / "DESIGN_MATRICES.jsonl"
    assert sha(source) == json.loads((OLD / "CENSUS.json").read_text())["design_projection_sha256"]
    records = []
    with source.open(encoding="utf-8") as stream:
        for line in stream:
            r = json.loads(line)
            if r["member"] != MEMBER:
                continue
            assert len(r["metadata"]) == 1
            m = r["metadata"][0]
            r["key"] = matrix_key(r)
            r["pair"] = tuple(sorted([m["lib1_drug_id"], m["lib2_drug_id"]]))
            r["axes"] = {m[f"lib{a}_drug_id"]: {Decimal(d[f"lib{a}_conc"]) for d in r["dose_pairs"]} for a in [1, 2]}
            records.append(r)
    pairs = sorted({r["pair"] for r in records}, key=lambda p: (keyed("AZ-paid-reference-pairs-v1|" + "|".join(p)), p))
    query_pairs = set(pairs[:(len(pairs)+1)//2])
    target_pairs = set(pairs) - query_pairs
    grouped = defaultdict(list)
    for r in records:
        m = r["metadata"][0]
        grouped[(r["PROJECT_ID"], m["MASTER_CELL_ID"], m["CELL_ID"], r["BARCODE"])].append(r)
    episodes = {}
    for group in grouped.values():
        queries = [r for r in group if r["pair"] in query_pairs]
        for r in group:
            if r["pair"] not in target_pairs:
                continue
            witnesses = []
            for drug in r["pair"]:
                matches = [q for q in queries if drug in q["axes"] and r["axes"][drug] <= q["axes"][drug]]
                witnesses.append(min(matches, key=matrix_key) if matches else None)
            if any(w is None for w in witnesses):
                continue
            m = r["metadata"][0]
            groupkey = (m["MASTER_CELL_ID"], r["pair"])
            episode = {"cell": m["MASTER_CELL_ID"], "cancer_type": m["CANCER_TYPE"], "pair": r["pair"],
                       "target": r["key"], "witnesses": [w["key"] for w in witnesses],
                       "stock": m["CELL_ID"], "rows": r["rows"]}
            if groupkey not in episodes or r["key"] < tuple(episodes[groupkey]["target"]):
                episodes[groupkey] = episode
    cells = sorted({e["cell"] for e in episodes.values()}, key=lambda c: (keyed("AZ-paid-reference-cells-v1|" + c), c))
    if len(cells) < 320 or len({e["pair"] for e in episodes.values()}) < 4:
        write(OUT / "DESIGN_ABORT.json", {"cells": len(cells), "pairs": len({e["pair"] for e in episodes.values()})})
        raise RuntimeError("Registered metadata-only design sufficiency failed")
    role_cells = {"train": cells[:160], "validation": cells[160:224], "test": cells[224:320], "reserve": cells[320:]}
    roles = {c: role for role, values in role_cells.items() for c in values}
    for e in episodes.values():
        e["role"] = roles[e["cell"]]
    episode_list = sorted(episodes.values(), key=lambda e: (e["cell"], e["pair"]))
    selected = {tuple(k) for e in episode_list if e["role"] != "reserve" for k in [e["target"]] + e["witnesses"]}
    clean = []
    for r in records:
        if r["key"] in selected:
            clean.append({k: v for k, v in r.items() if k != "axes"})
    write(OUT / "EPISODES.json", episode_list)
    write(OUT / "SELECTED_DESIGN.json", clean)
    result = {"code_sha256": sha(Path(__file__)), "source_projection_sha256": sha(source),
              "member": MEMBER, "query_pairs": sorted(query_pairs), "target_pairs": sorted(target_pairs),
              "role_cells": role_cells, "counts": {role: {"cells": len(values),
                  "episodes": sum(e["role"] == role for e in episode_list),
                  "target_rows": sum(e["rows"] for e in episode_list if e["role"] == role)} for role, values in role_cells.items()},
              "selected_matrix_keys": len(selected), "episode_file_sha256": sha(OUT / "EPISODES.json"),
              "selected_design_sha256": sha(OUT / "SELECTED_DESIGN.json"), "target_numeric_use": False,
              "note": "Disjoint query/target source-ID pairs; each target episode resets its two-paid-bundle history. Internal retrospective development."}
    write(OUT / "DESIGN.json", result)
    print(json.dumps({"counts": result["counts"], "query_pairs": len(query_pairs), "target_pairs": len(target_pairs), "selected_matrices": len(selected)}))


if __name__ == "__main__":
    main()
