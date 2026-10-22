"""Extract published method/design passages from two primary texts."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

BASE = Path('log/20261022/intervention_dynamics_renewal/skeptic')


def txt(node):
    return re.sub(r'\s+', ' ', ''.join(node.itertext())).strip() if node is not None else ''


class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'div':
            if self.depth:
                self.depth += 1
            elif 'ltx_para' in attributes.get('class', '').split():
                self.depth = 1
                self.parts = []

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.paragraphs.append(re.sub(r'\s+', ' ', ' '.join(self.parts)).strip())


def main():
    root = ET.fromstring((BASE / 'AP1_MEMORY_PRIMARY.body').read_bytes())
    article = root.find('.//article')
    if article is None:
        article = root
    keys = re.compile(r'withdraw|wash|rechall|expos|treat|revers|reporter|p300|CBP|accession|GSE|zenodo|available|RNA.seq|ATAC|single.cell|flow cyt|KRAS|memory', re.I)
    bio = {'title': txt(article.find('.//article-title')), 'sections': [], 'availability': [], 'supplements': []}
    for sec in article.findall('.//sec'):
        title = txt(sec.find('title'))
        paragraphs = [txt(p) for p in sec.findall('p') if keys.search(txt(p))]
        if paragraphs:
            bio['sections'].append({'title': title, 'paragraphs': paragraphs})
        if 'availab' in title.lower():
            bio['availability'].append({'title': title, 'text': txt(sec)})
    bio['supplements'] = [txt(v) for v in article.findall('.//supplementary-material')]
    bio['figures'] = [{'id': v.attrib.get('id'), 'caption': txt(v.find('caption'))} for v in article.findall('.//fig')]
    bio['availability_notes'] = [{'title': txt(v.find('title')), 'text': txt(v)}
                                 for v in article.findall('.//notes')
                                 if 'availability' in txt(v.find('title')).lower()]
    (BASE / 'AP1_PRIMARY_METHODS.json').write_text(json.dumps(bio, ensure_ascii=False, indent=2), encoding='utf-8')
    parser = ParagraphParser()
    parser.feed((BASE / 'DEEP_OSG_PRIMARY.body').read_text(encoding='utf-8'))
    math = [{'paragraph': index, 'text': text} for index, text in enumerate(parser.paragraphs)
            if re.search(r'semigroup|loss function|autonomous|random|control|regulariz|consisten|generator|variance', text, re.I)]
    (BASE / 'DEEP_OSG_PRIMARY_METHODS.json').write_text(json.dumps(math, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'bio_title': bio['title'], 'bio_availability': bio['availability_notes'], 'math_paragraphs': len(math)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
