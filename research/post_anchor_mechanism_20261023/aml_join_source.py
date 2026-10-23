"""Acquire pinned author join code as text; never import or execute it."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/post_anchor_mechanism/root_sources'
SHA = '3d5ef9070a259fb902feccbc5948f10e6a9d44ae'
NAMES = ['1_LineagePreprocessing.py', '2_TagClustering.py', 'AML_lineage_utilities.py']


def get(name):
    url = f'https://raw.githubusercontent.com/mckennalab/AML_lineage_tracing/{SHA}/python_scripts/{name}'
    record = dict(url=url, utc=datetime.now(timezone.utc).isoformat())
    target = OUT / ('aml_join_' + name.removesuffix('.py'))
    try:
        response = requests.get(url, timeout=35)
        target.with_suffix('.body').write_bytes(response.content)
        blob = b'blob ' + str(len(response.content)).encode() + b'\0' + response.content
        record.update(status=response.status_code, bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest(),
                      git_blob_sha1=hashlib.sha1(blob).hexdigest())
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    target.with_suffix('.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(get, NAMES)), indent=2))
