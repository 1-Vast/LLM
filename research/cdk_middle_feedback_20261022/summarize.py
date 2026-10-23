"""Summaries only; never refit or choose a new winner after outcomes."""
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/cdk_middle_feedback'


def main():
    results = json.loads((OUT / 'RESULT.json').read_text())
    summaries = {}
    for scheme in ('loo', 'index_blocked'):
        result = results[scheme]
        condition = {}
        families = sorted(set(tuple(r['task'][:2]) for r in result['rows']))
        for family in families:
            condition['_'.join(family)] = {
                name: {metric: float(np.mean([r[metric] for r in result['rows'] if r['method'] == name and tuple(r['task'][:2]) == family]))
                       for metric in ('hellinger2', 'tv')}
                for name in result['means']}
        pairs = result['paired_selected']
        summaries[scheme] = {
            'condition_means': condition,
            'paired_selected_mean_gain': {k: float(np.mean([r[k] for r in pairs])) for k in ('hellinger_gain', 'tv_gain')},
            'hellinger_positive_cultures': sum(r['hellinger_gain'] > 0 for r in pairs),
            'leave_condition_out_gain': {'_'.join(f): {k: float(np.mean([r[k] for r in pairs if tuple(r['task'][:2]) != f]))
                                                     for k in ('hellinger_gain', 'tv_gain')} for f in families},
            'paired_class_gain': {name: {metric: result['means']['early_' + name][metric] - result['means']['middle_' + name][metric]
                                         for metric in ('hellinger2', 'tv')} for name in ('shrink', 'kernel', 'ridge')},
        }
    (OUT / 'SUMMARY.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
    print(json.dumps({s: {k: v for k, v in summaries[s].items() if k != 'condition_means'} for s in summaries}, indent=2))


if __name__ == '__main__':
    main()
