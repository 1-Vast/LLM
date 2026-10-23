"""Write-once verification and inventory after reviewers finish this phase."""
import ast
from datetime import datetime, timezone
import json
import subprocess

from prepare import LOG, ROOT, sha, write
from preserve import verify


def main():
    prior = verify()
    checks = [{'name': '984_completed_files_unchanged', 'passed': prior['passed'] and len(prior['checks']) == 984}]
    baseline = json.loads((LOG / 'BASELINE_PRESERVATION.json').read_text(encoding='utf-8'))
    checks.append({'name': 'prior_manifest_hashes_unchanged', 'passed': prior['manifest_sha256'] == baseline['manifest_sha256']})
    freeze = json.loads((LOG / 'COVERAGE_FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        checks.append({'name': 'freeze:' + name, 'passed': sha(ROOT / name) == expected})
    comparison = json.loads((LOG / 'INDEPENDENT_COMPARISON.json').read_text(encoding='utf-8'))
    checks.append({'name': 'independent_exact_counters', 'passed': comparison['passed']
                   and not comparison['mismatches'] and comparison['checks'] > 40000
                   and comparison['root_sha256'] == sha(LOG / 'COVERAGE_RESULT.json')
                   and comparison['independent_sha256'] == sha(LOG / 'skeptic/INDEPENDENT_COVERAGE_RESULT.json')})
    for name in ('TEST_EXECUTION.json', 'COVERAGE_EXECUTION_01.json'):
        execution = json.loads((LOG / name).read_text(encoding='utf-8'))
        checks.append({'name': name, 'passed': execution['exit_code'] == 0})
    tests = json.loads((LOG / 'skeptic/SYNTHETIC_TESTS.json').read_text(encoding='utf-8'))
    checks.append({'name': 'three_independent_synthetic_cases', 'passed': tests['tests_passed'] == 3 and tests['exit_code'] == 0})
    code = ROOT / 'research/prism_profile_opportunity_20261022'
    for path in code.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8-sig'))
    diff = subprocess.run(['git', 'diff', '--check', '--', str(code.relative_to(ROOT)), str(LOG.relative_to(ROOT)),
                           'research/REPORT.md', 'log/README.md'], cwd=ROOT, capture_output=True, text=True)
    checks.append({'name': 'scoped_diff_check', 'passed': diff.returncode == 0})
    passed = all(row['passed'] for row in checks)
    write(LOG / 'FINAL_INTEGRITY.json', {'utc': datetime.now(timezone.utc).isoformat(), 'passed': passed,
          'checks': checks, 'prior_files': 984, 'new_model_fits': 0, 'new_HTTP': 0, 'new_provider_calls': 0,
          'python_files_parse': len(list(code.glob('*.py'))), 'diff_stdout': diff.stdout, 'diff_stderr': diff.stderr})
    if not passed:
        raise RuntimeError('Final integrity failure')
    files = sorted(path for folder in (LOG, code) for path in folder.rglob('*') if path.is_file()
                   and path.name != 'FINAL_FILE_INVENTORY.json')
    write(LOG / 'FINAL_FILE_INVENTORY.json', {'utc': datetime.now(timezone.utc).isoformat(), 'files': [
          {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in files]})
    print(json.dumps({'passed': passed, 'checks': len(checks), 'prior_files': 984, 'phase_files': len(files)}))


if __name__ == '__main__':
    main()
