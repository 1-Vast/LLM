"""Readable primary-source projection; raw receipts remain authoritative."""
from html.parser import HTMLParser
from pathlib import Path
import sys

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

out = Path('D:/MAESTRO/log/20261022/operator_renewal/frontier')
for name in sys.argv[1:]:
    parser = Text()
    parser.feed((out / (name + '.body')).read_text(encoding='utf-8'))
    (out / (name + '.txt')).write_text('\n'.join(parser.parts), encoding='utf-8')
