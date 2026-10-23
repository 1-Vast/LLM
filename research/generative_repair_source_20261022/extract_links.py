"""Copy already saved publisher supplement links, without network access."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json

root = Path('D:/MAESTRO')
source = root / 'tmp/ptv1_src/art.html'
out = root / 'log/20261022/generative_repair_renewal/source'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and '41586_2026_11001_MOESM' in attrs.get('href', ''):
            self.current = dict(url=attrs['href'], text=[])
    def handle_data(self, text):
        if self.current is not None and text.strip():
            self.current['text'].append(text.strip())
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.current['text'] = ' '.join(self.current['text'])
            self.links.append(self.current)
            self.current = None

parser = Links()
parser.feed(source.read_text(encoding='utf-8', errors='replace'))
result = dict(source=str(source.relative_to(root)), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              links=parser.links, source_downloads_made=False)
(out / 'PUBLISHER_SUPPLEMENT_LINKS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
