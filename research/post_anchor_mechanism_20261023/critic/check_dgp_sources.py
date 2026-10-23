"""Static byte provenance checks only; never imports foreign model code."""
from pathlib import Path
import hashlib
import json

root = Path('D:/MAESTRO/log/20261023/post_anchor_mechanism')
src = root/'root_sources'
tree = json.loads((src/'dgp_tree.body').read_text())
entries = {x['path']:x for x in tree['tree']}
assert not tree['truncated']
checks = []
for label,path in [('dgp_model','src/dgpla/model.py'),('dgp_prior','src/dgpla/prior.py'),('dgp_repro','docs/REPRODUCIBILITY.md')]:
    blob = (src/(label+'.body')).read_bytes()
    receipt = json.loads((src/(label+'.receipt.json')).read_text())
    sha256 = hashlib.sha256(blob).hexdigest()
    git_hash = hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\x00'+blob).hexdigest()
    assert sha256 == receipt['sha256']
    assert git_hash == entries[path]['sha']
    assert len(blob) == entries[path]['size']
    checks.append({'label':label,'path':path,'bytes':len(blob),'sha256':sha256,'git_blob_sha1':git_hash,'pass':True})
output = {'scope':'static source identity only; foreign code not executed/imported',
          'tree_revision':tree['sha'],'tree_truncated':tree['truncated'],'checks':checks}
(root/'critic/DGP_SOURCE_CHECK.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
print(json.dumps(output,indent=2))
