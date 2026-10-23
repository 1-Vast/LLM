from pathlib import Path
from lxml import html

p = Path('log/20261023/grounded_feedback_renewal/constructive')
doc = html.fromstring((p / 'primary.body').read_bytes())
for element in doc.xpath('//script|//style|//nav|//footer'):
    element.drop_tree()
(p / 'primary.text.txt').write_text(doc.text_content(), encoding='utf-8')
