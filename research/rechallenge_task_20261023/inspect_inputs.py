"""Read only workbook labels/dimensions and ZIP filenames; never assay numbers."""
import io
import json
from pathlib import Path
import posixpath
import zipfile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/rechallenge_task/root'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def project(path):
    with zipfile.ZipFile(path) as archive:
        shared = ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in relationships}
        result = []
        for sheet in workbook.findall('s:sheets/s:sheet', NS):
            target = targets[sheet.attrib[REL]]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            tree = ET.fromstring(archive.read(member))
            labels = []
            for row in tree.findall('s:sheetData/s:row', NS):
                if int(row.attrib['r']) > 3:
                    continue
                for cell in row.findall('s:c', NS):
                    if cell.attrib.get('t') == 's':
                        index = int(cell.find('s:v', NS).text)
                        labels.append(dict(cell=cell.attrib['r'], text=''.join(shared[index].itertext())))
                    elif cell.attrib.get('t') == 'inlineStr':
                        labels.append(dict(cell=cell.attrib['r'], text=''.join(cell.find('s:is', NS).itertext())))
            result.append(dict(sheet=sheet.attrib['name'], dimension=tree.find('s:dimension', NS).attrib,
                               labels_first3rows=labels,
                               formula_count=len(tree.findall('.//s:f', NS))))
        return result


if __name__ == '__main__':
    result = {f'experiment{n}': project(OUT / f'transition_exp{n}.body') for n in (3, 4)}
    with zipfile.ZipFile(OUT / 'transition_supplements.body') as archive:
        result['supplement_members'] = [dict(name=i.filename, bytes=i.file_size) for i in archive.infolist()]
    result['scope'] = 'Only first-three-row text labels, dimensions, formula counts and archive member metadata; no numeric assay responses'
    destination = OUT / 'INPUT_STRUCTURE.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
