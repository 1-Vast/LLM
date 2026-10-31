"""Source identity availability only; no read-count or biological response access."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parent.parent
SOURCE = E / 'investigator/sources/promoter_425a.csv.hop1'
DESIGN = E / 'root/local_donor_design_pairs.json'
FIELDS = ['chr', 'isoform', 'intron1start_o', 'intron2start_o',
          'intron1_maxent5_nt', 'intron2_maxent5_nt']
labels = {}
for pair in json.loads(DESIGN.read_text())['pairs']:
    labels[pair['reference_id']] = 'GT'
    labels[pair['edited_id']] = 'GC'
summary = defaultdict(Counter)
seen = defaultdict(lambda: defaultdict(set))
exceptions = []
with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.reader(stream)
    header = next(reader)
    indices = [header.index(field) for field in FIELDS]
    for values in reader:
        row = [values[index] for index in indices]
        variant = str(int(float(row[0])))
        if variant not in labels:
            continue
        label = labels[variant]
        summary[label]['exported_rows'] += 1
        for slot in (0, 1):
            raw = float(row[2 + slot]) if row[2 + slot] else float('nan')
            corrected = float(row[4 + slot]) if row[4 + slot] else float('nan')
            if raw == 435:
                summary[label]['representative_raw_donor435_rows'] += 1
                summary[label]['representative_donor435_survives_within3_rows'] += 432 <= corrected <= 438
                if not 432 <= corrected <= 438 and len(exceptions) < 5:
                    exceptions.append({'id': variant, 'isoform': row[1], 'slot': slot + 1,
                                       'corrected': str(corrected)})
        endpoints = tuple(int(value) for value in row[1].split('_')[1:] if value)
        kinds = []
        if endpoints == (88, 1214):
            kinds.append('S')
        if len(endpoints) == 4 and endpoints[0] == 88 and endpoints[3] == 1214:
            a, d = endpoints[1:3]
            if 303 <= a <= 420 and 450 <= d <= 600:
                kinds.append('C_broad')
                if 416 <= a <= 420:
                    kinds.append('C_coverage_guarded')
        for kind in kinds:
            summary[label][kind + '_identity_rows'] += 1
            seen[label][kind].add(variant)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


out = {'scope': 'Unweighted identity availability, not RNA abundance or response analysis',
       'source_sha256': sha(SOURCE), 'design_sha256': sha(DESIGN),
       'script_sha256': sha(Path(__file__)),
       'contract_sha256': sha(E / 'root/donor_survival_identity_contract.md'),
       'projected_columns': FIELDS, 'design_constructs': len(labels),
       'summary': {label: dict(values) for label, values in summary.items()},
       'constructs_with_identity': {label: {kind: len(ids) for kind, ids in kinds.items()}
                                    for label, kinds in seen.items()},
       'donor_identity_exceptions': exceptions, 'RNA_count_fields_used': False,
       'physical_G_purity_qualified': False, 'all_preimages_recovered': False}
target = E / 'root/donor_survival_identity_check.json'
assert not target.exists()
target.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(out))
