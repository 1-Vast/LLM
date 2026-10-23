"""Conventional finite functional-feedback pilot; only frozen development rows decoded."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'
PRIOR = ROOT / 'log/20261022/decrypte_source_qualification'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
QUERY = np.array([1, 2, 3])
SUPPORT = {0: np.array([], dtype=int), 1: np.array([4]), 2: np.array([0, 4])}
METHODS = ('simple', 'gaussian', 'direct', 'library')
GRIDS = {'simple': [None], 'gaussian': [0.01, 0.1, 1., 10.],
         'direct': [0.01, 0.1, 1., 10.], 'library': [0.1, 0.3, 1., 3.]}


def read_development():
    start = time.perf_counter()
    partition = json.loads((OUT / 'PARTITIONS.json').read_text(encoding='utf-8'))
    dev = set(partition['partitions']['development'])
    ids = json.loads((PRIOR / 'IDENTITIES.json').read_text(encoding='utf-8'))['rows']
    allowed = {r['row']: r for r in ids if r['drug'] in dev and r['cell'] == 'Jurkat'}
    source = PRIOR / 'supplement.xlsx'
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha == partition['source_sha256']
    records = []
    with zipfile.ZipFile(source) as z:
        # This exact member was resolved through the workbook relationships in identities.py.
        member = json.loads((PRIOR / 'IDENTITIES.json').read_text(encoding='utf-8'))['member']
        with z.open(member) as handle:
            for _, row in ET.iterparse(handle, events=('end',)):
                if row.tag != '{' + NS['s'] + '}row':
                    continue
                index = int(row.attrib['r'])
                if index not in allowed:
                    row.clear()
                    continue
                record = {k: allowed[index][k] for k in ('row', 'drug', 'cell', 'assay')}
                record['cells'] = {}
                for cell in row.findall('s:c', NS):
                    column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                    if column not in 'JKLMNOPQRST':
                        continue
                    assert cell.find('s:f', NS) is None
                    assert cell.attrib.get('t', 'n') == 'n', cell.attrib['r']
                    value = cell.find('s:v', NS)
                    assert value is not None and value.text is not None
                    number = float(value.text)
                    assert np.isfinite(number)
                    record['cells'][column] = {'coordinate': cell.attrib['r'], 'payload': value.text, 'value': number}
                assert set(record['cells']) == set('JKLMNOPQRST')
                records.append(record)
                row.clear()
    assert len(records) == len(dev) * 3
    assert Counter(r['assay'] for r in records) == {'Metabolic activity': 48, 'Confluency': 48, 'Cytotoxicity': 48}
    drugs = sorted(dev)
    primary = {r['drug']: r for r in records if r['assay'] == 'Metabolic activity'}
    y = np.array([[primary[d]['cells'][c]['value'] for c in 'KLMNO'] for d in drugs])
    chemistry = {r['drug']: r for r in partition['chemical_metadata']}
    groups = [chemistry[d]['group'] for d in drugs]
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    features = []
    missing = []
    for d in drugs:
        smi = chemistry[d].get('smiles')
        missing.append(smi is None)
        if smi is None:
            features.append(np.zeros(2048))
        else:
            mol = Chem.MolFromSmiles(smi)
            parent = max(Chem.GetMolFrags(mol, asMols=True), key=lambda m: (m.GetNumHeavyAtoms(), Chem.MolToSmiles(m)))
            features.append(np.asarray(generator.GetFingerprint(parent), dtype=float))
    features = np.stack(features)
    intersection = features @ features.T
    union = features.sum(1)[:, None] + features.sum(1)[None, :] - intersection
    chemical = np.divide(intersection, union, out=np.zeros_like(union), where=union > 0)
    np.fill_diagonal(chemical, 1.)
    prepared = {'drugs': drugs, 'groups': groups, 'missing_structure': missing,
                'y': y.tolist(), 'chemical': chemical.tolist(), 'records': records,
                'extracted_coordinates': [cell['coordinate'] for r in records for cell in r['cells'].values()],
                'source_sha256': sha, 'read_wall_s': time.perf_counter() - start}
    (OUT / 'DEVELOPMENT_VALUES.json').write_text(json.dumps(prepared, ensure_ascii=False, indent=2), encoding='utf-8')
    return prepared


def quality(data):
    result = {}
    for assay in ('Metabolic activity', 'Confluency', 'Cytotoxicity'):
        rows = [r for r in data['records'] if r['assay'] == assay]
        relative = np.array([[r['cells'][c]['value'] for c in 'KLMNO'] for r in rows])
        raw = np.array([[r['cells'][c]['value'] for c in 'PQRST'] for r in rows])
        baseline = np.array([r['cells']['J']['value'] for r in rows])
        ratio_errors = []
        for a, b in zip(raw, relative):
            if np.all(b != 0):
                ratios = a / b
                ratio_errors.append(float(np.ptp(ratios) / max(1., np.max(np.abs(ratios)))))
        result[assay] = {'relative_min': float(relative.min()), 'relative_max': float(relative.max()),
            'negative_relative_cells': int(np.sum(relative < 0)), 'zero_relative_cells': int(np.sum(relative == 0)),
            'mean_abs_deviation_from_1': float(np.mean(np.abs(relative - 1))),
            'range_quantiles': np.quantile(np.ptp(relative, axis=1), [0, .25, .5, .75, 1]).tolist(),
            'relative_zero_max_abs_deviation_from_1': float(np.max(np.abs(baseline - 1))),
            'raw_over_relative_denominator_relative_spread_max': max(ratio_errors) if ratio_errors else None,
            'denominator_eligible_drugs': len(ratio_errors)}
    return result


def predict(method, train, target, y_source, chemical, budget, hyper, target_support):
    """Only source response arrays and explicitly revealed target supports enter this function."""
    src = y_source[train]
    support = SUPPORT[budget]
    mean = src.mean(0)
    if method == 'simple':
        if budget == 0:
            return np.ones(3)
        if budget == 1:
            return np.repeat(target_support[0], 3)
        return target_support[0] + (target_support[1] - target_support[0]) * np.array([.25, .5, .75])
    if method == 'gaussian':
        if budget == 0:
            return mean[QUERY]
        covariance = (src - mean).T @ (src - mean) / max(1, len(train) - 1)
        scale = max(float(np.trace(covariance) / 5), 1e-12)
        block = covariance[np.ix_(support, support)] + hyper * scale * np.eye(len(support))
        return mean[QUERY] + covariance[np.ix_(QUERY, support)] @ np.linalg.solve(block, target_support - mean[support])
    if method == 'library':
        if budget == 0:
            return mean[QUERY]
        scale = np.maximum(src[:, support].std(0), 1e-6)
        distance = np.mean(((src[:, support] - target_support) / scale) ** 2, axis=1)
        logweights = -distance / (2 * hyper * hyper)
        weights = np.exp(logweights - logweights.max())
        return weights @ src[:, QUERY] / weights.sum()
    if method == 'direct':
        k = chemical[np.ix_(train, train)].copy()
        kt = chemical[target, train].copy()
        if budget:
            scale = np.maximum(src[:, support].std(0), 1e-6)
            xs = (src[:, support] - mean[support]) / scale
            xt = (target_support - mean[support]) / scale
            k += xs @ xs.T / budget
            kt += xt @ xs.T / budget
        kmean = k.mean(0)
        grand = kmean.mean()
        kt = kt - kt.mean() - kmean + grand
        k = k - kmean[:, None] - kmean[None, :] + grand
        coefficients = np.linalg.solve(k + len(train) * hyper * np.eye(len(train)), src[:, QUERY] - mean[QUERY])
        return mean[QUERY] + kt @ coefficients
    raise ValueError(method)


def nested_evaluate(data):
    start = time.perf_counter()
    y = np.array(data['y'])
    chem = np.array(data['chemical'])
    groups = np.array(data['groups'])
    n = len(y)
    predictions = {str(b): {m: np.zeros((n, 3)) for m in METHODS} for b in SUPPORT}
    selected = {str(b): np.zeros((n, 3)) for b in SUPPORT}
    choices = []
    # Cache source-only inner predictions by exact ordered training set. Same folds recur across outer groups.
    cache = {}
    for outer_group in sorted(set(groups)):
        targets = np.flatnonzero(groups == outer_group)
        outer_train = np.flatnonzero(groups != outer_group)
        for budget in SUPPORT:
            candidate_scores = []
            for method in METHODS:
                grid = [None] if budget == 0 and method in ('gaussian', 'library') else GRIDS[method]
                tuning = []
                for hyper in grid:
                    errors = []
                    for inner_group in sorted(set(groups[outer_train])):
                        train = outer_train[groups[outer_train] != inner_group]
                        validation = outer_train[groups[outer_train] == inner_group]
                        for val in validation:
                            key = (tuple(train), int(val), budget, method, hyper)
                            if key not in cache:
                                cache[key] = predict(method, train, val, y, chem, budget, hyper, y[val, SUPPORT[budget]])
                            errors.append(float(np.mean((cache[key] - y[val, QUERY]) ** 2)))
                    tuning.append((float(np.mean(errors)), hyper))
                best_score, best_hyper = min(tuning, key=lambda t: t[0])
                candidate_scores.append((best_score, method, best_hyper))
                for target in targets:
                    predictions[str(budget)][method][target] = predict(method, outer_train, target, y, chem, budget, best_hyper, y[target, SUPPORT[budget]])
                choices.append({'outer_group': outer_group, 'target_drugs': [data['drugs'][i] for i in targets],
                                'budget': budget, 'method': method, 'hyper': best_hyper, 'inner_mse': best_score,
                                'inner_grid': [{'mse': score, 'hyper': h} for score, h in tuning]})
            score, method, hyper = min(candidate_scores, key=lambda t: t[0])
            selected[str(budget)][targets] = predictions[str(budget)][method][targets]
            choices.append({'outer_group': outer_group, 'budget': budget, 'selected_method': method, 'hyper': hyper, 'inner_mse': score})
    return {'predictions': {b: {m: p.tolist() for m, p in v.items()} for b, v in predictions.items()},
            'selected_predictions': {b: p.tolist() for b, p in selected.items()}, 'choices': choices,
            'query_indices': QUERY.tolist(), 'support_indices': {str(b): s.tolist() for b, s in SUPPORT.items()},
            'wall_s': time.perf_counter() - start, 'cached_inner_predictions': len(cache)}


def summarize(data, result):
    y = np.array(data['y'])[:, QUERY]
    groups = np.array(data['groups'])
    programs = {b: {**v, 'selected': result['selected_predictions'][b]} for b, v in result['predictions'].items()}
    losses = {b: {m: (np.array(p) - y) ** 2 for m, p in v.items()} for b, v in programs.items()}
    metrics = {b: {m: {'mse': float(e.mean()), 'mae': float(np.mean(np.abs(np.array(programs[b][m]) - y))),
                            'dose_mse': e.mean(0).tolist(), 'drug_mse': e.mean(1).tolist()} for m, e in v.items()} for b, v in losses.items()}
    rng = np.random.default_rng(20261022)
    unique = sorted(set(groups))
    counts = np.array([np.sum(groups == g) for g in unique])
    draws = rng.multinomial(len(unique), np.ones(len(unique)) / len(unique), size=10000)

    def compare(base, updated):
        diff = (base - updated).mean(1)
        totals = np.array([diff[groups == g].sum() for g in unique])
        boot = draws @ totals / (draws @ counts)
        largest = np.argsort(np.abs(diff))[-3:]
        leave_one = [float(np.delete(diff, i).mean()) for i in largest]
        return {'mean_gain': float(diff.mean()), 'ci95': np.quantile(boot, [.025, .975]).tolist(),
                'ci97_5_two_budget_gate': np.quantile(boot, [.0125, .9875]).tolist(),
                'dose_mean_gain': (base - updated).mean(0).tolist(), 'positive_drugs': int(np.sum(diff > 0)),
                'largest_absolute_gain_drugs': [data['drugs'][i] for i in largest],
                'delete_each_largest_gain_mean': leave_one}

    comparisons = {}
    oracle_method = min(losses['0'], key=lambda m: losses['0'][m].mean())
    for b in ('1', '2'):
        for method in (*METHODS, 'selected'):
            comparisons[f'{method}_B{b}_vs_same_B0'] = compare(losses['0'][method], losses[b][method])
        comparisons[f'selected_B{b}_vs_selected_B0'] = compare(losses['0']['selected'], losses[b]['selected'])
        comparisons[f'selected_B{b}_vs_posthoc_oracle_B0'] = compare(losses['0'][oracle_method], losses[b]['selected'])
    gate = {}
    for b in ('1', '2'):
        c = comparisons[f'selected_B{b}_vs_selected_B0']
        gate[b] = {'pass': bool(c['ci97_5_two_budget_gate'][0] > 0 and sum(x >= 0 for x in c['dose_mean_gain']) >= 2
                               and min(c['delete_each_largest_gain_mean']) > 0)}
    return {'metrics': metrics, 'comparisons': comparisons, 'development_gate': gate,
            'any_budget_gate_pass': any(g['pass'] for g in gate.values()),
            'bootstrap': {'seed': 20261022, 'draws': 10000, 'unit': 'development Murcko scaffold group'},
            'drugs': data['drugs'], 'source_group_count': len(unique), 'posthoc_B0_oracle_method': oracle_method}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'evaluate'))
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert not (OUT / 'DEVELOPMENT_VALUES.json').exists()
        data = read_development()
        qa = quality(data)
        (OUT / 'QUALITY.json').write_text(json.dumps(qa, indent=2), encoding='utf-8')
        print(json.dumps({'development_drugs': len(data['drugs']), 'quality': qa}, indent=2))
    else:
        assert not (OUT / 'PREDICTIONS.json').exists()
        data = json.loads((OUT / 'DEVELOPMENT_VALUES.json').read_text(encoding='utf-8'))
        result = nested_evaluate(data)
        result['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'rdkit': rdBase.rdkitVersion}
        (OUT / 'PREDICTIONS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        summary = summarize(data, result)
        (OUT / 'SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'metrics': {b: {m: v['mse'] for m, v in rows.items()} for b, rows in summary['metrics'].items()},
                          'gate': summary['development_gate'], 'wall_s': result['wall_s']}, indent=2))


if __name__ == '__main__':
    main()
