"""Independent saved-array reconstruction; never imports or executes root predictor."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261023/cxcl9_source_feasibility'
data = json.loads((OUT/'PREDICTIONS.json').read_text())
reported = json.loads((OUT/'PREDICTION_RESULTS.json').read_text())
freeze = json.loads((OUT/'PREDICTION_FREEZE.json').read_text())
keys = [tuple(x) for x in data['keys']]
control = np.array([d == 'None' for c, d in keys])
feed = np.array([d == 'None' or c == 'IFNG_TNFA' for c, d in keys])
test = ~feed
assert feed.tolist() == data['feedback'] and (control.sum(), feed.sum(), test.sum()) == (4, 9, 15)
methods = ['source_copy', 'control_affine', 'control_anchored_copy', 'global_affine',
           'drug_shift', 'drug_slope', 'residual_kernel', 'half_shift']
adaptive = methods[3:]
penalties = [0.0001, 0.01, 1.0]
kernel_grid = [(a, b) for a in [.25, 1., 4.] for b in penalties]
drugs = sorted(set(d for c, d in keys) - {'None'})
anchor_index = np.array([keys.index((c, 'None')) for c, d in keys])
assignment = np.array([[int(d == drug) for drug in drugs] for c, d in keys], float)
drug_feed = np.array([keys.index(('IFNG_TNFA', d)) for d in drugs])
distance = np.array([[sum(x != y for x, y in zip(k, l)) for l in keys] for k in keys])
comparisons = []


def check(label, actual, expected):
    a, b = np.asarray(actual, float), np.asarray(expected, float)
    assert a.shape == b.shape, label
    error = float(np.max(np.abs(a-b))) if a.size else 0.
    comparisons.append({'name': label, 'components': int(a.size), 'max_abs_difference': error})
    assert np.allclose(a, b, atol=2e-11, rtol=2e-11), (label, error)


def reconstruct(source, feedback_values, name, config=None):
    # Direct operators on allowed rows, independent of target test values.
    centered_effect = source - source[anchor_index]
    base = feedback_values[anchor_index] + centered_effect
    if name == 'source_copy':
        return source.copy()
    if name.endswith('affine'):
        mask = control if name == 'control_affine' else feed
        x, y = source[mask], feedback_values[mask]
        slope = np.dot(x-x.mean(), y-y.mean()) / np.dot(x-x.mean(), x-x.mean())
        return y.mean() + slope*(source-x.mean())
    if name == 'control_anchored_copy':
        return base
    residual = feedback_values[drug_feed] - base[drug_feed]
    if name in ('drug_shift', 'half_shift'):
        return base + assignment @ residual * (0.5 if name == 'half_shift' else 1.)
    if name == 'drug_slope':
        x = centered_effect[drug_feed]
        increments = x*residual/(x*x+config)
        return base + centered_effect*(assignment @ increments)
    assert name == 'residual_kernel'
    length, penalty = config
    kernel = np.exp(-distance/length)
    eigenvalues, eigenvectors = np.linalg.eigh(kernel[np.ix_(feed, feed)])
    residual_feedback = feedback_values[feed] - base[feed]
    coefficients = eigenvectors @ ((eigenvectors.T @ residual_feedback)/(eigenvalues+penalty))
    return base + kernel[:, feed] @ coefficients


def score(pred, truth):
    return float(np.dot((pred-truth)[test], (pred-truth)[test])/15)


def source_score(samples, method, config=None):
    errors = []
    for source, target in (samples, samples[::-1]):
        observed = np.full(24, np.nan)
        observed[feed] = target[feed]
        errors.append(score(reconstruct(source, observed, method, config), target))
    return sum(errors)/2


def metrics(pred, samples):
    truth = samples.mean(0)
    menus = []
    for cytokine in ['None', 'IFNG', 'TNFA']:
        indices = sorted([i for i, (c, d) in enumerate(keys) if c == cytokine], key=lambda i: keys[i][1])
        selected = sorted(indices, key=lambda i: (-pred[i], keys[i][1]))[0]
        best = sorted(indices, key=lambda i: (-truth[i], keys[i][1]))[0]
        noncontrols = [i for i in indices if keys[i][1] != 'None']
        menus.append({'cytokine': cytokine, 'selected_drug': keys[selected][1],
                      'best_observed_drug': keys[best][1], 'regret': float(truth[best]-truth[selected]),
                      'mse': float(np.mean((pred[noncontrols]-truth[noncontrols])**2))})
    return {'mse': score(pred, truth), 'sample_mse': [score(pred, x) for x in samples],
            'mean_menu_regret': float(np.mean([x['regret'] for x in menus])), 'menus': menus}


hash_checks = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in freeze['files'].items()}
assert len(hash_checks) == 13 and all(hash_checks.values())
rows = {}
directional = []
for record_name, record in data['records'].items():
    variant, cell = record_name.split('/')
    saved = reported['variants'][variant][cell]
    source_samples = np.asarray(record['source_samples'])
    target_samples = np.asarray(record['target_samples'])
    assert source_samples.shape == target_samples.shape == (2, 24)
    config = {}
    for name, candidates in [('drug_slope', penalties), ('residual_kernel', kernel_grid)]:
        scores = [source_score(source_samples, name, candidate) for candidate in candidates]
        config[name] = candidates[int(np.argmin(scores))]
        check(record_name+'/'+name+'/source_grid', scores,
              [x['source_mse'] for x in saved['source_configuration_search'][name]])
        assert [json.loads(json.dumps(x)) for x in candidates] == [x['config'] for x in saved['source_configuration_search'][name]]
        assert json.loads(json.dumps(config[name])) == saved['chosen_configs'][name]
    choices = {name: source_score(source_samples, name, config.get(name)) for name in adaptive}
    check(record_name+'/source_selection', list(choices.values()), [saved['source_selection_scores'][m] for m in adaptive])
    selected = sorted(adaptive, key=lambda m: (choices[m], adaptive.index(m)))[0]
    assert selected == saved['selected_adaptive']
    observed = np.full(24, np.nan)
    observed[feed] = target_samples.mean(0)[feed]
    reconstructed = {}
    for name in methods:
        pred = reconstruct(source_samples.mean(0), observed, name, config.get(name))
        pred[control] = observed[control]
        check(record_name+'/'+name+'/prediction', pred, record['predictions'][name])
        computed = metrics(pred, target_samples)
        reference = saved['models'][name]
        for metric in ['mse', 'sample_mse', 'mean_menu_regret']:
            check(record_name+'/'+name+'/'+metric, computed[metric], reference[metric])
        for a, b in zip(computed['menus'], reference['menus']):
            for label in ['cytokine', 'selected_drug', 'best_observed_drug']:
                assert a[label] == b[label], (record_name, name, label)
            for metric in ['mse', 'regret']:
                check(record_name+'/'+name+'/'+a['cytokine']+'/'+metric, a[metric], b[metric])
        reconstructed[name] = computed
    dispersion = float(np.mean((target_samples[0, test]-target_samples[1, test])**2))
    check(record_name+'/duplicate_dispersion', dispersion, saved['target_duplicate_dispersion'])
    base, chosen = reconstructed['control_anchored_copy'], reconstructed[selected]
    directional.append({'variant': variant, 'cell': cell, 'mse_improves': chosen['mse'] < base['mse'],
                        'regret_not_worse': chosen['mean_menu_regret'] <= base['mean_menu_regret']})
    rows[record_name] = {'selected_adaptive': selected, 'chosen_configs': config,
                         'source_selection_scores': choices, 'models': reconstructed}
assert directional == reported['directional_checks']
status = 'DEVELOPMENT_SUPPORTED' if all(x['mse_improves'] and x['regret_not_worse'] for x in directional) else 'NOT_SUPPORTED_OR_MIXED'
assert status == reported['status']
result = {'status': 'PASS_SAVED_ARRAY_RECONSTRUCTION', 'root_status_reconstructed': status,
          'freeze_hash_checks': hash_checks, 'comparisons': len(comparisons),
          'numeric_components': sum(x['components'] for x in comparisons),
          'max_abs_difference': max(x['max_abs_difference'] for x in comparisons),
          'directional_checks': directional, 'records': rows,
          'scope': 'Saved arrays only; independent matrix/eigendecomposition and analytic affine reconstruction. No raw aggregation audit, root import, root rerun, new biological fit or independent biological task.',
          'comparison_details': comparisons}
(OUT/'method/RESULT_AUDIT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: result[k] for k in ['status', 'root_status_reconstructed', 'comparisons', 'numeric_components', 'max_abs_difference', 'directional_checks']}, indent=2))
