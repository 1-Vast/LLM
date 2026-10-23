from html.parser import HTMLParser
from pathlib import Path

class Projection(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip += 1
        if tag in ('p','section','h1','h2','h3','h4','li','tr'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip -= 1
        if tag in ('p','section','h1','h2','h3','h4','li','tr'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

folder = Path(__file__).resolve().parents[3] / 'log/20261023/response_law_revision/critic'
for stem in ('cicme_primary','recombination_primary'):
    p=Projection(); p.feed((folder/(stem+'.body')).read_text(encoding='utf8'))
    (folder/(stem+'.txt')).write_text('\n'.join(' '.join(s.split()) for s in ''.join(p.parts).splitlines() if s.strip()), encoding='utf8')
