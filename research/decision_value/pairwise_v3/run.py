"""Frozen, matched-information dual-source feedback development replay."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import norm, t, ttest_1samp
from threadpoolctl import threadpool_limits

from research.decision_value.pairwise_20261009 import model as base, run as previous
from research.decision_value.pairwise_v3 import joint_residual as joint, support

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / 'research/astra/boundary_acquisition_20261007/packet2'
DEFAULT_OUT = ROOT / 'outputs/decision_value/pairwise_v3'
REPRESENTATIONS = base.REPRESENTATIONS
ARMS = ('no_update', 'knowledge_mean', 'knowledge_old', 'knowledge_refit_empirical',
        'knowledge_refit_map', 'knowledge_strong_shrink', 'molecule_refit_map',
        'Morgan_refit_map', 'permutedknowledge_refit_map', 'knowledge_prebuy_stop')
ALPHAS = (0., .01, .1, .25)
ETAS = (0., .5)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(path, root):
    for name, expected in read(path)['inputs'].items():
        if sha(root / name) != expected:
            raise ValueError('freeze_mismatch:' + name)


def freeze(out, name, files):
    write(out / name, dict(inputs={file: sha(out / file) for file in files},
                          source_freeze_sha256=sha(HERE / 'FREEZE.json')))


def reference():
    with np.load(HERE / 'PUBLIC_REFERENCE.npz') as archive:
        return {key: (archive[key].item() if archive[key].ndim == 0 else archive[key]) for key in archive.files}


def configurations(selected):
    rows = {'no_update': dict(mean_representation=None, residual_kind='old', representation=None, eta=0., alpha=0.),
            'knowledge_mean': dict(mean_representation='knowledge', residual_kind='refit', representation=None, eta=0., alpha=0.)}
    for arm, bank, rep in [('knowledge_old', 'old', None), ('knowledge_refit_empirical', 'refit', None),
                           ('knowledge_refit_map', 'refit', 'knowledge')]:
        rows[arm] = dict(mean_representation='knowledge', residual_kind=bank, representation=rep, **selected[arm])
    rows['knowledge_strong_shrink'] = dict(mean_representation='knowledge', residual_kind='refit', representation=None, eta=0., alpha=.01)
    for rep in ('molecule', 'Morgan', 'permutedknowledge'):
        rows[rep + '_refit_map'] = dict(mean_representation=rep, residual_kind='refit', representation=rep, **selected[rep + '_refit_map'])
    rows['knowledge_prebuy_stop'] = dict(rows['knowledge_refit_map'])
    return rows


def descriptor(fits, history, target, pairs, query, eigens, ref, configuration):
    rep = configuration['mean_representation']
    fitted = fits[rep or 'knowledge']
    if rep is None:
        mean_B, mean_A = joint.baseline(history, target)
    else:
        mean_B, mean_A = joint.mean(fitted, target, eigens, ref)
    matrices = fitted[configuration['residual_kind'] + '_matrices']
    matrix = matrices['empirical']
    covariance_rep = configuration['representation']
    if covariance_rep:
        matrix = base.kernel.blend(matrix, matrices[covariance_rep], configuration['eta'])
    n = len(mean_B)
    column, variance = matrix[:n, n + query], float(matrix[n + query, n + query])
    indices = np.asarray(pairs)
    i, j = indices[:, 0], indices[:, 1]
    pair_variance = matrix[i, i] + matrix[j, j] - 2 * matrix[i, j]
    diagnostics = support.assess(history['basal'], target['basal'], ref)
    return dict(mean_before=mean_B, predicted_A=float(mean_A[query]), gain=column / variance,
                variance_A=variance, pair_variance=np.maximum(pair_variance, 1e-12),
                pair_reduction=(column[i] - column[j]) ** 2 / variance,
                support=diagnostics, configuration=configuration)


def forecast(desc, observed, pairs):
    alpha = desc['configuration']['alpha']
    innovation, z, clip = 0., None, 1.
    if alpha > 0:
        if observed is None or not np.isfinite(observed):
            raise ValueError('charged_finite_A_required')
        innovation = float(observed - desc['predicted_A'])
        z = innovation / np.sqrt(desc['variance_A'])
        clip = min(1., 3. / abs(z)) if z else 1.
    effective = alpha * desc['support']['weight'] * clip
    mean = desc['mean_before'] + effective * desc['gain'] * innovation
    pair = np.asarray(pairs)
    delta = mean[pair[:, 0]] - mean[pair[:, 1]]
    variance = np.maximum(desc['pair_variance'] - effective * desc['pair_reduction'], 1e-12)
    return dict(mean=mean, pair_delta=delta, pair_variances=variance,
                alpha_effective=effective, innovation=innovation, innovation_z=z, outlier_factor=clip)


def top(values):
    return np.lexsort((np.arange(len(values)), -values))[:5].tolist()


def choose(history, kernels, eigens, mask, ref):
    inner, folds = [], []
    for fold in range(3):
        keep = [i for i in range(len(history['train_B'])) if i % 3 != fold]
        held = [i for i in range(len(history['train_B'])) if i % 3 == fold]
        training = base.training_view(history, keep)
        fits = {rep: joint.fit(training, kernels, eigens, mask, ref, rep) for rep in REPRESENTATIONS}
        folds.append(dict(keep_positions=keep, held_positions=held))
        for index in held:
            target = base.public_view(history, index)
            prior, _ = joint.baseline(training, target)
            pairs, query, _ = base.pairs_and_query(prior)
            inner.append(dict(fits=fits, history=training, target=target, pairs=pairs, query=query,
                              observed=float(history['train_A'][index, query]), outcomes=history['train_B'][index]))
    selected, tuning = {}, {}
    arms = [('knowledge_old', 'knowledge', 'old', None),
            ('knowledge_refit_empirical', 'knowledge', 'refit', None),
            ('knowledge_refit_map', 'knowledge', 'refit', 'knowledge'),
            *((r + '_refit_map', r, 'refit', r) for r in ('molecule', 'Morgan', 'permutedknowledge'))]
    for arm, mean_rep, bank, covariance_rep in arms:
        trials = []
        for eta in ETAS if covariance_rep else (0.,):
            for alpha in ALPHAS:
                cfg = dict(mean_representation=mean_rep, residual_kind=bank, representation=covariance_rep, eta=eta, alpha=alpha)
                regrets = []
                for row in inner:
                    desc = descriptor(row['fits'], row['history'], row['target'], row['pairs'], row['query'], eigens, ref, cfg)
                    pred = forecast(desc, row['observed'] if alpha > 0 else None, row['pairs'])
                    outcomes = row['outcomes']
                    regrets.append(float(np.sort(outcomes)[-5:].sum() - outcomes[top(pred['mean'])].sum()))
                trials.append(dict(alpha=alpha, eta=eta, top5_regret=float(np.mean(regrets))))
        best = min(trials, key=lambda v: (v['top5_regret'], v['alpha'], v['eta']))
        selected[arm] = dict(alpha=best['alpha'], eta=best['eta'])
        tuning[arm] = trials
    configs, scales = configurations(selected), {}
    for arm, cfg in configs.items():
        errors = []
        for row in inner:
            desc = descriptor(row['fits'], row['history'], row['target'], row['pairs'], row['query'], eigens, ref, cfg)
            pred = forecast(desc, row['observed'] if cfg['alpha'] > 0 else None, row['pairs'])
            pair = np.asarray(row['pairs'])
            truth = row['outcomes'][pair[:, 0]] - row['outcomes'][pair[:, 1]]
            errors.extend(((pred['pair_delta'] - truth) / np.sqrt(pred['pair_variances'])).tolist())
        scales[arm] = max(1., float(np.sqrt(np.mean(np.square(errors)))))
    return dict(configurations=configs, probability_scales=scales, tuning=tuning, inner_folds=folds)


def prepare(out, pilot=False):
    if out.exists():
        raise RuntimeError('refuse_overwrite')
    out.mkdir(parents=True)
    started = time.perf_counter()
    kernels, eigens, mask, metadata = previous.public_kernels()
    ref = reference()
    with np.load(PACKET / 'training_arrays.npz') as archive:
        arrays = dict(archive)
    complete = np.flatnonzero((arrays['availability_A'] & arrays['availability_B'] & arrays['state_available_B']).all(1)).tolist()
    plans, choices, forecasts, diagnostics = [], {}, {}, {}
    for held in complete[:1] if pilot else complete:
        for seed in base.SEEDS:
            for size, indices in base.histories(complete, held, seed).items():
                key = f'ref{held}__seed{seed}__n{size}'
                history, target = base.training_view(arrays, indices), base.public_view(arrays, held)
                choice = choose(history, kernels, eigens, mask, ref)
                fits = {r: joint.fit(history, kernels, eigens, mask, ref, r) for r in REPRESENTATIONS}
                prior, _ = joint.baseline(history, target)
                pairs, query, initial = base.pairs_and_query(prior)
                plans.append(dict(episode=key, context=held, seed=seed, history_size=size,
                                  history_ids=indices, pairs=pairs, query_A=query, initial_selected=initial))
                choice['descriptors'] = {}
                diagnostics[key] = {}
                for rep, fitted in fits.items():
                    diagnostics[key][rep] = dict(old_A_MSE=float(np.mean(fitted['old_error_A'] ** 2)),
                        old_B_MSE=float(np.mean(fitted['old_error_B'] ** 2)), refit_A_MSE=float(np.mean(fitted['error_A'] ** 2)),
                        refit_B_MSE=float(np.mean(fitted['error_B'] ** 2)), old_rho=fitted['old_rho'], refit_rho=fitted['refit_rho'])
                    for name in ('loo_mean_A', 'loo_mean_B', 'error_A', 'error_B'):
                        forecasts[key + '__' + rep + '__' + name] = fitted[name]
                for arm, cfg in choice['configurations'].items():
                    desc = descriptor(fits, history, target, pairs, query, eigens, ref, cfg)
                    for name in ('mean_before', 'gain', 'pair_variance', 'pair_reduction'):
                        forecasts[key + '__' + arm + '__' + name] = desc.pop(name)
                    choice['descriptors'][arm] = desc
                choices[key] = choice
        print(f'Prepared ref{held}; labels restricted to historical training views', flush=True)
    np.savez_compressed(out / 'PRE_A_ARRAYS.npz', **forecasts)
    write(out / 'PLANS.json', plans)
    write(out / 'CHOICES.json', choices)
    write(out / 'TRAINING_DIAGNOSTICS.json', diagnostics)
    write(out / 'KERNEL_METADATA.json', metadata)
    write(out / 'PREPARE_TIMING.json', dict(seconds=time.perf_counter() - started))
    freeze(out, 'PRE_A_FREEZE.json', ['PRE_A_ARRAYS.npz', 'PLANS.json', 'CHOICES.json', 'TRAINING_DIAGNOSTICS.json', 'KERNEL_METADATA.json'])


def commit(out):
    validate(out / 'PRE_A_FREEZE.json', out)
    started = time.perf_counter()
    plans, choices = read(out / 'PLANS.json'), read(out / 'CHOICES.json')
    requests = []
    for plan in plans:
        choice = choices[plan['episode']]
        for arm, cfg in choice['configurations'].items():
            buy = arm not in ('no_update', 'knowledge_mean') and (arm != 'knowledge_prebuy_stop' or cfg['alpha'] > 0)
            requests.append(dict(episode=plan['episode'], arm=arm, query_A=plan['query_A'],
                                 A_units=int(buy), status='charged_before_release' if buy else 'stopped_before_release'))
    write(out / 'POLICY_REQUESTS.json', requests)
    with np.load(PACKET / 'training_arrays.npz') as archive:
        measured_A = archive['train_A']
    with np.load(out / 'PRE_A_ARRAYS.npz') as archive:
        arrays = dict(archive)
    predictions, commitments, receipts = {}, [], []
    lookup = {(r['episode'], r['arm']): r for r in requests}
    for plan in plans:
        key, query = plan['episode'], plan['query_A']
        source_request = dict(status='charged_before_release', measurement_units=1, query_A=query)
        observed = previous.reveal(source_request, lambda q: measured_A[plan['context'], q])
        receipts.append(dict(episode=key, context=plan['context'], query_A=query, observed_A=observed, measurement_units=1))
        choice = choices[key]
        for arm in ARMS:
            desc = dict(choice['descriptors'][arm])
            for name in ('mean_before', 'gain', 'pair_variance', 'pair_reduction'):
                desc[name] = arrays[key + '__' + arm + '__' + name]
            request = lookup[(key, arm)]
            value = observed if request['A_units'] else None
            pred = forecast(desc, value, plan['pairs'])
            mean = pred.pop('mean'); prediction_key = key + '__' + arm
            predictions[prediction_key] = mean
            pair = np.asarray(plan['pairs'])
            delta, variances = pred.pop('pair_delta'), pred.pop('pair_variances')
            scale = choice['probability_scales'][arm]
            prob = norm.cdf(delta / (np.sqrt(variances) * scale))
            decisions = [int(i if d > 0 or (d == 0 and i < j) else j) for (i, j), d in zip(pair, delta)]
            commits = dict(plan, arm=arm, configuration=desc['configuration'], prediction_key=prediction_key,
                selected=top(mean), mean_only_selected=top(desc['mean_before']), cost=5 + request['A_units'],
                purchased_A=[query] if request['A_units'] else [], A_released=bool(request['A_units']),
                pair_decisions=decisions, pair_delta=delta.tolist(), pair_variances=variances.tolist(),
                pair_probabilities=prob.tolist(), probability_scale=scale, predicted_A=desc['predicted_A'],
                variance_A=desc['variance_A'], support=desc['support'], **pred)
            commitments.append(commits)
    np.savez_compressed(out / 'PREDICTIONS.npz', **predictions)
    write(out / 'A_RECEIPTS.json', receipts)
    write(out / 'COMMITMENTS.json', commitments)
    write(out / 'COMMIT_TIMING.json', dict(seconds=time.perf_counter() - started))
    freeze(out, 'COMMITMENT_FREEZE.json', ['PRE_A_FREEZE.json', 'POLICY_REQUESTS.json', 'A_RECEIPTS.json', 'PREDICTIONS.npz', 'COMMITMENTS.json'])


def relative_flips(mean, before, truth, pairs):
    indices = np.asarray(pairs); i, j = indices[:, 0], indices[:, 1]
    old_delta, new_delta, true_delta = before[i] - before[j], mean[i] - mean[j], truth[i] - truth[j]
    old = (old_delta > 0) | ((old_delta == 0) & (i < j))
    new = (new_delta > 0) | ((new_delta == 0) & (i < j))
    changed, wins = old != new, true_delta > 0
    defined = abs(true_delta) > 1e-12
    return dict(total=int(changed.sum()), corrected=int((changed & defined & (new == wins)).sum()),
                harmful=int((changed & defined & (new != wins)).sum()), ambiguous=int((changed & ~defined).sum()),
                coverage=float(changed.mean()))


def contrast(results, arm, control, metric):
    lookup = {(r['episode'], r['arm']): r for r in results}
    values = []
    for context in sorted({r['context'] for r in results}):
        episodes = [r for r in results if r['context'] == context and r['arm'] == arm]
        values.append(float(np.mean([r[metric] - lookup[(r['episode'], control)][metric] for r in episodes])))
    mean = float(np.mean(values)); n = len(values)
    ci = None
    if n > 1:
        rad = float(t.ppf(.975, n - 1) * np.std(values, ddof=1) / np.sqrt(n)); ci = [mean - rad, mean + rad]
    p = float(ttest_1samp(values, 0., alternative='greater').pvalue) if n > 1 and np.max(np.abs(values)) > 0 else 1.
    return dict(mean=mean, context_95CI=ci, one_sided_p=p, context_units=n)


def holm(comparisons):
    running = 0.
    for rank, name in enumerate(sorted(comparisons, key=lambda name: comparisons[name]['one_sided_p'])):
        running = max(running, min(1., (len(comparisons) - rank) * comparisons[name]['one_sided_p']))
        comparisons[name]['holm_p'] = running


def summarize(results):
    groups, comparisons = {}, {}
    for size in base.SIZES:
        rows = [r for r in results if r['history_size'] == size]; arms = {}
        for arm in ARMS:
            group = [r for r in rows if r['arm'] == arm]
            values = {k: float(np.mean([r[k] for r in group])) for k in ('terminal_B', 'top5_regret', 'pair_regret', 'RNA_MSE', 'flip_coverage', 'gaussian_interval_95_coverage')}
            brier = [r['brier'] for r in group if r['brier'] is not None]
            total = sum(r['feedback_relative_mean']['total'] for r in group)
            harmful = sum(r['feedback_relative_mean']['harmful'] for r in group)
            values.update(brier=float(np.mean(brier)) if brier else None, brier_defined_episodes=len(brier),
                episodes=len(group), corrected_flips=sum(r['corrected_flips'] for r in group), harmful_flips=sum(r['harmful_flips'] for r in group),
                feedback_corrected_flips=sum(r['feedback_relative_mean']['corrected'] for r in group), feedback_harmful_flips=harmful,
                feedback_flips=total, feedback_harm_fraction=harmful / total if total else None,
                feedback_coverage=float(np.mean([r['feedback_relative_mean']['coverage'] for r in group])),
                effective_updates=sum(r['alpha_effective'] > 0 for r in group), A_purchases=sum(bool(r['purchased_A']) for r in group),
                total_cost=sum(r['cost'] for r in group), eta_positive_effective=sum(r['alpha_effective'] > 0 and r['configuration']['eta'] > 0 for r in group))
            arms[arm] = values
        groups[str(size)] = arms
        comps = {control: contrast(rows, 'knowledge_refit_map', control, 'terminal_B') for control in ARMS if control != 'knowledge_refit_map'}
        comparisons[str(size)] = comps
    primary = comparisons['8']; transfer = {k: dict(primary[k]) for k in ('knowledge_mean', 'no_update', 'knowledge_old')}
    attribution = {k: dict(primary[k]) for k in ('knowledge_refit_empirical', 'knowledge_strong_shrink', 'molecule_refit_map', 'Morgan_refit_map', 'permutedknowledge_refit_map')}
    holm(transfer); holm(attribution)
    policy, baseline, mean = [groups['8'][k] for k in ('knowledge_refit_map', 'no_update', 'knowledge_mean')]
    gates = dict(positive_top5_transfer=all(r['mean'] > 0 and r['holm_p'] <= .05 for r in transfer.values()),
        meaningful_pair_regret=baseline['pair_regret'] - policy['pair_regret'] >= .001,
        feedback_harm=policy['feedback_harm_fraction'] is not None and policy['feedback_harm_fraction'] <= .1,
        feedback_coverage=policy['feedback_coverage'] >= .05,
        brier_noninferiority=policy['brier'] is not None and mean['brier'] is not None and policy['brier'] <= mean['brier'] + .01)
    transfer_pass = all(gates.values())
    knowledge_pass = transfer_pass and all(r['mean'] > 0 and r['holm_p'] <= .05 for r in attribution.values()) and policy['eta_positive_effective'] > 0
    return dict(history_sizes=groups, top5_context_comparisons=comparisons, primary_transfer_comparisons=transfer,
        primary_attribution_comparisons=attribution, transfer_gate_components=gates, transfer_gate=transfer_pass,
        knowledge_specific_gate=knowledge_pass, P2_broad_acquisition_release=transfer_pass,
        claim_boundary='Exposed transductive cached RNA development;43 context units, no functional, independent biological, calibrated conditional risk, monetary NetVOI or LLM advantage claim.')


def evaluate(out):
    validate(out / 'COMMITMENT_FREEZE.json', out)
    started = time.perf_counter()
    commits = read(out / 'COMMITMENTS.json')
    with np.load(out / 'PREDICTIONS.npz') as archive: predictions = dict(archive)
    with np.load(out / 'PRE_A_ARRAYS.npz') as archive: prepared = dict(archive)
    with np.load(PACKET / 'training_arrays.npz') as archive: truth = archive['train_B']
    results = []
    for row in commits:
        mean, outcome = predictions[row['prediction_key']], truth[row['context']]
        before = prepared[row['episode'] + '__' + row['arm'] + '__mean_before']
        results.append(dict(row, **previous.score(row, mean, outcome),
            near_equivalence_sensitivity=previous.score(row, mean, outcome, epsilon=.001),
            feedback_relative_mean=relative_flips(mean, before, outcome, row['pairs'])))
    write(out / 'RESULTS.json', results)
    write(out / 'SUMMARY.json', summarize(results))
    write(out / 'EVALUATE_TIMING.json', dict(seconds=time.perf_counter() - started))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('prepare', 'commit', 'evaluate', 'all'), default='all')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args(); validate(HERE / 'FREEZE.json', ROOT)
    phases = ('prepare', 'commit', 'evaluate') if args.phase == 'all' else (args.phase,)
    for phase in phases:
        prepare(args.out, args.pilot) if phase == 'prepare' else globals()[phase](args.out)


if __name__ == '__main__':
    with threadpool_limits(limits=1): main()
