"""Retrieve small functional table and a bounded state prefix; inspect headers only."""
import hashlib
import json
import struct
import zlib
from zip_directory import byte_range
from metadata import OUT


def member(name,entry,file,full=False):
    offset=entry['local_offset']
    # Bound overhead for local filename/extra fields, then retain exactly payload.
    length=entry['compressed_bytes']+4096 if full else 65536
    body=byte_range(name,file['download_url'],offset,offset+length-1,file['size'])
    h=struct.unpack_from('<4s5H3L2H',body)
    assert h[0]==b'PK\x03\x04' and h[3]==entry['compression']==8
    name_len,extra_len=h[9:11]
    assert body[30:30+name_len].decode()==entry['path']
    begin=30+name_len+extra_len
    payload=body[begin:begin+entry['compressed_bytes']]
    dec=zlib.decompressobj(-15)
    raw=dec.decompress(payload)
    result=dict(archive_member=entry['path'],full_member=full,
        archive_MD5_not_verified=True,bytes_decompressed=len(raw))
    if full:
        assert dec.eof and len(raw)==entry['bytes']
        assert zlib.crc32(raw)==entry['crc32']
        result['crc32_verified']=True
        result['sha256']=hashlib.sha256(raw).hexdigest()
        (OUT/(name+'.csv')).write_bytes(raw)
    else:
        result['crc32_verified']=False
    assert b'\n' in raw
    result['header']=raw.split(b'\n',1)[0].decode('utf-8-sig').rstrip('\r')
    return result


if __name__=='__main__':
    files={x['name']:x for x in json.loads((OUT/'figshare_data_manifest.body').read_text())['files']}
    rows=json.loads((OUT/'ARCHIVE_DIRECTORY.json').read_text())['processed.zip']
    byname={x['path']:x for x in rows}
    result=[member('crispr_table',byname['processed/crispr_table.csv'],files['processed.zip'],True),
            member('pseudobulk_prefix',byname['processed/pseudobulk_sum_by_ko.csv'],files['processed.zip'])]
    (OUT/'MEMBER_SCHEMA.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([{**x,'header':x['header'][:500]} for x in result],indent=2))
