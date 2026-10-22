"""JSON-only structural completeness; primary nonnumeric drug Table1 identity."""
import json
import re
import xml.etree.ElementTree as ET

import numeric_identity as census
import redirect_followup as follow
import source_schema as source


def main():
    identity_path = census.OUT / 'CENSUS.json'
    struct_path = follow.OUT / 'NUMERIC_COORDINATE_STRUCTURE.json'
    identity = json.loads(identity_path.read_text(encoding='utf-8'))
    structure = json.loads(struct_path.read_text(encoding='utf-8'))
    present = {s['sheet']: set(s['numeric_typed_coordinates_with_value_node_only']) for s in structure['sheets']}
    scopes = {
        'main_mean_response_slots': ('Fig1B', {f'{col}{r["row"]}' for col in ['C', 'D', 'E', 'F', 'G'] for r in identity['main_clone_identity']['rows']}),
        'main_sem_response_slots': ('Fig1B', {f'{col}{r["row"]}' for col in ['I', 'J', 'K', 'L', 'M'] for r in identity['main_clone_identity']['rows']}),
        'Fig4_top_OD_response_slots': ('Fig4B', {f'{census.column(c)}{r}' for start in [3, 11, 18, 25, 32, 39, 46] for c in range(start, start + 6) for r in range(9, 29)}),
        'Fig4_embedded_IC50_candidate_response_slots': ('Fig4B', {f'{census.column(c)}{r}' for c in range(4, 24) for r in range(35, 49)}),
        'Fig4_AUC_summary_response_slots': ('Fig4B', {f'{census.column(c)}32' for c in range(4, 19)}),
    }
    checks = []
    for label, (sheet, coords) in scopes.items():
        checks.append({'object': label, 'sheet': sheet, 'expected_coordinate_count': len(coords),
            'numeric_typed_value_node_count': len(coords & present[sheet]),
            'coordinates_without_numeric_value_node': sorted(coords - present[sheet]),
            'numerical_value_validity_checked': False})
    primary_path = source.ROOT / 'log/20261022/dynamic_source_followup/ncbi_scout/PRIMARY.xml'
    before = source.sha(primary_path)
    tree = ET.parse(primary_path).getroot()
    tables = [t for t in tree.iter('table-wrap') if t.attrib.get('id') == 'pbio.3002970.t001']
    if len(tables) != 1:
        raise RuntimeError('Table1_identity_absent_or_ambiguous')
    rows = []
    for tr in tables[0].iter('tr'):
        values = [' '.join(' '.join(c.itertext()).split()) for c in tr if c.tag in {'td', 'th'}]
        # The authorized Table1 contains drug names/abbreviations and target classes only.
        values = ['[text containing digits withheld]' if re.search(r'\d', text) else text for text in values]
        if values:
            rows.append(values)
    result = {'scope': 'STRUCTURAL_PRESENCE_ONLY_NOT_RESPONSE_NUMBERS', 'checks': checks,
        'primary_Table1_identity': {'source_sha256': before, 'rows': rows, 'source_unchanged': source.sha(primary_path) == before},
        'input_hashes': {str(p): source.sha(p) for p in [identity_path, struct_path]},
        'limits': 'A numeric type and value-node presence do not prove finite validity, non-missing measurement, exact fitting/normalization formula or biological independence.'}
    source.write_json(follow.OUT / 'FINAL_IDENTITY_STRUCTURE_CHECKS.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
