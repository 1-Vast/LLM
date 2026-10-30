"""Coordinator acceptance checks using only DS005 metadata inputs and A/C tables."""
import csv
import hashlib
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path("D:/MAESTRO")
TASK = ROOT / "research/deepseek/tasks/DS005"
task = json.loads((TASK / "task.json").read_text(encoding="utf-8-sig"))
result = json.loads((TASK / "result.json").read_text(encoding="utf-8-sig"))
inputs = []
for item in task["inputs"]:
    path = Path(item["path"])
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    inputs.append({"path": item["path"], "bytes": path.stat().st_size,
                   "sha256": sha, "matches_task": sha == item["sha256"]})
assert all(r["matches_task"] for r in inputs)
paths = {Path(i["path"]).name: Path(i["path"]) for i in task["inputs"]}
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
with zipfile.ZipFile(paths["q1_elife_supp1.docx"]) as archive:
    document = ET.fromstring(archive.read("word/document.xml"))
tables = document.findall(".//w:tbl", ns)


def table_rows(table):
    return [["".join(t.text or "" for t in c.findall(".//w:t", ns)).strip()
             for c in row.findall("w:tc", ns)] for row in table.findall("w:tr", ns)]


# Only original table A and C are selected; no text extraction from the other tables.
a, c = table_rows(tables[0]), table_rows(tables[2])
assert a[0] == ["Drug name", "Target", "Downstream effector", "Dose 1 (nM)", "Dose 2 (nM)"]
assert c[0][0] == "Index" and c[0][5] == "Index"
copy_checks = []
for name, original in (("A", a), ("C", c)):
    with paths[f"q1_supp1_table_{name}_conditions.tsv"].open(encoding="utf-8-sig", newline="") as handle:
        derived = list(csv.reader(handle, delimiter="\t"))
    mismatch = [i for i in range(max(len(original), len(derived)))
                if i >= len(original) or i >= len(derived) or original[i] != derived[i]]
    copy_checks.append({"table": name, "docx_rows_including_header": len(original),
                        "tsv_rows_including_header": len(derived), "mismatching_rows": mismatch})
assert all(not r["mismatching_rows"] for r in copy_checks)
blocks = [row[offset:offset+5] for row in c[1:] for offset in (0, 5)]
indices = {int(b[0]) for b in blocks}
class_indices = {}
for index, first, dose, second, second_dose in blocks:
    for label in (first, second):
        if label.strip():
            class_indices.setdefault(label.strip(), set()).add(int(index))
class_checks = []
for readout in result["readouts"]:
    for implementation in readout["implementations"]:
        label = implementation["table_C_class_raw"]
        actual = sorted(class_indices.get(label, set()))
        saved = sorted(int(i) for i in implementation["table_C_indices"])
        class_checks.append({"drug": implementation["drug_raw_A"], "class": label,
                             "computed_index_count": len(actual), "matches_saved": actual == saved,
                             "pair_status": implementation["pair_status"]})
assert all(r["matches_saved"] for r in class_checks)
node_lines = [line.split() for line in paths["q1_pertbio_node_index.txt"].read_text().splitlines() if line.strip()]
exp_lines = [line.split() for line in paths["q1_pertbio_exp_index.txt"].read_text().splitlines() if line.strip()]
out = {"task_id": "DS005", "reviewed_task_version": task["task_version"],
       "reviewed_utc": datetime.now(timezone.utc).isoformat(),
       "reviewer": "main coordinator; not an independent biological replication",
       "verdict": "accepted_for_metadata_with_qualifications",
       "scientific_mapping_closed": False, "inputs": inputs,
       "reviewed_artifacts": {name: hashlib.sha256((TASK / name).read_bytes()).hexdigest()
                              for name in ("task.json", "report.md", "result.json")},
       "copy_checks": copy_checks, "table_c": {"condition_blocks": len(blocks),
           "unique_indices": len(indices), "missing_1_to_89": sorted(set(range(1, 90)) - indices)},
       "class_index_checks": class_checks,
       "exp_index": {"rows": len(exp_lines), "unique_labels": len({r[0] for r in exp_lines})},
       "node_index": {"rows": len(node_lines), "role_column_counts": dict(Counter(r[2] for r in node_lines))},
       "qualifications": [
           "MAPK1pT202->MAPKpT202 is a source-context alias hypothesis, not certified same antibody/isoform measurement.",
           "All eight full action/probe/dose mappings remain unresolved; no inferred unit conversion or missing-index imputation.",
           "DOCX out-of-scope B/D/E/F text exposure is retained; no team-unseen confirmation claim based on these sources.",
           "Three biological replicates stated in the RPPA method do not provide exported raw per-condition replicate errors.",
           "Acceptance does not validate P1v2 coordinate identity, biological mechanism, independent decision benefit or transfer."],
       "response_values_parsed_or_exported": 0, "network_requests": 0,
       "scientific_fit_or_experiment": False}
with (TASK / "main_review.json").open("x", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
print(json.dumps({"verdict": out["verdict"], "input_hashes_passed": len(inputs),
                  "copy_mismatches": [r["mismatching_rows"] for r in copy_checks],
                  "class_index_checks_passed": sum(r["matches_saved"] for r in class_checks),
                  "table_c": out["table_c"], "scientific_mapping_closed": False}, ensure_ascii=False))
