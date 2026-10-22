import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reference_assembly import contrast

class ReferenceTests(unittest.TestCase):
    def test_log_then_average_is_not_log_of_average_signal(self):
        state=contrast([['0'],['2']],[['0'],['0']])
        np.testing.assert_array_equal(state,[1.])
        self.assertNotAlmostEqual(float(state[0]),float(np.log2((1+4)/2)))

    def test_decimal_cancellation_and_all_probe_coordinates_retained(self):
        state=contrast([['0.1','-2'],['0.2','4']],[['0.3','1'],['0','1']])
        np.testing.assert_array_equal(state,[0.,0.])
        self.assertEqual(len(state),2)

if __name__=='__main__':unittest.main()
