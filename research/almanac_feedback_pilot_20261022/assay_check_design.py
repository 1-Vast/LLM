"""Audit derived design metadata only; never opens archive or response files."""
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parents[2]
folder = root / 'log/20261022/almanac_feedback_pilot'
tasks = json.loads((folder / 'root/DESIGN_TASKS.json').read_text())
keys, combo_rows = set(), set()
plates = defaultdict(set)
counts = Counter()
for t in tasks:
    assert len(t['pair']) == 2 and t['pair'][0] < t['pair'][1]
    assert len(t['combination_rows']) == len(set(t['combination_rows'])) == 9
    assert len(t['single_agent_rows']) == len(set(t['single_agent_rows'])) == 6
    assert not set(t['combination_rows']) & set(t['single_agent_rows'])
    assert not combo_rows & set(t['combination_rows'])
    combo_rows.update(t['combination_rows'])
    for axis in t['doses']:
        doses = list(map(Decimal, axis))
        assert len(doses) == len(set(doses)) == 3
        assert doses == sorted(doses) and doses[0] > 0
    key = json.dumps([t['cell'], t['pair'], t['doses']])
    assert key not in keys
    keys.add(key)
    assert t['valid_flags'] == ['Y']
    assert all(min(t['combination_rows']) < row for row in t['other_occurrence_first_rows'])
    plates[(t['study'], t['plate'])].add(tuple(t['cell']))
    counts['alternate_occurrences'] += len(t['other_occurrence_first_rows'])
assert all(len(cells) == 1 for cells in plates.values())
result = {'scope': 'Derived DESIGN_TASKS metadata only; not an independent raw row audit',
          'tasks': len(tasks), 'unique_combination_row_references': len(combo_rows),
          'physical_plate_keys': len(plates), 'counts': dict(counts), 'assertions': 'PASS'}
out = folder / 'assay/DESIGN_METADATA_CHECK.json'
assert not out.exists()
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
