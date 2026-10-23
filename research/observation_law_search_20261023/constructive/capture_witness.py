"""Exact synthetic observation witness, not a biological outcome experiment."""
import json
from fractions import Fraction as F
from pathlib import Path

worlds = [
    {'name': 'A', 'live': [50, 50], 'capture': [F(2, 5), F(2, 5)]},
    {'name': 'B', 'live': [80, 20], 'capture': [F(1, 4), F(1, 1)]},
]
results = []
for world in worlds:
    captured = [F(n) * p for n, p in zip(world['live'], world['capture'])]
    results.append({'name': world['name'], 'total_live': sum(world['live']),
                    'expected_captured': list(map(str, captured)),
                    'captured_state_fraction': list(map(str, [x / sum(captured) for x in captured])),
                    'after_state1_kill': world['live'][1],
                    'after_state2_kill': world['live'][0]})
assert results[0]['total_live'] == results[1]['total_live']
assert results[0]['expected_captured'] == results[1]['expected_captured']
assert results[0]['captured_state_fraction'] == results[1]['captured_state_fraction']
assert results[0]['after_state1_kill'] != results[1]['after_state1_kill']
Path('log/20261023/observation_law_search/constructive/CAPTURE_WITNESS.json').write_text(
    json.dumps({'checks_passed': 4, 'worlds': results,
                'scope': 'Equal expected observed summaries, not equality of the full finite-sampling likelihood under independent binomial capture. No claim about all repeated capture experiments.'}, indent=2), encoding='utf-8')
print(json.dumps(results))
