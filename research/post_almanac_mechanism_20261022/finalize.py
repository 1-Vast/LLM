"""Final local bindings and predecessor preservation for this research phase."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/post_almanac_mechanism'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    out = PHASE / 'FINAL_BINDINGS.json'
    assert not out.exists()
    old = json.loads((ROOT / 'log/20261022/almanac_feedback_pilot/root/FINAL_BINDINGS.json').read_text())
    drift = [rel for rel, expected in old['bindings'].items() if sha(ROOT / rel) != expected]
    assert not drift, drift
    for role in ('biology', 'skeptic', 'frontier'):
        assert (PHASE / role / 'INDEPENDENT.md').exists()
    assert (PHASE / 'skeptic/OFFICIAL_CODE_CROSS.md').exists()
    assert (PHASE / 'biology/CROSS_API.md').exists()
    code_dirs = [ROOT / 'research' / name for name in ('post_almanac_mechanism_20261022',
        'post_almanac_frontier_20261022', 'post_almanac_biology_20261022', 'post_almanac_skeptic_20261022')]
    files = [p for base in [PHASE] + code_dirs for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    bindings = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}
    out.write_text(json.dumps({'scope': 'local phase only; not scientific novelty or global provenance',
        'bindings': bindings, 'file_count': len(bindings), 'predecessor_files_verified': len(old['bindings'])}, indent=2), encoding='utf-8')
    assert all(sha(ROOT / rel) == expected for rel, expected in bindings.items())
    verify = {'status': 'PASS', 'phase_files_verified': len(bindings),
              'almanac_predecessor_files_verified': len(old['bindings']), 'scope': 'local bindings and predecessor preservation only'}
    (PHASE / 'VERIFICATION.json').write_text(json.dumps(verify, indent=2), encoding='utf-8')
    print(json.dumps(verify))


if __name__ == '__main__':
    main()
