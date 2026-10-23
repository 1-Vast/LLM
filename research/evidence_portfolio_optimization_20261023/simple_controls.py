"""Post-result ordinary-filter controls; leaves frozen primary artifacts unchanged."""
import json

import numpy as np

import study as s


def main():
    frozen = json.loads((s.LOG / 'FREEZE.json').read_text(encoding='utf-8'))
    assert all(s.digest(s.ROOT / p) == h for p, h in frozen['files'].items())
    meta = json.loads((s.DATA / 'ELIGIBLE.json').read_text(encoding='utf-8'))
    old = json.loads((s.DATA / 'CHOICES.json').read_text(encoding='utf-8'))
    with np.load(s.DATA / 'OBSERVED.npz', allow_pickle=False) as obs:
        scout = obs['scout'].copy()
    first = old['scouts']  # Already in original-score order; do not inspect old final responses.
    F = len(old['finals']['feedback'])
    gate = lambda i: not (scout[i] > 0.10)
    choices = {
        'gate_original': np.array(sorted(first, key=gate)[:F]),
        'gate_random': np.array(sorted(first, key=lambda i: (gate(i), s.hashed('portfolio-gate-random-v1:' + meta[i]['unit'])))[:F]),
    }
    nominations = s.DATA / 'SIMPLE_CHOICES.json'
    s.save(nominations, {a: idx.tolist() for a, idx in choices.items()})
    s.save(s.LOG / 'SIMPLE_CHOICES_RECEIPT.json', {
        'post_result': True, 'new_final_responses_converted_after_choice_save': True,
        'choice_sha256': s.digest(nominations), 'code_sha256': s.digest(s.ROOT / 'research/evidence_portfolio_optimization_20261023/simple_controls.py'),
        'plan_sha256': s.digest(s.LOG / 'SIMPLE_CONTROL_PLAN.md'), 'threshold': 0.10})
    final_values = s.values(s.VALIDATION, {(meta[i]['unit'], meta[i]['final_plate']) for idx in choices.values() for i in idx})
    final = np.array([final_values.get((r['unit'], r['final_plate']), np.nan) for r in meta])
    detail = s.DATA / 'SIMPLE_FINALS.npz'
    np.savez_compressed(detail, final=final)
    lines = sorted({r['sidm'] for r in meta})
    li = np.array([lines.index(r['sidm']) for r in meta])
    boot = np.random.default_rng(20261023).integers(0, len(lines), (2000, len(lines)))
    feedback = np.array(old['finals']['feedback'])
    with np.load(s.DATA / 'OBSERVED.npz', allow_pickle=False) as obs:
        old_final = obs['final'].copy()
    summary = {}
    for a, idx in choices.items():
        summary[a] = {'planned_reads': len(first) + F, 'final_reads': len(idx),
                      'missing_final_reads': int(np.isnan(final[idx]).sum())}
        for threshold in (0.10, 0.0):
            pos = (scout[idx] > threshold) & (final[idx] > threshold)
            feedback_pos = (scout[feedback] > threshold) & (old_final[feedback] > threshold)
            counts = np.bincount(li[idx], weights=pos, minlength=len(lines))
            baseline = np.bincount(li[feedback], weights=feedback_pos, minlength=len(lines))
            d = counts - baseline
            summary[a][str(threshold)] = {'repeat_positive': int(pos.sum()),
                'positive_final_reads_secondary': int((final[idx] > threshold).sum()),
                'difference_from_feedback': int(d.sum()),
                'conditional_sidm_bootstrap_95pct_difference': np.quantile(d[boot].sum(1), [.025, .975]).tolist()}
    result = {'post_result_descriptive_only': True, 'scout_positive_candidates': int((scout[first] > .10).sum()),
              'summary': summary, 'choice_sha256': s.digest(nominations), 'observed_sha256': s.digest(detail)}
    s.save(s.LOG / 'SIMPLE_CONTROL_RESULTS.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
