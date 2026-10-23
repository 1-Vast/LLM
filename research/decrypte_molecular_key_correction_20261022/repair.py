"""Repair a drug-prefixed protein key; keep the frozen predictors unchanged."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/decrypte_molecular_increment'
OUT = SOURCE / 'key_correction'
MODEL = ROOT / 'research/decrypte_molecular_increment_20261022'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original_verify():
    original = json.loads((SOURCE / 'FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in original['files'].items():
        assert sha(ROOT / name) == expected, name


def verify():
    original_verify()
    frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in frozen['files'].items():
        assert sha(ROOT / name) == expected, name


def freeze():
    original_verify()
    assert not (OUT / 'FREEZE.json').exists()
    assert not (OUT / 'matrix.npz').exists()
    assert not (SOURCE / 'PREDICTIONS.json').exists() and not (SOURCE / 'SUMMARY.json').exists()
    assert (SOURCE / 'EVALUATE_CONSOLE.txt').stat().st_size == 0
    paths = [Path(__file__).resolve(), OUT / 'PROTOCOL.md']
    paths += [SOURCE / name for name in (
        'FREEZE.json', 'PAYLOADS.json', 'PREPARATION.json', 'matrix.npz',
        'IDENTITY_INVENTORY.json', 'IDENTITY_POLICY.json', 'EVALUATE_CONSOLE.txt',
        'review/PROTEIN_KEY_CORRECTION.md', 'assay/KEY_CORRECTION_REVIEW.md')]
    frozen = {'utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Post-extraction exact key correction; no prior saved model scores; exposure disclosed',
              'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}}
    (OUT / 'FREEZE.json').write_text(json.dumps(frozen, indent=2), encoding='utf-8')
    print(json.dumps({'frozen_files': len(paths), 'utc': frozen['utc']}))


def prepare():
    verify()
    assert not (OUT / 'matrix.npz').exists()
    inventory = json.loads((SOURCE / 'IDENTITY_INVENTORY.json').read_text(encoding='utf-8'))
    payloads = json.loads((SOURCE / 'PAYLOADS.json').read_text(encoding='utf-8'))
    previous = json.loads((SOURCE / 'PREPARATION.json').read_text(encoding='utf-8'))
    labels = {}
    for record in inventory['records']:
        assert len(record['distinct_internal_drug_counts']) == 1
        labels[record['drug']] = next(iter(record['distinct_internal_drug_counts']))
    corrected, keymap = {}, {}
    for drug, entries in payloads.items():
        prefix = labels[drug] + ':'
        corrected[drug], keymap[drug] = [], []
        seen = set()
        for identifier, line, payload in entries:
            assert identifier.startswith(prefix), (drug, line, 'prefix mismatch')
            suffix = identifier[len(prefix):]
            assert suffix and suffix not in seen, (drug, line, 'empty/colliding suffix')
            seen.add(suffix)
            corrected[drug].append((suffix, line, payload))
            keymap[drug].append((identifier, suffix, line))
    identifiers = sorted(set().union(*(set(row[0] for row in rows) for rows in corrected.values())))
    columns = {name: i for i, name in enumerate(identifiers)}
    x = np.full((48, len(identifiers)), np.nan)
    lines = np.zeros(x.shape, dtype=np.int32)
    for i, drug in enumerate(previous['drugs']):
        for identifier, line, payload in corrected[drug]:
            value = np.nan if payload.strip() in ('', 'NA', 'NaN', 'nan', '#N/A') else float(payload)
            if not np.isfinite(value):
                value = np.nan
            assert not np.isfinite(value) or value >= 0
            j = columns[identifier]
            x[i, j], lines[i, j] = value, line
    assert int(np.isfinite(x).sum()) == previous['finite_entries']
    np.savez_compressed(OUT / 'matrix.npz', intensity=x, row_indices=lines)
    (OUT / 'PAYLOADS.json').write_text(json.dumps(corrected, ensure_ascii=False), encoding='utf-8')
    (OUT / 'KEY_MAP.json').write_text(json.dumps(keymap, ensure_ascii=False), encoding='utf-8')
    result = dict(previous)
    result.update({'identifiers': identifiers, 'shape': list(x.shape),
                   'missing_entries': int(np.sum(~np.isfinite(x))),
                   'key_correction': 'exact raw observed drug prefix plus colon removed once; suffix retained whole',
                   'original_preparation_sha256': sha(SOURCE / 'PREPARATION.json'),
                   'original_payloads_sha256': sha(SOURCE / 'PAYLOADS.json')})
    (OUT / 'PREPARATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'IDENTITY_POLICY.json').write_bytes((SOURCE / 'IDENTITY_POLICY.json').read_bytes())
    print(json.dumps({'shape': list(x.shape), 'finite': int(np.isfinite(x).sum()),
                      'proteins_observed_at_least_80pct': int((np.isfinite(x).mean(0) >= .8).sum())}))


def run():
    verify()
    sys.path.insert(0, str(MODEL))
    spec = importlib.util.spec_from_file_location('frozen_molecular_evaluator', MODEL / 'evaluate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.main()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'prepare', 'run'))
    action = parser.parse_args().action
    {'freeze': freeze, 'prepare': prepare, 'run': run}[action]()
