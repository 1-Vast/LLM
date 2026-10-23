"""Verify phase sources, frozen calculations, identity audits and final bytes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path):
    obj = read(path)
    entries = obj.get('files', [obj])
    if isinstance(entries, dict):
        entries = [dict(path=name, sha256=value if isinstance(value, str) else value['sha256'])
                   for name, value in entries.items()]
    for entry in entries:
        source = Path(entry['path'] if 'path' in entry else entry['file'])
        if not source.is_absolute():
            source = ROOT / source
        assert digest(source) == entry['sha256'], str(source)
    return len(entries)


if __name__ == '__main__':
    target = OUT / 'VERIFICATION.json'
    if target.exists():
        print(json.dumps(dict(files=check(target), drift=0, mode='recheck')))
        sys.exit(0)
    seals = [ROOT / 'log/20261023/depmap_state_increment/VERIFICATION.json',
             ROOT / 'log/20261023/functional_update_operation/VERIFICATION.json',
             OUT / 'ALLOCATION_FREEZE.json']
    seals += sorted(p for p in OUT.rglob('*.json') if 'seal' in p.name.lower())
    checked = {str(p.relative_to(ROOT)): check(p) for p in seals}
    requests = []
    for ledger in sorted((OUT / 'sources').glob('*REQUESTS.json')) + [OUT / 'sources/SEARCHES.json']:
        for row in read(ledger):
            suffix = '.json' if ledger.name == 'SEARCHES.json' else '.body'
            source = ledger.parent / (row['name'] + suffix)
            assert digest(source) == row['sha256']
            requests.append(dict(status=row['status'], bytes=row['bytes']))
    for receipt in sorted((OUT / 'rhaister').glob('*.receipt.json')):
        row = read(receipt)
        source = receipt.with_name(receipt.name.replace('.receipt.json', '.body'))
        assert digest(source) == row['sha256']
        requests.append(dict(status=row['status'], bytes=row['bytes']))
    receipt = read(OUT / 'IDENTITY_RECEIPT.json')
    assert digest(OUT / 'summary_statistics.parquet') == receipt['sha256']
    requests.append(dict(status=receipt['status'], bytes=receipt['bytes']))
    assert len(requests) == 24
    identity, independent = read(OUT / 'IDENTITY_RESULT.json'), read(OUT / 'rhaister/IDENTITY_CHECK.json')
    for ours, other in [('raw_rows', 'metadata_rows'), ('distinct_cells', 'contexts'),
                        ('distinct_conditions', 'conditions'), ('unique_cell_condition_pairs', 'unique_pairs'),
                        ('single_drug_noncontrol_conditions', 'single_non_DMSO_conditions'),
                        ('distinct_single_drugs', 'single_non_DMSO_drug_count')]:
        assert identity[ours] == independent[other]
    audit = read(OUT / 'critic_allocation_check.json')
    assert audit['covariance_checks'] == 812 and all(audit['freeze_hashes'].values())
    assert all(all(case['agreement'].values()) for case in audit['cases'].values())
    files = {p.relative_to(ROOT).as_posix(): digest(p)
             for base in [OUT, Path(__file__).resolve().parent]
             for p in sorted(base.rglob('*')) if p.is_file() and p != target}
    target.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
        scope='source bytes, exact mathematics and identity-only audits; no biological performance',
        files=files, checked_seals=checked, http_requests=len(requests),
        http_body_bytes=sum(row['bytes'] for row in requests),
        http_statuses={str(status): sum(row['status'] == status for row in requests)
                       for status in sorted({row['status'] for row in requests})},
        python=sys.version, platform=platform.platform(), model_api_calls=0,
        decision='STOP_RESTATED_SHIFT / QUALIFIED_RELATIVE_SOURCE / NO_CORE_GO',
        goal='ACTIVE / NOT_ACHIEVED'), indent=2), encoding='utf-8')
    assert check(target) == len(files)
    print(json.dumps(dict(files=len(files), drift=0, http_requests=len(requests),
                         mode='initial-seal')))
