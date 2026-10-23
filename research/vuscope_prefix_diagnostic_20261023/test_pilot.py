"""Necessary implementation checks on synthetic values only."""
from io import BytesIO
import unittest
from zipfile import ZipFile

import numpy as np

import pilot


class ForecastContract(unittest.TestCase):
    def test_published_surface_and_nested_zero_drift(self):
        p = np.array([1, np.log(100), .1, -1, .5, np.log(10)])
        dose, t = np.array([-2., -1., 0]), np.array([0., 1., 2.])
        upper = 100*2**t/(99+2**t)
        lower = 10*2**(.5*t)/(9+2**(.5*t))
        expected = lower+(upper-lower)/(1+10**(.1*abs(upper-lower)*(dose+1)))
        np.testing.assert_allclose(pilot.surface(p, dose, t), expected)
        np.testing.assert_allclose(pilot.surface(np.r_[p, 0], dose, t, True), expected)

    def test_future_payload_not_decoded_by_prefix_reader(self):
        stream = BytesIO()
        with ZipFile(stream, 'w') as archive:
            archive.writestr('data.txt', 'Vessel\nDate Time\tElapsed\tA1\n2023-01-01\t6\t10\n2023-01-02\t75\tNOT_A_FLOAT\n')
        stream.seek(0)
        with ZipFile(stream) as archive:
            self.assertEqual(pilot.read_rows(archive, 'data.txt', {6}), {6.: {'A1': 10.}})

    def test_logistic_decline_and_zero_safe_direct(self):
        self.assertLess(pilot.logistic(np.array([2.]), 1, np.log(.5))[0], 1)
        hours = np.arange(6, 73, 3, dtype=float)
        y = np.zeros((len(hours), 6))
        for config in pilot.DIRECT:
            prediction = pilot.direct_predict(config, hours, y, np.array([120.]))
            self.assertTrue(np.isfinite(prediction).all())
            self.assertTrue((prediction >= 0).all())


if __name__ == '__main__':
    unittest.main()
