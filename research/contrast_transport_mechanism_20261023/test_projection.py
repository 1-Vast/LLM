"""Synthetic verification of the descriptive estimand, no real outcomes."""
import unittest
import numpy as np

from project_signal import basis, decompose, make_design


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(237)
        self.z = np.column_stack((np.ones(20), self.rng.normal(size=(20, 3))))

    def test_additive_is_not_false_residual_signal(self):
        values = self.z @ self.rng.normal(size=(4, 2))
        result, _ = decompose(self.z, values)
        self.assertIsNone(result['residual_correlation'])
        self.assertFalse(result['screen'])
        self.assertLess(abs(result['residual_fraction']), 1e-25)

    def test_residual_and_mixed_covariance(self):
        q, _, _ = basis(self.z)
        noise = self.rng.normal(size=20)
        residual = noise - q @ (q.T @ noise)
        additive = self.z[:, 1] - self.z[:, 1].mean()
        for weight in [0., 1.]:
            with self.subTest(weight=weight):
                values = np.column_stack((weight*additive+residual, weight*additive+2*residual))
                result, _ = decompose(self.z, values)
                expected = 2*(residual @ residual) / (weight**2*(additive @ additive)+2*(residual @ residual))
                self.assertAlmostEqual(result['residual_fraction'], expected)
                self.assertAlmostEqual(result['residual_correlation'], 1.)

    def test_signed_shares_not_clipped(self):
        q, _, _ = basis(self.z)
        v = self.rng.normal(size=20)
        e = v - q @ (q.T @ v)
        a = self.z[:, 1] - self.z[:, 1].mean()
        a *= np.linalg.norm(e) / (2*np.linalg.norm(a))
        result, _ = decompose(self.z, np.column_stack((a+e, -a+e)))
        self.assertGreater(result['residual_fraction'], 1)
        self.assertLess(result['additive_fraction'], 0)

    def test_constant_and_zero_covariance(self):
        result, _ = decompose(self.z, np.ones((20, 2)))
        self.assertIsNone(result['original_correlation'])
        self.assertIsNone(result['residual_correlation'])
        self.assertIsNone(result['residual_fraction'])
        self.assertFalse(result['screen'])
        result, _ = decompose(self.z, np.zeros((20, 2)))
        self.assertIsNone(result['residual_fraction'])

    def test_balanced_role_guide_design_and_abort(self):
        # Four canonical actions, including an equal-weight mirrored-action analogue.
        gene = np.array([[1., 1., 0.], [.5, .5, 1.], [0., 1., 1.], [1., 0., 1.]])
        guide = np.repeat(gene/3, 3, axis=1)
        labels = dict(role_gene=['L:A', 'R:B', 'L:C'],
                      role_guide=[f'{g}:g{k}' for g in ['L:A', 'R:B', 'L:C'] for k in range(3)])
        labels['guide_parent'] = {h: h.rsplit(':', 1)[0] for h in labels['role_guide']}
        design = make_design(gene, guide, labels)
        np.testing.assert_allclose(design[:, 1:], gene[::2]-gene[1::2])
        guide[0, 0] += .01
        with self.assertRaises(AssertionError):
            make_design(gene, guide, labels)


if __name__ == '__main__':
    unittest.main(verbosity=2)
