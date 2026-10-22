"""Additional check after original seal; does not rewrite initial result."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
from trace_credit_check import events, conditional_score

rows = list(events())
checks = 0
for r in rows:
    reward_score = conditional_score(rows, lambda t: (t['z'], t['reward']), (r['z'], r['reward']))
    full_score = conditional_score(rows, lambda t: (t['z'], t['w']), (r['z'], r['w']))
    assert reward_score == full_score
    checks += 1

# Known policy likelihood times unknown-to-agent physical response likelihood.
# Physical transitions cancel when conditioned on the actual logged action.
history_checks = 0
for action in (0, 1):
    for response in (0, 1):
        pa = [F(1, 4), F(3, 4)] if action else [F(3, 4), F(1, 4)]
        py = F(4, 5) if action == response else F(1, 5)
        posterior_with_env = pa[1] * py / sum(p * py for p in pa)
        posterior_policy_only = pa[1] / sum(pa)
        assert posterior_with_env == posterior_policy_only
        history_checks += 1

p = Path('log/20261022/operator_renewal/recursive')
r = {'reward_condition_full_score_equalities': checks, 'action_history_environment_cancellations': history_checks,
     'qualification': 'In this toy reward deterministically identifies w. This does not imply biological rewards identify hidden state. History cancellation requires the same response law given logged actions across policies.',
     'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(p / 'REWARD_CONDITION_CHECK.json').write_text(json.dumps(r, indent=2), encoding='utf-8')
print(json.dumps(r, indent=2))
