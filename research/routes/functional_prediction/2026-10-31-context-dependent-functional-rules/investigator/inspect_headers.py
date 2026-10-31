import json,pathlib,zipfile,xml.etree.ElementTree as E,posixpath
area=pathlib.Path(__file__).resolve().parent
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
out=[]
for p in (area/'sources').glob('*.xlsx.hop1'):
 with zipfile.ZipFile(p) as z:
  wb=E.fromstring(z.read('xl/workbook.xml'))
  rel=E.fromstring(z.read('xl/_rels/workbook.xml.rels'))
  targets={r.attrib['Id']:r.attrib['Target'] for r in rel}
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   strings=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
  rec={'file':p.name,'zip_members':[{'name':i.filename,'compressed_bytes':i.compress_size,'uncompressed_bytes':i.file_size} for i in z.infolist()],'sheets':[]}
  for sh in wb.find('s:sheets',ns):
   rid=sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
   target=targets[rid]; target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
   sheet=E.fromstring(z.read(target))
   dim=sheet.find('s:dimension',ns)
   headers=[]
   row=sheet.find("s:sheetData/s:row[@r='1']",ns)
   if row is not None:
    for c in row:
     t=c.attrib.get('t'); v=c.find('s:v',ns)
     if t=='s' and v is not None: headers.append({'cell':c.attrib['r'],'text':strings[int(v.text)]})
     elif t=='inlineStr': headers.append({'cell':c.attrib['r'],'text':''.join(c.find('s:is',ns).itertext())})
   rec['sheets'].append({'title':sh.attrib['name'],'dimension':None if dim is None else dim.attrib.get('ref'),'row1_text_labels_only':headers})
  out.append(rec)
(area/'xlsx_metadata_only.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k!='zip_members'} for r in out],indent=2))
