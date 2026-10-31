"""One frozen, research-local raw-count experiment. Importing never opens data."""
import csv
import hashlib
import json
import pathlib
import warnings

import numpy as np
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, Ridge

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parents[3] / 'data/external/conditional_interventions_20261030/egi'
COUNT_SHA = '105353899a4b91bc5446bfacc20ee91a13ff6bf17f8d53805fc8bb543f2a1403'
GUIDE_SHA = '9adbe2671aa6d422f394016677b4f944c9347eacfb8bc6acb07a2b0ba184ea78'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_fold(a, b):
    a, b = sorted((a, b))
    return int(hashlib.sha256(f'MAESTRO-EGI-A1|{a}|{b}'.encode()).hexdigest()[:8], 16) % 10


def med(x, axis=None):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return np.nanmedian(x, axis=axis)


def q_from_logratio(logratio, eligible, ntc):
    """Fixed controls only; targeting doubles never enter these normalizers."""
    masked = np.where(eligible, logratio, np.nan)
    row = med(masked[:, ntc], axis=1)
    col = med(masked[ntc, :], axis=0)
    center = med(masked[np.ix_(ntc, ntc)])
    return masked - row[:, None] - col[None, :] + center


def make_source_inputs(source_counts, eligible, ntc, groups, pair_index, pseudocount=1):
    """Only one culture's T0/UT/DRUG and the frozen common T0 mask enter."""
    t0, ut, drug = source_counts
    baseline_lr = np.log2((ut + pseudocount) / (t0 + pseudocount))
    delta_lr = np.log2((drug + pseudocount) / (ut + pseudocount))
    q0 = q_from_logratio(baseline_lr, eligible, ntc)
    qd = q_from_logratio(delta_lr, eligible, ntc)
    baselines, responses = [], []
    for i, j in pair_index:
        a, b = groups[i], groups[j]
        baselines.append(med(np.r_[q0[np.ix_(a, b)].ravel(), q0[np.ix_(b, a)].ravel()]))
        responses.append(med(np.r_[qd[np.ix_(a, b)].ravel(), qd[np.ix_(b, a)].ravel()]))
    singles = []
    for lr in (baseline_lr, delta_lr):
        z = np.where(eligible, lr, np.nan)
        center = med(z[np.ix_(ntc, ntc)])
        singles.append(np.array([med(np.r_[z[np.ix_(a, ntc)].ravel(),
                                                  z[np.ix_(ntc, a)].ravel()]) - center
                                 for a in groups]))
    return np.array(baselines), np.array(responses), np.array(singles)


def source_features(baseline, singles, pairs, n_genes):
    matrix = np.zeros((n_genes, n_genes))
    i, j = pairs.T
    matrix[i, j] = matrix[j, i] = np.nan_to_num(baseline)
    u, s, _ = np.linalg.svd(matrix, full_matrices=False)
    coordinates = u[:, :8] * np.sqrt(s[:8])
    gene_features = np.column_stack([singles.T, coordinates])
    a, b = gene_features[i], gene_features[j]
    x = np.column_stack([np.nan_to_num(baseline), a + b, np.abs(a - b), a * b])
    centered = matrix - matrix.mean(axis=1, keepdims=True)
    centered /= np.maximum(np.linalg.norm(centered, axis=1, keepdims=True), 1e-12)
    cosine = np.maximum(centered @ centered.T, 0)
    np.fill_diagonal(cosine, 0)
    w = np.zeros_like(matrix)
    for g in range(n_genes):
        neighbors = np.argsort(-cosine[g], kind='stable')[:10]
        w[g, neighbors] = cosine[g, neighbors]
    w /= np.maximum(w.sum(axis=1, keepdims=True), 1e-12)
    return x, w


def choose(grid, y_dev, validation):
    assert all(np.isfinite(prediction).all() for _, prediction in grid)
    scores = [float(np.mean((p[validation] - y_dev[validation]) ** 2)) for _, p in grid]
    best = int(np.argmin(scores))
    return grid[best][1], {'parameter': grid[best][0], 'validation_mse': scores[best],
                          'grid_validation_mse': scores}


def predict_source(baseline, singles, y_dev, pairs, train, validation, n_genes):
    """y_dev has NaN test labels; neither evaluation culture nor source test labels exist here."""
    x, graph = source_features(baseline, singles, pairs, n_genes)
    mean, sd = x[train].mean(axis=0), x[train].std(axis=0)
    z = (x - mean) / np.where(sd > 0, sd, 1)
    incidence = np.zeros((len(pairs), n_genes))
    incidence[np.arange(len(pairs)), pairs[:, 0]] = 1
    incidence[np.arange(len(pairs)), pairs[:, 1]] = 1
    predictions = {'zero': np.zeros(len(pairs)),
                   'mean': np.full(len(pairs), y_dev[train].mean())}
    scaling = np.column_stack([np.ones(len(pairs)), baseline])
    predictions['baseline_rescaling'] = scaling @ np.linalg.lstsq(scaling[train], y_dev[train], rcond=None)[0]
    selected = {}
    for name, features in [('gene_ridge', incidence), ('direct_ridge', z)]:
        grid = []
        for alpha in (1, 100, 10000):
            model = Ridge(alpha=alpha).fit(features[train], y_dev[train])
            grid.append(({'alpha': alpha}, model.predict(features)))
        predictions[name], selected[name] = choose(grid, y_dev, validation)
    grid = []
    for alpha in (0.001, 0.01, 0.1):
        model = ElasticNet(alpha=alpha, l1_ratio=0.5, max_iter=3000).fit(z[train], y_dev[train])
        grid.append(({'alpha': alpha}, model.predict(z)))
    predictions['elastic_net'], selected['elastic_net'] = choose(grid, y_dev, validation)
    grid = []
    for leaves in (7, 15):
        model = HistGradientBoostingRegressor(max_leaf_nodes=leaves, l2_regularization=10,
                                             max_iter=150, learning_rate=0.05,
                                             random_state=20261031).fit(z[train], y_dev[train])
        grid.append(({'max_leaf_nodes': leaves}, model.predict(z)))
    predictions['boosting'], selected['boosting'] = choose(grid, y_dev, validation)
    i, j = pairs.T
    mask = np.zeros((n_genes, n_genes))
    mask[i[train], j[train]] = mask[j[train], i[train]] = 1
    observed = np.zeros_like(mask)
    observed[i[train], j[train]] = observed[j[train], i[train]] = y_dev[train]
    grid = []
    for rank in (2, 8, 16):
        reconstruction = observed.copy()
        for _ in range(30):
            u, s, vh = np.linalg.svd(reconstruction, full_matrices=False)
            reconstruction = (u[:, :rank] * s[:rank]) @ vh[:rank]
            reconstruction = (reconstruction + reconstruction.T) / 2
            reconstruction = np.where(mask, observed, reconstruction)
            np.fill_diagonal(reconstruction, 0)
        grid.append(({'rank': rank}, reconstruction[i, j]))
    predictions['matrix_completion'], selected['matrix_completion'] = choose(grid, y_dev, validation)
    residual = np.zeros_like(mask)
    residual[i[train], j[train]] = residual[j[train], i[train]] = (
        y_dev[train] - predictions['direct_ridge'][train])
    permutation = np.random.default_rng(20261031).permutation(n_genes)
    for name, w in [('candidate', graph), ('permuted_graph', graph[np.ix_(permutation, permutation)])]:
        numerator, denominator = w @ residual @ w.T, w @ mask @ w.T
        grid = [({'lambda': lam}, predictions['direct_ridge'] + (numerator / (denominator + lam))[i, j])
                for lam in (0.1, 1, 10)]
        predictions[name], selected[name] = choose(grid, y_dev, validation)
    return predictions, selected


def signed_hits(prediction, y1, y2):
    return ((np.abs(y1) >= 1) & (np.abs(y2) >= 1) & (np.sign(y1) == np.sign(y2))
            & (np.sign(prediction) == np.sign(y1)) & (prediction != 0))


def metrics(prediction, target, y1, y2, keep):
    assert np.isfinite(prediction).all()
    indices = np.flatnonzero(keep)
    top = indices[np.argsort(-np.abs(prediction[indices]), kind='stable')[:100]]
    hit = (np.abs(target) >= 1) & (np.sign(prediction) == np.sign(target)) & (prediction != 0)
    joint = signed_hits(prediction, y1, y2)
    return {'hits_at_100': int(hit[top].sum()), 'precision_at_100': float(hit[top].mean()),
            'negative_hits': int((hit[top] & (prediction[top] < 0)).sum()),
            'joint_confirmed_hits_descriptive': int(joint[top].sum()),
            'mse': float(np.mean((prediction[indices] - target[indices]) ** 2)),
            'mae': float(np.mean(np.abs(prediction[indices] - target[indices]))),
            'spearman': (float(spearmanr(prediction[indices], target[indices]).statistic)
                         if np.ptp(prediction[indices]) > 0 else None),
            'top_indices': top.tolist()}


def load_counts():
    import gzip
    path = DATA / '14_GI_expt1_counts.txt.gz'
    assert digest(path) == COUNT_SHA
    guide_path = HERE / 'egi_admission/guide_identity.tsv'
    assert digest(guide_path) == GUIDE_SHA
    meta = list(csv.DictReader(guide_path.open(encoding='utf-8'), delimiter='\t'))
    guides = [r['guide_identity'] for r in meta]
    index = {g: i for i, g in enumerate(guides)}
    ntc = np.array([i for i, r in enumerate(meta) if r['is_ntc'] == 'True'])
    gene_guides = {}
    for g, row in enumerate(meta):
        if row['is_ntc'] == 'False':
            gene_guides.setdefault(row['source_gene_label'], []).append(g)
    counts = np.empty((2, 3, len(guides), len(guides)))
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as handle:
        rows = csv.DictReader(handle, delimiter='\t')
        seen = set()
        for row in rows:
            a, b = row['double'].split(':')
            i, j = index[a], index[b]
            assert (i, j) not in seen
            seen.add((i, j))
            for r in range(2):
                counts[r, :, i, j] = [float(row[f'Rep{r + 1}_{label}']) for label in ('T0', 'UT', 'DRUG')]
    assert len(seen) == len(guides) ** 2
    assert np.isfinite(counts).all() and (counts >= 0).all() and np.equal(counts, np.floor(counts)).all()
    mask = (counts[:, 0] >= 30).all(axis=0)
    assert mask[np.ix_(ntc, ntc)].sum() >= 25
    good = (mask[:, ntc].sum(axis=1) >= 5) & (mask[ntc, :].sum(axis=0) >= 5)
    genes = sorted(g for g, ids in gene_guides.items() if len(ids) == 2 and good[ids].all())
    groups = [np.array(gene_guides[g]) for g in genes]
    pairs = []
    for i in range(len(genes)):
        for j in range(i + 1, len(genes)):
            ab = mask[np.ix_(groups[i], groups[j])].sum()
            ba = mask[np.ix_(groups[j], groups[i])].sum()
            if ab + ba >= 4 and ab >= 1 and ba >= 1:
                pairs.append((i, j))
    return counts, mask, ntc, genes, groups, np.array(pairs, dtype=int)


def write_support(path, scores, counts, mask, ntc, genes, groups, pairs, target):
    meta = list(csv.DictReader((HERE / 'egi_admission/guide_identity.tsv').open(encoding='utf-8'), delimiter='\t'))
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['model', 'rank', 'gene_a', 'gene_b', 'guide_a', 'guide_b', 'retained',
                         'r1_t0', 'r1_ut', 'r1_drug', 'r2_t0', 'r2_ut', 'r2_drug',
                         'eligible_a_ntc', 'eligible_ntc_b', 'eligible_ntc_ntc',
                         'target_a_ntc_ut_median', 'target_a_ntc_drug_median',
                         'target_ntc_b_ut_median', 'target_ntc_b_drug_median'])
        for name, score in scores.items():
            for rank, n in enumerate(score['top_indices'], 1):
                i, j = pairs[n]
                for first, second in ((groups[i], groups[j]), (groups[j], groups[i])):
                    for a in first:
                        for b in second:
                            an, nb = ntc[mask[a, ntc]], ntc[mask[ntc, b]]
                            writer.writerow([name, rank, genes[i], genes[j], meta[a]['guide_identity'],
                                             meta[b]['guide_identity'], bool(mask[a, b]),
                                             *counts[:, :, a, b].ravel(), len(an), len(nb),
                                             int(mask[np.ix_(ntc, ntc)].sum()),
                                             med(counts[target, 1, a, an]), med(counts[target, 2, a, an]),
                                             med(counts[target, 1, nb, b]), med(counts[target, 2, nb, b])])


def main():
    out = HERE / 'a_results'
    out.mkdir(exist_ok=False)
    counts, mask, ntc, genes, groups, pairs = load_counts()
    folds = np.array([pair_fold(genes[i], genes[j]) for i, j in pairs])
    train, validation, test = folds <= 6, folds == 7, folds >= 8
    sources = [make_source_inputs(counts[r], mask, ntc, groups, pairs) for r in range(2)]
    b = np.array([s[0] for s in sources])
    y = np.array([s[1] for s in sources])
    assert np.isfinite(y).all() and np.isfinite(b).all()
    confirmed = (np.abs(y) >= 1).all(axis=0) & (np.sign(y[0]) == np.sign(y[1]))
    qc = {'genes': len(genes), 'pairs': len(pairs), 'train': int(train.sum()),
          'validation': int(validation.sum()), 'test': int(test.sum()),
          'confirmed_strong_pairs': int(confirmed.sum()),
          'train_confirmed_strong_pairs': int(confirmed[train].sum()),
          'train_cross_culture_spearman': float(spearmanr(y[0, train], y[1, train]).statistic),
          'all_cross_culture_spearman': float(spearmanr(y[0], y[1]).statistic),
          'all_cross_culture_pearson': float(np.corrcoef(y)[0, 1]),
          'zero_fraction_by_sample': (counts == 0).mean(axis=(2, 3)).tolist(),
          'eligible_ordered_constructs': int(mask.sum()),
          'minimum_eligible_t0': float(counts[:, 0, mask].min())}
    with (out / 'endpoints.tsv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['gene_a', 'gene_b', 'fold', 'baseline_r1', 'baseline_r2', 'response_r1', 'response_r2'])
        for n, (i, j) in enumerate(pairs):
            writer.writerow([genes[i], genes[j], folds[n], *b[:, n], *y[:, n]])
    result = {'protocol': 'a_protocol_v2.md', 'qc': qc, 'status': 'DETECTABILITY_STOP',
              'biological_cultures': 2, 'directions': {}}
    gate = (len(pairs) >= 10000 and test.sum() >= 1000 and confirmed[train].sum() >= 500
            and qc['train_cross_culture_spearman'] >= 0.2)
    if gate:
        alternative_y = {p: np.array([make_source_inputs(counts[r], mask, ntc, groups, pairs, p)[1]
                                     for r in range(2)]) for p in (0.5, 2)}
        floor_pair = np.zeros((2, len(pairs)), dtype=bool)
        for r in range(2):
            low = (counts[r, 1] < 10) | (counts[r, 2] < 10)
            for n, (i, j) in enumerate(pairs):
                a, b = groups[i], groups[j]
                valid = np.r_[mask[np.ix_(a, b)].ravel(), mask[np.ix_(b, a)].ravel()]
                values = np.r_[low[np.ix_(a, b)].ravel(), low[np.ix_(b, a)].ravel()]
                floor_pair[r, n] = values[valid].mean() >= 0.5
        for source in range(2):
            y_dev = y[source].copy()
            y_dev[test] = np.nan
            predictions, selection = predict_source(b[source], sources[source][2], y_dev,
                                                   pairs, train, validation, len(genes))
            assert all(np.isfinite(prediction).all() for prediction in predictions.values())
            scores = {name: metrics(pred, y[1 - source], y[0], y[1], test)
                      for name, pred in predictions.items()}
            for score in scores.values():
                score['target_floor_pairs_in_top100'] = int(floor_pair[1 - source, score['top_indices']].sum())
            rivals = [n for n in scores if n != 'candidate']
            hits = scores['candidate']['hits_at_100']
            passed = (hits >= 20 and all(hits - scores[n]['hits_at_100'] >= 5 for n in rivals)
                      and scores['candidate']['target_floor_pairs_in_top100'] <= 20)
            sensitivity = {}
            for p, alt in alternative_y.items():
                values = {name: metrics(pred, alt[1 - source], alt[0], alt[1], test)['hits_at_100']
                          for name, pred in predictions.items()}
                sensitivity[str(p)] = values
                passed = passed and values['candidate'] >= 20 and all(
                    values['candidate'] - values[name] >= 5 for name in rivals)
            sensitivities = []
            for g in range(len(genes)):
                keep = test & (pairs[:, 0] != g) & (pairs[:, 1] != g)
                local = {n: metrics(p, y[1 - source], y[0], y[1], keep)['hits_at_100']
                         for n, p in predictions.items()}
                sensitivities.append(local['candidate'] - max(local[n] for n in rivals))
            key = f'culture{source + 1}_to_culture{2 - source}'
            write_support(out / f'{key}_top100_support.tsv', scores, counts, mask,
                          ntc, genes, groups, pairs, 1 - source)
            result['directions'][key] = {'selection': selection, 'metrics': scores,
                                        'practical_gate': bool(passed),
                                        'fixed_ranking_pseudocount_sensitivity': sensitivity,
                                        'leave_one_gene_out_gain_range': [min(sensitivities), max(sensitivities)]}
            with (out / f'{key}_predictions.tsv').open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                names = list(predictions)
                writer.writerow(['gene_a', 'gene_b', *names])
                for n in np.flatnonzero(test):
                    i, j = pairs[n]
                    writer.writerow([genes[i], genes[j], *[predictions[name][n] for name in names]])
        result['status'] = ('PRACTICAL_GATE_PASS' if all(d['practical_gate'] for d in result['directions'].values())
                            else 'PRACTICAL_GATE_FAIL')
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'qc': qc,
                      'hits': {k: {m: v['hits_at_100'] for m, v in d['metrics'].items()}
                               for k, d in result['directions'].items()}}, indent=2))


if __name__ == '__main__':
    main()
