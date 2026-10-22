"""Post-seal compare independent conversion with root source/dev artifacts."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_feedback_headroom'
REVIEW = LOG/'review'
TOLERANCE = 1e-12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = REVIEW/'DATA_NUMERIC_COMPARISON.json'
    assert not out.exists()
    independent_path = REVIEW/'DATA_INDEPENDENT_NUMERIC.json'
    seal_path = REVIEW/'DATA_INDEPENDENT_NUMERIC_SEAL.json'
    independent = json.loads(independent_path.read_bytes())
    seal = json.loads(seal_path.read_bytes())
    assert seal['result_sha256'] == sha(independent_path)
    assert seal['root_numeric_outputs_read_before_seal'] is False
    manifest = json.loads((LOG/'MANIFEST.json').read_bytes())
    projection = json.loads((LOG/'FUNCTIONAL_PROJECTION.json').read_bytes())
    means = json.loads((LOG/'CONDITION_MEANS.json').read_bytes())
    result = json.loads((LOG/'HEADROOM_RESULT.json').read_bytes())
    predictions = json.loads((LOG/'DEVELOPMENT_PREDICTIONS.json').read_bytes())
    freeze = json.loads((LOG/'FREEZE.json').read_bytes())
    failures, checks, exact_checks, numeric_checks, max_error = [], 0, 0, 0, 0.0

    def exact(condition, label):
        nonlocal checks, exact_checks
        checks += 1
        exact_checks += 1
        if not condition:
            failures.append(label)

    def close(left, right, label):
        nonlocal checks, numeric_checks, max_error
        checks += 1
        numeric_checks += 1
        delta = abs(float(left)-float(right))
        max_error = max(max_error, delta)
        if delta > TOLERANCE:
            failures.append(label)

    for name, digest in freeze['sha256'].items():
        if name != manifest['raw_zip_relative']:
            exact(sha(ROOT/name) == digest, 'freeze_unchanged:'+name)
    independent_rows = {tuple(row['key']): row for row in independent['normalized_record_values']}
    root_rows = {tuple(row['key']): row for row in projection['records']}
    exact(len(independent_rows) == len(root_rows) == 186, '186records')
    exact(set(independent_rows) == set(root_rows), 'exact_recordkeys')
    root_audit = {tuple(row['key']): row for row in projection['audit']}
    exact(set(root_audit) == set(independent_rows), 'root_audit_keys')
    outside = 0
    for key, row in independent_rows.items():
        root = root_rows[key]
        flags = {}
        for flag in root['quality_flags']:
            flags[flag['assay']] = {'below_zero': flag['below_zero'], 'above_100': flag['above_100']}
        this_outside = False
        for index, assay in enumerate(('DNA', 'LDH')):
            value = Decimal(row['normalized_assays_decimal'][assay])
            close(value, root['values'][index], str(key)+':'+assay+':normalized')
            expected_flags = row['range_flags'][assay]
            exact(flags.get(assay+'(%)', {'below_zero': False, 'above_100': False}) == expected_flags,
                  str(key)+':'+assay+':flags')
            audited = root_audit[key]['assays'][assay+'(%)']
            exact(audited['status'] == 'finite', str(key)+':'+assay+':rootfinite')
            close(value, audited['normalized_value'], str(key)+':'+assay+':auditnormalized')
            close(value*100, audited['published_percentage'], str(key)+':'+assay+':published')
            this_outside |= any(expected_flags.values())
        exact(root_audit[key]['complete_valid_record'] is True, str(key)+':complete')
        outside += int(this_outside)
    exact(outside == projection['finite_outside_0_100_records_retained'], 'outside_count')
    exact(not projection['invalid'], 'root_no_invalid')
    exact(projection['skipped_response_columns_accessed'] == 0, 'root_skip_columns')
    for counter in ('assay_field_accesses', 'numeric_cast_attempts', 'numeric_parse_successes', 'finite_numeric_cast_successes'):
        exact(projection['exposure_counters'][counter] == {'DNA(%)': 186, 'LDH(%)': 186}, counter)
    root_conditions = {(row['compound_label'], level): (row, dose)
                       for row in means for level, dose in row['doses'].items()}
    exact(len(root_conditions) == len(independent['condition_aggregates']) == 93, '93conditions')
    for row in independent['condition_aggregates']:
        compound, dose = root_conditions[row['compound_label'], row['dose_level']]
        exact(compound['role'] == row['role'], row['compound_label']+':role')
        for index, assay in enumerate(('DNA', 'LDH')):
            stat = row['assays'][assay]
            exact(stat['n'] == dose['n'], row['compound_label']+':'+row['dose_level']+':'+assay+':n')
            close(stat['mean_decimal'], dose['mean'][index], row['compound_label']+':'+row['dose_level']+':'+assay+':mean')
            close(stat['sd_ddof1_decimal'], dose['sd'][index], row['compound_label']+':'+row['dose_level']+':'+assay+':sd')
    mapping = {'constant_085': 'constant_085', 'middle_copy': 'middle_copy',
               'source_high_median': 'constant_source_median', 'source_median_offset': 'median_residual'}
    baseline_summary = {}
    for own_name, root_name in mapping.items():
        own = independent['development_baselines'][own_name]
        root = result['development'][root_name]
        close(own['development_DNA_MAE_decimal'], root['dna_mae'], own_name+':DNA_MAE')
        root_by_label = {row['compound_label']: row for row in predictions[root_name]}
        exact(set(root_by_label) == {row['compound_label'] for row in own['per_compound']}, own_name+':devlabels')
        for row in own['per_compound']:
            reference = root_by_label[row['compound_label']]
            close(row['prediction_decimal'], reference['prediction'][0], own_name+':'+row['compound_label']+':prediction')
            close(row['target_decimal'], reference['target'][0], own_name+':'+row['compound_label']+':target')
        baseline_summary[root_name] = {'independent_development_DNA_MAE': float(own['development_DNA_MAE_decimal']),
                                       'root_development_DNA_MAE': root['dna_mae']}
    exact(independent['later_assay_casts'] == independent['control_assay_casts'] == 0, 'independent_latercontrols0')
    exact(independent['source_labels'] == 24 and independent['development_labels'] == 7, 'independent_roles')
    exact(independent['new_biological_observations'] == 0, 'no_new_observations')
    raw = ROOT/manifest['raw_zip_relative']
    with zipfile.ZipFile(raw) as archive:
        raw_metadata = [{'filename': info.filename, 'uncompressed_bytes': info.file_size,
                         'compressed_member_bytes': info.compress_size} for info in archive.infolist()]
    raw_hash = independent['input_sha256'][manifest['raw_zip_relative']]
    exact(raw_hash == manifest['inputs_sha256'][manifest['raw_zip_relative']], 'raw_hash')
    inputs = [independent_path, seal_path, LOG/'MANIFEST.json', LOG/'FUNCTIONAL_PROJECTION.json',
              LOG/'CONDITION_MEANS.json', LOG/'HEADROOM_RESULT.json', LOG/'DEVELOPMENT_PREDICTIONS.json',
              LOG/'FREEZE.json', REVIEW/'DATA_NUMERIC_COMPARISON_PROTOCOL.md', Path(__file__)]
    report = {'status': 'PASS_SOURCE_DEVELOPMENT_CONVERSION_AND_FOUR_BASELINES' if not failures else 'FAIL',
              'checks': checks, 'exact_checks': exact_checks, 'numeric_tolerance_checks': numeric_checks,
              'absolute_tolerance': TOLERANCE, 'max_observed_absolute_difference': max_error,
              'failures': failures, 'verified_records': 186, 'verified_assay_values': 372,
              'verified_condition_aggregates': 93, 'outside_0_100_records_retained': outside,
              'development_DNA_baselines': baseline_summary,
              'raw_file_bytes': raw.stat().st_size, 'raw_sha256': raw_hash,
              'raw_member_metadata_only': raw_metadata,
              'independent_logical_raw_conversion_passes': 1, 'new_biological_observations': 0,
              'additional_raw_numeric_conversions_in_this_comparison': 0,
              'later_values_accessed_or_cast': 0, 'control_values_accessed_or_cast': 0,
              'new_HTTP': 0, 'new_fits': 0,
              'input_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in inputs},
              'scope': 'Independent Decimal conversion/aggregation and four basic DNA baselines only; ridge/KRR/search/RSI not validated here.'}
    write = out.open('x', encoding='utf-8')
    with write as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'input_sha256'}, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == '__main__':
    raise SystemExit(main())
