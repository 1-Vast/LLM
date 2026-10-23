"""Independent selected XML/payload and fixed-OOF metric audit; no model imports."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'
PRIOR = ROOT / 'log/20261022/decrypte_source_qualification'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_json(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def main():
    freeze = read_json('FREEZE.json')
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
              for p, h in freeze['files'].items()}
    assert all(hashes.values())
    part = read_json('PARTITIONS.json')
    data = read_json('DEVELOPMENT_VALUES.json')
    pred = read_json('PREDICTIONS.json')
    summary = read_json('SUMMARY.json')
    ids = json.loads((PRIOR / 'IDENTITIES.json').read_text(encoding='utf-8'))
    development = set(part['partitions']['development'])
    allow = {r['row']: r for r in ids['rows']
             if r['drug'] in development and r['cell'] == 'Jurkat'}
    book = PRIOR / 'supplement.xlsx'
    assert hashlib.sha256(book.read_bytes()).hexdigest() == part['source_sha256']
    decoded = []
    with zipfile.ZipFile(book) as z:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rid = next(s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
                   for s in wb.findall('s:sheets/s:sheet', NS)
                   if s.attrib['name'] == 'TableS1 - Cpd via info')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in rels if r.attrib['Id'] == rid)
        member = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        assert member == ids['member']
        # Decode only requested identity shared strings, never Effect or other rows' responses.
        shared = ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings = shared.findall('s:si', NS)
        with z.open(member) as stream:
            for _, node in ET.iterparse(stream, events=('end',)):
                if node.tag != '{' + NS['s'] + '}row':
                    continue
                index = int(node.attrib['r'])
                if index not in allow:
                    node.clear()
                    continue
                record = {'row': index, 'cells': {}}
                identity = {}
                for cell in node.findall('s:c', NS):
                    coord = cell.attrib['r']
                    col = ''.join(c for c in coord if c.isalpha())
                    if col not in {'A', 'B', 'U', *'JKLMNOPQRST'}:
                        continue
                    val = cell.find('s:v', NS)
                    assert cell.find('s:f', NS) is None and val is not None
                    if col in ('A', 'B', 'U'):
                        assert cell.attrib.get('t') == 's'
                        identity[col] = ''.join(strings[int(val.text)].itertext())
                    else:
                        assert cell.attrib.get('t', 'n') == 'n'
                        value = float(val.text)
                        assert np.isfinite(value)
                        record['cells'][col] = {'coordinate': coord, 'payload': val.text, 'value': value}
                expected = allow[index]
                assert identity == {'A': expected['drug'], 'B': 'Jurkat', 'U': expected['assay']}
                record.update(drug=identity['A'], cell=identity['B'], assay=identity['U'])
                assert set(record['cells']) == set('JKLMNOPQRST')
                decoded.append(record)
                node.clear()
    assert len(decoded) == 144
    saved = {r['row']: r for r in data['records']}
    for record in decoded:
        assert record == saved[record['row']]
    coordinates = [v['coordinate'] for r in decoded for v in r['cells'].values()]
    assert len(coordinates) == 1584 and len(set(coordinates)) == 1584
    assert coordinates == data['extracted_coordinates']
    drugs = sorted(development)
    assert drugs == data['drugs'] == summary['drugs']
    primary = {r['drug']: r for r in decoded if r['assay'] == 'Metabolic activity'}
    full_y = np.array([[primary[d]['cells'][c]['value'] for c in 'KLMNO'] for d in drugs])
    assert np.array_equal(full_y, data['y'])
    assert pred['query_indices'] == [1, 2, 3]
    assert pred['support_indices'] == {'0': [], '1': [4], '2': [0, 4]}
    truth = full_y[:, [1, 2, 3]]
    errors = {}
    largest_error = 0.
    metrics_checked = 0
    for budget in ('0', '1', '2'):
        errors[budget] = {}
        methods = dict(pred['predictions'][budget], selected=pred['selected_predictions'][budget])
        for method, raw_p in methods.items():
            p = np.array(raw_p)
            assert p.shape == (48, 3) and np.isfinite(p).all()
            e = np.square(truth - p)
            errors[budget][method] = e
            calculated = {'mse': float(e.mean()), 'mae': float(np.abs(truth - p).mean()),
                          'dose_mse': e.mean(axis=0).tolist(), 'drug_mse': e.mean(axis=1).tolist()}
            for key, value in calculated.items():
                delta = float(np.max(np.abs(np.asarray(value) - summary['metrics'][budget][method][key])))
                largest_error = max(largest_error, delta)
                metrics_checked += np.asarray(value).size
    assert largest_error < 1e-12
    chemistry = {r['drug']: r for r in part['chemical_metadata']}
    groups = [chemistry[d]['group'] for d in drugs]
    assert groups == data['groups']
    unique = sorted(set(groups))
    membership = np.array([[g == u for u in unique] for g in groups], dtype=int)
    rng = np.random.default_rng(20261022)
    frequencies = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), 10000)
    # Independent drug-weight construction rather than group-sum implementation.
    drug_weights = frequencies @ membership.T
    denom = drug_weights.sum(axis=1)
    comparison_error = 0.
    gate = {}
    for label, old in summary['comparisons'].items():
        method, rest = label.split('_B', 1)
        budget, comparator = rest.split('_vs_', 1)
        if comparator == 'same_B0':
            base_method = method
        elif comparator == 'selected_B0':
            base_method = 'selected'
        elif comparator == 'posthoc_oracle_B0':
            base_method = min(errors['0'], key=lambda m: errors['0'][m].mean())
        else:
            raise AssertionError(label)
        delta = errors['0'][base_method] - errors[budget][method]
        per_drug = delta.mean(axis=1)
        boot = (drug_weights * per_drug).sum(axis=1) / denom
        top = np.argsort(np.abs(per_drug))[-3:]
        calc = {'mean_gain': per_drug.mean(), 'ci95': np.quantile(boot, [.025, .975]),
                'ci97_5_two_budget_gate': np.quantile(boot, [.0125, .9875]),
                'dose_mean_gain': delta.mean(axis=0), 'positive_drugs': int((per_drug > 0).sum()),
                'delete_each_largest_gain_mean': [np.delete(per_drug, i).mean() for i in top]}
        assert [drugs[i] for i in top] == old['largest_absolute_gain_drugs']
        for key, value in calc.items():
            comparison_error = max(comparison_error, float(np.max(np.abs(np.asarray(value) - old[key]))))
        if method == 'selected' and comparator == 'selected_B0':
            gate[budget] = bool(calc['ci97_5_two_budget_gate'][0] > 0
                                and np.count_nonzero(calc['dose_mean_gain'] >= 0) >= 2
                                and min(calc['delete_each_largest_gain_mean']) > 0)
    assert comparison_error < 1e-12
    assert gate == {b: x['pass'] for b, x in summary['development_gate'].items()}
    assert any(gate.values()) == summary['any_budget_gate_pass']
    # Validate stored selected outer predictions/choices without refitting models.
    selections = 0
    for c in pred['choices']:
        if 'selected_method' not in c:
            continue
        group = c['outer_group']
        b = str(c['budget'])
        rows = [i for i, g in enumerate(groups) if g == group]
        options = [x for x in pred['choices'] if x.get('outer_group') == group
                   and x.get('budget') == c['budget'] and 'method' in x]
        winner = min(options, key=lambda x: x['inner_mse'])
        assert winner['method'] == c['selected_method'] and winner['hyper'] == c['hyper']
        assert np.array_equal(np.array(pred['selected_predictions'][b])[rows],
                              np.array(pred['predictions'][b][winner['method']])[rows])
        selections += 1
    result = {'status': 'PASS', 'frozen_hashes_verified': len(hashes), 'development_drugs': len(drugs),
              'decoded_rows': len(decoded), 'numeric_cells_exact': len(coordinates),
              'unopened_response_rows_decoded': 0, 'primary_query_coordinates_per_program': truth.size,
              'program_budget_prediction_arrays': 15, 'metric_scalar_components_checked': metrics_checked,
              'metric_max_abs_error': largest_error, 'comparison_max_abs_error': comparison_error,
              'bootstrap_draws': 10000, 'bootstrap_seed': 20261022, 'scaffold_groups': len(unique),
              'selection_records_checked': selections, 'development_gate': gate,
              'model_refits_independently_reproduced': False}
    (OUT / 'review/RESULT_AUDIT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
