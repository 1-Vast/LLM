import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/ptpc_update_opportunity'
source = json.loads((OUT / 'HEADER_COMPATIBILITY.json').read_text())
records = source['headers'][1:]
accessions = [r['identifier'].split('_', 1)[0] for r in records]
pattern = r'(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9](?:[A-Z][A-Z0-9]{2}[0-9])?)'
invalid = [a for a in accessions if re.fullmatch(pattern, a) is None]
duplicates = sorted(a for a in set(accessions) if accessions.count(a) > 1)
common = sorted(set(accessions) & set(source['old_ordered_nodes']))
result = {'rule': 'literal prefix before first underscore; no gene or isoform mapping',
          'invalid_accessions': invalid, 'duplicate_accessions': duplicates,
          'new_count': len(accessions), 'old_count': source['old_count'],
          'exact_accession_common_count': len(common), 'common_accessions': common,
          'new_ordered_accessions': accessions}
target = OUT / 'ACCESSION_ALIGNMENT.json'
assert not target.exists()
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in ('common_accessions', 'new_ordered_accessions')}))
