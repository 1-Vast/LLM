"""Synthetic algebra only; no biological inputs, fitting, or protected access."""
import hashlib
import json
from pathlib import Path
import numpy as np

out=Path('log/20261023/function_update_renewal/constructive')
rng=np.random.default_rng(20261023)
d,k,n=7,11,23
W=rng.normal(size=(d,k))
beta=rng.normal(size=d)
features=rng.normal(size=(n,k))
targets=rng.normal(size=n)
effective=W.T@beta
before=features@effective
lam=.7
eta=.3
history=[]
for i in range(5):
 phi=features[i]
 r=targets[i]-beta@W@phi
 denominator=float(beta@beta*(phi@phi)+lam)
 W=W+eta*r*np.outer(beta,phi)/denominator
 effective=effective+eta*r*(beta@beta)*phi/denominator
 difference=float(np.max(np.abs(features@W.T@beta-features@effective)))
 history.append(difference)
 assert difference<1e-12
# Any vector orthogonal to the functional readout makes an invisible state edit.
v=rng.normal(size=d)
v=v-beta*(beta@v)/(beta@beta)
z=rng.normal(size=k)
W2=W+np.outer(v,z)
functional_difference=float(np.max(np.abs(features@W.T@beta-features@W2.T@beta)))
state_difference=float(np.linalg.norm(features@W.T-features@W2.T))
assert functional_difference<1e-12 and state_difference>1
result={
 'scope':'SYNTHETIC_ALGEBRA_NOT_BIOLOGICAL_RESULT',
 'seed':20261023,
 'effective_head_update_max_errors':history,
 'functional_nullspace_max_error':functional_difference,
 'functional_nullspace_state_change_norm':state_difference,
 'conclusion':'Linear shared state-operator revision is scalar normalized residual updating in disguise; functional-only feedback cannot identify its orthogonal state corrections.',
 'biological_files_read':0,'model_fits':0,
}
(out/'OPERATOR_CHECK.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
