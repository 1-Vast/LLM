"""Synthetic checks only: never read the real response archive."""
import unittest
from forecast import predict_batch, forecast_campaign


class Isolation(unittest.TestCase):
    def setUp(self):
        self.initial = [dict(seq='a', t0=0., t1=0., cv=2.),
                        dict(seq='b', t0=1., t1=1., cv=4.)]
        self.queries = [dict(seq='a', t0=0.5, t1=0.5)]

    def test_query_labels_and_g1_identity(self):
        result = predict_batch(self.initial, list(self.initial), self.queries, ('a', 'b', 'c'))
        for method in ('ridge', 'mean', 'nn'):
            self.assertEqual(result['frozen_' + method], result['cumulative_' + method])
        with self.assertRaises(ValueError):
            predict_batch(self.initial, self.initial, [dict(self.queries[0], cv=100)], ('a', 'b'))

    def test_future_feedback_not_earlier_prediction(self):
        rows = [dict(r, gen=0, number=i+1) for i, r in enumerate(self.initial)]
        rows += [dict(seq='a', t0=0.2, t1=0.3, cv=3., gen=1, number=1),
                 dict(seq='b', t0=0.4, t1=0.5, cv=5., gen=2, number=1),
                 dict(seq='a', t0=0.8, t1=0.7, cv=7., gen=3, number=1)]
        original = forecast_campaign('synthetic', rows, ('a', 'b'), 4)
        changed = [dict(r, cv=-100000.) if r['gen'] >= 2 else dict(r) for r in rows]
        later = forecast_campaign('synthetic', changed, ('a', 'b'), 4)
        self.assertEqual(original[:2], later[:2])
        self.assertEqual(original[2]['predictions']['frozen_ridge'], later[2]['predictions']['frozen_ridge'])
        self.assertNotEqual(original[2]['predictions']['cumulative_ridge'], later[2]['predictions']['cumulative_ridge'])


if __name__ == '__main__':
    unittest.main()
