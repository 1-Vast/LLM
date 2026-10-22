"""Exact synthetic checks of the sole API candidate; no biological data input."""
from fractions import Fraction as F
from pathlib import Path
import json

checks = []

# Nonzero probability cannot identify the signed mean.
q = F(3, 4)
positive = {1: q, 0: 1-q, -1: F(0)}
negative = {1: F(0), 0: 1-q, -1: q}
nonzero = lambda p: p[1] + p[-1]
mean = lambda p: p[1] - p[-1]
assert nonzero(positive) == nonzero(negative) == q
assert mean(positive) == -mean(negative) == q
checks.append(dict(name='same_nonzero_probability_opposite_signed_mean', passed=True,
                   q=str(q), means=[str(mean(positive)), str(mean(negative))]))

# One shared nuisance correction preserves all pairwise score differences.
scores = [F(1, 2), F(-1, 3), F(1, 5)]
correction = F(7, 10)
adjusted = [s-correction for s in scores]
assert all(adjusted[i]-adjusted[j] == scores[i]-scores[j]
           for i in range(len(scores)) for j in range(len(scores)))
assert sorted(range(len(scores)), key=scores.__getitem__) == sorted(range(len(scores)), key=adjusted.__getitem__)
checks.append(dict(name='shared_subtraction_preserves_pairwise_differences_and_order', passed=True))

# A single-well construction with identical reference controls, not source means.
m0, t0 = F(10), F(100)
def endpoints(m, t):
    return 1-m/m0, 1-(m/t)/(m0/t0)

examples = [(F(9), F(10)), (F(1), F(110))]
for m, t in examples:
    rcn, rcf = endpoints(m, t)
    assert rcn-rcf == (m/m0)*(t0/t-1)
checks.append(dict(name='single_well_disagreement_identity', passed=True,
                   scope='Identical controls only; does not invert source averaged ratios'))
a, b = [endpoints(*e) for e in examples]
assert a[0]-a[1] > 0 > b[0]-b[1]
assert a[0] < b[0] and a[1] < b[1]
assert not (a[0] > 0 and a[1] > 0) and b[0] > 0 and b[1] > 0
checks.append(dict(name='positive_disagreement_can_rank_pareto_dominated_action_above_joint_positive_action',
                   passed=True, action_a=list(map(str,a)), action_b=list(map(str,b))))

out = Path(__file__).resolve().parents[2] / 'log/20261022/mse_mechanism_renewal/ALGEBRA_RESULT.json'
with out.open('x', encoding='utf-8') as f:
    json.dump(dict(scope='Exact synthetic arithmetic; no empirical biology or average gain claim',
                   biological_data_reads=0, checks=checks), f, indent=2)
print(json.dumps(dict(status='PASS', checks=len(checks), biological_data_reads=0)))
