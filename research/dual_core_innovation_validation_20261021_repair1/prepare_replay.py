"""Train a seeded model and prepare parent-only exposed-replay episodes."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
OLD = HERE.with_name('dual_core_innovation_validation_20261021')
sys.path.insert(0, str(OLD))
sys.path.insert(0, str(HERE))
import ptv_tasks as T
import ptv_models as M
from repair_model import build_model


def save_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'prepared.pt').exists():
        raise RuntimeError('Prepared output already exists; use a fresh run directory')
    torch.set_num_threads(4)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    start = time.perf_counter()
    prep = T.Prep()
    ex = prep.R.experiments()
    train = ex[ex.part == 'dev'].copy()
    items, retained = prep.items(train)
    tens = M.make_tensors(items)
    model = build_model(len(prep.R.nodes), len(next(iter(prep.fp.values()))),
                        seed=0, hidden=16, device=device)
    losses = []
    M.train(model, tens, epochs=30, seed=0,
            log=lambda ep, loss: losses.append({'epoch': ep + 1, 'loss': loss}))
    if device == 'cuda':
        torch.cuda.synchronize()
    train_seconds = time.perf_counter() - start
    torch.save(model.state_dict(), out / 'model.pt')
    train_single = retained[(retained.ndrug == 1) & retained.y.notna()]
    episodes = {'sel': [], 'final_regression': []}
    rates = train_single.groupby('perts').y.mean()
    for stage, part in [('sel', 'sel'), ('final_regression', 'final')]:
        rows = ex[(ex.part == part) & (ex.ndrug == 1) & ex.y.notna()]
        for cell in sorted(rows.cell.unique()):
            frame = rows[rows.cell == cell].copy()
            pool = T.contested_pool(train_single, sorted(frame.perts.tolist()))
            data, keep = prep.items(frame[frame.perts.isin(pool)])
            drugs = keep.perts.tolist()
            if len(drugs) < 5:
                raise ValueError('Replay pool has fewer than five drugs')
            inputs = {key: torch.tensor(np.stack([it[key] for it in data]), dtype=torch.float32).unsqueeze(-1)
                      for key in ('x', 'pert', 'fpA', 'fpB')}
            prior, b1 = {}, {}
            for drug in drugs:
                ref = train_single[train_single.perts == drug]
                correlations = [np.corrcoef(prep.baseline(cell), prep.baseline(c))[0, 1] for c in ref.cell]
                weights = np.exp(np.asarray(correlations) / .15)
                prior[drug] = float(rates[drug])
                b1[drug] = float(weights @ ref.y.to_numpy() / weights.sum())
            features = np.stack([prep.fp[d] for d in drugs])
            norm = np.linalg.norm(features, axis=1)
            similarity = features @ features.T / np.maximum(norm[:, None] * norm[None, :], 1e-12)
            sim = {d: {other: float(similarity[i, j]) for j, other in enumerate(drugs)}
                   for i, d in enumerate(drugs)}
            molecular = {}
            for drug, item in zip(drugs, data):
                y = np.zeros_like(item['y']); mask = np.zeros_like(item['yobs'])
                y[1] = item['y'][1]; mask[1] = item['yobs'][1]
                molecular[drug] = {'y': y.tolist(), 'mask': mask.tolist()}
            labels = {d: int(y) for d, y in zip(drugs, keep.y)}
            if any(float(y) not in (0., 1.) for y in keep.y):
                raise ValueError('Single-drug labels must be binary')
            with torch.no_grad():
                model.eval()
                _, pred = model(*[inputs[k].to(device) for k in ('x', 'pert', 'fpA', 'fpB')])
            W = dict(zip(drugs, pred.cpu().numpy().astype(float).tolist()))
            episode = {'drugs': drugs, 'W': W, 'prior': prior, 'nn': b1, 'sim': sim,
                       'labels': labels, 'mol': molecular, 'lam': .5, 'budget': 5.}
            episodes[stage].append({'cell': cell, 'lineage': str(keep.lineage.iloc[0]),
                                    'episode': episode, 'inputs': inputs, 'features': features})
    torch.save(episodes, out / 'prepared.pt')
    metadata = {'exposure': 'Previously exposed public replay; no independent confirmation',
                'seed': 0, 'epochs': 30, 'hidden': 16, 'device': device,
                'n_train': len(items), 'train_lineages': sorted(retained.lineage.unique().tolist()),
                'train_seconds_including_preparation': train_seconds, 'losses': losses,
                'episodes': {k: [{'cell': e['cell'], 'lineage': e['lineage'], 'n_drugs': len(e['episode']['drugs'])}
                                for e in value] for k, value in episodes.items()}}
    save_json(out / 'preparation.json', metadata)
    print(json.dumps({k: v for k, v in metadata.items() if k not in ('losses', 'episodes')}), flush=True)


if __name__ == '__main__':
    prepare(HERE / 'RUN')
