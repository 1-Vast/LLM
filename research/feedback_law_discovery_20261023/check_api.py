"""Exact scalar audit of the literal retained formula, not a biological experiment."""
from fractions import Fraction as F
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/feedback_law_discovery'


def main():
    rows = []
    for n in (1, 10, 100):
        psi = F(n, n+1)
        t = 1-psi
        phi = n*t/(n*t*t+1)
        prediction = phi*t
        direct = F(n, n+1)
        copied_weight = phi*(1-psi)
        assert prediction == F(n, n*n+3*n+1)
        assert copied_weight == prediction
        assert (1-prediction)**2 > (1-direct)**2
        rows.append(dict(n=n, psi=str(psi), residual_feature=str(t), phi=str(phi),
                         prediction=str(prediction), squared_error=str((1-prediction)**2),
                         raw_ridge_prediction=str(direct), raw_ridge_squared_error=str((1-direct)**2),
                         copied_predictor_identical=True))
    result = dict(status='PASS_LITERAL_FORMULA_AND_SCOPE_CHECK', rows=rows,
                  scope='Exact constructed scalar cases; no biological estimates or new updater performance',
                  conclusion='Copying the fitted residual predictor reproduces the alleged inheritance contrast',
                  biological_fits=0, source_implementations_executed=0)
    (OUT/'API_CHECK_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
