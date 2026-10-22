"""Hand-written audit of a retained proposal; synthetic algebra, no assay data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261022/intervention_program_renewal'
SEED=20261022


def orders(values):
    return np.sign(values[:,None]-values[None,:])


def disagreement(first,second):
    take=np.triu_indices(len(first),1)
    return int(np.count_nonzero(orders(first)[take]!=orders(second)[take]))


def corrected_routed_step(params,x,y,control,eta):
    result=params.copy()
    residual=y-params[0]-x@params[1:]
    if control:
        result[0]+=eta*residual
    else:
        result[1:]+=2*eta*residual*x
    return result


def ordinary_masked_gradient(params,x,y,control,eta):
    design=np.r_[1.,x]
    gradient=2*(design@params-y)*design
    diagonal=np.r_[.5,np.zeros(len(x))] if control else np.r_[0.,np.ones(len(x))]
    return params-eta*diagonal*gradient


def main():
    path=OUT/'FSI_ALGEBRA_AUDIT.json'
    if path.exists():
        raise FileExistsError('audit_already_recorded')
    source=OUT/'mechanism/RESPONSE.md'
    expected='901264267c1f355ac7cde3a1027bf9920af5d6516dda1993b85a6ebda1e9fd07'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
    rng=np.random.default_rng(SEED)
    rank_cases=[]
    for f in (np.array([-2.,0.,1.,4.]),np.array([-2.,0.,0.,4.])):
        g=np.array([4.,0.,-1.,2.])
        original=orders(f)
        original_disagreement=disagreement(f,g)
        for offset in (-10.,-.25,0.,.25,10.):
            forecast=f+offset
            assert np.array_equal(original,orders(forecast))
            assert disagreement(forecast,g)==original_disagreement
            rank_cases.append({'f':f.tolist(),'g':g.tolist(),'offset':offset,
                'rank_disagreement':disagreement(forecast,g),
                'hits_above_zero':(forecast>0).tolist(),'ranks_equal':True})
        for scale in (.125,.5,1.,2.,8.):
            assert np.array_equal(original,orders(scale*f))
    # Offset does affect threshold calibration, so the audit does not erase that value.
    assert rank_cases[0]['hits_above_zero']!=rank_cases[4]['hits_above_zero']
    eta=.25
    true_offset=2.
    trajectory=[]
    literal,corrected=0.,0.
    for n in range(1,21):
        literal+=eta*true_offset
        corrected+=eta*(true_offset-corrected)
        assert abs(literal-n*eta*true_offset)<1e-12
        assert abs(corrected-true_offset*(1-(1-eta)**n))<1e-12
        trajectory.append({'n':n,'literal_update_offset':literal,'corrected_offset':corrected,
                           'true_offset':true_offset})
    assert abs(literal-true_offset)>abs(corrected-true_offset)
    a=np.array([.3,.2,-.4,.1])
    b=a.copy()
    sequence=[]
    for i in range(40):
        x=rng.normal(size=3)
        y=float(rng.normal())
        control=i%3==0
        a=corrected_routed_step(a,x,y,control,.01)
        b=ordinary_masked_gradient(b,x,y,control,.01)
        difference=float(np.max(np.abs(a-b)))
        assert difference<1e-12
        sequence.append({'i':i,'x':x.tolist(),'y':y,'control':control,
            'routed_params':a.tolist(),'ordinary_params':b.tolist(),'max_abs_difference':difference})
    X=np.tile([1.,1.],(3,1))
    theta1=np.array([1.,2.])
    theta2=np.array([2.,1.])
    assert np.linalg.matrix_rank(X)==1
    assert np.array_equal(X@theta1,X@theta2)
    result={'utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,
        'source_sha256':expected,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256':hashlib.sha256((OUT/'FSI_ALGEBRA_PROTOCOL.md').read_bytes()).hexdigest(),
        'biological_response_access':False,'drug_performance_test':False,
        'rank_cases':rank_cases,'positive_scale_cases':10,'control_update_trajectory':trajectory,
        'masked_gradient_sequence':sequence,
        'max_masked_gradient_difference':max(s['max_abs_difference'] for s in sequence),
        'identifiability_counterexample':{'X':X.tolist(),'theta1':theta1.tolist(),'theta2':theta2.tolist(),
            'same_observed_predictions':(X@theta1).tolist(),'design_rank':1,'parameters':2},
        'verdict':'EXACT_RANK_RATIONALE_REFUTED_AND_CORRECTED_UPDATE_ORDINARY',
        'limits':['Additive/common positive scales only; no theorem about drug-dependent/nonlinear measurement bias.',
                  'Threshold calibration can change even when rankings do not.',
                  'Stepwise equality uses the stated linear subcase and a fixed label-coordinate gradient preconditioner.',
                  'No empirical acquisition/world/agent/inheritance/RSI result or universal impossibility follows.']}
    with path.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps({'verdict':result['verdict'],'rank_cases':len(rank_cases),
        'positive_scale_cases':10,'steps':len(sequence),'max_difference':result['max_masked_gradient_difference']}))


if __name__=='__main__':
    main()
