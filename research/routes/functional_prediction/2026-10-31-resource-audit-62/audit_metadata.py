"""Bounded public source acquisition and metadata-only workbook projection."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, io, json, urllib.request, urllib.error, zipfile, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
RECEIPTS = ROOT / 'receipts'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REQUESTS = []

def acquire(name, url, cap=20*1024*1024):
    rec = {'name': name, 'url': url, 'started_utc': datetime.now(timezone.utc).isoformat(), 'cap': cap, 'retries': 0}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-public-resource-audit/1.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            rec.update(status=response.status, final_url=response.url, headers=dict(response.headers))
            length = int(response.headers.get('Content-Length', '0'))
            if length > cap:
                rec.update(body_bytes=0, disposition='not_read_advertised_over_cap')
            else:
                body = response.read(cap+1)
                rec.update(body_bytes=len(body), complete=len(body)<=cap)
                if len(body)<=cap:
                    path=RECEIPTS/name
                    path.write_bytes(body)
                    rec.update(saved_path=str(path), sha256=hashlib.sha256(body).hexdigest(), zip_valid=zipfile.is_zipfile(io.BytesIO(body)))
    except urllib.error.HTTPError as exc:
        body=exc.read(2048)
        rec.update(status=exc.code, body_bytes=len(body), error=str(exc))
    except Exception as exc:
        rec.update(error=type(exc).__name__+': '+str(exc), body_bytes=None)
    REQUESTS.append(rec)
    (RECEIPTS/'http_receipts.json').write_text(json.dumps(REQUESTS,indent=2),encoding='utf-8')
    return rec

def project(path):
    # Whitelist: ZIP names, workbook sheets/dimensions, and first 4 rows' text
    # cells only. Numeric cells, formula bodies and all later cells are omitted.
    out={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'projection':'sheet names, dimensions, first four row text cells only; no numeric cells/formulas', 'sheets':[]}
    with zipfile.ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets={a.attrib['Id']:a.attrib['Target'] for a in rel}
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            # Only strings referenced by the whitelisted rows are projected below.
            shared=ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)
        for sheet in wb.findall('m:sheets/m:sheet',NS):
            rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target=targets[rid].replace('\\','/')
            member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            if member.startswith('xl/../'): member=member[6:]
            doc=ET.fromstring(z.read(member))
            rows=doc.findall('m:sheetData/m:row',NS)
            item={'name':sheet.attrib['name'], 'dimension':doc.find('m:dimension',NS).attrib.get('ref') if doc.find('m:dimension',NS) is not None else None,'header_text':[]}
            for row in rows[:4]:
                cells=[]
                for c in row.findall('m:c',NS):
                    typ=c.attrib.get('t')
                    if c.find('m:f',NS) is not None: continue
                    if typ=='s':
                        val=c.find('m:v',NS)
                        if val is not None:
                            text=''.join(shared[int(val.text)].itertext())
                            cells.append({'cell':c.attrib.get('r'),'text':text})
                    elif typ=='inlineStr':
                        cells.append({'cell':c.attrib.get('r'),'text':''.join(c.find('m:is',NS).itertext())})
                    elif typ=='str':
                        val=c.find('m:v',NS)
                        if val is not None: cells.append({'cell':c.attrib.get('r'),'text':val.text})
                if cells: item['header_text'].append({'row':row.attrib.get('r'),'cells':cells})
            item['numeric_cells_in_body_present_not_read']=any(c.attrib.get('t') not in ('s','inlineStr','str','e','b') and c.find('m:v',NS) is not None for row in rows[4:] for c in row.findall('m:c',NS))
            out['sheets'].append(item)
    return out

if __name__=='__main__':
    resources=[
        ('sarcoma_source.xlsx','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12334625/supplementaryFiles'),
        ('pa14_source.xlsx','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13187417/supplementaryFiles'),
    ]
    summaries=[]
    for name,url in resources:
        r=acquire(name,url)
        if r.get('zip_valid'):
            metadata=project(RECEIPTS/name)
            (RECEIPTS/(name+'.metadata.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
            summaries.append({'name':name,'sheets':[(x['name'],x['dimension']) for x in metadata['sheets']]})
    print(json.dumps({'requests':REQUESTS,'summaries':summaries},ensure_ascii=False,indent=2))
