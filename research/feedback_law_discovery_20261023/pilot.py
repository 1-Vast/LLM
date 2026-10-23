"""Frozen exposed-source functional screen; no expression or protected outcomes."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery/pilot'
CACHE = ROOT/'tmp/context_transfer_20261017/beataml_domain.npz'
STEPS, BATCH, SUPPORT, WIDTH = 120, 16, 8, 16


def hashed(value):
    return int(hashlib.sha256(value.encode()).hexdigest(), 16)


class Updater(nn.Module):
    def __init__(self, drugs):
        super().__init__()
        self.embedding = nn.Parameter(torch.randn(drugs, WIDTH)/WIDTH**.5)
        self.step = nn.Parameter(torch.full((WIDTH,), float(np.log(np.expm1(.1)))))

    def forecast(self, h):
        return torch.tanh(h) @ self.embedding.T

    def update(self, h, indices, values, training):
        predictions = self.forecast(h).gather(1, indices)
        loss = ((predictions-values)**2).sum()/(2*SUPPORT)
        grad = torch.autograd.grad(loss, h, create_graph=training)[0]
        return h-F.softplus(self.step)*grad

    def view(self, indices, values, mode, training):
        h = torch.zeros((len(indices), WIDTH), requires_grad=True)
        packages = [list(range(8))] if mode == 'union' else (
            [list(range(4)), list(range(4, 8))] if mode == 'AB' else
            [list(range(4, 8)), list(range(4))])
        for package in packages:
            h = self.update(h, indices[:, package], values[:, package], training)
        return self.forecast(h)


class SetPredictor(nn.Module):
    def __init__(self, drugs):
        super().__init__()
        self.embedding = nn.Embedding(drugs, WIDTH)
        self.encode = nn.Sequential(nn.Linear(WIDTH+1, 32), nn.ReLU(), nn.Linear(32, 32))
        self.decode = nn.Sequential(nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, drugs))

    def forward(self, indices, values):
        records = torch.cat([self.embedding(indices), values[..., None]], dim=-1)
        return self.decode(self.encode(records).sum(dim=1)/SUPPORT)


def masked_mean(values, mask):
    return ((values*mask).sum(dim=1)/mask.sum(dim=1)).mean()


def episode(rng, available, train_rows):
    rows = rng.choice(train_rows, BATCH, replace=True)
    support = np.stack([rng.choice(available[r], SUPPORT, replace=False) for r in rows])
    return rows, support


def train_model(kind, seed, z, available, train_rows):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = SetPredictor(z.shape[1]) if kind == 'set' else Updater(z.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=.01)
    data = torch.tensor(np.where(np.isfinite(z), z, 0), dtype=torch.float32)
    present = torch.tensor(np.isfinite(z), dtype=torch.float32)
    history = []
    started = time.perf_counter()
    for step in range(STEPS):
        rows, indices = episode(rng, available, train_rows)
        indices = torch.tensor(indices)
        target = data[rows]
        values = target.gather(1, indices)
        mask = present[rows].clone()
        mask.scatter_(1, indices, 0)
        if kind == 'set':
            views = [model(indices, values) for _ in range(3)]
        else:
            modes = ['AB', 'AB' if kind == 'fixed' else 'BA', 'union']
            views = [model.view(indices, values, m, True) for m in modes]
        query = sum(masked_mean((p-target)**2, mask) for p in views)/3
        penalty = masked_mean((views[0]-views[1])**2, mask)+masked_mean((views[0]-views[2])**2, mask)
        loss = query+penalty if kind == 'consistent' else query
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if not torch.isfinite(loss):
            raise RuntimeError(f'Nonfinite training loss {kind}/{seed}/{step}')
        history.append([float(query.detach()), float(penalty.detach())])
    elapsed = time.perf_counter()-started
    return model, dict(kind=kind, seed=seed, train_seconds=elapsed,
                       parameters=sum(p.numel() for p in model.parameters()),
                       outer_steps=STEPS, context_episodes=STEPS*BATCH,
                       query_view_evaluations=STEPS*BATCH*3,
                       fast_package_gradient_evaluations=0 if kind == 'set' else STEPS*BATCH*5,
                       history=history)


def metrics(prediction, truth, mask, groups):
    mse, regret = [], []
    for p, y, m in zip(prediction, truth, mask):
        p, y = p[m], y[m]
        mse.append(float(np.mean((p-y)**2)))
        chosen = np.argsort(p, kind='stable')[:3]
        optimal = np.argsort(y, kind='stable')[:3]
        regret.append(float(y[chosen].mean()-y[optimal].mean()))
    mse, regret = np.array(mse), np.array(regret)
    labels = sorted(set(groups))
    cluster_mse = [float(mse[groups == g].mean()) for g in labels]
    cluster_regret = [float(regret[groups == g].mean()) for g in labels]
    return dict(mse=float(np.mean(cluster_mse)), regret=float(np.mean(cluster_regret)),
                context_mse=mse.tolist(), context_regret=regret.tolist(),
                groups=labels, cluster_mse=cluster_mse, cluster_regret=cluster_regret)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'INITIATED.json').exists(), 'Inspect a previous run rather than repeat'
    (OUT/'INITIATED.json').write_text(json.dumps(dict(status='INITIATED', cache_sha256=hashlib.sha256(CACHE.read_bytes()).hexdigest())), encoding='utf-8')
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    with np.load(CACHE, allow_pickle=False) as source:
        y = source['Y'].astype(float)
        groups, contexts, items = (source[key].astype(str) for key in ('groups', 'contexts', 'items'))
    folds = np.array([hashed('context-transfer-subject:'+g) % 5 for g in groups])
    source_rows = np.flatnonzero(folds != 0)
    drugs = np.flatnonzero(np.isfinite(y[source_rows]).sum(axis=0) >= 100)
    y, items = y[:, drugs], items[drugs]
    available = [np.flatnonzero(np.isfinite(row)) for row in y]
    eligible = np.array([len(a) >= 16 for a in available])
    train_rows, query_rows = np.flatnonzero((folds != 0) & eligible), np.flatnonzero((folds == 0) & eligible)
    assert len(train_rows) > 30 and len(query_rows) > 10 and len(drugs) > 8
    means = np.nanmean(y[source_rows], axis=0)
    scales = np.maximum(np.nanstd(y[source_rows], axis=0), 1e-6)
    z = (y-means)/scales
    indices = np.stack([sorted(available[r], key=lambda j: hashed('consistency-pilot-support:'+contexts[r]+':'+items[j]))[:8]
                        for r in query_rows])
    values = np.take_along_axis(z[query_rows], indices, axis=1)
    mask = np.isfinite(y[query_rows])
    np.put_along_axis(mask, indices, False, axis=1)
    manifest = dict(cache_sha256=hashlib.sha256(CACHE.read_bytes()).hexdigest(), drugs=items.tolist(),
                    train_contexts=contexts[train_rows].tolist(), query_contexts=contexts[query_rows].tolist(),
                    query_groups=groups[query_rows].tolist(), support_indices=indices.tolist(),
                    source_means=means.tolist(), source_scales=scales.tolist(),
                    python_scope='Y/groups/contexts/items only; no X/events/G', exposure='Previously exposed exploratory development')
    (OUT/'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    records, arrays = [], dict(truth=y[query_rows], query_mask=mask, support_indices=indices)
    mean_prediction = np.broadcast_to(means, y[query_rows].shape).copy()
    records.append(dict(kind='mean', seed=None, parameters=len(drugs), train_seconds=0.,
                        metrics=metrics(mean_prediction, y[query_rows], mask, groups[query_rows])))
    arrays['mean'] = mean_prediction
    started = time.perf_counter()
    centered = np.where(np.isfinite(z[source_rows]), z[source_rows], 0)
    covariance = centered.T @ centered/len(source_rows)
    covariance_prediction = []
    for support, observed in zip(indices, values):
        coefficient = np.linalg.solve(covariance[np.ix_(support, support)]+np.eye(8), observed)
        covariance_prediction.append(covariance[:, support] @ coefficient)
    prediction = np.array(covariance_prediction)*scales+means
    records.append(dict(kind='covariance', seed=None, parameters=int(covariance.size),
                        train_seconds=time.perf_counter()-started,
                        metrics=metrics(prediction, y[query_rows], mask, groups[query_rows])))
    arrays['covariance'] = prediction
    for seed in (0, 1, 2):
        for kind in ('fixed', 'augmented', 'consistent', 'set'):
            model, record = train_model(kind, seed, z, available, train_rows)
            model.eval()
            idx = torch.tensor(indices)
            val = torch.tensor(values, dtype=torch.float32)
            started = time.perf_counter()
            if kind == 'set':
                with torch.no_grad():
                    p = model(idx, val).numpy()
                views = [p, p.copy(), p.copy()]
            else:
                views = [model.view(idx, val, mode, False).detach().numpy() for mode in ('AB', 'BA', 'union')]
            prediction = views[0]*scales+means
            record.update(evaluation_seconds=time.perf_counter()-started,
                          metrics=metrics(prediction, y[query_rows], mask, groups[query_rows]),
                          order_sensitivity=float(np.mean((views[0]-views[1])[mask]**2)),
                          partition_sensitivity=float(np.mean((views[0]-views[2])[mask]**2)))
            records.append(record)
            arrays[f'{kind}_{seed}'] = prediction
            arrays[f'{kind}_{seed}_BA'] = views[1]*scales+means
            arrays[f'{kind}_{seed}_union'] = views[2]*scales+means
            torch.save(model.state_dict(), OUT/f'{kind}_{seed}.pt')
            (OUT/f'{kind}_{seed}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
            print(json.dumps(dict(kind=kind, seed=seed, mse=record['metrics']['mse'], regret=record['metrics']['regret'], seconds=record['train_seconds'])), flush=True)
    np.savez_compressed(OUT/'PREDICTIONS.npz', **arrays)
    (OUT/'RESULT.json').write_text(json.dumps(dict(status='COMPLETED', train_contexts=len(train_rows),
        query_contexts=len(query_rows), query_patients=len(set(groups[query_rows])), drugs=len(drugs), records=records), indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
