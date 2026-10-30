"""Check condition labels only; never open the response or activity matrix."""

import hashlib
import json
from collections import Counter
from pathlib import Path

here = Path(__file__).resolve().parent
source = here.parent / "2026-10-28-agent-a-matched-signal-function" / "sources"
names = [
    "q1_condition_manifest_from_S1C.json",
    "q1_supp1_table_A_conditions.tsv",
    "q1_pertbio_exp_index.txt",
    "q1_pertbio_node_index.txt",
]
inputs = {name: (source / name).read_bytes() for name in names}
rows = json.loads(inputs[names[0]].decode("utf-8-sig"))
indices = Counter(row["source_index"] for row in rows)
paired = [row for row in rows if row["perturbation2"]]
drugs = sorted({row[key] for row in rows for key in ("perturbation1", "perturbation2")} - {""})
exp_labels = [line.split()[0] for line in inputs[names[2]].decode("utf-8-sig").splitlines() if line.strip()]
protein_labels = {
    fields[0]
    for line in inputs[names[3]].decode("utf-8-sig").splitlines()
    if (fields := line.split()) and fields[-1] == "1"
}
groups = []
for a, b, readout in [
    ("AKTi", "PI3Ki", "AKTpS473"),
    ("MEKi", "BRAFi", "MAPK1pT202"),
    ("mTORi", "PKCi", "S6pS240"),
    ("JAKi", "SRCi", "GSK3pS21"),
]:
    contexts = []
    for partner in sorted(set(drugs) - {a, b}):
        left = [row for row in paired if {row["perturbation1"], row["perturbation2"]} == {a, partner}]
        right = [row for row in paired if {row["perturbation1"], row["perturbation2"]} == {b, partner}]
        if left and right:
            contexts.append({"partner": partner, "left_conditions": left, "right_conditions": right})
    groups.append({
        "implementations": [a, b],
        "source_calibration_readout": readout,
        "readout_exactly_in_protein_index": readout in protein_labels,
        "common_partner_count": len(contexts),
        "contexts": contexts,
    })
result = {
    "scope": "metadata only; condition opportunities, not effect or independent samples",
    "inputs_sha256": {name: hashlib.sha256(value).hexdigest() for name, value in inputs.items()},
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "source_condition_rows": len(rows),
    "missing_source_indices_1_to_89": sorted(set(range(1, 90)) - set(indices)),
    "duplicate_source_indices": {str(key): value for key, value in indices.items() if value > 1},
    "author_index_condition_count": len(exp_labels),
    "author_index_single_labels": sum("," not in label for label in exp_labels),
    "author_index_pair_labels": sum("," in label for label in exp_labels),
    "groups": groups,
    "total_group_partner_opportunities": sum(group["common_partner_count"] for group in groups),
    "functional_matrix_opened": False,
    "scientific_training_runs": 0,
    "limits": [
        "S1C source labels are not yet mapped row by row to the author matrix index",
        "Dose text is retained verbatim; units and numeric punctuation are unresolved",
        "Shared calibration readout does not establish matched measured response",
        "Shared drugs and partners make opportunities dependent, not biological replicates",
    ],
}
(here / "static_substitution_metadata.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({
    "source_rows": len(rows),
    "missing_indices": result["missing_source_indices_1_to_89"],
    "common_partner_counts": [group["common_partner_count"] for group in groups],
    "total_opportunities": result["total_group_partner_opportunities"],
}, ensure_ascii=False))
