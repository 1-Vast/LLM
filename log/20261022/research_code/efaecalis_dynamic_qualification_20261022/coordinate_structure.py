"""Read coordinate/type/value-presence metadata only, never numerical text."""
import json
import posixpath
import xml.etree.ElementTree as ET
import zipfile

import redirect_followup as follow
import source_schema as source


def main():
    network = json.loads((follow.OUT / 'NETWORK.json').read_text(encoding='utf-8'))
    path = source.Path(network['raw_path'])
    before = source.sha(path)
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels}
        records = []
        for s in workbook.findall('m:sheets/m:sheet', source.NS):
            if s.attrib['name'] not in {'Fig1B', 'Fig4B'}:
                continue
            target = targets[s.attrib[source.RID]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            with z.open(target) as stream:
                for _, cell in ET.iterparse(stream, events=('end',)):
                    if cell.tag != '{' + source.NS['m'] + '}c':
                        continue
                    coordinate = cell.attrib.get('r', '')
                    if cell.attrib.get('t', 'n') == 'n' and cell.find('m:v', source.NS) is not None:
                        rows.append(coordinate)
                    cell.clear()
            records.append({'sheet': s.attrib['name'], 'numeric_typed_coordinates_with_value_node_only': rows})
    after = source.sha(path)
    if after != before:
        raise RuntimeError('source_changed')
    source.write_json(follow.OUT / 'NUMERIC_COORDINATE_STRUCTURE.json', {'source_sha256_before': before,
        'source_sha256_after': after, 'numeric_values_interpreted': False, 'sheets': records})
    selected = []
    for item in records:
        if item['sheet'] == 'Fig4B':
            byrow = {}
            for c in item['numeric_typed_coordinates_with_value_node_only']:
                row = source.re.search(r'\d+$', c)[0]
                byrow.setdefault(row, []).append(c)
            selected = [{'row': k, 'numeric_value_node_coordinates': v} for k, v in byrow.items()]
    print(json.dumps({'Fig4B_coordinate_structure_only': selected}))


if __name__ == '__main__':
    main()
