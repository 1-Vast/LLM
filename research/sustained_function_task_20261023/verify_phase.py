"""Verify this phase's seals and the preceding local snapshot; no scientific rerun."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/sustained_function_task'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    for role in ('constructive', 'critic', 'source'):
        for stem in ('INDEPENDENT', 'CROSS'):
            directory = OUT / role
            possible = [directory / (stem + suffix) for suffix in ('.seal.json', '_SEAL.json')]
            seal_path = next(p for p in possible if p.exists())
            seal = json.loads(seal_path.read_text(encoding='utf-8-sig'))
            if 'files' in seal:
                for name, expected in seal['files'].items():
                    checks.append(dict(path=name, ok=digest(ROOT / name) == expected))
                continue
            expected = seal.get('sha256', seal.get('cross_sha256'))
            actual = digest(directory / (stem + '.md'))
            checks.append(dict(path=str(directory / (stem + '.md')),
                               ok=actual.lower() == expected.lower()))
    for role in ('constructive', 'critic'):
        document = OUT / role / 'DELAYED_RESULT_REVIEW.md'
        seal = json.loads(document.with_suffix('.seal.json').read_text(encoding='utf-8-sig'))
        checks.append(dict(path=str(document), ok=digest(document).lower() == seal['sha256'].lower()))
    freeze = json.loads((OUT / 'DELAYED_DEATH_FREEZE.json').read_text(encoding='utf-8'))
    for entry in freeze['files']:
        checks.append(dict(path=entry['path'],
                           ok=digest(ROOT / entry['path']) == entry['sha256']))
    prior = json.loads((ROOT / 'log/20261023/update_strategy_renewal/VERIFICATION.json').read_text(encoding='utf-8'))
    for name, expected in prior['files'].items():
        checks.append(dict(path=name, ok=digest(ROOT / name) == expected))
    for receipt in list((OUT / 'root').glob('*.receipt.json')) + list((OUT / 'constructive').glob('*.receipt.json')):
        metadata = json.loads(receipt.read_text(encoding='utf-8'))
        body = receipt.with_name(receipt.name.replace('.receipt.json', '.body'))
        checks.append(dict(path=str(body), ok=digest(body) == metadata['sha256']))
    source_bodies = ('GET1_search.json', 'GET2_PMC11841093.xml', 'GET3_zenodo14507473.json')
    receipts = [json.loads(line) for line in (OUT / 'source/REQUESTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(receipts) == len(source_bodies)
    for metadata, name in zip(receipts, source_bodies):
        body = OUT / 'source' / name
        checks.append(dict(path=str(body), ok=digest(body) == metadata['sha256']))
    failures = [entry for entry in checks if not entry['ok']]
    snapshots = {}
    for directory in (OUT, ROOT / 'research/sustained_function_task_20261023'):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                snapshots[str(path.relative_to(ROOT))] = digest(path)
    destination = OUT / 'VERIFICATION.json'
    assert not destination.exists()
    result = dict(utc=datetime.now(timezone.utc).isoformat(),
                  goal='ACTIVE / NOT_ACHIEVED', files=snapshots,
                  seal_prior_receipt_checks=len(checks), preceding_files=len(prior['files']),
                  failures=failures,
                  scope='Local bytes, not global historical provenance or biological truth')
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshots), checks=len(checks), failures=failures), indent=2))
    assert not failures
