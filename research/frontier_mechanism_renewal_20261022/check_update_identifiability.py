"""Exact algebraic counterexamples, not biological performance experiments."""
from fractions import Fraction as F
from pathlib import Path
import json

out = Path('D:/MAESTRO/log/20261022/frontier_mechanism_renewal')
rows = []

# Both environments expose the same support (x=1,y=1), same initial theta=0,
# same residual +1 and same update theta'=1. Their unseen query outcomes differ.
for query_y in [F(1), F(-1)]:
    before = query_y**2 / 2
    after = (query_y - 1)**2 / 2
    gain = before - after
    identity = query_y * 1 - F(1, 2)
    assert gain == identity
    rows.append(dict(query_y=str(query_y), support_residual='1', support_loss_after='0', query_gain=str(gain)))
assert rows[0]['query_gain'] == '1/2'
assert rows[1]['query_gain'] == '-3/2'

# A noisy-label alternative also has the identical observed support residual.
# A scalar residual alone cannot distinguish stable signal from transient noise.
# This is a logical nonidentification example, not a probabilistic impossibility.
checks = dict(exact_quadratic_gain_both_worlds=True,
              same_observed_support_and_update=True,
              opposite_query_gain_signs=True,
              fit_support_perfectly_in_both_worlds=True)
result = dict(scope='EXACT_MATHEMATICS_ONLY; no biological values or fits',
              checks=checks, examples=rows,
              limitation='Does not rule out population-level information in residual histories or gain prediction from additional task structure.')
(out / 'ALGEBRA_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
