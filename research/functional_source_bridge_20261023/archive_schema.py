"""Authenticate small metadata and inspect large ZIP tails via bounded ranges."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import struct
from zipfile import ZipFile
import requests
from metadata import OUT, fetch


def tail(name,url,size):
    start=max(0,size-65536)
    stamp=datetime.now(timezone.utc).isoformat()
    with requests.get(url,headers={'Range':f'bytes={start}-{size-1}'},stream=True,timeout=(15,40)) as r:
        # Refuse ignored ranges without materializing entire large file.
        body=r.raw.read(65537,decode_content=False)
        receipt=dict(url=url,final_url=r.url,status=r.status_code,range=f'bytes={start}-{size-1}',
            content_range=r.headers.get('Content-Range'),content_length=r.headers.get('Content-Length'),
            bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),start=stamp,
            end=datetime.now(timezone.utc).isoformat())
    (OUT/(name+'.body')).write_bytes(body)
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    result=dict(name=name,receipt=receipt)
    if r.status_code==206 and receipt['content_range']==f'bytes {start}-{size-1}/{size}' and len(body)==size-start:
        pos=body.rfind(b'PK\x05\x06')
        assert pos>=0
        e=struct.unpack_from('<4s4H2LH',body,pos)
        result['eocd']=dict(entries=e[4],central_directory_bytes=e[5],central_directory_offset=e[6])
    return result


if __name__=='__main__':
    manifest=json.loads((OUT/'figshare_data_manifest.body').read_text())
    files={x['name']:x for x in manifest['files']}
    meta=files['metadata.zip']
    existing=OUT/'metadata.zip.body'
    if existing.exists():
        payload=existing.read_bytes()
    else:
        _,r=fetch('metadata.zip',meta['download_url'])
        assert r.status_code==200
        payload=r.content
    assert len(payload)==meta['size']
    assert hashlib.md5(payload).hexdigest()==meta['computed_md5']
    rows=[]
    with ZipFile(BytesIO(payload)) as z:
        for m in z.infolist():
            row=dict(path=m.filename,bytes=m.file_size,crc=m.CRC)
            if m.filename.endswith('.csv') and not m.filename.split('/')[-1].startswith('._'):
                with z.open(m) as stream:
                    header=stream.readline()
                    try:
                        row['header']=header.decode('utf-8-sig').rstrip('\r\n')
                    except UnicodeDecodeError:
                        row['header_encoding']='non-UTF8; not interpreted'
            rows.append(row)
    (OUT/'METADATA_SCHEMA.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    results=[]
    for name in ['processed.zip','downloaded.zip']:
        f=files[name]
        results.append(tail(name+'.tail',f['download_url'],f['size']))
    (OUT/'ZIP_TAIL_SCHEMA.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(dict(metadata_rows=rows,large_archives=results),indent=2))
