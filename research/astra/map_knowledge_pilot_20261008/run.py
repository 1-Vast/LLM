"""Frozen, exposed-data MAP-inspired representation pilot; no MAP reproduction claim."""
import ast
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.feature_extraction.text import HashingVectorizer
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / 'research/astra/boundary_acquisition_20261007/packet2'
sys.path.insert(0, str(ROOT / 'research/astra/boundary_acquisition_20261007'))
from method import reference_row


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def top(mean):
    return np.lexsort((np.arange(len(mean)), -mean))[:5]


def representations(labels):
    acquisition = json.loads((HERE / 'ACQUISITION.json').read_text())
    raw = ROOT / acquisition['local_raw']
    edges = ROOT / acquisition['edges']['local_raw']
    assert sha(raw) == acquisition['sha256']
    assert sha(edges) == acquisition['edges']['sha256']
    index = {}
    for row in csv.DictReader(raw.open(encoding='utf-8-sig')):
        index.setdefault(row['Drug Name'].strip().casefold(), []).append(row)
    names = [ast.literal_eval(label)[0][0].strip().casefold() for label in labels]
    matched = {name: index[name][0] for name in set(names) if len(index.get(name, [])) == 1}
    ids = {row['PubChem ID'] for row in matched.values()}
    relations = {i: [] for i in ids}
    for row in csv.DictReader(edges.open(encoding='utf-8-sig')):
        if row['Drug ID'] in ids:
            relations[row['Drug ID']].append(row['relation'] + ' ' + row['Gene ID'])
    fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=256)
    hasher = HashingVectorizer(n_features=128, alternate_sign=True, norm='l2')
    rng = np.random.default_rng(20261008)
    ps = rng.normal(size=(256, 12)) / np.sqrt(256)
    pk = rng.normal(size=(128, 12)) / np.sqrt(128)
    vectors, records = {}, []
    RDLogger.DisableLog('rdApp.error')
    for name, row in sorted(matched.items()):
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is None:
            continue
        bits = np.zeros(256)
        DataStructs.ConvertToNumpyArray(fpgen.GetFingerprint(mol), bits)
        text = row['moa'] + ' ' + ' '.join(relations[row['PubChem ID']])
        vectors[name] = np.r_[bits @ ps, hasher.transform([text]).toarray()[0] @ pk]
        records.append(dict(drug=name, pubchem=row['PubChem ID'], smiles=row['smiles'],
                            moa=row['moa'], directed_relations=relations[row['PubChem ID']]))
    embedding = np.array([vectors.get(name, np.zeros(24)) for name in names])
    mask = np.array([name in vectors for name in names])
    shuffled = dict(zip(sorted(vectors), rng.permutation(list(vectors.values()))))
    permuted = np.array([shuffled.get(name, np.zeros(24)) for name in names])
    write('QUALIFIED_KNOWLEDGE.json', dict(records=records, matched_rows=int(mask.sum()),
                                         menu_rows=len(labels), matching='Exact unique name; no salt guessing'))
    return embedding, permuted, mask


def fold_data(arrays, train, held):
    xs, ys, priors, m0s, masks = [], [], [], [], []
    for cell in train + [held]:
        # For training rows, also exclude held. No outer/inner held label enters a prior.
        exclusions = tuple(i for i in range(45) if i not in train and i != cell)
        x, _, mask, m0 = reference_row(arrays, cell, exclusions)
        keep = np.array([i in train and i != cell for i in range(45)])
        avail = arrays['state_available_B'] & keep[:, None]
        state_mean = (np.where(avail, arrays['state_B'], 0).sum(0) / avail.sum(0))
        prior = m0 + .5 * np.where(arrays['state_available_B'][cell],
                                   arrays['state_B'][cell] - state_mean, 0)
        xs.append(x); ys.append(arrays['train_B'][cell]); priors.append(prior)
        m0s.append(m0); masks.append(mask)
    return np.array(xs), np.array(ys), np.array(priors), np.array(m0s), np.array(masks)


def feature_rows(x, basal, embedding, matched, arm):
    ncell, ndrug = x.shape[:2]
    # Fixed random basal projection; no response or held-cell-fitted dimensionality reduction.
    proj = np.random.default_rng(23).normal(size=(2000, 8)) / np.sqrt(2000)
    b = basal @ proj
    design = x[:, :, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20]]
    # These are distance/dose/plate/source coverage; omit residual log magnitude and variance.
    source_missing = np.broadcast_to((~matched)[None, :, None], (ncell, ndrug, 1))
    if arm == 'missing':
        return np.concatenate([design, source_missing], axis=2)
    if arm == 'design':
        return design
    d = embedding[:, :12] if arm == 'structure' else embedding
    main = np.broadcast_to(d[None], (ncell, ndrug, d.shape[1]))
    interaction = (b[:, None, :, None] * d[None, :, None, :]).reshape(ncell, ndrug, -1)
    return np.concatenate([design, source_missing, main, interaction], axis=2)


def ridge_predict(x, residual, mask, xtest, alpha):
    if alpha == 0:
        return np.zeros(len(xtest))
    x, y = x.reshape(-1, x.shape[-1])[mask.ravel()], residual.ravel()[mask.ravel()]
    centre, scale = x.mean(0), np.maximum(x.std(0), 1e-8)
    x = (x - centre) / scale
    ym = y.mean()
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (y - ym))
    return (xtest - centre) / scale @ beta + ym


def predict(arrays, train, held, embedding, matched, arm, alpha):
    x, y, prior, m0, masks = fold_data(arrays, train, held)
    if arm == 'M0': return m0[-1], y[-1], masks[-1]
    if arm == 'M2': return prior[-1], y[-1], masks[-1]
    f = feature_rows(x, arrays['basal'][train + [held]], embedding, matched, arm)
    correction = ridge_predict(f[:-1], y[:-1] - prior[:-1], masks[:-1] & matched,
                               f[-1], alpha)
    return prior[-1] + np.where(matched, correction, 0), y[-1], masks[-1]


def choose(arrays, train, embedding, matched, arm):
    if arm in ('M0', 'M2'): return 0, {}
    losses = {}
    for alpha in (0, 1, 10, 100, 1000):
        loss = []
        # Fixed three inner representative cells, their complete labels excluded from training.
        for held in train[::max(1, len(train)//3)][:3]:
            remaining = [i for i in train if i != held]
            p, y, mask = predict(arrays, remaining, held, embedding, matched, arm, alpha)
            loss.append(float(np.mean((p[mask] - y[mask])**2)))
        losses[alpha] = float(np.mean(loss))
    return min(losses, key=lambda a: (losses[a], a)), losses


def metrics(mean, observed, mask):
    p, y = mean[mask], observed[mask]
    delta_y, delta_p = y[:, None] - y, p[:, None] - p
    pairs = np.triu(np.ones(delta_y.shape, bool), 1) & (np.abs(delta_y) > 1e-12)
    return dict(mse=float(np.mean((p-y)**2)),
                pair_accuracy=float(np.mean((delta_y[pairs]*delta_p[pairs]) > 0)),
                selected=top(mean).tolist(), top5_B=float(observed[top(mean)].sum()))


def kg_replay(mean, covariance, obsvar, offset, yA, yB):
    mean, covariance = mean.copy(), covariance.copy()
    initial = set(top(mean))
    normals = np.random.default_rng(20261008).standard_normal(64)
    purchased, history = [], []
    for step in range(8):
        gains = []
        current = mean[top(mean)].sum()
        for i in range(len(mean)):
            if i in purchased: continue
            sd = np.sqrt(covariance[i, i] + obsvar[i])
            draws = mean[None] + normals[:, None] * (covariance[:, i] / sd)[None]
            gain = np.partition(draws, len(mean)-5, axis=1)[:, -5:].sum(1).mean() - current
            gains.append((float(gain), -i))
        _, neg = max(gains); i = -neg
        # Purchase receipt precedes access to this A scalar. No B access until commitment.
        history.append(dict(step=step, purchased_A=i, cumulative_cost=step+1))
        value = yA[i] - offset[i]
        column = covariance[:, i].copy()
        mean += column / (covariance[i, i] + obsvar[i]) * (value-mean[i])
        covariance -= np.outer(column, column)/(covariance[i, i]+obsvar[i])
        purchased.append(i)
    selected = top(mean).tolist()
    history.append(dict(committed_B=selected, cumulative_cost=13))
    return dict(selected=selected, terminal_B=float(yB[selected].sum()), cost=13,
                swapped_in=sorted(set(selected)-initial), history=history)


def main():
    started = time.perf_counter()
    assert sha(HERE/'PROTOCOL.json') == json.loads((HERE/'FREEZE.json').read_text())['protocol_sha256']
    protocol = json.loads((HERE/'PROTOCOL.json').read_text())
    for path, identity in protocol['inputs'].items(): assert sha(ROOT/path) == identity
    labels = json.loads((PACKET/'PACKET_MANIFEST.json').read_text())['labels']
    arrays = dict(np.load(PACKET/'training_arrays.npz'))
    emb, perm, matched = representations(labels)
    arms = protocol['arms']; diagnostic, choices = [], {}
    # References were in STATE pretraining: these diagnostics cannot establish STATE transfer.
    for fold in range(3):
        test = [i for i in range(45) if i % 3 == fold]
        train = [i for i in range(45) if i not in test]
        for arm in arms:
            e = perm if arm == 'permuted_knowledge' else emb
            a, loss = choose(arrays, train, e, matched, arm)
            for held in test:
                p, y, mask = predict(arrays, train, held, e, matched, arm, a)
                diagnostic.append(dict(fold=fold, cell=held, arm=arm, alpha=a, **metrics(p,y,mask)))
    prior = dict(np.load(PACKET/'public_prior.npz'))
    target_predictions = {}
    for arm in arms:
        e = perm if arm == 'permuted_knowledge' else emb
        alpha, losses = choose(arrays, list(range(45)), e, matched, arm)
        choices[arm] = dict(alpha=alpha, inner_losses=losses)
        xs, ys, ps, _, masks = fold_data(arrays, list(range(45)), 0)
        # Only first45 reference rows form the training set; appended duplicate is unused.
        for cell, file in json.loads((PACKET/'PACKET_MANIFEST.json').read_text())['contexts'].items():
            key = cell.replace('-', '_').replace('/', '_')
            base = prior[key+'__M0'] if arm == 'M0' else prior[key+'__M2']
            p = base.copy()
            if arm not in ('M0', 'M2'):
                obs = np.load(ROOT/'data/external/tahoe_zeroshot_20261007/observations'/f'{file}.npz')
                basal = np.average(obs['basal_mean'], axis=0, weights=obs['basal_n'])
                allx = np.concatenate([xs[:45], prior[key+'__features'][None]])
                allb = np.concatenate([arrays['basal'], basal[None]])
                f = feature_rows(allx, allb, e, matched, arm)
                correction = ridge_predict(f[:-1], ys[:45]-ps[:45], masks[:45]&matched, f[-1], alpha)
                p += np.where(matched, correction, 0)
            target_predictions[key+'__'+arm] = p
    np.savez_compressed(HERE/'PREDICTIONS.npz', **target_predictions)
    write('MODEL_CHOICES.json', choices)
    # New predictions and model choices are saved before any target evaluator access.
    evaluator = dict(np.load(PACKET/'evaluator_private.npz'))
    results = []
    for name, p in target_predictions.items():
        key, arm = name.split('__')
        results.append(dict(context=key, arm=arm, **metrics(p, evaluator[key+'__B'], np.ones(146,bool)),
                            kg=kg_replay(p, prior['cov'], prior['obsvar'], prior['offset'],
                                         evaluator[key+'__A'], evaluator[key+'__B'])))
    write('REFERENCE_DIAGNOSTIC.json', diagnostic)
    write('RESULTS.json', results)
    summary = {}
    for arm in arms:
        rows = [r for r in results if r['arm']==arm]
        summary[arm] = dict(alpha=choices[arm]['alpha'], mean_mse=float(np.mean([r['mse'] for r in rows])),
                            mean_pair_accuracy=float(np.mean([r['pair_accuracy'] for r in rows])),
                            mean_top5_B=float(np.mean([r['top5_B'] for r in rows])),
                            mean_KG_B=float(np.mean([r['kg']['terminal_B'] for r in rows])),
                            total_KG_cost=sum(r['kg']['cost'] for r in rows))
    write('SUMMARY.json', dict(arms=summary, seconds=time.perf_counter()-started,
                              source_sha256=sha(Path(__file__)), status=protocol['status']))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    with threadpool_limits(limits=1): main()
