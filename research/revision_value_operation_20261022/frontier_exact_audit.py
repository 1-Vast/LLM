"""Exact rational finite checks; no biological observations or simulator oracle."""
from fractions import Fraction as F
import itertools
import json
from pathlib import Path

out = Path('log/20261022/revision_value_operation/frontier')
# Identical observational laws with opposite revision values under no overlap.
worlds = [[F(1, 2), F(0)], [F(1, 2), F(1)]]
assert worlds[0][0] == worlds[1][0]
no_overlap_values = [w[1] - w[0] for w in worlds]
assert no_overlap_values == [F(-1, 2), F(1, 2)]

# Only contrast support is required: common policy mass on an unobserved arm cancels.
old = [F(1, 2), F(0), F(1, 2)]
new = [F(0), F(1, 2), F(1, 2)]
diff = [a-b for a,b in zip(new, old)]
q = [F(1, 2), F(1, 2), F(0)]
cases = 0
for means in itertools.product([F(0),F(1,2),F(1)], repeat=3):
    for model in itertools.product([F(0),F(1)], repeat=3):
        target = sum(d*m for d,m in zip(diff,means))
        base = sum(d*m for d,m in zip(diff,model))
        expectation = sum(q[a]*(base + diff[a]/q[a]*(means[a]-model[a])) for a in (0,1))
        assert expectation == target
        # Difference of two ordinary DR scores using zero for unobserved residuals.
        for a in (0,1):
            scores = [sum(p*m for p,m in zip(policy,model)) + policy[a]/q[a]*(means[a]-model[a]) for policy in [new, old]]
            assert scores[0]-scores[1] == base + diff[a]/q[a]*(means[a]-model[a])
        cases += 1

# Choosing a revision with its own evaluation feedback creates bias despite q=1/2.
reuse_mean = F(0)
independent_mean = F(0)
for action, outcome in itertools.product((0,1), repeat=2):
    selected = action if outcome else 1-action
    d_observed = F(int(selected == action)) - F(1,2)
    reuse_mean += F(1,4)*2*d_observed*outcome
    for audit_action, audit_outcome in itertools.product((0,1), repeat=2):
        d_audit = F(int(selected == audit_action)) - F(1,2)
        independent_mean += F(1,16)*2*d_audit*audit_outcome
assert reuse_mean == F(1,2) and independent_mean == 0
result = {
    'status':'PASS',
    'no_overlap':{'same_logged_action0_mean':'1/2','opposite_revision_values':list(map(str,no_overlap_values))},
    'contrast_support':{'old':list(map(str,old)),'new':list(map(str,new)),'logger':list(map(str,q)),'exact_model_mean_cases':cases,'ordinary_DR_difference_equal':True},
    'adaptive_reuse':{'true_value':0,'same_feedback_estimator_expectation':str(reuse_mean),'fresh_audit_estimator_expectation':str(independent_mean),'full_support_known_propensity':True},
    'scope':'Finite synthetic identification/equivalence checks. No biological validation, variance superiority, new estimator, long-horizon claim or trained model.'
}
(out/'EXACT_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
