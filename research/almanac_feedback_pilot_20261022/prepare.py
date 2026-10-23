"""Selectively decode only frozen allowed PercentGrowth source rows."""
import csv
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'
OLD = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'


def verify_freeze():
    manifest = json.loads((OUT / 'PRE_RESPONSE_FREEZE.json').read_text())
    for rel, sha in manifest['bindings'].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha, rel


def main():
    verify_freeze()
    assert not (OUT / 'VALUES.npz').exists()
    start = time.perf_counter()
    split = json.loads((OUT / 'SPLIT.json').read_text())
    tasks = json.loads((OUT / 'DESIGN_TASKS.json').read_text())
    chosen = [[tasks[i] for i in row] for row in split['task_indices_by_cell_pair']]
    solo_lines = np.array([[t['single_agent_rows'] for t in row] for row in chosen])
    combo_lines = np.array([[t['combination_rows'] for t in row] for row in chosen])
    allowed = set(map(int, solo_lines.ravel())) | set(map(int, combo_lines.ravel()))
    values = {}
    with zipfile.ZipFile(OLD / 'archive.zip') as z:
        with z.open('ComboDrugGrowth_Nov2017.csv') as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            header = next(reader)
            position = header.index('PERCENTGROWTH')
            for line, row in enumerate(reader, 2):
                if line in allowed:
                    values[line] = float(row[position]) / 100
    assert values.keys() == allowed
    solo = np.array([values[int(i)] for i in solo_lines.ravel()]).reshape(solo_lines.shape)
    y = np.array([values[int(i)] for i in combo_lines.ravel()]).reshape(combo_lines.shape)
    assert np.isfinite(solo).all() and np.isfinite(y).all()
    np.savez_compressed(OUT / 'VALUES.npz', solo=solo, y=y, solo_lines=solo_lines, combo_lines=combo_lines)
    (OUT / 'VALUE_RECEIPT.json').write_text(json.dumps({
        'column': 'PERCENTGROWTH / 100', 'solo_shape': list(solo.shape), 'y_shape': list(y.shape),
        'unique_decoded_rows': len(values), 'unique_solos': len(set(solo_lines.ravel())),
        'unique_combinations': len(set(combo_lines.ravel())), 'wall_s': time.perf_counter() - start,
        'no_response_filtering': True, 'selection_and_later_values_decoded': False}, indent=2), encoding='utf-8')
    print('Prepared authorized functional entries; no payloads printed.', flush=True)


if __name__ == '__main__':
    main()
