"""Local continuity/source/version checks, not scientific validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261023/feedback_sufficiency_renewal'
checks = []
historical_versions = []


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})


previous = ROOT / 'log/20261023/srs_prefix_qualification/VERIFICATION.json'
for relative, expected in read(previous)['files'].items():
    path = ROOT / relative
    check('predecessor:' + relative, path.exists() and sha(path) == expected)

for role, expected_count in [('root', 6), ('constructive', 4), ('critic', 4)]:
    receipts = list((BASE / role).glob('*.receipt.json'))
    check(role + ':receipt count', len(receipts) == expected_count)
    for path in receipts:
        receipt = read(path)
        name = path.name.removesuffix('.receipt.json')
        body = path.with_name(name)
        if not body.exists():
            body = path.with_name(name + '.body')
        check('receipt:' + str(path.relative_to(BASE)), body.exists()
              and sha(body) == receipt['sha256'] and body.stat().st_size == receipt['bytes'])

code_path = ROOT / 'research/feedback_sufficiency_renewal_20261023/sign_collision.py'
code = code_path.read_text(encoding='utf-8')
old = code.replace("    result_path = OUT / 'SIGN_COLLISION_RESULT.json'\n    if result_path.exists():\n        raise FileExistsError(result_path)\n", '')
old = old.replace('    result_path.write_text(', "    (OUT / 'SIGN_COLLISION_RESULT.json').write_text(")
pre_guard_sha = hashlib.sha256(old.encode()).hexdigest()

for seal_path in BASE.rglob('*SEAL.json'):
    seal = read(seal_path)
    mapping = {seal['path']: seal['sha256']} if 'path' in seal and 'sha256' in seal else seal.get('files', {})
    for relative, expected in mapping.items():
        path = Path(relative)
        if not path.is_absolute():
            path = ROOT / path
        current = path.exists() and sha(path) == expected
        if not current and path == code_path and seal_path.name == 'SIGN_PREFLIGHT_SEAL.json':
            current = pre_guard_sha == expected
            historical_versions.append({'seal': str(seal_path.relative_to(ROOT)),
                                        'reviewed_code_sha256': expected,
                                        'reconstructed_pre_guard_sha256': pre_guard_sha,
                                        'current_code_sha256': sha(code_path),
                                        'change': 'Documented overwrite refusal only; current bytes bound by execution freeze'})
        check('seal:' + str(seal_path.relative_to(BASE)) + ':' + relative, current)

for relative, expected in read(BASE / 'root/SIGN_EXECUTION_FREEZE.json')['files'].items():
    check('execution freeze:' + relative, sha(ROOT / relative) == expected)
check('all six exact result checks', all(read(BASE / 'root/SIGN_COLLISION_RESULT.json')['checks'].values()))
independent = read(BASE / 'constructive/SIGN_RESULT_AUDIT.json')
check('independent audit source binding', independent['source_sha256'] == sha(BASE / 'root/SIGN_COLLISION_RESULT.json'))
check('eleven independent fields match', len(independent['saved_fields_match']) == 11
      and all(independent['saved_fields_match'].values()) and independent['all_pass'])
for relative in ['constructive/CROSS.md', 'constructive/HISTORY_CORRECTION.md',
                 'constructive/RESULT_ADDENDUM.md', 'critic/CROSS.md', 'critic/RESULT_REVIEW.md',
                 'root/PRIMARY_METHOD_ASSESSMENT.md', 'root/CODE_ASSESSMENT.md', 'DECISION.md']:
    check('artifact:' + relative, (BASE / relative).is_file())

files = sorted(p for folder in [BASE, ROOT / 'research/feedback_sufficiency_renewal_20261023']
               for p in folder.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json'
               and '__pycache__' not in p.parts)
report = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Local continuity, source receipt, review version and arithmetic consistency only; not biological validity or completed research goal',
          'checks': checks, 'failures': sum(not x['passed'] for x in checks),
          'historical_review_versions': historical_versions,
          'files': {str(p.relative_to(ROOT)): sha(p) for p in files}}
(BASE / 'VERIFICATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'checks': len(checks), 'failures': report['failures'], 'files': len(files),
                  'historical_review_versions': len(historical_versions)}))
for failure in checks:
    if not failure['passed']:
        print(json.dumps(failure))
raise SystemExit(bool(report['failures']))
