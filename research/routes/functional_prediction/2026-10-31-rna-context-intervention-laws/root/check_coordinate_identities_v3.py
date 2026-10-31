"""Compare source-defined key serialization; RNA count/effect columns unused."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

E = Path(__file__).resolve().parent.parent
SOURCE = E / 'investigator/sources/promoter_425a.csv.hop1'
FIELDS = ['chr', 'isoform', 'intron1start_o', 'intron1end_o', 'intron2start_o', 'intron2end_o',
          'intron1_maxent5_nt', 'intron1_maxent3_nt', 'intron2_maxent5_nt', 'intron2_maxent3_nt']


def coordinates(values):
    result = []
    for value in values:
        number = float(value) if value.strip() else math.nan
        if number > 0:
            assert number.is_integer()
            result.append(int(number))
    return sorted(result)


checks = Counter()
examples = []
with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.reader(stream)
    header = next(reader)
    indices = [header.index(field) for field in FIELDS]
    for values in reader:
        row = [values[index] for index in indices]
        prefix = str(int(float(row[0]))) + '_'
        raw, corrected = coordinates(row[2:6]), coordinates(row[6:10])
        raw_key = prefix + '_'.join(map(str, raw))
        corrected_key = prefix + '_'.join(map(str, corrected))
        checks['rows'] += 1
        checks['literal_matches_o'] += row[1] == raw_key
        checks['literal_matches_corrected'] += row[1] == corrected_key
        checks['raw_and_corrected_boundary_sets_differ'] += raw != corrected
        if row[1] != corrected_key and len(examples) < 5:
            examples.append({'literal': row[1], 'expected': corrected_key})

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


out = {'scope': 'Source-derived, unweighted identity-only serialization; no RNA count/effect analysis',
       'projected_columns': FIELDS, 'identity_checks': dict(checks), 'unresolved_examples': examples,
       'source_sha256': sha(SOURCE), 'script_sha256': sha(Path(__file__)),
       'contract_sha256': sha(E / 'root/coordinate_identity_contract_v3.md'),
       'upstream_code_sha256': sha(E / 'root/sources/mpra_ce.detect_splicesites.py'),
       'RNA_count_fields_used': False, 'all_raw_preimages_recoverable_from_export': False,
       'interpretation': 'Corrected endpoint serialization, not physical donor identity or homogeneous raw counts. v1/v2 interpretation corrections preserved.'}
target = E / 'root/coordinate_identity_check_v3.json'
assert not target.exists()
target.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(out))
