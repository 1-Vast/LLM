"""Exact fixed-design diagnostic; not a biological experiment or numerical fit."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/feedback_shift_mechanism/constructive'


def empirical_minimum(data,weights):
    total=sum(weights)
    theta=sum(w*y for (_,y),w in zip(data,weights))/total
    derivative=sum(w*(theta-y) for (_,y),w in zip(data,weights))*2/total
    assert derivative == 0
    return dict(theta=str(theta),query_squared_risk=str((theta-F(1))**2),
                objective_derivative=str(derivative),weight_sum=str(total))


if __name__ == '__main__':
    freeze=json.loads((OUT/'MATH_FREEZE.json').read_text())
    for name,expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected
    destination=OUT/'MATH_RESULT.json'
    assert not destination.exists(), 'Preserve the original run'
    old=[(F(1),F(1)),(F(-1),F(-1))]
    expanded=old+[(F(-1),F(-1))]*8
    assert all(x==y for x,y in expanded)
    weights=[F(10) if x==1 else F(0) for x,y in expanded]
    assert sum(weights)==10
    results=dict(kind='exact_fixed_design_math_not_biology',conditional_law='y=x unchanged',
                 query_distribution={'+1':'1','-1':'0'},
                 old_observations=[[str(x),str(y)] for x,y in old],
                 added_observations=[['-1','-1']]*8,
                 old_unweighted=empirical_minimum(old,[F(1)]*2),
                 expanded_unweighted=empirical_minimum(expanded,[F(1)]*10),
                 ordinary_oracle_weighted=empirical_minimum(expanded,weights),
                 scope='Counterexample to inferring conditional shift from a worsening update; not a proposed-QP performance test')
    assert results['old_unweighted']['query_squared_risk']=='1'
    assert results['expanded_unweighted']['query_squared_risk']=='81/25'
    assert results['ordinary_oracle_weighted']['query_squared_risk']=='0'
    destination.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
