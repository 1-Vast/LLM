from pathlib import Path
import json
from html.parser import HTMLParser

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

base = Path('D:/MAESTRO/log/20261022/native_operation/proposer/sources')
for name in ['sequential_cell_search', 'lie_2025_search']:
    data = json.loads((base / (name + '.body')).read_bytes())
    records = data.get('resultList', {}).get('result', data.get('message', {}).get('items', []))
    for row in records:
        print(name, json.dumps({k: row[k] for k in ['title', 'DOI', 'doi', 'id', 'pmcid', 'pubYear', 'URL', 'published', 'link'] if k in row}))
for name in ['dgm_abs', 'dgm_html']:
    parser = TextParser()
    parser.feed((base / (name + '.body')).read_text(encoding='utf-8'))
    text = ' '.join(parser.parts)
    for term in ['Submitted on', 'archive', 'stepping stones', 'self-modif']:
        start = text.lower().find(term.lower())
        print(name, term, text[max(0, start-150):start+1000])
