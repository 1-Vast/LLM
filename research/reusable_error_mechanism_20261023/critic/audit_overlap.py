"""Independent saved-array and frozen-source audit; never imports root code."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
F = ROOT/'log/20261023/reusable_error_mechanism'
freeze = json.loads((F/'OVERLAP_FREEZE.json').read_text())
bad = [p for p, h in freeze['files'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h]
assert not bad
saved = np.load(F/'OVERLAP_ARRAYS.npz')
old = np.load(ROOT/'log/20261023/mixed_feedback_estimator/OOF_STATE.npz')
state = np.load(ROOT/'log/20261023/mixed_feedback_estimator/STATE_BY_GEM.npz')
report = json.loads((F/'OVERLAP_RESULT.json').read_text())
pairs = saved['pairs'].tolist()
folds = saved['folds']
assert np.array_equal(saved['pairs'], old['pairs'])
expected_folds = np.array([int.from_bytes(hashlib.sha256(('MAESTRO_MIXED_DIAGONAL_V1|'+p).encode()).digest()[:8], 'big') % 5 for p in pairs])
assert np.array_equal(folds, expected_folds) and np.array_equal(folds, old['folds'])
lookup = {(str(n), str(g)): row for n, g, row in zip(state['group_names'], state['gems'], state['mean_log1pCP10K'])}
records = []
fit_checks = 0
for item, inputs, targets in zip(report['directions'], [('1','2','3','4'),('5','6','7','8')], [('5','6','7','8'),('1','2','3','4')]):
    direction = item['direction']
    h, truth = [], []
    for pair in pairs:
        a, b = pair.split('|')
        hg = []
        for gem in inputs:
            sa, sb = lookup[a,gem]-lookup['CONTROL',gem], lookup[b,gem]-lookup['CONTROL',gem]
            hg.append(-1.0*((sa*sb)>0)*np.sign(sa)*np.minimum(abs(sa),abs(sb)))
        h.append(np.mean(hg,axis=0))
        truth.append(np.mean([lookup[pair,g]-lookup[a,g]-lookup[b,g]+lookup['CONTROL',g] for g in targets],axis=0))
    h, truth = np.array(h), np.array(truth)
    assert np.array_equal(h,saved[direction+'__h'])
    source_target_difference = float(np.max(abs(truth-saved[direction+'__truth'])))
    assert source_target_difference < 1e-14
    prefix = 'mean_log1pCP10K__'+direction+'__'
    assert np.max(abs(truth-old[prefix+'truth'])) < 1e-14
    assert np.array_equal(saved[direction+'__direct'],old[prefix+'linear_ridge'])
    prediction = np.zeros_like(truth)
    coefficients = []
    for fold in range(5):
        train, test = folds != fold, folds == fold
        denom = np.sum(h[train]**2)
        theta = float(np.clip(np.sum(h[train]*truth[train])/denom,0,1)) if denom else 0.
        prediction[test] = theta*h[test]
        row = item['folds'][fold]
        assert row['fold']==fold and row['train_pairs']==int(train.sum()) and row['test_pairs']==int(test.sum())
        assert abs(theta-row['theta'])<1e-14
        coefficients.append(theta)
        for key, value in [('MSE',np.mean((prediction[test]-truth[test])**2)),('direct_MSE',np.mean((saved[direction+'__direct'][test]-truth[test])**2))]:
            assert abs(float(value)-row[key])<1e-14
        fit_checks += 1
    assert np.max(abs(prediction-saved[direction+'__prediction'])) < 1e-14
    theta_oracle = float(np.clip(np.sum(h*truth)/np.sum(h*h),0,1))
    assert abs(theta_oracle-item['theta_oracle'])<1e-14
    fit_checks += 1
    scores = {name:float(np.mean((old[prefix+name]-truth)**2)) for name in ['additive','linear_ridge','q_ridge','bilinear_ridge','mean']}
    scores['bounded_overlap'] = float(np.mean((prediction-truth)**2))
    scores['in_sample_global_scalar_oracle'] = float(np.mean((theta_oracle*h-truth)**2))
    for name, value in scores.items():
        assert abs(value-item['scores'][name])<1e-14
    assert abs(float(np.sum(h*truth))-item['pooled_h_dot_r'])<1e-12
    assert abs(float(np.sum(h*h))-item['pooled_h_norm2'])<1e-12
    assert abs(float(np.mean(h!=0))-item['feature_nonzero_fraction'])<1e-14
    records.append({'direction':direction,'scores':scores,'coefficients':coefficients,
                    'oracle':theta_oracle,'relative_direct_improvement':1-scores['bounded_overlap']/scores['linear_ridge'],
                    'source_target_max_abs_difference': source_target_difference,
                    'prediction_max_abs_difference':float(np.max(abs(prediction-saved[direction+'__prediction']))),
                    'winning_folds':sum(x['MSE']<x['direct_MSE'] for x in item['folds'])})
assert fit_checks==12==report['fit_calls']
out={'result':'PASS','freeze_files_checked':len(freeze['files']),'freeze_mismatches':bad,
     'source_features_targets':'features bitwise equal; target/prediction differences explicitly recorded; tolerance 1e-14',
     'coefficients_checked':10,'oracle_coefficients_checked':2,'fit_count_arithmetic':12,
     'scope':'Verifies saved mathematical outputs and count, not unrecorded runtime trace or raw extraction.',
     'directions':records}
(F/'critic/RESULT_AUDIT.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
