"""Finite synthetic continuation credit; no biological data or external model."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import hashlib

OUT = Path('log/20261022/mechanism_gap/recursive')
SEQUENCES = list(product((0, 1), repeat=2))


def prediction(a, rho, enabled, fitted, t):
    return a * rho ** t if enabled and fitted == 1 else a * rho if fitted == 0 else a


def run(a, rho, sequence, terminal=2):
    enabled, fitted = False, None
    scores = [-((a - a * rho ** 2) / a) ** 2]
    for step, edit in enumerate(sequence):
        if step == 0 and edit == 1:
            enabled = True
        elif edit == 0:
            fitted = 0
        elif enabled:
            fitted = 1
        yhat = prediction(a, rho, enabled, fitted, 2)
        scores.append(-((yhat - a * rho ** 2) / a) ** 2)
    final = prediction(a, rho, enabled, fitted, terminal)
    return scores, ((final - a * rho ** terminal) / a) ** 2


def mean(xs):
    return sum(xs) / len(xs)


source = []
for a, rho in product((F(1, 4), F(3, 4)), (F(1), F(1, 2))):
    for seq in SEQUENCES:
        scores, _ = run(a, rho, seq)
        source.append({'a': a, 'rho': rho, 'context': rho < 1, 'sequence': seq, 'scores': scores})

policies = {}
learned = {}
for context in (False, True):
    rows = [r for r in source if r['context'] == context]
    suffix = {seq: mean([r['scores'][2] - r['scores'][1] for r in rows if r['sequence'] == seq]) for seq in SEQUENCES}
    immediate = {first: mean([r['scores'][1] - r['scores'][0] for r in rows if r['sequence'][0] == first]) for first in (0, 1)}
    continuation = {first: immediate[first] + max(suffix[first, second] for second in (0, 1)) for first in (0, 1)}
    first = max((0, 1), key=continuation.get)
    seq = first, max((0, 1), key=lambda second: suffix[first, second])
    totals = {s: mean([r['scores'][2] - r['scores'][0] for r in rows if r['sequence'] == s]) for s in SEQUENCES}
    portfolio = max(SEQUENCES, key=totals.get)
    beta = {s: (1 + sum(r['scores'][2] == 0 for r in rows if r['sequence'] == s)) / F(2 + sum(r['sequence'] == s for r in rows)) for s in SEQUENCES}
    beta_seq = max(SEQUENCES, key=beta.get)
    # Independent depth-two exhaustive rollout on the same observed transitions.
    rollout = sorted(((totals[s], -s[0], -s[1], s) for s in SEQUENCES), reverse=True)[0][3]
    assert seq == portfolio == beta_seq == rollout
    myopic = max((0, 1), key=immediate.get)
    policies[context] = {'continuation': seq, 'contextual_sequence': portfolio,
                         'beta_contextual': beta_seq, 'finite_horizon_rollout': rollout,
                         'myopic_diagnostic': (myopic, 0), 'source_best_program': (1, 1)}
    learned[str(context)] = {'immediate': immediate, 'continuation': continuation,
                             'suffix': {str(k): v for k, v in suffix.items()}, 'sequence': seq}
assert learned['True']['sequence'] == (1, 1)
assert learned['True']['immediate'][1] == 0
assert learned['True']['continuation'][1] > learned['True']['continuation'][0]

# Freeze learned checkpoints before any later terminal evaluation.
serialize = lambda x: str(x) if isinstance(x, F) else x
checkpoint = json.dumps(learned, default=serialize, indent=2)
(OUT / 'CHECKPOINT.json').write_text(checkpoint, encoding='utf8')
(OUT / 'SOURCE_TRACES.json').write_text(json.dumps(source, default=serialize, indent=2), encoding='utf8')
later = []
for a, rho in product((F(1, 3), F(2, 3)), (F(1), F(1, 2))):
    losses = {method: run(a, rho, seq, terminal=3)[1] for method, seq in policies[rho < 1].items()}
    direct_prediction = a * ((a * rho) / a) ** 3
    losses['fixed_direct_refit'] = ((direct_prediction - a * rho ** 3) / a) ** 2
    later.append({'a': a, 'rho': rho, 'fresh_base': a, 'sequences': policies[rho < 1], 'losses': losses})
summary = {method: mean([r['losses'][method] for r in later]) for method in later[0]['losses']}
assert summary['myopic_diagnostic'] == F(9, 128)
assert all(value == 0 for method, value in summary.items() if method != 'myopic_diagnostic')
result = {'status': 'PASS_FALSIFIER_NO_NOVELTY_OR_BIOLOGICAL_GAIN', 'source_tasks': 4, 'later_tasks': 4,
          'mean_terminal_normalized_squared_errors': summary, 'later': later,
          'costs': {'shared_source_trajectories': 16, 'shared_source_edit_and_score_calls': 32,
                    'source_base_scores': 4, 'source_functional_observations': 12,
                    'later_functional_observations_including_terminal': 16,
                    'later_edit_and_feedback_scores_per_search_method': 8,
                    'later_direct_fits': 4, 'source_data_available_to_every_method': True,
                    'note': 'Synthetic logical observations are not authenticated physical assay bundles. Source costs are included, not amortized away. Compiled direct refit may use fewer evaluations.'},
          'checkpoint_sha256': hashlib.sha256(checkpoint.encode()).hexdigest(),
          'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scope': 'Continuation law was learned from synthetic source outcomes, but exact source-best full program and direct refit already solve later family. No independent empirical Level3 claim.'}
(OUT / 'RESULT.json').write_text(json.dumps(result, default=serialize, indent=2), encoding='utf8')
print(json.dumps({k: v for k, v in result.items() if k != 'later'}, default=serialize, indent=2))
