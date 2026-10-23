"""Exact falsification of three literal API proposal claims; no real data."""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/contrast_gate_check'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    sums = [sum(w / sum(weights) for w in weights)
            for weights in ([F(2), F(3)], [F(1, 1000000)], [F(7)] * 100)]
    empty_support_defined = sum([]) != 0
    truth, support = F(1), F(0)
    tolerance = F(1, 4)
    predictions = [F(0), F(1)]
    consistency = [(abs(p - support) <= tolerance, (p - truth) ** 2) for p in predictions]
    actual = [F(1, 5), F(2, 5)]
    before, after = [F(4, 5), F(2, 5)], actual.copy()
    choose_before = min(range(2), key=before.__getitem__)
    choose_after = min(range(2), key=after.__getitem__)
    regrets = [actual[i] - min(actual) for i in (choose_before, choose_after)]
    checks = [all(s == 1 for s in sums), not empty_support_defined,
              consistency == [(True, F(1)), (False, F(0))],
              all(p > 0 for p in before + after),
              choose_before != choose_after, regrets == [F(1, 5), F(0)]]
    assert all(checks)
    files = [Path(__file__), OUT / 'PROTOCOL.md',
             ROOT / 'log/20261022/contrast_mechanism_scout/api_direct/RESPONSE.md']
    result = {'passed': True, 'checks': len(checks), 'normalized_sums': sums,
              'zero_support_formula_defined': empty_support_defined,
              'consistency_gate_pass_and_squared_error': consistency,
              'projection_effect_signs_unchanged': True, 'before_after_action_regret': regrets,
              'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in files},
              'scope': 'Exact counterexamples to literal claims; no biological, population-learning impossibility, novelty or RSI conclusion.'}
    with (OUT / 'RESULT.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, default=str)
    print(json.dumps(result, default=str))
