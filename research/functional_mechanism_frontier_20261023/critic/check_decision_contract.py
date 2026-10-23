"""Exact boundary between action-set coverage and a drug nomination decision."""
import json
from pathlib import Path
from fractions import Fraction as F

true_utility={'A':F(1),'B':F(0)}
predicted={'A':F(2,5),'B':F(9,10)}
prediction_set=['A','B']
best=max(true_utility,key=true_utility.get)
nominated=max(prediction_set,key=predicted.get)
set_loss=int(best not in prediction_set)
decision_loss=true_utility[best]-true_utility[nominated]
assert set_loss==0 and decision_loss==1
assay_then_choose=max(prediction_set,key=true_utility.get)
assert true_utility[assay_then_choose]==true_utility[best]
out={'set_miscoverage':set_loss,'predicted_argmax_regret':str(decision_loss),
     'assays_needed_to_choose_actual_best_from_set':len(prediction_set),'budget':1,
     'all_set_assays_exceed_budget':len(prediction_set)>1,
     'scope':'Deterministic logical boundary, not conformal theorem refutation, empirical risk, drug efficacy or a fitted algorithm.'}
root=Path(__file__).resolve().parents[3]
(root/'log/20261023/functional_mechanism_frontier/critic/DECISION_CONTRACT_CHECK.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
