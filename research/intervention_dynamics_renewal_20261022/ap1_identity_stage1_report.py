"""Summarize already exported authorized strings; never decode workbook cells."""
from collections import Counter
import json
from pathlib import Path

import ap1_identity_stage1 as reader


def main():
    result = json.loads((reader.OUT/'STAGE1_STRINGS.json').read_text(encoding='utf-8'))
    frozen = json.loads((reader.OUT/'FREEZE.json').read_text(encoding='utf-8'))
    roles = {
        'Figure 2b': {'identity': {'B4': 'experiment code'},
                      'condition': {'C4': '5nM trametinib', 'D4': '1nM trametinib', 'E4': '1nM ->5nM trametinib'},
                      'candidate_ids_seen': 'B6:B12; seven source exp aliases already identified in published code',
                      'missing': ['biological independence of1541A/B and other files', 'clone/passage/well', 'phase duration and zero flags']},
        'Figure 2g': {'identity': {'D3': 'Name condition code', 'F2': 'exp'}, 'response_closed': {'E2': 'colony'},
                      'dictionary_seen': 'H3:H6 maps hi1,hi2,lo1,lo2; other entries outside stage1',
                      'missing': ['complete condition dictionary', 'experiment roster', 'observed-zero/missing distinction', 'dose/phase/run independence']},
        'Figure 3b': {'identity': {'B2': 'exp_id', 'C2': 'Id', 'D2': 'Channel', 'E2': 'XY', 'F2': 'Z', 'G2': 'Time', 'H2': 'Tags', 'I2': 'Shape', 'J2': 'Name', 'S2': 'sample_identifier', 'T2': 'dataset_identifier'},
                      'response_closed': 'K:N morphology; O:R channels; U:X point counts; Y:AE normalization/area-derived values',
                      'missing': ['run and sample ID dictionaries', 'gene/channel dictionary', 'time units/phase map', 'functional condition/run join']},
        'Figure 3b summary': {'identity': {'D4': 'dataset_identifier', 'E3': 'sample_identifier'},
                              'response_closed': 'F:H means; I:K standard errors',
                              'missing': ['summary-to-raw sample/dataset value mapping', 'run independence', 'gene names'],
                              'join_caution': 'Raw Dataset 1 uses ASCII space; summary Dataset\u00a01 uses nonbreaking space. Preserve originals; any normalization must be explicit.'},
        'Figure 4c': {'identity': {'D5': 'Id', 'E4': 'Channel', 'F4': 'XY', 'G4': 'Z', 'H4': 'Time', 'I4': 'Tags', 'J4': 'Shape', 'O4': 'Name'},
                      'response_closed': 'K:N fluorescence/normalization; P:AG intensity and morphology fields',
                      'secondary_section_seen': {'B68': 'Figure4c background annotations'},
                      'missing': ['run/clone/well identity', 'initial-to-later lineage connection', 'secondary header roles', 'time units']},
        'Figure 4e': {'identity': {'D5': 'lineageId', 'E4': 'generation', 'F4': 'annotationID', 'I4': 'file_id'},
                      'section_labels': {'B5': 'starting cell', 'B55': 'final colony'},
                      'file_alias_seen': 'I6:I8 =VID1578 only; not a full-run census',
                      'response_closed': 'G:H greencell/redcell; J redgreenfc; K color is a categorical state candidate',
                      'missing': ['lower-block header equivalence', 'paired lineage mapping across blocks', 'clone/well/run identity', 'time/dose/track selection rules']},
        'Figure 5b': {'identity': {'B1': 'Channel', 'C1': 'condition', 'D1': 'XY', 'E1': 'Z', 'F1': 'Time', 'G1': 'Tags', 'H1': 'Shape', 'I1': 'Name'},
                      'condition_seen': 'C2:C5 trametinib-off', 'response_closed': 'J:X colony fluorescence summaries',
                      'missing': ['stable colony/lineage/run/well key', 'clone identity', 'time/phase dictionary', 'same-object growth endpoint']},
        'Figure 5c': {'identity': {'B1': 'Channel', 'C1': 'condition', 'D1': 'XY', 'E1': 'Z', 'F1': 'Time', 'G1': 'Tags', 'H1': 'Shape', 'I1': 'Name'},
                      'condition_seen': 'C2:C5 trametinib-A485', 'response_closed': 'J:X colony fluorescence summaries',
                      'missing': ['stable colony/lineage/run/well key', 'clone identity', 'time/phase dictionary', 'same-object growth endpoint']}}
    exposure = []
    for name, sheet in result['sheets'].items():
        for item in sheet['strings']:
            if item['text'] == 'NA':
                exposure.append({'sheet': name, 'coordinate': item['coordinate'], 'text': item['text'],
                                 'role': 'response missing-marker exposure' if name == 'Figure 3b' and item['coordinate'][0] in 'UVWX' else 'unknown/annotation missing-marker string; not authenticated identity'})
            if name == 'Figure 4e' and item['coordinate'] in ['K6', 'K7', 'K8']:
                exposure.append({'sheet': name, 'coordinate': item['coordinate'], 'text': item['text'],
                                 'role': 'color/state-category exposure; not an independent-run identity'})
    reader.write('FIELD_ROLES.json', {'utc': reader.utc(), 'status': 'STAGE1_ONLY_STAGE2_COORDINATES_NOT_AUTHORIZED',
                 'roles': roles, 'string_exposure': exposure, 'stage1_output_sha256': reader.sha(reader.OUT/'STAGE1_STRINGS.json')})
    checks = [{'path': f['path'], 'unchanged': reader.sha(f['path']) == f['sha256']} for f in frozen['files']]
    totals = Counter()
    for sheet in result['sheets'].values():
        totals.update(sheet['type_counts'])
    reader.write('FINAL_CHECKS.json', {'utc': reader.utc(), 'status': 'STAGE1_DESIGN_STRINGS_ONLY',
                 'frozen_checks': checks, 'all_frozen_unchanged': all(c['unchanged'] for c in checks),
                 'source_sha256': reader.sha(reader.RAW), 'source_hash_matches': reader.sha(reader.RAW) == reader.EXPECTED,
                 'authorized_coordinate_count': sum(totals.values()), 'authorized_type_counts': dict(totals),
                 'decoded_nonempty_string_coordinates': sum(len(s['strings']) for s in result['sheets'].values()),
                 'decoded_shared_string_count': result['decoded_shared_string_count'],
                 'numeric_values_interpreted': False, 'formulas_interpreted': False, 'finite_gate_performed': False,
                 'stage2_executed': False, 'network_requests': 0,
                 'report_code_sha256': reader.sha(__file__)})
    print(json.dumps({'all_frozen_unchanged': all(c['unchanged'] for c in checks),
                      'authorized_type_counts': dict(totals), 'decoded_shared_string_count': result['decoded_shared_string_count'],
                      'exposure_records': len(exposure)}))


if __name__ == '__main__':
    main()
