"""Identity and exact-budget counterexamples for the separate extension."""
import numpy as np
import pytest

from research.decision_value.axis_extension_20261010.audit import matching, write
from research.decision_value.axis_extension_20261010.selection import uncovered
from research.decision_value.axis_extension_20261010.verify import compare_all


def test_positive_counts_do_not_name_ambiguous_coordinate():
    x=np.array([[1.,1.],[2.,2.]])
    result=matching(['TNF','SDK2'],x,x[:,0,None],['TNF'])
    assert result[0]['nonzero_cells']==2 and not result[0]['passed']
    assert result[0]['matching_source_symbols']==['TNF','SDK2']


def test_exposed_consistency_cannot_be_relabeled_as_fresh_holdout():
    x=np.array([[1.,1.],[2.,2.],[0.,1.]])
    target=x[:,0,None]
    assert not compare_all(['TNF','SDK2'],x[:2],target[:2],['TNF'])[0]['passed']
    assert compare_all(['TNF','SDK2'],x,target,['TNF'])[0]['passed']


def test_unique_zero_or_duplicate_symbol_is_rejected():
    assert not matching(['TNF'],np.zeros((2,1)),np.zeros((2,1)),['TNF'])[0]['passed']
    x=np.array([[1.,0.],[2.,0.]])
    assert not compare_all(['TNF','TNF'],x,x[:,0,None],['TNF'])[0]['passed']


def test_value_gate_uses_frozen_tolerance_not_binary_presence():
    x=np.array([[1e-6,0.],[2e-6,0.]])
    assert not matching(['TNF','SDK2'],x,x[:,0,None],['TNF'])[0]['passed']


def test_cost_counts_gaps_and_refuses_output_overwrite(tmp_path):
    assert uncovered([(0,9),(5,14),(20,29)],[(0,4),(7,11),(22,24)])==12
    path=tmp_path/'RESULT.json'
    write(path,dict(frozen=True))
    with pytest.raises(FileExistsError):write(path,dict(frozen=False))
