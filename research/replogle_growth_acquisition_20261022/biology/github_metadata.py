"""Bounded three-request public GitHub metadata-only source qualification."""
import datetime
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

out = Path('log/20261022/replogle_growth_acquisition/biology')
out.mkdir(parents=True, exist_ok=True)

def fetch(name, url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-qualification', 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body, status = response.read(), response.status
    except urllib.error.HTTPError as error:
        body, status = error.read(), error.code
    except Exception as error:
        body, status = str(error).encode(), None
    (out / (name + '.body')).write_bytes(body)
    receipt = dict(url=url, status=status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (out / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    return json.loads(body) if status == 200 else None

repo = fetch('norman_repo', 'https://api.github.com/repos/thomasmaxwellnorman/Perturbseq_GI')
repos = fetch('replogle_repos', 'https://api.github.com/users/josephreplogle/repos?per_page=100')
if repos:
    metadata = [{key: item.get(key) for key in ['name', 'description', 'html_url', 'default_branch']} for item in repos]
    (out / 'REPlOGLE_REPOS.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata))
if repo:
    branch = repo['default_branch']
    tree = fetch('norman_tree', 'https://api.github.com/repos/thomasmaxwellnorman/Perturbseq_GI/git/trees/' + branch + '?recursive=1')
    if tree:
        paths = [item['path'] for item in tree.get('tree', [])]
        (out / 'NORMAN_PATHS.json').write_text(json.dumps(dict(truncated=tree.get('truncated'), paths=paths), indent=2), encoding='utf-8')
        print(json.dumps(paths))
