"""Verify inherited-update phase bindings and predecessor continuity, then seal."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/inherited_update_renewal'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists()
    seals = [ROOT/'log/20261023/cxcl9_source_feasibility/VERIFICATION.json',
             ROOT/'log/20261023/action_rule_search/VERIFICATION.json',
             OUT/'API_CHECK_FREEZE.json']
    seals += sorted(path for role in ['biology', 'constructive', 'frontier']
                    for path in (OUT/role).glob('*SEAL.json'))
    verified = []
    resolutions = []
    for seal in seals:
        payload = json.loads(seal.read_text(encoding='utf-8'))
        files = payload.get('files')
        if isinstance(files, list):
            files = {row['path']: row['sha256'] for row in files}
        assert isinstance(files, dict) and files, seal
        for name, expected in files.items():
            path = Path(name)
            if not path.is_absolute():
                path = (seal.parent if len(path.parts) == 1 else ROOT)/path
            if digest(path) != expected:
                snapshot = OUT/'constructive/CROSS_APPENDED_SNAPSHOT.md'
                assert path == OUT/'constructive/CROSS.md' and snapshot.exists(), (seal, path)
                assert digest(snapshot) == expected, (seal, path, snapshot)
                resolutions.append({'seal': seal.relative_to(ROOT).as_posix(),
                                    'original_path': path.relative_to(ROOT).as_posix(),
                                    'expected': expected,
                                    'verified_snapshot': snapshot.relative_to(ROOT).as_posix()})
        verified.append({'seal': seal.relative_to(ROOT).as_posix(), 'files': len(files)})
    result = json.loads((OUT/'API_CHECK.json').read_text(encoding='utf-8'))
    assert result['same_history_toy']['proposed'] == result['same_history_toy']['ordinary_rank_one_gaussian']
    assert F(result['finite_control_check']['finite_control_increment']['exact']) == F(1,16)
    assert F(result['coordinate_check']['difference']['exact']) == F(999999,1000001)
    report = json.loads((OUT/'frontier/RESULT_AUDIT.json').read_text(encoding='utf-8'))
    assert report, 'Independent numerical audit required'
    audit = {'status': 'PASS_LOCAL', 'utc': datetime.now(timezone.utc).isoformat(),
             'seals': verified, 'experiment_reruns': 0,
             'historical_version_resolutions': resolutions,
             'scope': 'Local saved arithmetic and continuity; no biological or global provenance verification'}
    (OUT/'AUDIT.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    paths = sorted(path for base in [OUT, ROOT/'research/inherited_update_renewal_20261023']
                   for path in base.rglob('*') if path.is_file() and path != target)
    files = {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}
    target.write_text(json.dumps({'files': files, 'scope': 'Inherited update phase only'}, indent=2), encoding='utf-8')
    assert all(digest(ROOT/name) == expected for name, expected in files.items())
    current = {path.relative_to(ROOT).as_posix() for base in [OUT, ROOT/'research/inherited_update_renewal_20261023']
               for path in base.rglob('*') if path.is_file() and path != target}
    assert current == set(files)
    print(json.dumps({'status': 'SEALED_LOCAL', 'files': len(files), 'drift': 0,
                      'unsealed_files': 0, 'verified_seals': len(verified)}))
