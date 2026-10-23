"""One pinned public author-code retrieval, read-only evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_rule_discovery/root'
URL = 'https://raw.githubusercontent.com/keikeiqi/MGTTA/34816cff343e51786aa577540ffb3f252dc331ad/tta_library/metanet/TTT.py'

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'author_memory_source.txt'
    if path.exists():
        raise FileExistsError(path)
    receipt = {'url': URL, 'utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1}
    try:
        response = requests.get(URL, timeout=45)
        raw = response.content
        path.write_bytes(raw)
        git_blob_sha1 = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        receipt.update(status=response.status_code, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                       final_url=response.url, git_blob_sha1=git_blob_sha1,
                       tree_blob_match=git_blob_sha1 == 'c2a62c14c630b4a0385c394b5995797571b24670',
                       generated_or_author_code_executed=False)
    except requests.RequestException as error:
        receipt['error_type'] = type(error).__name__
    (OUT / 'AUTHOR_MEMORY_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
