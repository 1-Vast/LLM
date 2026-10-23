"""Check declared local seals and bind this phase without a global integrity claim."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(1024 * 1024):
            sha.update(block)
    return sha.hexdigest()


def entries(record):
    if isinstance(record, dict):
        if isinstance(record.get('sha256'), str):
            path = record.get('path', record.get('file'))
            if isinstance(path, str):
                yield path, record['sha256']
        for key, value in record.items():
            if isinstance(value, str) and len(value) == 64 and (key.startswith('log/') or key.startswith('research/')):
                yield key, value
            elif isinstance(value, dict) and 'sha256' in value and (key.startswith('log/') or key.startswith('research/')):
                yield key, value['sha256']
            elif isinstance(value, (dict, list)):
                yield from entries(value)
    elif isinstance(record, list):
        for item in record:
            yield from entries(item)


def main():
    manifests = [p for p in OUT.rglob('*.json') if 'seal' in p.name.lower() or p.name in ('FREEZE.json', 'BINDINGS.json')]
    manifests.append(ROOT / 'log/20261022/decrypte_source_qualification/FINAL_BINDINGS.json')
    checks = 0
    for manifest in manifests:
        for name, expected in entries(json.loads(manifest.read_text(encoding='utf-8-sig'))):
            assert digest(ROOT / name) == expected, (str(manifest), name)
            checks += 1
    dirs = [OUT]
    dirs.extend(p for p in (ROOT / 'research').glob('decrypte_*_20261022') if p.name != 'decrypte_source_qualification_20261022')
    files = sorted({p for directory in dirs for p in directory.rglob('*') if p.is_file() and p.name != 'FINAL_BINDINGS.json'})
    result = {'scope': 'Current phase and listed research directories; previous qualification checked; no global provenance claim',
              'verified_local_manifest_entries': checks, 'manifest_count': len(manifests),
              'files': {str(p.relative_to(ROOT)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files}}
    (OUT / 'FINAL_BINDINGS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'verified_manifest_entries': checks, 'manifests': len(manifests), 'bound_files': len(files), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
