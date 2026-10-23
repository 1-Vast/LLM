"""Summarize the frozen run, with no new fitting or outcome selection."""
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/interaction_error_diagnostic'
r = json.loads((OUT/'RESULTS.json').read_text())
lines = ['# Frozen development run: descriptive results', '',
         'Published full-screen-conditioned GI units; two masks averaged within each context. '
         'Negative MSE change means improvement. Ranking change is identity-minus-score-direct regret.', '',
         '|Support|Context|Source-mean MSE|Score-direct MSE|Identity MSE|Identity MSE change|Regret change|Unseen-endpoint query fraction|',
         '|---|---|---:|---:|---:|---:|---:|---:|']
for a in r['aggregate']:
    for c in a['contexts']:
        mse = c['comparison']['mse']
        regret = c['comparison']['bottom20_regret']
        coverage = mean(row['endpoint_unseen_fraction'] for row in r['records']
                        if row['context'] == c['context'] and row['budget'] == a['budget'])
        lines.append(f"|{a['budget']}|{c['context']}|{mse['source_mean']:.5f}|{mse['score_direct']:.5f}|"
                     f"{mse['identity_ordinary']:.5f}|{100*(mse['identity_ordinary']/mse['score_direct']-1):+.2f}%|"
                     f"{regret['identity_ordinary']-regret['score_direct']:+.5f}|{coverage:.2%}|")
    for metric in ('mse', 'bottom20_regret'):
        values = {method: mean(c['comparison'][metric][method] for c in a['contexts'])
                  for method in a['contexts'][0]['comparison'][metric]}
        lines.extend(['', f"Support{a['budget']} equal-context mean {metric}: `{json.dumps(values)}`", ''])
lines.extend(['', f"Screening gate: {r['screening_gate']}; joint wins by budget: "
              f"{[(a['budget'], a['joint_wins']) for a in r['aggregate']]}", '',
              f"Recorded main-run wall time {r['total_seconds']:.3f}s (imports outside this timer). "
              f"Pipeline calls {sum(x['pipeline_calls'] for x in r['records'])}; "
              f"estimator fits {sum(x['estimator_fits'] for x in r['records'])}; "
              f"kernel solves {sum(x['kernel_linear_solves'] for x in r['records'])}.", '',
              'These totals include all registered tuning/refit/permutation operations. '
              'They exclude prior metadata tests/reviews and are not equal-cost comparisons or wet-screen savings. '
              'The identity permutation arm uses the true-support-selected configuration, so it is a negative-control diagnostic, not an independent null-selection test.'])
text = '\n'.join(lines)+'\n'
assert not (OUT/'SUMMARY.md').exists()
(OUT/'SUMMARY.md').write_text(text, encoding='utf-8')
print(text)
