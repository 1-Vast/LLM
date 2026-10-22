"""Exact synthetic event current and common-rate falsifier; no biological inputs."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform

OUT=Path('D:/MAESTRO/log/20261022/mechanism_gap/frontier')

def history(start, events):
    live=list(start)
    births=[0,0]; deaths=[0,0]; forward=0; backward=0
    for kind,state,count in events:
        if kind=='birth':
            live[state]+=count; births[state]+=count
        elif kind=='death':
            live[state]-=count; deaths[state]+=count
        elif kind=='switch':
            live[state]-=count; live[1-state]+=count
            if state==0: forward+=count
            else: backward+=count
        else: raise ValueError(kind)
        assert min(live)>=0
    estimate=live[1]-start[1]-births[1]+deaths[1]
    assert estimate==forward-backward
    return dict(start=list(start),end=live,births=births,deaths=deaths,
                total_births=sum(births),total_deaths=sum(deaths),
                net_current=estimate,gross_crossing=forward+backward)

def solve_first_two(j):
    # Ordinary two-rate linear elimination, separately implemented.
    determinant=F(20)*(-20)-F(-10)*10
    q01=(F(j[0])*(-20)-F(-10)*j[1])/determinant
    q10=(F(20)*j[1]-F(j[0])*10)/determinant
    return q01,q10

def main():
    selection_pulse=history((6,4), [('death',0,3),('death',1,1)])
    adaptation_pulse=history((6,4), [('switch',0,2),('death',0,1),('death',1,3)])
    selection_wash=history((3,3), [('birth',0,2),('death',1,2)])
    adaptation_wash=history((3,3), [('birth',0,2),('death',0,2),('switch',1,2)])
    for x,y in ((selection_pulse,adaptation_pulse),(selection_wash,adaptation_wash)):
        assert tuple(x[k] for k in ('start','end','total_births','total_deaths'))==tuple(y[k] for k in ('start','end','total_births','total_deaths'))
        assert x['net_current']==0 and y['net_current']!=0
    hidden_cycles=history((6,4), [('switch',0,2),('switch',1,2),('death',0,3),('death',1,1)])
    assert hidden_cycles['net_current']==selection_pulse['net_current']==0
    assert hidden_cycles['gross_crossing']==4

    flow_checks=0
    for current in range(-6,7):
        feasible=[f+b for f,b in product(range(7),repeat=2) if f-b==current]
        assert min(feasible)==abs(current)
        flow_checks+=1
    s=[(F(20),F(-10)),(F(10),F(-20)),(F(20),F(-20))]
    w=[F(2),F(2),F(-3)]
    assert all(sum(wi*si[k] for wi,si in zip(w,s))==0 for k in (0,1))
    fixed=[sum(x*q for x,q in zip(row,[F(1,5),F(1,5)])) for row in s]
    assert fixed==[2,-2,0]
    assert sum(wi*ji for wi,ji in zip(w,fixed))==0
    varying=[F(4),F(-2),F(2)]
    witness=sum(wi*ji for wi,ji in zip(w,varying))
    assert witness==-2
    rate_pairs=[(F(1,4),F(1,10)),(F(1,5),F(1,5)),(F(1,5),F(1,10))]
    assert [sum(x*q for x,q in zip(row,rates)) for row,rates in zip(s,rate_pairs)]==varying
    comparisons=0
    for raw in product(range(-4,5),repeat=3):
        j=list(map(F,raw))
        q01,q10=solve_first_two(j)
        ordinary_residual=j[2]-20*q01+20*q10
        proposed=sum(wi*ji for wi,ji in zip(w,j))
        assert proposed==-3*ordinary_residual
        comparisons+=1
    zero_but_negative=[F(-2),F(2),F(0)]
    q_negative=solve_first_two(zero_but_negative)
    assert sum(wi*ji for wi,ji in zip(w,zero_but_negative))==0
    assert q_negative==(F(-1,5),F(-1,5))
    result=dict(utc=datetime.now(timezone.utc).isoformat(),
                scope='integer synthetic event ledgers and deterministic expected-flow algebra only',
                event_histories=[selection_pulse,adaptation_pulse,selection_wash,adaptation_wash],
                hidden_gross_cycles=hidden_cycles,
                exact_min_cost_flow_checks=flow_checks,
                exact_common_rate_comparisons=comparisons,
                fixed_rate_sign_reversal=list(map(str,fixed)),
                varying_rate_current=list(map(str,varying)),varying_rate_witness=str(witness),
                zero_witness_negative_rates=list(map(str,q_negative)),
                ordinary_equivalence='same O(1) current; W equals -3 times optimized two-rate residual',
                stochastic_test='NOT_IMPLEMENTED; no iid/conditional occupation claim',
                biological_scalar_decodes=0,predictive_fits=0,
                python=platform.python_version(),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    target=OUT/'CHECK_RESULT.json'
    with target.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
