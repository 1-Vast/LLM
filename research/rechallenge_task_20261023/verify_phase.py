"""Check retrieval bytes, sealed reports and preceding local snapshot only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/rechallenge_task'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    def check(path, expected):
        checks.append(dict(path=str(path), matches=digest(path).lower() == expected.lower()))

    prior = read(ROOT / 'log/20261023/public_recovery_task/VERIFICATION.json')
    for name, expected in prior['files'].items():
        check(ROOT / name, expected)
    for path in sorted(OUT.rglob('*.json')):
        if 'seal' not in path.name.lower():
            continue
        seal = read(path)
        for key in ('artifact', 'report'):
            if key in seal and 'sha256' in seal:
                check(ROOT / seal[key], seal['sha256'])
        if 'design_sha256' in seal:
            check(path.parent / 'CHALLENGE_DESIGN.json', seal['design_sha256'])
        entries = seal.get('files', [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and 'path' in entry and 'sha256' in entry:
                    check(ROOT / entry['path'], entry['sha256'])
        elif isinstance(entries, dict):
            for name, expected in entries.items():
                candidate = ROOT / name
                check(candidate if candidate.exists() else path.parent / name, expected)
    root_receipts = list((OUT / 'root').glob('*.receipt.json'))
    for path in root_receipts:
        receipt = read(path)
        check(path.with_name(path.name.replace('.receipt.json', '.body')), receipt['sha256'])
    source_names = ('GET1_commits.json', 'GET2_tree.json', 'GET3_README.md',
                    'GET4_fig3_dose_responses.R', 'GET5_challenge_original.body')
    source_receipts = [json.loads(line) for line in (OUT / 'source/REQUESTS.jsonl').read_text(encoding='utf-8').splitlines()]
    for receipt, name in zip(source_receipts, source_names, strict=True):
        check(OUT / 'source' / name, receipt['sha256'])
    api = read(OUT / 'api/RECEIPT.json')
    # API receipt hashes the logical LF prompt string. Windows write_text
    # saved CRLF bytes; check that claim as text and snapshot raw bytes below.
    prompt = (OUT / 'api/PROMPT.md').read_text(encoding='utf-8')
    checks.append(dict(path=str(OUT / 'api/PROMPT.md'),
                       scope='Logical UTF-8 prompt with universal newline decoding, not on-disk byte hash',
                       matches=hashlib.sha256(prompt.encode()).hexdigest() == api['prompt_sha256']))
    snapshots = {}
    for directory in (OUT, ROOT / 'research/rechallenge_task_20261023'):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION_v2.json':
                snapshots[str(path.relative_to(ROOT))] = digest(path)
    result = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshots,
                  checks=checks, preceding_files=len(prior['files']),
                  failures=sum(not c['matches'] for c in checks),
                  root_gets=len(root_receipts), source_gets=len(source_receipts),
                  goal='ACTIVE / NOT_ACHIEVED',
                  scope='Local hash/receipt snapshot only, not assay truth, scientific independence or historical global provenance')
    destination = OUT / 'VERIFICATION_v2.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'files')}, indent=2))
    print('checks', len(checks), 'files', len(snapshots))
    assert result['failures'] == 0
