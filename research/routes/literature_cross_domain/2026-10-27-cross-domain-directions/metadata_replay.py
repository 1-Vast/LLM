"""Replay exact-time entity overlap from already exposed public design metadata."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'eight_directions_20261026/evidence_audit/mixseq_design_census.csv'
times = defaultdict(set)
with SOURCE.open(encoding='utf-8-sig', newline='') as handle:
    for row in csv.DictReader(handle):
        times[row['time']].add((row['perturbation'], row['cell_line']))
overlap = times['6'] & times['24']
result = {
    'source': str(SOURCE.relative_to(ROOT.parent.parent)),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'evidence': 'observed_design_metadata_only_no_expression_or_response_read',
    'all_time_labels': sorted(times),
    'exact_time_keys': {t: len(times[t]) for t in ['6', '24']},
    'common_drug_cell_keys_at_exact_6h_24h': len(overlap),
    'common_drugs': len({drug for drug, cell in overlap}),
    'common_cell_lines': len({cell for drug, cell in overlap}),
    'per_drug_common_cell_line_counts': dict(sorted(Counter(drug for drug, cell in overlap).items())),
    'scope': ('Time labels exactly 6 and 24 only; common entities do not certify matched dose, culture, '
              'batch or sample independence. Mixed time labels remain unresolved. No individual-cell '
              'trajectory or function/engagement pairing is established.'),
}
assert len(overlap) == 285 and result['common_drugs'] == 5
(ROOT / 'mixseq_metadata_check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
