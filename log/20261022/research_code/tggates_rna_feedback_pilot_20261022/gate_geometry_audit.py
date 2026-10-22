"""Outcome-free audit of the already-frozen candidate-containing mixture gate."""
from decimal import Decimal
from pathlib import Path
import json
import numpy as np
P=Path('log/20261022/tggates_rna_feedback_pilot')


def main():
    rng=np.random.default_rng(220226)
    target=rng.normal(size=(10000,7))
    candidate=rng.normal(size=(10000,7));direct=rng.normal(size=(10000,7))
    c=np.abs(candidate-target).mean(1);d=np.abs(direct-target).mean(1)
    m=np.abs(.5*(candidate+direct)-target).mean(1)
    bound=.5*(d-c)
    assert np.all(m-c<=bound+1e-12)
    # Independent exact-decimal sharp example, all errors share a sign.
    c0,d0=Decimal('.001'),Decimal('.04')
    m0=(c0+d0)/2
    assert m0-c0==Decimal('.0195')<Decimal('.02')
    cp,dp=Decimal('.001'),Decimal('.05')
    mp=(cp+dp)/2
    assert mp-cp==Decimal('.0245')>Decimal('.02')
    result=dict(status='PASS',biological_values_opened=0,model_fits=0,
        random_synthetic_instances=10000,
        inequality='MAE((candidate+direct)/2)-MAE(candidate) <= (MAE(direct)-MAE(candidate))/2',
        proof='Triangle inequality pointwise, then average and subtract candidate MAE.',
        necessary_for_original_absolute_gate='direct_MAE-candidate_MAE > 0.04',
        corollary='If selected direct developmentMAE <=0.04, strict >0.02 gain over the candidate-containing half mixture is impossible.',
        not_universal_impossibility='direct=.05 and candidate=.001 gives mixture=.0255, gain=.0245; '
            'the full gate additionally requires beating all other alternatives and route/noRNA increments.',
        exact_example=dict(candidate=str(c0),direct=str(d0),mixture=str(m0),gain=str(m0-c0)),
        decision='KEEP_FROZEN_GATE; interpret stop as utility/configuration decision, not proof of absent information.',
        frozen_code_changed=False,
        reporting='Report continuous candidate-vs-pure-direct, noRNA, routes and mixture contrasts separately. '
            'No post-result threshold relaxation, novel-core or RSI inference.')
    with (P/'GATE_GEOMETRY_AUDIT.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
