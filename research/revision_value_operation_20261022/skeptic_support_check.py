"""Exact identification counterexample; no dataset access."""
from fractions import Fraction as F
from pathlib import Path
import json, hashlib, subprocess, sys
out=Path('log/20261022/revision_value_operation/skeptic')
pi0=(F(1),F(0)); pi1=(F(0),F(1)); delta=tuple(b-a for a,b in zip(pi0,pi1))
mu=(F(1,2),F(1,2))
worlds=[(F(1,2),F(0)),(F(1,2),F(1))]
def dr(a,y,q):
    base=sum(d*m for d,m in zip(delta,mu))
    return base+delta[a]*(y-mu[a])/q[a]
records=[]
for y in worlds:
    true=sum(d*v for d,v in zip(delta,y))
    q=(F(1),F(0))
    logged_dr=dr(0,y[0],q)
    qrand=(F(1,2),F(1,2))
    expected=sum(qrand[a]*dr(a,y[a],qrand) for a in range(2))
    ips=sum(qrand[a]*delta[a]*y[a]/qrand[a] for a in range(2))
    assert expected==ips==true
    assert logged_dr==0
    records.append({'world':list(map(str,y)),'logged_action':0,'logged_y':str(y[0]),
                    'true_revision_value':str(true),'unsupported_DR':str(logged_dr),
                    'randomized_DR_expectation':str(expected),'randomized_IPS_expectation':str(ips)})
assert records[0]['logged_y']==records[1]['logged_y']
# Known actiona supplies -1/2; uncovered b has coefficient+1 and outcome[0,1].
lo,hi=-F(1,2),F(1,2)
assert all(lo<=sum(d*v for d,v in zip(delta,y))<=hi for y in worlds)
# World2 IPS: samples a => -1/(2(1-eps)), b=>1/eps.
eps=F(1,1000); q=(1-eps,eps); y=worlds[1]
z=[delta[a]*y[a]/q[a] for a in range(2)]
mean=sum(q[a]*z[a] for a in range(2)); variance=sum(q[a]*(z[a]-mean)**2 for a in range(2))
assert mean==F(1,2) and variance>999
res={'scope':'exact artificial support/contrast audit; no biological access','worlds':records,
 'sharp_identification_interval':list(map(str,(lo,hi))),'interval_width':str(hi-lo),
 'epsilon_logging_b':str(eps),'IPS_variance_per_sample':str(variance),
 'minimum_n_for_variance_at_most_0.01':str(variance/F(1,100)),
 'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'python':sys.version,'random_seed':'none; exact enumeration',
 'protocol_sha256':hashlib.sha256((out/'PROTOCOL.md').read_bytes()).hexdigest(),
 'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (out/'EXACT_SUPPORT_CHECK.json').open('x',encoding='utf-8') as f:json.dump(res,f,indent=2)
print(json.dumps(res,indent=2))
