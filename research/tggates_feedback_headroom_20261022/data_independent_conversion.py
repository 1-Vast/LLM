"""Independent, authorization-gated source/dev numerical conversion and seal."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_feedback_headroom'
REVIEW = LOG/'review'
MANIFEST = LOG/'MANIFEST.json'
PROTOCOL = REVIEW/'DATA_CONVERSION_AUDIT_PROTOCOL.md'
IDENTITY = ('EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES',
            'SEX_TYPE', 'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL')
HEADER = IDENTITY + ('DNA(%)', 'LDH(%)')
MISSING = {'', '-', '--', 'n/a', 'na', 'nan', 'no data', 'no_data', 'none',
           'not available', 'null'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, payload):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def key(row):
    return tuple(row[field] for field in IDENTITY[:3])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True,
                        help='Exact root freeze record named in explicit execution authorization.')
    args = parser.parse_args()
    freeze_path = args.freeze.resolve()
    assert freeze_path.is_file(), 'Require existing root freeze record'
    json.loads(freeze_path.read_bytes())
    manifest = json.loads(MANIFEST.read_bytes())
    out = REVIEW/'DATA_INDEPENDENT_NUMERIC.json'
    assert not out.exists(), 'Refuse rerun/overwrite'
    selected, ignored_targets, controls = {}, set(), set()
    for compound in manifest['compounds']:
        for dose_level, dose in compound['doses'].items():
            for row in dose['samples']:
                sample_key = key(row)
                if compound['role'] in {'source', 'development'}:
                    assert sample_key not in selected
                    selected[sample_key] = {'identity': row, 'compound_label': compound['compound_label'],
                                            'role': compound['role'], 'dose_level': dose_level}
                else:
                    ignored_targets.add(sample_key)
        controls.update(key(row) for row in compound['controls_metadata_only'])
    assert len(selected) == 186 and len(ignored_targets) == 84
    assert not set(selected) & (ignored_targets | controls)
    raw = ROOT/manifest['raw_zip_relative']
    bindings = {MANIFEST.relative_to(ROOT).as_posix(): sha(MANIFEST),
                PROTOCOL.relative_to(ROOT).as_posix(): sha(PROTOCOL),
                Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__)),
                str(freeze_path): sha(freeze_path), raw.relative_to(ROOT).as_posix(): sha(raw)}
    assert bindings[raw.relative_to(ROOT).as_posix()] == manifest['inputs_sha256'][raw.relative_to(ROOT).as_posix()]
    started = {'utc': datetime.now(timezone.utc).isoformat(), 'input_sha256': bindings,
               'permission': 'Root explicit freeze/execution notice required outside this script',
               'prior_root_numeric_outputs_read': False, 'new_observations': 0}
    write(REVIEW/'DATA_CONVERSION_STARTED.json', started)
    found, numeric_rows = set(), []
    role_values = Counter()
    contacted_rows = 0
    selected_value_attempts = 0
    later_cast = control_cast = 0
    stage = 'open_zip'
    try:
        with zipfile.ZipFile(raw) as archive:
            names = archive.namelist()
            assert names == ['open_tggates_cell_viability.csv'], 'Unexpected raw member list'
            with archive.open(names[0]) as binary:
                reader = csv.reader(io.TextIOWrapper(binary, encoding='cp932', newline=''))
                stage = 'header'
                assert tuple(next(reader)) == HEADER, 'Unexpected header'
                for tokens in reader:
                    contacted_rows += 1
                    stage = 'row_identity'
                    assert len(tokens) == len(HEADER), 'Unexpected row width'
                    sample_key = tuple(tokens[:3])
                    if sample_key not in selected:
                        continue
                    spec = selected[sample_key]
                    assert sample_key not in found, 'Duplicate selected key'
                    assert tuple(tokens[:10]) == tuple(spec['identity'][field] for field in IDENTITY), 'Selected identity mismatch'
                    found.add(sample_key)
                    values, flags = {}, {}
                    for column, assay in ((10, 'DNA'), (11, 'LDH')):
                        stage = 'selected_'+assay+'_parse'
                        token = tokens[column].strip()
                        selected_value_attempts += 1
                        if token.casefold() in MISSING:
                            raise ValueError('Missing selected assay')
                        value = Decimal(token)
                        if not value.is_finite():
                            raise ValueError('Nonfinite selected assay')
                        values[assay] = str(value/Decimal(100))
                        flags[assay] = {'below_zero': value < 0, 'above_100': value > 100}
                        role_values[spec['role']] += 1
                    numeric_rows.append({'key': list(sample_key), 'compound_label': spec['compound_label'],
                                         'role': spec['role'], 'dose_level': spec['dose_level'],
                                         'normalized_assays_decimal': values, 'range_flags': flags})
        stage = 'complete_keys'
        assert found == set(selected), 'Selected keys missing'
        assert selected_value_attempts == 372 and len(numeric_rows) == 186
        assert role_values == {'source': 288, 'development': 84}
        assert later_cast == control_cast == 0
        grouped = defaultdict(list)
        for row in numeric_rows:
            grouped[row['compound_label'], row['role'], row['dose_level']].append(row)
        aggregates = []
        with localcontext() as context:
            context.prec = 40
            for (label, role, level), rows in sorted(grouped.items()):
                assay_stats = {}
                for assay in ('DNA', 'LDH'):
                    values = [Decimal(row['normalized_assays_decimal'][assay]) for row in rows]
                    mean = sum(values)/len(values)
                    variance = sum((value-mean)**2 for value in values)/(len(values)-1) if len(values) > 1 else Decimal(0)
                    assay_stats[assay] = {'mean_decimal': str(mean), 'sd_ddof1_decimal': str(variance.sqrt()),
                                          'n': len(values)}
                aggregates.append({'compound_label': label, 'role': role, 'dose_level': level,
                                   'assays': assay_stats})
        assert len(aggregates) == 93
        means = {(row['compound_label'], row['dose_level']): Decimal(row['assays']['DNA']['mean_decimal'])
                 for row in aggregates}
        source = sorted({row['compound_label'] for row in numeric_rows if row['role'] == 'source'})
        development = sorted({row['compound_label'] for row in numeric_rows if row['role'] == 'development'})
        source_high_median = statistics.median(means[label, 'High'] for label in source)
        source_offset_median = statistics.median(means[label, 'High']-means[label, 'Middle'] for label in source)
        baselines = {}
        for method in ('constant_085', 'middle_copy', 'source_high_median', 'source_median_offset'):
            rows = []
            for label in development:
                prediction = {'constant_085': Decimal('0.85'), 'middle_copy': means[label, 'Middle'],
                              'source_high_median': source_high_median,
                              'source_median_offset': means[label, 'Middle']+source_offset_median}[method]
                target = means[label, 'High']
                rows.append({'compound_label': label, 'prediction_decimal': str(prediction),
                             'target_decimal': str(target), 'absolute_error_decimal': str(abs(prediction-target))})
            mae = sum(Decimal(row['absolute_error_decimal']) for row in rows)/len(rows)
            baselines[method] = {'development_DNA_MAE_decimal': str(mae), 'per_compound': rows}
        result = {'status': 'INDEPENDENT_NUMERIC_SEALED_BEFORE_ROOT_COMPARISON',
                  'input_sha256': bindings, 'contacted_all_rows': contacted_rows,
                  'allowed_selected_records': len(numeric_rows), 'assay_casts': selected_value_attempts,
                  'role_assay_casts': dict(role_values), 'later_assay_casts': later_cast,
                  'control_assay_casts': control_cast, 'source_labels': len(source),
                  'development_labels': len(development), 'normalized_record_values': sorted(numeric_rows, key=lambda row: row['key']),
                  'condition_aggregates': aggregates, 'development_baselines': baselines,
                  'source_high_median_decimal': str(source_high_median),
                  'source_median_high_minus_middle_decimal': str(source_offset_median),
                  'new_biological_observations': 0, 'logical_raw_conversion_passes': 1,
                  'new_HTTP': 0, 'new_CEL': 0, 'new_fits': 0,
                  'prior_root_numeric_outputs_read': False,
                  'interpretation': 'Repeated computation on existing source/dev observations only; no confirmation or later evaluation.'}
        write(out, result)
        write(REVIEW/'DATA_INDEPENDENT_NUMERIC_SEAL.json', {'utc': datetime.now(timezone.utc).isoformat(),
              'result_sha256': sha(out), 'root_numeric_outputs_read_before_seal': False,
              'script_sha256': sha(Path(__file__)), 'input_sha256': bindings})
        print(json.dumps({'status': result['status'], 'records': len(numeric_rows), 'assay_casts': selected_value_attempts,
                          'later_casts': later_cast, 'control_casts': control_cast,
                          'result_sha256': sha(out)}, ensure_ascii=False))
        return 0
    except Exception as exc:
        write(REVIEW/'DATA_INDEPENDENT_FAILURE.json', {'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'ABORT_RETAINED', 'stage': stage, 'error_type': type(exc).__name__,
              'contacted_rows': contacted_rows, 'selected_key_count_seen': len(found),
              'selected_value_attempts': selected_value_attempts, 'completed_role_values': dict(role_values),
              'later_casts': later_cast, 'control_casts': control_cast, 'input_sha256': bindings,
              'dropped_or_repaired_rows': 0})
        print(json.dumps({'status': 'ABORT_RETAINED', 'stage': stage, 'error_type': type(exc).__name__}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
