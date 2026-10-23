from pathlib import Path
from lxml import html
from pypdf import PdfReader

p = Path('log/20261023/rank_reversal_mechanism/constructive')
doc = html.fromstring((p / 'few_many.body').read_bytes())
for element in doc.xpath('//script|//style|//nav|//footer'):
    element.drop_tree()
(p / 'few_many.text.txt').write_text(doc.text_content(), encoding='utf-8')
with (p / 'biased.body').open('rb') as stream:
    pages = [page.extract_text() for page in PdfReader(stream).pages]
(p / 'biased.text.txt').write_text('\n'.join(pages), encoding='utf-8')
print({'few_many_chars': len(doc.text_content()), 'biased_pages': len(pages)})
