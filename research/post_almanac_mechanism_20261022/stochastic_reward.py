"""Exact expected-reward witness with strictly positive Plackett-Luce reference."""
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_almanac_mechanism/root'
LABELS = (0, 1, 0, 0)
WEIGHTS = (10000, 100, 1, 1)


def evaluate(sequence):
    remaining = set(range(4))
    reference = []
    hits = 0
    for chosen in sequence:
        assert chosen in remaining
        reference.append(F(sum(WEIGHTS[g] * LABELS[g] for g in remaining), sum(WEIGHTS[g] for g in remaining)))
        hits += LABELS[chosen]
        remaining.remove(chosen)
    return hits, sum(reference), F(hits) - sum(reference), reference


def potential(remaining, time):
    return F(0) if time == 3 else F(sum((g + 1) ** 2 for g in remaining), time + 2)


def main():
    path = OUT / 'STOCHASTIC_REWARD.json'
    assert not path.exists()
    a, b = (0, 2, 1), (2, 3, 0)
    hits_a, ref_a, reward_a, steps_a = evaluate(a)
    hits_b, ref_b, reward_b, steps_b = evaluate(b)
    assert hits_a > hits_b and reward_a < reward_b
    records = []
    for seq in itertools.permutations(range(4), 3):
        remaining = set(range(4))
        initial = potential(remaining, 0)
        shaped = F(0)
        for t, chosen in enumerate(seq):
            before = potential(remaining, t)
            remaining.remove(chosen)
            shaped += LABELS[chosen] + potential(remaining, t + 1) - before
        hits, ref, reward, _ = evaluate(seq)
        assert shaped == hits - initial
        records.append({'sequence': list(seq), 'hits': hits, 'expected_context_delta': str(reward),
                        'potential_shaped_total': str(shaped)})
    result = {'status': 'PASS', 'scope': 'synthetic stated-formula check, not actual author weights/code/training or biological performance',
              'labels': LABELS, 'strictly_positive_reference_weights': WEIGHTS,
              'A': {'sequence': a, 'hits': hits_a, 'expected_reference_sum': str(ref_a),
                    'reference_hit_probabilities': list(map(str, steps_a)), 'expected_delta_reward': str(reward_a)},
              'B': {'sequence': b, 'hits': hits_b, 'expected_reference_sum': str(ref_b),
                    'reference_hit_probabilities': list(map(str, steps_b)), 'expected_delta_reward': str(reward_b)},
              'expected_reward_order_reversed': True, 'potential_telescoping_cases': len(records),
              'all_sequence_records': records,
              'protocol_sha256': hashlib.sha256((OUT.parent / 'ASSAY_REWARD_PROTOCOL.md').read_bytes()).hexdigest(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'A', 'B', 'expected_reward_order_reversed', 'potential_telescoping_cases')}, indent=2))


if __name__ == '__main__':
    main()
