"""Plain-text extraction using Python standard library only."""
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path('log/20261022/next_mechanism/recursive')

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

for path in ROOT.glob('*.html'):
    parser = Text()
    parser.feed(path.read_text(encoding='utf-8'))
    path.with_suffix('.txt').write_text('\n'.join(parser.parts), encoding='utf-8')

crossref = json.loads((ROOT / 'crossref_discorl.json').read_text(encoding='utf-8'))
print(json.dumps([{k: x.get(k) for k in ['title', 'DOI', 'URL', 'published']}
                  for x in crossref['message']['items']], ensure_ascii=False, indent=2))
