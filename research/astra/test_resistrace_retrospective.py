"""Retrospective experimental boundaries; no STATE or causal utility claim."""
import gzip
import numpy as np
import pandas as pd
import pytest
from research.astra.resistrace_retrospective import baseline_groups, load_counts, predict_pair, attach_responses


def test_future_matching_does_not_select_or_group_baseline_inputs():
    data=pd.DataFrame({'sisters':[1,1,np.nan],'drugSens':['pre-resistant']*3,'prer_r_group':[1,1,2]},index=['a','b','c'])
    a=baseline_groups(data)
    data['drugSens']='pre-sensitive';data['prer_r_group']=np.nan
    pd.testing.assert_series_equal(a,baseline_groups(data))
    assert list(a)==['sister:1','sister:1','cell:c']



def test_unmatched_followup_is_missing_not_death():
    pre=pd.DataFrame({'sisters':[np.nan,np.nan],'prer_r_group':[1,np.nan]},index=['a','b'])
    post=pd.DataFrame({'prer_r_group':[1]},index=['future1'])
    linked=attach_responses(pre,post,baseline_groups(pre),np.array([[4.,5.]]))
    assert set(linked)=={'cell:a'}
    np.testing.assert_array_equal(linked['cell:a'][0],[4,5])



def test_blind_model_is_invariant_to_per_question_state():
    x=np.array([[0.,1],[2,1],[3,4],[5,2]])
    y=np.array([[1.,2],[3,1],[2,7],[4,1]])
    reference=x.mean(axis=0)
    a=predict_pair(x,y,x,reference,blind=True)
    b=predict_pair(x*100,y,x[::-1]*999,reference,blind=True)
    np.testing.assert_array_equal(a,b)



def test_reading_counts_validates_identity_and_total(tmp_path):
    path=tmp_path/'counts.gz'
    path.write_bytes(gzip.compress(b'gene\ta\tb\nENS1\t1\t2\nENS2\t3\t0\n'))
    meta=pd.DataFrame({'nCount_RNA':[4,2]},index=['a','b'])
    got=load_counts(path,meta,['ENS2','ENS1'])
    np.testing.assert_allclose(got,np.log1p([[7500,2500],[0,10000]]),rtol=1e-6)
    meta.loc['a','nCount_RNA']=5
    with pytest.raises(ValueError,match='totals disagree'):load_counts(path,meta,['ENS1'])
