"""Authenticate one publicly advertised processed route without expression reads."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/tggates_rna_feedback_pilot/rna_sources'
URLS = [('processed_zenodo_20204514', 'https://zenodo.org/api/records/20204514'),
        ('processed_HF_tree', 'https://huggingface.co/api/datasets/ajaygeetakumar/dili-toxicogenomics-expression/tree/main/eastman-pande-2019-crossspecies?recursive=false'),
        ('processed_HF_readme', 'https://huggingface.co/datasets/ajaygeetakumar/dili-toxicogenomics-expression/raw/main/README.md')]


def one(args):
    name, url = args
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url, 'method': 'GET',
               'logical_request': 1, 'RNA_expression_payload_allowed': False}
    try:
        response = requests.get(url, timeout=30, stream=True)
        chunks, total = [], 0
        for chunk in response.iter_content(65536):
            total += len(chunk)
            if total > 2*1024*1024:
                raise ValueError('Metadata cap')
            chunks.append(chunk)
        body = b''.join(chunks)
        with (OUT/(name+'.body')).open('xb') as stream:
            stream.write(body)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest(), headers=dict(response.headers))
    except Exception as exc:
        receipt['error_type'] = type(exc).__name__
    with (OUT/(name+'.http.json')).open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    return {k:receipt.get(k) for k in ('url','status','bytes','error_type')}


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as executor:
        for result in executor.map(one, URLS):
            print(json.dumps(result), flush=True)
