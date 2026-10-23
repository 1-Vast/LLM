"""Commit-pinned, explicit source-only allowlist for measurement provenance."""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from source import OUT, REPO, fetch
import json

ALLOW = [
    'README.md',
    '01_mechanistic_model/01_preparing_inputs.R',
    '01_mechanistic_model/utils.R',
    '02_active_learning/optimization.R',
    '02_active_learning/utils.R',
    'data/cxcl9_assay/metadata.md',
    'data/cxcl9_assay_active_learning/metadata.md',
    'data/model_inputs_active_learning/AsPC1/metadata.md',
]

if __name__ == '__main__':
    sha = json.loads((OUT/'commit.json').read_text(encoding='utf-8'))['sha']

    def retrieve(path):
        response = fetch(f'https://raw.githubusercontent.com/{REPO}/{sha}/{quote(path)}',
                         'source/'+path)
        return {'path': path, 'bytes': len(response.content), 'status': response.status_code}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, ALLOW))
    (OUT/'SOURCE_ALLOWLIST.json').write_text(json.dumps({'commit': sha, 'files': results}, indent=2),
                                            encoding='utf-8')
    print(json.dumps(results, indent=2))
