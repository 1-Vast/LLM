"""Strict coordinate allowlist for finite identity/design numbers only."""
from decimal import Decimal, InvalidOperation
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import redirect_followup as follow
import source_schema as source

OUT = source.OUT / 'numeric_identity'
PANELS = [('B', 2), ('J', 4), ('Q', 6), ('X', 8), ('AE', 10), ('AL', 12), ('AS', 14)]


class Failure(Exception):
    pass


def column(number):
    name = ''
    while number:
        number, digit = divmod(number - 1, 26)
        name = chr(65 + digit) + name
    return name


def scopes(safe):
    fig1 = next(s for s in safe['sheets'] if s['sheet_name'] == 'Fig1B')
    labels = {c['coordinate']: c['text'] for c in fig1['string_schema_identity_cells'] if 'text' in c}
    rows = {int(c[1:]): text for c, text in labels.items() if re.fullmatch(r'A\d+', c) and re.fullmatch(r'(?:CIP|DAP|DOX|CRO|LZD) [1-4]', text)}
    if len(rows) != 80:
        raise Failure('main_string_identity_row_count')
    fig4 = {f'{col}{r}' for col, _ in PANELS for r in range(9, 29)}
    fig4.update(f'{column(c)}4' for c in range(3, 9))
    fig4.update(f'{column(c)}34' for c in range(4, 24))
    fig4.update(f'C{r}' for r in range(35, 49))
    fig4.update(f'{column(c)}31' for c in range(4, 19))
    return {'Fig1B': {f'B{r}' for r in rows}, 'Fig4B': fig4}, rows


def read_allowed(path, allow):
    values = {name: {} for name in allow}
    with zipfile.ZipFile(path, 'r') as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels if r.attrib.get('TargetMode') != 'External'}
        seen = set()
        for sheet in workbook.findall('m:sheets/m:sheet', source.NS):
            name = sheet.attrib['name']
            if name not in allow:
                continue
            if name in seen:
                raise Failure('duplicate_sheet')
            seen.add(name)
            target = targets[sheet.attrib[source.RID]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            with z.open(target) as stream:
                for _, cell in ET.iterparse(stream, events=('end',)):
                    if cell.tag != '{' + source.NS['m'] + '}c':
                        continue
                    coord = cell.attrib.get('r', '')
                    if coord not in allow[name]:
                        cell.clear()
                        continue
                    if coord in values[name]:
                        raise Failure('duplicate_allowed_coordinate')
                    if cell.attrib.get('t', 'n') != 'n' or cell.find('m:f', source.NS) is not None:
                        raise Failure('allowed_cell_not_plain_numeric')
                    value_node = cell.find('m:v', source.NS)
                    if value_node is None or value_node.text is None:
                        raise Failure('allowed_cell_missing_value')
                    try:
                        value = Decimal(value_node.text)
                    except InvalidOperation:
                        raise Failure('allowed_cell_invalid_numeric') from None
                    if not value.is_finite():
                        raise Failure('allowed_cell_nonfinite')
                    values[name][coord] = str(value)
                    cell.clear()
    if set(values) != seen or any(set(values[n]) != allow[n] for n in allow):
        raise Failure('allowed_coordinate_or_sheet_missing')
    return values


def integer(value):
    d = Decimal(value)
    if d != d.to_integral_value():
        raise Failure('identity_not_integer')
    return int(d)


def analyze(values, row_labels):
    main = []
    for row, label in sorted(row_labels.items()):
        drug, lineage = label.split()
        main.append({'row': row, 'selection_drug': drug, 'lineage': int(lineage), 'day': integer(values['Fig1B'][f'B{row}'])})
    main_keys = {(r['selection_drug'], r['lineage'], r['day']) for r in main}
    expected = {(d, l, t) for d in ['CIP', 'DAP', 'DOX', 'CRO', 'LZD'] for l in range(1, 5) for t in [2, 4, 6, 8]}
    if len(main_keys) != 80 or main_keys != expected:
        raise Failure('main_product_incomplete_or_duplicate')
    panel_records = []
    for col, day in PANELS:
        ids = [integer(values['Fig4B'][f'{col}{r}']) for r in range(9, 29)]
        if len(set(ids)) != 20:
            raise Failure('panel_ids_not_twenty_unique')
        panel_records.append({'day_from_string': day, 'replicate_column': col, 'ids_in_row_order': ids})
    same_set = all(set(p['ids_in_row_order']) == set(panel_records[0]['ids_in_row_order']) for p in panel_records)
    same_order = all(p['ids_in_row_order'] == panel_records[0]['ids_in_row_order'] for p in panel_records)
    embedded_ids = [integer(values['Fig4B'][f'{column(c)}34']) for c in range(4, 24)]
    daily_days = [integer(values['Fig4B'][f'C{r}']) for r in range(35, 49)]
    summary_days = [integer(values['Fig4B'][f'{column(c)}31']) for c in range(4, 19)]
    concentrations = [{'coordinate': f'{column(c)}4', 'value': values['Fig4B'][f'{column(c)}4']} for c in range(3, 9)]
    if any(Decimal(c['value']) < 0 for c in concentrations):
        raise Failure('negative_challenge_concentration')
    return {'main_clone_identity': {'rows': main, 'unique_keys': len(main_keys), 'complete_5drug_4lineage_4day': True,
                'independent_trajectory_labels': 20, 'assay_drug_slots_per_record': 5,
                'finite_response_slot_completeness_checked': False},
            'CRO_population_DOX_challenge': {'top_panels': panel_records, 'all_panels_same_twenty_ID_set': same_set,
                'all_panels_same_ID_row_order': same_order, 'embedded_strain_ids': embedded_ids,
                'embedded_ID_set_matches_top_panels': set(embedded_ids) == set(panel_records[0]['ids_in_row_order']),
                'embedded_ID_order_matches_top_panels': embedded_ids == panel_records[0]['ids_in_row_order'],
                'embedded_numeric_day_labels': daily_days, 'AUC_summary_day_labels_only': summary_days,
                'DOX_concentration_design': concentrations,
                'dose_units_not_in_numeric_cells': 'Confirm through primary caption/code; do not derive units from magnitude.',
                'response_values_accessed': False}}


def main():
    try:
        frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8-sig'))
        if any(source.sha(f['path']) != f['sha256'] for f in frozen['files']):
            raise Failure('frozen_input_changed_before_read')
        safe = json.loads((follow.OUT / 'SAFE_WORKING_SCHEMA.json').read_text(encoding='utf-8'))
        allow, row_labels = scopes(safe)
        registered = json.loads((OUT / 'EXACT_ALLOWLIST.json').read_text(encoding='utf-8'))
        if {k: set(v) for k, v in registered.items()} != allow:
            raise Failure('frozen_allowlist_mismatch')
        network = json.loads((follow.OUT / 'NETWORK.json').read_text(encoding='utf-8'))
        path = source.Path(network['raw_path'])
        before = source.sha(path)
        if before != network['sha256']:
            raise Failure('source_hash_mismatch')
        values = read_allowed(path, allow)
        result = analyze(values, row_labels)
        checks = [{'path': f['path'], 'unchanged': source.sha(f['path']) == f['sha256']} for f in frozen['files']]
        if source.sha(path) != before or not all(c['unchanged'] for c in checks):
            raise Failure('frozen_or_source_changed')
        result.update({'utc': source.utc(), 'runtime': sys.executable, 'http_requests': 0,
            'status': 'IDENTITY_DESIGN_CENSUS_COMPLETE', 'source_sha256_before': before, 'source_sha256_after': source.sha(path),
            'allowed_coordinate_values': values, 'frozen_checks': checks,
            'exposure': 'Allowed identity and challenge-design numbers exposed; prior nonfinite strings remain already-exposed; no finite response arrays interpreted.'})
        source.write_json(OUT / 'CENSUS.json', result)
        compact = {'main_clone_identity': {k: v for k, v in result['main_clone_identity'].items() if k != 'rows'},
            'CRO_population_DOX_challenge': result['CRO_population_DOX_challenge'], 'status': result['status']}
        print(json.dumps(compact))
        return 0
    except Exception as error:
        failure = {'utc': source.utc(), 'error_type': type(error).__name__, 'http_requests': 0}
        if isinstance(error, Failure):
            failure['reason'] = str(error)
        source.write_json(OUT / 'FAILURE.json', failure)
        print(json.dumps(failure))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
