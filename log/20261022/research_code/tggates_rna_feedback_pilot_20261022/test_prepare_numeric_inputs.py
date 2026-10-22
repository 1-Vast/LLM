import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_numeric_inputs import project_function

class NeverCast:
    def __float__(self):raise AssertionError('Forbidden High/Low development cast')

class ProjectionTests(unittest.TestCase):
    def test_development_high_and_low_assays_are_not_cast(self):
        row=dict(compound_label='fixture',block_id='one',role='development',fingerprint_on_bits=[],unit='uM',
            doses={k:dict(concentration='1',mean=[NeverCast(),NeverCast()],sd=[NeverCast(),NeverCast()])
                   for k in ['Low','Middle','High']})
        row['doses']['Middle'].update(mean=['.9','.8'],sd=['.1','.2'])
        projected,casts=project_function([row])
        self.assertEqual(casts,dict(source=0,development=4))
        self.assertNotIn('mean',projected[0]['doses']['High'])
        self.assertNotIn('mean',projected[0]['doses']['Low'])
        self.assertEqual(projected[0]['doses']['Middle']['mean'],[.9,.8])

if __name__=='__main__':unittest.main()
