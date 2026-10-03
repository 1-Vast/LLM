"""Meaningful boundaries for raw reconstruction and retrospective state studies."""
import io
import json

import numpy as np
import pytest

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
