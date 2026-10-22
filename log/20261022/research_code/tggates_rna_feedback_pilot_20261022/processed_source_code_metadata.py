"""Inspect author normalization source only; do not fetch numerical matrices."""
from datetime import datetime, timezone
import base64
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/tggates_rna_feedback_pilot/rna_sources'


def get(name, url):
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url, 'logical_request':1,
               'RNA_numerical_payload_allowed':False}
    body = None
    try:
        response = requests.get(url, timeout=30)
        body = response.content
        if len(body) > 2*1024*1024:
            raise ValueError('Source metadata cap')
        with (OUT/(name+'.body')).open('xb') as stream:
            stream.write(body)
        receipt.update(status=response.status_code, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                       headers=dict(response.headers), final_url=response.url)
    except Exception as exc:
        receipt['error_type'] = type(exc).__name__
    with (OUT/(name+'.http.json')).open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps({k:receipt.get(k) for k in ('url','status','bytes','error_type')}), flush=True)
    return body if receipt.get('status') == 200 else None


def main():
    body = get('processed_author_tree', 'https://api.github.com/repos/Ajay1989Kumar/eastman-pande-2019-repro/git/trees/HEAD?recursive=1')
    if body is None:
        return
    tree = json.loads(body)
    candidates = [row for row in tree.get('tree', []) if row['type']=='blob'
                  and row['path'].lower().endswith('.r') and any(word in row['path'].lower() for word in ('rma','preprocess','norm'))]
    with (OUT/'processed_author_code_candidates.json').open('x', encoding='utf-8') as stream:
        json.dump({'tree_sha':tree.get('sha'), 'truncated':tree.get('truncated'), 'candidates':candidates}, stream, indent=2)
    for index, row in enumerate(candidates[:2]):
        blob = get('processed_author_norm_code_'+str(index), 'https://api.github.com/repos/Ajay1989Kumar/eastman-pande-2019-repro/git/blobs/'+row['sha'])
        if blob:
            parsed = json.loads(blob)
            content = base64.b64decode(parsed['content'])
            with (OUT/('processed_author_norm_code_'+str(index)+'.decoded.R')).open('xb') as stream:
                stream.write(content)


if __name__ == '__main__':
    main()
