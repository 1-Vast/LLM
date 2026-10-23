import html.parser
import pathlib
import sys

class Text(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'a':
            self.links.extend(v for k, v in attrs if k == 'href' and any(s in v for s in ('github', 'arxiv', 'deepmind')))
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())

root = pathlib.Path(__file__).resolve().parents[3]
folder = root / 'log/20261023/functional_transition_law/critic'
p = Text()
name = sys.argv[1] if len(sys.argv)>1 else 'online_dfl'
p.feed((folder / (name+'.body')).read_text(encoding='utf-8'))
(folder / (name+'.txt')).write_text('\n'.join(p.parts), encoding='utf-8')
print('\n'.join(dict.fromkeys(p.links)))

