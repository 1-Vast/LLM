"""Exact root-approved design identities; no response column or R code execution."""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import ap1_identity_stage1 as first


STRING = {'s', 'inlineStr', 'str'}
IDENTITY = STRING | {'n'}


def policy():
    result = {}

    def add(sheet, region, field, types):
        positions = result.setdefault(sheet, {})
        a, b = map(first.coordinate, region.split(':'))
        for row in range(a[1], b[1]+1):
            for column in range(a[0], b[0]+1):
                positions[f'{first.column_name(column)}{row}'] = {'field': field, 'allowed_types': sorted(types)}

    for column, field in [('D', 'Name'), ('F', 'exp'), ('H', 'condition_dictionary')]:
        add('Figure 2g', f'{column}{3 if column == "H" else 4}:{column}21', field, STRING)
    for column, field, types in [('B', 'exp_id', IDENTITY), ('C', 'Id', STRING), ('E', 'XY', {'n'}),
                                 ('F', 'Z', {'n'}), ('G', 'Time_design_frame', {'n'}),
                                 ('S', 'sample_identifier', IDENTITY), ('T', 'dataset_identifier', IDENTITY)]:
        add('Figure 3b', f'{column}3:{column}10868', field, types)
    add('Figure 3b summary', 'D5:D100', 'dataset_identifier', IDENTITY)
    add('Figure 3b summary', 'E5:E100', 'sample_identifier', IDENTITY)
    for sheet, last in [('Figure 5b', 241), ('Figure 5c', 226)]:
        for column, field in zip('CDEFGHI', ['condition', 'XY', 'Z', 'Time_design_frame', 'Tags', 'Shape', 'Name']):
            add(sheet, f'{column}2:{column}{last}', field, IDENTITY)
    for column, field in zip('FGH', ['XY', 'Z', 'Time_design_frame']):
        add('Figure 4c', f'{column}5:{column}78', field, {'n'})
    add('Figure 4e', 'D4:I6', 'alignment_string_candidate', STRING)
    add('Figure 4e', 'D54:I58', 'alignment_string_candidate', STRING)
    for column, field in [('E', 'generation_or_lineage_string'), ('I', 'file_id_string')]:
        for start, end in [(6, 54), (56, 102)]:
            add('Figure 4e', f'{column}{start}:{column}{end}', field, STRING)
    return result


def read_identity(path, allowed):
    output, indices = {}, set()
    with zipfile.ZipFile(path) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = {e.attrib['Id']: e.attrib['Target'] for e in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        paths = {}
        for sheet in book.findall('m:sheets/m:sheet', first.NS):
            if sheet.attrib['name'] in allowed:
                target = rels[sheet.attrib[first.REL_ID]]
                paths[sheet.attrib['name']] = str(PurePosixPath('xl')/target) if not target.startswith('/') else target.lstrip('/')
        if set(paths) != set(allowed):
            raise ValueError('missing_target_sheet')
        for name, positions in allowed.items():
            cells, merges = {}, []
            with archive.open(paths[name]) as handle:
                for _, node in ET.iterparse(handle, events=('end',)):
                    tag = node.tag.rsplit('}', 1)[-1]
                    if tag == 'mergeCell':
                        merges.append(node.attrib['ref'])
                    elif tag == 'c':
                        location = node.attrib.get('r')
                        if location in positions:
                            if location in cells:
                                raise ValueError('duplicate_authorized_coordinate')
                            spec = positions[location]
                            kind = node.attrib.get('t', 'n')
                            formula = node.find('m:f', first.NS) is not None
                            item = {'coordinate': location, 'field': spec['field'], 'type': 'formula' if formula else kind,
                                    'value_opened': False}
                            if not formula and kind in spec['allowed_types']:
                                if kind == 's':
                                    index = node.findtext('m:v', default='', namespaces=first.NS)
                                    if not re.fullmatch('[0-9]+', index):
                                        raise ValueError('invalid_shared_index')
                                    item['shared_string_index'] = int(index)
                                    indices.add(int(index))
                                elif kind == 'inlineStr':
                                    inline = node.find('m:is', first.NS)
                                    nodes = [] if inline is None else inline.findall('m:t', first.NS)+inline.findall('m:r/m:t', first.NS)
                                    item['value'] = ''.join(t.text or '' for t in nodes)
                                else:
                                    value = node.find('m:v', first.NS)
                                    if value is not None:
                                        item['value'] = value.text or ''
                                item['value_opened'] = 'shared_string_index' in item or 'value' in item
                            cells[location] = item
                        node.clear()
                    elif tag == 'row':
                        node.clear()
            for location, spec in positions.items():
                cells.setdefault(location, {'coordinate': location, 'field': spec['field'], 'type': 'absent', 'value_opened': False})
            output[name] = {'cells': cells, 'merge_ranges': merges}
        if indices:
            with archive.open('xl/sharedStrings.xml') as handle:
                shared = first.selected_shared_strings(handle, indices)
        else:
            shared = {}
        for sheet in output.values():
            for item in sheet['cells'].values():
                if 'shared_string_index' in item:
                    item['value'] = shared[item['shared_string_index']]
            sheet['type_counts'] = dict(Counter(item['type'] for item in sheet['cells'].values()))
        return {'sheets': output, 'decoded_shared_string_indices': sorted(indices), 'response_fields_opened': False,
                'numeric_identity_literals_only': True, 'Time_interpretation': 'raw design frame; not automatically biological days'}


def freeze():
    if first.sha(first.RAW) != first.EXPECTED:
        raise ValueError('source_hash_mismatch')
    tests = json.loads((first.OUT/'STAGE2_SYNTHETIC_TESTS.json').read_text(encoding='utf-8'))
    if not tests['success']:
        raise ValueError('synthetic_tests_not_passed')
    files = [first.OUT/'STAGE2_PROTOCOL.md', Path(__file__), Path(first.__file__),
             Path(__file__).with_name('test_ap1_identity_stage2.py'), first.OUT/'STAGE2_SYNTHETIC_TESTS.json',
             first.OUT/'STAGE1_STRINGS.json', first.OUT/'FIELD_ROLES.json']
    first.write('STAGE2_FREEZE.json', {'utc': first.utc(), 'source_sha256': first.EXPECTED,
                                     'policy_sha256': hashlib.sha256(json.dumps(policy(), sort_keys=True).encode()).hexdigest(),
                                     'files': [{'path': str(p), 'sha256': first.sha(p)} for p in files]})


def run():
    frozen = json.loads((first.OUT/'STAGE2_FREEZE.json').read_text(encoding='utf-8'))
    if first.sha(first.RAW) != first.EXPECTED or any(first.sha(f['path']) != f['sha256'] for f in frozen['files']):
        raise ValueError('frozen_input_changed')
    first.write('STAGE2_READ_STARTED.json', {'utc': first.utc(), 'source_sha256': first.EXPECTED})
    result = read_identity(first.RAW, policy())
    checks = [{'path': f['path'], 'unchanged': first.sha(f['path']) == f['sha256']} for f in frozen['files']]
    if first.sha(first.RAW) != first.EXPECTED or not all(c['unchanged'] for c in checks):
        raise ValueError('frozen_input_changed_after_read')
    result.update({'utc': first.utc(), 'status': 'STAGE2_EXACT_IDENTITIES_ONLY_COMPLETE', 'source_sha256': first.EXPECTED,
                   'frozen_checks': checks, 'network_requests': 0})
    first.write('STAGE2_IDENTITIES.json', result)
    print(json.dumps({'status': result['status'], 'sheets': {name: {'type_counts': sheet['type_counts'], 'opened': sum(i['value_opened'] for i in sheet['cells'].values())} for name, sheet in result['sheets'].items()}}))


if __name__ == '__main__':
    try:
        {'freeze': freeze, 'run': run}[sys.argv[1]]()
    except Exception as error:
        if not (first.OUT/'STAGE2_FAILURE.json').exists():
            first.write('STAGE2_FAILURE.json', {'utc': first.utc(), 'status': 'STOP_IDENTITY_STAGE2_FAILURE', 'error_type': type(error).__name__})
        raise
