"""One frozen four-column terminal read-contrast diagnostic, no model fitting."""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/replicated_contrast'
DATA = OUT/'counts.body'
PRIOR = ROOT/'log/20261023/interaction_error_diagnostic/PAIR_IDS.json'
COLS = ['MCF7_T9_1', 'MDAMB231_T9_1', 'MCF7_T9_2', 'MDAMB231_T9_2']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_pairs():
    pairs = [tuple(p) for p in json.loads(PRIOR.read_text())]
    return sorted(pairs, key=lambda p: hashlib.sha256(
        ('replicated-contrast-v1|'+'|'.join(p)).encode()).hexdigest())[:1024]


def extract(path, pairs):
    positions = {p: i for i, p in enumerate(pairs)}
    counts, mapping, ids = [], [], []
    with path.open('rb') as source:
        header = next(csv.reader([source.readline().decode('utf-8-sig')]))
        assert header[:5] == ['construct_id', 'target_a_id', 'probe_a_id', 'target_b_id', 'probe_b_id']
        columns = [header.index(name) for name in COLS]
        assert len(set(columns)) == 4
        for line in source:
            fields = line.rstrip(b'\r\n').split(b',')
            assert len(fields) == len(header)
            construct, a, ga, b, gb = [s.decode('utf-8') for s in fields[:5]]
            pair = tuple(sorted((a, b)))
            if pair not in positions:
                continue
            # All other count fields, including plasmid/lung, remain opaque bytes.
            row = [float(fields[j]) for j in columns]
            assert all(np.isfinite(v) and v >= 0 and v.is_integer() for v in row), construct
            counts.append(row)
            mapping.append(positions[pair])
            ids.append(construct)
    assert len(ids) == len(set(ids))
    counts, mapping = np.array(counts), np.array(mapping, dtype=np.int64)
    sizes = np.bincount(mapping, minlength=len(pairs))
    assert np.isin(sizes, [9, 18]).all()
    means = np.zeros((len(pairs), 4))
    np.add.at(means, mapping, np.log2(counts+1))
    means /= sizes[:, None]
    return counts, mapping, ids, means, sizes


def contrasts(means):
    differences = means[::2] - means[1::2]
    return differences, np.column_stack((differences[:, 0]-differences[:, 1],
                                         differences[:, 2]-differences[:, 3]))


def main():
    begin = time.perf_counter()
    assert not (OUT/'CONTRAST_RESULT.json').exists()
    assert sha(DATA) == 'b406381dc961859d59753a693a0224098378fc83165a25645f4bfe4ac0f6d0bb'
    pairs = selected_pairs()
    assert len(pairs) == 1024 and len(set(pairs)) == 1024
    (OUT/'SELECTED_PAIR_IDS.json').write_text(json.dumps(pairs), encoding='utf-8')
    bound = [Path(__file__), OUT/'PLAN.md', OUT/'NUMERICAL_PLAN.md', OUT/'SELECTED_PAIR_IDS.json', DATA, PRIOR]
    freeze = OUT/'NUMERICAL_FREEZE.json'
    assert not freeze.exists()
    freeze.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
        files={str(p.relative_to(ROOT)): sha(p) for p in bound},
        scope='Before count extraction; four exact samples and fixed ID-hash contrasts'), indent=2), encoding='utf-8')
    counts, mapping, ids, means, sizes = extract(DATA, pairs)
    differences, delta = contrasts(means)
    discovery = np.abs(delta[:, 0]) >= .5
    same_sign = (delta[:, 0]*delta[:, 1]) > 0
    confirmation = discovery & same_sign & (np.abs(delta[:, 1]) >= .25)
    n = int(discovery.sum())
    fraction = float(confirmation.sum()/n) if n else None
    correlation_defined = bool(np.all(np.std(delta, axis=0) > 0))
    np.savez_compressed(OUT/'CONTRAST_ARRAYS.npz', counts=counts, pair_row=mapping,
                        pair_means=means, construct_sizes=sizes, context_differences=differences,
                        delta=delta, discovery=discovery, confirmation=confirmation)
    (OUT/'CONSTRUCT_IDS.json').write_text(json.dumps(ids), encoding='utf-8')
    report = dict(utc=datetime.now(timezone.utc).isoformat(), selected_columns=COLS,
                  actions=1024, contrast_n=512, construct_rows=len(counts),
                  count_zero_fraction=dict(zip(COLS, (counts == 0).mean(axis=0).tolist())),
                  count_le_five_fraction=dict(zip(COLS, (counts <= 5).mean(axis=0).tolist())),
                  correlation_defined=correlation_defined,
                  pearson=float(np.corrcoef(delta.T)[0, 1]) if correlation_defined else None,
                  spearman=float(spearmanr(delta[:, 0], delta[:, 1]).statistic) if correlation_defined else None,
                  all_contrast_sign_concordance=float(same_sign.mean()),
                  discovery_n=n, confirmation_n=int(confirmation.sum()),
                  confirmation_fraction=fraction,
                  measurement_screen=bool(n >= 20 and fraction is not None and fraction >= .8),
                  numerical_seconds=time.perf_counter()-begin,
                  arrays_sha256=sha(OUT/'CONTRAST_ARRAYS.npz'), ids_sha256=sha(OUT/'CONSTRUCT_IDS.json'),
                  environment=dict(python=platform.python_version(), numpy=np.__version__),
                  git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  scope='Repeated differential log(count+1) read statistic, not GI, fitness, biological reversal or RSI',
                  goal='ACTIVE / NOT_ACHIEVED')
    (OUT/'CONTRAST_RESULT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
