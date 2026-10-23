import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path

folder = Path('log/20261023/feedback_sufficiency_renewal')
result_path = folder / 'root/SIGN_COLLISION_RESULT.json'
saved = json.loads(result_path.read_text(encoding='utf-8-sig'))

def scalar_descent(label, rate, steps):
    parameter = Q(0)
    path = [parameter]
    losses = []
    for _ in range(steps):
        error = parameter - label
        losses.append(abs(error))
        gradient = Q((error > 0) - (error < 0))
        parameter -= rate * gradient
        path.append(parameter)
    return path, losses

def render(values):
    if isinstance(values, list):
        return [render(value) for value in values]
    return str(values)

labels = [Q(1), Q(2)]
runs = [scalar_descent(label, Q(1, 4), 2) for label in labels]
targets = [2 * label for label in labels]
predictions = [2 * path[-1] for path, _ in runs]
risk = sum((pred - target) ** 2 for pred, target in zip(predictions, targets)) / 2
shared = sum(targets) / 2
shared_risk = sum((shared - target) ** 2 for target in targets) / 2
direct = [2 * label for label in labels]
direct_risk = sum((pred - target) ** 2 for pred, target in zip(direct, targets)) / 2
breakers = [scalar_descent(label, Q(3, 4), 3)[0] for label in labels]
expected = {
    'labels': render(labels),
    'paths': render([path for path, _ in runs]),
    'losses': render([losses for _, losses in runs]),
    'targets': render(targets),
    'mae_predictions': render(predictions),
    'mae_mse': str(risk),
    'shared_best': str(shared),
    'shared_minimum_mse': str(shared_risk),
    'ordinary_direct_predictions': render(direct),
    'ordinary_direct_mse': str(direct_risk),
    'breaker_paths': render(breakers),
}
checks = {key: saved[key] == value for key, value in expected.items()}
output = {
    'scope': 'Independent Fraction arithmetic only; no source script import or biological performance',
    'source_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
    'independent_values': expected,
    'saved_fields_match': checks,
    'shared_optimality': 'risk(z) = (z - 3)^2 + 1 for the two stipulated equally weighted query targets',
    'all_pass': all(checks.values()),
}
target = folder / 'constructive/SIGN_RESULT_AUDIT.json'
if target.exists():
    raise FileExistsError(target)
target.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
assert output['all_pass']
print(json.dumps({'all_pass': output['all_pass'], 'compared_fields': len(checks)}))
