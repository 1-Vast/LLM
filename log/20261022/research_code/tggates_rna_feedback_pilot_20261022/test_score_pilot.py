import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from score_pilot import evaluate

class GateTests(unittest.TestCase):
    def predictions(self,candidate=.001,baseline=.04):
        return {name:np.full((7,2),value) for name,value in dict(rho_0=candidate,direct=baseline,
            no_rna=baseline,route_01=baseline,route_10=baseline,route_00=baseline,null_rho_0=0.).items()}

    def test_descriptive_null_does_not_select_or_rescue_gate(self):
        pred=self.predictions(baseline=.01)
        result=evaluate(pred,np.zeros((7,2)),list('abcdefg'),{})
        self.assertEqual(result['strongest_nonisomorphic_ordinary'],'direct')
        self.assertFalse(result['useful_gain_gate'])
        self.assertEqual(result['decision'],'STOP_THIS_CONFIGURATION_EXPANSION')

    def test_strong_ordinary_model_can_stop_an_apparently_good_candidate(self):
        pred=self.predictions();pred['four_gene']=np.full((7,2),.005)
        result=evaluate(pred,np.zeros((7,2)),list('abcdefg'),{})
        self.assertEqual(result['strongest_nonisomorphic_ordinary'],'four_gene')
        self.assertFalse(result['useful_gain_gate'])

    def test_utility_alone_cannot_replace_world_route_increment(self):
        pred=self.predictions();pred['route_01']=pred['rho_0'].copy()
        result=evaluate(pred,np.zeros((7,2)),list('abcdefg'),{})
        self.assertTrue(result['useful_gain_gate']);self.assertFalse(result['state_route_increment'])
        self.assertEqual(result['decision'],'STOP_THIS_CONFIGURATION_EXPANSION')

    def test_positive_gate_still_does_not_claim_agent_or_rsi(self):
        result=evaluate(self.predictions(),np.zeros((7,2)),list('abcdefg'),{})
        self.assertTrue(result['useful_gain_gate'])
        self.assertEqual(result['decision'],'GO_ONLY_TO_NEW_QUALIFICATION_NOT_RSI_PROOF')
        self.assertEqual(result['rsi_c4'],'NOT_TESTED')
        self.assertFalse(result['later_opened'])

if __name__=='__main__':unittest.main()
