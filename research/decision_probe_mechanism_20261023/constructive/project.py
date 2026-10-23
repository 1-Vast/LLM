from pathlib import Path
from html.parser import HTMLParser


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

base = Path('D:/MAESTRO/log/20261023/decision_probe_mechanism/constructive')
for name in ['directional', 'proxies', 'opo']:
    parser = Text()
    parser.feed((base / (name + '.body')).read_text(encoding='utf-8'))
    (base / (name + '.text.txt')).write_text('\n'.join(parser.parts), encoding='utf-8')
