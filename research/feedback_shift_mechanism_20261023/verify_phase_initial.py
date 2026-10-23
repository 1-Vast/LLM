"""Verify bounded receipts, explicit seals, prior snapshot and fixed diagnostics."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261023/feedback_shift_mechanism'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks, network = [], Counter()

    def check(label, name, expected, base=ROOT):
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        actual = sha(path) if path.is_file() else None
        checks.append(dict(binding=label, path=str(path), expected=expected,
                           actual=actual, matches=actual == expected.lower()))

    prior = ROOT / 'log/20261023/organoid_schedule_forecast/VERIFICATION.json'
    for name, digest in json.loads(prior.read_text(encoding='utf-8'))['files'].items():
        check('preceding_snapshot', name, digest)
    for record in sorted(PHASE.rglob('*.json')):
        is_http = record.name.endswith('.receipt.json')
        if not is_http and 'seal' not in record.name.lower() and 'freeze' not in record.name.lower():
            continue
        data = json.loads(record.read_text(encoding='utf-8-sig'))
        if is_http:
            network[(record.parent.name, str(data.get('status', 'NO_STATUS')))] += 1
            if 'sha256' in data:
                check('retained_HTTP_bytes', str(record).replace('.receipt.json', '.body'), data['sha256'])
        files = data.get('files', {})
        if isinstance(files, dict):
            for name, digest in files.items():
                check(record.name, name, digest, ROOT if (ROOT / name).is_file() else record.parent)
        elif isinstance(files, list):
            for item in files:
                check(record.name, item['path'], item['sha256'])
        name = data.get('report') or data.get('artifact') or data.get('path')
        if name and 'sha256' in data:
            check(record.name, name, data['sha256'], ROOT if (ROOT / name).is_file() else record.parent)
    api = json.loads((PHASE / 'api/RECEIPT.json').read_text())
    prompt = (PHASE / 'api/PROMPT.md').read_text(encoding='utf-8')
    checks.append(dict(binding='logical_prompt_universal_newlines',
                       matches=hashlib.sha256(prompt.encode()).hexdigest() == api['prompt_sha256']))
    witness = json.loads((PHASE / 'constructive/MATH_RESULT.json').read_text())
    checks.append(dict(binding='saved_exact_stationary_risk', matches=(
        F(witness['old_unweighted']['query_squared_risk']) == 1 and
        F(witness['expanded_unweighted']['query_squared_risk']) == F(81, 25) and
        F(witness['ordinary_oracle_weighted']['query_squared_risk']) == 0)))
    root_check = json.loads((PHASE / 'root/API_CHECK.json').read_text())
    checks.append(dict(binding='saved_API_arithmetic', matches=(
        F(root_check['same_lawful_inputs_unseen_current_mean10_output']) == 10 and
        F(root_check['same_lawful_inputs_unseen_current_mean20_output']) == 15 and
        F(root_check['beta1_example_output']) == F(29, 2))))
    paths = sorted(set(PHASE.rglob('*')) | set((ROOT / 'research/feedback_shift_mechanism_20261023').rglob('*')))
    snapshot = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                  checks=checks, failures=sum(not x['matches'] for x in checks),
                  http_counts={f'{role}:{status}':n for (role,status),n in sorted(network.items())},
                  provider_usage=api['provider_usage'],
                  scope='Retained bytes, explicit artifact seals and saved math consistency, not experimental truth or historical global provenance repair',
                  goal='ACTIVE / NOT_ACHIEVED')
    target = PHASE / 'VERIFICATION.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), checks=len(checks), failures=report['failures'], http_counts=report['http_counts'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
