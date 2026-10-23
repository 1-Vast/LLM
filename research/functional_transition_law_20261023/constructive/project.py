from html.parser import HTMLParser
from pathlib import Path


class Projection(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, text):
        self.parts.append(text)
    def handle_starttag(self, tag, attrs):
        if tag in ('p','div','h1','h2','h3','li','tr'):
            self.parts.append('\n')


path = Path('log/20261023/functional_transition_law/constructive')
parser = Projection()
parser.feed((path/'mz_primary.body').read_text(encoding='utf-8'))
lines = [' '.join(x.split()) for x in ''.join(parser.parts).splitlines() if x.strip()]
(path/'mz_primary.text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i, text in enumerate(lines,1):
    if any(term in text.lower() for term in ('memory kernel','orthogonal','architecture','finite-memory','loss function','causal','training objective')):
        print(i,text[:800])
