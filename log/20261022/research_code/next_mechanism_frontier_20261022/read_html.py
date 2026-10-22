"""Render acquired arXiv primary text, preserving math alttext."""
from html.parser import HTMLParser
from pathlib import Path

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.math_depth = 0
    def handle_starttag(self, tag, attrs):
        if tag == 'math':
            self.math_depth += 1
            self.parts.append(dict(attrs).get('alttext', ''))
        if tag in ('p', 'section', 'h1', 'h2', 'h3', 'tr'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag == 'math':
            self.math_depth -= 1
    def handle_data(self, data):
        if not self.math_depth:
            self.parts.append(data)

if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[2] / 'log/20261022/next_mechanism/frontier/sources'
    parser = Reader()
    parser.feed((folder / 'idtd_html.body').read_text(encoding='utf-8'))
    (folder / 'idtd_html.txt').write_text(''.join(parser.parts), encoding='utf-8')
