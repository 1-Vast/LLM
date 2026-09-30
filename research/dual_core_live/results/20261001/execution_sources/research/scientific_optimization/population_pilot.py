"""Real single-cell, held-out-chemical development pilot; see POPULATION_PROTOCOL.md."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import h5py
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from virtual_cell.artifacts import shift_labels
from virtual_cell.learned_response import PopulationPair, fit_population_flow, population_mmd


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 22), b''):
            result.update(block)
    return result.hexdigest()


def column(group, name):
    x = group[name]
    if isinstance(x, h5py.Group):
        codes = x['codes'][:]
        return np.where(codes >= 0, x['categories'].asstr()[:][np.maximum(codes, 0)], None)
    return x.asstr()[:] if x.dtype.kind in 'OS' else x[:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    source = ROOT / 'data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad'
    prepared = ROOT / 'outputs/biological_depth_20260926/prepared'
    compounds = pd.read_csv(prepared / 'compounds.csv').set_index('compound')
    genes = pd.read_csv(prepared / 'genes.csv')
    manifest = json.loads((prepared / 'prepare_manifest.json').read_text())
    offset = manifest['audit']['feature_label_check']['chosen_offset']
    rng = np.random.default_rng(20260927)
    with h5py.File(source) as f:
        meta = pd.DataFrame({k: column(f['obs'], k) for k in
                            ('cell_line', 'perturbation', 'dose_value', 'time', 'replicate', 'plate')})
        active = meta[(meta.cell_line == 'A549') & (meta.time == 24)]
        controls = {key: rows.index.to_numpy() for key, rows in
                    active[(active.perturbation == 'control') & (active.dose_value == 0)].groupby(['replicate', 'plate'])}
        candidates = {}
        for (drug, rep, plate), rows in active[active.dose_value == 1000].groupby(['perturbation', 'replicate', 'plate']):
            if drug in compounds.index and len(rows) >= 64 and len(controls.get((rep, plate), [])) >= 64:
                candidates.setdefault(drug, []).append((rep, plate, rows.index.to_numpy()))
        by_group = {}
        for drug in sorted(candidates):
            by_group.setdefault(str(compounds.loc[drug, 'skeleton']), drug)
        groups = sorted(by_group, key=lambda g: hashlib.sha256(('population-pilot|' + g).encode()).hexdigest())[:24]
        if len(groups) != 24:
            raise ValueError('insufficient_eligible_groups')
        records = []
        for i, group in enumerate(groups):
            drug = by_group[group]
            for rep, plate, rows in sorted(candidates[drug], key=lambda x: x[:2])[:2]:
                records.append({'compound': drug, 'group': group, 'replicate': rep, 'plate': plate,
                                'split': 'train' if i < 16 else 'validation' if i < 20 else 'test',
                                'control_rows': rng.choice(controls[rep, plate], 64, replace=False).tolist(),
                                'treated_rows': rng.choice(rows, 64, replace=False).tolist()})
        selected = sorted({r for item in records for key in ('control_rows', 'treated_rows') for r in item[key]})
        labels = np.array([s or '' for s in shift_labels(column(f['var'], 'ensembl_id'), offset, f['X'].attrs['shape'][1])])
        unique = ~pd.Series(labels).duplicated(keep=False).to_numpy()
        human = np.char.startswith(labels, 'ENSG') & unique
        index = {g: i for i, g in enumerate(labels) if human[i]}
        columns = np.array([index[g] for g in genes.ensembl])
        positions = np.full(len(labels), -1)
        positions[columns] = np.arange(len(columns))
        matrix = f['X']
        indptr = matrix['indptr'][:]
        expression = np.zeros((len(selected), len(columns)), dtype=np.float32)
        for j, row in enumerate(selected):
            start, stop = int(indptr[row]), int(indptr[row + 1])
            indices, counts = matrix['indices'][start:stop], matrix['data'][start:stop].astype(float)
            library = counts[human[indices]].sum()
            keep = positions[indices] >= 0
            expression[j, positions[indices[keep]]] = np.log1p(counts[keep] * 10000 / max(library, 1.))
    print(f'extracted {len(selected)} unique real cells, {len(records)} condition populations', flush=True)
    lookup = {r: i for i, r in enumerate(selected)}
    train_controls = sorted({lookup[r] for item in records if item['split'] == 'train' for r in item['control_rows']})
    chosen = np.argsort(-expression[train_controls].var(axis=0), kind='stable')[:128]
    pca = PCA(n_components=16, svd_solver='full').fit(expression[train_controls][:, chosen])
    latent = pca.transform(expression[:, chosen]).astype(np.float32)
    distances = pdist(latent[train_controls])
    bandwidth = float(np.median(distances[distances > 0]))
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=128)
    gate = float(np.log1p(1000.) / np.log1p(10000.))
    pairs, fps = [], []
    for item in records:
        fp = generator.GetFingerprintAsNumPy(Chem.MolFromSmiles(compounds.loc[item['compound'], 'smiles']))
        fps.append(fp.astype(float))
        pairs.append(PopulationPair(latent[[lookup[r] for r in item['control_rows']]],
                                    latent[[lookup[r] for r in item['treated_rows']]],
                                    np.r_[fp, gate].astype(np.float32), gate, item['group']))
    train = [i for i, r in enumerate(records) if r['split'] == 'train']
    val = [i for i, r in enumerate(records) if r['split'] == 'validation']
    test = [i for i, r in enumerate(records) if r['split'] == 'test']
    model, history = fit_population_flow([pairs[i] for i in train], [pairs[i] for i in val], bandwidth=bandwidth)
    shifts = np.stack([pairs[i].treated.mean(0) - pairs[i].control.mean(0) for i in train])
    results, arrays = [], {}
    for i in test:
        p = pairs[i]
        similarity = np.array([np.minimum(fps[i], fps[j]).sum() / max(np.maximum(fps[i], fps[j]).sum(), 1.) for j in train])
        predictions = {'vehicle': p.control, 'mean_shift': p.control + shifts.mean(0),
                       'chemical_nn': p.control + shifts[np.isclose(similarity, similarity.max())].mean(0),
                       'population_flow': model.predict_population(p.control, p.condition, p.dose_gate)}
        arrays[f'observed_{i}'] = p.treated
        for name, y in predictions.items():
            arrays[f'{name}_{i}'] = y
            results.append({'condition': i, 'group': p.group, 'model': name,
                            'mmd': population_mmd(y, p.treated, bandwidth),
                            'mean_mse': float(np.square(y.mean(0) - p.treated.mean(0)).mean()),
                            'variance_mse': float(np.square(y.var(0) - p.treated.var(0)).mean())})
    metrics = pd.DataFrame(results).groupby(['model', 'group'])[['mmd', 'mean_mse', 'variance_mse']].mean().groupby('model').mean().to_dict('index')
    gate_pass = all(metrics['population_flow']['mmd'] < metrics[name]['mmd'] for name in metrics if name != 'population_flow')
    summary = {'status': 'development_unregistered', 'gate': 'PASS' if gate_pass else 'FAIL',
               'test_groups': len({pairs[i].group for i in test}), 'test_populations': len(test),
               'bandwidth': bandwidth, 'selected_epoch': min(history, key=lambda r:r['validation_mmd'])['epoch'],
               'metrics': metrics, 'decision_gain': 'NOT_EVALUATED', 'default_promoted': False,
               'hashes': {str(p.relative_to(ROOT)): digest(p) for p in
                          (source, prepared / 'genes.csv', prepared / 'compounds.csv', prepared / 'prepare_manifest.json',
                           Path(__file__), Path(__file__).with_name('POPULATION_PROTOCOL.md'),
                           ROOT / 'src/virtual_cell/learned_response.py')}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (out / 'populations.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    (out / 'history.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
    pd.DataFrame(results).to_csv(out / 'condition_metrics.csv', index=False)
    np.savez_compressed(out / 'predictions.npz', **arrays)
    np.savez_compressed(out / 'coordinates.npz', genes=genes.ensembl.to_numpy(dtype=str)[chosen],
                        mean=pca.mean_, components=pca.components_, rows=np.array(selected), latent=latent)
    torch.save(model.state_dict(), out / 'population_flow.pt')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
