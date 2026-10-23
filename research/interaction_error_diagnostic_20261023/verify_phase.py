"""Check retained bytes and frozen/result bindings, not scientific novelty."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261023/interaction_error_diagnostic'
CODE = ROOT/'research/interaction_error_diagnostic_20261023'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(binding, name, expected):
        p = Path(name)
        if not p.is_absolute():
            p = ROOT/p if (ROOT/p).is_file() else LOG/p
        actual = sha(p) if p.is_file() else None
        checks.append(dict(binding=binding, path=str(p), expected=expected,
                           actual=actual, matches=actual == expected.lower()))

    previous = ROOT/'log/20261023/cross_context_interaction/VERIFICATION.json'
    for name, digest in json.loads(previous.read_text())['files'].items():
        check('preceding_local_snapshot', name, digest)
    for record in sorted(LOG.rglob('*.json')):
        if 'SEAL' not in record.name and record.name != 'RUN_FREEZE.json':
            continue
        data = json.loads(record.read_text(encoding='utf-8-sig'))
        entries = data.get('files', data)
        if isinstance(entries, dict):
            for name, digest in entries.items():
                if isinstance(digest, str) and len(digest) == 64 and ('/' in name or '\\' in name):
                    check(record.name, name, digest)
        for field in ('file', 'report', 'path'):
            if field in data and 'sha256' in data:
                check(record.name, data[field], data['sha256'])
                break
    results = json.loads((LOG/'RESULTS.json').read_text())
    for name, field in [('PREDICTIONS.npz', 'prediction_sha256'), ('PAIR_IDS.json', 'pair_ids_sha256'),
                        ('PLAN.md', 'plan_sha256'), ('AMENDMENT_BEFORE_VALUES.md', 'amendment_sha256')]:
        check('result_binding', str(LOG/name), results[field])
    check('result_binding', str(CODE/'run.py'), results['code_sha256'])
    paths = sorted([*LOG.rglob('*'), *CODE.rglob('*')])
    snapshot = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  scope='Local byte/freeze consistency only; numerical audit is separately retained; no historical provenance repair',
                  goal='ACTIVE / NOT_ACHIEVED')
    target = LOG/'VERIFICATION.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), checks=len(checks), failures=report['failures'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
