from html.parser import HTMLParser
from pathlib import Path


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


base = Path('D:/MAESTRO/log/20261023/response_law_revision/constructive')
for name in ['symmetry', 'sindy']:
    parser = Text()
    parser.feed((base / (name + '.body')).read_text(encoding='utf-8'))
    (base / (name + '.text.txt')).write_text('\n'.join(parser.parts), encoding='utf-8')
