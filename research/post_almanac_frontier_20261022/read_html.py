from html.parser import HTMLParser
from pathlib import Path

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

base = Path('log/20261022/post_almanac_mechanism/frontier/sources')
for name in ['amortized_reasoning', 'biology_loop', 'deep_screening']:
    reader = Reader()
    reader.feed((base / (name + '.txt')).read_text(encoding='utf8'))
    text = ' '.join(' '.join(reader.parts).split())
    (base / (name + '.readable.txt')).write_text(text, encoding='utf8')
    print('\nSOURCE', name, '\n', text[:24000])
