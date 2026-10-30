"""Inspect identities and design only; never read the response column."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

episode = Path(__file__).resolve().parent.parent
source = episode / 'sources/root15_emerald_summary_cdn.body'
expected = '3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9'
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
parquet = pq.ParquetFile(source)
names = parquet.schema.names
assert 'cell_line' in names and 'condition' in names
rows = parquet.read(columns=['cell_line', 'condition']).to_pylist()
pairs = Counter((r['cell_line'], r['condition']) for r in rows)
conditions = sorted({r['condition'] for r in rows})
parsed = {}
unparsed = []
for condition in conditions:
    try:
        value = ast.literal_eval(condition)
        if not isinstance(value, list) or not all(isinstance(x, tuple) and len(x) == 3 for x in value):
            raise ValueError('Not a list of treatment tuples')
        parsed[condition] = value
    except (ValueError, SyntaxError):
        unparsed.append(condition)
singles = {c: v for c, v in parsed.items() if len(v) == 1}
combinations = {c: v for c, v in parsed.items() if len(v) > 1}
drugs = sorted({v[0][0] for v in singles.values()})
units = sorted({str(x[2]) for v in parsed.values() for x in v})
controls = {c: v for c, v in singles.items() if v[0][0] in ['DMSO_T0', 'DMSO_TF']}
noncontrol_singles = {c: v for c, v in singles.items() if c not in controls}
per_line = Counter(r['cell_line'] for r in rows)
per_condition = Counter(r['condition'] for r in rows)
result = {
    'source': str(source), 'sha256': expected,
    'physical_response_file_acquired': True,
    'semantic_columns_read': ['cell_line', 'condition'],
    'response_column_read': False, 'response_values_accessed': 0,
    'response_statistics_accessed': False,
    'rows': parquet.metadata.num_rows, 'row_groups': parquet.metadata.num_row_groups,
    'schema_names': names, 'unique_cell_lines': len(per_line),
    'unique_conditions': len(conditions), 'unique_cell_condition_keys': len(pairs),
    'key_multiplicity_histogram': dict(sorted(Counter(pairs.values()).items())),
    'rows_per_line_histogram': dict(sorted(Counter(per_line.values()).items())),
    'rows_per_condition_histogram': dict(sorted(Counter(per_condition.values()).items())),
    'single_tuple_conditions': len(singles), 'multi_tuple_conditions': len(combinations),
    'single_tuple_drug_names': drugs, 'literal_concentration_units': units,
    'control_conditions': {v[0][0]: {'condition': c, 'rows': per_condition[c], 'key_multiplicity': sorted({n for (line, condition), n in pairs.items() if condition == c})} for c, v in controls.items()},
    'noncontrol_single_drug_conditions': len(noncontrol_singles),
    'noncontrol_single_drug_names': sorted({v[0][0] for v in noncontrol_singles.values()}),
    'single_conditions_after_dropping_time_zero': sum(v[0][0] != 'DMSO_T0' for v in singles.values()),
    'unparsed_conditions': unparsed,
    'independent_preparation_keys_in_schema': [n for n in names if n in ['sample', 'plate', 'batch', 'replicate', 'preparation']],
    'qualification': 'Repeated identity keys are row multiplicity only; independent biological preparation and source-control pairing remain unqualified.'
}
(episode / 'data/summary_metadata.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
