"""Bind only this molecular phase and its corrected scientific evidence."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/decrypte_molecular_increment'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = PHASE / 'FINAL_BINDINGS.json'
    assert not target.exists()
    for name in ('FREEZE.json', 'key_correction/FREEZE.json'):
        for relative, expected in json.loads((PHASE / name).read_text(encoding='utf-8'))['files'].items():
            assert sha(ROOT / relative) == expected, relative
    audit = json.loads((PHASE / 'assay/KEY_CORRECTED_RESULT_AUDIT.json').read_text(encoding='utf-8'))
    assert audit['status'] == 'PASS' and not audit['joint_advance']
    assert not json.loads((PHASE / 'key_correction/JOINT_GATE.json').read_text(encoding='utf-8'))['advance']
    for name in ('review/RESULT_CROSS.md', 'assay/CROSS_RESULT.md'):
        assert (PHASE / name).exists(), name
    paths = [p for p in PHASE.rglob('*') if p.is_file()]
    for directory in ('decrypte_molecular_increment_20261022',
                      'decrypte_molecular_key_correction_20261022',
                      'decrypte_molecular_increment_audit_20261022',
                      'decrypte_molecular_audit_20261022',
                      'decrypte_molecular_download_20261022'):
        paths += [p for p in (ROOT / 'research' / directory).rglob('*.py')]
    result = {'utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Molecular incremental phase only; historical drift unresolved; not global integrity',
              'decision': 'STOP_EXACT_HIGH_DOSE_MOLECULAR_INCREMENT; FULL_OBJECTIVE_NOT_ACHIEVED',
              'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    assert all(sha(ROOT / p) == h for p, h in result['files'].items())
    print(json.dumps({'bound_files': len(result['files']), 'verification': 'PASS'}))


if __name__ == '__main__':
    main()
