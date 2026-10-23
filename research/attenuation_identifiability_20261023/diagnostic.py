"""Exact Jensen-contrast and normalized-domain audit on already exposed aggregates."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/attenuation_identifiability'
OLD = ROOT / 'log/20261023/mixed_feedback_estimator'
PREVIOUS = ROOT / 'log/20261023/reusable_error_mechanism'


def toy():
    baseline = np.array([[1000., 9000.]])
    single = np.array([[3000., 7000.]])
    doubles = {'homogeneous': np.array([[5000., 5000.]]),
               'heterogeneous': np.array([[1000., 9000.], [9000., 1000.]])}
    output = []
    for name, double in doubles.items():
        for arr in [baseline, single, double]:
            np.testing.assert_array_equal(arr.sum(axis=1), 10000.)
        m = double.mean(axis=0) - 2 * single.mean(axis=0) + baseline.mean(axis=0)
        np.testing.assert_array_equal(m, 0.)
        mixed = np.log1p(double).mean(axis=0) - 2 * np.log1p(single).mean(axis=0) + np.log1p(baseline).mean(axis=0)
        g = -2 * (np.log1p(single).mean(axis=0) - np.log1p(baseline).mean(axis=0))
        output.append(dict(name=name, normalized_mean_CP_mixed=m.tolist(), mean_log_mixed=mixed.tolist(),
                           descriptive_projection=float(np.dot(g, mixed) / np.dot(g, g))))
    assert output[0]['mean_log_mixed'] != output[1]['mean_log_mixed']
    return output


def main():
    assert not (OUT / 'STARTED.json').exists(), 'Inspect existing run instead of silent retry'
    freeze = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    constructed = toy()
    (OUT / 'STARTED.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat())), encoding='utf-8')
    started = time.perf_counter()
    data = np.load(OLD / 'STATE_BY_GEM.npz', allow_pickle=False)
    previous = np.load(PREVIOUS / 'OVERLAP_ARRAYS.npz', allow_pickle=False)
    fixed = np.load(PREVIOUS / 'ATTENUATION_ARRAYS.npz', allow_pickle=False)
    pairs = previous['pairs'].tolist()
    assert len(pairs) == 73 and len(data['genes']) == 103
    lookup = {(str(n), int(g)): i for i, (n, g) in enumerate(zip(data['group_names'], data['gems']))}
    m, ell = data['mean_CP10K'], data['mean_log1pCP10K']
    assert np.isfinite(m).all() and np.isfinite(ell).all()
    assert m.min() >= 0 and m.max() <= 10000. + 1e-10
    assert np.all(m.sum(axis=1) <= 10000. + 1e-10)
    ll = np.log1p(m)
    jensen = ll - ell
    assert jensen.min() >= -1e-12
    contrasts = {name: [] for name in ['ell', 'logmean', 'jensen']}
    cf = []
    for pair in pairs:
        a, b = pair.split('|')
        rows = {name: [] for name in contrasts}
        cf_rows = []
        for gem in range(1, 9):
            ii = [lookup[(name, gem)] for name in [pair, a, b, 'CONTROL']]
            for name, arr in [('ell', ell), ('logmean', ll), ('jensen', jensen)]:
                rows[name].append(arr[ii[0]] - arr[ii[1]] - arr[ii[2]] + arr[ii[3]])
            cf_rows.append(m[ii[1]] + m[ii[2]] - m[ii[3]])
        for name in contrasts:
            contrasts[name].append(rows[name])
        cf.append(cf_rows)
    contrasts = {name: np.asarray(arr) for name, arr in contrasts.items()}
    cf = np.asarray(cf)
    identity_error = float(np.max(np.abs(contrasts['ell'] - contrasts['logmean'] + contrasts['jensen'])))
    assert identity_error < 1e-12
    saved = dict(pairs=np.array(pairs), genes=data['genes'], normalized_mean_cf=cf, **contrasts)
    reports = []
    for direction, gems in [('A_to_B', [4, 5, 6, 7]), ('B_to_A', [0, 1, 2, 3])]:
        r, lo, jj = [contrasts[name][:, gems, :].mean(axis=1) for name in ['ell', 'logmean', 'jensen']]
        truth = previous[direction + '__truth']
        truth_error = float(np.max(np.abs(r - truth)))
        assert truth_error < 1e-12
        g = fixed[direction + '__g']
        denominator = np.sum(g * g)
        numerators = [float(np.sum(g * v)) for v in [r, lo, jj]]
        qr, ql, qj = [v / denominator if denominator else None for v in numerators]
        projection_error = abs(qr - ql + qj) if denominator else None
        energy = dict(mean_r2=float(np.mean(r * r)), mean_logmean2=float(np.mean(lo * lo)),
                      mean_jensen2=float(np.mean(jj * jj)), minus_twice_cross=float(-2 * np.mean(lo * jj)))
        energy_error = abs(energy['mean_r2'] - energy['mean_logmean2'] - energy['mean_jensen2'] - energy['minus_twice_cross'])
        assert (projection_error is None or projection_error < 1e-12) and energy_error < 1e-12
        reports.append(dict(direction=direction, truth_reconstruction_max_abs=truth_error,
                            signed_projection=dict(observed=qr, logmean=ql, mixed_J=qj,
                                                   signed_numerators=numerators, denominator=float(denominator),
                                                   identity_max_abs=projection_error), energy=energy, energy_identity_abs=energy_error))
        saved[direction + '__g'] = g
    invalid = (cf < 0) | (cf > 10000.)
    domain = dict(coordinates=int(cf.size), pair_gems=int(cf.shape[0] * cf.shape[1]),
                  negative=int(np.sum(cf < 0)), log_math_invalid_le_minus_one=int(np.sum(cf <= -1)),
                  above_10000=int(np.sum(cf > 10000.)),
                  selected_sum_above_10000=int(np.sum(cf.sum(axis=2) > 10000.)),
                  pair_gems_with_any_bad_coordinate=int(np.sum(np.any(invalid, axis=2))),
                  complete_103_coordinate_feasibility_not_claimed=True, minimum=float(cf.min()), maximum=float(cf.max()))
    result = dict(status='VERIFIED_ALGEBRA_ONLY_NO_CAUSAL_ATTRIBUTION',
                  per_gem_identity_max_abs=identity_error, group_J_min=float(jensen.min()),
                  directions=reports, normalized_mean_additive_domain=domain, synthetic_constructed=constructed,
                  seconds=time.perf_counter() - started, model_fit_calls=0, biological_function_reads=0,
                  raw_matrix_reads=0, scope='Retrospective exposed normalized state; J is not noise and projections are not causal shares')
    np.savez_compressed(OUT / 'DECOMPOSITION.npz', **saved)
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
