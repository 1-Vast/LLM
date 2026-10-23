"""Expose original article paragraphs, without downloading experimental data."""
from pathlib import Path
import xml.etree.ElementTree as ET

out = Path(__file__).resolve().parents[3] / 'log/20261023/feedback_sufficiency_renewal/critic'
root = ET.fromstring((out / 'primary2.body').read_bytes())
lines = [' '.join(''.join(node.itertext()).split()) for node in root.iter()
         if node.tag in ('article-title', 'p', 'title')]
(out / 'PRIMARY_TEXT.txt').write_text('\n\n'.join(lines), encoding='utf-8')
for i, line in enumerate(lines):
    if any(x in line.lower() for x in ('predict', 'learning', 'availability', 'gse', 'github', 'algorithm')):
        print(i, line)
