"""Exact tests of complete API equations; no biological inputs or generated code."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/inherited_update_renewal'


def encode(value):
    if isinstance(value, F):
        return {'exact': str(value), 'decimal': float(value)}
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [encode(item) for item in value]
    return value


if __name__ == '__main__':
    target = OUT/'API_CHECK.json'
    assert not target.exists(), 'One frozen check only'
    freeze = json.loads((OUT/'API_CHECK_FREEZE.json').read_text(encoding='utf-8'))
    for path, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
    direction, a, y = [F(1), F(2)], [F(1), F(1)], F(3)
    dot = sum(x*z for x, z in zip(direction, a))
    alpha = y/dot
    proposed = [alpha*x for x in direction]
    # Conditional N(0, ss^T) mean after a^T theta=y, zero observation noise.
    covariance_a = [x*dot for x in direction]
    empirical_bayes = [x*y/(dot*dot) for x in covariance_a]
    assert proposed == empirical_bayes == [F(1), F(2)]
    ordinary_uninformed = [F(3, 2), F(3, 2)]
    epsilon = F(1, 1000000)
    scale = F(1, 1000)
    identity = [1/(1+epsilon), 1/(1+epsilon)]
    reparameterized_physical = [scale*scale/(scale*scale+epsilon), 1/(1+epsilon)]
    identity_query = identity[1]/identity[0]
    changed_query = reparameterized_physical[1]/reparameterized_physical[0]
    assert identity_query == 1 and changed_query == F(2000000, 1000001)
    history = [F(-1, 4), F(1, 2)]
    history_control = history[0]+history[1]**2
    history_drug = sum(history)
    s2 = history_drug/(1+epsilon)
    step = history_drug/s2
    final_theta = [F(0), step*s2]
    final_control = final_theta[0]+final_theta[1]**2
    assert history_control == 0 and final_control == F(1, 16)
    result = {'status': 'PASS_EXACT_LITERAL_CHECKS', 'utc': datetime.now(timezone.utc).isoformat(),
              'same_history_toy': {'proposed': proposed, 'ordinary_rank_one_gaussian': empirical_bayes,
                                  'uninformed_ls': ordinary_uninformed,
                                  'proposed_query_error': (proposed[1]-2)**2,
                                  'ordinary_same_history_query_error': (empirical_bayes[1]-2)**2},
              'coordinate_check': {'epsilon': epsilon, 'physical_scale': scale,
                                   'identity_direction': identity,
                                   'changed_physical_direction': reparameterized_physical,
                                   'identity_query_after_same_feedback': identity_query,
                                   'changed_query_after_same_feedback': changed_query,
                                   'difference': changed_query-identity_query},
              'finite_control_check': {'history_control_increment': history_control,
                                       'history_drug_increment': history_drug,
                                       'direction_second_coordinate': s2, 'alpha': step,
                                       'initial_control_jacobian_dot_direction': F(0),
                                       'finite_control_increment': final_control,
                                       'final_drug_prediction': sum(final_theta)},
              'scope': 'Synthetic arithmetic only; no biological prediction or RSI verification'}
    target.write_text(json.dumps(encode(result), indent=2), encoding='utf-8')
    print(json.dumps(encode(result), indent=2))
