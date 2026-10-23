"""Decode only CSV header and first five identifier fields, never count fields."""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/replicated_contrast'
DATA = OUT/'counts.body'
groups, constructs, probes, rows = Counter(), set(), defaultdict(set), 0
with DATA.open('rb') as source:
    header = next(csv.reader([source.readline().decode('utf-8-sig')]))
    assert header[:5] == ['construct_id', 'target_a_id', 'probe_a_id', 'target_b_id', 'probe_b_id']
    for raw in source:
        fields = raw.rstrip(b'\r\n').split(b',', 5)
        assert len(fields) == 6 and all(b'"' not in f for f in fields[:5])
        construct, a, ga, b, gb = [s.decode('utf-8') for s in fields[:5]]
        assert construct not in constructs
        constructs.add(construct)
        pair = tuple(sorted((a, b)))
        groups[pair] += 1
        probes[a].add(ga)
        probes[b].add(gb)
        rows += 1
result = dict(columns=header, column_count=len(header), rows=rows, canonical_pairs=len(groups),
              constructs_per_pair=dict(Counter(groups.values())),
              probe_counts_per_target=dict(Counter(len(v) for v in probes.values())),
              probe_examples={k: sorted(probes[k]) for k in sorted(probes)[:4]},
              selected_columns=[s for s in header if s in ('MCF7_T9_1', 'MCF7_T9_2', 'MDAMB231_T9_1', 'MDAMB231_T9_2')],
              scope='Correct comma delimiter; first five ID fields decoded, remainder retained as opaque bytes')
assert len(result['selected_columns']) == 4
target = OUT/'METADATA.json'
assert not target.exists()
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
