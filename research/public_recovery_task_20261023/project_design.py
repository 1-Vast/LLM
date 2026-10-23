"""Inspect only leading design fields of the pinned functional-assay CSV."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/public_recovery_task/root'
lines = (OUT / 'count_header_source.body').read_bytes().splitlines()
header = lines[0].decode('utf-8-sig').split(',')
assert header == ['sample', 'replicate', 'schedule', '0', '7', '14', '21', '28']
records = []
for line in lines[1:]:
    if not line.strip():
        continue
    leading = line.split(b',', 3)[:3]
    assert len(leading) == 3
    records.append(dict(zip(header[:3], (part.decode('utf-8') for part in leading))))
result = dict(header=header, design=records,
              scope='Design fields only; outcome byte suffixes not decoded or numerically parsed')
destination = OUT / 'COUNT_DESIGN.json'
assert not destination.exists()
destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
