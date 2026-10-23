"""Download OA primary article XML; extract prose, never supplementary numeric tables."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import hashlib
import json
import xml.etree.ElementTree as ET

out=Path('D:/MAESTRO/log/20261022/early_update_mechanism/biology')
url='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11919725/fullTextXML'
path=out/'decryptE_fulltext.xml'
assert not path.exists()
receipt=dict(url=url,started_utc=datetime.now(timezone.utc).isoformat(),retries=0,max_bytes=8*1024*1024)
try:
    try:
        response=urlopen(Request(url,headers={'User-Agent':'Primary-source mechanism review/1.0'}),timeout=40)
    except HTTPError as error:
        response=error
    with response:
        body=response.read(8*1024*1024+1)
        assert len(body)<=8*1024*1024
        receipt.update(status=response.status,final_url=response.geturl())
    path.write_bytes(body)
    receipt.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    if receipt['status']==200:
        tree=ET.fromstring(body)
        assert any(n.text=='10.1038/s41587-024-02218-y' for n in tree.findall('.//article-id'))
        text=[]
        def visit(node,section=''):
            if node.tag in ('table-wrap','table','fig','ref-list'):
                return
            if node.tag=='sec':
                heading=node.find('title')
                section=''.join(heading.itertext()) if heading is not None else section
            if node.tag=='p':
                text.append(dict(section=section,text=''.join(node.itertext())))
                return
            for child in node:
                visit(child,section)
        visit(tree)
        (out/'decryptE_PROSE.json').write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf-8')
        (out/'decryptE_PROSE.txt').write_text('\n\n'.join(f"[{i}] {r['section']}\n{r['text']}" for i,r in enumerate(text)),encoding='utf-8')
except Exception as error:
    receipt.update(error_type=type(error).__name__,error=str(error))
receipt['ended_utc']=datetime.now(timezone.utc).isoformat()
(out/'decryptE_fulltext.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
