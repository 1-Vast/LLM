"""Summarize frozen result records only; no workbook access or refitting."""
import json
from pathlib import Path

root = Path('log/20261023/interaction_error_diagnostic')
r = json.loads((root / 'RESULTS.json').read_text())
out = {'screening_gate': r['screening_gate'], 'budgets': []}
for aggregate in r['aggregate']:
    budget = aggregate['budget']
    rows = []
    for c in aggregate['contexts']:
        m = c['comparison']
        rows.append({'context': c['context'], 'metrics': m,
                     'identity_vs_direct_mse_gain': m['mse']['score_direct'] - m['mse']['identity_ordinary'],
                     'identity_vs_direct_regret_gain': m['bottom20_regret']['score_direct'] - m['bottom20_regret']['identity_ordinary'],
                     'selected': [x['chosen'] for x in r['records'] if x['context'] == c['context'] and x['budget'] == budget]})
    means = {metric: {model: sum(c['comparison'][metric][model] for c in aggregate['contexts']) / 5
                     for model in aggregate['contexts'][0]['comparison'][metric]}
             for metric in ['mse', 'bottom20_regret']}
    coverage = [x['endpoint_unseen_fraction'] for x in r['records'] if x['budget'] == budget]
    out['budgets'].append({'budget': budget, 'joint_wins': aggregate['joint_wins'],
                           'mean_metrics': means, 'endpoint_unseen_range': [min(coverage), max(coverage)],
                           'contexts': rows})
(root / 'constructive' / 'RESULT_SUMMARY.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
