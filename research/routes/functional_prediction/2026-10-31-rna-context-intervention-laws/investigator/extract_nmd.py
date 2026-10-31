import xml.etree.ElementTree as E,pathlib
b=pathlib.Path('research/routes/functional_prediction/2026-10-31-rna-context-intervention-laws/investigator');r=E.parse(b/'sources/nmd_variable2025.xml').getroot(); rows=[]
for i,e in enumerate(r.iter()):
 if e.tag in ['title','p']:
  t=' '.join(''.join(e.itertext()).split());rows.append(f'NODE{i} {t}')
(b/'nmd_passages.txt').write_text('\n'.join(rows),encoding='utf8')
for x in rows:
 if any(k in x.lower() for k in ['gtex','knockdown','causal','data avail','nmd efficiency','confound']):
  print(x[:1800])
