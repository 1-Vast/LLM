"""Nested ordinary predictors for conditional high-dose protein information."""
import importlib.util
import json
from pathlib import Path
import platform
import time
import numpy as np
from freeze import verify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment'
PREVIOUS = ROOT / 'log/20261022/decrypte_feedback_pilot'
GRID = (.01, .1, 1., 10.)
METHODS = ('F-Gaussian', 'F-direct', 'M-mask-direct', 'M-value-direct', 'M-both-direct',
           'M-RBF-direct', 'M-joint-PC', 'M-residual', 'M-mix')
QUERY = np.array([1, 2, 3])

# Reuse the actual previously frozen conventional Gaussian implementation.
spec = importlib.util.spec_from_file_location('prior_finite_feedback', ROOT / 'research/decrypte_feedback_pilot_20261022/run_pilot.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


class Engine:
    def __init__(self, y, chemical, proteins, groups):
        self.y = np.asarray(y)
        self.chemical = np.asarray(chemical)
        self.proteins = np.asarray(proteins)
        self.groups = np.asarray(groups)
        self.folds = {}
        self.eigens = {}
        self.residual_cache = {}

    def fold(self, train):
        key = tuple(train)
        if key in self.folds:
            return self.folds[key]
        observed = np.isfinite(self.proteins)
        tx = np.log2(1 + np.where(observed, self.proteins, 0.))
        counts = observed[train].sum(0)
        mean = (tx[train] * observed[train]).sum(0) / np.maximum(counts, 1)
        variance = (((tx[train] - mean) * observed[train]) ** 2).sum(0) / np.maximum(counts, 1)
        value_eligible = (counts / len(train) >= .8) & (variance > 1e-12)
        value = (tx[:, value_eligible] - mean[value_eligible]) / np.maximum(np.sqrt(variance[value_eligible]), 1e-6)
        value[~observed[:, value_eligible]] = 0.
        mask_mean = observed[train].mean(0)
        mask_std = observed[train].std(0)
        mask_eligible = mask_std > 1e-6
        mask = (observed[:, mask_eligible] - mask_mean[mask_eligible]) / np.maximum(mask_std[mask_eligible], 1e-6)
        k_value = value @ value.T / max(1, value.shape[1])
        k_mask = mask @ mask.T / max(1, mask.shape[1])
        combined = k_value + k_mask
        high_mean = self.y[train, 4].mean()
        high_std = max(self.y[train, 4].std(), 1e-6)
        high = ((self.y[:, 4] - high_mean) / high_std)[:, None]
        base = self.chemical + high @ high.T
        distance = np.maximum(np.diag(combined)[:, None] + np.diag(combined)[None, :] - 2 * combined, 0.)
        source_distances = distance[np.ix_(train, train)]
        positive = source_distances[source_distances > 1e-12]
        bandwidth = float(np.median(positive)) if len(positive) else None
        rbf = np.exp(-distance / (2 * bandwidth)) if bandwidth is not None else np.ones_like(distance)
        source_gram = combined[np.ix_(train, train)]
        eigenvalues, eigenvectors = np.linalg.eigh(source_gram)
        threshold = max(1e-12, (float(eigenvalues[-1]) if len(eigenvalues) else 0.) * 1e-10)
        eligible = np.flatnonzero(eigenvalues > threshold)[::-1][:max(0, min(8, len(train)-2))]
        if len(eligible):
            pc = combined[:, train] @ eigenvectors[:, eligible] / np.sqrt(eigenvalues[eligible])
            pc = (pc - pc[train].mean(0)) / np.maximum(pc[train].std(0), 1e-6)
            pc /= np.sqrt(pc.shape[1])
        else:
            pc = np.zeros((len(self.y), 0))
        pc_features = np.column_stack((high, pc))
        result = {'kernels': {'F-direct': base, 'M-mask-direct': base+k_mask,
                    'M-value-direct': base+k_value, 'M-both-direct': base+combined,
                    'M-RBF-direct': base+rbf, 'M-joint-PC': pc_features @ pc_features.T,
                    'M-residual': combined},
                  'value_eligible': value_eligible, 'mask_eligible': mask_eligible,
                  'value_mean': mean[value_eligible], 'value_scale': np.sqrt(variance[value_eligible]),
                  'pc_features': pc_features, 'pc_rank': len(eligible), 'rbf_bandwidth': bandwidth}
        self.folds[key] = result
        return result

    def gaussian(self, train, target, penalty):
        return prior.predict('gaussian', np.asarray(train), target, self.y, self.chemical,
                             1, penalty, self.y[target, [4]])

    def residuals(self, train):
        key = tuple(train)
        if key not in self.residual_cache:
            train = np.array(train)
            residuals = np.zeros((len(train), 3))
            for group in sorted(set(self.groups[train])):
                keep = train[self.groups[train] != group]
                for position in np.flatnonzero(self.groups[train] == group):
                    target = train[position]
                    residuals[position] = self.y[target, QUERY] - self.gaussian(keep, target, .1)
            self.residual_cache[key] = residuals
        return self.residual_cache[key]

    def ridge(self, train, targets, method, penalty, responses):
        key = (tuple(train), method)
        all_kernel = self.fold(train)['kernels'][method]
        kernel = all_kernel[np.ix_(train, train)]
        kmean = kernel.mean(0)
        grand = float(kmean.mean())
        centered = kernel - kmean[:, None] - kmean[None, :] + grand
        if key not in self.eigens:
            self.eigens[key] = np.linalg.eigh(centered)
        eigenvalues, eigenvectors = self.eigens[key]
        response_mean = responses.mean(0)
        coefficient = eigenvectors @ ((eigenvectors.T @ (responses-response_mean)) / (np.maximum(eigenvalues, 0.) + len(train)*penalty)[:, None])
        cross = all_kernel[np.ix_(targets, train)]
        cross = cross - cross.mean(1)[:, None] - kmean[None, :] + grand
        return response_mean + cross @ coefficient

    def predict(self, method, train, targets, penalty):
        train, targets = np.asarray(train), np.asarray(targets)
        if method == 'F-Gaussian':
            return np.stack([self.gaussian(train, t, penalty) for t in targets])
        if method == 'M-mix':
            return (self.predict('F-Gaussian', train, targets, penalty) +
                    self.predict('M-both-direct', train, targets, penalty)) / 2
        if method == 'M-residual':
            base = np.stack([self.gaussian(train, t, .1) for t in targets])
            return base + self.ridge(train, targets, method, penalty, self.residuals(train))
        return self.ridge(train, targets, method, penalty, self.y[np.ix_(train, QUERY)])


def evaluate(engine, drugs):
    start = time.perf_counter()
    groups = engine.groups
    n = len(drugs)
    predictions = {name: np.zeros((n, 3)) for name in METHODS}
    selected = {'functional': np.zeros((n, 3)), 'molecular': np.zeros((n, 3))}
    choices = []
    for outer_group in sorted(set(groups)):
        train = np.flatnonzero(groups != outer_group)
        targets = np.flatnonzero(groups == outer_group)
        grid_scores = {m: [] for m in METHODS}
        for method in METHODS:
            for penalty in GRID:
                losses = []
                for inner_group in sorted(set(groups[train])):
                    source = train[groups[train] != inner_group]
                    validation = train[groups[train] == inner_group]
                    pred = engine.predict(method, source, validation, penalty)
                    losses.extend(np.mean((pred - engine.y[np.ix_(validation, QUERY)]) ** 2, axis=1))
                grid_scores[method].append({'penalty': penalty, 'mse': float(np.mean(losses))})
            best = min(grid_scores[method], key=lambda x: x['mse'])
            predictions[method][targets] = engine.predict(method, train, targets, best['penalty'])
            choices.append({'outer_group': outer_group, 'drugs': [drugs[i] for i in targets], 'method': method,
                            'grid': grid_scores[method], 'penalty': best['penalty'], 'inner_mse': best['mse']})
        for portfolio, methods in [('functional', METHODS[:2]), ('molecular', METHODS[2:])]:
            candidates = [(m, min(grid_scores[m], key=lambda x: x['mse'])) for m in methods]
            method, best = min(candidates, key=lambda x: x[1]['mse'])
            selected[portfolio][targets] = predictions[method][targets]
            choices.append({'outer_group': outer_group, 'portfolio': portfolio, 'selected_method': method,
                            'penalty': best['penalty'], 'inner_mse': best['mse']})
    eligibility = [{'source_indices': [int(i) for i in key], 'value_columns': int(fold['value_eligible'].sum()),
                    'mask_columns': int(fold['mask_eligible'].sum()), 'pc_rank': fold['pc_rank'],
                    'rbf_bandwidth': fold['rbf_bandwidth']} for key, fold in engine.folds.items()]
    return {'predictions': {m: p.tolist() for m, p in predictions.items()},
            'selected_predictions': {m: p.tolist() for m, p in selected.items()}, 'choices': choices,
            'fold_eligibility': eligibility, 'wall_s': time.perf_counter()-start}


def summarize(engine, drugs, result, check_previous=True):
    programs = {**result['predictions'], **result['selected_predictions']}
    y = engine.y[:, QUERY]
    errors = {m: (np.array(p)-y)**2 for m, p in programs.items()}
    metrics = {m: {'mse': float(e.mean()), 'mae': float(np.abs(np.array(programs[m])-y).mean()),
                   'drug_mse': e.mean(1).tolist(), 'dose_mse': e.mean(0).tolist()} for m, e in errors.items()}
    unique = sorted(set(engine.groups))
    counts = np.array([np.sum(engine.groups == g) for g in unique])
    rng = np.random.default_rng(20261022)
    draws = rng.multinomial(len(unique), np.ones(len(unique))/len(unique), size=10000)

    def comparison(base, updated):
        diff = (errors[base]-errors[updated]).mean(1)
        totals = np.array([diff[engine.groups == g].sum() for g in unique])
        boot = draws @ totals / (draws @ counts)
        largest = np.argsort(np.abs(diff))[-3:]
        return {'mean_gain': float(diff.mean()), 'ci95': np.quantile(boot, [.025, .975]).tolist(),
                'dose_mean_gain': (errors[base]-errors[updated]).mean(0).tolist(),
                'positive_drugs': int(np.sum(diff > 0)), 'largest_absolute_gain_drugs': [drugs[i] for i in largest],
                'delete_each_largest_gain_mean': [float(np.delete(diff, i).mean()) for i in largest]}

    comparisons = {f'{m}_vs_functional': comparison('functional', m) for m in METHODS[2:]}
    comparisons['molecular_vs_functional'] = comparison('functional', 'molecular')
    comparisons['M-both_vs_M-mask'] = comparison('M-mask-direct', 'M-both-direct')
    main = comparisons['molecular_vs_functional']
    gates = {'main_ci_positive': main['ci95'][0] > 0,
             'dose_directions': sum(v >= 0 for v in main['dose_mean_gain']) >= 2,
             'delete_each_largest': min(main['delete_each_largest_gain_mean']) > 0,
             'beats_F_Gaussian': metrics['molecular']['mse'] < metrics['F-Gaussian']['mse'],
             'value_over_mask': comparisons['M-both_vs_M-mask']['mean_gain'] > 0}
    agreement = None
    if check_previous:
        old = json.loads((PREVIOUS / 'PREDICTIONS.json').read_text(encoding='utf-8'))
        agreement = {name: float(np.max(np.abs(np.array(result['predictions'][name]) - np.array(old['predictions']['1'][m]))))
                     for name, m in [('F-Gaussian', 'gaussian'), ('F-direct', 'direct')]}
    return {'metrics': metrics, 'comparisons': comparisons, 'gate': gates, 'gate_pass': bool(all(gates.values())),
            'functional_reference_max_error': agreement, 'drugs': drugs,
            'bootstrap': {'seed': 20261022, 'draws': 10000, 'unit': 'development scaffold group', 'groups': len(unique)}}


def main():
    assert (OUT / 'FREEZE.json').exists()
    verify()
    assert not (OUT / 'PREDICTIONS.json').exists()
    old = json.loads((PREVIOUS / 'DEVELOPMENT_VALUES.json').read_text(encoding='utf-8'))
    prepared = json.loads((OUT / 'PREPARATION.json').read_text(encoding='utf-8'))
    assert prepared['drugs'] == old['drugs']
    proteins = np.load(OUT / 'matrix.npz')['intensity']
    engine = Engine(old['y'], old['chemical'], proteins, old['groups'])
    result = evaluate(engine, old['drugs'])
    result['environment'] = {'python': platform.python_version(), 'numpy': np.__version__}
    (OUT / 'PREDICTIONS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = summarize(engine, old['drugs'], result)
    (OUT / 'SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    assert max(summary['functional_reference_max_error'].values()) < 1e-8, 'Functional reference disagreement blocks interpretation'
    print(json.dumps({'mse': {m: v['mse'] for m, v in summary['metrics'].items()},
                      'gate': summary['gate'], 'pass': summary['gate_pass'], 'wall_s': result['wall_s']}, indent=2), flush=True)
    # Every sensitivity rebuilds all source folds, rather than deleting OOF loss rows.
    policy = json.loads((OUT / 'IDENTITY_POLICY.json').read_text(encoding='utf-8'))
    passes = [summary['gate_pass']]
    for sensitivity in policy['sensitivities']:
        keep = np.array([i for i, d in enumerate(old['drugs']) if d not in sensitivity['exclude']])
        assert len(keep) == sensitivity['expected_n']
        subset_drugs = [old['drugs'][i] for i in keep]
        subset_engine = Engine(np.asarray(old['y'])[keep], np.asarray(old['chemical'])[np.ix_(keep, keep)],
                               proteins[keep], np.asarray(old['groups'])[keep])
        subset_result = evaluate(subset_engine, subset_drugs)
        subset_summary = summarize(subset_engine, subset_drugs, subset_result, check_previous=False)
        prefix = 'SENSITIVITY' + sensitivity['name']
        (OUT / (prefix + '_PREDICTIONS.json')).write_text(json.dumps(subset_result, ensure_ascii=False, indent=2), encoding='utf-8')
        (OUT / (prefix + '_SUMMARY.json')).write_text(json.dumps(subset_summary, ensure_ascii=False, indent=2), encoding='utf-8')
        passes.append(subset_summary['gate_pass'])
        print(json.dumps({'sensitivity': sensitivity, 'gate': subset_summary['gate'],
                          'pass': subset_summary['gate_pass'], 'wall_s': subset_result['wall_s']}, indent=2), flush=True)
    (OUT / 'JOINT_GATE.json').write_text(json.dumps({'passes': passes, 'advance': all(passes)}, indent=2), encoding='utf-8')
    print(json.dumps({'joint_advance': all(passes)}), flush=True)


if __name__ == '__main__':
    main()
