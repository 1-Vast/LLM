"""Frozen source-only scalar access and descriptive shortlist opportunity audit."""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mse_source_gate'
MEMBERS = ROOT / 'log/20261022/biological_decision_scout/sources/complete_members'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TAG = '{' + NS['m'] + '}'
FIELDS = ['Lymphocyte_act', 'Lymphocyte_conv',
          'Macrophage_round', 'Macrophage_stretched', 'Malignant_adherent',
          'Malignant_colony', 'Malignant_single', 'Malignant_spheroid', 'Other', 'Unassigned']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(name, payload):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)


def string(cell, shared):
    if cell.get('t') == 's':
        return shared[int(cell.findtext('m:v', namespaces=NS))]
    assert cell.get('t') == 'inlineStr', 'Only string keys/headers are allowed'
    return ''.join(cell.find('m:is', NS).itertext())


def read_source(path, sheet_name, allowed_samples, fields):
    """Inspect scalar text only after row AND field authorization; deny all other sheets."""
    records, accesses, skipped = {}, [], []
    with zipfile.ZipFile(path) as z:
        shared = [''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        rels = {r.get('Id'): r.get('Target').lstrip('/')
                for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = {s.get('name'): s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                  for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet', NS)}
        target = rels[sheets[sheet_name]]
        if not target.startswith('xl/'):
            target = 'xl/' + target
        header = None
        with z.open(target) as stream:
            for _, row in ET.iterparse(stream, events=('end',)):
                if row.tag != TAG + 'row':
                    continue
                cells = {re.sub(r'\d', '', c.get('r')): c for c in row.findall('m:c', NS)}
                if header is None:
                    header = {col: string(c, shared) for col, c in cells.items()}
                    assert header['A'] == 'SampleID'
                    assert len(set(header.values())) == len(header)
                    columns = {field: next(col for col, name in header.items() if name == field) for field in fields}
                else:
                    sample = string(cells['A'], shared)
                    if sample not in allowed_samples:
                        skipped.append(sample)
                    else:
                        assert sample not in records, 'Duplicate authorized source sample'
                        values = {}
                        for field, col in columns.items():
                            cell = cells.get(col)
                            record = {'sample': sample, 'sheet': sheet_name, 'field': field,
                                      'coordinate': col + row.get('r'), 'status': 'missing', 'value': None}
                            if cell is not None and cell.find('m:f', NS) is not None:
                                record['status'] = 'formula_disallowed'
                            elif cell is not None and cell.get('t') in (None, 'n'):
                                token = cell.findtext('m:v', namespaces=NS)
                                if token is not None:
                                    record['numeric_token'] = token
                                    try:
                                        value = Decimal(token)
                                        record['status'] = 'finite' if value.is_finite() else 'nonfinite'
                                        if value.is_finite():
                                            record['value'] = str(value)
                                    except InvalidOperation:
                                        record['status'] = 'invalid_numeric_token'
                            elif cell is not None:
                                record['status'] = 'nonnumeric'
                            accesses.append(record)
                            values[field] = None if record['value'] is None else Decimal(record['value'])
                        records[sample] = values
                row.clear()
    assert set(records) == set(allowed_samples), 'Missing authorized source row'
    return records, accesses, skipped


def opportunity(hit, patients, drugs):
    """LOPO global5 vs sample oracle5, averaged samples within patient first."""
    groups = sorted(set(patients))
    patient_hits = [[Fraction(int(hit[np.array(patients) == p, j].sum()), patients.count(p))
                     for j in range(len(drugs))] for p in groups]
    rows = []
    for i, p in enumerate(groups):
        training_means = [sum(patient_hits[k][j] for k in range(len(groups)) if k != i) / (len(groups) - 1)
                          for j in range(len(drugs))]
        selected = sorted(range(len(drugs)), key=lambda j: (-training_means[j], drugs[j]))[:5]
        observed = hit[np.array(patients) == p]
        baseline = Fraction(int(observed[:, selected].sum()), 5 * len(observed))
        oracle = Fraction(int(np.minimum(observed.sum(axis=1), 5).sum()), 5 * len(observed))
        mixed = bool(np.any((observed.sum(axis=1) > 0) & (observed.sum(axis=1) < len(drugs))))
        rows.append({'patient': p, 'baseline': float(baseline), 'oracle': float(oracle),
                     'gap': float(oracle - baseline), 'baseline_exact': str(baseline),
                     'oracle_exact': str(oracle), 'gap_exact': str(oracle - baseline), 'mixed_hit_sample': mixed,
                     'selected': [drugs[j] for j in selected]})
    means = {name: sum(Fraction(r[name + '_exact']) for r in rows) / len(rows)
             for name in ('baseline', 'oracle', 'gap')}
    return {'patients': rows, **{name: float(value) for name, value in means.items()},
            **{name + '_exact': str(value) for name, value in means.items()},
            'mixed_hit_patients': sum(r['mixed_hit_sample'] for r in rows),
            'leave_one_patient_out_label_aggregations': len(groups)}


def run():
    freeze = load(OUT / 'FREEZE.json')
    for name, expected in freeze['files'].items():
        assert sha(ROOT / name) == expected, name
    assert not (OUT / 'RESULT.json').exists(), 'No reruns/overwrite'
    manifest = load(OUT / 'PATIENT_MENU_MANIFEST.json')
    source = [r for r in manifest['rows'] if r['partition'] == 'source']
    samples, drugs = [r['sample'] for r in source], manifest['drugs']
    all_access, arrays, skipped_ids = [], {}, {}
    for sheet in ('RCN raw', 'RCF raw', 'Cell_type_abundance_raw'):
        number = 6 if sheet == 'Cell_type_abundance_raw' else 8
        fields = FIELDS if number == 6 else drugs
        data, access, skipped = read_source(MEMBERS / f'41467_2024_52694_MOESM{number}_ESM.xlsx', sheet, set(samples), fields)
        all_access.extend(access)
        arrays[sheet] = [[data[s][f] for f in fields] for s in samples]
        skipped_ids[sheet] = skipped
    bad = [r for r in all_access if r['status'] != 'finite' or Decimal(r['value']) > Decimal('1.0000000001')
           or (r['sheet'] == 'Cell_type_abundance_raw' and Decimal(r['value']) < Decimal('-0.0000000001'))]
    assert {r['sample'] for r in all_access} == set(samples)
    assert len(all_access) == len(samples) * (65 * 2 + 10)
    counts = Counter(r['sheet'] for r in all_access)
    checks = {'all_required_values_finite_and_in_contract': not bad}
    result = {'checks': checks, 'violations': bad, 'source_samples': len(samples),
              'source_patients': len({r['patient'] for r in source}),
              'numeric_access_attempts': dict(counts), 'source_required_field_attempts': len(all_access),
              'nonsource_scalar_accesses': 0, 'scaled_sheet_accesses': 0,
              'predictive_model_fits': 0, 'provider_calls': 0,
              'raw_denominator_and_retained_well_precision_authenticated': False,
              'freeze_sha256': sha(OUT / 'FREEZE.json'), 'utc': datetime.now(timezone.utc).isoformat()}
    write('SOURCE_VALUE_ACCESS.json', {'records': all_access, 'skipped_sample_ids': skipped_ids,
          'note': 'Full acquired worksheet bytes parsed; only authorized source scalar text inspected/converted.'})
    if not bad:
        n, f = np.array(arrays['RCN raw']), np.array(arrays['RCF raw'])
        terminal = [drugs.index(d) for d in manifest['terminal_drugs']]
        hit = (n[:, terminal] >= Decimal('0.50')) & (f[:, terminal] >= Decimal('0.20'))
        result['opportunity'] = opportunity(hit, [r['patient'] for r in source], manifest['terminal_drugs'])
        checks['descriptive_oracle_gap_at_least_0.10'] = Fraction(result['opportunity']['gap_exact']) >= Fraction(1, 10)
        checks['at_least_10_mixed_hit_patient_groups'] = result['opportunity']['mixed_hit_patients'] >= 10
        result['source_hit_counts_per_sample'] = dict(zip(samples, hit.sum(axis=1).tolist()))
        result['response_summaries'] = {name: {'min_exact_decimal': str(np.min(a)), 'max_exact_decimal': str(np.max(a)),
                                             'negative': int((np.array(a) < 0).sum())}
                                        for name, a in arrays.items()}
    result['passed'] = all(checks.values())
    result['decision'] = 'GO_ONLY_TO_SEPARATE_ORDINARY_INFORMATION_GATE' if result['passed'] else 'STOP_EXACT_CONFIGURATION'
    write('RESULT.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('violations', 'source_hit_counts_per_sample')}))


if __name__ == '__main__':
    assert sys.argv[1:] == ['run']
    run()
