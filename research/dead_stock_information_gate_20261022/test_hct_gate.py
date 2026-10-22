"""Leakage, physical mean, grouping and observation-unit tests before the gate."""
import copy
from datetime import datetime, timedelta
import unittest

import numpy as np
from scipy.integrate import solve_ivp

from hct_gate import (compartments, features, inner_split, labels, macro,
                      prefix, structure, weights)


def fake_rows():
    origin = datetime(2020, 1, 1, 12)
    rows = []
    for t in range(0, 89, 4):
        for img in ['1', '2', '3']:
            live, dead = 100*2**(.02*t), 10+t
            rows.append({'seed': 'mcer-1e3', 'concentration': '0', 'well': 'A1', 'img': img,
                         'Elapsed': str(t), 'Date Time': (origin+timedelta(hours=t)).strftime('%m/%d/%Y %I:%M:%S %p'),
                         'intersect_live_cells': str(live), 'intersect_dead_cells': str(dead),
                         'tot_cells': str(live+dead)})
    return rows


class GateTests(unittest.TestCase):
    def test_future_readouts_opaque_to_prefix_and_identity(self):
        original = fake_rows()
        g = structure(original)[0]
        p = prefix(g)
        changed = copy.deepcopy(original)
        for r in changed:
            if float(r['Elapsed']) > 24:
                for k in ['intersect_live_cells', 'intersect_dead_cells', 'tot_cells']:
                    r[k] = 'closed_future_not_a_number'
        g2 = structure(changed)[0]
        p2 = prefix(g2)
        for arm in ['live_only', 'dead_initial', 'dead_snapshot', 'dead_history']:
            np.testing.assert_array_equal(features(g, p, arm), features(g2, p2, arm))

    def test_future_dead_and_total_never_needed_for_live_target(self):
        rows = fake_rows()
        for r in rows:
            if float(r['Elapsed']) > 24:
                r['intersect_dead_cells'] = 'closed'
                r['tot_cells'] = 'closed'
        g = structure(rows)
        self.assertAlmostEqual(labels(g, ['0'])[0], np.log2(100*2**1.44+1))
        with self.assertRaisesRegex(ValueError, 'authorization'):
            labels(g, ['12.5'])

    def test_same_image_panel_and_physical_well(self):
        rows = fake_rows()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            structure(rows+[rows[0]])
        with self.assertRaisesRegex(ValueError, 'incomplete_image'):
            structure(rows[1:])
        rows[-1]['seed'] = 'mkate-3e3'
        with self.assertRaisesRegex(ValueError, 'identity_changed'):
            structure(rows)

    def test_mean_observation_not_three_independent_wells(self):
        rows = fake_rows()
        for r in rows:
            if r['Elapsed'] == '0':
                r['intersect_live_cells'] = str(10*int(r['img']))
        groups = structure(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(prefix(groups[0])['L'][0], 20)

    def test_zero_dose_features_and_dead_mask(self):
        g = structure(fake_rows())[0]
        p = prefix(g)
        altered = copy.deepcopy(p)
        altered['D'] *= 5
        altered['z'] = np.log2(altered['D']+1)
        a = features(g, p, 'live_only')
        self.assertTrue(np.all(np.isfinite(a)))
        np.testing.assert_array_equal(a, features(g, altered, 'live_only'))
        self.assertFalse(np.array_equal(features(g, p, 'dead_history'), features(g, altered, 'dead_history')))

    def test_concentration_groups_inner_and_outer_disjoint(self):
        doses = ['0', '.385', '.77', '1.55', '3.125', '6.25', '12.5', '25']
        for outer in doses:
            train, val, historical = inner_split(doses, outer)
            self.assertEqual(len(train), 6)
            self.assertNotIn(outer, historical)
            self.assertNotIn(val, train)
            self.assertEqual(set(train+[val]), set(historical))

    def test_generator_solution_matches_independent_ode_integration(self):
        rng = np.random.default_rng(20261022)
        candidates = [np.r_[rng.uniform(0, .2, 4), rng.uniform(0, 1)] for _ in range(30)]
        candidates += [np.array([.02, .05, .03, .03, .5]), np.array([0., 0., 0., 0., 0.])]
        for pars in candidates:
            b, k, d, c, q = pars
            t = np.array([0., 4., 24., 72.])
            m = np.array([[b-k, 0, 0], [k, -d, 0], [0, d, -c]])
            xx = solve_ivp(lambda tt, yy: m@yy, (0., 72.), [(1-q)*100, q*100, 5.],
                           t_eval=t, rtol=1e-10, atol=1e-10).y.T
            exact = np.c_[xx[:, 0]+xx[:, 1], xx[:, 2]]
            np.testing.assert_allclose(compartments(pars, t, 100, 5), exact, rtol=2e-8, atol=1e-7)

    def test_clearance_does_not_change_live_without_parameter_update(self):
        a = np.array([.03, .05, .02, 0., .2])
        b = a.copy()
        b[3] = .15
        t = np.array([0., 24., 72.])
        aa, bb = compartments(a, t, 100, 50), compartments(b, t, 100, 50)
        np.testing.assert_array_equal(aa[:, 0], bb[:, 0])
        self.assertFalse(np.array_equal(aa[:, 1], bb[:, 1]))

    def test_macro_and_fit_weights_respect_dose_clusters(self):
        keys = [('0', 'a', 'A'), ('1', 'a', 'B')]
        extended = keys+[keys[0]]*8
        score = macro(extended, np.zeros(10), np.array([1., 3.]+[1.]*8))
        self.assertEqual(score['macro_mae'], 2.)
        w = weights(extended)
        self.assertAlmostEqual(w[1], sum(w[i] for i, k in enumerate(extended) if k[0] == '0'))


if __name__ == '__main__':
    unittest.main()
