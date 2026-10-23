"""Independent identity-only projection. Never read growth-rate column values."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import pyarrow.parquet as pq

BASE = Path('log/20261023/dose_update_qualification')
path = BASE / 'summary_statistics.parquet'
meta = pq.ParquetFile(path)
rows = pq.read_table(path, columns=['cell_line', 'condition']).to_pylist()
pairs = Counter((row['cell_line'], row['condition']) for row in rows)
conditions = sorted({row['condition'] for row in rows})
singles, multis, controls, unparsed = {}, [], [], []
for condition in conditions:
    try:
        parsed = ast.literal_eval(condition)
    except (ValueError, SyntaxError):
        unparsed.append(condition)
        continue
    if not isinstance(parsed, list) or not parsed:
        unparsed.append(condition)
    elif any(str(item[0]).startswith('DMSO') for item in parsed):
        controls.append(condition)
    elif len(parsed) == 1:
        singles[condition] = parsed[0]
    else:
        multis.append(condition)
result = {
    'scope': 'Only cell_line and condition decoded; phenotype column never projected',
    'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'schema_names': meta.schema.names,
    'metadata_rows': meta.metadata.num_rows,
    'decoded_identity_rows': len(rows),
    'contexts': len({row['cell_line'] for row in rows}),
    'conditions': len(conditions),
    'unique_pairs': len(pairs),
    'pair_multiplicity_histogram': dict(sorted(Counter(pairs.values()).items())),
    'single_non_DMSO_conditions': len(singles),
    'single_non_DMSO_drugs': sorted({str(value[0]) for value in singles.values()}),
    'single_non_DMSO_drug_count': len({str(value[0]) for value in singles.values()}),
    'single_non_DMSO_units': sorted({str(value[2]) for value in singles.values()}),
    'multi_conditions': len(multis),
    'control_conditions': controls,
    'unparsed_conditions': unparsed,
    'interpretation': 'Duplicate pairs do not certify biological replicates. No sample/run identity or internal-public value equality inferred.'
}
(BASE/'rhaister'/'IDENTITY_CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
