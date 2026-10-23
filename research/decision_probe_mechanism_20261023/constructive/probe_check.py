from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json

worlds = list(product([0, 1], repeat=2))
probes = [lambda d, n: n, lambda d, n: d ^ n]


def risk(chosen):
    groups = {}
    for d, n in worlds:
        outcome = tuple(probes[q](d, n) for q in chosen)
        counts = groups.setdefault(outcome, [0, 0])
        counts[d] += 1
    return sum((F(min(counts), 4) for counts in groups.values()), F(0))


subsets = [(), (0,), (1,), (0, 1)]
risks = [risk(s) for s in subsets]
assert risks == [F(1, 2), F(1, 2), F(1, 2), F(0)]
costs = [r + F(len(s), 8) for r, s in zip(risks, subsets)]
assert costs == [F(1, 2), F(5, 8), F(5, 8), F(1, 4)]
marginals = {}
for d, q, y in product([0, 1], repeat=3):
    marginals[d, q, y] = sum(F(probes[q](d, n) == y, 2) for n in [0, 1])
assert all(p == F(1, 2) for p in marginals.values())
factorized_risk = F(0)
for ys in product([0, 1], repeat=2):
    joint_masses = [F(1, 2) * marginals[d, 0, ys[0]] * marginals[d, 1, ys[1]] for d in [0, 1]]
    factorized_risk += min(joint_masses)
assert factorized_risk == F(1, 2)
result = dict(kind='stipulated_exact_math_not_biology', subsets=subsets,
              terminal_risks=list(map(str, risks)), objectives=list(map(str, costs)),
              greedy_objective='1/2', full_joint_two_probe_objective='1/4',
              factorized_decision_quotient_pair_risk=str(factorized_risk))
out = Path('D:/MAESTRO/log/20261023/decision_probe_mechanism/constructive/OPERATION_RESULT.json')
assert not out.exists()
out.write_text(json.dumps(result, indent=2))
print(json.dumps(result))
