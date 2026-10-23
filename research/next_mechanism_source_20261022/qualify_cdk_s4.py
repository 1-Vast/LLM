"""One bounded primary Table S4 request; only text annotations, no assay values."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, zipfile
import xml.etree.ElementTree as ET
import requests
root=Path('D:/MAESTRO')
out=root/'log/20261022/next_mechanism/source/cdk_review'
url='https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-026-01690-2/MediaObjects/13073_2026_1690_MOESM5_ESM.xlsx'
def digest(b): return hashlib.sha256(b).hexdigest()
def safe(text):
    if re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?',text.strip()): return '[numeric text suppressed]'
    return text
def fetch():
    record={'url':url,'body_cap':100000,'started_utc':datetime.now(timezone.utc).isoformat()}
    try:
        with requests.get(url,timeout=60,stream=True) as response:
            record.update(status=response.status_code,final_url=response.url,headers=dict(response.headers))
            chunks=[]; size=0
            for chunk in response.iter_content(16384):
                size+=len(chunk)
                if size>100000: raise RuntimeError('body cap exceeded')
                chunks.append(chunk)
        body=b''.join(chunks)
        (out/'table_s4.body').write_bytes(body)
        record.update(bytes=len(body),sha256=digest(body),md5=hashlib.md5(body).hexdigest())
    except Exception as exc: record['error']=repr(exc)
    (out/'table_s4.receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))
def headers():
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(out/'table_s4.body') as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(t.text or '' for t in si.findall('.//s:t',ns)) for si in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets=[]
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('.//s:sheet',ns):
            target=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows=[]
            for row in ET.fromstring(archive.read(target)).findall('.//s:row',ns)[:20]:
                cells=[]
                for cell in list(row)[:30]:
                    item={'cell':cell.attrib.get('r')}
                    if cell.find('s:f',ns) is not None: item['formula_suppressed']=True
                    elif cell.attrib.get('t')=='s': item['text']=safe(strings[int(cell.find('s:v',ns).text)])
                    elif cell.attrib.get('t')=='inlineStr': item['text']=safe(''.join(t.text or '' for t in cell.findall('.//s:t',ns)))
                    else: item['numeric_or_other_suppressed']=True
                    cells.append(item)
                rows.append({'row':row.attrib.get('r'),'cells':cells})
            sheets.append({'name':sheet.attrib['name'],'rows':rows})
    body=(out/'table_s4.body').read_bytes()
    result={'scope':'Text labels only, first 20 rows and 30 cells per row; numeric cells/formulas suppressed.',
            'sha256':digest(body),'matches_primary_declared_md5':hashlib.md5(body).hexdigest()=='880ff5429f11f79a57d2f58081e1698b','sheets':sheets}
    (out/'TABLE_S4_HEADERS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    import sys
    fetch() if sys.argv[1]=='fetch' else headers()
