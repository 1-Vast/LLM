"""Authenticate publisher-linked filenames and select only the supplement PDF."""
import json
from pathlib import Path
from retrieve import OUT

rows = json.loads((OUT/'FIGSHARE_INDEX.json').read_text())
inventory = []
for row in rows:
    data = json.loads((OUT/('figshare_'+str(row['id'])+'.json')).read_text())
    assert data['id'] == row['id'] and data['doi'] == row['doi']
    assert data['resource_doi'] == '10.1021/acs.analchem.5c04806'
    for file in data['files']:
        inventory.append(dict(article_id=data['id'], doi=data['doi'], name=file['name'],
                              download_url=file['download_url'], size=file['size'],
                              computed_md5=file.get('computed_md5'), id=file['id']))
record = dict(files=inventory, file_count=len(inventory),
              pdfs=sum(f['name'].lower().endswith('.pdf') for f in inventory),
              mp4s=sum(f['name'].lower().endswith('.mp4') for f in inventory),
              scope='Current public publisher supplement inventory, not every possible author resource')
(OUT/'FILE_INVENTORY.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
