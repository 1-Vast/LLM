"""Meaningful pairwise-missingness and raw scalar-isolation checks."""
import numpy as np
from diagnostic import moments, selected_auc


def test_pairwise_complete():
    y = np.array([[1., 3., np.nan], [2., np.nan, 4.], [4., 2., 6.],
                  [7., 9., 3.], [np.nan, 8., 2.]])
    weights = np.array([2, 1, 3, 1, 2])
    for values, w in [(y, None), (y, weights)]:
        estimates = moments(values, w)
        repeated = values if w is None else np.repeat(values, w, axis=0)
        for i in range(3):
            for j in range(3):
                valid = np.isfinite(repeated[:, i]) & np.isfinite(repeated[:, j])
                pair = repeated[valid][:, [i, j]]
                assert estimates['n'][i, j] == len(pair)
                np.testing.assert_allclose(estimates['corr'][i, j],
                                           np.corrcoef(pair.T)[0, 1], atol=1e-12)
                np.testing.assert_allclose(estimates['slope'][i, j],
                                           np.cov(pair.T)[0, 1]/np.var(pair[:, 0], ddof=1),
                                           atol=1e-12)


def test_no_nonsource_auc_parse():
    def row(context, value, inclusion='TRUE'):
        return dict(dbgap_rnaseq_sample=context, dbgap_subject_id='p',
                    paper_inclusion=inclusion, inhibitor='a', auc=value)
    rows = [row('not_selected', 'POISON'), row('selected', 'POISON', 'FALSE'),
            row('selected', '2'), row('selected', '4'), row('selected', 'NA')]
    result, count, decoded = selected_auc(rows, {'selected': 'p'}, np.array(['a']))
    assert decoded == 2 and count[0, 0] == 2 and result[0, 0] == 3
    assert np.all(moments(np.ones((5, 2)))['constant'])


if __name__ == '__main__':
    test_pairwise_complete()
    test_no_nonsource_auc_parse()
    print('PASS: pairwise/weighted moments and nonselected AUC isolation')
