"""Compare design identifiers only; do not decode functional-value columns."""
from collections import Counter
from io import BytesIO
import csv
import json
import struct
import zlib
from zipfile import ZipFile
from metadata import OUT

if __name__=='__main__':
    b=(OUT/'pseudobulk_prefix.body').read_bytes()
    h=struct.unpack_from('<4s5H3L2H',b)
    r=zlib.decompressobj(-15).decompress(b[30+h[9]+h[10]:])
    first,second,_=r.split(b'\n',2)
    a=next(csv.reader([first.decode()]));t=next(csv.reader([second.decode()]))
    assert len(a)==len(t) and t[0]=='assigned_ko'
    state=list(zip(a[1:],t[1:]))
    # Split only the two identifier columns. Remaining response text stays bytes.
    raw=(OUT/'crispr_table.csv').read_bytes().splitlines()
    assert raw[0]==b'cell_line,guide,gene_effect,dependency_strength_class,is_dependent'
    function=[tuple(x.decode() for x in row.split(b',',2)[:2]) for row in raw[1:]]
    assert all(len(x)==2 for x in function)
    with ZipFile(OUT/'metadata.zip.body') as z:
        design=list(csv.DictReader(z.read('metadata/cell_line_metadata.csv').decode().splitlines()))
    s,f=set(state),set(function)
    result=dict(scope='identifiers only, no functional values cast; prefix state header not full matrix validation',
        state_columns=len(state),state_unique=len(s),function_rows=len(function),function_unique=len(f),
        matched=len(s&f),state_only=sorted(s-f),function_only=sorted(f-s),
        state_by_line=dict(Counter(x[0] for x in state)),
        function_by_line=dict(Counter(x[0] for x in function)),cell_line_design=design)
    (OUT/'IDENTITY_JOIN.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
