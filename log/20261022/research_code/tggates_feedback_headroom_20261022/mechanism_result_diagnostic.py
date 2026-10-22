"""Post-open descriptors of permitted frozen outputs; no raw/later access or fits."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/tggates_feedback_headroom'


def describe(values):
    values = np.asarray(values, dtype=float)
    return {'n': len(values), 'min': float(values.min()), 'median': float(np.median(values)),
            'mean': float(values.mean()), 'max': float(values.max())}


def main():
    paths = {name: LOG / name for name in ['CONDITION_MEANS.json', 'SOURCE_CV.json',
             'HEADROOM_RESULT.json', 'DEVELOPMENT_BOOTSTRAP.json', 'RUN_RECEIPT.json']}
    files = {name: json.loads(path.read_text(encoding='utf-8')) for name, path in paths.items()}
    rows = files['CONDITION_MEANS.json']
    assert {row['role'] for row in rows} == {'source', 'development'}
    assert len(rows) == 31
    result = {'scope': 'Post-result descriptive review of source/development frozen outputs only',
              'new_fits': 0, 'raw_zip_access': False, 'later_values_access': False,
              'inputs_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for name, path in paths.items()},
              'source_selected_cv': files['SOURCE_CV.json']['selected'], 'roles': {}}
    for role in ['source', 'development']:
        chosen = [row for row in rows if row['role'] == role]
        role_result = {}
        for index, assay in enumerate(['DNA', 'LDH']):
            assay_result = {}
            for level in ['Low', 'Middle', 'High']:
                means = [row['doses'][level]['mean'][index] for row in chosen]
                sds = [row['doses'][level]['sd'][index] for row in chosen]
                counts = [row['doses'][level]['n'] for row in chosen]
                assert set(counts) == {2}
                assay_result[level] = {'published_mean': describe(means), 'within_condition_sd': describe(sds),
                                      'absolute_repeat_difference': describe(np.asarray(sds) * np.sqrt(2)),
                                      'half_absolute_repeat_difference': describe(np.asarray(sds) / np.sqrt(2))}
            changes = [row['doses']['High']['mean'][index] - row['doses']['Middle']['mean'][index]
                       for row in chosen]
            assay_result['high_minus_middle'] = {'signed': describe(changes),
                                                'absolute': describe(np.abs(changes))}
            role_result[assay] = assay_result
        result['roles'][role] = role_result
    baseline = files['HEADROOM_RESULT.json']['best_development_dna_mae']
    result['strict_gain_arithmetic'] = {'baseline_mae': baseline, 'absolute_gain_must_exceed': 0.02,
          'candidate_mae_must_be_less_than': baseline - 0.02,
          'relative_reduction_must_exceed': 0.02 / baseline,
          'separate_relative_requirement': 0.10}
    development = [row for row in rows if row['role'] == 'development']
    errors = [{'compound_label': row['compound_label'],
               'middle_dna': row['doses']['Middle']['mean'][0],
               'high_dna': row['doses']['High']['mean'][0],
               'middle_copy_dna_absolute_error': abs(row['doses']['High']['mean'][0]
                                                       - row['doses']['Middle']['mean'][0])}
              for row in development]
    result['development_middle_copy_all_seven'] = errors
    ordered = sorted((row['middle_copy_dna_absolute_error'] for row in errors), reverse=True)
    result['development_middle_copy_error_concentration'] = {
        'largest_one_fraction_of_total': ordered[0] / sum(ordered),
        'largest_two_fraction_of_total': sum(ordered[:2]) / sum(ordered)}
    result['caution'] = 'Repeat differences describe two released measurements; not a universal noise floor, donor variance, or bound on predicting their published mean.'
    output = LOG / 'review/MECHANISM_RESULT_DIAGNOSTIC.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': 'DESCRIPTORS_RETAINED', 'output': str(output),
                      'strict_gain_arithmetic': result['strict_gain_arithmetic'],
                      'source_selected_cv': {family: {'dna_mae': value['dna_mae'], 'ldh_mae': value['ldh_mae']}
                                             for family, value in result['source_selected_cv'].items()},
                      'development_dna': result['roles']['development']['DNA'],
                      'development_middle_copy_all_seven': errors,
                      'error_concentration': result['development_middle_copy_error_concentration']},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
