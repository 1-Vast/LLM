"""Independent selected-column reconstruction and fixed-OOF audit; no model imports.

Prepared before result availability. Run only after root authorizes result audit.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/decrypte_molecular_increment'
BASE = SOURCE / 'key_correction'
OLD = ROOT / 'log/20261022/decrypte_feedback_pilot'
OUT = SOURCE / 'assay'
METHODS = ['F-Gaussian', 'F-direct', 'M-mask-direct', 'M-value-direct',
           'M-both-direct', 'M-RBF-direct', 'M-joint-PC', 'M-residual', 'M-mix']
QUERY = [1, 2, 3]
ALIASES = {'TG100-115': 'TG-100-115', 'Carboplatine': 'Carboplatin',
           'Cyclophosphamid': 'Cyclophosphamide', 'Idealisib': 'Idelalisib'}
UNCERTAIN = {'CHDI00465983': 'CHDI-0046593-0000-003', 'Gemcitabine': 'Gemcytabine'}
MAX_ERROR = 0.
CHECKED = 0


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(actual, expected, tolerance=1e-10):
    global MAX_ERROR, CHECKED
    a, b = np.asarray(actual), np.asarray(expected)
    assert a.shape == b.shape, (a.shape, b.shape)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    finite = np.isfinite(a) & np.isfinite(b)
    assert np.array_equal(np.isfinite(a), np.isfinite(b))
    error = float(np.max(np.abs(a[finite]-b[finite]))) if np.any(finite) else 0.
    MAX_ERROR = max(MAX_ERROR, error)
    CHECKED += int(a.size)
    assert error <= tolerance, (error, tolerance)


def reconstruct():
    frozen_count = 0
    for phase in (SOURCE, BASE):
        frozen = read(phase / 'FREEZE.json')
        for name, sha in frozen['files'].items():
            assert digest(ROOT / name) == sha, name
        frozen_count += len(frozen['files'])
    old = read(OLD / 'DEVELOPMENT_VALUES.json')
    partition = read(OLD / 'PARTITIONS.json')['partitions']['development']
    manifest = read(SOURCE / 'DOWNLOAD_MANIFEST.json')
    prepared = read(BASE / 'PREPARATION.json')
    saved_payloads = read(BASE / 'PAYLOADS.json')
    original_payloads = read(SOURCE / 'PAYLOADS.json')
    key_map = read(BASE / 'KEY_MAP.json')
    assert prepared['original_preparation_sha256'] == digest(SOURCE / 'PREPARATION.json')
    assert prepared['original_payloads_sha256'] == digest(SOURCE / 'PAYLOADS.json')
    policy = read(BASE / 'IDENTITY_POLICY.json')
    assert policy['aliases'] == ALIASES and policy['uncertain_file_labels'] == UNCERTAIN
    assert policy['sensitivities'] == [
        {'name': '47', 'exclude': ['CHDI00465983'], 'expected_n': 47},
        {'name': 'CERTAIN', 'exclude': ['CHDI00465983', 'Gemcitabine'], 'expected_n': 46}]
    records = manifest['records']
    assert manifest['complete'] and len(records) == 48
    assert len({r['drug'] for r in records}) == 48
    assert {r['drug'] for r in records} == set(partition) == set(old['drugs'])
    assert prepared['download_manifest_sha256'] == digest(SOURCE / 'DOWNLOAD_MANIFEST.json')
    assert prepared['source_functional_sha256'] == digest(OLD / 'DEVELOPMENT_VALUES.json')
    assert prepared['drugs'] == old['drugs']
    identified, line_positions = {}, {}
    row_total = 0
    for record in records:
        assert record['status'] in ('downloaded_unparsed', 'reused_archived_unparsed')
        path = ROOT / record['path']
        assert digest(path) == record['sha256']
        if record['status'] == 'downloaded_unparsed':
            assert str(record['http_code']) == '200'
        expected = UNCERTAIN.get(record['drug'], record['repository_drug']).strip()
        expected = ALIASES.get(expected, expected)
        values, positions, payloads, originals, mappings = {}, {}, [], [], []
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle, delimiter='\t')
            header = next(reader)
            assert len(header) == len(set(header))
            columns = [header.index(c) for c in ('identifier', 'drug', 'Normalized_Intensity_10000')]
            for line, fields in enumerate(reader, 2):
                if not fields:
                    continue
                assert len(fields) == len(header)
                original_name, raw_drug, raw = (fields[i] for i in columns)
                nominal_drug = ALIASES.get(raw_drug.strip(), raw_drug.strip())
                assert nominal_drug == expected, (record['drug'], line, raw_drug)
                prefix = raw_drug + ':'
                assert original_name.startswith(prefix), (record['drug'], line, 'prefix mismatch')
                name = original_name[len(prefix):]
                assert name and name not in values
                if raw.strip() in ('', 'NA', 'NaN', 'nan', '#N/A'):
                    number = np.nan
                else:
                    number = float(raw)
                    if not np.isfinite(number):
                        number = np.nan
                assert not np.isfinite(number) or number >= 0
                values[name], positions[name] = number, line
                payloads.append([name, line, raw])
                originals.append([original_name, line, raw])
                mappings.append([original_name, name, line])
        assert payloads == saved_payloads[record['drug']]
        assert originals == original_payloads[record['drug']]
        assert mappings == key_map[record['drug']]
        identified[record['drug']], line_positions[record['drug']] = values, positions
        row_total += len(values)
    union = sorted({name for values in identified.values() for name in values})
    assert union == prepared['identifiers']
    x = np.array([[identified[d].get(i, np.nan) for i in union] for d in old['drugs']])
    lines = np.array([[line_positions[d].get(i, 0) for i in union] for d in old['drugs']])
    with np.load(BASE / 'matrix.npz') as matrix:
        equal(x, matrix['intensity'], 0.)
        equal(lines, matrix['row_indices'], 0.)
    assert list(x.shape) == prepared['shape']
    assert int(np.isfinite(x).sum()) == prepared['finite_entries']
    assert int((~np.isfinite(x)).sum()) == prepared['missing_entries']
    assert int((x == 0).sum()) == prepared['zero_entries']
    return old, x, {'frozen_files_both_phases': frozen_count, 'selected_rows': row_total,
                    'shape': list(x.shape), 'payloads_exact': True, 'values_masks_lines_exact': True,
                    'original_to_corrected_keys_payloads_lines_exact': True}


def verify_eligibility(records, x):
    for row in records:
        source = np.array(row['source_indices'], dtype=int)
        observed = np.isfinite(x[source])
        transformed = np.log2(1+np.where(observed, x[source], 0.))
        count = observed.sum(axis=0)
        mean = transformed.sum(axis=0) / np.maximum(count, 1)
        variance = np.sum(np.where(observed, transformed-mean, 0.)**2, axis=0) / np.maximum(count, 1)
        eligible = (observed.mean(axis=0) >= .8) & (variance > 1e-12)
        mask_eligible = observed.std(axis=0) > 1e-6
        assert int(eligible.sum()) == row['value_columns']
        assert int(mask_eligible.sum()) == row['mask_columns']


def verify_result(old, x, indices, prediction_name, summary_name, previous_reference):
    p, s = read(BASE / prediction_name), read(BASE / summary_name)
    drugs = [old['drugs'][i] for i in indices]
    groups = np.array(old['groups'])[indices]
    target = np.array(old['y'])[indices][:, QUERY]
    assert drugs == s['drugs']
    programs = {**p['predictions'], **p['selected_predictions']}
    errors = {}
    for method, prediction in programs.items():
        prediction = np.array(prediction)
        assert prediction.shape == target.shape and np.all(np.isfinite(prediction))
        error = (prediction-target)**2
        errors[method] = error
        saved = s['metrics'][method]
        equal(saved['mse'], error.mean())
        equal(saved['mae'], np.abs(prediction-target).mean())
        equal(saved['drug_mse'], error.mean(axis=1))
        equal(saved['dose_mse'], error.mean(axis=0))
    unique = sorted(set(groups))
    counts = np.random.default_rng(20261022).multinomial(len(unique), [1/len(unique)]*len(unique), size=10000)
    # Explicit per-drug bootstrap multiplicities, independent of root's group-total implementation.
    weights = counts @ np.array([groups == g for g in unique], dtype=int)
    def comparison(base, changed, saved):
        difference = (errors[base]-errors[changed]).mean(axis=1)
        draws = (weights @ difference) / weights.sum(axis=1)
        equal(saved['mean_gain'], difference.mean())
        equal(saved['ci95'], np.percentile(draws, [2.5, 97.5]))
        equal(saved['dose_mean_gain'], (errors[base]-errors[changed]).mean(axis=0))
        assert saved['positive_drugs'] == int((difference > 0).sum())
        influential = np.argsort(np.abs(difference))[-3:]
        assert saved['largest_absolute_gain_drugs'] == [drugs[i] for i in influential]
        equal(saved['delete_each_largest_gain_mean'], [np.delete(difference, i).mean() for i in influential])
    for method in METHODS[2:]:
        comparison('functional', method, s['comparisons'][method+'_vs_functional'])
    comparison('functional', 'molecular', s['comparisons']['molecular_vs_functional'])
    comparison('M-mask-direct', 'M-both-direct', s['comparisons']['M-both_vs_M-mask'])
    c = s['comparisons']['molecular_vs_functional']
    gates = {'main_ci_positive': c['ci95'][0] > 0,
             'dose_directions': sum(v >= 0 for v in c['dose_mean_gain']) >= 2,
             'delete_each_largest': min(c['delete_each_largest_gain_mean']) > 0,
             'beats_F_Gaussian': s['metrics']['molecular']['mse'] < s['metrics']['F-Gaussian']['mse'],
             'value_over_mask': s['comparisons']['M-both_vs_M-mask']['mean_gain'] > 0}
    assert gates == s['gate'] and bool(all(gates.values())) == s['gate_pass']
    assert s['bootstrap']['groups'] == len(unique)
    choice_count = 0
    for group in unique:
        rows = [r for r in p['choices'] if r['outer_group'] == group]
        methods = {r['method']: r for r in rows if 'method' in r}
        assert set(methods) == set(METHODS)
        for method, row in methods.items():
            assert row['drugs'] == [d for d, g in zip(drugs, groups) if g == group]
            assert [r['penalty'] for r in row['grid']] == [.01, .1, 1., 10.]
            best = min(row['grid'], key=lambda item: item['mse'])
            assert row['penalty'] == best['penalty'] and row['inner_mse'] == best['mse']
        for portfolio, menu in [('functional', METHODS[:2]), ('molecular', METHODS[2:])]:
            selected = next(r for r in rows if r.get('portfolio') == portfolio)
            winner = min(menu, key=lambda m: methods[m]['inner_mse'])
            assert selected['selected_method'] == winner
            assert selected['penalty'] == methods[winner]['penalty']
            equal(selected['inner_mse'], methods[winner]['inner_mse'], 0.)
            equal(np.array(p['selected_predictions'][portfolio])[groups == group],
                  np.array(p['predictions'][winner])[groups == group], 0.)
            choice_count += 1
    verify_eligibility(p['fold_eligibility'], x[indices])
    if previous_reference:
        prior = read(OLD / 'PREDICTIONS.json')['predictions']['1']
        for current, old_name in [('F-Gaussian', 'gaussian'), ('F-direct', 'direct')]:
            delta = float(np.max(np.abs(np.array(p['predictions'][current])-np.array(prior[old_name]))))
            equal(delta, s['functional_reference_max_error'][current])
            assert delta < 1e-8
    else:
        assert s['functional_reference_max_error'] is None
    return {'drugs': len(drugs), 'groups': len(unique), 'gates': gates,
            'gate_pass': s['gate_pass'], 'portfolio_choices': choice_count,
            'fold_eligibility_records': len(p['fold_eligibility'])}


def main():
    old, x, data = reconstruct()
    primary = verify_result(old, x, np.arange(48), 'PREDICTIONS.json', 'SUMMARY.json', True)
    keep = np.array([i for i, d in enumerate(old['drugs']) if d != 'CHDI00465983'])
    assert len(keep) == 47
    sensitivity = verify_result(old, x, keep, 'SENSITIVITY47_PREDICTIONS.json', 'SENSITIVITY47_SUMMARY.json', False)
    certain = np.array([i for i, d in enumerate(old['drugs']) if d not in UNCERTAIN])
    assert len(certain) == 46
    subset = verify_result(old, x, certain, 'SENSITIVITYCERTAIN_PREDICTIONS.json', 'SENSITIVITYCERTAIN_SUMMARY.json', False)
    passes = [primary['gate_pass'], sensitivity['gate_pass'], subset['gate_pass']]
    joint = read(BASE / 'JOINT_GATE.json')
    assert joint == {'passes': passes, 'advance': all(passes)}
    report = {'status': 'PASS', 'data': data, 'primary48': primary, 'sensitivity47': sensitivity,
              'certain46': subset, 'joint_advance': all(passes),
              'numeric_components_checked': CHECKED, 'max_absolute_error': MAX_ERROR,
              'scope': 'Independent exact original-to-corrected key and selected-column data/mask/payload reconstruction; both freezes; corrected fixed-OOF metrics/bootstrap/gates, choice consistency and source eligibility counts. No root imports or independent model/inner-risk refits; no full PCA/RBF arithmetic reproduction.'}
    (OUT / 'KEY_CORRECTED_RESULT_AUDIT.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
