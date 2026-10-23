"""Independent centered per-pair audit; only separated source and saved outputs."""
from pathlib import Path
import hashlib
import json
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT/'log/20261023/functional_error_renewal/diagnostic'
OUT = ROOT/'log/20261023/functional_error_renewal/constructive'


def direct(array, i, j):
    ok = np.isfinite(array[:, i]) & np.isfinite(array[:, j])
    a, b = array[ok, i], array[ok, j]
    n = len(a)
    a, b = a-a.mean(), b-b.mean()
    aa, bb, ab = np.dot(a, a), np.dot(b, b), np.dot(a, b)
    denominator = np.sqrt(aa*bb)
    return dict(n=float(n), corr=float(np.clip(ab/denominator, -1, 1))
                if denominator > 1e-12 else 0.,
                covariance=float(ab/max(n-1, 1)),
                slope=float(ab/aa) if aa > 1e-12 else 0.,
                constant=bool(denominator <= 1e-12))


def main():
    start = time.perf_counter()
    with np.load(DATA/'SOURCE.npz', allow_pickle=False) as source:
        y, d, h = source['y'], source['discovery'], source['high']
        drugs, patients = source['drugs'], source['patients']
    result = json.loads((DATA/'RESULT.json').read_text())
    saved = json.loads((DATA/'PAIRS.json').read_text())
    boot = np.load(DATA/'BOOTSTRAP.npy', allow_pickle=False)
    arrays = [y[m] for m in (d & ~h, d & h, ~d & ~h, ~d & h)]
    assert len(set(patients)) == len(patients)
    assert [len(a) for a in arrays] == result['cell_sizes']
    source_hash = hashlib.sha256((DATA/'SOURCE.npz').read_bytes()).hexdigest()
    assert source_hash == result['source_sha256']
    eligible = []
    for i in range(len(drugs)):
        for j in range(i+1, len(drugs)):
            if all(np.sum(np.isfinite(a[:, i]) & np.isfinite(a[:, j])) >= 25
                   for a in arrays):
                eligible.append((i, j))
    assert len(eligible) == len(saved) == result['eligible_pairs']
    errors = {k: 0. for k in ('n', 'corr', 'covariance', 'slope', 'delta')}
    correlations = np.zeros((4, len(eligible)))
    constants = 0
    for k, ((i, j), row) in enumerate(zip(eligible, saved)):
        assert (str(drugs[i]), str(drugs[j])) == (row['drug_i'], row['drug_j'])
        for c, a in enumerate(arrays):
            calc = direct(a, i, j)
            for key in ('n', 'corr', 'covariance', 'slope'):
                errors[key] = max(errors[key], abs(calc[key]-row['cells'][c][key]))
            assert calc['constant'] == row['cells'][c]['constant']
            constants += calc['constant']
            correlations[c, k] = calc['corr']
        delta = correlations[1, k]-correlations[0, k]
        delta_r = correlations[3, k]-correlations[2, k]
        errors['delta'] = max(errors['delta'], abs(delta-row['delta_discovery']),
                              abs(delta_r-row['delta_replication']))
    assert errors['n'] == 0 and errors['covariance'] < 1e-8
    assert max(errors[k] for k in ('corr', 'slope', 'delta')) < 1e-10
    dd, dr = correlations[1]-correlations[0], correlations[3]-correlations[2]
    t = float(np.mean(dd*dr))
    assert abs(t-result['T']) < 1e-12
    reverse_d = correlations[0]*correlations[1] < 0
    reverse_r = correlations[2]*correlations[3] < 0
    fields = dict(constant_pair_cell_count=int(constants),
                  correlation_reversals_discovery=int(reverse_d.sum()),
                  correlation_reversals_replication=int(reverse_r.sum()),
                  correlation_reversals_both=int((reverse_d & reverse_r).sum()),
                  contrast_direction_agreement=float(np.mean(dd*dr > 0)))
    assert all(value == result[key] for key, value in fields.items())
    quantiles = np.quantile(boot, [.05, .025, .975])
    assert np.array_equal(quantiles, [result['bootstrap_lower_one_sided95'],
                                     *result['bootstrap_central95']])
    rng = np.random.default_rng(20261023)
    first_three = []
    for _ in range(3):
        repeated = [a[rng.integers(0, len(a), len(a))] for a in arrays]
        rs = np.array([[direct(a, i, j)['corr'] for i, j in eligible]
                       for a in repeated])
        first_three.append(float(np.mean((rs[1]-rs[0])*(rs[3]-rs[2]))))
    bootstrap_error = float(np.max(np.abs(np.array(first_three)-boot[:3])))
    assert bootstrap_error < 1e-12
    assert len(boot) == result['bootstraps'] == 2000
    decision = ('CONTINUE_ASSOCIATION_INVESTIGATION_ONLY' if quantiles[0] > .01
                else 'STOP_THIS_CD14_STRATIFIED_SOURCE_RATIONALE')
    assert decision == result['decision']
    report = dict(status='PASS', source_sha256=source_hash, eligible_pairs=len(eligible),
                  pair_cell_reconstructions=4*len(eligible), max_errors=errors,
                  T=t, recomputed_fields=fields, bootstrap_quantiles=quantiles.tolist(),
                  bootstrap_first_three=first_three,
                  bootstrap_first_three_max_error=bootstrap_error,
                  decision=decision, elapsed_seconds=time.perf_counter()-start,
                  scope='Separated SOURCE only; direct centered pairs; three bootstrap draws; '
                        'saved full2000 quantiles; no root import, refit, raw or dev access')
    (OUT/'AUDIT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
