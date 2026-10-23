"""Exact expectations for finite-logit stochastic reference, not an author run."""
import json
import math
from pathlib import Path

labels = [0, 1, 0, 0]
logits = [6, 4, 2, 0]
sequences = [[0, 2, 1], [2, 3, 0]]
results = []
for sequence in sequences:
    remaining = set(range(4))
    expected_reference_hits = []
    for chosen in sequence:
        weights = {i: math.exp(logits[i]) for i in remaining}
        expected_reference_hits.append(sum(weights[i] * labels[i] for i in remaining) / sum(weights.values()))
        remaining.remove(chosen)
    hits = sum(labels[i] for i in sequence)
    results.append({'sequence': sequence, 'hits': hits, 'expected_reference_hits_by_step': expected_reference_hits, 'expected_delta': hits - sum(expected_reference_hits)})
assert results[0]['hits'] > results[1]['hits']
assert results[0]['expected_delta'] < results[1]['expected_delta']
record = {'labels': labels, 'reference_logits': logits, 'temperature': 1, 'batch_size': 1, 'method': 'Gumbel-top-1 categorical expectation, analytically summed', 'results': results, 'scope': 'Two fixed acquisition paths; stochastic reference expectation. Not a released-model or biological run, nor a prediction of empirical learning benefit.'}
Path('log/20261022/post_almanac_mechanism/frontier/STOCHASTIC_REFERENCE_CHECK.json').write_text(json.dumps(record, indent=2), encoding='utf8')
print(json.dumps(record, indent=2))
