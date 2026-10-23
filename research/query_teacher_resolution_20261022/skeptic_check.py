"""Independent fixed-state teacher check, numpy only; no biological input."""
from pathlib import Path
import json,hashlib
import numpy as np
out=Path('log/20261022/query_teacher_resolution/skeptic')
A=np.array([[.3,-.4],[.2,.5]]); b=np.array([.7,-.2]); k=np.array([1.,0.]); y=.8
P=np.array([[.2,-.1,.3,-.2,.4,-.3],[-.3,.2,-.1,.4,.1,.2]])
eta=.3
u=A@k; h=np.tanh(u); error=y-b@h
z=np.concatenate((k,u,b)); r=np.tanh(P@z)
def step(p,eta_b=0.):
 r=np.tanh(p@z)
 return A+eta*error*np.outer(r,k),b+eta_b*error*h
orth=np.array([0.,1.]); before=float(b@np.tanh(A@orth)); queries=[]
for pp in (P,-P,np.zeros_like(P),P*10):
 aa,bb=step(pp)
 np.testing.assert_array_equal(aa@orth,A@orth)
 assert float(bb@np.tanh(aa@orth))==before
 queries.append(float(bb@np.tanh(aa@orth)))
aa,bb=step(P,.2)
expected=float((bb-b)@np.tanh(A@orth));actual=float(bb@np.tanh(aa@orth)-before)
np.testing.assert_allclose(expected,actual,atol=1e-16)
q=np.array([.6,.8]); target=-.1
def risk(p):
 aa,_=step(p); pred=b@np.tanh(aa@q);return .5*(pred-target)**2
anew,_=step(P);uq=anew@q;hq=np.tanh(uq);pred=b@hq
v=(pred-target)*b*(1-hq*hq)*eta*error*(k@q)*(1-r*r)
analytic=np.outer(v,z)
fd=np.zeros_like(P);dh=1e-6
for idx in np.ndindex(P.shape):
 pp=P.copy();pm=P.copy();pp[idx]+=dh;pm[idx]-=dh
 fd[idx]=(risk(pp)-risk(pm))/(2*dh)
assert np.max(np.abs(fd-analytic))<1e-9
report=dict(scope='Fixed artificial teacher geometry and exact analytic outer derivative vs finite differences; no performance or prior-art proof',
 A=A.tolist(),b=b.tolist(),k=k.tolist(),P=P.tolist(),orthogonal_query=orth.tolist(),
 orthogonal_outputs_for_four_teachers=queries,head_only_orthogonal_change=actual,
 outer_gradient_max_abs_difference=float(np.max(np.abs(fd-analytic))),outer_gradient_norm=float(np.linalg.norm(analytic)),
 full_target_detach_teacher_gradient='zero if no other P path; incompatible with the nonzero intended gradient',
 protocol_sha256=hashlib.sha256((out/'PROTOCOL.md').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (out/'CHECK.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
