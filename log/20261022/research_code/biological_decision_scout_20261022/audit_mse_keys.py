"""Project only authenticated metadata keys and missingness masks, never assay values."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2] / 'log/20261022/biological_decision_scout/sources'
NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def sheets(path):
    z = zipfile.ZipFile(path)
    strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si', NS)]
    rels = {r.get('Id'): r.get('Target').lstrip('/') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    result = {}
    for e in ET.fromstring(z.read('xl/workbook.xml')).findall('x:sheets/x:sheet', NS):
        target = rels[e.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
        if not target.startswith('xl/'):
            target = 'xl/' + target
        result[e.get('name')] = (strings, ET.fromstring(z.read(target)))
    return result


def string_cell(cell, strings, numeric_metadata=False):
    if cell is None:
        return None
    kind = cell.get('t')
    if kind == 's':
        return strings[int(cell.findtext('x:v', namespaces=NS))]
    if kind == 'inlineStr':
        return ''.join(cell.find('x:is', NS).itertext())
    if numeric_metadata:
        return cell.findtext('x:v', namespaces=NS)  # Original metadata token, never float-cast.
    raise ValueError('Scalar access denied outside approved metadata columns')


def key_rows(sheet, columns):
    strings, root = sheet
    out = []
    for row in root.findall('x:sheetData/x:row', NS)[1:]:
        cells = {re.sub('[0-9]', '', c.get('r')): c for c in row.findall('x:c', NS)}
        record = {label: string_cell(cells.get(col), strings, numeric_metadata=True) for label, col in columns.items()}
        if any(v is not None for v in record.values()):
            out.append(record)
    return out


member = ROOT / 'complete_members'
clinical = key_rows(sheets(member / '41467_2024_52694_MOESM4_ESM.xlsx')['Clinical data'],
                    {'sample': 'A', 'patient': 'B', 'sample_type': 'E', 'tumor_type': 'F'})
experiment = key_rows(sheets(member / '41467_2024_52694_MOESM5_ESM.xlsx')['Experiment details'],
                      {'experiment': 'A', 'sample': 'B', 'plate': 'C', 'storage': 'E', 'protocol': 'F'})
control = key_rows(sheets(member / '41467_2024_52694_MOESM6_ESM.xlsx')['Cell_type_abundance_raw'], {'sample': 'A'})
response = {}
for name, (strings, root) in sheets(member / '41467_2024_52694_MOESM8_ESM.xlsx').items():
    rows = root.findall('x:sheetData/x:row', NS)
    headers = {re.sub('[0-9]', '', c.get('r')): string_cell(c, strings) for c in rows[0].findall('x:c', NS)}
    drug_cols = {c: v for c, v in headers.items() if c != 'A'}
    entries = []
    kinds = Counter()
    for row in rows[1:]:
        cells = {re.sub('[0-9]', '', c.get('r')): c for c in row.findall('x:c', NS)}
        sample = string_cell(cells['A'], strings)
        available = []
        unavailable = []
        for col, drug in drug_cols.items():
            cell = cells.get(col)
            if cell is None or cell.find('x:v', NS) is None and cell.get('t') != 'inlineStr':
                status = 'empty'
            elif cell.get('t') in ('s', 'inlineStr', 'e'):
                status = 'nonnumeric_missing_or_annotation'
                # No outcome string is displayed or interpreted.
            else:
                status = 'numeric_slot'
            kinds[status] += 1
            (available if status == 'numeric_slot' else unavailable).append(drug)
        entries.append({'sample': sample, 'numeric_slot_drugs': available, 'other_drugs': unavailable})
    response[name] = {'rows': entries, 'drugs': list(drug_cols.values()), 'slot_types': dict(kinds)}

pid = {r['sample']: r['patient'] for r in clinical}
response_ids = {r['sample'] for r in response['RCF raw']['rows']}
counts = Counter(pid[s] for s in response_ids)
plates = {r['sample']: r['plate'] for r in experiment}
response_drugs = set(response['RCF raw']['drugs'])
all_numeric = set.intersection(*(set(r['numeric_slot_drugs']) for r in response['RCF raw']['rows']))
summary = {
    'clinical_rows': len(clinical), 'clinical_unique_samples': len(pid),
    'clinical_unique_patients': len(set(pid.values())),
    'experiment_rows': len(experiment), 'unique_experiment_ids': len({r['experiment'] for r in experiment}),
    'unique_plate_ids': len({r['plate'] for r in experiment}),
    'control_unique_samples': len({r['sample'] for r in control}),
    'response_unique_samples': len(response_ids), 'response_patients': len(counts),
    'patients_with_multiple_response_samples': sum(v > 1 for v in counts.values()),
    'response_sample_counts_per_patient': dict(Counter(counts.values())),
    'response_without_clinical': sorted(response_ids - set(pid)),
    'clinical_without_response': sorted(set(pid) - response_ids),
    'response_without_control': sorted(response_ids - {r['sample'] for r in control}),
    'response_without_experiment': sorted(response_ids - set(plates)),
    'response_drugs': len(response_drugs), 'all_sample_numeric_slot_drugs': sorted(all_numeric),
    'per_sheet_slot_types': {n: v['slot_types'] for n, v in response.items()},
    'patient_grouped_split_possible': len(counts) > 1,
    'raw_means_have_no_well_ids': True,
    'metadata_examples': experiment[:3],
    'assay_value_casts': 0,
    'note': 'Numeric-slot masks establish storage/coverage only, not finite values, reliable measurements or valid decisions.'
}
payload = {'summary': summary, 'clinical_identity': clinical, 'experiment_identity': experiment, 'response_masks': response}
out = ROOT / 'MSE_KEY_AUDIT.json'
if out.exists():
    raise FileExistsError(out)
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
