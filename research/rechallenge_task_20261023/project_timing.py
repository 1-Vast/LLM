"""Project recorded sample times and schedule labels, excluding response column B."""
import json
from pathlib import Path
import posixpath
import zipfile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/rechallenge_task/root'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

if __name__ == '__main__':
    projected = {}
    for number in (3, 4):
        sheets = []
        with zipfile.ZipFile(OUT / f'transition_exp{number}.body') as archive:
            shared = ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)
            targets = {e.attrib['Id']: e.attrib['Target'] for e in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
            workbook = ET.fromstring(archive.read('xl/workbook.xml'))
            for sheet in workbook.findall('s:sheets/s:sheet', NS):
                target = targets[sheet.attrib[REL]]
                member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
                tree = ET.fromstring(archive.read(member))
                selected = []
                for row in tree.findall('s:sheetData/s:row', NS):
                    if int(row.attrib['r']) < 4:
                        continue
                    record = dict(row=int(row.attrib['r']))
                    for cell in row.findall('s:c', NS):
                        column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                        # A is physical measurement time; C a death-modality
                        # schedule label; D a declared SIMULATION input time.
                        if column not in ('A', 'C', 'D'):
                            continue
                        value = cell.find('s:v', NS)
                        if value is None:
                            continue
                        if cell.attrib.get('t') == 's':
                            text = ''.join(shared[int(value.text)].itertext())
                        else:
                            text = value.text
                        record[column] = text
                    selected.append(record)
                sheets.append(dict(sheet=sheet.attrib['name'], selected_design_rows=selected))
        projected[str(number)] = sheets
    projected['scope'] = 'Design text only; A actual measurement times, C schedule labels, D simulation input times. No B density, E simulated death or F simulated measurement values decoded. D not authenticated physical administration times.'
    destination = OUT / 'TIMING_DESIGN.json'
    assert not destination.exists()
    destination.write_text(json.dumps(projected, indent=2), encoding='utf-8')
    print(json.dumps(projected, indent=2))
