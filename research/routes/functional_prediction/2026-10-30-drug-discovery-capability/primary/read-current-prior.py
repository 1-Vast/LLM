from pathlib import Path
import xml.etree.ElementTree as ET
p=Path(r'D:\MAESTRO\reference\papers\doi-10.1038-s41467-026-75772-5\supp-p03.body')
r=ET.fromstring(p.read_bytes())
for el in r.iter('p'):
 if any(x.attrib.get('rid')=='CR12' for x in el.iter('xref')):
  print(el.attrib, ''.join(el.itertext()))
