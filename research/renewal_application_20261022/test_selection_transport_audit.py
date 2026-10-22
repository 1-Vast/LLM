import unittest

from selection_transport_audit import MODELS, audit, ordinary_mixture, summarize


class ObservabilityTests(unittest.TestCase):
    def test_explicit_endpoint_and_mass_balance(self):
        expected = {'A|0': 198, 'A|1': 0, 'B|0': 198, 'B|1': 4}
        for events in MODELS.values():
            observed, _ = summarize(events)
            self.assertEqual(observed['initial'], {'A': 200, 'B': 200})
            self.assertEqual(observed['endpoint_state_generation'], expected)
            self.assertEqual(observed['birth_events_total'], 2)
            self.assertEqual(observed['death_events_total'], 2)
            self.assertEqual(observed['endpoint_total'], 400)

    def test_joint_feedback_changes_identifiability(self):
        observed_s, flow_s = summarize(MODELS['selection_only'])
        observed_t, flow_t = summarize(MODELS['state_change'])
        self.assertEqual(observed_s, observed_t)
        self.assertEqual((flow_s['A>B'], flow_t['A>B']), (0, 2))
        self.assertNotEqual(sum(v for k, v in flow_s.items() if k.startswith('A>')),
                            sum(v for k, v in flow_t.items() if k.startswith('A>')))

    def test_static_mixture_is_an_exact_ordinary_reproduction(self):
        observed, _ = summarize(MODELS['selection_only'])
        baseline = ordinary_mixture(observed)
        self.assertEqual(baseline['cycling_given_state'], {'A': '0', 'B': '2/101'})
        self.assertEqual(baseline['reproduced_joint'], observed['endpoint_state_generation'])
        self.assertTrue(all(audit()['checks'].values()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
