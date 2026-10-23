from fractions import Fraction as F
from math import comb
from pathlib import Path
import json,hashlib
OUT=Path('log/20261022/update_rule_renewal/skeptic')
def tail(n,k):return sum(F(comb(n,j),2**n) for j in range(k,n+1))
records=[]
for ordered,m in ((True,12),(False,6)):
 p=tail(m,m);assert p<F(1,20)
 records.append(dict(ordered_edges=ordered,nodes=4,m=m,binomial_p_all_agree=str(p),
     true_null_acceptance=str(F(1,2)),all_indicators_same_latent_sign=True))
p=tail(8,7);S=7-100
assert p<F(1,20) and S<0
res=dict(edge_dependence=records,
 sign_mismatch=dict(m=8,k=7,p=str(p),S=S,gate_positive_direction=True,applied_sign=-1),
 main_effect=dict(state_error_A=1,state_error_B=0,same_drug_edge_error=1,same_state_edge_error=0),
 scope='Exact synthetic witnesses; no biological outcomes or general empirical dominance claim',
 protocol_sha256=hashlib.sha256((OUT/'ESG_CHECK_PROTOCOL.md').read_bytes()).hexdigest())
with (OUT/'ESG_EXACT_CHECK.json').open('x',encoding='utf-8') as f:json.dump(res,f,indent=2)
print(json.dumps(res,indent=2))
