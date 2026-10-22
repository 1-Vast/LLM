"""Offline primary-paragraph index; no workbook, network or numerical assay read."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/stack_raw_qualification'
OUT = BASE / 'data_auditor'
SOURCE = ROOT / 'log/20261022/functional_dynamics_gate/functional_auditor/RESPONSE_05_05_primary_efetch.body'
EXPECTED = 'fc96e1bc0ef59d9155e42a286a782f2a791eba04925984e41e1dcfdea6be974f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(element):
    return ' '.join(''.join(element.itertext()).split())


def main():
    if sha(SOURCE) != EXPECTED:
        raise ValueError('retained_primary_hash_mismatch')
    body = ET.fromstring(SOURCE.read_bytes())
    parents = {child: parent for parent in body.iter() for child in parent}
    selected = []
    for index, paragraph in enumerate(body.iter('p'), 1):
        current, ancestry = paragraph, []
        while current in parents:
            current = parents[current]
            if current.tag == 'sec':
                title = current.find('title')
                ancestry.append({'id': current.attrib.get('id'), 'title': text(title) if title is not None else ''})
        titles = [item['title'] for item in reversed(ancestry)]
        value = text(paragraph)
        method = any(title in ['STAR Methods', 'Method Details', 'Quantification and Statistical Analysis',
                              'Data and Software Availability', 'Data and software availability',
                              'Experimental Model and Subject Details', 'KEY RESOURCES TABLE'] for title in titles)
        anchors = ['High quality data was obtained', 'see online Data Repository for all live',
                   'Cells seeded in 384-well plates were exposed to library compounds',
                   'three independent biological replicates', 'doi:10.17632/3pnv5wh5jm.2',
                   'designed to detect live and dead cells', 'three major steps',
                   'free dataset', 'mKate2+ protein', 'SG+ signals from long dead',
                   '1,833 different bioactive compounds', '1,833-member bioactive compound screens']
        if method or any(anchor in value for anchor in anchors):
            selected.append({'paragraph_index': f'P{index:03d}', 'global_p_ordinal_1based': index,
                             'ancestor_sections': list(reversed(ancestry)), 'text': value})
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'source_path': str(SOURCE), 'source_sha256': EXPECTED,
              'index_rule': 'P001 etc count every XML p element in document order, including abstract and captions; whitespace normalized only in displayed text',
              'paragraphs': selected, 'all_primary_p_count': sum(1 for _ in body.iter('p')),
              'network_requests': 0, 'workbook_access': False, 'assay_response_array_access': False,
              'published_primary_aggregate_narrative_already_exposed': True,
              'source_unchanged_after': sha(SOURCE) == EXPECTED,
              'root_protocol_sha256': sha(BASE / 'ROOT_PROTOCOL.md')}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'PRIMARY_PARAGRAPHS.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps({'all_primary_p_count': result['all_primary_p_count'], 'selected': selected}, ensure_ascii=False))


if __name__ == '__main__':
    main()
