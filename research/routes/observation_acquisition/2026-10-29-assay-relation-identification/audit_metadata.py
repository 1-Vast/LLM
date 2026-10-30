"""Frozen derivative-only metadata support check; no response input."""
from collections import defaultdict
from decimal import Decimal
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "2026-10-29-edit-support-audit/primary_metadata.json"
started = time.monotonic()
raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "d426f1c3fcbe23034235754d8cd418934a2eac150f82d0ffb7cea9e653559611"
rows = json.loads(raw)
support = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
cell_projects = defaultdict(set)
keys = set()
for row in rows:
    assert set(row) == {"project", "cell", "drug_id", "ref", "doses_uM"}
    p, c, d = row["project"], row["cell"], row["drug_id"]
    assert row["ref"] and (p, c, d) not in keys
    keys.add((p, c, d))
    cell_projects[c].add(p)
    for text in row["doses_uM"]:
        q = Decimal(text)
        assert q.is_finite() and q > 0
        support[p][d][q].add(c)

best = []
evaluated = 0
project_counts = {}
for p in sorted(support):
    drugs = support[p]
    project_counts[p] = {"distinct_master_cell_ids": len(set().union(*(s for doses in drugs.values() for s in doses.values()))),
                         "distinct_drug_ids": len(drugs)}
    for triple in combinations(sorted(drugs), 3):
        options = [sorted(drugs[d]) for d in triple]
        for doses in product(*options):
            evaluated += 1
            assert evaluated <= 2_000_000, "Incomplete enumeration: stop, no qualification verdict"
            cells = set.intersection(*(drugs[d][q] for d, q in zip(triple, doses)))
            item = (len(cells), p, triple, doses)
            best.append(item)
            best.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))
            del best[5:]
    assert time.monotonic() - started < 120, "CPU/wall scope exhausted"

result = {"input_sha256": hashlib.sha256(raw).hexdigest(), "input_records": len(rows),
          "source_level": "Previous primary metadata derivative; not independent original-archive recomputation",
          "protocol_sha256": hashlib.sha256((HERE / "metadata_protocol.md").read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "project_counts": project_counts, "distinct_master_cell_id_strings": len(cell_projects),
          "master_cell_ids_in_multiple_projects": sum(len(v) > 1 for v in cell_projects.values()),
          "complete_menu_combinations_evaluated": evaluated,
          "top5": [{"common_master_cell_ids": n, "project": p, "drug_ids": list(ds),
                    "doses_uM": [str(q) for q in qs]} for n, p, ds, qs in best],
          "H_DQ_R_minimum_200": bool(best and best[0][0] >= 200),
          "qualification": "metadata_support_present" if best and best[0][0] >= 200 else "metadata_support_below_fixed_gate",
          "response_values_accessed": False, "full_measurement_qualification": "unknown",
          "unknown": ["True biological-cell independence", "Source well and culture replicate identity", "Matched exposure and endpoint for selected keys", "Noise and conditional functional dependence", "Actual physical-well and batch costs", "Independent functional confirmation"],
          "wall_seconds": time.monotonic() - started}
with (HERE / "metadata_result.json").open("x", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(json.dumps({"records": len(rows), "menu_combinations": evaluated, "top": result["top5"][:1],
                  "qualification": result["qualification"], "seconds": result["wall_seconds"]}, ensure_ascii=False))
