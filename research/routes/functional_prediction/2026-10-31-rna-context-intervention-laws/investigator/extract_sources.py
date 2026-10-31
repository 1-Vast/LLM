import xml.etree.ElementTree as ET,pathlib
base=pathlib.Path('research/routes/functional_prediction/2026-10-31-rna-context-intervention-laws/investigator')
for name in ['promoter2026','cas13_aso2026']:
 r=ET.parse(base/'sources'/f'{name}.xml').getroot(); rows=[]
 for i,e in enumerate(r.iter()):
  if e.tag in ['article-title','title','p','table-wrap','supplementary-material']:
   t=' '.join(''.join(e.itertext()).split()); rows.append(f'NODE{i} {t}')
 (base/f'{name}_passages.txt').write_text('\n'.join(rows),encoding='utf-8')
