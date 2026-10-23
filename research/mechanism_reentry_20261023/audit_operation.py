"""Independently reconstruct the peer's exact limited target-field example."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/mechanism_reentry'
source = OUT/'critic/TARGET_FIELD_CHECK.json'
claim = json.loads(source.read_text(encoding='utf-8'))
matrix = ((F(1), F(1)), (F(-1), F(1)))  # I-J for T=(-y,x)
assert matrix[0][1] != matrix[1][0]
checks = []
for point in [(0, 0), (1, 0), (0, 1), (2, -3)]:
    x = tuple(map(F, point))
    target = (-x[1], x[0])
    residual = tuple(xi-ti for xi, ti in zip(x, target))
    conventional = tuple(sum(a*b for a, b in zip(row, x)) for row in matrix)
    assert residual == conventional
    for step in [F(1, 10), F(1, 4)]:
        detached = tuple(a-step*b for a, b in zip(x, residual))
        vector_update = tuple(a-step*b for a, b in zip(x, conventional))
        assert detached == vector_update
        checks.append(dict(point=point, step=str(step), exact_match=True))
assert claim['cross_partials'] == dict(d_gx_d_y=1, d_gy_d_x=-1)
result = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              cross_partials_match=True, static_C2_potential_excluded_on_open_set=True,
              ordinary_detached_target_and_vector_update_exact_match=True, checks=checks,
              scope='Independent exact reconstruction after reading peer claim; not a prospective biological experiment.',
              author_code_executed=False, biological_labels_read=False,
              limitations='Squared-error analytic example, not a numerical replication of categorical DiscoRL or discovery performance.')
(OUT/'ROOT_OPERATION_AUDIT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
