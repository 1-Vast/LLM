"""Bind the reviewed finite experiment before scientific extraction."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment'


def verify():
    frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in frozen['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def main():
    assert not (OUT / 'FREEZE.json').exists()
    assert not (OUT / 'matrix.npz').exists()
    manifest_path = OUT / 'DOWNLOAD_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    inventory = json.loads((OUT / 'IDENTITY_INVENTORY.json').read_text(encoding='utf-8'))
    policy = json.loads((OUT / 'IDENTITY_POLICY.json').read_text(encoding='utf-8'))
    assert manifest['complete'] and inventory['manifest_complete_flag']
    assert inventory['successful_files_examined'] == 48
    assert inventory['manifest_sha256_at_start'] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert not inventory['files_with_duplicate_identifiers']
    for record in inventory['records']:
        assert record['row_count'] and not record['empty_identifier_rows']
        expected = policy['uncertain_file_labels'].get(record['drug'], record['repository_drug'])
        normalize = lambda s: policy['aliases'].get(s.strip(), s.strip())
        assert all(normalize(name) == normalize(expected) for name in record['distinct_internal_drug_counts']), record['drug']
    paths = list((ROOT / 'research/decrypte_molecular_increment_20261022').glob('*.py'))
    paths += [OUT / name for name in (
        'NUMERICAL_PROTOCOL_DRAFT.md', 'PROTOCOL_AMENDMENT.md', 'LEXICAL_AMENDMENT.md',
        'ADDITIONAL_IDENTITY_AMENDMENT.md', 'IDENTITY_POLICY.json', 'IDENTITY_INVENTORY.json',
        'DOWNLOAD_MANIFEST.json',
        'review/ADDITIONAL_IDENTITY_DISPOSITION.md',
        'review/LEXICAL_IDENTITIES.md', 'SYNTHETIC_CHECKS.json',
        'review/INDEPENDENT.md', 'review/CROSS_REVIEW.md', 'review/IDENTITY_DISPOSITION.md',
        'assay/INDEPENDENT.md', 'assay/CROSS_REVIEW.md', 'assay/CHDI_IDENTITY.md',
        'assay/CODE_AUDIT.md', 'assay/CODE_AUDIT_ADDENDUM.md',
        'assay/FINAL_IDENTITY_CODE_AUDIT.md',
        'downloads/EXPOSURE_INCIDENT.md')]
    paths += [ROOT / 'research/decrypte_feedback_pilot_20261022/run_pilot.py']
    paths += [ROOT / 'log/20261022/decrypte_feedback_pilot' / name for name in (
        'PARTITIONS.json', 'DEVELOPMENT_VALUES.json', 'PREDICTIONS.json')]
    files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(paths)}
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
              'head': '47a0e2dea5a7dd42379fa17eb3621caf6bd0114c',
              'scope': 'Exploratory pre-root-extraction freeze; team CHDI exposure disclosed; not universal blindness',
              'downloads': 'Complete48 manifest and metadata inventory frozen; PREPARATION also records manifest hash'}
    (OUT / 'FREEZE.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(files), 'utc': result['utc']}))


if __name__ == '__main__':
    main()
