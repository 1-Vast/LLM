"""Independent exact arithmetic; no root implementation imports or biological data."""
import json
from fractions import Fraction as F
from pathlib import Path

out = Path('log/20261023/feedback_law_discovery/constructive')
root_result = json.loads(Path('log/20261023/feedback_law_discovery/API_CHECK_RESULT.json').read_text())
rows = []
for n in (1, 10, 100):
    psi = F(n, n + 1)
    t = 1 - psi
    phi = n * t / (n * t * t + 1)
    prediction = phi * t
    ridge = F(n, n + 1)
    row = dict(n=n, psi=str(psi), residual_feature=str(t), phi=str(phi),
               prediction=str(prediction), squared_error=str((1-prediction)**2),
               raw_ridge_prediction=str(ridge), raw_ridge_squared_error=str((1-ridge)**2),
               copied_predictor_identical=(phi*t == prediction))
    assert row == next(r for r in root_result['rows'] if r['n'] == n)
    rows.append(row)

# Polynomial coefficient arrays in h,a,b for U(h,y)=(1-eta)h+eta*y.
checks = []
for eta in (F(0), F(1,4), F(1,2), F(1)):
    h, a, b = F(2,3), F(-1,5), F(7,8)
    update = lambda z,y: (1-eta)*z + eta*y
    ab, ba = update(update(h,a),b), update(update(h,b),a)
    union = h - eta*((h-a)+(h-b))
    assert ab-ba == eta**2*(b-a)
    assert ab-union == eta**2*(h-a)
    checks.append(dict(eta=str(eta), comm=str(ab-ba), partition=str(ab-union)))

result = dict(status='PASS_INDEPENDENT_RATIONAL_RECONSTRUCTION', api_rows=rows,
              updater_formula_witnesses=checks,
              scope='Constructed arithmetic only; no biological fit, root code import, or general performance claim')
target = out/'CROSS_ARITHMETIC.json'
target.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
