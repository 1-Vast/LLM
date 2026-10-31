"""Correct library-prefix and absent-junction conventions; response fields unused."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parent.parent
SOURCE = E / 'investigator/sources/promoter_425a.csv.hop1'
RAW = ['intron1start_o', 'intron1end_o', 'intron2start_o', 'intron2end_o']
CORRECTED = ['intron1_maxent5_nt', 'intron1_maxent3_nt', 'intron2_maxent5_nt', 'intron2_maxent3_nt']
ALLOWED = ['chr', 'isoform', *RAW, *CORRECTED]


def normalize(value):
    if value.strip().lower() in ('', 'nan', 'none'):
        return 'nan'
    number = float(value)
    assert number.is_integer(), value
    return str(int(number))


def isoform_key(variant, coordinates):
    parts = [variant]
    for index in (0, 2):
        pair = coordinates[index:index + 2]
        if pair != ('0', '0'):
            parts.extend(pair)
    return '_'.join(parts)


checks = Counter()
examples = []
with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.reader(stream)
    header = next(reader)
    indices = {key: header.index(key) for key in ALLOWED}
    for values in reader:
        row = {key: values[index] for key, index in indices.items()}
        variant = normalize(row['chr'])
        raw = tuple(normalize(row[key]) for key in RAW)
        corrected = tuple(normalize(row[key]) for key in CORRECTED)
        raw_key = isoform_key(variant, raw)
        corrected_key = isoform_key(variant, corrected)
        checks['rows'] += 1
        checks['literal_matches_o'] += row['isoform'] == raw_key
        checks['literal_matches_corrected'] += row['isoform'] == corrected_key
        checks['o_differs_from_corrected'] += raw != corrected
        checks['coordinate_pairs_with_nan'] += any(value == 'nan' for value in (*raw, *corrected))
        if row['isoform'] != corrected_key and len(examples) < 5:
            examples.append({'library_id': variant, 'literal_isoform': row['isoform'],
                             'o_key': raw_key, 'corrected_key': corrected_key})

out = {'scope': 'Unweighted coordinate identities only; RNA counts and responses unused',
       'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'contract_sha256': hashlib.sha256((E / 'root/coordinate_identity_contract_v2.md').read_bytes()).hexdigest(),
       'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'projected_columns': ALLOWED, 'identity_checks': dict(checks),
       'unresolved_corrected_key_examples': examples,
       'supersedes_only': 'Invalid literal-key match comparisons in coordinate_identity_check.json',
       'RNA_count_fields_used': False, 'upstream_raw_count_preservation_qualified': False}
target = E / 'root/coordinate_identity_check_v2.json'
assert not target.exists()
target.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(out))
