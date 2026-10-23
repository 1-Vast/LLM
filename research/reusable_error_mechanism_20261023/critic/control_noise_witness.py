"""Exact observation counterexample; no cell-data inference."""
from fractions import Fraction as F
import json
from pathlib import Path

def h(a,b):
    return -((a>0)-(a<0))*min(abs(a),abs(b)) if a*b>0 else F(0)

# True baseline/single/double are all10: true effects/interactions zero.
# Every distinct gem control estimate has a shared systematic bias c.
# No same random control measurement is reused across input/target gems.
c = F(1,2)
input_single_a = input_single_b = -c
target_residual = c
assert h(input_single_a,input_single_b)==target_residual
# Independent symmetric, zero-mean input/target control errors do not
# create expected h*r covariance in this null example.
expected = sum(h(-ei,-ei)*et for ei in [F(-1),F(1)] for et in [F(-1),F(1)])/4
assert expected==0
out={'true_biological_mixed_effect':'0', 'systematic_control_bias':str(c),
     'input_h':str(h(input_single_a,input_single_b)),'target_residual':str(target_residual),
     'apparent_overlap_theta':'1','independent_symmetric_control_error_E_hr':str(expected),
     'scope':'Exact conditional counterexample only; requires shared systematic control bias across distinct gems. It does not assert such bias in MAESTRO or reuse the same random control sample.'}
root=Path(__file__).resolve().parents[3]
(root/'log/20261023/reusable_error_mechanism/critic/CONTROL_NOISE_WITNESS.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
