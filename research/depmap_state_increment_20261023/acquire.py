"""Recover one pinned ZIP member without parsing biological values."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import zlib
import requests

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/depmap_state_increment'
SOURCE=ROOT/'log/20261023/functional_source_bridge/root'

if __name__=='__main__':
    rows=json.loads((SOURCE/'ARCHIVE_DIRECTORY.json').read_text())['processed.zip']
    entry=next(x for x in rows if x['path']=='processed/pseudobulk_sum_by_ko.csv')
    manifest=json.loads((SOURCE/'figshare_data_manifest.body').read_text())
    item=next(x for x in manifest['files'] if x['name']=='processed.zip')
    offset=entry['local_offset']; end=offset+entry['compressed_bytes']+4095
    target=OUT/'pseudobulk.range'
    assert not target.exists()
    start=datetime.now(timezone.utc).isoformat()
    with requests.get(item['download_url'],headers={'Range':f'bytes={offset}-{end}'},stream=True,timeout=(15,60)) as r:
        body=r.raw.read(end-offset+2,decode_content=False)
        receipt=dict(url=item['download_url'],status=r.status_code,content_range=r.headers.get('Content-Range'),
            start=start,end=datetime.now(timezone.utc).isoformat(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    target.write_bytes(body)
    (OUT/'ACQUISITION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    assert receipt['status']==206 and receipt['content_range']==f'bytes {offset}-{end}/{item["size"]}'
    assert len(body)==end-offset+1
    h=struct.unpack_from('<4s5H3L2H',body)
    assert h[0]==b'PK\x03\x04' and h[3]==8
    n,e=h[9:11]
    assert body[30:30+n].decode()==entry['path']
    dec=zlib.decompressobj(-15)
    data=dec.decompress(body[30+n+e:30+n+e+entry['compressed_bytes']])
    assert dec.eof and len(data)==entry['bytes'] and zlib.crc32(data)==entry['crc32']
    (OUT/'pseudobulk.csv').write_bytes(data)
    result=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32=entry['crc32'],
                compressed_bytes=entry['compressed_bytes'],whole_archive_md5_verified=False,
                scope='member bytes acquired and CRC-checked; no CSV data parsing')
    (OUT/'ACQUISITION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
