"""Exact structural-resolution versus drug-regret probe ranking witness."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

# Four equiprobable mechanistic models; first three agree on optimal drug A.
utilities = {'m1': {'A': 1, 'B': 0}, 'm2': {'A': 1, 'B': 0},
             'm3': {'A': 1, 'B': 0}, 'm4': {'A': 0, 'B': 1}}
# Both probes cost one unit, and expose only the outcome of the selected probe.
partitions = {'structure_probe': [('m1', 'm4'), ('m2',), ('m3',)],
              'drug_probe': [('m1', 'm2', 'm3'), ('m4',)]}
results = {}
for probe, groups in partitions.items():
    expected_size = F(0)
    expected_regret = F(0)
    decision_ambiguity = F(0)
    for models in groups:
        probability = F(len(models), 4)
        expected_size += probability * len(models)
        means = {a: sum(F(utilities[m][a]) for m in models)/len(models) for a in ('A', 'B')}
        chosen = max(('A', 'B'), key=lambda a: means[a])
        conditional_regret = sum(F(max(utilities[m].values()) - utilities[m][chosen]) for m in models)/len(models)
        expected_regret += probability * conditional_regret
        possible_best = {max(('A', 'B'), key=lambda a: utilities[m][a]) for m in models}
        decision_ambiguity += probability * len(possible_best)
    results[probe] = dict(expected_structural_set=str(expected_size),
                          expected_drug_regret=str(expected_regret),
                          expected_best_drug_set=str(decision_ambiguity))
assert results['structure_probe'] == {'expected_structural_set': '3/2', 'expected_drug_regret': '1/4', 'expected_best_drug_set': '3/2'}
assert results['drug_probe'] == {'expected_structural_set': '5/2', 'expected_drug_regret': '0', 'expected_best_drug_set': '1'}
out = Path(__file__).resolve().parents[3] / 'log/20261023/decision_probe_mechanism/critic'
record = dict(status='PASS', results=results, false_exclusion=0,
              equal_probe_cost=1, randomness=False, actual_biological_data=False,
              explanation='At zero structural false-exclusion, a deterministic observation requires retaining its whole structural fiber. This is a chosen-target counterexample, not a refutation of RAED or Action-BED and not a new algorithm.',
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'PROBE_TARGET_WITNESS.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
