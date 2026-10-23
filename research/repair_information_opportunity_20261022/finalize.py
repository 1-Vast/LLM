"""Verify this phase's bindings only; never repeat scientific computations."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/repair_information_opportunity'
CODE = [Path(__file__).parent, ROOT / 'research/repair_information_source_20261022']


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def bound(name, expected, parent=LOG):
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path if path.parts[0] in ('log', 'research') else parent / path
        check('binding:' + path.relative_to(ROOT).as_posix(), path.is_file() and sha(path) == expected.lower())

    def walk(value, parent):
        if isinstance(value, dict):
            if 'sha256' in value:
                for key in ('path', 'file', 'audit', 'code'):
                    if isinstance(value.get(key), str):
                        bound(value[key], value['sha256'], parent)
                        break
            for key in ('files', 'source_sha256'):
                mapped = value.get(key)
                if isinstance(mapped, dict):
                    for name, digest in mapped.items():
                        if isinstance(digest, str) and len(digest) == 64:
                            bound(name, digest, parent)
            for child in value.values():
                walk(child, parent)
        elif isinstance(value, list):
            for child in value:
                walk(child, parent)

    for path in sorted(LOG.rglob('*SEAL.json')):
        walk(load(path), path.parent)
    walk(load(LOG / 'FREEZE.json'), LOG)
    result = load(LOG / 'UPPER_BOUND_RESULT.json')
    bound('UPPER_BOUND_PROTOCOL.md', result['protocol_sha256'])
    bound('FREEZE.json', result['freeze_sha256'])
    bound('research/repair_information_opportunity_20261022/upper_bound.py', result['code_sha256'])
    match = load(LOG / 'INDEPENDENT_MATCH.json')
    bound('UPPER_BOUND_RESULT.json', match['primary_sha256'])
    bound('INDEPENDENT_RECOMPUTE.json', match['independent_sha256'])
    bound('research/repair_information_opportunity_20261022/compare_independent.py', match['comparison_code_sha256'])
    check('three_tables_twelve_menus_independent_match', match['matched']
          and match['matched_tables'] == 3 and match['matched_menus'] == 12)
    check('primary_opportunity_failed', result['primary_B1_fallback_room'] is False
          and result['primary_all_saved_room'] is False)
    check('recorded_no_fits_or_old_update_reruns', result['biological_predictor_fits'] == 0
          and result['old_updates_rerun'] == 0 and result['router_fits'] == 0)
    for row in load(LOG / 'CACHED_TABLE_IDENTITIES.json'):
        bound(row['path'], row['sha256'])
    receipts = sorted((LOG / 'source').rglob('request_*.receipt.json'))
    check('five_exact_source_requests', len(receipts) == 5)
    retained = 0
    capped = 0
    for path in receipts:
        row = load(path)
        body = path.with_name(path.name.replace('.receipt.json', '.body'))
        bound(body.relative_to(ROOT).as_posix(), row['sha256'])
        check('receipt_bytes:' + path.name, body.stat().st_size == row['bytes'] and row['status'] == 200)
        retained += row['bytes']
        capped += bool(row.get('body_capped'))
    check('source_retained_bytes_and_partial_status', retained == 1055214 and capped == 1)
    listing = load(LOG / 'source/list_followup/request_2_list.body')
    check('actual_list_metadata_only', listing['code'] == 200 and len(listing['data']) == 3
          and all(group['requireApproval'] is True for group in listing['data']))
    for folder in CODE:
        for path in folder.glob('*.py'):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            check('python_parse:' + path.relative_to(ROOT).as_posix(), True)
    for name in ('DECISION.md', 'CONTINUATION.md', 'CROSS_DECISION.md', 'RECURSION_CROSSCHECK.md'):
        check('required:' + name, (LOG / name).is_file())
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, text=True, capture_output=True)
    check('git_diff_check', diff.returncode == 0)
    files = [{'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
              'sha256': sha(path)} for folder in [LOG] + CODE
             for path in sorted(folder.rglob('*')) if path.is_file() and '__pycache__' not in path.parts]
    record = {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'files': files, 'excludes_itself': True,
              'scope': 'This phase and explicitly listed historical inputs only; not all predecessor bytes',
              'legacy_three_response_drift': 'Unresolved, recorded in next_mechanism/root/FINALIZATION_LIMITATION.md',
              'old_scientific_experiments_rerun_by_finalizer': 0,
              'scientific_performance_success': False, 'full_goal': 'ACTIVE / NOT_ACHIEVED',
              'direct_deepseek_calls': 0, 'native_usage_and_cost': 'NOT_EXPOSED',
              'source_requests': 5, 'retained_body_bytes': retained, 'incomplete_bodies': capped}
    with (LOG / 'FINAL_BINDINGS.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps({'passed': True, 'binding_checks': len(checks), 'files': len(files),
                      'full_goal_complete': False}))


if __name__ == '__main__':
    main()
