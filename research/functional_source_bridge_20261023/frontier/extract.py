from html.parser import HTMLParser
from pathlib import Path
class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
root = Path('log/20261023/functional_source_bridge/frontier')
for name in ('ttte2e', 'centaur'):
    parser = Text()
    parser.feed((root / (name + '.body')).read_text(encoding='utf-8'))
    (root / (name + '.text')).write_text(' '.join(' '.join(parser.parts).split()), encoding='utf-8')
