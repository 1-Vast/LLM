"""Exact moments of stipulated log-count dynamics, not biological data or fitting."""
from fractions import Fraction as F
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'log/20261023/functional_transition_law/critic'

# z(t)=r*t+k*t*(t-1)/2; z1=r+e1,z2=2r+k+e2,z3=3r+3k.
# Cov(r,k)=I, Cov(e)=I. Frozen source-prior posterior update:
# K=(I+H'H)^-1 H'=[[1/4,1/4],[-1/4,1/4]].
H = ((F(1), F(0)), (F(2), F(1)))
K = ((F(1,4), F(1,4)), (F(-1,4), F(1,4)))
late = (F(3), F(3))
weights = tuple(sum(late[i]*K[i][j] for i in range(2)) for j in range(2))
assert weights == (0, F(3,2))

def risk(w, var_r=F(1), var_k=F(1)):
    coeff_r = w[0]+2*w[1]-3
    coeff_k = w[1]-3
    return coeff_r**2*var_r+coeff_k**2*var_k+w[0]**2+w[1]**2

rows = []
for vk in (F(1), F(9)):
    row = dict(curvature_variance=str(vk),
               ordinary_joint_refit_risk=str(risk((F(-3), F(3)), var_k=vk)),
               inherited_innovation_risk=str(risk(weights, var_k=vk)),
               same_prior_bayes_risk=str(risk(weights, var_k=vk)),
               direct_conditional_predictor_risk=str(risk(weights, var_k=vk)))
    rows.append(row)
assert rows[0]['ordinary_joint_refit_risk'] == '18'
assert rows[0]['inherited_innovation_risk'] == '9/2'
assert rows[1]['inherited_innovation_risk'] == '45/2'
assert risk(weights, var_k=9) > risk((F(-3), F(3)), var_k=9)

report = dict(rows=rows, update_matrix=[[str(v) for v in row] for row in K],
              late_output_weights=list(map(str, weights)),
              interpretation='Finite-sample prior gain matched by Bayes/direct conditional prediction; shift can reverse it.',
              biological_data_read=False, fits=0)
(OUT/'TEMPORAL_INNOVATION_RESULT.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
