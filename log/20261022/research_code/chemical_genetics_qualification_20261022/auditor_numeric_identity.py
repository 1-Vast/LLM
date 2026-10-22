"""Access numeric values only at exact Fig.5a E2:E61 identity coordinates."""
from decimal import Decimal, InvalidOperation
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import auditor_identity_followup as prior

BASE = prior.base
OUT = BASE.OUT.parent / 'numeric_identity'
COORDS = {f'E{row}' for row in range(2, 62)}
EXPECTED = {(lineage, day) for lineage in range(1, 13) for day in (2, 3, 5, 7, 10)}


class IdentityFailure(Exception):
    def __init__(self, reason, coordinate=None):
        self.reason = reason
        self.coordinate = coordinate
        super().__init__(reason)


def read_days(path):
    """Never retrieve value/formula text from cells outside the exact scope."""
    values = {}
    with zipfile.ZipFile(path, 'r') as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = [s for s in workbook.findall('m:sheets/m:sheet', BASE.NS) if s.attrib['name'] == 'Fig.5a']
        if len(sheets) != 1:
            raise IdentityFailure('sheet_absent_or_ambiguous')
        rel_id = sheets[0].attrib[BASE.REL_NS]
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = [r.attrib['Target'] for r in rels if r.attrib['Id'] == rel_id and r.attrib.get('TargetMode') != 'External']
        if len(targets) != 1:
            raise IdentityFailure('sheet_relationship_absent_or_ambiguous')
        target = targets[0]
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        with archive.open(target) as source:
            for _, cell in ET.iterparse(source, events=('end',)):
                if cell.tag != '{' + BASE.NS['m'] + '}c':
                    continue
                coordinate = cell.attrib.get('r', '')
                if coordinate not in COORDS:
                    cell.clear()
                    continue
                if coordinate in values:
                    raise IdentityFailure('duplicate_allowed_coordinate', coordinate)
                if cell.attrib.get('t', 'n') != 'n' or cell.find('m:f', BASE.NS) is not None:
                    raise IdentityFailure('allowed_cell_not_plain_numeric', coordinate)
                node = cell.find('m:v', BASE.NS)
                if node is None or node.text is None:
                    raise IdentityFailure('allowed_cell_value_absent', coordinate)
                try:
                    value = Decimal(node.text)
                    if not value.is_finite() or value != value.to_integral_value():
                        raise IdentityFailure('day_not_finite_integer', coordinate)
                except InvalidOperation:
                    raise IdentityFailure('day_not_numeric', coordinate) from None
                values[coordinate] = int(value)
                cell.clear()
    missing = COORDS - set(values)
    if missing:
        raise IdentityFailure('allowed_coordinate_missing', sorted(missing, key=lambda c: int(c[1:]))[0])
    return values


def compare(days, safe_cells):
    rows = []
    keys = []
    for row in range(2, 62):
        b, c, d = (safe_cells.get(f'{column}{row}', '').strip() for column in ('B', 'C', 'D'))
        match = re.fullmatch(r'Tetracycline (\d+)/Azithromycin/(\d+)', b)
        if match is None:
            raise IdentityFailure('safe_B_identity_invalid', f'B{row}')
        lineage, encoded_day = map(int, match.groups())
        if c != f'Tetracycline {lineage}' or d != 'Azithromycin':
            raise IdentityFailure('safe_C_D_identity_conflict', f'B{row}')
        if days[f'E{row}'] != encoded_day:
            raise IdentityFailure('numeric_day_string_mismatch', f'E{row}')
        keys.append((lineage, encoded_day))
        rows.append({'row': row, 'B_coordinate': f'B{row}', 'B_identity': b,
                     'lineage': lineage, 'day_from_B': encoded_day,
                     'E_coordinate': f'E{row}', 'day_from_E': days[f'E{row}'], 'row_match': True})
    if len(set(keys)) != len(keys):
        raise IdentityFailure('duplicate_lineage_day_key')
    if set(keys) != EXPECTED:
        raise IdentityFailure('lineage_day_product_mismatch')
    return rows


def main():
    failure_path = OUT / 'FAILURE.json'
    try:
        freeze = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8-sig'))
        prechecks = [{'path': f['path'], 'unchanged': BASE.sha(f['path']) == f['sha256']} for f in freeze['files']]
        if not all(c['unchanged'] for c in prechecks):
            raise IdentityFailure('frozen_input_changed_before_census')
        provenance = json.loads((prior.OUT / 'EXTRACTION.json').read_text(encoding='utf-8'))
        path = BASE.Path(provenance['path'])
        before = BASE.sha(path)
        if before != provenance['sha256']:
            raise IdentityFailure('workbook_provenance_hash_mismatch')
        projection = json.loads((prior.OUT / 'STRING_IDENTITIES.json').read_text(encoding='utf-8'))
        books = [b for b in projection if BASE.Path(b['source_path']).name == prior.EXTRA]
        sheets = [s for b in books for s in b['sheets'] if s['sheet_name'] == 'Fig.5a']
        if len(sheets) != 1:
            raise IdentityFailure('safe_string_sheet_absent_or_ambiguous')
        safe = {c['coordinate']: c['text'] for c in sheets[0]['string_cells'] if 'text' in c}
        days = read_days(path)
        rows = compare(days, safe)
        checks = [{'path': f['path'], 'unchanged': BASE.sha(f['path']) == f['sha256']} for f in freeze['files']]
        if BASE.sha(path) != before or not all(c['unchanged'] for c in checks):
            raise IdentityFailure('input_changed_during_census')
        result = {'utc': BASE.utc(), 'status': 'SEALED_IDENTITY_ONLY', 'http_requests': 0,
            'runtime': sys.executable, 'source_path': str(path), 'source_sha256_before': before,
            'source_sha256_after': BASE.sha(path), 'exact_numeric_access_scope': 'Fig.5a!E2:E61',
            'numeric_value_coordinates_accessed': sorted(days, key=lambda c: int(c[1:])),
            'other_numeric_values_accessed': False, 'response_F_G_values_accessed': False,
            'numeric_day_string_all_rows_match': True, 'rows_verified': len(rows),
            'lineages': list(range(1, 13)), 'days': [2, 3, 5, 7, 10],
            'unique_keys': len({(r['lineage'], r['day_from_E']) for r in rows}),
            'duplicate_keys': [], 'missing_expected_keys': [], 'unexpected_keys': [],
            'rows': rows, 'frozen_files_unchanged': checks,
            'limits': 'Only lineage/day identity sealed; prior qualitative outcomes are design-exposed; no genomic state or F target semantics certified.'}
        BASE.write_json(OUT / 'CENSUS.json', result)
        print(json.dumps({k: result[k] for k in ['status', 'http_requests', 'exact_numeric_access_scope', 'rows_verified', 'lineages', 'days', 'unique_keys', 'numeric_day_string_all_rows_match']}))
        return 0
    except Exception as error:
        failure = {'utc': BASE.utc(), 'status': 'FAILED_RETAINED', 'error_type': type(error).__name__, 'http_requests': 0}
        if isinstance(error, IdentityFailure):
            failure.update({'reason': error.reason, 'coordinate': error.coordinate})
        BASE.write_json(failure_path, failure)
        print(json.dumps(failure))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
