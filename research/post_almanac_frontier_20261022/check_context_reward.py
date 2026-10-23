"""Finite synthetic audit of the stated AssayFormer context-delta objective."""
import itertools
import json
from pathlib import Path

records = []
for n in range(3, 7):
    for labels in itertools.product((0, 1), repeat=n):
        for horizon in range(2, n):
            evaluated = []
            for seq in itertools.permutations(range(n), horizon):
                remaining = set(range(n))
                baseline_sum = 0
                hits = 0
                for chosen in seq:
                    reference = min(remaining)  # fixed deterministic ranking
                    baseline_sum += labels[reference]
                    hits += labels[chosen]
                    remaining.remove(chosen)
                evaluated.append({'sequence': seq, 'hits': hits, 'delta': hits-baseline_sum, 'reference_hits': baseline_sum})
            witness = next(((a,b) for a in evaluated for b in evaluated if a['hits'] > b['hits'] and a['delta'] < b['delta']), None)
            if witness:
                records.append({'n': n, 'labels': labels, 'horizon': horizon, 'better_hits': witness[0], 'better_delta': witness[1]})
                break
        if records:
            break
    if records:
        break
assert records, 'No strict ranking-reversal witness found'
out = {'scope': 'synthetic deterministic batch-size-one restriction, no biological labels', 'result': records[0], 'claim_limit': 'The state-dependent reference return changes the stated total-hit objective. This does not refute author empirical gains or demonstrate a novel replacement.'}
Path('log/20261022/post_almanac_mechanism/frontier/CONTEXT_REWARD_CHECK.json').write_text(json.dumps(out, indent=2), encoding='utf8')
print(json.dumps(out, indent=2))
