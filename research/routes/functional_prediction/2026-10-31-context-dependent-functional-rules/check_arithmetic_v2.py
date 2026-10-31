"""Small arithmetic/access checks on artificial arrays; no biological file reads."""
import json
import numpy as np
import experiment_v2 as e

assert e.fold('A','B') == e.fold('B','A')
values = np.array([-100.,-5.,-1.,0.,.2,5.,100.])
for lam in e.GRID:
    assert np.allclose(e.inverse(e.transform(values,lam),lam),values,rtol=1e-11,atol=1e-11)

ut = np.zeros((4,4))
target = np.full((4,4),np.nan)
ntc = np.array([2,3])
mask = np.ones((4,4),dtype=bool)
ut[0,2:] = ut[2:,0] = -1
ut[1,2:] = ut[2:,1] = -1
ut[0,1] = ut[1,0] = -3
target[2:,2:] = 0
target[0,2:] = target[2:,0] = -2
target[1,2:] = target[2:,1] = -1
q,pred = e.predict_matrix(ut,target,2.,mask,ntc)
assert np.allclose(pred[0,1],-5) and np.allclose(q[0,1],-1)
q_identity,_ = e.predict_matrix(ut,target,1.,mask,ntc)
assert np.allclose(q_identity,0,atol=1e-12)
poisoned = target.copy()
poisoned[:2,:2] = 100
q_poison,_ = e.predict_matrix(ut,poisoned,2.,mask,ntc)
assert np.allclose(q_poison,q,equal_nan=True)

# Exact Y-to-D cancellation with nonzero NTC offsets and an asymmetric control matrix.
rng = np.random.default_rng(7)
counts = rng.integers(50,1000,size=(4,4,4)).astype(float)
y0 = e.endpoint(counts,1,1.,mask,ntc)
y1 = e.endpoint(counts,2,1.,mask,ntc)
a,b,n = e.controls(y1-y0,mask,ntc)
q_y = y1-y0-a[:,None]-b[None,:]+n
assert np.allclose(q_y,e.q_label(counts,2,1.,mask,ntc),atol=1e-12)

active = np.array([[False,True],[True,False]])
assert np.allclose(e.aggregate(np.array([[0.,2.],[6.,0.]]),active,np.array([0,0]),np.array([2])),[4])
print(json.dumps({'status':'PASS','scope':'Synthetic inversion, constructive example, identity Q=0, forbidden target-double poison, raw-Q algebra, orientation averaging; no biological validation'}))
