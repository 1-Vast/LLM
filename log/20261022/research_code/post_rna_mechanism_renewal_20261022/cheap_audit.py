"""Check three proposed operations; no biological outcomes or fitted models."""
from fractions import Fraction as F
import hashlib,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/post_rna_mechanism_renewal'

def softmax(x):
    a=np.asarray(x,dtype=float);v=np.exp(a-a.max(axis=-1,keepdims=True));return v/v.sum(axis=-1,keepdims=True)

def bayes_query(incumbent,outcomes,cost):
    assert sum(p for _,p in outcomes)==1
    prior=sum(value*p for value,p in outcomes)
    assert incumbent>=prior
    flip=sum(p for value,p in outcomes if value>incumbent)
    evsi=sum(max(incumbent,value)*p for value,p in outcomes)-incumbent
    return dict(prior=prior,flip=flip,evsi=evsi,cost=cost,net=evsi-cost,flip_score=flip/cost)

def main():
    checks={}
    s_low=.5-.5*math.exp(-1);s_high=.5+.5*math.exp(-1)
    checks['lambda0_has_finite_history_memory']=abs((s_high-s_low)-math.exp(-1))<1e-15
    checks['lambda1_strictly_decreasing_no_bistability']=(-1+1/4)<0
    roots=[(1-math.sqrt(1-4/5))/2,.5,(1+math.sqrt(1-4/5))/2]
    drift=lambda s: .5-s+5*s*(1-s)*(s-.5)
    derivative=lambda s: -1+5*(-3*s*s+3*s-.5)
    checks['lambda5_three_equilibria']=max(abs(drift(s)) for s in roots)<1e-15
    checks['lambda5_outer_stable_centre_unstable']=derivative(roots[0])<0<derivative(roots[1]) and derivative(roots[2])<0
    q=np.array([.2,.3,.5]);t0=np.eye(3);t1=np.array([[.1,.8,.1],[.3,.5,.2],[.6,.1,.3]])
    pi=[q@t for t in (t0,t1)]
    counts=[123*softmax(np.log(p)+source) for p,source in zip(pi,([0,0,0],[1,-2,.5]))]
    checks['transport_locations_change']=not np.allclose(pi[0],pi[1])
    checks['normalized_count_total_head_unchanged']=all(abs(c.sum()-123)<1e-12 for c in counts)
    logits=np.array([[1.,-1.,2.],[0.,2.,-3.]])
    checks['only_destination_constant_condition_cancels']=np.allclose(softmax(logits),softmax(logits+7))
    harmful=bayes_query(F(3,5),[(F(61,100),F(1,2)),(F(59,100),F(1,2))],F(1,10))
    b=bayes_query(F(0),[(F(1,1000),F(9,10)),(F(-9,1000),F(1,10))],F(1,100))
    c=bayes_query(F(0),[(F(1),F(1,10)),(F(-1,9),F(9,10))],F(1,100))
    checks['positive_flip_can_have_negative_net_value']=harmful['flip_score']>0 and harmful['evsi']==F(1,200) and harmful['net']<0
    checks['flip_ranking_can_reverse_value_ranking']=b['flip_score']>c['flip_score'] and b['net']<0<c['net'] and b['evsi']<c['evsi']
    def rational(row):return {k:dict(exact=str(v),value=float(v)) for k,v in row.items()}
    result=dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                caf=dict(lambda0_states=[s_low,s_high],history_difference=s_high-s_low,lambda1_max_drift_derivative=-.75,lambda5_equilibria=roots,lambda5_derivatives=[derivative(s) for s in roots]),
                transport=dict(pi=[p.tolist() for p in pi],spatial_bin_counts=[n.tolist() for n in counts],total_counts=[float(n.sum()) for n in counts],total_head=123),
                decision=dict(harmful_query=rational(harmful),candidate_B=rational(b),candidate_C=rational(c)),
                biological_fits=0,biological_values_read=0,reserve_values_read=0)
    with (P/'CHEAP_AUDIT_RESULT.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result));assert all(checks.values())

if __name__=='__main__':main()
