"""Exact stipulated loss/update discriminator, not a cell simulation or fit."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/feedback_sufficiency_renewal/root'


def path(label, steps, rate):
    theta = F(0)
    states, losses = [theta], []
    for _ in range(steps):
        residual = theta - label
        assert residual != 0
        losses.append(abs(residual))
        theta -= rate * (1 if residual > 0 else -1)
        states.append(theta)
    return states, losses


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, list):
        return [encode(x) for x in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


if __name__ == '__main__':
    result_path = OUT / 'SIGN_COLLISION_RESULT.json'
    if result_path.exists():
        raise FileExistsError(result_path)
    frozen = json.loads((OUT / 'SIGN_EXECUTION_FREEZE.json').read_text(encoding='utf-8'))
    for relative, sha in frozen['files'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
    labels = [F(1), F(2)]
    first = [path(y, 2, F(1, 4)) for y in labels]
    prediction = [2 * states[-1] for states, _ in first]
    target = [2 * y for y in labels]
    mae_mse = sum((p-y)**2 for p, y in zip(prediction, target)) / 2
    shared_best = sum(target) / 2
    shared_mse = sum((shared_best-y)**2 for y in target) / 2
    direct = [2 * y for y in labels]
    direct_mse = sum((p-y)**2 for p, y in zip(direct, target)) / 2
    breaker = [path(y, 3, F(3, 4)) for y in labels]
    checks = {
        'original_paths_identical': first[0][0] == first[1][0],
        'original_losses_different': first[0][1] != first[1][1],
        'mae_mse_five': mae_mse == 5,
        'restricted_shared_minimum_one': shared_mse == 1,
        'ordinary_direct_zero': direct_mse == 0,
        'breaker_paths_diverge': breaker[0][0][-1] != breaker[1][0][-1],
    }
    assert all(checks.values())
    result = {'scope': 'Exact stipulated finite-step MAE limitation and scope breaker; not biological performance or novelty',
              'labels': labels, 'paths': [s for s, _ in first], 'losses': [l for _, l in first],
              'targets': target, 'mae_predictions': prediction, 'mae_mse': mae_mse,
              'shared_best': shared_best, 'shared_minimum_mse': shared_mse,
              'ordinary_direct_predictions': direct, 'ordinary_direct_mse': direct_mse,
              'breaker_paths': [s for s, _ in breaker], 'checks': checks}
    result_path.write_text(json.dumps(encode(result), indent=2), encoding='utf-8')
    print(json.dumps(encode(result), indent=2))
