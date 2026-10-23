"""Acquire the one authenticated pseudobulk artifact; inspect schema, never values."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import h5py
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function'
manifest = json.loads((OUT / 'root_sources/FIGSHARE_PROCESSED_MANIFEST.json').read_text(encoding='utf-8'))
entry = next(item for item in manifest['files'] if item['id'] == 35774443)
target = OUT / 'data' / entry['name']
target.parent.mkdir(exist_ok=True)
assert not target.exists()
started = time.monotonic()
with requests.get(entry['download_url'], timeout=(30, 45), stream=True) as response:
    receipt = {'url': entry['download_url'], 'status': response.status_code,
               'utc': datetime.now(timezone.utc).isoformat(), 'expected_bytes': entry['size']}
    (OUT / 'data/DOWNLOAD_STARTED.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    response.raise_for_status()
    with target.open('xb') as stream:
        for chunk in response.iter_content(1024 * 1024):
            stream.write(chunk)
            assert stream.tell() <= entry['size']
md5, sha256 = hashlib.md5(), hashlib.sha256()
with target.open('rb') as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        md5.update(chunk)
        sha256.update(chunk)
receipt.update(bytes=target.stat().st_size, md5=md5.hexdigest(), sha256=sha256.hexdigest(),
               seconds=time.monotonic() - started)
(OUT / 'data/DOWNLOAD_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
assert receipt['bytes'] == entry['size']
assert receipt['md5'] == entry['computed_md5']
schema = []
with h5py.File(target, 'r') as handle:
    def inspect(name, node):
        if isinstance(node, h5py.Dataset):
            schema.append({'path': name, 'shape': node.shape, 'dtype': str(node.dtype)})
    handle.visititems(inspect)
(OUT / 'data/HDF5_SCHEMA.json').write_text(json.dumps(schema, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
print(json.dumps(schema, indent=2))
