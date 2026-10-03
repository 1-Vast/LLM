"""Meaningful boundaries for raw reconstruction and retrospective state studies."""
import gzip
import io
import json

import numpy as np
import pandas as pd
import pytest

from tools.datasets.resistrace_retrospective import baseline_groups, load_counts, predict_pair, attach_responses
from tools.datasets.state_raw_reconstruction import convert_counts
from tools.datasets.state_remote_h5 import RangeFile


def raw_contract():
    return {'raw_ensembl_axis':['ENS1','ENS2','ENS3'],'source_indices':[2,0]}


def test_raw_reconstruction_uses_full_library_before_subsetting():
    result=convert_counts([[1,7,2]],['ENS1','ENS2','ENS3'],raw_contract(),research_reconstruction=True)
    np.testing.assert_allclose(result,np.log1p([[2000,1000]]),rtol=1e-6)


@pytest.mark.parametrize('values,genes,research',[
    ([[1,7,2]],['ENS1','ENS2','ENS3'],False),
    ([[1,7,2]],['ENS2','ENS1','ENS3'],True),
    ([[1,7,2]],['ENS1','ENS1','ENS3'],True),
    ([[0,0,0]],['ENS1','ENS2','ENS3'],True),
    ([[1,-1,2]],['ENS1','ENS2','ENS3'],True),
    ([[1,1.5,2]],['ENS1','ENS2','ENS3'],True),
    ([[1,np.nan,2]],['ENS1','ENS2','ENS3'],True),
])
def test_raw_unknown_axis_invalid_counts_and_unreviewed_external_samples_refuse(values,genes,research):
    with pytest.raises(ValueError):
        convert_counts(values,genes,raw_contract(),research_reconstruction=research)


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



def test_range_reader_checks_response_offsets_and_hides_exception_urls(tmp_path,monkeypatch):
    response=io.BytesIO(b'abcd')
    response.status=206
    response.headers={'Content-Range':'bytes 4-7/100'}
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:response)
    with pytest.raises(RuntimeError,match='sanitized receipt'):
        RangeFile('https://example.invalid/public',tmp_path/'range',block_size=4)
    receipt=json.loads((tmp_path/'range/receipts.json').read_text())[0]
    assert receipt['error']=='ValueError'
    assert not (tmp_path/'range/block_0.raw').exists()
