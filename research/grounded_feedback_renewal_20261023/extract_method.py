"""Readable primary HTML with math image alternatives retained."""
from pathlib import Path
import sys
from html.parser import HTMLParser


class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = None
        self.buffer = []
        self.paragraphs = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style', 'nav']:
            self.skip += 1
        if tag in ['h1', 'h2', 'h3', 'h4', 'p']:
            self.active, self.buffer = tag, []
        if tag == 'img' and self.active:
            self.buffer.append(dict(attrs).get('alt', ''))

    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'nav']:
            self.skip -= 1
        if tag == self.active:
            self.paragraphs.append(' '.join(' '.join(self.buffer).split()))
            self.active, self.buffer = None, []

    def handle_data(self, value):
        if self.active and not self.skip:
            self.buffer.append(value)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/grounded_feedback_renewal/root'
label = sys.argv[1]
parser = Reader()
parser.feed((OUT/(label+'.body')).read_text(encoding='utf-8'))
text = '\n\n'.join(parser.paragraphs)
(OUT/(label+'.txt')).write_text(text, encoding='utf-8')
print(text[:14000])
