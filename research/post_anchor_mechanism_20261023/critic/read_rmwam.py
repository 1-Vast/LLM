from html.parser import HTMLParser
from pathlib import Path

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ['script','style']:
            self.skip += 1
        elif tag in ['p','h1','h2','h3','div','section'] and not self.skip:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ['script','style']:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

base = Path('D:/MAESTRO/log/20261023/post_anchor_mechanism/critic')
p = Reader()
p.feed((base/'rmwam.body').read_text(encoding='utf-8'))
lines = [' '.join(t.split()) for t in ''.join(p.parts).splitlines() if t.strip()]
(base/'rmwam.text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,t in enumerate(lines):
    if any(k in t.lower() for k in ['counterfactual','utility','3.3','3.4','gating']):
        print(i,t[:1800])
