"""Predeclared resistant-culture pair ordering with ordinary direct controls."""
import hashlib
import itertools
import json
from pathlib import Path
import time
import zipfile
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_functional_increment'
OLD = ROOT / 'log/20261022/cdk_middle_feedback'
SOURCE = ROOT / 'log/20261022/next_mechanism/source/cdk_review/table_s4.body'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def rank_targets(y):
    return np.array([(np.sum(y < v) + .5 * np.sum(y == v)) / len(y) for v in y])


def predict(gram, labels, groups, train, test, lam):
    # Access labels only through train, including target-rank construction.
    target = np.zeros(len(train))
    for group in set(groups[j] for j in train):
        positions = [k for k, j in enumerate(train) if groups[j] == group]
        target[positions] = rank_targets(labels[[train[k] for k in positions]])
    q = np.eye(len(groups))
    means = []
    fallbacks = []
    for i in range(len(groups)):
        positions = [k for k, j in enumerate(train) if groups[j] == groups[i]]
        fallbacks.append(not positions)
        if not positions:
            positions = list(range(len(train)))
        members = [train[k] for k in positions]
        q[i, members] -= 1 / len(members)
        means.append(float(target[positions].mean()))
    centered = q @ gram @ q.T
    kernel = centered[np.ix_(train, train)]
    scale = float(np.trace(kernel) / len(train))
    scale = scale if scale > 1e-12 else 1.0
    alpha = np.linalg.solve(kernel + lam * scale * np.eye(len(train)), target - np.array(means)[train])
    predictions = np.array(means)[test] + centered[np.ix_(test, train)] @ alpha
    return predictions, np.array(means)[test], [fallbacks[i] for i in test]


def grams(data):
    early = np.sqrt(data[:, 0])
    middle = np.sqrt(data[:, 1])
    e = early @ early.T
    return {'early': e, 'early_middle': (e + middle @ middle.T) / 2}


def read_selected(tasks):
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '76e61a74f2574ff0e50bf70e514773ff14a14f3f98225367c6dfcb0818e51345'
    expected = {f'{er}_{drug}R_{rep}': i for i, (drug, er, rep) in enumerate(tasks)}
    values = np.full((len(tasks), 2), np.nan)
    records, seen = [], set()
    with zipfile.ZipFile(SOURCE) as archive:
        strings_root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        strings = [''.join(t.text or '' for t in item.findall('.//s:t', NS)) for item in strings_root]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))

        def decode(cell):
            assert cell.find('s:f', NS) is None, 'Formula forbidden'
            raw = cell.find('s:v', NS)
            if cell.get('t') == 'inlineStr':
                return ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
            if raw is None:
                return ''
            return strings[int(raw.text)] if cell.get('t') == 's' else raw.text

        for row in sheet.findall('.//s:sheetData/s:row', NS):
            cells = {''.join(c for c in cell.get('r') if c.isalpha()): cell for cell in row}
            if 'B' not in cells:
                continue
            name = decode(cells['B']).strip()
            if name not in expected:
                assert name == 'Samples' or '_Vehicle_' in name, f'Unexpected identity: {name}'
                continue
            assert name not in seen
            seen.add(name)
            for j, col in enumerate(('C', 'D')):
                raw = decode(cells[col]).strip() if col in cells else ''
                record = {'sample': name, 'task': tasks[expected[name]], 'column': col, 'raw': raw}
                if raw not in ('', 'N/A'):
                    v = float(raw)
                    assert np.isfinite(v) and v > 0, record
                    values[expected[name], j] = v
                record['eligible'] = bool(np.isfinite(values[expected[name], j]))
                records.append(record)
    assert seen == set(expected)
    return values, records


def evaluate(values, tasks, kernels):
    groups = [f'{drug}_{er}' for drug, er, _ in tasks]
    result = {}
    for challenge, y in zip(('palbociclib', 'abemaciclib'), values.T):
        eligible = np.flatnonzero(np.isfinite(y)).tolist()
        rows, ties, nonestimable = [], [], []
        for a, b in itertools.combinations(eligible, 2):
            if groups[a] != groups[b]:
                continue
            if y[a] == y[b]:
                ties.append([int(a), int(b)])
                continue
            train = [i for i in eligible if i not in (a, b)]
            if len(train) < 2:
                nonestimable.append({'test': [int(a), int(b)], 'group': groups[a],
                                     'reason': 'fewer_than_two_eligible_source_cultures', 'train': train})
                continue
            for lam in (.1, 1, 10):
                for name, gram in kernels.items():
                    pred, baseline, fallback = predict(gram, y, groups, train, [a, b], lam)
                    diff = float(pred[0] - pred[1])
                    loss = .5 if abs(diff) <= 1e-12 else float(np.sign(diff) != np.sign(y[a] - y[b]))
                    rows.append({'test': [int(a), int(b)], 'group': groups[a], 'train': [int(i) for i in train],
                                 'method': name, 'lambda': lam, 'predictions': pred.tolist(),
                                 'baseline': baseline.tolist(), 'pooled_fallback': fallback, 'loss': loss,
                                 'truth': [float(y[a]), float(y[b])]})
        summary = {}
        for lam in (.1, 1, 10):
            summary[str(lam)] = {}
            for name in kernels:
                selected = [r for r in rows if r['lambda'] == lam and r['method'] == name]
                group_loss = {g: float(np.mean([r['loss'] for r in selected if r['group'] == g]))
                              for g in sorted(set(r['group'] for r in selected))}
                summary[str(lam)][name] = {'group_loss': group_loss,
                    'macro_loss': float(np.mean(list(group_loss.values()))) if group_loss else None,
                    'pairs': len(selected)}
        result[challenge] = {'eligible': eligible, 'missing': list(np.flatnonzero(~np.isfinite(y)).astype(int).tolist()),
                             'true_ties': ties, 'nonestimable': nonestimable,
                             'condition_baseline_loss': .5 if rows else None,
                             'summary': summary, 'rows': rows}
    return result


def main():
    started = time.perf_counter()
    assert not (OUT / 'RESULT.json').exists(), 'No silent rerun'
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for name, digest in freeze['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    metadata = json.loads((OLD / 'PREPARATION.json').read_text())
    assert hashlib.sha256((OLD / 'prepared.npz').read_bytes()).hexdigest() == metadata['prepared_sha256']
    data = np.load(OLD / 'prepared.npz')['compositions']
    kernels = grams(data)
    values, records = read_selected(metadata['tasks'])
    result = evaluate(values, metadata['tasks'], kernels)
    payload = {'tasks': metadata['tasks'], 'source_records': records, 'results': result,
               'wall_seconds': time.perf_counter() - started,
               'scope': 'Exploratory within-condition functional ordering; overlapping pairs, unknown measurement uncertainty; no WM/agent/RSI claim'}
    (OUT / 'RESULT.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({k: v['summary'] for k, v in result.items()}, indent=2))


if __name__ == '__main__':
    main()
