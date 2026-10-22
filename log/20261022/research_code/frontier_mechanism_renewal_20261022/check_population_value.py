"""Exact stipulated population check; no biological data or learned fit."""
from fractions import Fraction as F
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/frontier_mechanism_renewal'


if __name__ == '__main__':
    population = [(z, s, F(1, 2) * (F(4, 5) if z == s else F(1, 5)))
                  for z in (-1, 1) for s in (-1, 1)]
    risks = {name: sum(p * (F(z) - forecast(s)) ** 2 for z, s, p in population)
             for name, forecast in {'unchanged': lambda s: F(0),
                                    'unconditional_support_edit': lambda s: F(1),
                                    'population_conditional': lambda s: F(3, 5) * s}.items()}
    accuracy = sum(p for z, s, p in population if z == s)
    constant_accuracy = sum(p for z, s, p in population if z == 1)
    means = {str(s): sum(p * z for z, ss, p in population if ss == s) /
             sum(p for z, ss, p in population if ss == s) for s in (-1, 1)}
    checks = [sum(p for z, s, p in population) == 1,
              risks['unchanged'] == 1, risks['unconditional_support_edit'] == 2,
              risks['population_conditional'] == F(16, 25),
              accuracy == F(4, 5), constant_accuracy == F(1, 2),
              means == {'-1': F(-3, 5), '1': F(3, 5)}]
    assert all(checks)
    result = {'passed': True, 'checks': len(checks), 'risks': risks,
              'action_accuracy': accuracy, 'constant_action_accuracy': constant_accuracy,
              'conditional_target_means': means,
              'scope': 'Exact stipulated stable task/sensor population; not estimated biology, finite-data learning, novelty or RSI evidence.'}
    with (OUT / 'INDEPENDENT_POPULATION_ALGEBRA.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, default=str)
    print(json.dumps(result, default=str))
