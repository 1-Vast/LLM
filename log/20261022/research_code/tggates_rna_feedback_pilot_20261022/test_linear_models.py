"""Numerical identities and fold ownership; fixtures contain no biological values."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from linear_models import Blocks,Ridge,ReducedRidge,RBF

class NumericalTests(unittest.TestCase):
    def setUp(self):
        self.rng=np.random.default_rng(15079)
        self.x=self.rng.normal(size=(12,7));self.y=self.rng.normal(size=(12,5))
        self.q=self.rng.normal(size=(4,7))

    def test_dual_matches_primal_and_unpenalized_intercept(self):
        model=Ridge().fit([self.x],self.y,.3)
        x=model.transformer.transform([self.x]);q=model.transformer.transform([self.q])
        a=np.linalg.solve((x-x.mean(0)).T@(x-x.mean(0))+12*.3*np.eye(7),
                          (x-x.mean(0)).T@(self.y-self.y.mean(0)))
        np.testing.assert_allclose(model.predict([self.q]),self.y.mean(0)+(q-x.mean(0))@a,atol=1e-12)

    def test_full_rank_reduced_ridge_equals_ridge(self):
        full=Ridge().fit([self.x],self.y,.3)
        reduced=ReducedRidge().fit([self.x],self.y,.3,5,[1])
        np.testing.assert_allclose(full.predict([self.q]),reduced.predict([self.q]),atol=1e-12)

    def test_weighted_dual_matches_weighted_primal(self):
        w=np.arange(1,13,dtype=float)
        m=Ridge().fit([self.x],self.y,.3,w)
        x=m.transformer.transform([self.x]);q=m.transformer.transform([self.q])
        xc=x-np.average(x,axis=0,weights=w);ym=np.average(self.y,axis=0,weights=w)
        a=np.linalg.solve(xc.T@(xc*w[:,None])+12*.3*np.eye(7),xc.T@((self.y-ym)*w[:,None]))
        np.testing.assert_allclose(m.predict([self.q]),ym+(q-m.xmean)@a,atol=1e-12)

    def test_no_test_row_influences_transform_or_fit(self):
        before=Ridge().fit([self.x],self.y,.3).predict([self.q[:1]])
        altered=self.q.copy();altered[1:]*=1e9
        after=Ridge().fit([self.x],self.y,.3).predict([altered])[:1]
        np.testing.assert_allclose(before,after,atol=1e-12)

    def test_rank_bound_and_constant_block(self):
        m=ReducedRidge().fit([self.x,np.ones((12,2))],self.y,.3,1,[1,0])
        pred=m.predict([self.q,np.ones((4,2))])-m.ymean
        self.assertLessEqual(np.linalg.matrix_rank(pred,tol=1e-10),1)
        self.assertTrue(np.isfinite(pred).all())

    def test_rbf_constant_target_and_constant_input(self):
        m=RBF().fit([np.ones((12,3))],np.ones((12,2)),.3,.5)
        np.testing.assert_allclose(m.predict([np.ones((4,3))]),1)

    def test_sequential_linear_correction_collapses_exactly(self):
        # Independent explicit collapsed expression checks no hidden nonlinear claim.
        p,q=7,2; u=self.rng.normal(size=(4,p));v=self.rng.normal(size=(4,q))
        f=self.rng.normal(size=(4,p));cx=self.rng.normal(size=(p,p));cy=self.rng.normal(size=(q,q))
        g=self.rng.normal(size=(p,q));b=self.rng.normal(size=q)
        sequential=(f+u@cx)@g+b+v@cy
        collapsed=f@g+b+u@(cx@g)+v@cy
        np.testing.assert_allclose(sequential,collapsed,atol=1e-12)

    def test_svd_sign_changes_cancel_in_low_rank_prediction(self):
        from unittest.mock import patch
        original=np.linalg.svd
        a=ReducedRidge().fit([self.x],self.y,.3,2,[1]).predict([self.q])
        def flipped(x,**kwargs):
            u,s,vt=original(x,**kwargs)
            signs=np.where(np.arange(len(s))%2,-1.,1.)
            return u*signs,s,vt*signs[:,None]
        with patch('numpy.linalg.svd',flipped):
            b=ReducedRidge().fit([self.x],self.y,.3,2,[1]).predict([self.q])
        np.testing.assert_allclose(a,b,atol=1e-12)

if __name__=='__main__':unittest.main()
