"""Audit treatment identities and exact dose support; never read outcomes."""
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


episode = Path(__file__).resolve().parent.parent
source = episode.parent / '2026-10-30-drug-discovery-capability/sources/root15_emerald_summary_cdn.body'
expected = '3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9'
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
table = pq.ParquetFile(source)
assert table.schema.names == ['cell_line', 'condition', 'growth_rate']
rows = table.read(columns=['cell_line', 'condition']).to_pylist()
parsed = {}
for condition in sorted({r['condition'] for r in rows}):
    value = ast.literal_eval(condition)
    assert isinstance(value, list) and value
    assert all(isinstance(t, tuple) and len(t) == 3 for t in value)
    assert all(t[2] == 'uM' for t in value)
    parsed[condition] = tuple(sorted(value))
singles = {v[0] for v in parsed.values() if len(v) == 1}
combinations = {k: v for k, v in parsed.items() if len(v) > 1}
families = defaultdict(list)
for name, components in combinations.items():
    families[tuple(t[0] for t in components)].append({
        'condition': name,
        'all_exact_single_doses_present': all(t in singles for t in components),
        'missing_single_doses': [t for t in components if t not in singles],
    })
result = {
    'source_path': str(source), 'source_sha256': expected,
    'semantic_columns_read': ['cell_line', 'condition'],
    'outcome_column_read': False, 'outcome_values_accessed': 0,
    'cell_lines': len({r['cell_line'] for r in rows}),
    'conditions': len(parsed), 'combination_conditions': len(combinations),
    'combination_order_histogram': dict(Counter(map(len, combinations.values()))),
    'combination_families': len(families),
    'conditions_with_all_exact_single_doses': sum(all(t in singles for t in v) for v in combinations.values()),
    'matched_single_dose_conditions_by_order': dict(Counter(
        len(v) for v in combinations.values() if all(t in singles for t in v))),
    'families': [{'drug_names': k, 'conditions': v} for k, v in sorted(families.items())],
    'independent_preparation_fields': [],
    'sequence_or_order_fields': [],
    'claim_boundary': 'Treatment tuple order is not an administration schedule; combination conditions and cell-line rows are not independent culture replicates. Exact dose support does not establish synergy or dynamics.',
}
(episode / 'root/pooled_design.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'families'}, indent=2))
