"""Check retained sources, explicit seals and preceding local snapshot."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261023/response_law_revision'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks, network = [], Counter()

    def check(binding, name, expected):
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path if (ROOT / path).is_file() else PHASE / path
        actual = sha(path) if path.is_file() else None
        checks.append(dict(binding=binding, path=str(path), expected=expected,
                           actual=actual, matches=actual == expected.lower()))

    prior = ROOT / 'log/20261023/decision_probe_mechanism/VERIFICATION.json'
    for name, digest in json.loads(prior.read_text(encoding='utf-8'))['files'].items():
        check('preceding_local_snapshot', name, digest)
    for record in sorted(PHASE.rglob('*.json')):
        data = json.loads(record.read_text(encoding='utf-8-sig'))
        if record.name.endswith('.receipt.json'):
            network[(record.parent.name, str(data['status']))] += 1
            check(record.name, str(record).replace('.receipt.json', '.body'), data['sha256'])
        elif 'seal' in record.name.lower() or 'freeze' in record.name.lower():
            files = data.get('files', data)
            if isinstance(files, dict):
                for name, digest in files.items():
                    if isinstance(digest, str) and len(digest) == 64 and '/' in name:
                        check(record.name, name, digest)
            if 'report' in data and 'sha256' in data:
                check(record.name, data['report'], data['sha256'])
    witness = json.loads((PHASE / 'root/GATE_RESULT.json').read_text())
    check('root_gate_code', 'research/response_law_revision_20261023/gate_check.py', witness['code_sha256'])
    api = json.loads((PHASE / 'api/RECEIPT.json').read_text())
    prompt = (PHASE / 'api/PROMPT.md').read_text(encoding='utf-8')
    checks.append(dict(binding='logical_API_prompt_universal_newlines', matches=(
        hashlib.sha256(prompt.encode()).hexdigest() == api['prompt_sha256'])))
    paths = sorted(list(PHASE.rglob('*')) + list((ROOT / 'research/response_law_revision_20261023').rglob('*')))
    snapshot = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  http_counts={f'{role}:{status}': n for (role, status), n in sorted(network.items())},
                  provider_usage=api['provider_usage'],
                  scope='Local retained-byte continuity, not scientific truth, secure blinding or historical provenance repair',
                  goal='ACTIVE / NOT_ACHIEVED')
    target = PHASE / 'VERIFICATION.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), checks=len(checks), failures=report['failures'], http_counts=report['http_counts'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())

