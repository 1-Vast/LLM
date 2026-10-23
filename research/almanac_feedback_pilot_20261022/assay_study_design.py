"""Check source exclusion sizes using frozen metadata only."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
folder = root / 'log/20261022/almanac_feedback_pilot'
split = json.loads((folder / 'root/SPLIT.json').read_text())
tasks = json.loads((folder / 'root/DESIGN_TASKS.json').read_text())
indices = split['task_indices_by_cell_pair']
hist = Counter()
for p in range(split['pair_count']):
    source = [tasks[row[p]]['study'] for row in indices[:30]]
    for row in indices[30:40]:
        target = tasks[row[p]]['study']
        hist[sum(s != target for s in source)] += 1
result = {'scope': 'Frozen design metadata only; no response access',
          'source_n_histogram': dict(sorted(hist.items())), 'min_source_n': min(hist),
          'all_study_sensitivity_source_n_at_least_two': min(hist) >= 2}
out = folder / 'assay/STUDY_SOURCE_SIZE.json'
assert not out.exists()
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
