"""Recover only CRC-certified complete ZIP members from a saved partial stream."""
import pathlib,struct,zlib,json,hashlib
B=pathlib.Path(__file__).parent
raw=(B/'caf_supp_package.body').read_bytes();p=0;records=[]
while raw[p:p+4]==b'PK\x03\x04':
    h=struct.unpack_from('<IHHHHHIIIHH',raw,p)
    flags,method,crc,cs,us,nl,xl=h[2],h[3],h[6],h[7],h[8],h[9],h[10]
    name=raw[p+30:p+30+nl].decode();start=p+30+nl+xl
    record={'name':name,'offset':p,'recovered':False}
    if method!=8: record['reason']='unsupported';records.append(record);break
    d=zlib.decompressobj(-15);v=d.decompress(raw[start:]);record['deflate_eof']=d.eof
    if not d.eof: record['reason']='incomplete deflate stream';records.append(record);break
    end=len(raw)-len(d.unused_data)
    if flags&8:
        if raw[end:end+4]==b'PK\x07\x08':end+=4
        if len(raw)-end<12:record['reason']='missing descriptor';records.append(record);break
        crc,cs,us=struct.unpack_from('<III',raw,end);end+=12
    actual=zlib.crc32(v)&0xffffffff
    record.update(crc32=crc,actual_crc32=actual,declared_size=us,actual_size=len(v))
    if actual!=crc or len(v)!=us:record['reason']='CRC/size mismatch';records.append(record);break
    target=B/('caf_recovered_'+pathlib.Path(name).name)
    if not target.exists():target.write_bytes(v)
    record.update(recovered=True,path=str(target),sha256=hashlib.sha256(v).hexdigest())
    records.append(record);p=end
(B/'caf_partial_headers.json').write_text(json.dumps({'complete_zip':False,'members':records,'remaining_bytes':len(raw)-p},indent=2))
print(json.dumps(records))
