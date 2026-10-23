"""Read only assay-method narrative from authenticated DOCX, no table bodies."""
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from attachment import OUT, NS

if __name__ == '__main__':
    with zipfile.ZipFile(OUT/'mmc2_authenticated.docx') as archive:
        document = ET.fromstring(archive.read('word/document.xml'))
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', NS))
                  for p in document.findall('.//w:body/w:p', NS)]
    matches = [{'paragraph': i, 'text': text} for i, text in enumerate(paragraphs)
               if re.search(r'CellTiter|drug screen|dose.response|area under|normaliz|Z.factor|Z.?prime|DMSO|100 compound', text, re.I)]
    target = OUT/'ASSAY_METHOD_PARAGRAPHS.json'
    assert not target.exists()
    target.write_text(json.dumps(matches, indent=2), encoding='utf-8')
    print(json.dumps(matches, indent=2))
