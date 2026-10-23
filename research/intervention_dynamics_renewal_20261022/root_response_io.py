"""Authenticate five author-code/design blobs; do not execute them."""
import base64
import hashlib
import json
from pathlib import Path

import root_search as scout

PATHS = ['Figure 2/readme', 'Figure 2/Fig2CDE.m', 'Figure 4/readme',
         'Figure 4/Fig4A.m', 'Figure 4/Fig4BCD.m']


def main():
    manifest = json.loads((scout.OUT/'RESPONSE_DYNAMICS_MANIFEST.json').read_text())
    entries = {e['path']: e for e in manifest['entries']}
    code_out = Path(__file__).resolve().parent/'response_published_code'
    code_out.mkdir(exist_ok=True)
    records = []
    for i, name in enumerate(PATHS, 1):
        e = entries[name]
        receipt, raw = scout.get(f'response_io_{i}', e['url'], cap=50_000)
        if receipt.get('status') != 200 or 'error_type' in receipt:
            print('RESPONSE_CODE_ACCESS_FAILURE_RETAINED')
            return 1
        blob = json.loads(raw)
        content = base64.b64decode(blob['content'], validate=False)
        actual = hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
        if actual != e['sha'] or blob['sha'] != actual or len(content) != e['size']:
            raise ValueError('git_blob_mismatch')
        local = (code_out/f'Figure{name[7]}_{Path(name).name}') if name.endswith('.m') else (
            scout.OUT/f'RESPONSE_Figure{name[7]}_readme.txt')
        with local.open('xb') as f:
            f.write(content)
        records.append({'path': name, 'size': len(content), 'git_blob_sha1': actual,
            'sha256': hashlib.sha256(content).hexdigest(), 'local_path': str(local)})
        print(json.dumps({'path': name, 'source': content.decode('utf-8-sig')}, ensure_ascii=False))
    scout.write(scout.OUT/'RESPONSE_DYNAMICS_IO.json', records)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
