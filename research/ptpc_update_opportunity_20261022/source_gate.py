"""Frozen, HCT116-only PTPC annotation type/group qualification; no fitting."""
from pathlib import Path
from io import BytesIO
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261022/ptpc_update_opportunity/source'
PRIOR = ROOT/'log/20261022/generative_repair_renewal/source/archive_followup'
MEMBER = 'TableS8_PTPC_info_0703.xlsx'
EXPECTED_ARCHIVE = 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TAG = '{'+NS['s']+'}'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    path = OUT/name
    assert not path.exists(), f'Refuse overwrite: {name}'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_prior():
    seal = json.loads((PRIOR/'SEAL.json').read_text(encoding='utf-8'))
    checked = []
    for item in seal['files']:
        path = ROOT/item['path']
        assert digest(path) == item['sha256'], f'Prior source changed: {path}'
        checked.append(item['path'])
    assert digest(PRIOR/'archive.body') == EXPECTED_ARCHIVE
    return checked


def classify(cell, value):
    storage = 'absent' if cell is None else cell.attrib.get('t', 'n')
    if cell is not None and cell.find('s:f', NS) is not None:
        return 'unknown', 'formula', '[formula cell]'
    if storage in ('b', 'e'):
        return 'unknown', storage, value
    token = value.strip()
    if token.casefold() in ('', 'na', 'n/a', 'nan'):
        return 'missing', storage, value
    if storage == 'n':
        try:
            number = Decimal(token)
            if number.is_finite() and number in (0, 1):
                return str(int(number)), storage, value
        except InvalidOperation:
            pass
        return 'unknown', storage, value
    if storage not in ('s', 'inlineStr', 'str'):
        return 'unknown', storage, value
    mapping = {'y': '1', 'sensitive': '1', '1': '1',
               'n': '0', 'resistant': '0', '0': '0'}
    return mapping.get(token.casefold(), 'unknown'), storage, value


def run():
    assert not (OUT/'LABEL_GATE_RESULT.json').exists(), 'Gate already completed'
    receipt = json.loads((OUT/'PROTOCOL_SEAL.json').read_text(encoding='utf-8'))
    assert receipt['previous_seal_sha256'] == digest(PRIOR/'SEAL.json'), 'Prior seal changed'
    for item in receipt['files']:
        assert digest(ROOT/item['path']) == item['sha256'], 'Frozen protocol/code changed'
    checked = verify_prior()
    with zipfile.ZipFile(PRIOR/'archive.body') as outer:
        workbook_bytes = outer.read(MEMBER)
    member_sha = hashlib.sha256(workbook_bytes).hexdigest()
    rows, skipped = [], Counter()
    with zipfile.ZipFile(BytesIO(workbook_bytes)) as book:
        # Lookup nodes remain private; never resolve non-HCT116 Efficacy cells.
        strings = ET.fromstring(book.read('xl/sharedStrings.xml')).findall('s:si', NS)
        def value(cell):
            if cell is None:
                return ''
            if cell.attrib.get('t') == 's':
                return ''.join(n.text or '' for n in strings[int(cell.find('s:v', NS).text)].findall('.//s:t', NS))
            if cell.attrib.get('t') == 'inlineStr':
                return ''.join(n.text or '' for n in cell.findall('.//s:t', NS))
            node = cell.find('s:v', NS)
            return node.text or '' if node is not None else ''
        rels = {n.attrib['Id']: n.attrib['Target'] for n in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        target = None
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).findall('.//s:sheet', NS):
            if sheet.attrib['name'] == 'A_metadata':
                target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        assert target
        target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        header = None
        with book.open(target) as stream:
            for _, row in ET.iterparse(stream, events=['end']):
                if row.tag != TAG+'row':
                    continue
                cells = {re.match(r'[A-Z]+', c.attrib['r'])[0]: c for c in row if c.tag == TAG+'c'}
                if header is None:
                    header = {value(c): col for col, c in cells.items()}
                    assert set(header) == {'Sample_ID', 'Cell_line', 'Cell_plate', 'Pert_ID', 'Compound_name', 'Pert_time_(hrs)', 'Efficacy', 'Rep'}
                else:
                    line = value(cells.get(header['Cell_line']))
                    if line != 'HCT116':
                        skipped[line] += 1
                        row.clear()
                        continue
                    record = {key: value(cells.get(col)) for key, col in header.items() if key != 'Efficacy'}
                    efficacy = cells.get(header['Efficacy'])
                    label, storage, raw = classify(efficacy, value(efficacy))
                    record.update(row=int(row.attrib['r']), label=label, storage_type=storage, raw_token=raw,
                                  control=any(record[key].strip().casefold() == 'control' for key in ('Compound_name', 'Pert_ID')))
                    rows.append(record)
                row.clear()
    assert len(rows) == 1289 and dict(skipped) == {'A375': 216, 'NCI-H1975': 249, 'NCI-H2170': 255, 'Panc1005': 208}
    strata = defaultdict(list)
    groups = defaultdict(list)
    samples = defaultdict(list)
    for row in rows:
        strata[(row['control'], row['Pert_time_(hrs)'], row['Rep'])].append(row)
        groups[(row['Cell_line'], row['Pert_ID'])].append(row)
        samples[row['Sample_ID']].append(row)
    def counts(subset):
        return dict(rows=len(subset), labels=dict(Counter(r['label'] for r in subset)),
                    actual_tokens=[dict(storage_type=k[0], token=k[1], rows=v)
                                   for k, v in sorted(Counter((r['storage_type'], r['raw_token']) for r in subset).items())])
    grouping = []
    for key, subset in sorted(groups.items()):
        observed = set(r['label'] for r in subset)
        conflict = {'0', '1'} <= observed
        usable = not any(r['control'] for r in subset) and not conflict and 'unknown' not in observed and bool(observed & {'0', '1'})
        grouping.append(dict(Cell_line=key[0], Pert_ID=key[1], control=any(r['control'] for r in subset),
                             rows=len(subset), labels=dict(Counter(r['label'] for r in subset)),
                             times=sorted(set(r['Pert_time_(hrs)'] for r in subset)),
                             rep_counts=dict(Counter(r['Rep'] for r in subset)),
                             sample_ids=len(set(r['Sample_ID'] for r in subset)),
                             known_class_conflict=conflict, mixed_missingness='missing' in observed and bool(observed & {'0', '1'}),
                             all_missing=observed == {'missing'}, unknown='unknown' in observed,
                             candidate_condition_annotation=usable, strict_complete_candidate=usable and 'missing' not in observed))
    unknowns = [dict(row=r['row'], token=r['raw_token'], storage_type=r['storage_type']) for r in rows if r['label'] == 'unknown']
    result = dict(created_utc=now(), status='PAUSE_UNKNOWN_LABEL_DEFINITION' if unknowns else 'RECOGNIZED_ENCODING_ONLY',
                  target='author-released Efficacy annotation; assay semantics remain unverified',
                  source_archive_sha256=EXPECTED_ARCHIVE, S8_member=MEMBER, S8_member_sha256=member_sha,
                  prior_seal_sha256=digest(PRIOR/'SEAL.json'), prior_sealed_files_verified=len(checked),
                  protocol_seal_sha256=digest(OUT/'PROTOCOL_SEAL.json'),
                  background_roles={'development': ['HCT116'], 'selection_unopened': ['A375'], 'final_unopened': ['NCI-H1975', 'NCI-H2170', 'Panc1005']},
                  skipped_non_HCT116_label_cells=dict(skipped), protein_worksheets_opened=False,
                  all_HCT116=counts(rows), noncontrol_HCT116=counts([r for r in rows if not r['control']]),
                  controls_HCT116=counts([r for r in rows if r['control']]),
                  strata=[dict(control=key[0], time=key[1], Rep=key[2], **counts(subset)) for key, subset in sorted(strata.items())],
                  observed_rep_annotations=dict(Counter(r['Rep'] for r in rows)),
                  unique_sample_ids=len(samples), rows_excluding_techrep=sum(r['Rep'].strip().casefold() != 'techrep' for r in rows),
                  duplicate_sample_ids=[dict(Sample_ID=k, rows=[r['row'] for r in v], Rep=[r['Rep'] for r in v]) for k, v in sorted(samples.items()) if len(v)>1],
                  condition_groups=len(grouping), conflicting_groups=sum(g['known_class_conflict'] for g in grouping),
                  mixed_missing_groups=sum(g['mixed_missingness'] for g in grouping), all_missing_groups=sum(g['all_missing'] for g in grouping),
                  unknown_groups=sum(g['unknown'] for g in grouping),
                  candidate_noncontrol_conditions=sum(g['candidate_condition_annotation'] for g in grouping),
                  strict_complete_noncontrol_conditions=sum(g['strict_complete_candidate'] for g in grouping),
                  unknown_HCT116_tokens=unknowns,
                  limitation='Condition counts are annotations, not independent function assay purchases or RSI tasks. No numerical experiment authorized.')
    save('HCT116_CONDITION_GROUPS.json', grouping)
    save('LABEL_GATE_RESULT.json', result)
    save('RESULT_SEAL.json', dict(created_utc=now(), files=[dict(path=str(p.relative_to(ROOT)), sha256=digest(p)) for p in [OUT/'PROTOCOL_SEAL.json', OUT/'HCT116_CONDITION_GROUPS.json', OUT/'LABEL_GATE_RESULT.json']]))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seal-protocol', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    assert args.seal_protocol != args.run
    if args.seal_protocol:
        save('PROTOCOL_SEAL.json', dict(created_utc=now(), values_opened=False,
             files=[dict(path=str(p.relative_to(ROOT)), sha256=digest(p)) for p in [OUT/'LABEL_GATE_PROTOCOL.md', Path(__file__).resolve()]],
             previous_seal_sha256=digest(PRIOR/'SEAL.json')))
        print(json.dumps(dict(protocol_sealed=True, receipt_sha256=digest(OUT/'PROTOCOL_SEAL.json'))))
    else:
        run()
