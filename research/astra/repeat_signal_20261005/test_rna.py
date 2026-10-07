import numpy as np
from .rna_test import fitted,baselines

def test_rna_zero_context_returns_same_direction_baseline():
    y=np.arange(24.).reshape(6,4)/24;h=(y>.5).astype(float);r=np.array([1,0,3,2])
    p=fitted(y,h,np.zeros((6,2)),np.zeros((3,2)),r)
    b=baselines(y,h,r)
    assert all(np.allclose(v,b['same_y']) for k,v in p.items() if k.startswith('rna_'))

def test_rna_learns_opposite_candidate_effects():
    x=np.linspace(-1,1,30)[:,None];y=np.c_[x[:,0],-x[:,0]];h=(y>0).astype(float)
    p=fitted(y,h,x,np.array([[-1.],[1.]]),np.array([1,0]))['rna_1']
    assert p[1,0]>p[0,0] and p[1,1]<p[0,1]
