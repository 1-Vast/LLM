"""Inspect existing result-table identities without decoding metric columns."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/repair_information_opportunity'
NAMES = ('research/dual_core_innovation_validation_20261021/RUN/sel_eval/Q_per_background.csv',
         'research/dual_core_innovation_validation_20261021/RUN/final_eval/Q_per_background.csv',
         'research/dual_core_innovation_validation_20261021/RUN/selection/sel_Q_M1.csv')
records = []
for name in NAMES:
    path = ROOT / name
    raw = path.read_bytes()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        identities = [(row['cell'], row['lineage'], row['arm']) for row in reader]
    records.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'header': header, 'rows': len(identities),
                    'cell_lineages': sorted(set((cell, lin) for cell, lin, _ in identities)),
                    'arms': sorted(set(arm for _, _, arm in identities))})
with (OUT / 'CACHED_TABLE_IDENTITIES.json').open('x', encoding='utf-8') as handle:
    json.dump(records, handle, indent=2)
print(json.dumps(records))
