"""Check released baseline token reuse; no new prediction or fit."""
import csv
import io
import json
from pathlib import Path

base = Path('log/20261023/public_recovery_task')
rows = list(csv.DictReader(io.StringIO((base / 'root/count_header_source.body').read_bytes().decode('utf-8-sig'))))
result = {}
for sample in ('Vector Control', 'V600E'):
    lookup = {(r['schedule'], r['replicate']): r['0'] for r in rows if r['sample'] == sample}
    result[sample] = dict(all_six_day0_tokens_identical_by_replicate=all(
        lookup['Continuous', str(i)] == lookup['Intermittent', str(i)]
        for i in range(1, 7)), interpretation='shared released baseline entries; physical assay provenance not identified')
(base / 'source/BASELINE_REUSE_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
