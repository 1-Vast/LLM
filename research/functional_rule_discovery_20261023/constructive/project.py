from pathlib import Path
from lxml import html

folder = Path('log/20261023/functional_rule_discovery/constructive')
root = html.fromstring((folder / 'primary.body').read_bytes())
(folder / 'primary.text.txt').write_text('\n\n'.join(element.text_content() for element in root.xpath('//h1|//h2|//h3|//p')), encoding='utf-8')
