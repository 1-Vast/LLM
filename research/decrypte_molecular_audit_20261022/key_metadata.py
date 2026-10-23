"""Validate proposed identifier prefix removal using strings only; no intensity access."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment'
payload_path = OUT / 'PAYLOADS.json'
inventory_path = OUT / 'IDENTITY_INVENTORY.json'
payloads = json.loads(payload_path.read_text(encoding='utf-8'))
inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
records = {r['drug']: r for r in inventory['records']}
assert set(payloads) == set(records) and len(records) == 48
suffix_sets = {}
report = []
failures = []
for drug, rows in payloads.items():
    names = list(records[drug]['distinct_internal_drug_counts'])
    assert len(names) == 1
    prefix = names[0] + ':'
    counts = Counter()
    invalid = []
    for row in rows:
        identifier = row[0]  # Do not access numeric payload at index2.
        if not identifier.startswith(prefix) or len(identifier) == len(prefix):
            invalid.append(identifier)
        else:
            counts[identifier[len(prefix):]] += 1
    duplicates = {key: value for key, value in counts.items() if value > 1}
    suffix_sets[drug] = set(counts)
    report.append({'drug': drug, 'internal_name': names[0], 'exact_prefix': prefix,
                   'identifier_count': len(rows), 'suffix_count': len(counts),
                   'invalid_prefix_identifiers': invalid, 'duplicate_suffixes': duplicates,
                   'protein_group_suffix_count': sum(';' in s for s in counts),
                   'additional_colon_suffix_count': sum(':' in s for s in counts)})
    if invalid or duplicates:
        failures.append(drug)
occurrence = Counter(s for values in suffix_sets.values() for s in values)
drugs = sorted(suffix_sets)
overlap = [len(suffix_sets[a] & suffix_sets[b])
           for i, a in enumerate(drugs) for b in drugs[i+1:]]
overlap.sort()
result = {'status': 'PASS' if not failures else 'FAIL',
          'source_payload_sha256': hashlib.sha256(payload_path.read_bytes()).hexdigest(),
          'source_inventory_sha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
          'drug_count': len(drugs), 'identifier_rows_checked': sum(len(r) for r in payloads.values()),
          'rule': "Remove exactly one prefix equal to that file's observed internal drug string plus colon; retain entire remaining suffix unchanged",
          'numeric_payloads_semantically_accessed_by_this_script': False,
          'failures': failures, 'unique_suffix_union': len(occurrence),
          'suffixes_shared_at_least_two_drugs': sum(n >= 2 for n in occurrence.values()),
          'suffixes_present_in_all_48': sum(n == 48 for n in occurrence.values()),
          'suffix_occurrence_histogram': dict(sorted(Counter(occurrence.values()).items())),
          'pairwise_overlap': {'pairs': len(overlap), 'minimum': overlap[0],
                               'median': (overlap[len(overlap)//2-1] + overlap[len(overlap)//2]) / 2,
                               'maximum': overlap[-1]},
          'original_prediction_file_exists': (OUT / 'PREDICTIONS.json').exists(),
          'original_summary_file_exists': (OUT / 'SUMMARY.json').exists(),
          'records': report}
(OUT / 'review/PROTEIN_KEY_METADATA.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'suffix_occurrence_histogram')}, indent=2))
