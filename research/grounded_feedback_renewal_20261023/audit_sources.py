"""Audit retained public-source receipts and report seals, not scientific claims."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/grounded_feedback_renewal'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = OUT/'SOURCE_AUDIT.json'
    assert not target.exists()
    checks, requests = [], []
    for receipt in sorted(OUT.rglob('*.receipt.json')):
        record = json.loads(receipt.read_text())
        body = receipt.with_name(receipt.name.replace('.receipt.json', '.body'))
        if 'sha256' in record:
            checks.append(dict(file=str(body.relative_to(ROOT)), matches=sha(body)==record['sha256']))
        requests.append(dict(role=receipt.parent.name, status=record.get('status'),
                             bytes=record.get('bytes'), receipt=str(receipt.relative_to(ROOT))))
    for role in ['constructive', 'critic']:
        for seal in sorted((OUT/role).glob('*SEAL.json')):
            record = json.loads(seal.read_text())
            bound = ({record['path']: record['sha256']} if 'path' in record and 'sha256' in record
                     else record.get('files', record))
            for name, expected in bound.items():
                if not isinstance(expected, str) or len(expected) != 64:
                    continue
                path = ROOT/name if name.startswith('log') or name.startswith('research') else seal.parent/name
                checks.append(dict(file=str(path.relative_to(ROOT)), matches=sha(path)==expected))
    assert len(requests) == 16
    assert all(c['matches'] for c in checks)
    report = dict(utc=datetime.now(timezone.utc).isoformat(), logical_gets=len(requests), requests=requests,
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  source_role_complete=False, api_model_calls=0, experimental_fits=0,
                  scope='Receipt/content and local-seal consistency, not scientific authenticity or wire-transaction count')
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(logical_gets=len(requests), checks=len(checks), failures=report['failures'])))


if __name__ == '__main__':
    main()
