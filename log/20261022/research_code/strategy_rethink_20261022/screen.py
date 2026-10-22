"""Finite conventional proposal-checkpoint screen; no historical module imports."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/strategy_rethink'
SOURCE = ROOT / 'research/knowledge_transfer_20261012/cache/dev_routes.npz'
ROUTES = ('context', 'pheno', 'chem', 'know')
PROGRAMS = [(feature, lam) for feature in range(4) for lam in (.1, 1., 10.)]
S0, FULL = 4, 10
SEEDS = (1729, 2718, 31415)
ARMS = ('old', 'new', 'cyclic', 'source_best', 'contextual', 'history', 'permuted')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for part in iter(lambda: handle.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)


def unit(x):
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norm, 1e-12)


def check_freeze():
    frozen = json.loads((OUT / 'FREEZE.json').read_text())
    for record in frozen['files']:
        assert sha(ROOT / record['path']) == record['sha256'], record['path']
    assert sha(SOURCE) == frozen['route_input_sha256']


def load_pack(compounds):
    """Return only explicitly requested compound rows; no old score arrays loaded."""
    with np.load(SOURCE, allow_pickle=False) as z:
        comp, line, regime = z['comp'], z['line'], z['regime']
        take = (regime == 'A') & np.isin(comp, compounds)
        pack = {'comp': comp[take], 'line': line[take]}
        raw_truth = z['truth'][take].astype(np.float64)
        assert np.isfinite(raw_truth).all(), 'nonfinite declared truth'
        pack['truth'] = unit(raw_truth)
        pack['pred'], pack['support'], pack['available'] = [], [], []
        for route in ROUTES:
            available = z[f'av_{route}'][take]
            pred = z[f'pred_{route}'][take].astype(np.float64)
            support = z[f'sup_{route}'][take].astype(np.float64)
            assert np.isfinite(pred[available]).all(), (route, 'pred')
            assert np.isfinite(support[available]).all(), (route, 'support')
            pred[~available] = 0
            support[~available] = 0
            pack['available'].append(available)
            pack['pred'].append(unit(pred))
            pack['support'].append(support)
    pack['pred'] = np.stack(pack['pred'], 1)
    pack['available'] = np.stack(pack['available'], 1)
    return pack


def subset(pack, compounds):
    take = np.isin(pack['comp'], compounds)
    return {key: [item[take] for item in value] if key == 'support' else value[take]
            for key, value in pack.items()}


def features(pack, route, kind):
    parts = []
    if kind >= 1:
        parts.append(pack['support'][route])
    if kind >= 2:
        parts.append(np.eye(9)[pack['line']])
    if kind >= 3:
        agreement = np.einsum('nd,nrd->nr', pack['pred'][:, route], pack['pred'])
        parts.append(np.where(pack['available'], agreement, 0.))
    return np.concatenate(parts, 1) if parts else np.empty((len(pack['comp']), 0))


def fit_ridge(x, y, lam):
    mean = x.mean(0)
    scale = x.std(0)
    scale[scale == 0] = 1
    a = np.column_stack((np.ones(len(x)), (x - mean) / scale))
    penalty = np.eye(a.shape[1]) * lam
    penalty[0, 0] = 0
    beta = np.linalg.solve(a.T @ a + penalty, a.T @ y)
    return {'mean': mean, 'scale': scale, 'beta': beta}


def fit_solver(cal, program):
    kind, lam = PROGRAMS[program]
    models = []
    for route in range(4):
        keep = cal['available'][:, route]
        if not keep.any():
            models.append(None)
            continue
        x = features(cal, route, kind)[keep]
        y = np.sum(cal['pred'][keep, route] * cal['truth'][keep], 1)
        models.append(fit_ridge(x, y, lam))
    return {'program': program, 'models': models}


def predict(pack, solver):
    kind = PROGRAMS[solver['program']][0]
    weights = np.zeros((len(pack['comp']), 4))
    for route, model in enumerate(solver['models']):
        if model is None:
            continue
        x = features(pack, route, kind)
        a = np.column_stack((np.ones(len(x)), (x - model['mean']) / model['scale']))
        rho = np.clip(a @ model['beta'], 0., .95)
        weights[:, route] = np.where(pack['available'][:, route], rho / (1 - rho ** 2), 0.)
    return unit(np.sum(weights[:, :, None] * pack['pred'], 1))


def score(pack, prediction):
    row = np.sum(pack['truth'] * prediction, 1)
    values = [float(np.mean(row[pack['comp'] == comp])) for comp in np.unique(pack['comp'])]
    return float(np.mean(values)), row


def descriptor(cal):
    return np.concatenate((cal['available'].mean(0), np.bincount(cal['line'], minlength=9) / len(cal['line'])))


def checkpoint(source_scores, descriptors):
    # No terminal scores are accepted by this function.
    gains = source_scores - source_scores[:, [S0]]
    logits = gains.mean(0) / .02
    allowed = np.array([j for j in range(12) if j != S0])
    permuted_logits = logits.copy()
    permuted_logits[allowed] = logits[np.random.default_rng(99173).permutation(allowed)]
    models = [fit_ridge(descriptors, gains[:, j], 10.) for j in range(12)]
    return {'logits': logits, 'permuted_logits': permuted_logits, 'models': models,
            'source_scores': source_scores, 'descriptors': descriptors,
            'desc_mean': descriptors.mean(0), 'desc_scale': np.where(descriptors.std(0) == 0, 1., descriptors.std(0))}


def nominate(arm, seed, episode, desc, learned):
    allowed = np.array([j for j in range(12) if j != S0])
    if arm in ('old', 'new', 'permuted'):
        key = f'{seed}:{episode}:{arm}'
        rng = np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))
        logits = (np.zeros(12) if arm == 'old' else learned['logits'] if arm == 'new'
                  else learned['permuted_logits'])
        chosen = []
        for _ in range(4):
            prob = np.exp(logits[allowed] - np.max(logits[allowed]))
            prob /= prob.sum()
            pick = int(rng.choice(allowed, p=prob))
            chosen.append(pick)
            allowed = allowed[allowed != pick]
        return chosen
    if arm == 'cyclic':
        return allowed[:4].tolist()
    if arm == 'source_best':
        values = learned['source_scores'].mean(0)
    elif arm == 'contextual':
        values = np.array([np.r_[1., (desc - model['mean']) / model['scale']] @ model['beta']
                           for model in learned['models']])
    else:
        distance = np.sum(((learned['descriptors'] - desc) / learned['desc_scale']) ** 2, 1)
        values = learned['source_scores'][int(np.argmin(distance))]
    return sorted(allowed.tolist(), key=lambda j: (-values[j], j))[:4]


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serial(item) for item in value]
    return value


def main():
    start = time.perf_counter()
    check_freeze()
    assert not (OUT / 'STARTED.json').exists(), 'completed/started execution may not be overwritten'
    write('STARTED.json', {'started_utc_ns': time.time_ns(), 'freeze_sha256': sha(OUT / 'FREEZE.json')})
    manifest = json.loads((OUT / 'EPISODE_MANIFEST.json').read_text())
    episodes = manifest['episodes']
    public_ids = [c for phase in episodes.values() for episode in phase
                  for split in ('calibration', 'development') for c in episode[split]]
    public = load_pack(public_ids)
    source_scores, descriptors, fit_counts = [], [], {'source': 0, 'later_before_seal': 0, 'oracle_extra': 0}
    fit_cpu = {'source': 0., 'later_before_seal': 0., 'oracle_extra': 0.}
    for episode in episodes['source']:
        cal, dev = subset(public, episode['calibration']), subset(public, episode['development'])
        scores = []
        for program in range(12):
            before = time.process_time()
            solver = fit_solver(cal, program)
            scores.append(score(dev, predict(dev, solver))[0])
            fit_cpu['source'] += time.process_time() - before
            fit_counts['source'] += 1
        source_scores.append(scores)
        descriptors.append(descriptor(cal))
    learned = checkpoint(np.array(source_scores), np.array(descriptors))
    write('SOURCE_LEARNING.json', serial(learned))
    cache, feedback, deployments = {}, {}, []

    def evaluate(episode, program, category='later_before_seal'):
        key = (episode['id'], program)
        if key not in cache:
            before = time.process_time()
            cal = subset(public, episode['calibration'])
            solver = fit_solver(cal, program)
            cache[key] = solver
            feedback[key] = score(subset(public, episode['development']), predict(subset(public, episode['development']), solver))[0]
            fit_cpu[category] += time.process_time() - before
            fit_counts[category] += 1
        return feedback[key]

    for episode in episodes['later']:
        baseline = evaluate(episode, S0)
        desc = descriptor(subset(public, episode['calibration']))
        # No terminal pack or oracle is created before every arm commits.
        for seed in SEEDS:
            for arm in ARMS:
                chosen = nominate(arm, seed, episode['id'], desc, learned)
                assert len(chosen) == len(set(chosen)) == 4 and S0 not in chosen
                observed = {S0: baseline}
                trajectory = []
                for program in chosen:
                    observed[program] = evaluate(episode, program)
                    trajectory.append({'program': program, 'development_score': observed[program]})
                deployment = min(observed, key=lambda j: (-observed[j], j))
                deployments.append({'episode': episode['id'], 'seed': seed, 'arm': arm,
                                    'start_program': S0, 'trajectory': trajectory, 'deployment': deployment})
        evaluate(episode, FULL)
    write('DEPLOYMENTS.json', deployments)
    write('DEPLOYMENT_SEAL.json', {'deployments_sha256': sha(OUT / 'DEPLOYMENTS.json'),
                                  'source_learning_sha256': sha(OUT / 'SOURCE_LEARNING.json'),
                                  'terminal_selected_for_scoring': False,
                                  'terminal_feedback_exposed': False,
                                  'earlier_full_truth_array_decoded': True,
                                  'oracle_exposed': False,
                                  'fit_counts': fit_counts.copy(), 'utc_ns': time.time_ns()})
    # Terminal slices enter scoring only beyond this on-disk seal; full-array decode occurred earlier.
    terminal = load_pack([c for episode in episodes['later'] for c in episode['evaluation']])
    all_scores, rows = {}, []
    for episode in episodes['later']:
        test = subset(terminal, episode['evaluation'])
        scores, predictions = [], []
        for program in range(12):
            evaluate(episode, program, 'oracle_extra')
            prediction = predict(test, cache[(episode['id'], program)])
            value, row = score(test, prediction)
            scores.append(value)
            predictions.append(prediction)
            rows.append({'episode': episode['id'], 'program': program, 'comp': test['comp'].tolist(),
                         'line': test['line'].tolist(), 'row_cosine': row.tolist()})
        mixture, mixrow = score(test, unit(predictions[S0] + predictions[FULL]))
        rows.append({'episode': episode['id'], 'program': 'mixture', 'comp': test['comp'].tolist(),
                     'line': test['line'].tolist(), 'row_cosine': mixrow.tolist()})
        all_scores[episode['id']] = {'program_scores': scores, 'S0': scores[S0],
                                     'full_dictionary': scores[FULL], 'mixture': mixture,
                                     'oracle': max(scores)}
    for item in deployments:
        item['terminal_score'] = all_scores[item['episode']]['program_scores'][item['deployment']]
    write('TERMINAL_ROWS.json', rows)
    write('TRAJECTORY_RESULTS.json', deployments)
    means = {arm: float(np.mean([d['terminal_score'] for d in deployments if d['arm'] == arm])) for arm in ARMS}
    for arm in ('S0', 'full_dictionary', 'mixture', 'oracle'):
        means[arm] = float(np.mean([s[arm] for s in all_scores.values()]))
    ordinary = ['old', 'cyclic', 'source_best', 'contextual', 'history', 'S0', 'full_dictionary', 'mixture']
    best = max(ordinary, key=lambda arm: means[arm])
    positive = (means['oracle'] > means['S0'] and means['new'] > means['old']
                and means['new'] > means[best])
    result = {'scope': 'CONDITIONAL_EXPOSED_BACKGROUND_NONINNOVATIVE_SCREEN',
              'episode_scores': all_scores, 'means': means,
              'new_minus_old': means['new'] - means['old'],
              'strongest_ordinary_envelope': best,
              'new_minus_strongest_ordinary': means['new'] - means[best],
              'oracle_minus_S0': means['oracle'] - means['S0'],
              'decision': 'ALLOW_SEPARATELY_FROZEN_SCREEN_ONLY' if positive else 'STOP_CURRENT_ARENA_GRAMMAR',
              'fit_counts': fit_counts, 'fit_cpu_seconds': fit_cpu,
              'logical_extra_requests': len(deployments) * 4,
              'wall_seconds': time.perf_counter() - start,
              'not_tested': ['novelty', 'functional_drug_discovery', 'world_gain', 'agent_planning',
                             'joint', 'solver_inheritance', 'strategy_invention', 'full_RSI']}
    write('RESULT.json', result)
    print(json.dumps({key: result[key] for key in ('decision', 'means', 'new_minus_old',
                      'new_minus_strongest_ordinary', 'oracle_minus_S0', 'fit_counts', 'wall_seconds')}))


if __name__ == '__main__':
    main()
