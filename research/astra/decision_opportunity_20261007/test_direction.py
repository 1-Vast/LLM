"""Meaningful paid-target isolation and shared-STATE-feedback boundary checks."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


study=module("test_direction_study","run.py")
trust=module("test_direction_trust","trust_channel.py")
transfer=module("test_direction_transfer","transfer.py")


def test_paid_A_can_be_revealed_once_and_B_only_after_five_commit(tmp_path):
    labels=[f"[('D{i}', 0.5, 'uM')]" for i in range(6)]
    wells={l:['pA','pB'] for l in labels}
    evaluator=study.PaidObservations(tmp_path,'case','L',labels,wells,np.arange(6.)/10,np.arange(6.)/20,
                                    {'A':np.ones(6,int),'B':np.ones(6,int)})
    assert evaluator.screen(2)==.2
    with pytest.raises(ValueError,match="duplicate"):evaluator.screen(2)
    with pytest.raises(ValueError,match="Five distinct"):evaluator.confirm([0,1,2])
    assert evaluator.confirm([0,1,2,3,4])==[0.,.05,.1,.15,.2]
    with pytest.raises(ValueError,match="late"):evaluator.screen(3)
    assert evaluator.store.snapshot('case').spent==6.
    assert len(evaluator.store.result_identities('case'))==6


def test_train_covariance_keeps_correlated_target_labels_and_psd():
    train=np.array([[0.,1.],[1.,2.],[2.,3.],[3.,4.]])
    cov,var,offset,n=study.fit_common_belief(train+.1,train,np.ones_like(train,bool))
    assert cov[0,1]>0 and np.linalg.eigvalsh(cov).min()>0
    assert np.allclose(offset,.1)
    assert np.all(var>0) and n.tolist()==[4,4]


def test_no_reference_support_refuses_instead_of_dropping_candidate():
    values=np.array([[1.,2.],[3.,4.]])
    available=np.array([[True,False],[True,False]])
    with pytest.raises(ValueError,match="Every registered candidate"):
        study.fit_common_belief(values,values,available)


def test_paid_scalar_updates_shared_gamma_and_unmeasured_WORLD_predictions():
    b=trust.TrustBelief(np.zeros(2),np.zeros(2),np.ones(2),np.ones(2),np.eye(2)*.01,np.ones(2)*.01,True)
    before=b.target_mean().copy();variance=b.cov[0,0]
    b.update(0,1.)
    assert b.mean[0]>.5 and b.cov[0,0]<variance
    assert b.target_mean()[1]>before[1]
    assert np.linalg.eigvalsh(b.cov).min()>-1e-10


def test_fixed_trust_control_cannot_change_gamma_or_uncorrelated_candidate():
    b=trust.TrustBelief(np.zeros(2),np.zeros(2),np.ones(2),np.ones(2),np.eye(2)*.01,np.ones(2)*.01,False)
    before=b.target_mean().copy();b.update(0,1.)
    assert b.mean[0]==.5 and b.cov[0,0]==0.
    assert b.target_mean()[1]==before[1]


def test_zero_STATE_channel_cannot_fabricate_WORLD_feedback_effect():
    b=trust.TrustBelief(np.zeros(2),np.zeros(2),np.zeros(2),np.zeros(2),np.eye(2)*.01,np.ones(2)*.01,True)
    b.update(0,.4)
    assert b.mean[0]==.5 and b.cov[0,0]==.25
    assert b.target_mean()[1]==0.


@pytest.mark.parametrize("index",[-1,True,False,12,1.2])
def test_invalid_purchase_identity_refused_before_charge(tmp_path,index):
    labels=[f"[('D{i}', 0.5, 'uM')]" for i in range(12)]
    evaluator=study.PaidObservations(tmp_path,'case','L',labels,{l:['a','b'] for l in labels},
        np.arange(12.),np.arange(12.),{'A':np.ones(12,int),'B':np.ones(12,int)})
    with pytest.raises(ValueError):evaluator.screen(index)
    with pytest.raises(ValueError):evaluator.confirm([0,1,2,3,index])
    assert evaluator.store.snapshot('case').spent==0.
    assert evaluator.store.snapshot('case').plan_version==0


def test_ninth_screen_refused_before_spending_confirmation_reserve(tmp_path):
    labels=[f"[('D{i}', 0.5, 'uM')]" for i in range(12)]
    evaluator=study.PaidObservations(tmp_path,'case','L',labels,{l:['a','b'] for l in labels},
        np.arange(12.),np.arange(12.),{'A':np.ones(12,int),'B':np.ones(12,int)})
    for i in range(8):evaluator.screen(i)
    version=evaluator.store.snapshot('case').plan_version
    with pytest.raises(ValueError):evaluator.screen(8)
    assert evaluator.store.snapshot('case').spent==8.
    assert evaluator.store.snapshot('case').plan_version==version
    evaluator.confirm([0,1,2,3,4])
    assert evaluator.store.snapshot('case').spent==13.


def test_transfer_five_screen_envelope_keeps_five_confirmation_credits(tmp_path):
    labels=[f"[('D{i}', 0.5, 'uM')]" for i in range(8)]
    evaluator=study.PaidObservations(tmp_path,'transfer','L',labels,{l:['a','b'] for l in labels},
        np.arange(8.),np.arange(8.),{'A':np.ones(8,int),'B':np.ones(8,int)}, budget=10.,max_screens=5)
    for i in range(5):evaluator.screen(i)
    version=evaluator.store.snapshot('transfer').plan_version
    with pytest.raises(ValueError):evaluator.screen(5)
    assert evaluator.store.snapshot('transfer').plan_version==version
    evaluator.confirm([0,1,2,3,4])
    assert evaluator.store.snapshot('transfer').spent==10.


def test_transfer_unpurchased_B_cannot_change_any_screen_or_final_commit(tmp_path):
    labels=[f"[('D{i}', 0.5, 'uM')]" for i in range(8)]
    prior=np.arange(8.)/10
    arm=dict(name='syntheticKG',model='M0',policy='knowledge_gradient',screens=5,cap=10)
    rows=[]
    for name,second_well in [('first',np.arange(8.)),('different',np.arange(8.)[::-1]*10)]:
        out=tmp_path/name;out.mkdir()
        evaluator=study.PaidObservations(out,name,'L',labels,{l:['a','b'] for l in labels},
            np.arange(8.)/10,second_well,{'A':np.ones(8,int),'B':np.ones(8,int)},budget=10.,max_screens=5)
        rows.append(transfer.episode(prior,np.eye(8)*.02,np.ones(8)*.01,np.zeros(8),evaluator,arm,
                                     np.random.default_rng(42).standard_normal(64)))
    assert rows[0]['screened']==rows[1]['screened']
    assert rows[0]['final_flags']==rows[1]['final_flags']
    assert rows[0]['utility']!=rows[1]['utility']
