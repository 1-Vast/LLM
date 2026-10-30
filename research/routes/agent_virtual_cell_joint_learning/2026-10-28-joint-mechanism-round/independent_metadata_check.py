"""Independent Q001 arithmetic; no responses or proposer implementation read."""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "metadata_inputs.json"
data = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
out = {
    "protocol": "Q001 frozen v1; independent implementation",
    "input_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "functional_response_consumed": False,
    "scientific_effect_validation": False,
    "tables": {},
    "scripts": [],
}

for group, table in data["tables"].items():
    assert hashlib.sha256(Path(table["source"]).read_bytes()).hexdigest() == table["sha256"]
    rows = table["rows"]
    assert all(set(r) == {"seq", "t0", "t1", "gen", "number", "line"} for r in rows)
    duplicates = collections.Counter(tuple(r[k] for k in ["seq", "t0", "t1", "gen", "number"]) for r in rows)
    summary = {"n": len(rows), "duplicate_excess": sum(n - 1 for n in duplicates.values()), "generations": {}}
    for gen in sorted({r["gen"] for r in rows}):
        part = [r for r in rows if r["gen"] == gen]
        summary["generations"][str(gen)] = {
            "n": len(part),
            "seq_counts": dict(collections.Counter(r["seq"] for r in part)),
            "t0_min_max": [min(r["t0"] for r in part), max(r["t0"] for r in part)],
            "t1_min_max": [min(r["t1"] for r in part), max(r["t1"] for r in part)],
            "sums": sorted({r["t0"] + r["t1"] for r in part}),
        }
    pairs = []
    for left, right in itertools.combinations(rows, 2):
        if left["seq"] == right["seq"]:
            continue
        if group == "OLA-IBET":
            matches = left["t0"] == right["t1"] and left["t1"] == right["t0"]
        else:
            matches = left["gen"] == right["gen"] and left["t0"] == right["t0"] and left["t1"] == right["t1"]
        if matches:
            pairs.append({"lines": [left["line"], right["line"]], "generations": [left["gen"], right["gen"]],
                          "seqs": [left["seq"], right["seq"]], "raw_times": [[left["t0"], left["t1"]], [right["t0"], right["t1"]]]})
    summary["same_generation_pairs"] = [p for p in pairs if p["generations"][0] == p["generations"][1]]
    summary["cross_generation_pairs"] = [p for p in pairs if p["generations"][0] != p["generations"][1]]
    summary["same_generation_count"] = len(summary["same_generation_pairs"])
    summary["cross_generation_count"] = len(summary["cross_generation_pairs"])
    out["tables"][group] = summary

stages = {("FAC", "GS0-GS1"): [0, 1], ("FAC", "GS2"): [2], ("FAC", "GS3"): [3],
          ("OLA-IBET", "GS0"): [0], ("OLA-IBET", "GS1-GS2"): [1, 2]}
for record in data["scripts"]:
    assert hashlib.sha256(Path(record["source"]).read_bytes()).hexdigest() == record["sha256"]
    group, stage = record["group"], record["stage"]
    rows = [r for r in data["tables"][group]["rows"] if r["gen"] in stages[group, stage]]
    ranges = {p["name"]: (p["low"], p["high"]) for p in record["parameters"] if "low" in p}
    bad_range = [r["line"] for r in rows if any(not lo <= r[name] <= hi for name, (lo, hi) in ranges.items())]
    result = {"group": group, "stage": stage, "n": len(rows), "ranges": ranges,
              "out_of_range_lines": bad_range, "out_of_range_count": len(bad_range)}
    if group == "FAC":
        threshold = int(re.search(r"thres=(\d+)", record["constraint_text"])[1])
        bad = [r["line"] for r in rows if r["t0"] + r["t1"] > threshold]
        result.update(sum_threshold=threshold, sum_violation_lines=bad, sum_violation_count=len(bad))
    else:
        text = "\n".join(x["text"] for x in record["time_lines"])
        total = int(re.search(r"=\s*(\d+)-df_samples", text)[1])
        bad = [r["line"] for r in rows if r["t1"] != total - r["t0"]]
        result.update(assignment_total=total, assignment_violation_lines=bad, assignment_violation_count=len(bad))
        if stage == "GS1-GS2":
            threshold = int(re.search(r"thres=(\d+)", record["constraint_text"])[1])
            bad = [r["line"] for r in rows if not threshold <= r["t0"] <= 48 - threshold]
            result.update(chrono_interval=[threshold, 48 - threshold], chrono_violation_lines=bad, chrono_violation_count=len(bad))
    out["scripts"].append(result)

# Positive-system counterexample, constructed independently of any shared code.
def mv(matrix, vector):
    return [sum(x * y for x, y in zip(row, vector)) for row in matrix]

a = [[0, 1, 0], [1, 0, 0], [0, 0, 1]]
b = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]
d = [[1, 0, 0], [0, 0, 0], [0, 0, 1]]
states = {"e1": [1, 0, 0], "e3": [0, 0, 1]}
checks = []
for label, x in states.items():
    ab, ba = mv(b, mv(a, x)), mv(a, mv(b, x))
    delta = [u - v for u, v in zip(ab, ba)]
    checks.append({"state": label, "ab": ab, "ba": ba, "kappa": sum(delta),
                   "abd": mv(d, ab), "bad": mv(d, ba), "kappa_after_d": sum(mv(d, delta))})
assert [r["kappa"] for r in checks] == [0, 0]
assert [r["kappa_after_d"] for r in checks] == [1, -1]
out["counterexample"] = {"Ta": a, "Tb": b, "Td": d, "c": [1, 1, 1], "cases": checks,
    "interpretation": "Synthetic positive linear populations and selective survival only; no biological effect measured."}
out["qualification"] = {
    "raw_pairs_are_only_candidates": True,
    "actual_exposure_matched_pair_count": None,
    "status": "unresolved",
    "reason": "No independently certified per-generation raw-to-hours map, full sequence dictionary, or culture-level replicate IDs in these inputs."
}
target = ROOT / "independent_metadata_check.json"
target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"tables": {k: {n: v[n] for n in ["n", "same_generation_count", "cross_generation_count"]} for k, v in out["tables"].items()},
                  "scripts": out["scripts"], "counterexample": checks, "output": str(target)}, ensure_ascii=False, indent=2))
