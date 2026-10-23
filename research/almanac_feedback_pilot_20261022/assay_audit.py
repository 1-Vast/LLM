"""Independent permitted-row values/design and saved-score audit; no root imports/refits."""
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/almanac_feedback_pilot'
DATA = PHASE / 'root'
OUT = PHASE / 'assay/NUMERICAL_AUDIT.json'
DESIGN = ('SCREENER', 'STUDY', 'PLATE', 'PANELNBR', 'CELLNBR', 'NSC1', 'SAMPLE1',
          'CONC1', 'CONCUNIT1', 'NSC2', 'SAMPLE2', 'CONC2', 'CONCUNIT2', 'VALID')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def metrics(pred, truth):
    diff = pred - truth[:, :, :8]
    a, s = truth[:, :, :8].mean(2), pred.mean(2)
    k = math.ceil(a.shape[1] / 10)
    regret = []
    for actual, score in zip(a, s):
        chosen = sorted(range(len(score)), key=lambda i: (score[i], i))[:k]
        oracle = sorted(range(len(actual)), key=lambda i: (actual[i], i))[:k]
        regret.append(float(actual[chosen].mean() - actual[oracle].mean()))
    return {'mse': float((diff * diff).mean()), 'mae': float(np.abs(diff).mean()),
            'cell_mse': (diff * diff).mean((1, 2)).tolist(),
            'cell_mae': np.abs(diff).mean((1, 2)).tolist(),
            'dose_mse': (diff * diff).mean((0, 1)).tolist(),
            'cell_top10pct_regret': regret, 'mean_top10pct_regret': float(np.mean(regret))}


def close(a, b):
    np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-14)


def main():
    assert not OUT.exists()
    required = ('VALUES.npz', 'PREDICTIONS.npz', 'TUNE_PREDICTIONS.npz', 'RESULTS.json')
    assert all((DATA / f).exists() for f in required), 'Wait for root completion notification'
    freeze = json.loads((DATA / 'PRE_RESPONSE_FREEZE.json').read_text())
    for path, digest in freeze['bindings'].items():
        assert sha(ROOT / path) == digest, path
    original_path = DATA / 'PRE_RESPONSE_FREEZE_AT_VALUE_READ.json'
    original = json.loads(original_path.read_text())
    rebind = json.loads((DATA / 'POST_EXTRACTION_REVIEW_REBIND.json').read_text())
    expected_changes = {'log/20261022/almanac_feedback_pilot/skeptic/IMPLEMENTATION_REVIEW.md',
                        'log/20261022/almanac_feedback_pilot/skeptic/IMPLEMENTATION_REVIEW.seal.json'}
    assert original['bindings'].keys() == freeze['bindings'].keys()
    changes = {p for p in original['bindings'] if original['bindings'][p] != freeze['bindings'][p]}
    assert changes == expected_changes == set(rebind['changed'])
    assert sha(original_path) == rebind['old_manifest_sha256']
    for p in changes:
        assert rebind['changed'][p] == {'before_sha256': original['bindings'][p],
                                       'after_sha256': freeze['bindings'][p]}
    split = json.loads((DATA / 'SPLIT.json').read_text())
    tasks = json.loads((DATA / 'DESIGN_TASKS.json').read_text())
    selected = [[tasks[i] for i in row] for row in split['task_indices_by_cell_pair']]
    assert len(selected) == 40 and all(len(row) == 887 for row in selected)
    expected_combo = np.array([[t['combination_rows'] for t in row] for row in selected])
    expected_solo = np.array([[t['single_agent_rows'] for t in row] for row in selected])
    allowed = set(map(int, expected_combo.ravel())) | set(map(int, expected_solo.ravel()))
    assert len(allowed) == 442191
    raw, payload = {}, {}
    archive = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive/archive.zip'
    with zipfile.ZipFile(archive) as z:
        with z.open('ComboDrugGrowth_Nov2017.csv') as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            header = next(reader)
            pos = {name: header.index(name) for name in DESIGN}
            pg = header.index('PERCENTGROWTH')
            for number, row in enumerate(reader, 2):
                if number not in allowed:
                    continue
                raw[number] = {name: row[i] for name, i in pos.items()}
                payload[number] = float(row[pg]) / 100
    assert set(raw) == set(payload) == allowed
    assert np.isfinite(list(payload.values())).all()
    for row in selected:
        for t in row:
            pair = tuple(tuple(d) for d in t['pair'])
            for a in range(3):
                for b in range(3):
                    d = raw[t['combination_rows'][3 * a + b]]
                    assert [d['PANELNBR'], d['CELLNBR']] == t['cell']
                    assert (d['SCREENER'], d['STUDY'], d['PLATE'], d['VALID']) == ('FF', t['study'], t['plate'], 'Y')
                    drugs = ((d['NSC1'], d['SAMPLE1']), (d['NSC2'], d['SAMPLE2']))
                    doses = (d['CONC1'], d['CONC2'])
                    if drugs[0] > drugs[1]:
                        drugs, doses = drugs[::-1], doses[::-1]
                    assert drugs == pair
                    assert doses == (t['doses'][0][a], t['doses'][1][b])
                    assert d['CONCUNIT1'] == d['CONCUNIT2'] == 'M'
            for j, number in enumerate(t['single_agent_rows']):
                d = raw[number]
                assert [d['PANELNBR'], d['CELLNBR']] == t['cell']
                assert (d['SCREENER'], d['STUDY'], d['PLATE'], d['VALID']) == ('FF', t['study'], t['plate'], 'Y')
                assert not d['NSC2']
                assert (d['NSC1'], d['SAMPLE1']) == pair[j // 3]
                assert d['CONC1'] == t['doses'][j // 3][j % 3] and d['CONCUNIT1'] == 'M'
            for axis in t['doses']:
                assert list(map(Decimal, axis)) == sorted(set(map(Decimal, axis)))
    values = np.load(DATA / 'VALUES.npz')
    np.testing.assert_array_equal(values['combo_lines'], expected_combo)
    np.testing.assert_array_equal(values['solo_lines'], expected_solo)
    raw_y = np.array([payload[int(i)] for i in expected_combo.ravel()]).reshape(expected_combo.shape)
    raw_solo = np.array([payload[int(i)] for i in expected_solo.ravel()]).reshape(expected_solo.shape)
    np.testing.assert_array_equal(values['y'], raw_y)
    np.testing.assert_array_equal(values['solo'], raw_solo)
    result = json.loads((DATA / 'RESULTS.json').read_text())
    predictions = np.load(DATA / 'PREDICTIONS.npz')
    tune = np.load(DATA / 'TUNE_PREDICTIONS.npz')
    derived = {}
    for name in predictions.files:
        assert predictions[name].shape == (10, 887, 8)
        assert np.isfinite(predictions[name]).all()
        derived[name] = metrics(predictions[name], raw_y[30:])
        for key, number in derived[name].items():
            close(number, result['development_metrics'][name][key])
    for budget in (0, 1):
        risks = result['tune_risks'][str(budget)]
        for name, risk in risks.items():
            p = tune[f'B{budget}:{name}']
            close(((p - raw_y[20:30, :, :8]) ** 2).mean(), risk)
        selected_name = min(risks, key=risks.get)
        assert selected_name == result['choices'][str(budget)]
        np.testing.assert_array_equal(tune[f'B{budget}-selected'], tune[f'B{budget}:{selected_name}'])
        np.testing.assert_array_equal(predictions[f'B{budget}-selected'], predictions[f'B{budget}:{selected_name}'])
    np.testing.assert_array_equal(tune['B1:B0-fallback'], tune['B0-selected'])
    np.testing.assert_array_equal(predictions['B1:B0-fallback'], predictions['B0-selected'])
    gain = np.array(derived['B0-selected']['cell_mse']) - np.array(derived['B1-selected']['cell_mse'])
    rng = np.random.default_rng(20261022)
    bootstrap = gain[rng.integers(0, 10, (10000, 10))].mean(1)
    ci = np.quantile(bootstrap, [.025, .975])
    study_gain = derived['B0-study-exclusion']['mse'] - derived['B1-study-exclusion']['mse']
    gates = {'positive_mean': bool(gain.mean() > 0), 'cell_bootstrap_lower_positive': bool(ci[0] > 0),
             'at_least_seven_cells_improve': bool(sum(gain > 0) >= 7),
             'all_delete_one_cell_positive': bool(all(np.delete(gain, i).mean() > 0 for i in range(10))),
             'study_exclusion_gain_positive': bool(study_gain > 0)}
    close(gain, result['cell_gains'])
    close(gain.mean(), result['selected_gain'])
    close(ci, result['bootstrap95_fixed_predictions'])
    close(study_gain, result['study_exclusion_gain'])
    assert gates == result['gates'] and all(gates.values()) == result['advance_to_error_diagnosis']
    hist = Counter()
    for p in range(887):
        studies = [row[p]['study'] for row in selected[:30]]
        for row in selected[30:]:
            hist[str(sum(s != row[p]['study'] for s in studies))] += 1
    for recorded in result['study_exclusion_source_n_histogram'].values():
        assert dict(hist) == recorded
    summary = {'status': 'PASS', 'scope': 'Independent selected raw PG/100 and design joins; saved predictions/metrics/selection/gates; no model refit or root model imports',
               'allowed_response_column': 'PERCENTGROWTH', 'decoded_unique_rows': len(payload),
               'audited_tasks': 35480, 'combo_numeric_elements': raw_y.size, 'solo_numeric_elements': raw_solo.size,
               'predictions_checked': len(predictions.files), 'study_source_n_histogram': dict(hist),
               'selected_gain': float(gain.mean()), 'gates': gates,
               'administrative_rebind': {'independently_compared_manifest_bindings': True,
                   'changed_files_only': sorted(changes),
                   'all_other_old_bindings_unchanged': True,
                   'limitation': 'Document changes after extraction; not an uninterrupted blind freeze. Before-fitting timing is recorded provenance, not independently reconstructed from current files.'},
               'inputs_sha256': {f: sha(DATA / f) for f in required}, 'code_sha256': sha(Path(__file__))}
    OUT.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
