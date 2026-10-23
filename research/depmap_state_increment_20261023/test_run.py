"""Synthetic information-isolation and estimator checks, no biological data."""
import unittest
import numpy as np
from run import gene_prior,kernel,nested,all_grid


class Invariants(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(71)
        self.lines=np.repeat(['a','b','c','d','e'],4)
        self.genes=np.tile(['g1','g2','g3','g4'],5)
        self.y=rng.normal(size=20)
        self.x=rng.normal(size=(20,3))
        self.grams={name:self.x@self.x.T for name in ['absolute','relative','context']}
        self.qc=rng.normal(size=(20,2))
        self.tr=np.arange(16);self.query=np.arange(16,20)

    def counter(self):
        return dict(eigendecompositions=0,lambda_fits=0)

    def test_outer_query_labels_cannot_select_or_predict(self):
        one=nested(self.y,self.genes,self.lines,self.lines,self.grams,self.qc,self.tr,self.query,self.counter())
        changed=self.y.copy();changed[self.query]+=10000
        two=nested(changed,self.genes,self.lines,self.lines,self.grams,self.qc,self.tr,self.query,self.counter())
        self.assertEqual(one[1],two[1])
        for name in one[0]:np.testing.assert_array_equal(one[0][name],two[0][name])

    def test_inner_validation_labels_not_in_inner_fit(self):
        fit=np.arange(8);val=np.arange(8,16)
        one=all_grid(self.y,self.genes,self.lines,self.grams,self.qc,fit,val,self.counter())
        changed=self.y.copy();changed[val]*=100
        two=all_grid(changed,self.genes,self.lines,self.grams,self.qc,fit,val,self.counter())
        for name in one:np.testing.assert_array_equal(one[name],two[name])
        np.testing.assert_array_equal(gene_prior(self.y,self.genes,fit,fit),gene_prior(changed,self.genes,fit,fit))

    def test_zero_linear_features_return_gene_mean(self):
        zero={k:np.zeros_like(v) for k,v in self.grams.items()}
        out=all_grid(self.y,self.genes,self.lines,zero,np.zeros_like(self.qc),self.tr,self.query,self.counter())
        for name in ['B','C','D','E']:
            np.testing.assert_allclose(out[name],np.repeat(out['A'],5,axis=1),atol=1e-12)

    def test_translation_and_gated_psd(self):
        shifted=self.x+np.array([2.,-4.,9.])
        gram={k:shifted@shifted.T for k in self.grams}
        for name in ['C','D','E','F','H']:
            a,b=kernel(name,self.grams,self.qc,self.genes,self.tr,self.query)
            c,d=kernel(name,gram,self.qc,self.genes,self.tr,self.query)
            np.testing.assert_allclose(a,c,atol=2e-12)
            np.testing.assert_allclose(b,d,atol=2e-12)
            self.assertGreaterEqual(np.linalg.eigvalsh(a).min(),-1e-10)
            if name in ['C','H']:
                np.testing.assert_array_equal(a[self.genes[self.tr,None]!=self.genes[None,self.tr]],0.)


if __name__=='__main__':unittest.main()
