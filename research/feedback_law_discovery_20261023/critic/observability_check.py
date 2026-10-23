"""Exact information-limit witness; stipulated linear tasks, not biology."""
from fractions import Fraction as F
from pathlib import Path
import json

tasks = ((F(1), F(0)), (F(0), F(1)))
support, query, diagnostic = (F(1), F(1)), (F(1), F(-1)), (F(1), F(0))
dot = lambda x, w: sum(a*b for a, b in zip(x, w))
minimum_norm = (F(1, 2), F(1, 2))
rows = []
for truth in tasks:
    initial_gradient = tuple(-dot(support, truth)*x for x in support)
    diagnostic_y = dot(diagnostic, truth)
    selected = tasks[0] if diagnostic_y == 1 else tasks[1]
    # Ordinary Bayesian discrimination has the identical likelihood and rule.
    posterior_candidates = [w for w in tasks if dot(diagnostic, w) == diagnostic_y]
    bayes = posterior_candidates[0]
    rows.append(dict(truth=list(map(str, truth)), support_y=str(dot(support, truth)),
                     initial_gradient=list(map(str, initial_gradient)),
                     query_truth=str(dot(query, truth)),
                     minimum_norm_error=str((dot(query, minimum_norm)-dot(query, truth))**2),
                     diagnostic_y=str(diagnostic_y),
                     inherited_rule_error=str((dot(query, selected)-dot(query, truth))**2),
                     ordinary_bayes_error=str((dot(query, bayes)-dot(query, truth))**2)))
assert rows[0]['initial_gradient'] == rows[1]['initial_gradient']
assert all(r['minimum_norm_error'] == '1' for r in rows)
assert all(r['inherited_rule_error'] == r['ordinary_bayes_error'] == '0' for r in rows)
out = Path('log/20261023/feedback_law_discovery/critic/observability_result.json')
out.write_text(json.dumps(dict(rows=rows, support_only_equal_prior_mse_lower_bound='1',
    diagnostic_cost=1, bayes_same_cost_matches=True,
    interpretation='Observability necessity only; no algorithmic advantage or biological result.'), indent=2)+'\n')
print(out.read_text())
