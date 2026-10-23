"""Verify local source/prediction/review continuity, then seal completed phase."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from source import ROOT, OUT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bindings(payload):
    files = payload.get('files', payload.get('sha256', {}))
    if isinstance(files, list):
        return {row['path']: row['sha256'] for row in files}
    if isinstance(files, dict):
        return files
    if isinstance(files, str) and isinstance(payload.get('file'), str):
        return {payload['file']: files}
    raise ValueError('Unsupported seal: do not silently skip evidence')


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists(), 'Never replace final manifest'
    expected_results = [OUT/'method/RESULT_AUDIT.json', OUT/'biology/RESULT_REVIEW.md',
                        OUT/'constructive/RAW_AUDIT.json']
    assert all(path.exists() for path in expected_results), 'Wait for independent audit completion'
    seals = [ROOT/'log/20261023/action_rule_search/VERIFICATION.json',
             ROOT/'log/20261023/observation_law_search/VERIFICATION.json',
             OUT/'PREDICTION_FREEZE.json']
    seals += sorted(path for role in ['method', 'biology', 'constructive']
                    for path in (OUT/role).glob('*SEAL.json'))
    verified = []
    for path in seals:
        files = bindings(json.loads(path.read_text(encoding='utf-8')))
        assert files, path
        for name, expected in files.items():
            bound = Path(name)
            if not bound.is_absolute():
                bound = (path.parent if len(bound.parts) == 1 else ROOT)/bound
            assert digest(bound) == expected, (path, bound)
        verified.append({'seal': path.relative_to(ROOT).as_posix(), 'files': len(files)})
    receipts = sorted(OUT.rglob('*.receipt.json'))
    assert len(receipts) == 15
    for path in receipts:
        receipt = json.loads(path.read_text(encoding='utf-8'))
        body = path.with_name(path.name.removesuffix('.receipt.json'))
        assert receipt['http_status'] == 200 and body.stat().st_size == receipt['bytes']
        assert digest(body) == receipt['sha256'], body
    tree = json.loads((OUT/'tree.json').read_text(encoding='utf-8'))
    objects = {row['path']: row for row in tree['tree'] if row['type'] == 'blob'}
    git_checks = []
    for base in [OUT/'source', OUT/'raw']:
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.name.endswith('.receipt.json'):
                continue
            name = path.relative_to(OUT/'source').as_posix() if base.name == 'source' else 'data/cxcl9_assay/'+path.name
            data = path.read_bytes()
            git_digest = hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
            assert git_digest == objects[name]['sha'], name
            git_checks.append(name)
    assert len(git_checks) == 12
    assert sorted(path.name for path in (OUT/'raw').glob('*.csv')) == [
        f'00_Raw_Data_{name}.csv' for name in ['E3CA', 'E3CB', 'E3DA', 'E3DB']]
    audit = {'status': 'PASS_LOCAL', 'utc': datetime.now(timezone.utc).isoformat(),
             'seals': verified, 'http_receipts': len(receipts), 'git_blob_bindings': git_checks,
             'experiment_reruns': 0,
             'scope': 'Saved data/arithmetic, pinned source and local continuity; no global provenance repair'}
    (OUT/'AUDIT.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    paths = sorted(path for base in [OUT, ROOT/'research/cxcl9_source_feasibility_20261023']
                   for path in base.rglob('*') if path.is_file() and path != target)
    files = {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}
    target.write_text(json.dumps({'files': files, 'scope': 'Current CXCL9 phase only'}, indent=2), encoding='utf-8')
    assert all(digest(ROOT/name) == expected for name, expected in files.items())
    current = {path.relative_to(ROOT).as_posix() for base in [OUT, ROOT/'research/cxcl9_source_feasibility_20261023']
               for path in base.rglob('*') if path.is_file() and path != target}
    assert current == set(files)
    print(json.dumps({'status': 'SEALED_LOCAL', 'files': len(files), 'drift': 0,
                      'unsealed_files': 0, 'verified_seals': len(verified),
                      'http_receipts': len(receipts), 'git_blob_checks': len(git_checks)}))
