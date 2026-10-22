"""Inspect public paper text, release metadata and repository path names only."""
from pathlib import Path
import json
from bs4 import BeautifulSoup
root=Path('D:/MAESTRO/log/20261022/contrast_mechanism_scout/sources')
out=[]
for name in ['batchie_prospective_metadata','batchie_retrospective_metadata']:
    data=json.loads((root/(name+'.body')).read_text())
    out.append(dict(source=name,files=data.get('files'),description=data.get('metadata',{}).get('description')))
tree=json.loads((root/'batchie_repo_tree.body').read_text())
out.append(dict(source='batchie_repo_tree',sha=tree.get('sha'),paths=[i for i in tree.get('tree',[]) if any(x in i['path'].lower() for x in ['readme','prospective','sarcoma','preprocess','data_structure','data.py'])]))
soup=BeautifulSoup((root/'tdal_html.body').read_bytes(),'html.parser')
sections=[]
for sec in soup.select('section'):
    heading=sec.find(['h1','h2','h3','h4'],recursive=False)
    if heading and any(s in heading.get_text(' ',strip=True).lower() for s in ['datasets and hit','temporal difference learning','dynamic acquisition']):
        sections.append(dict(heading=heading.get_text(' ',strip=True),text=sec.get_text(' ',strip=True)))
out.append(dict(source='tdal',sections=sections,links=sorted({a['href'] for a in soup.select('a[href]') if any(x in a['href'].lower() for x in ['github','zenodo','figshare'])})))
text=json.dumps(out,indent=2)
(root.parent/'SOURCE_INSPECTION.json').write_text(text,encoding='utf-8')
print(text)
