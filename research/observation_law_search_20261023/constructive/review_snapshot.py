"""Independent saved-result audit using real expm and adaptive quadrature."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad, quad_vec
from scipy.linalg import expm

base = Path('log/20261023/observation_law_search')
saved = json.loads((base / 'SNAPSHOT_WITNESS.json').read_text())
frozen = json.loads((base / 'ROOT_FREEZE.json').read_text())
hash_checks = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
               for p, h in frozen['files'].items()}
assert all(hash_checks.values())
rows = []
for world in saved['autonomous']:
    K = np.array([[-.25, -world['omega']], [world['omega'], -.25]])
    E = expm(K)
    cov_noise, cov_error = quad_vec(lambda t: .2 * expm(K*t) @ expm(K.T*t), 0, 1)
    covariance = E @ E.T + cov_noise
    for name, result in world['actions'].items():
        mean, error = quad_vec(lambda t: expm(K*t) @ np.array(result['force']), 0, 1)
        sd = np.sqrt(covariance[0, 0])
        burden, tail_error = quad(lambda x: np.exp(-.5*((x-mean[0])/sd)**2) / (sd*np.sqrt(2*np.pi)), 0, np.inf, epsabs=1e-12)
        burden *= np.exp(.1)
        discrepancy = max(np.max(np.abs(mean-result['analytic_mean_T'])), np.max(np.abs(covariance-world['covariance_T'])), abs(burden-result['absolute_tail_harm']))
        assert discrepancy < 1e-10
        rows.append({'omega': world['omega'], 'action': name, 'mean': mean.tolist(),
                     'covariance': covariance.tolist(), 'burden': burden,
                     'max_discrepancy': float(discrepancy), 'mean_quad_bound': float(error),
                     'cov_quad_bound': float(cov_error), 'tail_quad_bound': tail_error})
temporal = []
for result in saved['time_dependent']:
    diffusion = result['diffusivity']
    shift, error = quad(lambda t: -np.exp(-diffusion*t), 0, 1)
    assert abs(shift-result['analytic_shift']) < 1e-12
    temporal.append({'diffusivity': diffusion, 'shift': shift, 'error': error})
assert rows[0]['burden'] > rows[1]['burden']
assert rows[2]['burden'] < rows[3]['burden']
output = {'status': 'PASS_SAVED_MATH_ONLY', 'root_freeze_checks': hash_checks,
          'autonomous': rows, 'time_dependent': temporal,
          'original_script_executions': 0, 'biological_values_read': 0,
          'method': 'Real matrix exponential adaptive quadrature; direct Gaussian density tail integral. No root complex-integral or solve_ivp reuse.'}
(base / 'constructive/RESULT_NUMERIC.json').write_text(json.dumps(output, indent=2))
print(json.dumps(output, indent=2))
