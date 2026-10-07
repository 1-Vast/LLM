"""Focused synthetic checks; execute before metadata freeze, with no assay data."""
from __future__ import annotations
import unittest
import numpy as np
import pandas as pd

from .build_knowledge import resolver, signed_operator
from .model import history_lines, pair_kernel, transfer
from research.astra.confirmation_campaign_20261004.design import campaign as c


class Invariants(unittest.TestCase):
    def test_directed_signed_propagation_does_not_reverse_edges(self):
        op, n, conflicts = signed_operator(['A','B','C'], [('A','B',1),('B','C',-1)])
        first = np.array([[1.,0.,0.]]) @ op
        np.testing.assert_array_equal(first, [[0,1,0]])
        np.testing.assert_array_equal(first @ op, [[0,0,-1]])
        np.testing.assert_array_equal(np.array([[0.,0.,1.]]) @ op, [[0,0,0]])

    def test_conflicting_signs_and_complexes_are_not_flattened(self):
        op, n, conflicts = signed_operator(['A','B','C'],
            [('A','B',1),('A','B',-1),('A_B','C',1)])
        self.assertEqual(n, 0)
        self.assertEqual(conflicts, 1)
        self.assertEqual(op.nnz, 0)

    def test_ambiguous_alias_is_not_a_mapping(self):
        frame = pd.DataFrame({'symbol':['A','B','C'], 'alias_symbol':['X|C','X','Z'],
                              'prev_symbol':['','','']})
        r = resolver(frame)
        self.assertEqual(r('X'), (None,'ambiguous_alias'))
        self.assertEqual(r('C'), ('C','approved_symbol'))
        self.assertEqual(r('Z'), ('C','unambiguous_hgnc_alias'))

    def test_pair_symmetry_psd_and_nonadditive_capacity(self):
        pairs = [('A','B'),('A','C'),('D','B'),('D','C')]
        k = pair_kernel(np.eye(4), pairs, ['A','B','C','D'])
        reverse = pair_kernel(np.eye(4), [(b,a) for a,b in pairs], ['A','B','C','D'])
        np.testing.assert_allclose(k, reverse)
        self.assertGreater(np.linalg.eigvalsh(k).min(), 0)
        score = transfer(k, [0,1,2,3], [1,0,0,1])
        self.assertGreater(score[0]-score[1]-score[2]+score[3], .01)

    def test_constant_history_has_no_spurious_signal(self):
        k = np.full((4,4), .2) + .8*np.eye(4)
        np.testing.assert_allclose(transfer(k, [0,0,1], [.2,.2,.2]), .2)
        with self.assertRaises(ValueError):
            transfer(k, [], [])

    def test_history_excludes_target_and_nested_samples(self):
        hd = ['L'+str(i) for i in range(20)]
        small = history_lines(hd, 'L3', 4, 11, 1)
        large = history_lines(hd, 'L3', 8, 11, 1)
        self.assertNotIn('L3', large)
        self.assertTrue(set(small) <= set(large) <= set(hd))
        self.assertEqual(len(small),4)

    def test_future_outcome_poisoning_leaves_history_prediction_unchanged(self):
        lines = ('H1','H2','E')
        a = dict(y_s=np.arange(12.), y_v=np.arange(12.),
                 h_s=np.array([0,1,0,0,1,0,0,0,0,1,0,1],bool),
                 h_v=np.array([0,1,1,0,1,0,0,0,1,1,0,1],bool))
        full = c.TissueData('Breast',1,lines,np.repeat(np.arange(3),4),np.tile(np.arange(4),3),
                           [['A','B'],['A','C'],['D','B'],['D','C']]*3,
                           {r:{k:v.copy() for k,v in a.items()} for r in c.ROLES},
                           present_lines=frozenset(lines))
        h = c.restrict(full, lines[:2])
        t1 = c.make_target(full,h,'E','SV',allowed_history=lines[:2],forbidden=['E'])
        for role in c.ROLES:
            for key in ('h_s','h_v'):
                full.arrays[role][key][-4:] = ~full.arrays[role][key][-4:]
        t2 = c.make_target(full,h,'E','SV',allowed_history=lines[:2],forbidden=['E'])
        np.testing.assert_array_equal(t1.scores['C_mean'][0],t2.scores['C_mean'][0])
        with self.assertRaises(AssertionError):
            c.make_target(full,full,'E','SV',allowed_history=lines)


if __name__ == '__main__':
    unittest.main(verbosity=2)
