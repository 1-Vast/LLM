"""Verify the frozen run, independent numeric agreement and review recovery."""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from prepare import LOG, ROOT, digest, sample_key, write
from preserve import verify


def read(name):
    return json.loads((LOG / name).read_text(encoding='utf-8'))


def main():
    checks = []
    prior = verify()
    checks.append({'name': '1340_prior_files_unchanged', 'passed': prior['passed'] and len(prior['checks']) == 1340})
    checks.append({'name': 'prior_inventory_hashes', 'passed': prior['manifest_sha256'] == read('BASELINE_PRESERVATION.json')['manifest_sha256']})
    for name, expected in read('FREEZE.json')['sha256'].items():
        checks.append({'name': 'freeze:' + name, 'passed': digest(ROOT / name) == expected})
    tests = read('TEST_EXECUTION.json')
    checks.append({'name': '11_synthetic_tests_exit_zero', 'passed': tests['exit_code'] == 0
                   and tests['code_sha256'] == digest(Path(__file__).with_name('run_headroom.py'))
                   and tests['output_sha256'] == digest(LOG / 'TEST_OUTPUT.txt')})
    metadata = read('review/DATA_MANIFEST_AUDIT.json')
    checks.append({'name': '1800_independent_metadata_checks', 'passed': metadata['checks'] == 1800 and not metadata['failures']})
    comparison = read('review/DATA_NUMERIC_COMPARISON.json')
    checks.append({'name': '2792_independent_numeric_checks', 'passed': comparison['checks'] == 2792
                   and not comparison['failures'] and comparison['max_observed_absolute_difference'] < 1e-12
                   and comparison['verified_assay_values'] == 372})
    independent = read('review/DATA_INDEPENDENT_NUMERIC.json')
    checks.append({'name': 'independent_numeric_seal', 'passed': independent['status'] == 'INDEPENDENT_NUMERIC_SEALED_BEFORE_ROOT_COMPARISON'})
    run = read('RUN_RECEIPT.json')
    checks.append({'name': 'unique_main_complete_705_pipeline_580_estimator_fits', 'passed': run['status'] == 'COMPLETE_DEVELOPMENT_HEADROOM_CHECK'
                   and run['ledger']['pipeline_fits'] == 705 and run['ledger']['sklearn_fit_calls'] == 580
                   and run['freeze_sha256'] == digest(LOG / 'FREEZE.json')})
    checks.append({'name': 'no_later_or_control_numeric_casts', 'passed': run['ledger']['later_outcome_values_cast'] == 0
                   and run['ledger']['controls_outcome_values_cast'] == 0})
    manifest = read('MANIFEST.json')
    allowed = {sample_key(sample) for compound in manifest['compounds'] if compound['role'] in ('source', 'development')
               for dose in compound['doses'].values() for sample in dose['samples']}
    projection = read('FUNCTIONAL_PROJECTION.json')
    keys = [tuple(row['key']) for row in projection['records']]
    checks.append({'name': 'exact_186_allowed_records_only', 'passed': len(keys) == len(set(keys)) == len(allowed) == 186
                   and set(keys) == allowed and not projection['invalid']})
    counts = projection['exposure_counters']['finite_numeric_cast_successes']
    checks.append({'name': '372_finite_assay_casts', 'passed': counts == {'DNA(%)': 186, 'LDH(%)': 186}})
    checks.append({'name': '169_finite_out_of_range_records_retained', 'passed': projection['finite_outside_0_100_records_retained'] == 169})
    result = read('HEADROOM_RESULT.json')
    checks.append({'name': 'frozen_gate_preserved', 'passed': result['decision'] == 'GO_ONLY_TO_SEPARATELY_FROZEN_RNA_PILOT'
                   and result['best_development_family'] == 'middle_copy'
                   and abs(result['best_development_dna_mae'] - 0.023357142857142823) < 1e-14
                   and result['absolute_usefulness_gate'] == 0.02
                   and result['relative_usefulness_gate_for_later_pilot'] == 0.1
                   and result['rna_or_world_value_tested'] is False})
    recovery = {
        'review/MECHANISM_POST_RESULT_REVIEW.md': 'fc66e4e69d12635a1ce7b48d745046f2d1b94d9868b06426466df0781c092174',
        'review/SKEPTIC_POST_RESULT_REVIEW.md': '3f8dc4974acc1d61ba4b920c6b172bb2163bd0b45c3929aecaf2794c1fbd66e6'}
    for name, expected in recovery.items():
        checks.append({'name': 'exact_review_recovery:' + name, 'passed': digest(LOG / name) == expected})
    for name in ('review/MECHANISM_POST_RESULT_REPLY.md', 'review/SKEPTIC_POST_RESULT_REPLY.md'):
        checks.append({'name': 'actual_final_reply:' + name, 'passed': (LOG / name).stat().st_size > 500})
    code = Path(__file__).parent
    files = sorted(code.glob('*.py'))
    for path in files:
        ast.parse(path.read_text(encoding='utf-8-sig'))
    diff = subprocess.run(['git', 'diff', '--check', '--', str(code.relative_to(ROOT)), str(LOG.relative_to(ROOT)),
                           'research/REPORT.md', 'log/README.md'], cwd=ROOT, capture_output=True, text=True)
    checks.append({'name': 'scoped_diff_check', 'passed': diff.returncode == 0})
    integrity = {'utc': datetime.now(timezone.utc).isoformat(), 'passed': all(row['passed'] for row in checks),
                 'checks': checks, 'prior_files': 1340, 'python_files_parsed': len(files),
                 'diff_stdout': diff.stdout, 'diff_stderr': diff.stderr}
    write(LOG / 'FINAL_INTEGRITY.json', integrity)
    if not integrity['passed']:
        raise RuntimeError('Final integrity failed')
    paths = sorted(path for directory in (LOG, code) for path in directory.rglob('*') if path.is_file()
                   and path.name != 'FINAL_FILE_INVENTORY.json')
    write(LOG / 'FINAL_FILE_INVENTORY.json', {'utc': datetime.now(timezone.utc).isoformat(), 'files': [
        {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)} for path in paths]})
    print(json.dumps({'passed': integrity['passed'], 'checks': len(checks), 'prior_files': 1340, 'phase_files': len(paths)}))


if __name__ == '__main__':
    main()
