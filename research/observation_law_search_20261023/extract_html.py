"""Stdlib HTML text extraction for reading saved identification originals."""
from html.parser import HTMLParser
from pathlib import Path


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


if __name__ == '__main__':
    base = Path(__file__).resolve().parents[2] / 'log/20261023/observation_law_search/root_sources'
    for name in ['drift_identification', 'gradient_identification']:
        parser = TextParser()
        parser.feed((base / (name + '.fulltext.body')).read_text(encoding='utf-8'))
        (base / (name + '.txt')).write_text('\n'.join(parser.parts), encoding='utf-8')
        print(name)
