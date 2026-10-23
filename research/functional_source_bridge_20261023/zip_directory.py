"""Read ZIP central-directory metadata only using authenticated byte ranges."""
from datetime import datetime, timezone
import hashlib
import json
import struct
import requests
from metadata import OUT


def byte_range(name,url,start,end,total):
    path=OUT/(name+'.body')
    assert not path.exists()
    stamp=datetime.now(timezone.utc).isoformat()
    with requests.get(url,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,40)) as r:
        body=r.raw.read(end-start+2,decode_content=False)
        receipt=dict(url=url,status=r.status_code,range_start=start,range_end=end,total=total,
            content_range=r.headers.get('Content-Range'),bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),start=stamp,end=datetime.now(timezone.utc).isoformat())
    path.write_bytes(body)
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    assert receipt['status']==206 and receipt['content_range']==f'bytes {start}-{end}/{total}'
    assert len(body)==end-start+1
    return body


def directory(body,count):
    rows=[]
    pos=0
    for _ in range(count):
        fields=struct.unpack_from('<4s6H3L5H2L',body,pos)
        assert fields[0]==b'PK\x01\x02'
        name_len,extra_len,comment_len=fields[10:13]
        name=body[pos+46:pos+46+name_len].decode('utf-8')
        rows.append(dict(path=name,flags=fields[3],compression=fields[4],crc32=fields[7],
                         compressed_bytes=fields[8],bytes=fields[9],local_offset=fields[16]))
        pos+=46+name_len+extra_len+comment_len
    return rows


if __name__=='__main__':
    manifest=json.loads((OUT/'figshare_data_manifest.body').read_text())
    files={x['name']:x for x in manifest['files']}
    tails=json.loads((OUT/'ZIP_TAIL_SCHEMA.json').read_text())
    result={}
    for row in tails:
        name=row['name'].removesuffix('.tail')
        f=files[name]
        e=row['eocd']
        start=e['central_directory_offset']; end=start+e['central_directory_bytes']-1
        old=(OUT/(row['name']+'.body')).read_bytes()
        old_start=f['size']-len(old)
        if start>=old_start:
            body=old[start-old_start:end-old_start+1]
        else:
            body=byte_range(name+'.directory',f['download_url'],start,end,f['size'])
        result[name]=directory(body,e['entries'])
    (OUT/'ARCHIVE_DIRECTORY.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({name:[r for r in rows if any(t in r['path'] for t in
        ['knockout_metadata','pseudobulk_sum_by_ko','lfc_matrix','CRISPRGeneEffect','crispr_table','cell_quality_covariates'])]
        for name,rows in result.items()},indent=2))
