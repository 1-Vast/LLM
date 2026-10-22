from pathlib import Path
import requests,json,hashlib,datetime,zipfile,xml.etree.ElementTree as E
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
u='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-021-00779-1/MediaObjects/41588_2021_779_MOESM3_ESM.xlsx'
r=requests.get(u,timeout=40);assert len(r.content)<4_000_000
p=out/'supplement3.xlsx';p.write_bytes(r.content)
(out/'supplement_get_receipt.json').write_text(json.dumps({'url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with zipfile.ZipFile(p) as z:
 strings=[''.join(s.itertext()) for s in E.fromstring(z.read('xl/sharedStrings.xml'))]
 rels={r.attrib['Id']:r.attrib['Target'] for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
 ans=[]
 for s in E.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',ns):
  target=rels[s.attrib['{'+ns['r']+'}id']];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  root=E.fromstring(z.read(target)); rows=root.findall('m:sheetData/m:row',ns)
  headers=[]
  for row in rows[:1]:
   for c in row:
    v=c.find('m:v',ns)
    if c.attrib.get('t')=='s':headers.append([c.attrib['r'],strings[int(v.text)]])
    elif c.attrib.get('t')=='inlineStr':headers.append([c.attrib['r'],''.join(c.find('m:is',ns).itertext())])
    else:headers.append([c.attrib.get('r'),'NUMERIC_TOKEN_NOT_DECODED'])
  ans.append({'sheet':s.attrib['name'],'row_count':len(rows),'headers':headers})
(out/'supplement_headers.json').write_text(json.dumps(ans,indent=2));print(json.dumps(ans,indent=2))
