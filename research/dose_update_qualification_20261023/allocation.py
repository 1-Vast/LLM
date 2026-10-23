"""Exact correlated-control acquisition diagnostic; no biological validation."""
from fractions import Fraction as F
import hashlib
import json
from math import erfc, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification'


def variance(n, a, b):
    x, y, z = map(F, n)
    return a*a/x + b*b/y + (a-b)**2/z


def marginal(n, a, b):
    x, y, z = map(F, n)
    return a*a/x + b*b/y + (a*a+b*b)/z


if __name__ == '__main__':
    assert not (OUT / 'ALLOCATION_RESULT.json').exists()
    frozen = json.loads((OUT / 'ALLOCATION_FREEZE.json').read_text())
    for name, expected in frozen['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    allocations = [(x, y, 30-x-y) for x in range(1, 29) for y in range(1, 30-x)]
    assert len(allocations) == 406
    cases = {}
    for name, a, b in [('equal', F(1), F(1)), ('opposite', F(1), F(-1))]:
        for n in allocations:
            x, y, z = map(F, n)
            matrix_risk = a*a*(1/x+1/z) + b*b*(1/y+1/z) - 2*a*b/z
            assert variance(n, a, b) == matrix_risk
        exact = min(allocations, key=lambda n: (variance(n, a, b), n))
        proxy = min(allocations, key=lambda n: (marginal(n, a, b), n))
        exact_risk, proxy_risk = variance(exact, a, b), variance(proxy, a, b)
        cases[name] = dict(gradients=[str(a), str(b)],
            exact_design=exact, marginal_proxy_design=proxy,
            exact_risk=str(exact_risk), proxy_true_risk=str(proxy_risk),
            control_variance_coefficient=str((a-b)**2),
            ordinary_c_optimal_equals_exact=True,
            exact_gaussian_rank_error=.5*erfc(.5/sqrt(2*float(exact_risk))),
            proxy_gaussian_rank_error=.5*erfc(.5/sqrt(2*float(proxy_risk))))
    assert F(cases['equal']['proxy_true_risk']) > F(cases['equal']['exact_risk'])
    assert cases['equal']['control_variance_coefficient'] == '0'
    assert cases['opposite']['control_variance_coefficient'] == '4'
    result = dict(scope='stipulated Gaussian linear contrast; no biology or new algorithm',
        allocations_per_case=len(allocations), covariance_checks=2*len(allocations), cases=cases)
    (OUT / 'ALLOCATION_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
