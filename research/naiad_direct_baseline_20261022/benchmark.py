"""Frozen NAIAD author-model adapter, source-only checkpoint selection."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import time
import numpy as np
import pandas as pd
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import torch
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/naiad_direct_baseline'
INP = ROOT / 'log/20261022/norman_numeric_qualification'
spec = importlib.util.spec_from_file_location('naiad_models', Path(__file__).resolve().parent / 'vendor/naiad_models.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
THRESHOLDS = {0: 2, 2: 2, 4: 4, 10: 16, 20: 16, 30: 32, 40: 64, 60: 64, 80: 128, 100: 128}


def dimension(budget, genes):
    return THRESHOLDS[max(k for k in THRESHOLDS if k < budget / genes)]


def predict(model, ids, scalar):
    model.eval()
    with torch.no_grad():
        return .5 * (model(ids, scalar) + model(ids, scalar.flip(1)))


def train(ids, scalar, y, train_index, validation, n, budget, seed, model_type, epochs, device):
    started = time.perf_counter()
    torch.manual_seed(seed)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(seed)
    model = author.EmbedPhenoModel(n, d_embed=dimension(budget, n), d_pheno_hid=256,
                                   p_dropout=.1, model_type=model_type, embed_model='mlp').to(device)
    parameters = list(model.pheno_ffn.parameters())
    if model_type == 'both':
        parameters += list(model.embedding.parameters()) + list(model.embedding_ffn.parameters()) + list(model.embedding_comb.parameters())
    optimizer = torch.optim.Adam(parameters, lr=.01, weight_decay=0)
    dataset = TensorDataset(ids[train_index], scalar[train_index], y[train_index])
    loader = DataLoader(dataset, batch_size=1024, shuffle=False)
    steps = epochs * len(loader)
    warmup = int(steps / 10)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: (step + 1) / warmup
        if step < warmup else .1 + .9 * ((steps - step) / (steps - warmup)))
    best_epoch, best_mse = 0, float('inf')
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        for batch_ids, batch_scalar, batch_y in loader:
            optimizer.zero_grad()
            loss = torch.square(model(batch_ids, batch_scalar) - batch_y).sum()
            loss.backward()
            optimizer.step()
            scheduler.step()
        if validation is not None:
            pred = predict(model, ids[validation], scalar[validation])
            mse = torch.square(pred - y[validation]).mean().item()
            assert np.isfinite(mse)
            history.append(mse)
            if mse < best_mse:
                best_mse, best_epoch = mse, epoch
    if device.type == 'cuda':
        torch.cuda.synchronize()
    metadata = {'budget': budget, 'seed': seed, 'model_type': model_type,
                'train_count': len(train_index), 'epochs': epochs, 'optimizer_steps': steps,
                'embedding_dimension': dimension(budget, n), 'pheno_hidden': 256,
                'parameter_count_total': sum(p.numel() for p in model.parameters()),
                'parameter_count_optimized': sum(p.numel() for p in parameters),
                'seconds': time.perf_counter() - started, 'best_epoch': best_epoch,
                'best_inner_validation_mse': best_mse if validation is not None else None}
    return model, metadata, history


def main():
    start = time.perf_counter()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    pairs = pd.read_csv(INP / 'FUNCTION_SOURCE_DEVELOPMENT.csv')
    assert set(pairs['split']) == {'source', 'development'}
    assert pairs.pair.is_unique and pairs.gene_a.lt(pairs.gene_b).all()
    assert (pairs.pair == pairs.gene_a + '|' + pairs.gene_b).all()
    assert pairs.source_order.notna().all() and pairs.source_order.is_unique
    assert pairs['split'].value_counts().to_dict() == {'source': 3160, 'development': 1051}
    genes = sorted(set(pairs.gene_a) | set(pairs.gene_b))
    assert len(genes) == 103
    assert set(genes) == set(np.load(INP / 'SINGLE_RNA_FEATURES.npz')['genes'].tolist())
    lookup = {g: i for i, g in enumerate(genes)}
    priors = pd.read_csv(INP / 'SINGLE_GROWTH_PRIORS.csv').set_index('gene').average_fitness
    assert priors.index.is_unique and set(priors.index) == set(genes)
    ids = torch.tensor(np.column_stack([pairs.gene_a.map(lookup), pairs.gene_b.map(lookup)]), dtype=torch.long, device=device)
    scalar = torch.tensor(np.column_stack([pairs.gene_a.map(priors), pairs.gene_b.map(priors)]), dtype=torch.float32, device=device)
    assert torch.isfinite(scalar).all()
    # Reproduce author's fixed once-per-dataset scalar permutation without changing IDs.
    shuffle_generator = torch.Generator().manual_seed(0)
    order = torch.argsort(torch.rand(scalar.shape, generator=shuffle_generator), dim=-1).to(device)
    scalar = scalar.gather(1, order)
    truth = pairs.growth.to_numpy()
    assert np.isfinite(truth).all()
    y = torch.tensor(truth, dtype=torch.float32, device=device)
    source = sorted(pairs.index[pairs.split.eq('source')], key=lambda i: pairs.loc[i, 'source_order'])
    development = pairs.index[pairs.split.eq('development')].to_numpy()
    assert len(source) >= 2048 and not set(source) & set(development)
    prior_predictions = json.loads((ROOT / 'log/20261022/norman_baseline_calibration/DEVELOPMENT_PREDICTIONS.json').read_text())
    assert pairs.loc[development, 'pair'].tolist() == prior_predictions['pairs']
    results, costs, histories = [], [], []
    for budget in [128, 512, 2048]:
        selected = np.array(source[:budget])
        boundary = 3 * budget // 4
        inner_train, inner_validation = selected[:boundary], selected[boundary:]
        for model_type in ['pheno', 'both']:
            for seed in [0, 1, 2]:
                _, selection, history = train(ids, scalar, y, inner_train, inner_validation,
                    len(genes), budget, seed, model_type, 500, device)
                assert selection['best_epoch'] >= 1
                costs.append({'stage': 'inner', **selection})
                histories.append({'budget': budget, 'model_type': model_type, 'seed': seed, 'mse': history})
                model, fitted, _ = train(ids, scalar, y, selected, None,
                    len(genes), budget, seed, model_type, selection['best_epoch'], device)
                costs.append({'stage': 'final', **fitted})
                pred = predict(model, ids[development], scalar[development]).cpu().numpy().astype(float)
                assert np.isfinite(pred).all()
                row = {'budget': budget, 'model_type': model_type, 'seed': seed,
                       'embedding_dimension': fitted['embedding_dimension'], 'selected_epoch': selection['best_epoch'],
                       'inner_validation_mse': selection['best_inner_validation_mse'],
                       'development_mse': float(np.mean((pred - truth[development]) ** 2))}
                results.append({**row, 'prediction': pred.tolist()})
                print(json.dumps(row), flush=True)
                pd.DataFrame([{k: v for k, v in r.items() if k != 'prediction'} for r in results]).to_csv(OUT / 'SCORES.csv', index=False)
    (OUT / 'PREDICTIONS.json').write_text(json.dumps({'pairs': pairs.loc[development, 'pair'].tolist(),
        'truth': truth[development].tolist(), 'records': results}))
    (OUT / 'COSTS.json').write_text(json.dumps(costs, indent=2))
    (OUT / 'INNER_HISTORIES.json').write_text(json.dumps(histories))
    summary = {'status': 'EXECUTED_EXPLORATORY', 'utc': datetime.now(timezone.utc).isoformat(),
               'wall_seconds': time.perf_counter() - start, 'device': str(device), 'torch': torch.__version__,
               'cublas_workspace_config': os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
               'gene_count': len(genes), 'fit_count': len(costs), 'final_models': len(results),
               'protected_values_loaded': 0, 'fresh_biological_experiments': 0,
               'cuda_device_name': torch.cuda.get_device_name(0) if device.type == 'cuda' else None}
    (OUT / 'RESULT.json').write_text(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
