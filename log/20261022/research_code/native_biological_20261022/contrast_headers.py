from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json
out=Path('D:/MAESTRO/log/20261022/native_operation/biology');ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(out/'supplement3.xlsx') as z:
 ss=[''.join(s.itertext()) for s in E.fromstring(z.read('xl/sharedStrings.xml'))]
 sheets=E.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',ns)
 results=[]
 for k,s in enumerate(sheets,1):
  if not s.attrib['name'].startswith('Supplementary Table 2'):continue
  rows=[]
  for row in E.fromstring(z.read(f'xl/worksheets/sheet{k}.xml')).findall('m:sheetData/m:row',ns):
   if int(row.attrib['r'])>3:continue
   vals=[]
   for c in row:
    v=c.find('m:v',ns)
    if c.attrib.get('t')=='s' and v is not None:vals.append([c.attrib['r'],ss[int(v.text)]])
   rows.extend(vals)
  results.append({'sheet':s.attrib['name'],'strings_rows1to3':rows})
(out/'viability_header_detail.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
