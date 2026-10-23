"""Extract bounded methods/data access paragraphs, not numerical response files."""
from pathlib import Path
import xml.etree.ElementTree as ET
root=ET.parse('log/20261023/post_anchor_mechanism/source/elda_full.body').getroot()
terms=['For digital image analysis','Cell viability values underwent','The raw data supporting',
       'An FDA-approved anticancer drug library','Unfortunately, primary ALL cells']
selected=[' '.join(p.itertext()) for p in root.iter('p')
          if any(t in ' '.join(p.itertext()) for t in terms)]
Path('log/20261023/post_anchor_mechanism/source/ELDA_METHODS_SELECTED.txt').write_text('\n\n'.join(selected),encoding='utf8')
