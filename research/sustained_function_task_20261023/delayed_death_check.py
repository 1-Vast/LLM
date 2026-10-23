"""Exact counterexample to absorbing observed target counts at effector death."""
from fractions import Fraction as F
import hashlib
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/sustained_function_task'


def score(p, y):
    return (p - y) ** 2


def evaluate(sample_count):
    predictions = [F(0), F(1, 2)]
    total = [F(0), F(0), F(0)]
    mean_p = F(0)
    for source in product((0, 1), repeat=sample_count):
        empirical_p = F(sum(source), sample_count)
        mean_p += empirical_p / (2 ** sample_count)
        for y in (0, 1):
            weight = F(1, 2 ** (sample_count + 1))
            for index, p in enumerate(predictions + [empirical_p]):
                total[index] += weight * score(p, y)
    assert total[0] == F(1, 2)
    assert total[1] == F(1, 4)
    assert total[2] == F(1, 4) + F(1, 4 * sample_count)
    assert mean_p == F(1, 2)
    return dict(source_episodes=sample_count,
                source_query_assignments=2 ** (sample_count + 1),
                absorbed_brier=str(total[0]),
                ordinary_law_brier=str(total[1]),
                ordinary_empirical_brier=str(total[2]),
                empirical_mean_probability=str(mean_p),
                absorbed_mean_count_bias=str(F(-1, 2)))


if __name__ == '__main__':
    freeze = json.loads((OUT / 'DELAYED_DEATH_FREEZE.json').read_text(encoding='utf-8'))
    for item in freeze['files']:
        actual = hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest()
        assert actual == item['sha256'], item['path']
    result = dict(kind='stipulated_exact_math_not_biology',
                  query_pending_state_observed_by_either_method=False,
                  query_conditional_mean='1/2', terminal_remaining_count='0',
                  results=[evaluate(m) for m in (1, 2, 4, 8)],
                  decision='STOP_THIS_EFFECTOR_DEATH_ABSORBED_TARGET_COUNT_RULE')
    destination = OUT / 'DELAYED_DEATH_RESULT.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
