"""Coordinate-limited string reader; numeric/formula/error/boolean values stay closed."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
from xml.parsers import expat
import zipfile


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/intervention_dynamics_renewal'
OUT = BASE / 'ap1_identity'
RAW = BASE / 'root_scout/AP1_mainfigures_sourcedata_AutoRecovered.raw.xlsx'
EXPECTED = '6bcdbdd451e29246c5db16e9a67c43abf937e7cf3fb8796931d83096feaff42a'
SCOPE = {'Figure 2b': 'A2:F16', 'Figure 2g': 'B2:H21', 'Figure 3b': 'A2:AE10868',
         'Figure 3b summary': 'B3:L100', 'Figure 4c': 'B4:AT78', 'Figure 4e': 'A4:L102',
         'Figure 5b': 'A1:X241', 'Figure 5c': 'A1:X226'}
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    with (OUT/name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)


def coordinate(name):
    match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', name)
    if not match:
        raise ValueError('invalid_coordinate')
    column = 0
    for char in match[1]:
        column = column*26+ord(char)-64
    return column, int(match[2])


def column_name(number):
    result = ''
    while number:
        number, remainder = divmod(number-1, 26)
        result = chr(65+remainder)+result
    return result


def allowed_positions(dimension):
    first, last = map(coordinate, dimension.split(':'))
    positions = {}
    for row in range(first[1], last[1]+1):
        for column in range(first[0], last[0]+1):
            roles = []
            if row < first[1]+5:
                roles.append('header')
            if column < first[0]+2:
                roles.append('identity_candidate')
            if roles:
                positions[f'{column_name(column)}{row}'] = roles
    return positions


def selected_shared_strings(handle, indices):
    """SAX character capture is enabled only inside selected si/t nodes."""
    found, index, capture, in_text, phonetic = {}, -1, False, False, 0
    parts = []
    parser = expat.ParserCreate(namespace_separator='}')

    def start(name, attributes):
        nonlocal index, capture, in_text, phonetic, parts
        tag = name.rsplit('}', 1)[-1]
        if tag == 'si':
            index += 1
            capture, parts = index in indices, []
        elif tag == 'rPh':
            phonetic += 1
        elif tag == 't':
            in_text = capture and phonetic == 0

    def end(name):
        nonlocal capture, in_text, phonetic
        tag = name.rsplit('}', 1)[-1]
        if tag == 't':
            in_text = False
        elif tag == 'rPh':
            phonetic -= 1
        elif tag == 'si' and capture:
            found[index] = ''.join(parts)
            capture = False

    def characters(value):
        if in_text:
            parts.append(value)

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler = characters
    while chunk := handle.read(65536):
        parser.Parse(chunk, False)
    parser.Parse(b'', True)
    if set(found) != set(indices):
        raise ValueError('missing_selected_shared_string')
    return found


def read_stage1(path, scope):
    sheets, requested = {}, set()
    with zipfile.ZipFile(path) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {e.attrib['Id']: e.attrib['Target'] for e in rels}
        paths = {}
        for sheet in book.findall('m:sheets/m:sheet', NS):
            if sheet.attrib['name'] in scope:
                target = targets[sheet.attrib[REL_ID]]
                paths[sheet.attrib['name']] = str(PurePosixPath('xl')/target) if not target.startswith('/') else target.lstrip('/')
        if set(paths) != set(scope):
            raise ValueError('missing_target_sheet')
        for name, dimension in scope.items():
            positions = allowed_positions(dimension)
            observed, strings, merges, actual_dimension = {}, {}, [], None
            with archive.open(paths[name]) as handle:
                for _, node in ET.iterparse(handle, events=('end',)):
                    tag = node.tag.rsplit('}', 1)[-1]
                    if tag == 'dimension':
                        actual_dimension = node.attrib['ref']
                    elif tag == 'mergeCell':
                        merges.append(node.attrib['ref'])
                    elif tag == 'c':
                        location = node.attrib.get('r')
                        if location in positions:
                            if location in observed:
                                raise ValueError('duplicate_authorized_coordinate')
                            kind = node.attrib.get('t', 'n')
                            formula = node.find('m:f', NS) is not None
                            observed[location] = {'coordinate': location, 'roles': positions[location],
                                                  'type': 'formula' if formula else kind,
                                                  'ooxml_type': kind, 'formula_present': formula}
                            if not formula and kind == 's':
                                index_text = node.findtext('m:v', default='', namespaces=NS)
                                if not re.fullmatch('[0-9]+', index_text):
                                    raise ValueError('invalid_shared_string_index')
                                index = int(index_text)
                                strings[location] = {'shared_string_index': index}
                                requested.add(index)
                            elif not formula and kind == 'inlineStr':
                                inline = node.find('m:is', NS)
                                text_nodes = [] if inline is None else inline.findall('m:t', NS)+inline.findall('m:r/m:t', NS)
                                strings[location] = {'text': ''.join(t.text or '' for t in text_nodes)}
                            elif not formula and kind == 'str':
                                strings[location] = {'text': node.findtext('m:v', default='', namespaces=NS)}
                        node.clear()
                    elif tag == 'row':
                        node.clear()
            if actual_dimension != dimension:
                raise ValueError('used_range_changed')
            cells = [observed.get(location, {'coordinate': location, 'roles': roles, 'type': 'absent'})
                     for location, roles in positions.items()]
            sheets[name] = {'used_range': dimension, 'merge_ranges': merges, 'authorized_cells': cells,
                            'strings': strings, 'type_counts': dict(Counter(c['type'] for c in cells))}
        if requested:
            with archive.open('xl/sharedStrings.xml') as handle:
                shared = selected_shared_strings(handle, requested)
        else:
            shared = {}
        for sheet in sheets.values():
            output = []
            metadata = {cell['coordinate']: cell for cell in sheet['authorized_cells']}
            for location, item in sheet['strings'].items():
                text = shared[item['shared_string_index']] if 'shared_string_index' in item else item['text']
                if text:
                    output.append({'coordinate': location, 'roles': metadata[location]['roles'], 'text': text,
                                   'type': metadata[location]['type'],
                                   **({'shared_string_index': item['shared_string_index']} if 'shared_string_index' in item else {})})
            sheet['strings'] = output
        return {'sheets': sheets, 'decoded_shared_string_indices': sorted(requested),
                'decoded_shared_string_count': len(shared), 'numeric_values_interpreted': False,
                'formulas_interpreted': False, 'finite_gate_performed': False}


def freeze():
    if sha(RAW) != EXPECTED:
        raise ValueError('source_hash_mismatch')
    tests = json.loads((OUT/'SYNTHETIC_TESTS.json').read_text(encoding='utf-8'))
    if not tests['success']:
        raise ValueError('synthetic_tests_not_passed')
    paths = [OUT/'PROTOCOL.md', Path(__file__), Path(__file__).with_name('test_ap1_identity_stage1.py'),
             OUT/'SYNTHETIC_TESTS.json', BASE/'skeptic/AP1_MINIMUM_IDENTITY_SCOPE.md',
             BASE/'root_scout/AP1_WORKBOOK_STRUCTURE.json']
    write('FREEZE.json', {'utc': utc(), 'source_sha256': EXPECTED, 'scope': SCOPE,
                         'files': [{'path': str(p), 'sha256': sha(p)} for p in paths]})


def run():
    frozen = json.loads((OUT/'FREEZE.json').read_text(encoding='utf-8'))
    if sha(RAW) != EXPECTED or frozen['scope'] != SCOPE or any(sha(f['path']) != f['sha256'] for f in frozen['files']):
        raise ValueError('frozen_input_changed')
    write('READ_STARTED.json', {'utc': utc(), 'stage': 1, 'source_sha256': EXPECTED})
    result = read_stage1(RAW, SCOPE)
    result.update({'utc': utc(), 'status': 'STAGE1_STRINGS_ONLY_COMPLETE', 'source_sha256': EXPECTED})
    if sha(RAW) != EXPECTED or any(sha(f['path']) != f['sha256'] for f in frozen['files']):
        raise ValueError('frozen_input_changed_after_read')
    write('STAGE1_STRINGS.json', result)
    print(json.dumps({'status': result['status'], 'sheets': {n: {'strings': len(s['strings']), 'type_counts': s['type_counts']} for n, s in result['sheets'].items()}}))


if __name__ == '__main__':
    try:
        {'freeze': freeze, 'run': run}[sys.argv[1]]()
    except Exception as error:
        if not (OUT/'FAILURE.json').exists():
            write('FAILURE.json', {'utc': utc(), 'error_type': type(error).__name__, 'status': 'STOP_STAGE1_FAILURE'})
        raise
