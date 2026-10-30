"""Pre-outcome support selection. Never retains or numerically parses response fields."""
from collections import defaultdict, Counter
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import io
import itertools
import json
import time
import zipfile

HERE = Path(__file__).resolve().parent
ZIP = HERE.parents[1] / "tmp/extq1/gsdc_well_stats.zip"
EXPECTED = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"


def select_support():
    digest = hashlib.sha256()
    with ZIP.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    assert digest.hexdigest() == EXPECTED
    curves = defaultdict(set)
    mapping = defaultdict(set)
    fields = ["PROJECT_ID", "MASTER_CELL_ID"] + [f"lib{s}_{n}" for s in (1, 2) for n in ("drug_id", "drug", "conc")]
    with zipfile.ZipFile(ZIP) as archive, archive.open(MEMBER) as raw:
        rows = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        header = next(rows)
        indices = {name: header.index(name) for name in fields}
        count = 0
        for values in itertools.islice(rows, 20000):
            row = {name: values[index] for name, index in indices.items()}
            del values
            count += 1
            for side in (1, 2):
                project, cell = row["PROJECT_ID"], row["MASTER_CELL_ID"]
                drug, ref = row[f"lib{side}_drug_id"], row[f"lib{side}_drug"]
                concentration = Decimal(row[f"lib{side}_conc"])
                assert concentration.is_finite() and concentration > 0
                curves[(project, cell, drug, ref)].add(concentration)
                mapping[(project, cell, drug)].add(ref)
    assert count == 20000
    # Exact Python Unicode string ordering of reference IDs; dose ordering is Decimal numeric.
    canonical = {key: min(refs) for key, refs in mapping.items()}
    cells = sorted({key[:2] for key in canonical})
    pairs = []
    for (project, source), (target_project, target) in itertools.product(cells, repeat=2):
        if project != target_project or source == target:
            continue
        drugs = sorted({k[2] for k in canonical if k[:2] == (project, source)} &
                       {k[2] for k in canonical if k[:2] == (project, target)})
        shared = []
        for drug in drugs:
            source_ref, target_ref = canonical[(project, source, drug)], canonical[(project, target, drug)]
            doses = sorted(curves[(project, source, drug, source_ref)] & curves[(project, target, drug, target_ref)])
            if len(doses) >= 3:
                shared.append({"drug": drug, "source_ref": source_ref, "target_ref": target_ref,
                               "concentrations_micromolar": [str(d) for d in doses]})
        if len(shared) >= 6:
            pairs.append({"project": project, "source_cell": source, "target_cell": target, "drugs": shared})
    return {"zip_sha256": digest.hexdigest(), "member": MEMBER, "prefix_rows": count,
            "selection": "Canonical minimum reference string per(project,cell,drug), exact shared physical positive doses >=3, at least6 shared drugs, all oriented distinct-cell pairs",
            "response_fields_parsed": [], "canonical_cell_drug_groups": len(canonical),
            "eligible_oriented_pairs": len(pairs), "leave_one_drug_out_tasks": sum(len(p["drugs"]) for p in pairs),
            "shared_drug_count_histogram": dict(Counter(len(p["drugs"]) for p in pairs)),
            "target_menu_size_histogram": dict(Counter(len(d["concentrations_micromolar"]) for p in pairs for d in p["drugs"])),
            "pairs": pairs}


if __name__ == "__main__":
    start = time.perf_counter()
    result = select_support()
    result["wall_seconds"] = time.perf_counter() - start
    (HERE / "support_frozen.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "pairs"}, ensure_ascii=False))
