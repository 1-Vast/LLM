"""Independent H_FI-v1 replay. No imports from or reads of the primary implementation."""
import csv
import hashlib
import io
import json
import sys
import time
import traceback
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
PREFIX = 'independent_hfi_'
FAMILIES = ['constant', 'knn5', 'knn20', 'knn50', 'pav_increasing', 'pav_decreasing']
RAW_SHA = 'e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259'
MEMBER = 'combo_well_stats_GDSC_007_05May22.csv'
START_WALL = time.perf_counter()
START_CPU = time.process_time()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(name, obj):
    path = BASE / (PREFIX + name + '.json')
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def budget():
    if time.process_time() - START_CPU > 120 or time.perf_counter() - START_WALL > 180:
        raise RuntimeError('Resource polling guard exceeded')


def pav(x, labels, direction):
    # Input order is lexical cell ID; stable sort keeps that order inside ties.
    order = np.argsort(direction * x, kind='stable')
    xx, yy = (direction * x)[order], labels[order]
    groups = []
    for value, outcome in zip(xx, yy):
        if groups and value == groups[-1][0]:
            groups[-1][1] += 1
            groups[-1][2] += float(outcome)
        else:
            groups.append([float(value), 1, float(outcome)])
    blocks = []
    for value, weight, positive in groups:
        blocks.append([weight, positive, float(weight * value)])
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][0] > blocks[-1][1] / blocks[-1][0]:
            right = blocks.pop()
            left = blocks.pop()
            blocks.append([left[k] + right[k] for k in range(3)])
    return {'direction': direction, 'centers': [b[2] / b[0] for b in blocks],
            'probabilities': [b[1] / b[0] for b in blocks],
            'weights': [b[0] for b in blocks]}


def pav_predict(model, query):
    return np.interp(model['direction'] * query, model['centers'], model['probabilities'])


def neighbors(x, query):
    # x is in lexical cell-ID order; stable distance sort supplies the second key.
    return np.argsort(np.abs(query[:, None] - x[None, :]), axis=1, kind='stable')


def family_predictions(x, labels, query, near):
    out = np.empty((6, len(query)), dtype=np.float64)
    out[0] = float(np.mean(labels))
    for index, k in enumerate((5, 20, 50), 1):
        out[index] = np.mean(labels[near[:, :min(k, len(x))]], axis=1)
    out[4] = pav_predict(pav(x, labels, 1), query)
    out[5] = pav_predict(pav(x, labels, -1), query)
    return out


def fit_model(x, labels, kind):
    model = {'family': FAMILIES[kind]}
    if kind == 0:
        model['probability'] = float(np.mean(labels))
    elif kind < 4:
        model.update(k=(5, 20, 50)[kind - 1], x=x.tolist(), labels=labels.tolist())
    else:
        model.update(pav(x, labels, 1 if kind == 4 else -1))
    return model


def predict_model(model, query):
    family = model['family']
    if family == 'constant':
        return np.full(len(query), model['probability'])
    if family.startswith('knn'):
        x = np.asarray(model['x'])
        y = np.asarray(model['labels'])
        return np.mean(y[neighbors(x, query)[:, :min(model['k'], len(x))]], axis=1)
    return pav_predict(model, query)


def selfcheck():
    # No source-data access. Hand-computed duplicate/PAV block-center fixture.
    model = pav(np.array([0., 0., 1., 2.]), np.array([1, 1, 0, 1]), 1)
    assert model['weights'] == [3, 1]
    assert np.allclose(model['centers'], [1 / 3, 2])
    assert np.allclose(pav_predict(model, np.array([-1., 7 / 6, 3.])), [2 / 3, 5 / 6, 1])
    one = pav(np.array([0., 1.]), np.array([1, 0]), 1)
    assert np.array_equal(pav_predict(one, np.array([-10., 10.])), [.5, .5])
    tie = neighbors(np.array([0., 2., 0.]), np.array([1.]))
    assert tie.tolist() == [[0, 1, 2]]
    decreasing = pav(np.array([0., 1.]), np.array([1, 0]), -1)
    assert np.array_equal(pav_predict(decreasing, np.array([0., 1.])), [1., 0.])
    print('4 fixed-array engineering fixtures passed; no data opened')


def project_raw(menu):
    archive = ROOT / 'tmp' / 'extq1' / 'gsdc_well_stats.zip'
    assert sha(archive) == RAW_SHA, 'Archive identity mismatch before member/header read'
    selected = {}
    for c in menu['cells']:
        for drug in menu['drugs']:
            key = ('2', c['cell'], c['refs'][drug], Decimal(menu['doses_uM'][drug]))
            assert key not in selected
            selected[key] = (c['cell'], drug)
    values, counts, side_counts = {}, Counter(), Counter()
    raw_rows = 0
    with zipfile.ZipFile(archive) as container:
        info = container.getinfo(MEMBER)
        with container.open(info) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            header = next(reader)
            allowed = ['PROJECT_ID', 'MASTER_CELL_ID'] + [
                f'lib{s}_{field}' for s in (1, 2) for field in ('drug_id', 'drug', 'conc', 'y')]
            assert all(header.count(field) == 1 for field in allowed), 'Missing/duplicate whitelist header'
            pos = {field: header.index(field) for field in allowed}
            save('header_receipt', {'archive_sha256': RAW_SHA, 'member': MEMBER,
                                    'member_bytes': info.file_size, 'member_CRC': info.CRC,
                                    'header': header, 'accessed_fields': allowed,
                                    'CELL_LINE_ID_present': 'CELL_LINE_ID' in header})
            for row in reader:
                raw_rows += 1
                if raw_rows % 10000 == 0:
                    budget()
                project = row[pos['PROJECT_ID']]
                cell = row[pos['MASTER_CELL_ID']]
                if project != '2':
                    continue
                for side in (1, 2):
                    drug = row[pos[f'lib{side}_drug_id']]
                    ref = row[pos[f'lib{side}_drug']]
                    conc = Decimal(row[pos[f'lib{side}_conc']])
                    if not conc.is_finite():
                        continue
                    key = (project, cell, ref, conc)
                    if key not in selected:
                        continue
                    assert drug == selected[key][1], 'Frozen key/drug identity conflict'
                    text = row[pos[f'lib{side}_y']]
                    try:
                        number = Decimal(text)
                    except Exception as exc:
                        raise ValueError('Selected response missing/invalid') from exc
                    assert number.is_finite(), 'Selected response nonfinite'
                    if key in values:
                        assert values[key][0] == text, 'Selected repeated response raw-string conflict'
                        assert values[key][1] == number, 'Selected repeated response Decimal conflict'
                    else:
                        values[key] = (text, number)
                    counts[key] += 1
                    side_counts[str(side)] += 1
    assert set(values) == set(selected), 'Selected response missing'
    projection = []
    for key, (cell, drug) in sorted(selected.items()):
        text, number = values[key]
        projection.append({'cell': cell, 'drug': drug, 'ref': key[2], 'dose_uM': str(key[3]),
                           'raw_y': text, 'label': int(number >= Decimal('.5')),
                           'occurrences': counts[key]})
    path = save('raw_projection', projection)
    save('qc', {'raw_rows': raw_rows, 'selected_unique_coordinates': len(values),
                'selected_occurrences': sum(counts.values()), 'side_occurrences': dict(side_counts),
                'all_repeated': all(counts[k] > 1 for k in selected),
                'minimum_repetitions': min(counts.values()), 'maximum_repetitions': max(counts.values()),
                'string_conflicts': 0, 'Decimal_conflicts': 0, 'missing': 0, 'nonfinite': 0,
                'out_of_unit_interval': sum(not Decimal(0) <= v[1] <= Decimal(1) for v in values.values()),
                'projection_sha256': sha(path), 'only_selected_y_semantically_accessed': True,
                'repetitions_are_copies_not_biological_replicates': True})
    # Oracle stores all selected development values only for QC/evaluation, separately by role.
    by_coord = {(r['cell'], r['drug']): r for r in projection}
    split = {}
    for role in ('train', 'development'):
        cells = [c for c in menu['cells'] if c['role'] == role]
        split[role] = {'cells': cells,
                       'x': np.array([[float(by_coord[(c['cell'], d)]['raw_y']) for d in menu['drugs']] for c in cells]),
                       'labels': np.array([[by_coord[(c['cell'], d)]['label'] for d in menu['drugs']] for c in cells], dtype=np.int8)}
    return split


def choose_training(train, drugs):
    x, labels = train['x'], train['labels']
    folds = np.array([c['inner_fold'] for c in train['cells']])
    n, d = x.shape
    all_oof = np.full((d, d, 6, n), np.nan)
    blind = np.zeros((n, d), dtype=bool)
    for fold in range(5):
        fit, val = folds != fold, folds == fold
        assert fit.any() and val.any(), 'Empty frozen inner training/validation fold'
        blind[val] = np.mean(labels[fit], axis=0) >= .5
        for j in range(d):
            near = neighbors(x[fit, j], x[val, j])
            for t in range(d):
                if j != t:
                    all_oof[j, t][:, val] = family_predictions(x[fit, j], labels[fit, t], x[val, j], near)
        budget()
    chosen = np.full((d, d), -1, dtype=np.int8)
    predicted = np.zeros((d, d, n), dtype=bool)
    models, selection = {}, []
    for j in range(d):
        for t in range(d):
            if j == t:
                continue
            errors = np.count_nonzero((all_oof[j, t] >= .5) != labels[:, t], axis=1)
            k = int(np.argmin(errors))
            chosen[j, t] = k
            predicted[j, t] = all_oof[j, t, k] >= .5
            selection.append({'input': drugs[j], 'target': drugs[t],
                              'family_errors': dict(zip(FAMILIES, errors.tolist())),
                              'selected': FAMILIES[k], 'selected_errors': int(errors[k])})
            models[drugs[j] + '->' + drugs[t]] = fit_model(x[:, j], labels[:, t], k)
    entries, pairs = [], []
    for a in range(d):
        for b in range(a + 1, d):
            support = [int(np.count_nonzero((labels[:, a] == av) & (labels[:, b] == bv)))
                       for av, bv in ((0, 0), (0, 1), (1, 0), (1, 1))]
            supported = min(support) >= 10
            pairs.append({'a': drugs[a], 'b': drugs[b], 'state_counts_00_01_10_11': support, 'eligible': supported})
            if not supported:
                continue
            da = int(np.count_nonzero(predicted[a, b] != labels[:, b]))
            db = int(np.count_nonzero(predicted[b, a] != labels[:, a]))
            bl = int(np.count_nonzero(blind[:, a] != labels[:, a]) + np.count_nonzero(blind[:, b] != labels[:, b]))
            for q in range(d):
                if q in (a, b):
                    continue
                ref = int(np.count_nonzero(predicted[q, a] != labels[:, a]) + np.count_nonzero(predicted[q, b] != labels[:, b]))
                margins = [da - ref, db - ref, bl - ref]
                entries.append({'a': drugs[a], 'b': drugs[b], 'q': drugs[q],
                                'error_totals': {'reference': ref, 'direct_a': da, 'direct_b': db, 'blind': bl},
                                'margin_integer_by_opponent': margins, 'minimum_margin_integer': min(margins),
                                'minimum_margin_mean_two_label_loss': min(margins) / (2 * n)})
    best = min(entries, key=lambda e: (-e['minimum_margin_integer'], e['a'], e['b'], e['q'])) if entries else None
    np.savez_compressed(BASE / (PREFIX + 'oof.npz'), all_probabilities=all_oof,
                        selected_family=chosen, selected_predictions=predicted, blind_predictions=blind,
                        train_cells=np.array([c['cell'] for c in train['cells']]), train_labels=labels,
                        drugs=np.array(drugs), family_order=np.array(FAMILIES))
    paths = [save('model_selection', selection), save('pair_support', pairs),
             save('candidate_triples', entries), save('final_models', models)]
    freeze = {'best': best, 'eligible_pairs': sum(p['eligible'] for p in pairs),
              'eligible_triples': len(entries), 'train_cells': n, 'development_effects_used': False,
              'artifact_sha256': {p.name: sha(p) for p in paths},
              'oof_sha256': sha(BASE / (PREFIX + 'oof.npz'))}
    frozen = save('selection_freeze', freeze)
    return best, models, sha(frozen)


def evaluate(dev, train, drugs, best, models):
    a, b, q = (drugs.index(best[k]) for k in ('a', 'b', 'q'))
    n = len(dev['cells'])
    truth = dev['labels'][:, [a, b]]
    counts = [[int(np.count_nonzero(truth[:, k] == y)) for y in (0, 1)] for k in (0, 1)]
    if n < 50 or min(sum(counts, [])) < 5:
        return {'status': 'development_design_insufficient', 'class_counts': counts, 'n_development': n}
    x = dev['x']
    predictions = {}
    probabilities = {}
    for policy, inp in (('reference', q), ('direct_a', a), ('direct_b', b)):
        probs = np.zeros((n, 2))
        for column, target in enumerate((a, b)):
            probs[:, column] = truth[:, column] if inp == target else predict_model(models[drugs[inp] + '->' + drugs[target]], x[:, inp])
        probabilities[policy] = probs
        predictions[policy] = probs >= .5
    rates = np.mean(train['labels'][:, [a, b]], axis=0)
    probabilities['blind'] = np.tile(rates, (n, 1))
    predictions['blind'] = probabilities['blind'] >= .5
    losses = {policy: np.mean(pred != truth, axis=1) for policy, pred in predictions.items()}
    rng = np.random.Generator(np.random.PCG64(20261029))
    samples = rng.integers(0, n, size=(1999, n))
    comparisons = {}
    for opponent in ('direct_a', 'direct_b', 'blind'):
        differences = losses[opponent] - losses['reference']
        boot = np.mean(differences[samples], axis=1)
        comparisons[opponent] = {'mean_loss_reduction': float(np.mean(differences)),
                                 'bootstrap_lower_025': float(np.quantile(boot, .025, method='linear')),
                                 'mean_gate': bool(np.mean(differences) >= .025),
                                 'composition_lower_gate': bool(np.quantile(boot, .025, method='linear') > 0)}
    records = []
    for i, cell in enumerate(dev['cells']):
        for policy, inp in (('reference', q), ('direct_a', a), ('direct_b', b), ('blind', q)):
            records.append({'cell': cell['cell'], 'policy': policy, 'action': drugs[inp],
                            'paid_unique_exported_coordinates': 1, 'action_value': float(x[i, inp]),
                            'value_used_for_prediction': policy != 'blind',
                            'probabilities': probabilities[policy][i].tolist(),
                            'predictions': predictions[policy][i].astype(int).tolist(),
                            'oracle_labels': truth[i].tolist(), 'loss': float(losses[policy][i])})
    save('development_policy_log', records)
    np.savez_compressed(BASE / (PREFIX + 'bootstrap.npz'), indices=samples)
    passed = all(v['mean_gate'] and v['composition_lower_gate'] for v in comparisons.values())
    return {'status': 'development_supported' if passed else 'not_supported',
            'class_counts': counts, 'n_development': n, 'comparisons': comparisons,
            'mean_losses': {k: float(np.mean(v)) for k, v in losses.items()},
            'dual_direct_reference': {'coordinates_per_cell': 2, 'exported_label_loss': 0}}


def run():
    expected = json.loads((BASE / 'independent_hfi_implementation_freeze.json').read_text(encoding='utf-8'))
    assert sha(Path(__file__)) == expected['script_sha256'], 'Independent script changed after freeze'
    for filename, digest in expected['input_sha256'].items():
        assert sha(BASE / filename) == digest, 'Frozen authorized input changed: ' + filename
    menu = json.loads((BASE / 'menu_roles_frozen.json').read_text(encoding='utf-8'))
    cells = menu['cells']
    assert len(cells) == 732 and len(menu['drugs']) == 11
    assert [c['cell'] for c in cells] == sorted(set(c['cell'] for c in cells))
    for c in cells:
        role = 'train' if int(hashlib.sha256(('HFI-v1|' + c['cell']).encode()).hexdigest(), 16) % 10 < 7 else 'development'
        fold = int(hashlib.sha256(('HFI-inner-v1|' + c['cell']).encode()).hexdigest(), 16) % 5
        assert role == c['role'] and fold == c['inner_fold']
    save('role_log', {'cells': cells, 'drugs': menu['drugs'], 'doses_uM': menu['doses_uM'],
                      'all_development_effects_unavailable_to_training_api': True})
    split = project_raw(menu)
    best, models, freeze_sha = choose_training(split['train'], menu['drugs'])
    result = {'selection_freeze_sha256': freeze_sha, 'best': best,
              'costs': {'training_actual_search_coordinates': len(split['train']['cells']) * 11,
                        'reference_fixed_task_history_coordinates': len(split['train']['cells']) * 3,
                        'direct_fixed_task_history_coordinates_each': len(split['train']['cells']) * 2,
                        'blind_fixed_task_history_coordinates': len(split['train']['cells']) * 2,
                        'all_development_oracle_QC_coordinates': len(split['development']['cells']) * 11,
                        'deployment_coordinates_per_cell_each_policy_if_entered': 1},
              'development_effects_evaluated': False,
              'limitations': 'Same-screen processed export replay; no biological independence, real well saving, or new algorithm claim.'}
    if best is None or best['minimum_margin_integer'] <= 0:
        result['status'] = 'training_precondition_absent'
    else:
        result.update(evaluate(split['development'], split['train'], menu['drugs'], best, models))
        result['development_effects_evaluated'] = True
    save('result', result)
    print(json.dumps({'status': result['status'], 'best': best, 'development_effects_evaluated': result['development_effects_evaluated']}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--selfcheck']:
        selfcheck()
    else:
        status = 'completed'
        try:
            run()
        except Exception as exc:
            status = 'failed'
            save('failure', {'exception_type': type(exc).__name__, 'message': str(exc),
                             'traceback': traceback.format_exc(), 'no_retry_authorized': True})
            raise
        finally:
            save('process_receipt', {'status': status, 'CPU_seconds': time.process_time() - START_CPU,
                                     'wall_seconds': time.perf_counter() - START_WALL,
                                     'numpy_version': np.__version__, 'python_version': sys.version,
                                     'requested_model': 'Sol', 'requested_effort': 'high',
                                     'effective_model_effort_usage_fees': 'unknown',
                                     'network_actions': 0, 'raw_effect_runs': 1, 'primary_reads': 0})
