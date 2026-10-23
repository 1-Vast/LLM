"""Check retained source bytes, prevalue bindings and prior local snapshot."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261023/rank_reversal_mechanism'
CODE = ROOT/'research/rank_reversal_mechanism_20261023'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks, requests = [], Counter()

    def check(binding, name, expected):
        path = Path(name)
        if not path.is_absolute():
            path = ROOT/path if (ROOT/path).is_file() else LOG/path
        actual = sha(path) if path.is_file() else None
        checks.append(dict(binding=binding, path=str(path), expected=expected,
                           actual=actual, matches=actual == expected.lower()))

    prior = ROOT/'log/20261023/interaction_error_diagnostic/VERIFICATION.json'
    for name, digest in json.loads(prior.read_text())['files'].items():
        check('preceding_local_snapshot', name, digest)
    for record in sorted(LOG.rglob('*.json')):
        data = json.loads(record.read_text(encoding='utf-8-sig'))
        if record.name.endswith('.receipt.json'):
            requests[(record.parent.name, data['status'])] += 1
            check(record.name, str(record).replace('.receipt.json', '.body'), data['sha256'])
        elif record.name == 'FETCH_RECEIPT.json':
            requests[(record.parent.name, data['status'])] += 1
            check(record.name, str(record.parent/'author_decipher_data.py.body'), data['sha256'])
        if 'SEAL' in record.name or record.name == 'ANNOTATION_FREEZE.json':
            entries = data.get('files', data)
            if isinstance(entries, dict):
                for name, digest in entries.items():
                    if isinstance(digest, str) and len(digest) == 64 and ('/' in name or '\\' in name):
                        check(record.name, name, digest)
            for field in ('file', 'report', 'path'):
                if field in data and 'sha256' in data:
                    check(record.name, data[field], data['sha256'])
                    break
    annotation = json.loads((LOG/'FDR_ANNOTATION.json').read_text())
    for name, digest in annotation['bindings'].items():
        check('annotation_binding', name, digest)
    check('annotation_q_binding', str(LOG/'FDR_DEVELOPMENT.npz'), annotation['q_sha256'])
    check('source_saved_audit_seal', str(LOG/'source/RESULT_AUDIT.json'), json.loads(
        (LOG/'source/RESULT_INDEPENDENT_SEAL.json').read_text(encoding='utf-8-sig'))['audit_sha256'])
    paths = sorted([*LOG.rglob('*'), *CODE.rglob('*')])
    report = dict(utc=datetime.now(timezone.utc).isoformat(),
                  files={str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()},
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  http_counts={f'{role}:{status}': n for (role, status), n in sorted(requests.items())},
                  verification_environment=dict(python=platform.python_version(), numpy=np.__version__),
                  git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  scope='Local byte/freeze continuity only; source audit separately checks saved annotation; not historical provenance repair or scientific novelty',
                  goal='ACTIVE / NOT_ACHIEVED')
    target = LOG/'VERIFICATION.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(report['files']), checks=len(checks),
                         failures=report['failures'], http_counts=report['http_counts'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
