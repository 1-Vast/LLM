"""Checks addressing weighting, sample-size and no-feature-signal failure modes."""
import unittest
import numpy as np
from .conditional import context_weights,weighted_quantities,score_from
from research.astra.confirmation_campaign_20261004.design import campaign as c


class Checks(unittest.TestCase):
    def setUp(self):
        a = dict(y_s=np.array([2.,3.,4.,5.]),y_v=np.array([5.,4.,3.,2.]),
                 h_s=np.array([1,0,0,0],bool),h_v=np.array([1,1,0,0],bool))
        self.h = c.TissueData('Breast',1,('H1','H2'),np.array([0,0,1,1]),np.array([0,1,0,1]),
                             [['A','B'],['A','C']]*2,{r:a for r in c.ROLES},
                             present_lines=frozenset(('H1','H2')))

    def test_uniform_weights_exactly_recover_original_scores(self):
        q = weighted_quantities(self.h,'SV',np.array([0,1]),np.ones(4))
        original = c.predictor_scores(c.history_quantities(self.h,'SV',np.array([0,1])))
        for arm in c.SIMPLE:
            np.testing.assert_allclose(score_from(q,arm),original[arm][0],rtol=0,atol=1e-12)

    def test_weight_scale_does_not_inflate_evidence(self):
        w = np.array([1.,1.,.25,.25])
        q1 = weighted_quantities(self.h,'SV',np.array([0,1]),w)
        q2 = weighted_quantities(self.h,'SV',np.array([0,1]),w*10000)
        for k in q1:
            np.testing.assert_allclose(q1[k],q2[k])
        self.assertTrue((q1['effective_n']<=2).all())

    def test_constant_context_is_uniform_and_target_order_preserved(self):
        for pca in (False,True):
            np.testing.assert_array_equal(context_weights(np.ones((4,7)),np.ones(7),pca=pca),np.ones(4))

    def test_closer_history_gets_more_weight_and_pca_is_finite(self):
        x = np.array([[0.,0.],[1.,2.],[2.,3.],[5.,7.]])
        for pca in (False,True):
            w = context_weights(x,x[0],pca=pca)
            self.assertEqual(int(w.argmax()),0)
            self.assertTrue(np.isfinite(w).all())
            np.testing.assert_allclose(w,context_weights(x*4+8,x[0]*4+8,pca=pca))


if __name__ == '__main__':
    unittest.main(verbosity=2)
