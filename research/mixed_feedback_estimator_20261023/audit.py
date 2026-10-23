"""Check saved outputs and gate, without raw matrix access or refitting models."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'
CONTROLS = ['additive', 'mean', 'q_ridge', 'linear_ridge', 'bilinear_ridge', 'fixed_mixture']


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def main():
    for name, expected in json.loads((OUT / 'FREEZE.json').read_text())['files'].items():
        assert digest(ROOT / name) == expected, name
    data = np.load(OUT / 'OOF_STATE.npz')
    scores, fold_scores = pd.read_csv(OUT / 'SCORES.csv'), pd.read_csv(OUT / 'FOLD_SCORES.csv')
    assert len(scores) == 28 and len(fold_scores) == 140
    assert len(data['pairs']) == len(set(data['pairs'])) == 73
    predictions = 0
    for row in scores.itertuples():
        key = row.space + '__' + row.direction
        prediction, truth = data[key + '__' + row.model], data[key + '__truth']
        assert prediction.shape == truth.shape == (73, 103)
        mse = np.mean((prediction - truth) ** 2)
        assert np.isclose(mse, row.MSE, rtol=1e-12, atol=1e-14)
        predictions += prediction.size
    summaries = []
    for space in scores.space.unique():
        for direction in scores.direction.unique():
            subset = scores[(scores.space == space) & (scores.direction == direction)].set_index('model')
            best = subset.loc[CONTROLS, 'MSE'].idxmin()
            candidate, baseline = float(subset.loc['diagonal', 'MSE']), float(subset.loc[best, 'MSE'])
            folds = fold_scores[(fold_scores.space == space) & (fold_scores.direction == direction)]
            pivot = folds.pivot(index='fold', columns='model', values='MSE')
            summaries.append({'space': space, 'direction': direction, 'strongest_control': best,
                              'diagonal_MSE': candidate, 'strongest_control_MSE': baseline,
                              'relative_gain': 1 - candidate / baseline,
                              'positive_folds': int((pivot.diagonal < pivot[best]).sum())})
    primary = next(r for r in summaries if r['space'] == 'mean_log1pCP10K' and r['direction'] == 'A_to_B')
    reverse = next(r for r in summaries if r['space'] == 'mean_log1pCP10K' and r['direction'] == 'B_to_A')
    passed = primary['relative_gain'] >= .05 and primary['positive_folds'] >= 4 and reverse['relative_gain'] > 0
    costs = json.loads((OUT / 'FIT_COSTS.json').read_text())
    result = json.loads((OUT / 'RESULT.json').read_text())
    assert len(costs) == result['fit_calls'] == 600
    assert np.isclose(sum(r['seconds'] for r in costs), result['summed_fit_seconds'], rtol=1e-12)
    checked_seals = 0
    for role in ['constructive', 'prior', 'support']:
        seal = json.loads((OUT / role / 'INDEPENDENT_SEAL.json').read_text())
        for name, expected in seal.get('files', seal).items():
            assert digest(ROOT / name) == expected, name
            checked_seals += 1
    for role in ['constructive', 'prior']:
        seal = json.loads((OUT / role / 'RESULT_REVIEW_SEAL.json').read_text())
        for name, expected in seal['files'].items():
            assert digest(ROOT / name) == expected, name
            checked_seals += 1
        assert (OUT / role / 'RESULT_REVIEW.md').is_file()
        assert (OUT / role / 'RESULT_CROSS.md').is_file()
    extraction_check = json.loads((OUT / 'EXTRACTION_AUDIT.json').read_text())
    assert extraction_check['max_single_feature_discrepancy'] == 0
    assert extraction_check['source_pair_counts_checked'] == 73
    predecessor = json.loads((ROOT / 'log/20261023/update_law_search/VERIFICATION.json').read_text())
    for name, expected in predecessor['files'].items():
        assert digest(ROOT / name) == expected, name
    report = {'status': 'PASS_LOCAL', 'saved_prediction_values_checked': predictions,
              'score_rows_checked': len(scores), 'fit_calls_checked': len(costs),
              'independent_sealed_files_checked': checked_seals,
              'predecessor_files_unchanged': len(predecessor['files']), 'summaries': summaries,
              'gate': 'PASS_SOURCE_STATE_PREDICTIVE_GATE' if passed else 'STOP_CURRENT_DIAGONAL_MIXED_LAW_CONFIGURATION',
              'scope': 'Saved-output arithmetic, preregistered state gate and local continuity; not biology, functional utility, RSI or global provenance repair'}
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
    files = {}
    for folder in [OUT, Path(__file__).resolve().parent]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    (OUT / 'VERIFICATION.json').write_text(json.dumps({'files': files, **report}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
