"""Project saved primary HTML without adding a dependency."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261023/dose_update_qualification/sources/quota_primary.body'
if len(sys.argv) > 1:
    SOURCE = ROOT / 'log/20261023/dose_update_qualification/sources' / sys.argv[1]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.hidden += 1
        if not self.hidden and tag in ['p', 'div', 'h1', 'h2', 'h3', 'li', 'br']:
            self.parts.append('\n')
        if tag == 'img' and not self.hidden:
            alt = dict(attrs).get('alt', '')
            if alt:
                self.parts.append(alt)

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


if __name__ == '__main__':
    parser = Text()
    parser.feed(SOURCE.read_text(encoding='utf-8'))
    lines = [' '.join(line.split()) for line in ''.join(parser.parts).splitlines()]
    output = '\n'.join(line for line in lines if line)
    SOURCE.with_suffix('.txt').write_text(output, encoding='utf-8')
    print('Projected characters:', len(output))
