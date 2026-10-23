"""Freeze pair membership from identifiers only, before any functional values."""
from collections import Counter
import csv
import hashlib
from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract'
genes = json.loads((OUT / 'IDENTITY_JOIN.json').read_text())['matched_single_genes']
assert len(genes) == len(set(genes)) == 105
rows = []
for first, second in combinations(sorted(genes), 2):
    pair = first + '|' + second
    split_hash = hashlib.sha256(('MAESTRO_NORMAN_FUNCTION_V1|' + pair).encode()).digest()
    bucket = int.from_bytes(split_hash[:8], 'big') % 100
    split = 'source' if bucket < 60 else 'development' if bucket < 80 else 'protected'
    order = hashlib.sha256(('MAESTRO_NORMAN_BUDGET_V1|' + pair).encode()).hexdigest()
    rows.append({'gene_a': first, 'gene_b': second, 'pair': pair,
                 'split': split, 'bucket': bucket, 'source_order': order})
with (OUT / 'PAIR_SPLITS.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
assert len(rows) == len({r['pair'] for r in rows}) == 5460
result = {'potential_pairs_by_split': dict(Counter(r['split'] for r in rows)),
          'membership_only': True, 'functional_missingness_checked': False,
          'eligibility': 'Provisional105single targets; QC/feature availability still to qualify without changing pair split',
          'sha256': hashlib.sha256((OUT / 'PAIR_SPLITS.csv').read_bytes()).hexdigest()}
(OUT / 'PAIR_SPLITS.seal.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
