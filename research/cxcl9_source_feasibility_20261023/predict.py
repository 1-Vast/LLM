"""Frozen conventional passage transfer; no model choice uses target test labels."""
from datetime import datetime, timezone
import hashlib
import json
import time
import numpy as np
import pandas as pd
from source import OUT

CYTOKINES = ['None', 'IFNG', 'TNFA', 'IFNG_TNFA']
DRUGS = ['None', 'BMS-345541', 'Momelotinib', 'Salirasib', 'Taselisib', 'Trametinib']
KEYS = [(c, d) for c in CYTOKINES for d in DRUGS]
CONTROL = np.array([d == 'None' for c, d in KEYS])
FEEDBACK = np.array([d == 'None' or c == 'IFNG_TNFA' for c, d in KEYS])
TEST = ~FEEDBACK
METHODS = ['source_copy', 'control_affine', 'control_anchored_copy', 'global_affine',
           'drug_shift', 'drug_slope', 'residual_kernel', 'half_shift']
ADAPTIVE = ['global_affine', 'drug_shift', 'drug_slope', 'residual_kernel', 'half_shift']
PENALTIES = [0.0001, 0.01, 1.0]
KERNEL_CONFIGS = [(length, penalty) for length in [0.25, 1.0, 4.0] for penalty in PENALTIES]


def summarize(name, trim):
    frame = pd.read_csv(OUT/'raw'/f'00_Raw_Data_{name}.csv', keep_default_na=False)
    samples = sorted(frame['Condition'].unique())
    assert samples == ['Sample1', 'Sample2']
    values, counts = [], []
    for sample in samples:
        raw_means = []
        for cytokine, drug in KEYS:
            group = frame[(frame['Condition'] == sample) & (frame['Cytokines'] == cytokine)
                          & (frame['Inhibitors'] == drug)]['Fluorescent intensity (PE)'].to_numpy(float)
            assert len(group) > 0 and np.isfinite(group).all()
            n_raw = len(group)
            if trim:
                q1, q3 = np.quantile(group, [.25, .75])
                group = group[(group >= q1-1.5*(q3-q1)) & (group <= q3+1.5*(q3-q1))]
            assert len(group) > 0 and group.mean() > 0
            raw_means.append(float(group.mean()))
            counts.append({'file': name, 'sample': sample, 'cytokine': cytokine,
                           'drug': drug, 'raw_beads': n_raw, 'retained_beads': len(group)})
        logs = np.log10(raw_means)
        values.append(logs-logs[KEYS.index(('None', 'None'))])
    return np.array(values), counts


def anchored(source, observed):
    return np.array([observed[KEYS.index((c, 'None'))] + source[i]
                     - source[KEYS.index((c, 'None'))] for i, (c, d) in enumerate(KEYS)])


def predict(source, observed, method, config=None):
    # observed contains NaN at test positions: accidental target leakage fails loudly.
    assert np.isfinite(observed[FEEDBACK]).all() and np.isnan(observed[TEST]).all()
    if method == 'source_copy':
        return source.copy()
    if method in ['control_affine', 'global_affine']:
        mask = CONTROL if method == 'control_affine' else FEEDBACK
        design = np.column_stack([np.ones(24), source])
        coef = np.linalg.lstsq(design[mask], observed[mask], rcond=None)[0]
        return design @ coef
    base = anchored(source, observed)
    if method == 'control_anchored_copy':
        return base
    if method in ['drug_shift', 'half_shift', 'drug_slope']:
        result = base.copy()
        for drug in DRUGS[1:]:
            feedback_index = KEYS.index(('IFNG_TNFA', drug))
            residual = observed[feedback_index]-base[feedback_index]
            affected = np.array([d == drug for c, d in KEYS])
            if method in ['drug_shift', 'half_shift']:
                result[affected] += residual*(.5 if method == 'half_shift' else 1.0)
            else:
                effect = np.array([source[i]-source[KEYS.index((c, 'None'))]
                                   for i, (c, d) in enumerate(KEYS)])
                slope_delta = effect[feedback_index]*residual/(effect[feedback_index]**2+config)
                result[affected] += effect[affected]*slope_delta
        return result
    assert method == 'residual_kernel'
    length, penalty = config
    distance = np.array([[int(c != c2)+int(d != d2) for c2, d2 in KEYS] for c, d in KEYS])
    kernel = np.exp(-distance/length)
    weights = np.linalg.solve(kernel[np.ix_(FEEDBACK, FEEDBACK)]+penalty*np.eye(FEEDBACK.sum()),
                              observed[FEEDBACK]-base[FEEDBACK])
    return base+kernel[:, FEEDBACK] @ weights


def mask_feedback(values):
    observed = np.full(24, np.nan)
    observed[FEEDBACK] = values[FEEDBACK]
    return observed


def mse(prediction, truth):
    return float(np.mean((prediction[TEST]-truth[TEST])**2))


def tune(source_samples):
    configs = {'drug_slope': PENALTIES, 'residual_kernel': KERNEL_CONFIGS}
    chosen, search = {}, {}
    for method, options in configs.items():
        scores = []
        for config in options:
            errors = [mse(predict(source_samples[a], mask_feedback(source_samples[b]), method, config),
                          source_samples[b]) for a, b in [(0, 1), (1, 0)]]
            scores.append(float(np.mean(errors)))
        index = int(np.argmin(scores))
        chosen[method] = options[index]
        search[method] = [{'config': config, 'source_mse': error} for config, error in zip(options, scores)]
    selection = {}
    for method in ADAPTIVE:
        selection[method] = float(np.mean([
            mse(predict(source_samples[a], mask_feedback(source_samples[b]), method, chosen.get(method)),
                source_samples[b]) for a, b in [(0, 1), (1, 0)]]))
    selected = min(ADAPTIVE, key=lambda method: selection[method])
    return chosen, search, selection, selected


def metrics(prediction, target_samples):
    truth = target_samples.mean(axis=0)
    menus = []
    for cytokine in CYTOKINES[:3]:
        indices = [KEYS.index((cytokine, drug)) for drug in sorted(DRUGS)]
        selected = max(indices, key=lambda i: prediction[i])
        best = max(indices, key=lambda i: truth[i])
        menus.append({'cytokine': cytokine, 'selected_drug': KEYS[selected][1],
                      'best_observed_drug': KEYS[best][1],
                      'regret': float(truth[best]-truth[selected]),
                      'mse': float(np.mean([(prediction[i]-truth[i])**2 for i in indices
                                            if KEYS[i][1] != 'None']))})
    return {'mse': mse(prediction, truth), 'sample_mse': [mse(prediction, row) for row in target_samples],
            'mean_menu_regret': float(np.mean([row['regret'] for row in menus])), 'menus': menus}


if __name__ == '__main__':
    target = OUT/'PREDICTION_RESULTS.json'
    assert not target.exists(), 'Do not overwrite completed experiment'
    frozen = json.loads((OUT/'PREDICTION_FREEZE.json').read_text(encoding='utf-8'))
    root = OUT.parents[2]
    for path, expected in frozen['files'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest() == expected, path
    start = time.perf_counter()
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'variants': {}}
    saved = {}
    for variant, trim in [('within_well_iqr', True), ('untrimmed', False)]:
        rows = {}
        for cell, source_name, target_name in [('BxPC3', 'E3CA', 'E3CB'), ('AsPC1', 'E3DA', 'E3DB')]:
            source_samples, source_counts = summarize(source_name, trim)
            config, search, selection, selected = tune(source_samples)
            target_samples, target_counts = summarize(target_name, trim)
            source = source_samples.mean(axis=0)
            observed = mask_feedback(target_samples.mean(axis=0))
            predictions = {method: predict(source, observed, method, config.get(method)) for method in METHODS}
            for values in predictions.values():
                values[CONTROL] = observed[CONTROL]
            assert all(np.isfinite(values).all() for values in predictions.values())
            saved[f'{variant}/{cell}'] = {'source_samples': source_samples.tolist(),
                'target_samples': target_samples.tolist(),
                'predictions': {key: value.tolist() for key, value in predictions.items()},
                'source_counts': source_counts, 'target_counts': target_counts}
            rows[cell] = {'source_configuration_search': search, 'source_selection_scores': selection,
                          'selected_adaptive': selected, 'chosen_configs': config,
                          'models': {method: metrics(values, target_samples) for method, values in predictions.items()},
                          'target_duplicate_dispersion': float(np.mean((target_samples[0, TEST]-target_samples[1, TEST])**2))}
        result['variants'][variant] = rows
    result['wall_seconds'] = time.perf_counter()-start
    checks = []
    for variant, cells in result['variants'].items():
        for cell, row in cells.items():
            baseline = row['models']['control_anchored_copy']
            selected = row['models'][row['selected_adaptive']]
            checks.append({'variant': variant, 'cell': cell,
                           'mse_improves': selected['mse'] < baseline['mse'],
                           'regret_not_worse': selected['mean_menu_regret'] <= baseline['mean_menu_regret']})
    result['directional_checks'] = checks
    result['status'] = 'DEVELOPMENT_SUPPORTED' if all(
        row['mse_improves'] and row['regret_not_worse'] for row in checks) else 'NOT_SUPPORTED_OR_MIXED'
    (OUT/'PREDICTIONS.json').write_text(json.dumps({'keys': KEYS, 'feedback': FEEDBACK.tolist(),
        'records': saved}, indent=2), encoding='utf-8')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'wall_seconds': result['wall_seconds'],
                      'directional_checks': checks, 'primary': {cell: {
                          'selected': row['selected_adaptive'],
                          'models': {method: {'mse': value['mse'], 'regret': value['mean_menu_regret']}
                                     for method, value in row['models'].items()}}
                          for cell, row in result['variants']['within_well_iqr'].items()}}, indent=2))
