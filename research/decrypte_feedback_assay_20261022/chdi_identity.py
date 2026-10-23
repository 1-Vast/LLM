"""Read exactly permitted Table S1 identity cells; no response payloads."""
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

out = Path('log/20261022/decrypte_molecular_increment/assay')
out.mkdir(parents=True, exist_ok=True)
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with ZipFile('log/20261022/decrypte_source_qualification/supplement.xlsx') as z:
    root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    allowed = {f'{c}139' for c in 'ABCDEF'}
    cells = [c for c in root.findall('.//s:c', ns) if c.get('r') in allowed]
    string_indexes = {int(c.find('s:v', ns).text) for c in cells if c.get('t') == 's'}
    strings = ET.fromstring(z.read('xl/sharedStrings.xml'))
    selected_strings = {i: ''.join(n.itertext()) for i, n in enumerate(strings) if i in string_indexes}
    result = []
    for c in cells:
        v = c.find('s:v', ns)
        result.append({'coordinate': c.get('r'), 'type': c.get('t'),
                       'identity_text': selected_strings[int(v.text)] if c.get('t') == 's' else (v.text if v is not None else None)})
(out / 'CHDI_IDENTITY_CELLS.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
