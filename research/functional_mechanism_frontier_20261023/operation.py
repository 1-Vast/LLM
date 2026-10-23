"""Four exact rational scope checks; no peer/author implementation imported."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_mechanism_frontier'


def dot(a, b):
    return sum((x * y for x, y in zip(a, b)), F(0))


def main():
    assert not (OUT / 'OPERATION_RESULT.json').exists()
    paths = [Path(__file__), OUT / 'OPERATION_PROTOCOL.md', OUT / 'constructive/alphaedit.body',
             OUT / 'constructive/INDEPENDENT.md']
    record = dict(utc=datetime.now(timezone.utc).isoformat(),
                  files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (OUT / 'OPERATION_FREEZE.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    zero = F(0)
    fullspan_output, fullspan_target = zero, F(1)
    assert (fullspan_output - fullspan_target) ** 2 == 1
    w, e, old, shifted = [zero, F(1)], [zero, F(1)], [F(1), zero], [F(1), F(1, 10)]
    assert dot(e, old) == 0
    before, after, competitor = dot(w, shifted), dot([w[i] + e[i] for i in range(2)], shifted), F(3, 20)
    assert before < competitor < after
    delta = F(1, 3)
    assert 2 * (delta - 1) + 2 * delta + 2 * delta == 0
    assert delta != 0
    key, covariance, threshold = F(1, 20), F(1, 400), F(1, 100)
    assert key * key == covariance < threshold and key != 0
    result = dict(status='PASS_LITERAL_TRANSFER_BOUNDARIES',
                  fullspan=dict(projector='zero', permitted_edit='zero', remaining_squared_error='1'),
                  drift=dict(fixed_key_change='0', before=str(before), after=str(after), competitor=str(competitor), rank_flips=True),
                  soft_previous=dict(unique_minimizer=str(delta), old_previous_change=str(delta), hessian='6'),
                  approximate_null=dict(covariance=str(covariance), threshold=str(threshold), output_drift=str(key)),
                  scope='Stipulated exact operation cases, not biological validation or a counterexample to source assumptions',
                  model_fits=0, biological_outcomes_read=0)
    (OUT / 'OPERATION_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
