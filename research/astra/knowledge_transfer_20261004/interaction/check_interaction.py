import unittest
import numpy as np
from .learned import centre_by_line,pair_features,state_features,residual_prediction

class Checks(unittest.TestCase):
    def test_global_line_shift_cannot_supply_training_signal(self):
        li=np.repeat(np.arange(4),3)
        x=np.arange(36.).reshape(12,3)
        y=np.repeat([1.,-5.,8.,2.],3)[:,None]
        _,r=centre_by_line(x,y,li)
        np.testing.assert_array_equal(r,np.zeros_like(y))

    def test_target_extreme_state_cannot_change_history_basis(self):
        rng=np.random.default_rng(2)
        ph,tf=rng.normal(size=(8,14)),rng.normal(size=(8,30))
        h1,t1=state_features(ph,ph[0],tf,tf[0])
        h2,t2=state_features(ph,ph[0]*10000,tf,tf[0]*10000)
        np.testing.assert_array_equal(h1,h2)
        self.assertTrue(np.isfinite(t2).all())

    def test_interaction_can_reverse_relative_pair_order(self):
        phi=pair_features(np.eye(2))
        pid=np.tile([0,1],4);li=np.repeat(np.arange(4),2)
        z=np.repeat([-1.,1.,-1.,1.],2)[:,None]
        y=(np.tile([-1.,1.],4)*z[:,0])[:,None]
        a=residual_prediction(phi,pid,z,y,li,np.array([0,1]),np.array([1.]))
        b=residual_prediction(phi,pid,z,y,li,np.array([0,1]),np.array([-1.]))
        self.assertGreater(float(a[1,0]-a[0,0]),0)
        np.testing.assert_allclose(a,-b)

if __name__=='__main__':unittest.main(verbosity=2)
