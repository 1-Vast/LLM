from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

root = Path('log/20261023/hcc_link_recovery')
record = json.loads((root / 'biostudies_record.json').read_text(encoding='utf-8'))
xml = Path('log/20261023/hcc_task_qualification/epmc_fulltext.xml').read_text(encoding='utf-8')
pis = re.findall(r'<\?suppdata-md5\s+([^?]+)\?>', xml)
objects = []
def walk(node):
    if isinstance(node, dict):
        if 'path' in node or 'size' in node:
            objects.append(node)
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)
walk(record)
doc = root / 'biostudies_mmc2.docx'
with zipfile.ZipFile(doc) as z:
    document = ET.fromstring(z.read('word/document.xml'))
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in document.findall('.//w:p',ns)]
result = {'record_accno':record.get('accno'),'record_attributes':record.get('attributes'),
          'file_objects':objects,'original_suppdata_PI':pis,
          'downloaded_docx':{'bytes':doc.stat().st_size,'sha256':hashlib.sha256(doc.read_bytes()).hexdigest(),'md5':hashlib.md5(doc.read_bytes()).hexdigest(),'first_nonempty_paragraphs':[p for p in paragraphs if p][:3]},
          'source_sha256':{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'biostudies_record.json',root/'epmc_labs_links.xml',Path('log/20261023/hcc_task_qualification/epmc_fulltext.xml')]}}
(root/'agent'/'BIOSTUDIES_INDEPENDENT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
