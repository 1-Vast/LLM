"""Independent Fraction enumeration; no root allocation module import/run."""
from fractions import Fraction as Q
from pathlib import Path
from statistics import NormalDist
import hashlib
import json
import math

root = Path('D:/MAESTRO')
out = root / 'log/20261023/dose_update_qualification'
freeze = json.loads((out/'ALLOCATION_FREEZE.json').read_text(encoding='utf-8-sig'))
hashes = {p: hashlib.sha256((root/p).read_bytes()).hexdigest() == digest
          for p, digest in freeze['files'].items()}
assert all(hashes.values())
stored = json.loads((out/'ALLOCATION_RESULT.json').read_text())
allocs = [(na, nb, 30-na-nb) for na in range(1,29) for nb in range(1,30-na)]
assert len(allocs) == 406
cases = {}
total_cov_checks = 0
for name, ga, gb in [('equal', Q(1), Q(1)), ('opposite', Q(1), Q(-1))]:
    exacts = []
    proxies = []
    for alloc in allocs:
        na, nb, nc = alloc
        # Independent quadratic-form summation with h=(ga,-gb).
        cov = [[Q(1,na)+Q(1,nc), Q(1,nc)],
               [Q(1,nc), Q(1,nb)+Q(1,nc)]]
        h = [ga, -gb]
        exact = sum(h[i]*cov[i][j]*h[j] for i in range(2) for j in range(2))
        expansion = ga**2/na + gb**2/nb + (ga-gb)**2/nc
        assert exact == expansion
        total_cov_checks += 1
        proxy = sum(h[i]**2*cov[i][i] for i in range(2))
        exacts.append((exact, alloc))
        proxies.append((proxy, alloc))
    exact_risk, best_alloc = min(exacts)
    _, proxy_alloc = min(proxies)
    proxy_true = dict((a,v) for v,a in exacts)[proxy_alloc]
    expected = {
        'gradients': [str(ga),str(gb)], 'exact_design': list(best_alloc),
        'marginal_proxy_design': list(proxy_alloc), 'exact_risk': str(exact_risk),
        'proxy_true_risk': str(proxy_true),
        'control_variance_coefficient': str((ga-gb)**2),
        'ordinary_c_optimal_equals_exact': True,
    }
    agreement = {k: stored['cases'][name][k] == v for k,v in expected.items()}
    assert all(agreement.values())
    # Independent NormalDist CDF form, rather than root's erfc expression.
    rank_errors = [NormalDist().cdf(-0.5/math.sqrt(float(v))) for v in (exact_risk,proxy_true)]
    errors = [abs(rank_errors[i]-stored['cases'][name][key]) for i,key in enumerate(
        ['exact_gaussian_rank_error','proxy_gaussian_rank_error'])]
    assert max(errors) < 1e-15
    cases[name] = {'reconstructed': expected, 'agreement': agreement,
                   'cdf_rank_errors': rank_errors, 'rank_abs_discrepancies': errors}
assert total_cov_checks == 812
result = {'scope': 'ordinary exact linear-Gaussian design arithmetic, not biology or novelty',
          'root_code_imported_or_run': False, 'freeze_hashes': hashes,
          'allocations_per_case': len(allocs), 'covariance_checks': total_cov_checks,
          'cases': cases}
(out/'critic_allocation_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'freeze_matches': len(hashes), 'covariance_checks': total_cov_checks,
                  'cases': cases}, indent=2))
