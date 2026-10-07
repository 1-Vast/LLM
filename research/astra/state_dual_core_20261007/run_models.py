"""Matched, frozen-feature native RNA study. Never updates STATE weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import psutil
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def linear_kernel(x, train):
    """Training-only mean/total-variance; no per-gene test scaling."""
    x = np.asarray(x, dtype=float)
    centered = x - x[train].mean(axis=0)
    scale = max(float(np.mean(np.sum(centered[train] ** 2, axis=1))), 1e-12)
    return centered @ centered.T / scale


def predict(kernel, train, target, alpha):
    center = target[train].mean(axis=0)
    weights = np.linalg.solve(kernel[np.ix_(train, train)] + alpha * np.eye(len(train)), target[train] - center)
    return kernel[:, train] @ weights + center


def group_loss(frame, y, p, indices):
    errors = np.mean((y[indices] - p[indices]) ** 2, axis=1)
    return pd.DataFrame({'group': frame.iloc[indices].chemical_group.to_numpy(), 'error': errors}).groupby('group').error.mean()


def build_kernels(frame, features, train):
    source = pd.read_parquet(ROOT / 'tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_drugs.raw')
    lookup = {str(r.drug).strip().casefold(): r for r in source.itertuples()}
    rows = [lookup[d.strip().casefold()] for d in frame.drug]
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)
    fps = [generator.GetFingerprint(Chem.MolFromSmiles(r.canonical_smiles)) for r in rows]
    chemical = np.array([DataStructs.BulkTanimotoSimilarity(f, fps) for f in fps])
    targets = [set(str(r.targets).split(',')) if isinstance(r.targets, str) else set() for r in rows]
    target = np.array([[len(a & b) / max(np.sqrt(len(a)*len(b)), 1) for b in targets] for a in targets])
    dose = (frame.dose_uM.to_numpy()[:, None] == frame.dose_uM.to_numpy()[None, :]).astype(float)
    basal = linear_kernel(features['basal_mean'], train)
    state = linear_kernel(features['state_delta'], train)
    # One whole-drug mapping across doses, restricted to same split and dose/plate pattern.
    drug_rows = {d: part.sort_values('dose_uM').index.to_numpy() for d, part in frame.groupby('drug')}
    strata = {}
    for d, indices in drug_rows.items():
        key = (frame.loc[indices[0], 'split'], tuple(zip(frame.loc[indices, 'dose_uM'], frame.loc[indices, 'plate'])))
        strata.setdefault(key, []).append(d)
    perm = np.arange(len(frame))
    permuted_drugs = []
    for key, names in sorted(strata.items()):
        names = sorted(names)
        shifted = names[1:] + names[:1]  # deterministic nonidentity within each non-singleton stratum
        for first, second in zip(names, shifted):
            perm[drug_rows[first]] = drug_rows[second]
            permuted_drugs.append({'drug': first, 'mapped_drug': second, 'changed': first != second})
    missing = np.array([[not bool(t)] for t in targets], dtype=float)
    kernels = {
        'M1': (chemical + target + dose + basal) / 4,
        'M2': (chemical + target + dose + basal + state) / 5,
        'metadata_only': (chemical + target + dose) / 3,
        'basal_only': (basal + dose) / 2,
        'missingness_only': (linear_kernel(missing, train) + dose) / 2,
        'permuted_STATE': (chemical + target + dose + basal + linear_kernel(features['state_delta'][perm], train)) / 5,
    }
    return kernels, perm, permuted_drugs


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    proc = psutil.Process()
    cpu = proc.cpu_times()
    protocol = json.loads((HERE/'PROTOCOL.json').read_text())
    assert sha(HERE/'PROTOCOL.json') == json.loads((HERE/'PROTOCOL_FREEZE.json').read_text())['sha256']
    for name, expected in protocol['frozen_inputs'].items():
        assert sha(HERE/name) == expected, name
    frame = pd.read_csv(HERE/'world/conditions.csv')
    f = np.load(HERE/'world/state_features.npz')
    z = np.load(HERE/'world/sealed_outcomes.npz')
    assert np.array_equal(frame.condition_id, f['condition_id']) and np.array_equal(f['condition_id'], z['condition_id'])
    assert frame.groupby('chemical_group').split.nunique().max() == 1
    train = np.flatnonzero(frame.split == 'train')
    dev = np.flatnonzero(frame.split == 'development')
    cal = np.flatnonzero(frame.split == 'calibration')
    ev = np.flatnonzero(frame.split == 'evaluation')
    y = z['observed_delta'].astype(float)
    magnitude = z['magnitude'].astype(float)
    assert np.isfinite(y).all() and np.isfinite(magnitude).all()
    kernels, permutation, permutation_rows = build_kernels(frame, f, train)
    predictions = {'no_change': np.zeros_like(y), 'raw_STATE': f['state_delta'].astype(float)}
    dose_mean = np.zeros_like(y)
    dose_scalar = np.zeros(len(frame))
    for dose in sorted(frame.dose_uM.unique()):
        fitting = train[frame.iloc[train].dose_uM.to_numpy() == dose]
        mask = frame.dose_uM == dose
        dose_mean[mask] = y[fitting].mean(0)
        dose_scalar[mask] = magnitude[fitting].mean()
    predictions['dose_mean'] = dose_mean
    scalars = {'no_change': np.zeros(len(frame)), 'raw_STATE': np.sqrt(np.mean(f['state_delta'] ** 2, axis=1)), 'dose_mean': dose_scalar}
    selection = {}
    with threadpool_limits(limits=2):
        for name, kernel in kernels.items():
            trials = []
            for alpha in [0.1, 1.0, 10.0]:
                p = predict(kernel, train, y, alpha)
                trials.append((float(group_loss(frame, y, p, dev).mean()), alpha, p))
            loss, alpha, p = min(trials, key=lambda v: (v[0], v[1]))
            predictions[name] = p
            scalars[name] = predict(kernel, train, magnitude, alpha)
            selection[name] = {'alpha': alpha, 'development_group_mse': loss, 'trials': [{'alpha': a, 'development_group_mse': e} for e, a, _ in trials]}
        simple = min(['no_change', 'dose_mean'], key=lambda name: group_loss(frame, y, predictions[name], dev).mean())
        # Within the simple world choose strongest simple/non-STATE forecast only on dev scalar error.
        reference = min([simple, 'M1', 'metadata_only', 'basal_only', 'missingness_only'], key=lambda name: np.mean((scalars[name][dev]-magnitude[dev])**2))
        selection['M0_selected'] = simple
        selection['decision_reference_selected'] = reference
        write(out/'model_selection.json', selection)
        # Save predictions before any evaluation-statistic computation.
        np.savez_compressed(out/'predictions.npz', **predictions, **{'scalar_'+k: v for k,v in scalars.items()}, observed_delta=y, observed_magnitude=magnitude, condition_id=frame.condition_id.to_numpy(dtype=str))
        np.savez_compressed(out/'kernels.npz', **kernels, permutation=permutation)
        write(out/'permutation.json', permutation_rows)
        exported = frame.copy()
        exported['world_reference'] = scalars[reference]
        exported['world_state'] = scalars['M2']
        exported['observed_magnitude'] = magnitude
        exported.to_csv(out/'decision_records.csv', index=False)
        # Held-out label poisoning must not affect any training predictions.
        poisoned = y.copy()
        poisoned[np.r_[cal,ev]] = 1e9
        isolation = {}
        for name, kernel in kernels.items():
            checked = predict(kernel, train, poisoned, selection[name]['alpha'])
            isolation[name] = bool(np.array_equal(checked, predictions[name]))
        assert all(isolation.values())
        write(out/'isolation_check.json', {'evaluation_calibration_outcome_poisoning_bitwise_identical': isolation})
        metrics, errors = {}, {}
        for name, p in predictions.items():
            loss = group_loss(frame, y, p, ev)
            errors[name] = loss.to_numpy()
            s = scalars[name]
            residual = np.abs(s[cal] - magnitude[cal])
            group_max = pd.DataFrame({'group': frame.iloc[cal].chemical_group.to_numpy(), 'residual': residual}).groupby('group').residual.max().to_numpy()
            rank = min(len(group_max), int(np.ceil((len(group_max)+1)*0.8)))
            width = float(np.sort(group_max)[rank-1])
            coverage = np.abs(s[ev]-magnitude[ev]) <= width
            test_high = ev[frame.iloc[ev].dose_uM.to_numpy() == 5]
            ordering = []
            for a_i, a in enumerate(test_high):
                for b in test_high[a_i+1:]:
                    ordering.append(0.5 if s[a] == s[b] or magnitude[a] == magnitude[b] else float((s[a]-s[b])*(magnitude[a]-magnitude[b]) > 0))
            per_group_coverage = pd.DataFrame({'group': frame.iloc[ev].chemical_group.to_numpy(), 'covered': coverage}).groupby('group').covered.all()
            metrics[name] = {'evaluation_group_mse': float(loss.mean()), 'evaluation_mae': float(np.mean(np.abs(y[ev]-p[ev]))), 'scalar_mae': float(np.mean(np.abs(s[ev]-magnitude[ev]))), 'high_dose_pair_ordering': float(np.mean(ordering)), 'interval_halfwidth_80': width, 'interval_row_coverage': float(coverage.mean()), 'interval_group_simultaneous_coverage': float(per_group_coverage.mean()), 'calibration_drugs': len(group_max), 'selective_risk': 'constant method-specific conformal width; no within-method uncertainty ranking; full coverage retained', 'by_dose_mse': {str(d): float(np.mean((y[ix]-p[ix])**2)) for d in sorted(frame.dose_uM.unique()) if len(ix := ev[frame.iloc[ev].dose_uM.to_numpy() == d])}, 'by_plate_mse': {str(plate): float(np.mean((y[ix]-p[ix])**2)) for plate in frame.iloc[ev].plate.unique() if len(ix := ev[frame.iloc[ev].plate.to_numpy() == plate])}}
        rng = np.random.default_rng(731)
        comparisons = {}
        for comparator in [simple, 'M1']:
            difference = errors['M2'] - errors[comparator]
            bootstrap = difference[rng.integers(0, len(difference), (2000,len(difference)))].mean(1)
            comparisons[comparator] = {'M2_minus_comparator_mse': float(difference.mean()), 'descriptive_drug_bootstrap_95': np.quantile(bootstrap,[0.025,0.975]).tolist(), 'groups': len(difference)}
        efficiency = []
        train_drugs = list(dict.fromkeys(frame.iloc[train].drug))
        for n in [6,12,24]:
            subset = np.flatnonzero(frame.drug.isin(train_drugs[:n]))
            # Rebuild all training-dependent kernel preprocessing on this subset.
            smaller, _, _ = build_kernels(frame, f, subset)
            for name in ['M1','M2']:
                p = predict(smaller[name], subset, y, selection[name]['alpha'])
                efficiency.append({'training_drugs': n, 'method': name, 'evaluation_group_mse': float(group_loss(frame,y,p,ev).mean()), 'alpha_reused_from_full_training_selection': selection[name]['alpha']})
        write(out/'sample_efficiency.json', efficiency)
        passed = all(v['descriptive_drug_bootstrap_95'][1] < 0 for v in comparisons.values())
        write(out/'metrics.json', {'primary': comparisons, 'primary_success_rule_passed': passed, 'methods': metrics, 'evaluation_groups': len(errors['M2']), 'interpretation': 'exploratory conditional-on-one-cell/source panel; shared plate controls and pretraining overlap limit inference'})
        pd.DataFrame(errors, index=group_loss(frame,y,predictions['M2'],ev).index).rename_axis('chemical_group').to_csv(out/'group_errors.csv')
    cpu1 = proc.cpu_times()
    write(out/'resources.json', {'elapsed_seconds': time.perf_counter()-started,'cpu_seconds': cpu1.user+cpu1.system-cpu.user-cpu.system,'process_peak_working_set_bytes': proc.memory_info().peak_wset,'api_calls':0,'api_tokens':0,'api_cost_usd':0,'downloaded_bytes':0,'laboratory_credits':0,'model_fits': len(kernels)*4+6,'source_sha256': sha(__file__)})
    write(out/'manifest.json', {p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({'primary':comparisons,'passed':passed,'decision_reference':reference}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
