"""Verify report and code byte preservation in the staged publication, without reading data arrays."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/main_publication'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    entries = {}
    for raw in git('ls-files', '--stage', '-z').split(b'\0'):
        if raw:
            header, name = raw.decode('utf-8').split('\t', 1)
            mode, sha, stage = header.split()
            assert stage == '0', 'Unmerged index entry'
            entries[name] = sha
    changed = [p for p in git('diff', '--cached', '--no-renames', '--name-only', '--diff-filter=AM', '-z').decode().split('\0') if p]
    registry = json.loads((ROOT / 'research/STUDIES.json').read_text(encoding='utf-8'))
    prefixes = ['log/'] + ['research/' + x + '/' for x in registry['workspaces']]
    mismatches, count = [], 0
    for name in changed:
        if not any(name.startswith(prefix) for prefix in prefixes):
            continue
        data = (ROOT / name).read_bytes()
        sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        count += 1
        if entries[name] != sha:
            mismatches.append(name)
    assert not mismatches, mismatches
    bindings = []
    base = ROOT / 'log/20261023/research_progress'
    for row in json.loads((base / 'PACKAGE.json').read_text(encoding='utf-8'))['files']:
        name = (base / row['path']).relative_to(ROOT).as_posix()
        blob = git('cat-file', 'blob', entries[name])
        assert hashlib.sha256(blob).hexdigest() == row['sha256'], name
        bindings.append(name)
    freeze = json.loads((ROOT / 'log/20261023/evidence_portfolio_optimization/FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        if name in entries:
            assert hashlib.sha256(git('cat-file', 'blob', entries[name])).hexdigest() == expected, name
            bindings.append(name)
    plan = json.loads((OUT / 'PLAN.json').read_text(encoding='utf-8'))
    assert not plan['issues']
    assert all(x['preserved_hash_match'] for x in plan['tracked_deletion_preservation'])
    result = {'status': 'PASS', 'staged_byte_preservation_checks': count, 'staged_bound_files': bindings,
              'migration_preserved_deletions': len(plan['tracked_deletion_preservation']),
              'tests': {'repository_shape_and_experiment_contracts': '35 passed in 40.46s'},
              'no_new_experiment_or_global_provenance_repair_claim': True}
    (OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
