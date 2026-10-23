"""Exact finite conditional-sign update witness; ordinary baseline, no biology."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/functional_update_operation'


def mse(rows,rule):
    return sum((rule(r,sign)-target)**2 for r,sign,target in rows)/len(rows)


if __name__=='__main__':
    protocol=OUT/'CRITERION_PROTOCOL.md'
    freeze=OUT/'CRITERION_FREEZE.json'
    assert freeze.exists() and not (OUT/'CRITERION_RESULT.json').exists()
    payload=json.loads(freeze.read_text())
    for name,expected in payload['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected
    a=F(3,5)
    rows=[(F(r),F(sign),a*r*sign) for r in [-1,1] for sign in [-1,1]]
    # Both receive the identical lawful pre-feedback covariate sign when present.
    known=mse(rows,lambda r,s:a*s*r)
    none=mse(rows,lambda r,s:F(0))
    fixed=mse(rows,lambda r,s:a*r)
    # Hidden signs occur equally for every observed r. Any deterministic mapping
    # of r to b(r)*r has risk a²+E[b(r)²], minimized by b(r)=0.
    conditional={str(r):sum(t for rr,s,t in rows if rr==r)/2 for r in [F(-1),F(1)]}
    assert known==0 and none==a*a and fixed==2*a*a
    assert set(conditional.values())=={F(0)}
    result=dict(amplitude=str(a),ordinary_known_sign_mse=str(known),no_update_mse=str(none),
        fixed_positive_hidden_sign_mse=str(fixed),conditional_hidden_query_mean={k:str(v) for k,v in conditional.items()},
        best_hidden_sign_mse=str(none),
        loss_identity='For any lawful b(r), risk=a^2+E[b(r)^2]; compare all four equally likely outcomes.',
        scope='criterion audit only; stipulated signs/covariates/targets, not real biological tasks')
    (OUT/'CRITERION_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
