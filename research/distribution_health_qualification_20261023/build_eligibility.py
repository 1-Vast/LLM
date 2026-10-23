"""Freeze metadata-only known-target membership before any primary outcome values."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/distribution_health_qualification'
SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'

if __name__ == '__main__':
    target = OUT / 'ELIGIBILITY.tsv'
    if target.exists():
        raise FileExistsError(target)
    ids, controls = {}, set()
    with (SOURCE / 'idr_target_metadata.body').open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            guide = row['Reagent Identifier']
            ids.setdefault(guide, set())
            if row['Gene Identifier']:
                ids[guide].add(row['Gene Identifier'])
            if row['Control Type']:
                controls.add(guide)
    conditions = set()
    with (SOURCE / 'all_metadata.body').open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle, delimiter='\t'):
            conditions.add((row['Metadata_pert_name'], row['Metadata_cell_line']))
    eligible, excluded = [], []
    for guide, line in sorted(conditions):
        identifiers = ids.get(guide, set())
        if guide == 'EMPTY' or guide in controls:
            excluded.append((guide, line, 'reference_control'))
        elif len(identifiers) != 1:
            excluded.append((guide, line, 'missing_or_conflicting_target_id'))
        else:
            eligible.append((guide, line, next(iter(identifiers))))
    for path, header, rows in (
            (target, ('guide', 'cell_line', 'canonical_target_id'), eligible),
            (OUT / 'EXCLUSIONS.tsv', ('guide', 'cell_line', 'reason'), excluded)):
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle, delimiter='\t', lineterminator='\n')
            writer.writerow(header)
            writer.writerows(rows)
    record = {'scope': 'Metadata-only membership, not protected outcomes or a final predictive protocol',
              'eligible_conditions': len(eligible), 'eligible_guides': len({r[0] for r in eligible}),
              'canonical_target_groups': len({r[2] for r in eligible}),
              'excluded_conditions': len(excluded),
              'primary_endpoint': 'vb_percent_dead',
              'grouping_rule': 'All guides and lines sharing canonical_target_id remain in the same partition',
              'sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                         for name in ('ELIGIBILITY.tsv', 'EXCLUSIONS.tsv')},
              'source_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                                for name in ('idr_target_metadata.body', 'all_metadata.body')}}
    (OUT / 'ELIGIBILITY_RECORD.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
