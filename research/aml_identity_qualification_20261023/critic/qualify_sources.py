"""Metadata-only audit; foreign code is never imported or executed."""
import datetime
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/aml_identity_qualification/critic'
OLD = ROOT / 'log/20261023/post_anchor_mechanism/root_sources'

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

body = (OLD / 'aml_samples.body').read_bytes()
assert hashlib.sha256(body).hexdigest() == '8545602f3dd82e41836e7a8e34d7a8cbb82e6a5c715d3321eb68b4f15174e9c3'
metadata = []
for number, line in enumerate(body.decode('utf-8').splitlines(), 1):
    if line.startswith(('^SAMPLE', '!Sample_')) and not line.startswith('!Sample_table'):
        metadata.append({'line': number, 'text': line})
write_json(OUT / 'SAMPLE_METADATA.json', metadata)

def fetch(name, url):
    req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-qualification', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
        receipt = {'requested_url': url, 'final_url': response.url, 'status': response.status,
                   'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'headers': dict(response.headers)}
    (OUT / (name + '.body')).write_bytes(data)
    write_json(OUT / (name + '.receipt.json'), receipt)
    return data

tree = json.loads(fetch('singlecelllineage_tree', 'https://api.github.com/repos/mckennalab/SingleCellLineage/git/trees/HEAD?recursive=1'))
assert not tree['truncated']
paths = [x['path'] for x in tree['tree']]
readme = next(p for p in paths if p.lower() == 'readme.md')
readme_body = fetch('singlecelllineage_readme', 'https://raw.githubusercontent.com/mckennalab/SingleCellLineage/' + tree['sha'] + '/' + readme)
expected = next(x['sha'] for x in tree['tree'] if x['path'] == readme)
actual = hashlib.sha1(b'blob ' + str(len(readme_body)).encode() + b'\0' + readme_body).hexdigest()
assert actual == expected
write_json(OUT / 'SOURCE_INDEX.json', {'tree_commit': tree['sha'], 'readme': readme,
    'identity_related_paths': [p for p in paths if any(s in p.lower() for s in ['barcode', 'whitelist', '10x', 'readme', 'config'])],
    'http_requests': 2, 'scope': 'Repository tree and README only. No expression values or raw lineage records.'})
print(json.dumps({'tree_commit': tree['sha'], 'paths': len(paths), 'metadata_lines': len(metadata)}))
