"""Independent Decimal row-score assembly plus budget/deployment verification."""
from collections import defaultdict
from decimal import Decimal, localcontext
import json
import math

from screen import OUT, S0, sha, write


def load(name):
    return json.loads((OUT / name).read_text())


def main():
    result = load('RESULT.json')
    rows = load('TERMINAL_ROWS.json')
    trajectories = load('TRAJECTORY_RESULTS.json')
    committed = load('DEPLOYMENTS.json')
    seal = load('DEPLOYMENT_SEAL.json')
    assert sha(OUT / 'DEPLOYMENTS.json') == seal['deployments_sha256']
    assert sha(OUT / 'SOURCE_LEARNING.json') == seal['source_learning_sha256']
    assert seal['earlier_full_truth_array_decoded'] is True
    assert seal['terminal_selected_for_scoring'] is False
    assert seal['terminal_feedback_exposed'] is False
    compared = 0
    maximum_error = 0.
    for record in rows:
        grouped = defaultdict(list)
        for comp, scalar in zip(record['comp'], record['row_cosine']):
            grouped[comp].append(Decimal(str(scalar)))
        with localcontext() as ctx:
            ctx.prec = 40
            means = [sum(values) / Decimal(len(values)) for values in grouped.values()]
            independent = float(sum(means) / Decimal(len(means)))
        stored = (result['episode_scores'][record['episode']]['mixture'] if record['program'] == 'mixture'
                  else result['episode_scores'][record['episode']]['program_scores'][record['program']])
        error = abs(independent - stored)
        maximum_error = max(maximum_error, error)
        assert error < 2e-14
        compared += 1
    assert len(trajectories) == len(committed) == 8 * 3 * 7
    for record, original in zip(trajectories, committed):
        assert {key: value for key, value in record.items() if key != 'terminal_score'} == original
        requests = record['trajectory']
        assert len(requests) == len({r['program'] for r in requests}) == 4
        assert all(r['program'] != S0 for r in requests)
        assert record['deployment'] in {S0, *(r['program'] for r in requests)}
        assert record['terminal_score'] == result['episode_scores'][record['episode']]['program_scores'][record['deployment']]
    source = load('SOURCE_LEARNING.json')
    for j in range(12):
        expected = math.fsum(row[j] - row[S0] for row in source['source_scores']) / 8 / .02
        assert abs(expected - source['logits'][j]) < 1e-13
    nonbase = [j for j in range(12) if j != S0]
    assert sorted(source['logits'][j] for j in nonbase) == sorted(source['permuted_logits'][j] for j in nonbase)
    assert source['permuted_logits'][S0] == source['logits'][S0]
    episode_summary = []
    for episode, scores in result['episode_scores'].items():
        values = {arm: math.fsum(r['terminal_score'] for r in trajectories
                                if r['episode'] == episode and r['arm'] == arm) / 3
                  for arm in ('old', 'new', 'cyclic', 'source_best', 'contextual', 'history', 'permuted')}
        values.update({arm: scores[arm] for arm in ('S0', 'full_dictionary', 'mixture', 'oracle')})
        ordinary = [arm for arm in values if arm not in ('new', 'oracle', 'permuted')]
        strongest = max(ordinary, key=values.get)
        episode_summary.append({'episode': episode, 'means_over_3_seeds': values,
                                'new_minus_old': values['new'] - values['old'],
                                'new_minus_global_strongest_ordinary': values['new'] - values[result['strongest_ordinary_envelope']],
                                'episodewise_posthoc_envelope': strongest,
                                'new_minus_episodewise_envelope': values['new'] - values[strongest],
                                'oracle_minus_S0': values['oracle'] - values['S0']})
    seed_differences = {}
    for seed in (1729, 2718, 31415):
        means = {arm: math.fsum(r['terminal_score'] for r in trajectories if r['seed'] == seed and r['arm'] == arm) / 8
                 for arm in ('old', 'new')}
        seed_differences[str(seed)] = means['new'] - means['old']
    write('PAIRED_EPISODE_SUMMARY.json', {'episodes': episode_summary, 'seed_new_minus_old': seed_differences})
    write('INDEPENDENT_RESULT_CHECK.json', {'status': 'PASS', 'decimal_episode_scores': compared,
          'maximum_absolute_difference': maximum_error, 'validated_trajectories': len(trajectories),
          'proposal_counts': len(trajectories) * 4, 'source_logits_and_permutation': 'PASS',
          'deployment_integrity': 'PASS'})
    print(json.dumps({'status': 'PASS', 'decimal_scores': compared, 'max_error': maximum_error}))


if __name__ == '__main__':
    main()
