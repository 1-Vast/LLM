"""Prefix-only ordinary forecasts of condition-mean CellTiter-Glo proxy responses."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
from statistics import mean
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/public_recovery_task'
METHODS = ('persistence', 'global_exp', 'latest_interval', 'first_cycle')
TIMES = (0, 7, 14, 21, 28)
GROUPS = [(sample, schedule) for sample in ('Vector Control', 'V600E')
          for schedule in ('Continuous', 'Intermittent')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, timepoints):
    summaries = {}
    counts = {}
    for day in timepoints:
        valid = []
        tally = dict(valid=0, missing=0, nonfinite=0, negative=0)
        for row in rows:
            token = row[str(day)].strip()
            if token in ('', 'NA', 'N/A', 'NaN'):
                tally['missing'] += 1
                continue
            value = float(token)
            if not math.isfinite(value):
                tally['nonfinite'] += 1
            else:
                valid.append(value)
                tally['valid'] += 1
                if value < 0:
                    tally['negative'] += 1
        if len(valid) < 3:
            raise ValueError(f'Insufficient observations at day {day}: {tally}')
        summaries[day] = mean(valid)
        counts[day] = tally
    return summaries, counts


if __name__ == '__main__':
    started = time.perf_counter()
    freeze = json.loads((OUT / 'NUMERIC_FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        assert digest(ROOT / name) == expected, name
    destination = OUT / 'pilot'
    destination.mkdir(exist_ok=True)
    assert not (destination / 'PREFIX_FORECASTS.json').exists()
    # CSV tokens include future text; future values are converted only after forecast sealing.
    raw = (OUT / 'root/count_header_source.body').read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    assert list(rows[0]) == ['sample', 'replicate', 'schedule'] + [str(t) for t in TIMES]
    assert len(rows) == 24
    grouped = {group: [r for r in rows if (r['sample'], r['schedule']) == group] for group in GROUPS}
    prefixes = []
    for (sample, schedule), records in grouped.items():
        assert len(records) == 6
        assert {r['replicate'] for r in records} == {str(i) for i in range(1, 7)}
        values, counts = summarize(records, (0, 7, 14))
        if values[0] <= 0 or values[7] <= 0 or values[14] < 0:
            raise ValueError('Invalid aggregate baseline, first-week denominator or square-root input')
        a, b = values[7] / values[0], values[14] / values[0]
        q = b / a
        predictions = dict(persistence=[b, b], global_exp=[b ** 1.5, b ** 2],
                           latest_interval=[b * q, b * q ** 2])
        predictions['first_cycle'] = ([b * a, b ** 2] if schedule == 'Intermittent'
                                      else list(predictions['latest_interval']))
        assert all(math.isfinite(p) and p >= 0 for v in predictions.values() for p in v)
        if schedule == 'Intermittent':
            assert predictions['first_cycle'][1] == predictions['global_exp'][1]
        else:
            assert predictions['first_cycle'] == predictions['latest_interval']
        prefixes.append(dict(sample=sample, schedule=schedule, means=values,
                             counts=counts, predictions=predictions))
    prefix_file = destination / 'PREFIX_FORECASTS.json'
    prefix_file.write_text(json.dumps(prefixes, indent=2), encoding='utf-8')
    (destination / 'PREDICTION_SEAL.json').write_text(json.dumps(
        dict(sha256=digest(prefix_file), query_values_converted=False), indent=2), encoding='utf-8')
    scored = []
    for prefix in prefixes:
        group = (prefix['sample'], prefix['schedule'])
        values, counts = summarize(grouped[group], (21, 28))
        truth = [values[t] / prefix['means'][0] for t in (21, 28)]
        assert all(math.isfinite(y) for y in truth)
        scores = {}
        for method, prediction in prefix['predictions'].items():
            squared = [(p - y) ** 2 for p, y in zip(prediction, truth)]
            absolute = [abs(p - y) for p, y in zip(prediction, truth)]
            assert all(math.isfinite(v) for v in squared + absolute)
            scores[method] = dict(mse28=squared[1], late_mse=mean(squared),
                                  mae28=absolute[1], squared_error=squared,
                                  absolute_error=absolute)
        scored.append(dict(sample=group[0], schedule=group[1], truth=truth,
                           query_counts=counts, scores=scores))
    summary = {method: {metric: mean(r['scores'][method][metric] for r in scored)
                        for metric in ('mse28', 'late_mse', 'mae28')} for method in METHODS}
    intermittent = [r for r in scored if r['schedule'] == 'Intermittent']
    passes = all(r['scores']['first_cycle']['late_mse'] < r['scores']['latest_interval']['late_mse']
                 for r in intermittent)
    result = dict(scored=scored, summary=summary, descriptive_gate=passes,
                  decision=('ORDINARY_RECURRENCE_ONLY_NO_NEW_CORE_GO' if passes else
                            'STOP_THIS_FIRST_CYCLE_RECURRENCE_CONFIGURATION'),
                  python=platform.python_version(), wall_seconds=time.perf_counter() - started,
                  scope='Four-condition exposed development assay proxy; no biological independence or RSI')
    (destination / 'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(summary=summary, descriptive_gate=passes, decision=result['decision']), indent=2))
