"""Acquire two pinned MAT files, inspect variable names/shapes only."""
import base64
import hashlib
import json

from scipy.io import whosmat

import root_search as scout


def main():
    manifest = json.loads((scout.OUT/'RESPONSE_DYNAMICS_MANIFEST.json').read_text())
    entries = {e['path']: e for e in manifest['entries']}
    records = []
    for fig in (2, 4):
        name = f'Figure {fig}/data.mat'
        e = entries[name]
        receipt, raw = scout.get(f'response_mat_{fig}', e['url'], cap=1_100_000)
        if receipt.get('status') != 200 or 'error_type' in receipt:
            print('RESPONSE_MAT_ACCESS_FAILURE_RETAINED')
            return 1
        blob = json.loads(raw)
        content = base64.b64decode(blob['content'])
        actual = hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
        if actual != e['sha'] or actual != blob['sha'] or len(content) != e['size']:
            raise ValueError('git_blob_mismatch')
        target = scout.OUT/f'RESPONSE_Figure{fig}_data.raw.mat'
        with target.open('xb') as f:
            f.write(content)
        schema = [{'variable': n, 'shape': s, 'matlab_type': t} for n, s, t in whosmat(target)]
        records.append({'path': name, 'local_path': str(target), 'size': len(content),
            'git_blob_sha1': actual, 'sha256': hashlib.sha256(content).hexdigest(),
            'schema': schema, 'values_interpreted': False})
    scout.write(scout.OUT/'RESPONSE_DYNAMICS_SCHEMA.json', records)
    print(json.dumps(records, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
