"""Exact toy capacity ambiguity; no biological files, fitting or randomness."""
from fractions import Fraction as F
from pathlib import Path
import json


def loss(capacity, attenuation):
    return min(capacity) - min(c * a for c, a in zip(capacity, attenuation))


worlds = [(F(1), F(1)), (F(1), F(2))]
support = (F(1, 2), F(1))
query = (F(1), F(1, 2))
rows = []
for capacity in worlds:
    rows.append({
        "capacity": [str(c) for c in capacity],
        "control": str(min(capacity)),
        "support_loss": str(loss(capacity, support)),
        "query_loss": str(loss(capacity, query)),
    })
query_values = [loss(c, query) for c in worlds]
unresolved_posterior_mean = sum(query_values) / len(worlds)
unresolved_mse = sum((y - unresolved_posterior_mean) ** 2 for y in query_values) / len(worlds)
# Positive prerequisite: one legal state feature measures c2 without error.
# A same-information ordinary discrete EB prior uses that feature identically.
resolved_eb = {str(c[1]): loss(c, query) for c in worlds}
resolved_mse = sum((loss(c, query) - resolved_eb[str(c[1])]) ** 2 for c in worlds) / len(worlds)
result = {
    "scope": "Exact synthetic arithmetic only; no biological utility or algorithm advantage",
    "rows": rows,
    "unresolved_equal_prior_prediction": str(unresolved_posterior_mean),
    "unresolved_bayes_mse": str(unresolved_mse),
    "resolved_state_feature": "c2 measured exactly and provided equally to every method",
    "resolved_ordinary_eb_query_predictions": {k: str(v) for k, v in resolved_eb.items()},
    "resolved_ordinary_eb_mse": str(resolved_mse),
}
out = Path("log/20261023/functional_update_operation/constructive/CAPACITY_EXACT_RESULT.json")
assert not out.exists(), "Preserve original result; do not overwrite"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
