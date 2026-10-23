"""Retrieve metadata or explicitly allowlisted author source, never assay payloads."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/cxcl9_source_feasibility'
REPO = 'SysBioOncology/ActiveLearning_MechanisticModels_CXCL9'


def fetch(url, name):
    target = OUT / name
    assert not target.exists(), target
    start = datetime.now(timezone.utc).isoformat()
    response = requests.get(url, timeout=45, headers={'User-Agent': 'MAESTRO-source-audit'})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    receipt = {'url': url, 'final_url': response.url, 'utc_start': start,
               'utc_end': datetime.now(timezone.utc).isoformat(),
               'http_status': response.status_code, 'bytes': len(response.content),
               'sha256': hashlib.sha256(response.content).hexdigest()}
    target.with_name(target.name + '.receipt.json').write_text(
        json.dumps(receipt, indent=2), encoding='utf-8')
    response.raise_for_status()
    return response


if __name__ == '__main__':
    repo = fetch(f'https://api.github.com/repos/{REPO}', 'repository.json').json()
    branch = repo['default_branch']
    commit = fetch(f'https://api.github.com/repos/{REPO}/commits/{branch}', 'commit.json').json()
    sha = commit['sha']
    tree = fetch(f'https://api.github.com/repos/{REPO}/git/trees/{sha}?recursive=1', 'tree.json').json()
    assert not tree.get('truncated'), 'Incomplete inventory'
    print(json.dumps({'commit': sha, 'entries': len(tree['tree']),
                      'files': sum(row['type'] == 'blob' for row in tree['tree'])}))
