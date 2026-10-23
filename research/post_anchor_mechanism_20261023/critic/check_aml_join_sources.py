"""Byte-only provenance audit; no raw lineage records or foreign execution."""
from pathlib import Path
import hashlib
import json

base = Path('D:/MAESTRO/log/20261023/post_anchor_mechanism')
source = base/'root_sources'
tree = json.loads((source/'aml_tree.body').read_text())
assert tree['sha'] == '3d5ef9070a259fb902feccbc5948f10e6a9d44ae'
assert not tree['truncated']
entries = {x['path']:x for x in tree['tree']}
checks = []
for name in ['1_LineagePreprocessing','2_TagClustering','AML_lineage_utilities']:
    label = 'aml_join_'+name
    blob = (source/(label+'.body')).read_bytes()
    receipt = json.loads((source/(label+'.receipt.json')).read_text())
    digest = hashlib.sha256(blob).hexdigest()
    git_hash = hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\x00'+blob).hexdigest()
    entry = entries['python_scripts/'+name+'.py']
    assert digest == receipt['sha256']
    assert git_hash == entry['sha'] == receipt['git_blob_sha1']
    assert len(blob) == entry['size'] == receipt['bytes']
    checks.append({'path':entry['path'],'sha256':digest,'git_blob_sha1':git_hash,'bytes':len(blob),'pass':True})
(base/'critic/AML_JOIN_SOURCE_CHECK.json').write_text(json.dumps({'revision':tree['sha'],'scope':'static source identity only','checks':checks},indent=2),encoding='utf-8')
print('PASS: 3 SHA256, Git blob hashes and byte sizes')
