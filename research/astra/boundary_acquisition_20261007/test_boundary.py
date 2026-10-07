"""Cross-component boundaries for reference-only fitting and paid evidence policies."""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary_test_execute',HERE/'execute.py')
execute=importlib.util.module_from_spec(spec);spec.loader.exec_module(execute)
method=execute.method


def arrays():
    rng=np.random.default_rng(19);n,k=8,8
    return dict(train_A=rng.normal(size=(n,k)),train_B=rng.normal(size=(n,k)),
        availability_A=np.ones((n,k),bool),availability_B=np.ones((n,k),bool),
        precision_B=np.exp(rng.normal(size=(n,k))),basal=rng.normal(size=(n,5)),
        state_B=rng.normal(size=(n,k)),state_B_permuted=rng.normal(size=(n,k)),
        state_available_B=np.ones((n,k),bool),state_available_B_permuted=np.ones((n,k),bool),
        dose=np.array([.05,.5,5.,.05,.5,5.,.5,5.]),plate_design=np.eye(2)[np.arange(k)%2])


def test_outer_context_cannot_enter_inner_error_features_or_model_floor():
    a=arrays();included=np.ones(8,bool);included[2]=False
    original=method.dataset(a,included)
    changed=copy.deepcopy(a)
    for key in ('train_A','train_B','precision_B','basal','state_B'):
        changed[key][2]=1000.
    after=method.dataset(changed,included)
    for x,y in zip(original,after):assert np.array_equal(x,y)
    beforefit=method.fit(original[0],original[1]);afterfit=method.fit(after[0],after[1])
    assert beforefit['floor']==afterfit['floor']
    assert np.array_equal(beforefit['coef'],afterfit['coef'])


def test_missing_STATE_reference_row_not_treated_as_measured_zero():
    a=arrays();a['state_available_B'][0,3]=False
    _,_,eligible,_=method.reference_row(a,0)
    assert not eligible[3] and eligible.sum()==7


def test_covariance_scaling_retains_correlation_and_psd():
    c=np.array([[2.,.8],[.8,1.]])
    scaled=method.scale_covariance(c,np.array([.5,2.]))
    assert np.linalg.eigvalsh(scaled).min()>0
    assert scaled[0,1]/np.sqrt(scaled[0,0]*scaled[1,1])==pytest.approx(.8/np.sqrt(2.))


@pytest.mark.parametrize('invalid',['mean','noise','covariance','nonPSD'])
def test_invalid_policy_values_refuse_before_purchase(invalid):
    mean=np.arange(8.);cov=np.eye(8);noise=np.ones(8)
    if invalid=='mean':mean[0]=np.nan
    elif invalid=='noise':noise[0]=-1.
    elif invalid=='covariance':cov[0,0]=np.inf
    else:cov[:2,:2]=np.array([[1.,2.],[2.,1.]])
    with pytest.raises(ValueError):method.validate_inputs(mean,cov,noise)


def test_third_candidate_can_resolve_incumbent_challenger_boundary():
    mean=np.array([1.,.9,.8,.7,.6,.59,-10.,.0])
    c=np.eye(8)*.001
    vector=np.array([0.,0.,0.,0.,1.,-1.,4.,0.])
    c+=np.outer(vector,vector)
    scores,details=method.boundary_scores(mean,c,np.ones(8)*.1,range(8))
    chosen=max(scores,key=lambda i:(scores[i],-i))
    assert chosen==6
    assert details[chosen]['incumbent']==4 and details[chosen]['challenger']==5
    assert np.isfinite(scores[chosen]) and scores[chosen]>0


def evaluator(tmp_path,name,yB):
    labels=[f"[('D{i}',0.5,'uM')]" for i in range(8)]
    out=tmp_path/name;out.mkdir()
    return execute.study.PaidObservations(out,name,'synthetic',labels,{l:['a','b'] for l in labels},
        np.arange(8.)/10,yB,{'A':np.ones(8,int),'B':np.ones(8,int)})


def test_zero_A_stop_keeps_five_B_commit_and_explicit_unused_budget(tmp_path):
    e=evaluator(tmp_path,'stop',np.arange(8.))
    arm=dict(name='boundary',model='M2',acquisition='boundary',uncertainty='common',max_A=8,stopping=True)
    result=execute.episode(np.arange(8.)/10,np.eye(8)*.01,np.ones(8)*.01,np.zeros(8),e,arm,1e9,
                           np.random.default_rng(42).normal(size=64))
    assert result['screened']==[] and result['actual_credits']==5 and result['unused_cap']==8
    assert result['stopreason']=='boundary_surrogate_below_training_tau'
    assert len(e.store.result_identities('stop'))==5


def test_nonfinite_offset_refuses_before_charge(tmp_path):
    e=evaluator(tmp_path,'offset',np.arange(8.))
    arm=dict(name='boundary',model='M2',acquisition='boundary',uncertainty='common',max_A=8,stopping=True)
    offset=np.zeros(8);offset[1]=np.nan
    with pytest.raises(ValueError):
        execute.episode(np.arange(8.)/10,np.eye(8)*.01,np.ones(8)*.01,offset,e,arm,0.,np.ones(64))
    assert e.store.snapshot('offset').spent==0


def test_private_B_does_not_change_queries_stop_or_flags(tmp_path):
    arm=dict(name='boundary',model='M2',acquisition='boundary',uncertainty='common',max_A=3,stopping=True)
    rows=[]
    for name,yB in [('one',np.arange(8.)),('two',np.arange(8.)[::-1]*10)]:
        e=evaluator(tmp_path,name,yB)
        rows.append(execute.episode(np.arange(8.)/10,np.eye(8)*.01,np.ones(8)*.01,np.zeros(8),e,arm,0.,
                                   np.random.default_rng(42).normal(size=64)))
    for key in ('screened','final_flags','stopreason'):assert rows[0][key]==rows[1][key]
    assert rows[0]['utility']!=rows[1]['utility']


def test_stopped_policy_and_no_stop_share_every_acquisition_prefix(tmp_path):
    prior=np.arange(8.)/10;cov=np.eye(8)*.01;noise=np.ones(8)*.01
    initial,_=method.boundary_scores(prior,cov,noise,range(8))
    arms=[dict(name='one',model='M2',acquisition='boundary',uncertainty='common',max_A=3,stopping=True),
          dict(name='two',model='M2',acquisition='boundary',uncertainty='common',max_A=3,stopping=False)]
    rows=[]
    for arm in arms:
        e=evaluator(tmp_path,arm['name'],np.arange(8.))
        rows.append(execute.episode(prior,cov,noise,np.zeros(8),e,arm,max(initial.values())*.5,
                                   np.random.default_rng(42).normal(size=64)))
    assert rows[0]['screened']==rows[1]['screened'][:len(rows[0]['screened'])]
