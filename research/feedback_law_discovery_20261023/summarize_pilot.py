"""Apply the pre-frozen functional continuation rule; no new fitting or selection."""
import json
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parents[2]/'log/20261023/feedback_law_discovery/pilot'


if __name__ == '__main__':
    result = json.loads((OUT/'RESULT.json').read_text(encoding='utf-8'))
    records = result['records']
    table = []
    for kind in ('mean', 'covariance', 'fixed', 'augmented', 'consistent', 'set'):
        rows = [r for r in records if r['kind'] == kind]
        table.append(dict(kind=kind, seeds=len(rows),
                          mse=float(np.mean([r['metrics']['mse'] for r in rows])),
                          regret=float(np.mean([r['metrics']['regret'] for r in rows])),
                          order_sensitivity=float(np.mean([r.get('order_sensitivity', 0) for r in rows])),
                          partition_sensitivity=float(np.mean([r.get('partition_sensitivity', 0) for r in rows])),
                          train_seconds=sum(r['train_seconds'] for r in rows),
                          parameters=rows[0]['parameters']))
    comparisons = []
    for seed in (0, 1, 2):
        c = next(r for r in records if r['kind']=='consistent' and r['seed']==seed)
        a = next(r for r in records if r['kind']=='augmented' and r['seed']==seed)
        comparisons.append(dict(seed=seed,
            mse_relative_change=(c['metrics']['mse']/a['metrics']['mse']-1),
            regret_relative_change=(c['metrics']['regret']/a['metrics']['regret']-1),
            both_improve=all(c['metrics'][key] < a['metrics'][key] for key in ('mse', 'regret'))))
    by_kind = {r['kind']:r for r in table}
    beat_sentinels = all(by_kind['consistent'][metric] < by_kind[kind][metric]
                         for kind in ('mean','covariance','set') for metric in ('mse','regret'))
    passed = all(r['both_improve'] for r in comparisons) and beat_sentinels
    summary = dict(status='GO_TO_LATER_FULL_COMPARISON' if passed else 'STOP_EXPANDING_THIS_FIXED_CONSISTENCY_CONFIGURATION',
                   train_contexts=result['train_contexts'], query_contexts=result['query_contexts'],
                   query_patients=result['query_patients'], drugs=result['drugs'], table=table,
                   paired_seed_comparisons=comparisons, beat_sentinels=beat_sentinels,
                   context_episode_replays=sum(r.get('context_episodes',0) for r in records),
                   context_view_evaluations=sum(r.get('query_view_evaluations',0) for r in records),
                   scalar_query_evaluations=sum(r.get('scalar_query_evaluations',0) for r in records),
                   fast_package_gradient_evaluations=sum(r.get('fast_package_gradient_evaluations',0) for r in records),
                   overall_seconds=result['overall_seconds'], preprocessing_seconds=result['preprocessing_seconds'],
                   scope='Exposed-source fixed-config screen; no clinical utility, world, inheritance or RSI claim')
    (OUT/'SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
