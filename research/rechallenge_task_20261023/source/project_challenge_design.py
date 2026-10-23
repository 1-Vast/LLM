"""Decode header and sample/rep identities only, never response suffix bytes."""
from pathlib import Path
from collections import Counter
import csv
import io
import hashlib
import json

out = Path('log/20261023/rechallenge_task/source')
raw = (out / 'GET5_challenge_original.body').read_bytes()
lines = raw.splitlines()
header = next(csv.reader([lines[0].decode('utf-8-sig')]))
assert header[:2] == ['sample', 'rep_number']
design = []
for line in lines[1:]:
    if not line.strip():
        continue
    first, second, unopened = line.split(b',', 2)
    # Current design fields have no quoted commas; reject rather than scan responses.
    assert b'"' not in first + second
    design.append(dict(sample=first.decode('utf-8'), rep_number=second.decode('utf-8')))
result = dict(header=header, design=design,
              groups=dict(Counter(d['sample'] for d in design)),
              git_blob_sha1=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
              scope='all original bytes saved; header and two identity fields only decoded; numeric response suffix never decoded/cast')
(out / 'CHALLENGE_DESIGN.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
