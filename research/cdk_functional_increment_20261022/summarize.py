"""Summarize the fixed allocation gate without selecting a model or endpoint."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_functional_increment'
p = json.loads((OUT / 'RESULT.json').read_text())
summary = {'challenge': {}}
for name, result in p['results'].items():
    directions = {}
    for lam, metrics in result['summary'].items():
        e, m = metrics['early']['macro_loss'], metrics['early_middle']['macro_loss']
        directions[lam] = None if e is None or m is None else bool(m < e and m < .5)
    summary['challenge'][name] = {
        'eligible_cultures': len(result['eligible']), 'missing_cultures': len(result['missing']),
        'scored_pairs': result['summary']['1']['early']['pairs'],
        'nonestimable_pairs': len(result['nonestimable']), 'true_ties': len(result['true_ties']),
        'directions': directions,
        'gate': 'NOT_ESTIMABLE' if any(v is None for v in directions.values()) else
                ('PASS' if all(directions.values()) else 'FAILED'),
        'fixed_lambda_1': result['summary']['1']}
summary['overall'] = 'PASS' if all(v['gate'] == 'PASS' for v in summary['challenge'].values()) else 'NOT_MET'
summary['decision'] = 'STOP_EXPANDING_EXACT_FUNCTIONAL_PREFIX_KRR_CONFIGURATION' if summary['overall'] != 'PASS' else 'EXPLORATORY_FUNCTIONAL_SIGNAL_ONLY'
(OUT / 'SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
