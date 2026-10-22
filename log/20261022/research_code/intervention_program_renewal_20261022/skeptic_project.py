"""Project retained primary HTML method paragraphs, with stable source anchors."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from html.parser import HTMLParser


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.active = []

    def handle_starttag(self, tag, attrs):
        if tag in ('h1', 'h2', 'h3', 'h4', 'p', 'title'):
            item = {'tag': tag, 'id': dict(attrs).get('id'), 'parts': []}
            self.active.append(item)

    def handle_data(self, data):
        for item in self.active:
            item['parts'].append(data)

    def handle_endtag(self, tag):
        for index in range(len(self.active) - 1, -1, -1):
            if self.active[index]['tag'] == tag:
                item = self.active.pop(index)
                item['text'] = re.sub(r'\s+', ' ', ' '.join(item.pop('parts'))).strip()
                self.items.append(item)
                break

OUT = Path('log/20261022/intervention_program_renewal/skeptic')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('pattern')
    args = parser.parse_args()
    source = OUT / f'{args.label}.body'
    body = source.read_bytes()
    parsed = Paragraphs()
    parsed.feed(body.decode('utf-8', errors='replace'))
    selected = []
    for index, item in enumerate(parsed.items):
        if re.search(args.pattern, item['text'], re.I):
            selected.append({'ordinal': index, **item})
    record = {'source': str(source), 'sha256': hashlib.sha256(body).hexdigest(),
              'title': next((item['text'] for item in parsed.items if item['tag'] == 'title'), None),
              'pattern': args.pattern, 'paragraphs': selected}
    path = OUT / f'{args.label}_PROJECTION.json'
    if path.exists():
        raise RuntimeError('Do not overwrite a projection')
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
