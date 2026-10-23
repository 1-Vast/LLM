from html.parser import HTMLParser
from pathlib import Path

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

p = Path('log/20261023/functional_error_renewal/frontier')
t = Text()
t.feed((p / 'feta.body').read_text(encoding='utf-8'))
(p / 'feta.txt').write_text('\n'.join(t.parts), encoding='utf-8')
