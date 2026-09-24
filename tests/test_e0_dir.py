import numpy as np
import pytest
from evaluation.e0_dir_core import *
from evaluation.e0_dir_controller import *

def _episode():
    p=PredictionPair((1.,-1.),(.5,-.25),(.25,-.5),"m","basis","controls","proj")
    a=ActionSpec("a0","initial","drug",1,"nM","c","m","latent","basis","controls")
    h=LatentHypothesis("h0",(0.1,0.2),"latent","a0","within_registered_support")
    rs=tuple(ActionSpec(f"r{i}",f"r{i}","drug",i+1,"nM","c","m","latent","basis","controls") for i in range(2))
    hs=tuple((h,ActionSpec(f"h{i}",f"h{i}","drug",i+1,"nM","c","m","latent","basis","controls","hypothesis")) for i in range(2))
    return DIREpisode("e",p,a,h,rs,hs,4)

def test_residual_identity_preserves_cancellation():
    e=_episode(); assert np.allclose(e.pair.r_goal+e.pair.r_realization,e.pair.r_total)

def test_invalid_dimension_and_nan_rejected():
    with pytest.raises(ValueError): PredictionPair((1.,), (1.,2.), (0.,2.), "m","b","c","p")
    with pytest.raises(ValueError): PredictionPair((float("nan"),), (0.,), (0.,), "m","b","c","p")

class Provider:
    def predict(self, action, hypothesis): return (action.dose, -action.dose)

def test_keep_does_not_query_and_selector_is_shared():
    e=_episode(); rec=execute_step(e,DIRDecision(DIRRepairBranch.KEEP),Provider())
    assert rec.queried_action_ids == () and rec.selected_action_id == "a0"
    rec=execute_step(e,DIRDecision(DIRRepairBranch.REALIZATION),Provider())
    assert len(rec.queried_action_ids)==2 and rec.prediction_cost==2

def test_observation_binding_is_private_and_strict():
    e=_episode(); o=E0Observation("e","r0",(1.,-1.),"basis","private","drug_cluster_1")
    assert score_observation(o,e) >= 0
    with pytest.raises(ValueError): score_observation(E0Observation("other","r0",(1.,-1.),"basis","p","u"),e)

