"""Read only selected supplementary workbook sheet names and bounded safe text."""
from pathlib import Path
from io import BytesIO
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def safe(text):
    stripped = text.strip()
    if re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?', stripped):
        return '[numeric text suppressed]'
    if stripped.lower() in {'y','n','s','r','sensitive','resistant','yes','no','positive','negative'}:
        return '[outcome text suppressed]'
    return text

def inspect(mode, member, label, allowed_sheets):
    with zipfile.ZipFile(OUT / 'archive.body') as outer:
        body = outer.read(member)
    with zipfile.ZipFile(BytesIO(body)) as archive:
        rels = {item.attrib['Id']:item.attrib['Target'] for item in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = ET.fromstring(archive.read('xl/workbook.xml')).findall('.//s:sheet',NS)
        result = dict(member=member, sheets=[item.attrib['name'] for item in sheets])
        if mode == 'headers':
            strings = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                strings = ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',NS)
            views = []
            for sheet in sheets:
                if sheet.attrib['name'] not in allowed_sheets:
                    continue
                target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
                target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
                rows = []
                for row in ET.fromstring(archive.read(target)).findall('.//s:row',NS)[:12]:
                    cells = []
                    for cell in list(row)[:40]:
                        record = dict(cell=cell.attrib.get('r'))
                        if cell.find('s:f',NS) is not None:
                            record['formula_suppressed'] = True
                        elif cell.attrib.get('t') == 's':
                            index = int(cell.find('s:v',NS).text)
                            record['text'] = safe(''.join(item.text or '' for item in strings[index].findall('.//s:t',NS)))
                        elif cell.attrib.get('t') == 'inlineStr':
                            record['text'] = safe(''.join(item.text or '' for item in cell.findall('.//s:t',NS)))
                        else:
                            record['numeric_or_other_suppressed'] = True
                        cells.append(record)
                    rows.append(dict(row=row.attrib.get('r'),cells=cells))
                views.append(dict(sheet=sheet.attrib['name'],rows=rows))
            result['views'] = views
            result['scope'] = 'Selected sheets only, first12rows/40cells each; numeric/formula/outcome call text suppressed'
    (OUT / (label+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    inspect(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
