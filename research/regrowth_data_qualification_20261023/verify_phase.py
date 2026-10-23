"""Check phase seals, retrieval bytes and previous local snapshot without fitting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/regrowth_data_qualification'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    for role in ('root', 'source', 'critic'):
        for stem in ('INDEPENDENT', 'CROSS'):
            directory = OUT / role
            candidates = [directory / (stem + suffix) for suffix in ('.seal.json', '_SEAL.json')]
            seal = json.loads(next(p for p in candidates if p.exists()).read_text(encoding='utf-8-sig'))
            expected = seal.get('sha256', seal.get('cross_sha256'))
            checks.append(digest(directory / (stem + '.md')).lower() == expected.lower())
    source_seal = json.loads((OUT / 'source/INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
    checks.append(digest(OUT / 'source/HEADERS.json') == source_seal['headers_sha256'])
    receipt = json.loads((OUT / 'root/clpp_primary.receipt.json').read_text(encoding='utf-8'))
    checks.append(digest(OUT / 'root/clpp_primary.body') == receipt['sha256'])
    receipts = [json.loads(line) for line in (OUT / 'source/REQUESTS.jsonl').read_text(encoding='utf-8').splitlines()]
    for receipt, name in zip(receipts, ('GET1_OA_metadata.xml', 'GET2_EuropePMC_supplement.body'), strict=True):
        checks.append(digest(OUT / 'source' / name) == receipt['sha256'])
    prior = json.loads((ROOT / 'log/20261023/sustained_function_task/VERIFICATION.json').read_text(encoding='utf-8'))
    for name, expected in prior['files'].items():
        checks.append(digest(ROOT / name) == expected)
    files = {}
    for directory in (OUT, ROOT / 'research/regrowth_data_qualification_20261023'):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[str(path.relative_to(ROOT))] = digest(path)
    result = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                  files=files, checks=len(checks), preceding_files=len(prior['files']),
                  failures=sum(not check for check in checks),
                  scope='Local bytes, not biological truth or global historical provenance')
    destination = OUT / 'VERIFICATION.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
    assert all(checks)
