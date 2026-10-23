"""Independent raw-CSV audit of the frozen diagnostic; no root-module import."""
import csv
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path

base = Path('log/20261023/public_recovery_task')
out = base / 'source'
raw = (base / 'root/count_header_source.body').read_bytes()
rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
days = ('0', '7', '14', '21', '28')
methods = ('persistence', 'global_exp', 'latest_interval', 'first_cycle')
groups = [(sample, schedule) for sample in ('Vector Control', 'V600E')
          for schedule in ('Continuous', 'Intermittent')]
prefixes, scores, diagnostics = [], [], []
for sample, schedule in groups:
    cohort = [r for r in rows if (r['sample'], r['schedule']) == (sample, schedule)]
    assert len(cohort) == 6
    assert sorted(r['replicate'] for r in cohort) == [str(i) for i in range(1, 7)]
    means, counts = {}, {}
    for day in days:
        values = []
        tally = dict(valid=0, missing=0, nonfinite=0, negative=0)
        for record in cohort:
            token = record[day].strip()
            if token.lower() in ('', 'na', 'n/a', 'nan'):
                tally['missing'] += 1
                continue
            value = Decimal(token)
            if not value.is_finite():
                tally['nonfinite'] += 1
                continue
            values.append(value)
            tally['valid'] += 1
            tally['negative'] += int(value < 0)
        assert len(values) >= 3
        # Decimal accumulation differs from the root's float calculation.
        means[day] = float(sum(values) / len(values))
        counts[day] = tally
    assert means['0'] > 0
    g = {day: means[day] / means['0'] for day in days}
    a, b = g['7'], g['14']
    assert a > 0 and b >= 0
    q = b / a
    predictions = {
        'persistence': [b, b],
        'global_exp': [math.sqrt(b) * b, b * b],
        'latest_interval': [b * q, b * q * q],
        'first_cycle': ([b * a, b * b] if schedule == 'Intermittent'
                        else [b * q, b * q * q]),
    }
    assert all(math.isfinite(x) for pair in predictions.values() for x in pair)
    truth = [g['21'], g['28']]
    per_method = {}
    for method, pair in predictions.items():
        absolute = [abs(p - t) for p, t in zip(pair, truth)]
        squared = [(p - t) ** 2 for p, t in zip(pair, truth)]
        per_method[method] = dict(mse28=squared[1], late_mse=sum(squared) / 2,
                                  mae28=absolute[1], squared_error=squared,
                                  absolute_error=absolute)
    prefixes.append(dict(sample=sample, schedule=schedule,
                         means={d: means[d] for d in days[:3]},
                         counts={d: counts[d] for d in days[:3]},
                         predictions=predictions))
    scores.append(dict(sample=sample, schedule=schedule, truth=truth,
                       query_counts={d: counts[d] for d in days[3:]},
                       scores=per_method))
    diagnostics.append(dict(sample=sample, schedule=schedule,
                            all_means=means, all_counts=counts,
                            normalized_readouts=g))
summary = {method: {metric: sum(s['scores'][method][metric] for s in scores) / 4
                    for metric in ('mse28', 'late_mse', 'mae28')}
           for method in methods}
gate = all(s['scores']['first_cycle']['late_mse'] <
           s['scores']['latest_interval']['late_mse']
           for s in scores if s['schedule'] == 'Intermittent')
expected_prefix = json.loads((base / 'pilot/PREFIX_FORECASTS.json').read_bytes())
expected_result = json.loads((base / 'pilot/RESULT.json').read_bytes())
differences = []
numeric_count = 0
max_absolute_difference = 0.0

def compare(actual, expected, location):
    global numeric_count, max_absolute_difference
    if isinstance(actual, dict):
        if set(actual) != set(expected):
            differences.append(dict(path=location, error='keys'))
        for key in actual.keys() & expected.keys():
            compare(actual[key], expected[key], location + '/' + key)
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            differences.append(dict(path=location, error='length'))
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, location + '/' + str(index))
    elif isinstance(actual, (int, float)) and not isinstance(actual, bool):
        numeric_count += 1
        delta = abs(actual - expected)
        max_absolute_difference = max(max_absolute_difference, delta)
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            differences.append(dict(path=location, actual=actual, expected=expected))
    elif actual != expected:
        differences.append(dict(path=location, actual=actual, expected=expected))

compare(prefixes, expected_prefix, 'prefix')
compare(scores, expected_result['scored'], 'scored')
compare(summary, expected_result['summary'], 'summary')
compare(gate, expected_result['descriptive_gate'], 'gate')
compare('ORDINARY_RECURRENCE_ONLY_NO_NEW_CORE_GO', expected_result['decision'], 'decision')
freeze = json.loads((base / 'NUMERIC_FREEZE.json').read_bytes())
frozen_hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
                 for name, digest in freeze['files'].items()}
prediction_seal = json.loads((base / 'pilot/PREDICTION_SEAL.json').read_bytes())
seal_matches = hashlib.sha256((base / 'pilot/PREFIX_FORECASTS.json').read_bytes()).hexdigest() == prediction_seal['sha256']
result = dict(scope='independent arithmetic/provenance audit, not another experiment',
              raw_sha256=hashlib.sha256(raw).hexdigest(),
              rows=len(rows), groups=4, group_time_cells=20,
              diagnostics=diagnostics, rebuilt_prefix=prefixes,
              rebuilt_scored=scores, rebuilt_summary=summary,
              rebuilt_gate=gate, compared_numeric_fields=numeric_count,
              max_absolute_rounding_difference=max_absolute_difference,
              discrepancies=differences, frozen_hash_matches=frozen_hashes,
              prediction_seal_hash_matches=seal_matches,
              temporal_separation_claim='hash validates bytes, not inaccessible query or remote chronology',
              passed=not differences and all(frozen_hashes.values()) and seal_matches)
(out / 'RESULT_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: result[k] for k in ('rows', 'groups', 'compared_numeric_fields',
      'max_absolute_rounding_difference', 'rebuilt_summary', 'rebuilt_gate',
      'discrepancies', 'passed')}, indent=2))
