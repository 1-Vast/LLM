"""Readable original JATS projection, no experimental payload."""
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path('D:/MAESTRO/log/20261023/functional_state_sufficiency/biology')
root = ET.fromstring((OUT/'primary.body').read_bytes())
text = '\n\n'.join(' '.join(''.join(node.itertext()).split())
                    for node in root.iter() if node.tag in {'p', 'title', 'caption'})
(OUT/'PRIMARY_TEXT.txt').write_text(text, encoding='utf-8')
print(text)
