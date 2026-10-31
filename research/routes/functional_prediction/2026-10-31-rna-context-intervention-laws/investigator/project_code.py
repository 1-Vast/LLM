import json,pathlib,re
b=pathlib.Path('research/routes/functional_prediction/2026-10-31-rna-context-intervention-laws/investigator')
n=json.loads((b/'sources/promoter_figures.ipynb').read_text(encoding='utf8'))
s='\n'.join(f'CELL{i}\n'+''.join(c.get('source',[])) for i,c in enumerate(n['cells']) if c['cell_type']=='code')
(b/'promoter_code_only.txt').write_text(s,encoding='utf8')
d=json.loads((b/'sources/promoter_biostudies.json').read_text()); print(str(d)[:2000])
def walk(o):
 if isinstance(o,dict):
  if 'path' in o:print(o)
  for v in o.values():walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
walk(d)
