"""Before values, certify the study-exclusion diagnostic has enough source rows."""
import json
from collections import Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'


def main():
    assert not (OUT / 'STUDY_EXCLUSION_DESIGN.json').exists()
    split = json.loads((OUT / 'SPLIT.json').read_text())
    tasks = json.loads((OUT / 'DESIGN_TASKS.json').read_text())
    study = np.array([[tasks[i]['study'] for i in row] for row in split['task_indices_by_cell_pair']])
    counts = (study[:30, None] != study[None, 30:40]).sum(axis=0)
    result = {'scope': 'metadata only; same-pair source study exclusion',
              'source_n_histogram': dict(Counter(map(int, counts.ravel()))),
              'minimum_source_n': int(counts.min()), 'all_at_least_two': bool(np.all(counts >= 2)),
              'source_fit_cells': 30, 'development_cells': 10, 'pairs': split['pair_count']}
    assert result['all_at_least_two'], 'Sensitivity unavailable: freeze must be revised before response access'
    (OUT / 'STUDY_EXCLUSION_DESIGN.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
