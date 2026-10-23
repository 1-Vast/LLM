"""Verify phase inputs and preserve a local, explicitly bounded evidence manifest."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/revision_value_operation'
FUNCTION = ROOT / 'log/20261022/cdk_functional_increment'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((FUNCTION / 'FREEZE.json').read_text())
    checks = {p: digest(ROOT / p) == value for p, value in freeze['files'].items()}
    assert all(checks.values()), checks
    audit = json.loads((FUNCTION / 'audit/NUMERICAL_AUDIT.json').read_text())
    assert audit['status'] == 'PASS' and audit['prediction_rows_checked'] == 42
    assert audit['maximum_prediction_difference'] < 1e-12
    summary = json.loads((FUNCTION / 'SUMMARY.json').read_text())
    assert summary['challenge']['palbociclib']['gate'] == 'NOT_ESTIMABLE'
    assert summary['challenge']['abemaciclib']['gate'] == 'FAILED'
    for role in ('frontier', 'biology'):
        for name in ('INDEPENDENT.md', 'CROSS.md', 'RESULT_REVIEW.md', 'RESULT_CROSS.md'):
            assert (PHASE / role / name).is_file(), (role, name)
    predecessors = {}
    for previous in ('post_almanac_mechanism', 'cdk_middle_feedback'):
        old = json.loads((ROOT / f'log/20261022/{previous}/FINAL_BINDINGS.json').read_text())
        bad = [p for p, value in old['bindings'].items() if not (ROOT / p).is_file() or digest(ROOT / p) != value]
        predecessors[previous] = {'checked': len(old['bindings']), 'mismatches': bad}
    roots = [PHASE, FUNCTION, ROOT / 'research/revision_value_operation_20261022',
             ROOT / 'research/cdk_functional_increment_20261022']
    excluded = {'FINAL_BINDINGS.json', 'VERIFICATION.json'}
    bindings = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p)
                for folder in roots for p in sorted(folder.rglob('*'))
                if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
    (PHASE / 'FINAL_BINDINGS.json').write_text(json.dumps({
        'scope': 'Local two phases only, not scientific success or global provenance', 'bindings': bindings}, indent=2), encoding='utf-8')
    assert all(digest(ROOT / p) == value for p, value in bindings.items())
    verification = {'status': 'PASS_CURRENT_PHASE', 'bound_files': len(bindings),
                    'pre_outcome_input_checks': checks, 'predecessor_checks': predecessors,
                    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    'src_tools_diff': subprocess.check_output(['git', 'diff', '--stat', '--', 'src', 'tools'], cwd=ROOT, text=True),
                    'full_goal': 'ACTIVE_NOT_ACHIEVED', 'global_provenance': 'NOT_REPAIRED_BY_LOCAL_CHECK'}
    (PHASE / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    print(json.dumps({'status': verification['status'], 'bound_files': len(bindings),
                      'predecessors': predecessors, 'full_goal': verification['full_goal']}, indent=2))


if __name__ == '__main__':
    main()
