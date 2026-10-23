"""Read exact deposited compressed column headers, never biological records."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zlib
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
ITEMS=[('pre','GSM8791698','GSM8791698_sample2_sample3_FLARE_barcodes_founder_tag.stats.txt.gz'),
       ('post','GSM8791703','GSM8791703_sample4_FLARE_barcodes_founder_tag.stats.txt.gz')]
def fetch(item):
    name,accession,filename=item
    url=f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM8791nnn/{accession}/suppl/{filename}'
    receipt=dict(url=url,utc=datetime.now(timezone.utc).isoformat(),export_scope='first decompressed line only',
        contract_sha256=hashlib.sha256((OUT.parent/'LINEAGE_HEADER_PROTOCOL.md').read_bytes()).hexdigest())
    prefix=bytearray()
    try:
        with requests.get(url,headers={'Range':'bytes=0-65535'},stream=True,timeout=40) as response:
            receipt.update(status=response.status_code,content_range=response.headers.get('Content-Range'),
                           content_length=response.headers.get('Content-Length'))
            decoder=zlib.decompressobj(16+zlib.MAX_WBITS)
            header=b''
            for part in response.iter_content(4096):
                if len(prefix)+len(part)>1_048_576:
                    receipt['stop']='PREFIX_CAP';break
                prefix.extend(part)
                if response.status_code not in [200,206]:
                    receipt['stop']='HTTP_FAILURE';break
                header+=decoder.decompress(part,65536-len(header))
                if b'\n' in header:
                    receipt.update(header=header.split(b'\n',1)[0].decode('utf-8').rstrip('\r'),stop='HEADER_OBTAINED')
                    break
                if len(header)>=65536:
                    receipt['stop']='HEADER_LENGTH_CAP';break
    except Exception as error:receipt.update(error_type=type(error).__name__,error=str(error))
    (OUT/f'lineage_{name}.compressed_prefix').write_bytes(prefix)
    receipt.update(retained_prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest())
    (OUT/f'lineage_{name}.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:print(json.dumps(list(pool.map(fetch,ITEMS)),indent=2))
