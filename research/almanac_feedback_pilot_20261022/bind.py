"""Append-only local bindings for the response freeze and final phase artifacts."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/almanac_feedback_pilot'
CODE = ROOT / 'research/almanac_feedback_pilot_20261022'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    before = sys.argv[1] == 'before'
    output = PHASE / 'root' / ('PRE_RESPONSE_FREEZE.json' if before else 'FINAL_BINDINGS.json')
    assert not output.exists()
    if before:
        for role in ('assay', 'skeptic'):
            for name in ('INDEPENDENT.md', 'CROSS.md', 'PROTOCOL_REVIEW.md', 'IMPLEMENTATION_REVIEW.md'):
                assert (PHASE / role / name).exists(), (role, name)
        assert json.loads((PHASE / 'root/SYNTHETIC_TESTS.json').read_text())['status'] == 'PASS'
        assert not (PHASE / 'root/VALUES.npz').exists()
    paths = [p for base in (CODE, PHASE) for p in base.rglob('*') if p.is_file()]
    if before:
        old = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'
        paths += [old / 'archive.zip', old / 'ELIGIBLE_DESIGN_ROWS.json']
    bindings = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    result = {'scope': 'local phase bindings only; does not repair historical provenance drift',
              'stage': 'before any authorized numerical decoding' if before else 'after results and reviews',
              'file_count': len(bindings), 'bindings': bindings}
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert all(sha(ROOT / rel) == digest for rel, digest in bindings.items())
    print(json.dumps({'status': 'PASS', 'stage': result['stage'], 'file_count': len(bindings)}))


if __name__ == '__main__':
    main()
