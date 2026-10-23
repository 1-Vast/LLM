"""One frozen source/development assay-headroom check; never cast later outcomes."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import time
import zipfile

import numpy as np
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from prepare import ROOT, LOG, IDENTITY_FIELDS, KEY_FIELDS, LEVELS, sample_key, write

MISSING = {'', 'na', 'n/a', 'nan', 'null', 'none', '-', '--', 'no data', 'no_data', 'not available'}
RESPONSE_COLUMNS = ['DNA(%)', 'LDH(%)']
ALPHAS = [0.1, 1.0, 10.0, 100.0]
KERNEL_SCALES = [0.5, 2.0]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(manifest_path, manifest, freeze_path):
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    expected = freeze['sha256']
    required = [manifest_path, Path(__file__), Path(__file__).with_name('prepare.py'), LOG / 'PROTOCOL.md']
    required += [ROOT / relative for relative in manifest['inputs_sha256']]
    for path in required:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in expected or sha(path) != expected[relative]:
            raise RuntimeError('Required frozen input absent or changed: ' + relative)
    for relative, digest in manifest['inputs_sha256'].items():
        if sha(ROOT / relative) != digest:
            raise RuntimeError('Manifest input changed: ' + relative)
    return sha(freeze_path)


def permitted_samples(manifest):
    allowed = {}
    for compound in manifest['compounds']:
        if compound['role'] not in ('source', 'development'):
            continue
        for dose in compound['doses'].values():
            for sample in dose['samples']:
                key = sample_key(sample)
                if key in allowed:
                    raise ValueError('Repeated selected sample key')
                allowed[key] = sample
    return allowed


def project_rows(rows, allowed):
    """Filter by identity first; skipped rows' response columns are never accessed."""
    records, invalid, seen, exposure = [], [], set(), []
    counters = {name: {column: 0 for column in RESPONSE_COLUMNS} for name in
                ['assay_field_accesses', 'numeric_cast_attempts', 'numeric_parse_successes',
                 'finite_numeric_cast_successes']}
    scanned = 0
    for row in rows:
        scanned += 1
        key = sample_key(row)
        if key not in allowed:
            continue
        if key in seen:
            invalid.append({'key': list(key), 'reason': 'duplicate_selected_key'})
            continue
        seen.add(key)
        if any(row[field] != allowed[key][field] for field in IDENTITY_FIELDS):
            invalid.append({'key': list(key), 'reason': 'selected_identity_mismatch'})
            continue
        values, flags, assays = [], [], {}
        for column in RESPONSE_COLUMNS:
            counters['assay_field_accesses'][column] += 1
            raw = row[column]
            if raw is None or raw.strip().casefold() in MISSING:
                assays[column] = {'status': 'missing'}
                invalid.append({'key': list(key), 'assay': column, 'reason': 'missing'})
                break
            counters['numeric_cast_attempts'][column] += 1
            try:
                value = float(raw)
            except (ValueError, TypeError):
                assays[column] = {'status': 'unparseable'}
                invalid.append({'key': list(key), 'assay': column, 'reason': 'unparseable'})
                break
            counters['numeric_parse_successes'][column] += 1
            if not math.isfinite(value):
                assays[column] = {'status': 'nonfinite'}
                invalid.append({'key': list(key), 'assay': column, 'reason': 'nonfinite'})
                break
            counters['finite_numeric_cast_successes'][column] += 1
            assays[column] = {'status': 'finite', 'published_percentage': value,
                              'normalized_value': value / 100.0}
            values.append(value / 100.0)
            if value < 0 or value > 100:
                flags.append({'assay': column, 'below_zero': value < 0, 'above_100': value > 100})
        if len(values) == 2:
            records.append({'key': list(key), 'values': values, 'quality_flags': flags})
        exposure.append({'key': list(key), 'assays': assays, 'complete_valid_record': len(values) == 2})
    for key in sorted(set(allowed) - seen):
        invalid.append({'key': list(key), 'reason': 'selected_key_absent'})
    return {'records': records, 'invalid': invalid, 'raw_rows_scanned': scanned,
            'selected_keys_seen': len(seen), 'expected_selected_keys': len(allowed),
            'numeric_exposure_records': exposure, 'exposure_counters': counters,
            'skipped_response_columns_accessed': 0,
            'finite_outside_0_100_records_retained': sum(bool(row['quality_flags']) for row in records)}


def aggregate(manifest, projection):
    by_key = {tuple(row['key']): row['values'] for row in projection['records']}
    result = []
    for compound in manifest['compounds']:
        if compound['role'] not in ('source', 'development'):
            continue
        row = {field: compound[field] for field in ['compound_label', 'block_id', 'role', 'fingerprint_on_bits']}
        row['unit'] = compound['doses']['High']['unit']
        row['doses'] = {}
        for level in LEVELS:
            dose = compound['doses'][level]
            values = np.asarray([by_key[sample_key(sample)] for sample in dose['samples']], dtype=float)
            row['doses'][level] = {'concentration': float(dose['value']), 'n': len(values),
                                    'mean': values.mean(axis=0).tolist(),
                                    'sd': values.std(axis=0, ddof=1).tolist() if len(values) > 1 else [0.0, 0.0]}
        result.append(row)
    return sorted(result, key=lambda row: row['compound_label'])


def feature_arrays(rows, feature_type, unit_categories):
    continuous, fixed = [], []
    for row in rows:
        high, middle = row['doses']['High'], row['doses']['Middle']
        values = [math.log10(high['concentration']),
                  math.log10(high['concentration'] / middle['concentration'])]
        if feature_type == 'full_middle':
            values += middle['mean'] + middle['sd']
        elif feature_type != 'dose_chem':
            raise ValueError('Unknown feature type')
        fingerprint = np.zeros(2048)
        fingerprint[row['fingerprint_on_bits']] = 1
        continuous.append(values)
        fixed.append(np.r_[[float(row['unit'] == unit) for unit in unit_categories], fingerprint])
    return np.asarray(continuous), np.asarray(fixed)


def design(train, test, feature_type, units):
    train_cont, train_fixed = feature_arrays(train, feature_type, units)
    test_cont, test_fixed = feature_arrays(test, feature_type, units)
    scaler = StandardScaler().fit(train_cont)
    return np.c_[scaler.transform(train_cont), train_fixed], np.c_[scaler.transform(test_cont), test_fixed]


def targets(rows, level='High'):
    return np.asarray([row['doses'][level]['mean'] for row in rows])


def configurations():
    result = [{'family': family} for family in ['constant_085', 'constant_source_median',
              'middle_copy', 'median_residual', 'tanimoto_residual']]
    for features in ['dose_chem', 'full_middle']:
        for alpha in ALPHAS:
            result.append({'family': 'ridge_' + features, 'features': features, 'alpha': alpha})
            for scale in KERNEL_SCALES:
                result.append({'family': 'krr_' + features, 'features': features,
                               'alpha': alpha, 'kernel_scale': scale})
    return result


def fit_predict(train, test, config, units, ledger):
    family = config['family']
    ledger['active_fit'] = {'status': 'STARTED', 'stage': ledger.get('fit_stage', 'synthetic_or_unspecified'),
                            'config': config,
                            'heldout_proxy_blocks': sorted({row['block_id'] for row in test}),
                            'train_labels': [row['compound_label'] for row in train],
                            'test_labels': [row['compound_label'] for row in test]}
    ledger['pipeline_fits'] += 1
    ledger['pipeline_fits_by_family'][family] += 1
    y_train, y_middle = targets(train), targets(train, 'Middle')
    if family == 'constant_085':
        return np.full((len(test), 2), 0.85)
    if family == 'constant_source_median':
        return np.tile(np.median(y_train, axis=0), (len(test), 1))
    if family == 'middle_copy':
        return targets(test, 'Middle')
    if family == 'median_residual':
        return targets(test, 'Middle') + np.median(y_train - y_middle, axis=0)
    if family == 'tanimoto_residual':
        predictions = []
        for row in test:
            bits = set(row['fingerprint_on_bits'])
            similarities = []
            for other in train:
                other_bits = set(other['fingerprint_on_bits'])
                union = len(bits | other_bits)
                similarity = len(bits & other_bits) / union if union else 1.0
                similarities.append(similarity)
            index = min(range(len(train)), key=lambda i: (-similarities[i], train[i]['compound_label']))
            predictions.append(np.asarray(row['doses']['Middle']['mean']) + y_train[index] - y_middle[index])
        return np.asarray(predictions)
    x_train, x_test = design(train, test, config['features'], units)
    ledger['sklearn_fit_calls'] += 1
    if family.startswith('ridge_'):
        model = Ridge(alpha=config['alpha'], solver='lsqr', tol=1e-8)
        return model.fit(x_train, y_train).predict(x_test)
    if family.startswith('krr_'):
        distances = np.maximum(((x_train[:, None, :] - x_train[None, :, :]) ** 2).sum(axis=2), 0.0)
        positive = distances[np.triu_indices(len(train), k=1)]
        positive = positive[positive > 0]
        median = float(np.median(positive)) if len(positive) else 1.0
        denominator = median * config['kernel_scale']
        kernel_train = np.exp(-distances / denominator)
        test_distances = ((x_test[:, None, :] - x_train[None, :, :]) ** 2).sum(axis=2)
        kernel_test = np.exp(-test_distances / denominator)
        model = KernelRidge(alpha=config['alpha'], kernel='precomputed')
        prior = y_train.mean(axis=0)
        return model.fit(kernel_train, y_train - prior).predict(kernel_test) + prior
    raise ValueError('Unknown family')


def errors(predictions, rows):
    losses = np.abs(np.asarray(predictions) - targets(rows))
    return {'dna_mae': float(losses[:, 0].mean()), 'ldh_mae': float(losses[:, 1].mean())}


def group_losses(rows, predictions):
    losses = np.abs(np.asarray(predictions) - targets(rows))
    result = []
    for block in sorted({row['block_id'] for row in rows}):
        indices = [i for i, row in enumerate(rows) if row['block_id'] == block]
        result.append({'block_id': block, 'compound_labels': [rows[i]['compound_label'] for i in indices],
                       'compound_count': len(indices), 'dna_loss_sum': float(losses[indices, 0].sum()),
                       'ldh_loss_sum': float(losses[indices, 1].sum()),
                       'dna_mae': float(losses[indices, 0].mean()),
                       'ldh_mae': float(losses[indices, 1].mean())})
    return result


def bootstrap_groups(losses_by_family, seed=20261022, repeats=10000):
    families = sorted(losses_by_family)
    first = losses_by_family[families[0]]
    ids = [row['block_id'] for row in first]
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(ids), size=(repeats, len(ids)))
    result = {}
    for family in families:
        rows = losses_by_family[family]
        assert [row['block_id'] for row in rows] == ids
        counts = np.asarray([row['compound_count'] for row in rows])
        result[family] = {}
        for assay in ['dna', 'ldh']:
            sums = np.asarray([row[assay + '_loss_sum'] for row in rows])
            samples = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
            result[family][assay + '_mae_percentile_95'] = np.quantile(samples, [0.025, 0.975]).tolist()
    return {'seed': seed, 'repeats': repeats, 'proxy_blocks': len(ids), 'families': result,
            'interpretation': 'Descriptive whole-proxy-block resampling of these development labels; models fixed. '
                              'Does not correct development-family selection or prove donor/culture generalization.',
            'additional_significance_gate': False}


def select_source(source, units, ledger):
    blocks = sorted({row['block_id'] for row in source})
    if len(blocks) != 24:
        raise ValueError('Expected 24 source proxy blocks')
    candidate_scores, best = [], {}
    for number, config in enumerate(configurations()):
        predictions = np.zeros((len(source), 2))
        for block in blocks:
            train = [row for row in source if row['block_id'] != block]
            indices = [i for i, row in enumerate(source) if row['block_id'] == block]
            predictions[indices] = fit_predict(train, [source[i] for i in indices], config, units, ledger)
            ledger['active_fit']['status'] = 'COMPLETE'
        score = {'candidate_number': number, 'config': config, **errors(predictions, source),
                 'estimate_type': 'source candidate OOF; choosing this configuration makes selected CV optimistic'}
        candidate_scores.append(score)
        family = config['family']
        if family not in best or score['dna_mae'] < best[family]['score']['dna_mae']:
            best[family] = {'config': config, 'score': score, 'predictions': predictions.tolist(),
                            'group_losses': group_losses(source, predictions)}
    return candidate_scores, best


def prediction_rows(rows, predictions):
    return [{'compound_label': row['compound_label'], 'block_id': row['block_id'],
             'target': row['doses']['High']['mean'], 'prediction': list(prediction)}
            for row, prediction in zip(rows, predictions)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True)
    args = parser.parse_args()
    manifest_path = LOG / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    freeze_sha = verify_freeze(manifest_path, manifest, args.freeze.resolve())
    start = time.monotonic()
    write(LOG / 'STARTED.json', {'utc': datetime.now(timezone.utc).isoformat(), 'freeze_sha256': freeze_sha,
                               'later_values_numeric_permission': False})
    ledger = {'pipeline_fits': 0, 'sklearn_fit_calls': 0, 'pipeline_fits_by_family': Counter(),
              'new_http_calls': 0, 'new_provider_calls': 0, 'new_cel_downloads': 0,
              'later_outcome_values_cast': 0, 'controls_outcome_values_cast': 0}
    receipt = {'status': 'FAILED', 'freeze_sha256': freeze_sha}
    stage = 'raw_projection'
    try:
        with zipfile.ZipFile(ROOT / manifest['raw_zip_relative']) as archive:
            members = [item for item in archive.infolist() if item.filename.lower().endswith('.csv')]
            if len(members) != 1 or members[0].file_size > 10_000_000:
                raise ValueError('Unexpected raw member')
            raw = archive.read(members[0])
        reader = csv.DictReader(io.StringIO(raw.decode('cp932')))
        if set(reader.fieldnames or []) != set(IDENTITY_FIELDS + RESPONSE_COLUMNS):
            raise ValueError('Raw schema mismatch')
        projection = project_rows(reader, permitted_samples(manifest))
        write(LOG / 'FUNCTIONAL_PROJECTION.json', projection)
        receipt['projection_records'] = len(projection['records'])
        receipt['invalid_records'] = len(projection['invalid'])
        ledger['outcome_exposure'] = projection['exposure_counters']
        if projection['invalid']:
            receipt['status'] = 'NUMERICAL_QUALIFICATION_ABORT'
            return 2
        stage = 'aggregation'
        rows = aggregate(manifest, projection)
        write(LOG / 'CONDITION_MEANS.json', rows)
        source = [row for row in rows if row['role'] == 'source']
        development = [row for row in rows if row['role'] == 'development']
        assert len({row['block_id'] for row in development}) == 7
        stage = 'source_cv'
        ledger['fit_stage'] = stage
        candidate_scores, best = select_source(source, manifest['unit_categories'], ledger)
        write(LOG / 'SOURCE_CV.json', {'candidates': candidate_scores,
              'selected': {family: values['score'] for family, values in best.items()},
              'selected_group_losses': {family: values['group_losses'] for family, values in best.items()},
              'selected_cv_is_unbiased_nested_estimate': False,
              'weighting': 'Every compound label equal; proxy-block held out together.'})
        write(LOG / 'SOURCE_SELECTED_PREDICTIONS.json', {
              family: prediction_rows(source, values['predictions']) for family, values in best.items()})
        stage = 'development_prediction'
        ledger['fit_stage'] = stage
        predictions, scores, dev_group_losses = {}, {}, {}
        for family, values in best.items():
            pred = fit_predict(source, development, values['config'], manifest['unit_categories'], ledger)
            ledger['active_fit']['status'] = 'COMPLETE'
            predictions[family] = prediction_rows(development, pred)
            scores[family] = {**errors(pred, development), 'source_selected_config': values['config']}
            dev_group_losses[family] = group_losses(development, pred)
        write(LOG / 'DEVELOPMENT_PREDICTIONS.json', predictions)
        write(LOG / 'DEVELOPMENT_GROUP_LOSSES.json', dev_group_losses)
        write(LOG / 'DEVELOPMENT_BOOTSTRAP.json', bootstrap_groups(dev_group_losses))
        winner = min(scores, key=lambda family: (scores[family]['dna_mae'], family))
        value = scores[winner]['dna_mae']
        decision = 'STOP_THIS_002_ABSOLUTE_GAIN_CONFIGURATION' if value <= 0.02 else 'GO_ONLY_TO_SEPARATELY_FROZEN_RNA_PILOT'
        write(LOG / 'HEADROOM_RESULT.json', {'status': 'DEVELOPMENT_HEADROOM_ONLY', 'development': scores,
              'best_development_family': winner, 'best_development_dna_mae': value,
              'absolute_usefulness_gate': 0.02, 'relative_usefulness_gate_for_later_pilot': 0.10,
              'decision': decision, 'rna_or_world_value_tested': False,
              'best_family_is_development_selected': True, 'unbiased_performance_estimate': False,
              'later_values_cast': 0, 'independent_donors_inferred': False,
              'scope': 'Finite released catalog with name-derived proxy blocking; no confirmatory efficacy or RSI result.'})
        receipt['status'] = 'COMPLETE_DEVELOPMENT_HEADROOM_CHECK'
        receipt['decision'] = decision
        return 0
    except Exception as exc:
        receipt['error_type'] = type(exc).__name__
        receipt['failed_stage'] = stage
        ledger['failed_pipeline_attempts'] = int(ledger.get('active_fit', {}).get('status') == 'STARTED')
        return 1
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - start,
                       ledger=ledger, logical_costs=manifest['costs'])
        write(LOG / 'RUN_RECEIPT.json', receipt)
        print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
