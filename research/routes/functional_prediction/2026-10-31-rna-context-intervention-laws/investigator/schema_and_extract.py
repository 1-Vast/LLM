import pathlib,zipfile,csv,io,xml.etree.ElementTree as ET,json
b=pathlib.Path('research/routes/functional_prediction/2026-10-31-rna-context-intervention-laws/investigator')
z=zipfile.ZipFile(b/'sources/promoter_supp2.zip'); out={'archive_members':[(x.filename,x.file_size) for x in z.infolist()]}
for x in z.infolist():
 if x.filename.lower().endswith('.csv') and not x.filename.startswith('__MACOSX'):
  with z.open(x) as h:
   t=io.TextIOWrapper(h,encoding='utf-8-sig'); out[x.filename]={'header':next(csv.reader(t))}
(b/'promoter_schema.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))
r=ET.parse(b/'sources/polr3a_original.xml').getroot(); rows=[]
for i,e in enumerate(r.iter()):
 if e.tag in ['article-title','title','p']:
  rows.append(f'NODE{i} '+' '.join(''.join(e.itertext()).split()))
(b/'polr3a_passages.txt').write_text('\n'.join(rows),encoding='utf-8')
