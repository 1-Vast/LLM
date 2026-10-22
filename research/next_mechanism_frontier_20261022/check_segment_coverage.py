"""Exact fixed fixture plus source Eq13-16 score; not a biological fit."""
import datetime
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/next_mechanism/frontier'

def fisher(rows):
    return [[sum(row[i] * row[j] for row in rows) for j in range(2)] for i in range(2)]

def add(a, b):
    return [[a[i][j] + b[i][j] for j in range(2)] for i in range(2)]

def det(a):
    return a[0][0] * a[1][1] - a[0][1] * a[1][0]

def inverse(a):
    d = det(a)
    return [[a[1][1] / d, -a[0][1] / d], [-a[1][0] / d, a[0][0] / d]]

def trace(a):
    return a[0][0] + a[1][1]

def score(segments, alphas, regularization):
    coverage = []
    for i in range(2):
        j = 1 - i
        values = []
        for f in segments:
            schur = f[i][i] - f[i][j] * f[j][i] / (f[j][j] + regularization)
            values.append(float(schur) / float(f[i][i]) ** alphas[i])
        coverage.append(max(values))
    return {'coverage': coverage, 'objective': sum(math.log(c + 1e-6) for c in coverage)}

def encode(value):
    if isinstance(value, Q):
        return str(value)
    raise TypeError(type(value).__name__)

def main():
    plan_a = [[(Q(3,5),Q(4,5)),(Q(4,5),Q(3,5))],[(Q(3,5),Q(-4,5)),(Q(4,5),Q(-3,5))]]
    plan_b = [[(Q(7,5),Q(0)),(Q(0),Q(1,5))]] * 2
    plans = {'A': plan_a, 'B': plan_b}
    results = {}
    for name, rows_by_segment in plans.items():
        fs = [fisher(rows) for rows in rows_by_segment]
        pooled = add(*fs)
        covariance = inverse(pooled)
        contrast_var = covariance[0][0] + covariance[1][1] - 2 * covariance[0][1]
        results[name] = {
            'rows': rows_by_segment, 'scalar_readouts': sum(map(len, rows_by_segment)),
            'segment_fisher': fs, 'segment_trace': [trace(f) for f in fs],
            'segment_determinant': [det(f) for f in fs],
            'pooled_fisher': pooled, 'total_squared_sensitivity': trace(pooled),
            'covariance': covariance, 'parameter_mse': trace(covariance),
            'terminal_contrast_variance': contrast_var,
            'gaussian_sign_error_at_contrast_one': .5 * math.erfc(1 / math.sqrt(2 * float(contrast_var))),
        }
    a, b = results['A'], results['B']
    checks = {
        'equal_four_readouts': a['scalar_readouts'] == b['scalar_readouts'] == 4,
        'equal_total_squared_sensitivity': a['total_squared_sensitivity'] == b['total_squared_sensitivity'] == 4,
        'equal_segment_spectra_trace': a['segment_trace'] == b['segment_trace'] == [2,2],
        'equal_segment_spectra_determinant': a['segment_determinant'] == b['segment_determinant'] == [Q(49,625)]*2,
        'all_segments_positive_definite': all(f[0][0] > 0 and det(f) > 0 for v in results.values() for f in v['segment_fisher']),
        'common_row_norm_ceiling': all(sum(h*h for h in row) <= Q(49,25) for segments in plans.values() for rows in segments for row in rows),
        'pooled_A_exact_identity': a['pooled_fisher'] == [[2,0],[0,2]],
        'pooled_B_exact_diagonal': b['pooled_fisher'] == [[Q(98,25),0],[0,Q(2,25)]],
        'A_MSE_one': a['parameter_mse'] == 1,
        'B_MSE_625_over49': b['parameter_mse'] == Q(625,49),
        'pooled_A_optimal_selects_A': a['parameter_mse'] < b['parameter_mse'],
        'pooled_D_optimal_selects_A': det(a['pooled_fisher']) > det(b['pooled_fisher']),
        'pooled_E_optimal_selects_A': 2 > Q(2,25),
        'terminal_contrast_variance_favors_A': a['terminal_contrast_variance'] == 1 < b['terminal_contrast_variance'],
        'terminal_sign_error_favors_A': a['gaussian_sign_error_at_contrast_one'] < b['gaussian_sign_error_at_contrast_one'],
    }
    settings = [(x,x) for x in (0,.7,.85,1)] + [(x,y) for x in (.7,1) for y in (.7,1) if x != y]
    scores = []
    for alphas in settings:
        for reg in (Q(0), Q(1,1000000)):
            sa = score(a['segment_fisher'], alphas, reg)
            sb = score(b['segment_fisher'], alphas, reg)
            row = {'alphas': alphas, 'regularization': reg, 'A': sa, 'B': sb, 'chosen': 'B' if sb['objective'] > sa['objective'] else 'A'}
            checks[f'source_prefers_B_alpha{alphas}_reg{reg}'] = row['chosen'] == 'B'
            scores.append(row)
    protocol = OUT / 'MINIMAL_FALSIFICATION_PROTOCOL.md'
    output = {
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'git_head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        'python': platform.python_version(), 'randomness': 'none; analytical exact moments and normal CDF',
        'protocol_sha256': hashlib.sha256(protocol.read_bytes()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plans': results, 'source_scores': scores, 'checks': checks,
        'all_pass': all(checks.values()), 'check_count': len(checks),
        'decision': 'STOP_LITERAL_IDTD_DRUG_TRANSPLANT; joint pooling already solves this fixture',
        'biological_data_opened': False, 'model_api_calls': 0,
    }
    (OUT / 'RESULT.json').write_text(json.dumps(output, indent=2, default=encode), encoding='utf-8')
    print(json.dumps({'all_pass': output['all_pass'], 'checks': len(checks), 'A_MSE':a['parameter_mse'], 'B_MSE':b['parameter_mse'], 'A_sign_error':a['gaussian_sign_error_at_contrast_one'], 'B_sign_error':b['gaussian_sign_error_at_contrast_one']}, default=encode))
    if not output['all_pass']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
