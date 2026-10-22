"""Offline projection of already-retained landing HTML, no new GET."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/dead_stock_information_gate/root_stack'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.scripts, self.ld, self.meta = [], [], [], []
        self.active = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag == 'meta':
            self.meta.append(a)
        if tag == 'script':
            self.active = {'attrs': a, 'body': ''}

    def handle_data(self, data):
        if self.active is not None:
            self.active['body'] += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.active is not None:
            a = self.active
            self.scripts.append({'attrs': a['attrs'], 'chars': len(a['body']),
                                 'head': a['body'][:120]})
            if 'ld+json' in a['attrs'].get('type', ''):
                self.ld.append(json.loads(a['body']))
            self.active = None


def main():
    raw = (OUT/'stack_landing.body').read_text(encoding='utf-8')
    p = Page()
    p.feed(raw)
    state = re.findall(r'(?:window\.)?[A-Za-z_$][A-Za-z_$0-9]*(?:STATE|State|state)[A-Za-z_$0-9]*\s*=', raw)
    projection = {'links': p.links, 'scripts': p.scripts, 'ld_json': p.ld,
                  'metadata': p.meta, 'state_assignment_names': state,
                  'response_values_accessed': False}
    with (OUT/'LANDING_STRUCTURE.json').open('x', encoding='utf-8') as f:
        json.dump(projection, f, ensure_ascii=False, indent=2)
    print(json.dumps(projection, ensure_ascii=False))


if __name__ == '__main__':
    main()
