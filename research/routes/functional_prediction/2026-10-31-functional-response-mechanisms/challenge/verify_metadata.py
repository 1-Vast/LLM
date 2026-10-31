"""Independent metadata-only verification; never deserialize response values."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

episode = Path(__file__).resolve().parent.parent
freeze = json.loads((episode / "operator_question_freeze.json").read_text())
hashes = {
    name: hashlib.sha256((episode / name).read_bytes()).hexdigest() == expected
    for name, expected in freeze["files"].items()
}
source = episode.parent / "2026-10-30-drug-discovery-capability/sources/root15_emerald_summary_cdn.body"
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == "3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9"
parquet = pq.ParquetFile(source)
assert parquet.schema.names == ["cell_line", "condition", "growth_rate"]
rows = parquet.read(columns=["cell_line", "condition"]).to_pylist()
conditions = {r["condition"] for r in rows}
parsed = {c: tuple(sorted(ast.literal_eval(c))) for c in conditions}
singles = {p[0] for p in parsed.values() if len(p) == 1}
combinations = [p for p in parsed.values() if len(p) > 1]
key_counts = Counter((r["cell_line"], r["condition"]) for r in rows)
result = {
    "freeze_hash_matches": hashes,
    "source_sha256": source_hash,
    "semantic_columns_read": ["cell_line", "condition"],
    "response_values_accessed": 0,
    "rows": len(rows),
    "cell_lines": len({r["cell_line"] for r in rows}),
    "condition_labels": len(conditions),
    "canonical_unordered_conditions": len(set(parsed.values())),
    "unique_cell_condition_keys": len(key_counts),
    "key_multiplicity_histogram": dict(sorted(Counter(key_counts.values()).items())),
    "combination_condition_orders": dict(sorted(Counter(map(len, combinations)).items())),
    "combination_families": len({tuple(t[0] for t in p) for p in combinations}),
    "exact_single_matched_orders": dict(sorted(Counter(
        len(p) for p in combinations if all(t in singles for t in p)
    ).items())),
    "schema_exposes_schedule_or_preparation": False,
    "boundary": "No schedule is authenticated by tuple order or missing fields; row counts do not certify independent preparations.",
}
assert all(hashes.values())
(episode / "challenge/metadata_verification.json").write_text(
    json.dumps(result, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, indent=2))
