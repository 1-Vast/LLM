"""Exact synthetic algebra only: no fitting and no biological file reads."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import permutations
import hashlib
import json

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/native_operation/proposer'
N = 3
ZERO = tuple(tuple(Q(0) for _ in range(N)) for _ in range(N))
IDENTITY = tuple(tuple(Q(i == j) for j in range(N)) for i in range(N))

def matrix(rows):
    return tuple(tuple(Q(x) for x in row) for row in rows)

def add(a, b):
    return tuple(tuple(a[i][j] + b[i][j] for j in range(N)) for i in range(N))

def scale(a, s):
    return tuple(tuple(s * x for x in row) for row in a)

def mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(N)) for j in range(N)) for i in range(N))

def total(values):
    result = ZERO
    for value in values:
        result = add(result, value)
    return result

def bracket(a, b):
    return add(mul(b, a), scale(mul(a, b), -1))

def exp_series(a):
    a2 = mul(a, a)
    return (IDENTITY, a, scale(a2, Q(1, 2)), scale(mul(a2, a), Q(1, 6)))

def series_product(a, b):
    return tuple(total(mul(a[k], b[n-k]) for k in range(n+1)) for n in range(4))

def schedule(actions, drift):
    result = (IDENTITY, ZERO, ZERO, ZERO)
    for action in actions:
        result = series_product(exp_series(add(drift, action)), result)
    return result

def contrast(a, b, drift):
    terms = [(1, (a, b)), (-1, (b, a)), (-1, (a, ZERO)),
             (1, (ZERO, a)), (-1, (ZERO, b)), (1, (b, ZERO))]
    paths = [(sign, schedule(seq, drift)) for sign, seq in terms]
    return tuple(total(scale(path[n], sign) for sign, path in paths) for n in range(4))

a = matrix([[0, 0, 0], [0, 0, 1], [1, -1, 0]])
b = matrix([[0, 0, 0], [2, 1, 0], [0, 2, -1]])
c = matrix([[0, 0, 0], [-1, 2, -1], [2, 0, 1]])
drift = matrix([[0, 0, 0], [1, -1, 2], [0, 3, -2]])
checks = []

def check(name, condition, **details):
    checks.append(dict(name=name, passed=bool(condition), **details))
    if not condition:
        raise AssertionError(name)

for index in range(12):
    d = add(scale(drift, Q(index-5, 3)), scale(c, Q(index % 3, 2)))
    value = contrast(a, b, d)
    check('drift_cancellation_' + str(index), value[0] == ZERO and value[1] == ZERO and value[2] == bracket(a, b))

value = contrast(a, b, drift)
check('nonzero_action_bracket', value[2] != ZERO)
check('antisymmetry_through_cubic', contrast(b, a, drift) == tuple(scale(x, -1) for x in value))
check('cubic_bias_is_not_zero', value[3] != ZERO,
      interpretation='The stencil is asymptotic, not exact at finite duration.')
check('zero_bracket_self_action', contrast(a, a, drift) == (ZERO, ZERO, ZERO, ZERO))
naive = add(schedule((a, b), drift)[2], scale(schedule((b, a), drift)[2], -1))
check('naive_reverse_order_is_drift_confounded', naive != bracket(a, b))

for index, actions in enumerate(permutations((a, b, c))):
    generators = tuple(add(drift, x) for x in actions)
    generator_sum = total(generators)
    symmetric = scale(mul(generator_sum, generator_sum), Q(1, 2))
    order_features = scale(total(bracket(generators[i], generators[j]) for i in range(3) for j in range(i+1, 3)), Q(1, 2))
    check('ordinary_signature_equivalence_' + str(index),
          add(symmetric, order_features) == schedule(actions, drift)[2])
    decomposed = total(add(add(bracket(actions[i], actions[j]), bracket(drift, actions[j])), bracket(actions[i], drift)) for i in range(3) for j in range(i+1, 3))
    check('measured_background_reconstruction_' + str(index),
          scale(decomposed, Q(1, 2)) == order_features)

seal_path = OUT / 'INITIAL_SEAL.json'
seal = json.loads(seal_path.read_text(encoding='utf-8'))
for record in seal['own_artifacts']:
    p = Path(record['path'])
    check('initial_artifact_unchanged:' + p.name, hashlib.sha256(p.read_bytes()).hexdigest() == record['sha256'])

result = dict(kind='exact_synthetic_algebra_not_biology', checks=checks, passed=all(x['passed'] for x in checks),
              unique_algebra_checks=29, sealed_artifacts_verified=len(seal['own_artifacts']),
              coefficient_h2=[[str(x) for x in row] for row in value[2]],
              coefficient_h3=[[str(x) for x in row] for row in value[3]],
              predictive_fits=0, assay_fields_read=0, biological_success=False,
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              initial_seal_sha256=hashlib.sha256(seal_path.read_bytes()).hexdigest())
with (OUT / 'EXACT_FALSIFIER_RESULT.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result))
