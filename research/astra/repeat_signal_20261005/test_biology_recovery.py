import numpy as np
import pandas as pd
from .recover_biology import learn,blend,shuffle_rows,features

def test_dual_matches_primal_and_opposite_effects():
    x=np.linspace(-1,1,20)[:,None];h=np.c_[(x[:,0]>0).astype(float),(x[:,0]<0).astype(float)]
    z=np.array([[-1.],[1.]]);prior=np.array([.5,.5]);got=learn(h,x,z,prior)[1.]
    xx=(x-x.mean(0))/x.std(0);zz=(z-x.mean(0))/x.std(0)
    want=prior+zz@np.linalg.solve(xx.T@xx+np.eye(1),xx.T@(h-prior))
    assert np.allclose(got,want,atol=1e-12) and got[1,0]>got[0,0] and got[1,1]<got[0,1]

def test_whole_missing_cell_falls_back():
    h=np.arange(12.).reshape(6,2)%2;x=np.arange(12.).reshape(6,2);z=np.array([[np.nan,np.nan],[1.,2.]])
    got=learn(h,x,z,np.array([.4,.5]))[1.];assert np.isnan(got[0]).all()
    b=np.array([.7,.1]);assert np.array_equal(blend(b,got[0],1.),blend(b,got[0],0.))

def test_train_only_imputation():
    h=np.array([[0.,1.],[1.,0.],[1.,0.],[0.,1.]]);x=np.array([[1.,np.nan],[2.,np.nan],[3.,np.nan],[4.,np.nan]])
    got=learn(h,x,np.array([[2.5,np.nan],[4.,np.nan]]),np.array([.5,.5]))[10.]
    assert np.isfinite(got).all() and np.allclose(got[0],[.5,.5])

def test_shuffle_preserves_missing_cells():
    x=np.array([[1.,2.],[np.nan,np.nan],[3.,4.],[5.,6.]]);z=shuffle_rows(x,17)
    assert np.isnan(z[1]).all() and sorted(map(tuple,z[[0,2,3]]))==sorted(map(tuple,x[[0,2,3]]))

def test_compound_target_union():
    frames={'dependency':pd.DataFrame({'G1':[-1.],'G2':[-.2]},index=['cell'])}
    x=features('target_dependency',['cell'],[('t','A|B','A'),('t','unknown','B')],frames,{'A':['G1'],'B':['G1','G2']})
    assert np.allclose(x[0,0],[-.6,-1.,-1.,-1.,.6,1.]) and np.isnan(x[0,1,[0,1,4,5]]).all()
