"""Verify completed documents and frozen files; inventory without fitting."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/dead_stock_information_gate'
CODE = ROOT / 'research/dead_stock_information_gate_20261022'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})

    previous = load(LOG.parent / 'functional_dynamics_gate/FINAL_FILE_INVENTORY.json')
    for item in previous['files']:
        path = ROOT / item['path']
        check('prior_unchanged:' + item['path'],
              path.stat().st_size == item['bytes'] and digest(path) == item['sha256'])
    freeze = load(LOG / 'hct_gate/PRE_RESPONSE_FREEZE.json')
    for name, sha in freeze['hashes'].items():
        check('gate_frozen:' + name, digest(ROOT / name) == sha)
    diagnostic = load(LOG / 'data_auditor/target_failure_audit/DIAGNOSTIC.json')
    check('diagnostic_frozen_unchanged', diagnostic['all_frozen_unchanged'])
    check('four_negative_values_two_wells', diagnostic['invalid_record_count'] == 4
          and diagnostic['affected_well_count'] == 2)
    check('no_gate_scores', not (LOG / 'hct_gate/RESULT.json').exists()
          and not list((LOG / 'hct_gate').glob('FOLD_*.json')))
    for name in ['advocate/POST_FAILURE.md', 'advocate/POST_FAILURE_RAW.md',
                 'skeptic/POST_FAILURE_CROSS.md',
                 'data_auditor/target_failure_audit/REPORT.md',
                 'data_auditor/target_failure_audit/POST_FAILURE_CROSS.md']:
        check('final_review:' + name, (LOG / name).is_file())
    decision = LOG / 'DECISION.md'
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', decision.read_text(encoding='utf-8')):
        check('decision_link:' + target, (decision.parent / target).is_file())
    for name, target in [('research/REPORT.md', '../log/20261022/dead_stock_information_gate/DECISION.md'),
                         ('log/README.md', '20261022/dead_stock_information_gate/DECISION.md')]:
        check('navigation:' + name, target in (ROOT / name).read_text(encoding='utf-8'))
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'all_pass': all(item['pass'] for item in checks),
              'check_count': len(checks), 'fits': 0, 'future_array_reads': 0,
              'goal_status': 'ACTIVE_NOT_ACHIEVED'}
    with (LOG / 'FINALIZATION.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    inventory = LOG / 'FINAL_FILE_INVENTORY.json'
    files = []
    for folder in [LOG, CODE]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path != inventory:
                files.append({'path': path.relative_to(ROOT).as_posix(),
                              'bytes': path.stat().st_size, 'sha256': digest(path)})
    with inventory.open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
                   'excluded': ['this inventory', 'mutable navigation indexes']},
                  stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'all_pass': report['all_pass'], 'checks': len(checks),
                      'inventoried_files': len(files), 'prior_files': len(previous['files'])}))
    return 0 if report['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
