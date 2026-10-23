"""Constructed observational equivalence, not a biological fit or new theorem."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/renewal_application/skeptic'
# origin, destination (None means dead), generation, founders, descendants/founder
MODELS = {
    'selection_only': [('A', 'A', 0, 198, 1), ('A', None, None, 2, 0),
                       ('B', 'B', 0, 198, 1), ('B', 'B', 1, 2, 2)],
    'state_change': [('A', 'A', 0, 198, 1), ('A', 'B', 1, 1, 2),
                     ('A', None, None, 1, 0), ('B', 'B', 0, 198, 1),
                     ('B', 'B', 1, 1, 2), ('B', None, None, 1, 0)]}


def summarize(events):
    initial = {state: 0 for state in ('A', 'B')}
    joint = {state + '|' + str(generation): 0
             for state in ('A', 'B') for generation in (0, 1)}
    flow = {origin + '>' + destination: 0
            for origin in ('A', 'B') for destination in ('A', 'B')}
    births, deaths = 0, 0
    for origin, destination, generation, founders, descendants in events:
        initial[origin] += founders
        if descendants == 0:
            deaths += founders
        else:
            births += founders * (descendants - 1)
            joint[destination + '|' + str(generation)] += founders * descendants
            flow[origin + '>' + destination] += founders * descendants
    endpoint = {state: sum(joint[state + '|' + str(g)] for g in (0, 1))
                for state in ('A', 'B')}
    observed = {'initial': initial, 'endpoint_state_generation': joint,
                'endpoint_state': endpoint, 'endpoint_total': sum(endpoint.values()),
                'birth_events_total': births, 'death_events_total': deaths}
    return observed, flow


def ordinary_mixture(observed):
    """A saturated two-state conditional table, not an extrapolation claim."""
    total = observed['endpoint_total']
    state_weight, conditional, reproduced = {}, {}, {}
    for state, count in observed['endpoint_state'].items():
        state_weight[state] = Fraction(count, total)
        conditional[state] = Fraction(observed['endpoint_state_generation'][state + '|1'], count)
        for generation in (0, 1):
            probability = conditional[state] if generation else 1 - conditional[state]
            reproduced[state + '|' + str(generation)] = total * state_weight[state] * probability
    return {'state_weights': {k: str(v) for k, v in state_weight.items()},
            'cycling_given_state': {k: str(v) for k, v in conditional.items()},
            'reproduced_joint': {k: int(v) for k, v in reproduced.items()}}


def audit():
    first, first_flow = summarize(MODELS['selection_only'])
    second, second_flow = summarize(MODELS['state_change'])
    mixture = ordinary_mixture(first)
    checks = {
        'all_endpoint_and_global_observables_identical': first == second,
        'different_origin_destination_flow': first_flow != second_flow,
        'selection_no_A_to_B': first_flow['A>B'] == 0,
        'state_change_positive_A_to_B': second_flow['A>B'] == 2,
        'ordinary_mixture_reproduces_joint': mixture['reproduced_joint'] == first['endpoint_state_generation'],
        'one_percent_cycling_tail': Fraction(sum(v for k, v in first['endpoint_state_generation'].items()
                                               if k.endswith('|1')), first['endpoint_total']) == Fraction(1, 100)}
    return {'status': 'CONSTRUCTED_EQUIVALENCE_PASS' if all(checks.values()) else 'AUDIT_FAIL',
            'checks': checks, 'observed': first,
            'hidden_flows': {'selection_only': first_flow, 'state_change': second_flow},
            'ordinary_mixture': mixture,
            'additional_feedback_distinguishing_pair': {'origin_A_late_B': [first_flow['A>B'], second_flow['A>B']]},
            'limits': ['Hand-constructed counts; no biological data or fitted performance.',
                       'One joint count distinguishes this pair, not arbitrary systems.',
                       'Endpoint-equivalence does not preclude early-to-late predictive utility.']}


def main():
    freeze = json.loads((LOG / 'SELECTION_TRANSPORT_FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Freeze mismatch: ' + name)
    result = audit()
    with (LOG / 'SELECTION_TRANSPORT_RESULT.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'checks': result['checks']}))
    if not all(result['checks'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
