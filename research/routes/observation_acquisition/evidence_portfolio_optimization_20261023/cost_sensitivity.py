"""Post-result cost-aware SIDM bootstrap; no new response data."""
import json

import numpy as np

import study as s


def main():
    meta = json.loads((s.DATA / 'ELIGIBLE.json').read_text(encoding='utf-8'))
    choices = json.loads((s.DATA / 'CHOICES.json').read_text(encoding='utf-8'))
    extra = json.loads((s.DATA / 'SIMPLE_CHOICES.json').read_text(encoding='utf-8'))
    with np.load(s.DATA / 'OBSERVED.npz', allow_pickle=False) as z:
        scout, final = z['scout'].copy(), z['final'].copy()
    with np.load(s.DATA / 'SIMPLE_FINALS.npz', allow_pickle=False) as z:
        more = z['final'].copy()
    lines = sorted({r['sidm'] for r in meta})
    li = np.array([lines.index(r['sidm']) for r in meta])
    boot = np.random.default_rng(20261023).integers(0, len(lines), (2000, len(lines)))
    rates, point = {}, {}
    for a, indices in {**choices['finals'], **extra}.items():
        idx = np.array(indices)
        paid = np.array(choices['scouts_by_arm'].get(a, choices['scouts']))
        y = more if a in extra else final
        hits = (scout[idx] > .10) & (y[idx] > .10)
        counts = np.bincount(li[idx], weights=hits, minlength=len(lines))
        costs = np.bincount(li[idx], minlength=len(lines)) + np.bincount(li[paid], minlength=len(lines))
        rates[a] = 1000 * counts[boot].sum(1) / (7 * costs[boot].sum(1))
        point[a] = 1000 * counts.sum() / (7 * costs.sum())
    result = {'post_result_descriptive_only': True,
              'interpretation': 'Fixed-policy contributions resampled by SIDM, each arm normalized by its own resampled paid cost; no reranking or prospective inference',
              'positive_threshold': .10, 'differences_feedback_minus_control_per_1000_wells': {}}
    for a in ('fixed', 'direct', 'mix', 'gate_original', 'gate_random'):
        result['differences_feedback_minus_control_per_1000_wells'][a] = {
            'point': point['feedback'] - point[a],
            'conditional_sidm_bootstrap_95pct': np.quantile(rates['feedback'] - rates[a], [.025, .975]).tolist()}
    s.save(s.LOG / 'COST_SENSITIVITY.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
