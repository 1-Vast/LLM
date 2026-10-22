"""Exact offline screen/caption paragraphs and scoring formula, no raw data."""
import hashlib
import json
import xml.etree.ElementTree as ET

import primary_observation_audit as audit


def main():
    if audit.sha(audit.SOURCE) != audit.EXPECTED:
        raise ValueError('primary_hash_mismatch')
    root = ET.fromstring(audit.SOURCE.read_bytes())
    wanted = {9, 10, 11, 13, 14, 19, 69, 70}
    selected = [{'paragraph_index': f'P{index:03d}', 'text': audit.text(paragraph)}
                for index, paragraph in enumerate(root.iter('p'), 1) if index in wanted]
    section, = [element for element in root.iter('sec') if element.attrib.get('id') == 'S19']
    formulas = [{'attributes': element.attrib, 'xml': ET.tostring(element, encoding='unicode'),
                 'flattened_text': audit.text(element)} for element in section.iter('disp-formula')]
    original = json.loads((audit.OUT / 'PRIMARY_PARAGRAPHS.json').read_text(encoding='utf-8'))
    qc = next(row['text'] for row in original['paragraphs'] if row['paragraph_index'] == 'P045')
    t98_list = qc.split('removed from further analysis (', 1)[1].split(').', 1)[0]
    u2_list = qc.split('In the U-2 OSN experiment', 1)[1].split('for this reason (', 1)[1].split(').', 1)[0]
    result = {'source_sha256': audit.EXPECTED, 'index_rule': original['index_rule'],
              'additional_exact_paragraphs': selected, 'LF_formula_source_section_id': 'S19',
              'LF_formulas': formulas,
              'qc_literal_evidence': {'source_paragraph': 'P045', 'T98_stated_count_word': 'Eight',
                                      'T98_exact_list': t98_list,
                                      'T98_comma_and_final_and_entries': t98_list.replace(' and ', ', ').split(', '),
                                      'U2OS_stated_count_word': 'seven', 'U2OS_exact_list': u2_list,
                                      'U2OS_comma_and_final_and_entries': u2_list.replace(' and ', ', ').split(', '),
                                      'unrepaired_ambiguity': 'U2OS first comma-delimited entry is nintedanib PHA-665752; do not silently insert punctuation or decide a mask.'},
              'network_requests': 0, 'workbook_access': False, 'assay_response_array_access': False,
              'source_unchanged_after': audit.sha(audit.SOURCE) == audit.EXPECTED}
    with (audit.OUT / 'SCREEN_AND_FORMULA_EVIDENCE.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps({'additional_paragraph_ids': [row['paragraph_index'] for row in selected],
                      'formulas': formulas, 'qc_literal_evidence': result['qc_literal_evidence']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
