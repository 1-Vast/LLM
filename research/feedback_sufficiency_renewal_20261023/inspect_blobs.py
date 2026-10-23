"""Decode author code solely as source evidence; never import or execute it."""
import base64
import hashlib
import json
from retrieve import OUT

report = []
for name in ['metadrp_train', 'metadrp_optimizer']:
    data = json.loads((OUT / (name + '_blob.json')).read_text(encoding='utf-8'))
    raw = base64.b64decode(data['content'])
    blob_sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert blob_sha == data['sha'] and len(raw) == data['size']
    (OUT / (name + '_source.txt')).write_bytes(raw)
    report.append({'name': name, 'git_blob_sha1': blob_sha, 'sha256': hashlib.sha256(raw).hexdigest(),
                   'bytes': len(raw), 'scope': 'Source evidence only; no execution'})
(OUT / 'CODE_BINDING.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
