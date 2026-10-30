"""Read identity fields only; never convert, print, or summarize fluorescence."""
import csv, json, pathlib, struct, zlib
B=pathlib.Path(__file__).parent
out={}
for label in ['E3CA','E3CB','E3DA','E3DB']:
    with (B/('cxcl9_raw_'+label+'.body')).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f); header=next(reader); ids=set(); samples=set()
        for row in reader:
            ids.add(tuple(row[:7])); samples.add(row[1])
    out[label]={'header':header,'unique_identity_rows':[list(t) for t in sorted(ids)],
                'sample_ids':sorted(samples),'outcome_columns_ignored':[header[7]],
                'note':'Rows are capture-bead FACS measurements, not cell counts or independent cultures.'}
(B/'schema_only.json').write_text(json.dumps(out,indent=2),encoding='utf8')
# Examine only ZIP local headers in the partial prefix. No response outcomes decoded.
raw=(B/'caf_supp_package.body').read_bytes(); p=0; entries=[]
while raw[p:p+4]==b'PK\x03\x04':
    h=struct.unpack_from('<IHHHHHIIIHH',raw,p)
    _,ver,flags,method,tm,dt,crc,cs,us,nl,xl=h
    name=raw[p+30:p+30+nl].decode('utf8','replace')
    entries.append({'name':name,'flags':flags,'compression':method,'declared_compressed':cs,
                    'declared_uncompressed':us,'crc32':crc})
    if flags & 8:
        entries[-1]['recovery']='data-descriptor size unknown; not recovered/CRC not certified'
        break
    p+=30+nl+xl+cs
(B/'caf_partial_headers.json').write_text(json.dumps({'complete_zip':False,'local_entries':entries},indent=2))
print(json.dumps({k:dict(identity_rows=len(v['unique_identity_rows']),samples=v['sample_ids']) for k,v in out.items()}))
print(json.dumps(entries))
