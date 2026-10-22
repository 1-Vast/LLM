"""Verify the skeptic's joint-feasibility witness by independent enumeration."""
from itertools import product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/intervention_dynamics_renewal/mechanism_round2'


def separate_margins_pass(record):
    n = 2
    state_pass = sum(max(q[k] for q, z in record) for k in range(2)) <= n
    scalar_pass = max(z for q, z in record) <= min(z+n-sum(q) for q, z in record)
    return state_pass, scalar_pass


def audit():
    joint_types = tuple(product(range(2), repeat=2))
    realizable = set()
    configurations = 0
    for types in product(joint_types, repeat=2):
        for masks in product(range(4), repeat=3):
            views = []
            for mask in masks:
                kept = [types[i] for i in range(2) if (mask >> i) & 1]
                q = tuple(sum(state == k for state, y in kept) for k in range(2))
                z = sum(y for state, y in kept)
                views.append((q, z))
            realizable.add(tuple(views))
            configurations += 1
    rejected = (((1, 1), 1), ((1, 0), 1), ((1, 0), 0))
    positive = (((1, 1), 1), ((1, 0), 1), ((1, 0), 1))
    assert configurations == 1024
    assert separate_margins_pass(rejected) == (True, True)
    assert rejected not in realizable
    assert separate_margins_pass(positive) == (True, True)
    assert positive in realizable
    return {'status': 'PASS_EXACT_JOINT_LOGIC_ONLY', 'configurations': configurations,
        'distinct_realizable_summaries': len(realizable),
        'negative': {'half_mass_unit_summaries': rejected,
            'separate_state_and_scalar_gates_pass': True, 'joint_realizable': False},
        'positive': {'half_mass_unit_summaries': positive, 'joint_realizable': True},
        'biological_or_performance_evidence': False}


def main():
    result = audit() | {
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256': hashlib.sha256((OUT/'JOINT_LOGIC_PROTOCOL.md').read_bytes()).hexdigest()}
    with (OUT/'JOINT_LOGIC_RESULT.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
