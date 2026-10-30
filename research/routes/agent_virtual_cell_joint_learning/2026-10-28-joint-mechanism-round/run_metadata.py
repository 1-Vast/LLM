"""Q001 deterministic arithmetic on the frozen parameter projection only."""
from pathlib import Path
from collections import Counter
from itertools import combinations
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parent
started = time.process_time()
data = json.loads((ROOT / "metadata_inputs.json").read_text(encoding="utf-8"))
for source in data["sources"]:
    assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"]
result = {"protocol": "Q001 v1", "input_sha256": hashlib.sha256((ROOT / "metadata_inputs.json").read_bytes()).hexdigest(),
          "functional_response_consumed": False, "tables": {}, "literal_script_violations": []}
for group, table in data["tables"].items():
    rows = table["rows"]
    entry = {"row_count": len(rows), "gen_counts": dict(Counter(r["gen"] for r in rows)),
             "sum_t0_t1_unique": sorted({r["t0"] + r["t1"] for r in rows}),
             "by_gen": {}, "metadata_duplicate_count": len(rows) - len({tuple(r[c] for c in table["read_columns"]) for r in rows})}
    for gen in sorted({r["gen"] for r in rows}):
        subset = [r for r in rows if r["gen"] == gen]
        entry["by_gen"][gen] = {c: [min(r[c] for r in subset), max(r[c] for r in subset)] for c in ["t0", "t1"]}
    def pair(a, b):
        return {"gen_i": a["gen"], "gen_j": b["gen"], "line_i": a["line"], "line_j": b["line"],
                "number_i": a["number"], "number_j": b["number"],
                "raw_i": [a["seq"], a["t0"], a["t1"]], "raw_j": [b["seq"], b["t0"], b["t1"]]}
    if group == "OLA-IBET":
        swapped = [pair(a,b) for a,b in combinations(rows,2)
                   if a["seq"] != b["seq"] and a["t0"] == b["t1"] and a["t1"] == b["t0"]]
        entry["raw_swapped_pairs_same_gen"] = [p for p in swapped if p["gen_i"] == p["gen_j"]]
        entry["raw_swapped_pairs_cross_gen"] = [p for p in swapped if p["gen_i"] != p["gen_j"]]
    else:
        entry["different_seq_same_raw_coordinates_same_gen"] = [pair(a,b) for a,b in combinations(rows,2)
            if a["gen"] == b["gen"] and a["seq"] != b["seq"] and (a["t0"],a["t1"]) == (b["t0"],b["t1"])]
    result["tables"][group] = entry

# These literal conditions reproduce the displayed metadata contract, not an hours conversion.
stages = [("FAC", "GS0-GS1", [0,1], 10, 11), ("FAC", "GS2", [2], 10, 11),
          ("FAC", "GS3", [3], 22, 23), ("OLA-IBET", "GS0", [0], 11, None),
          ("OLA-IBET", "GS1-GS2", [1,2], 47, None)]
for group,stage,gens,high,sum_bound in stages:
    rows = [r for r in data["tables"][group]["rows"] if r["gen"] in gens]
    violated = []
    for row in rows:
        good = 1 <= row["t0"] <= high
        if group == "FAC":
            good = good and 1 <= row["t1"] <= high and row["t0"] + row["t1"] <= sum_bound
        elif stage != "GS0":
            good = good and 12 <= row["t0"] <= 36
        if not good:
            violated.append(row["line"])
    result["literal_script_violations"].append({"group": group, "stage": stage, "rows_in_scope": len(rows),
        "violating_lines": violated, "interpretation": "raw-coordinate literal check only; version/scale unresolved"})
result["qualification"] = {"time_to_hours": "unresolved", "actual_exposure_reversal_pairs": None,
    "primary_verdict": "unresolved: no certified per-generation mapping in inspected main text and maintenance snapshot",
    "drugs_cross_background": [], "biological_replicate_ids_in_tables": False,
    "scope": "source-defined therapy-order opportunities only; no memory, transfer, or algorithm benefit established"}
result["cpu_seconds"] = round(time.process_time() - started, 4)
assert result["cpu_seconds"] <= 60
(ROOT / "metadata_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"primary_verdict": result["qualification"]["primary_verdict"],
    "PDO_same_gen_raw_swap_pairs": len(result["tables"]["OLA-IBET"]["raw_swapped_pairs_same_gen"]),
    "PDO_cross_gen_raw_swap_pairs": len(result["tables"]["OLA-IBET"]["raw_swapped_pairs_cross_gen"]),
    "FAC_same_raw_different_seq_pairs": len(result["tables"]["FAC"]["different_seq_same_raw_coordinates_same_gen"]),
    "literal_violations": [{k:v for k,v in x.items() if k != "interpretation"} for x in result["literal_script_violations"]]}, ensure_ascii=False))
