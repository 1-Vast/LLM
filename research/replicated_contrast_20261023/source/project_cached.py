"""Project cached publisher design/caption and supplement-link metadata only."""
import json
from pathlib import Path
from lxml import html

out = Path('log/20261023/replicated_contrast/source')
source = Path('log/20261023/function_update_renewal/root_sources/multilineage.body')
tree = html.fromstring(source.read_bytes())
links = []
for a in tree.xpath('//a[@href]'):
    if 'MOESM' in a.get('href'):
        links.append(dict(url=a.get('href'), caption=' '.join(a.getparent().itertext())))
paragraphs = []
for p in tree.xpath('//p'):
    text = ' '.join(p.itertext())
    if ('guide pairs' in text and 'replicates' in text) or 'Reproducibility and validation of fitness' in text or text.startswith('The read counts for all screening data'):
        paragraphs.append(text)
report = dict(source=str(source), supplement_links=links, design_paragraphs=paragraphs,
              count_values_read=False, actual_sample_header_read=False)
(out/'CACHED_SOURCE_PROJECTION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
