"""Fixed ordinary density forecasts across two declared experiment files."""
import hashlib
import json
import math
from pathlib import Path
import platform
import posixpath
from statistics import mean
import time
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/rechallenge_forecast'
INPUT = ROOT / 'log/20261023/rechallenge_task/root'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
REGIMENS = ('AAAA', 'ANAN')
METHODS = ('persistence', 'target_linear', 'target_last_interval', 'source_curve',
           'source_offset', 'source_affine', 'source_residual_trend', 'source_event', 'pooled_event_refit')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    assert not path.exists(), 'Preserve previous execution artifacts'
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8', newline='\n')


def read_density(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        targets = {e.attrib['Id']: e.attrib['Target'] for e in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        for sheet in workbook.findall('s:sheets/s:sheet', NS):
            name = sheet.attrib['name']
            if name not in REGIMENS:
                continue
            assert name not in result
            target = targets[sheet.attrib[REL]]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            tree = ET.fromstring(archive.read(member))
            observations = {}
            for row in tree.findall('s:sheetData/s:row', NS):
                if int(row.attrib['r']) < 4:
                    continue
                cells = {''.join(c for c in cell.attrib['r'] if c.isalpha()): cell for cell in row.findall('s:c', NS)}
                if 'A' not in cells and 'B' not in cells:
                    continue
                values = []
                for column in ('A', 'B'):
                    cell = cells[column]
                    assert cell.find('s:f', NS) is None, 'No formulas allowed'
                    assert cell.attrib.get('t', 'n') == 'n', 'Numeric source cells required'
                    value = float(cell.find('s:v', NS).text)
                    assert math.isfinite(value)
                    values.append(value)
                at, density = values
                assert at not in observations
                observations[at] = density
            assert set(observations) == {0, 24, 48, 72, 96}
            result[name] = [observations[t] for t in (0, 24, 48, 72, 96)]
    assert set(result) == set(REGIMENS)
    return result


def line_predict(x, y, queries):
    center_x, center_y = mean(x), mean(y)
    denominator = sum((v - center_x) ** 2 for v in x)
    slope = sum((a - center_x) * (b - center_y) for a, b in zip(x, y)) / denominator if denominator else 0.
    return [center_y + slope * (q - center_x) for q in queries]


def event_differences(curves):
    differences = {'A': [], 'N': []}
    for regimen, values in curves.items():
        for action, before, after in zip(regimen, values, values[1:]):
            differences[action].append(after - before)
    return differences


def predict_fold(source, target_prefix):
    assert set(source) == set(target_prefix) == set(REGIMENS)
    assert all(len(source[r]) == 5 and len(target_prefix[r]) == 3 for r in REGIMENS)
    source_differences = event_differences(source)
    target_differences = event_differences(target_prefix)
    forecasts = {}
    for regimen in REGIMENS:
        s, y = source[regimen], target_prefix[regimen]
        residuals = [a - b for a, b in zip(y, s)]
        trend = line_predict([0, 1, 2], residuals, [3, 4])
        methods = dict(persistence=[y[2], y[2]], target_linear=line_predict([0, 1, 2], y, [3, 4]),
                       target_last_interval=[y[2] + (h - 2) * (y[2] - y[1]) for h in (3, 4)],
                       source_curve=s[3:], source_offset=[v + mean(residuals) for v in s[3:]],
                       source_affine=line_predict(s[:3], y, s[3:]),
                       source_residual_trend=[a + b for a, b in zip(s[3:], trend)])
        for method, refit in (('source_event', False), ('pooled_event_refit', True)):
            rates = {a: mean(source_differences[a] + (target_differences[a] if refit else [])) for a in ('A', 'N')}
            current = y[2]
            methods[method] = []
            for action in regimen[2:]:
                current += rates[action]
                methods[method].append(current)
        # The fixed pooling weights are an ordinary mixture, not a new update.
        target_current = y[2]
        for index, action in enumerate(regimen[2:]):
            target_current += mean(target_differences[action])
            mixture = (2 * methods['source_event'][index] + target_current) / 3
            assert math.isclose(methods['pooled_event_refit'][index], mixture, rel_tol=1e-12, abs_tol=1e-12)
        assert set(methods) == set(METHODS)
        assert all(math.isfinite(value) for values in methods.values() for value in values)
        forecasts[regimen] = methods
    return forecasts


if __name__ == '__main__':
    started = time.perf_counter()
    freeze = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        assert digest(ROOT / name) == expected, name
    pilot = OUT / 'pilot'
    assert not pilot.exists(), 'Do not rerun or remove partial artifacts'
    pilot.mkdir()
    # Reciprocal CV legally uses each full file as the OTHER fold's source.
    # All numeric responses therefore materialize here; this is not blindness.
    data = {n: read_density(INPUT / f'transition_exp{n}.body') for n in (3, 4)}
    predictions = []
    for source_number, target_number in ((3, 4), (4, 3)):
        source = data[source_number]
        prefix = {r: data[target_number][r][:3] for r in REGIMENS}
        fold_started = time.perf_counter()
        forecast = predict_fold(source, prefix)
        predictions.append(dict(source=source_number, target=target_number, source_values=source,
                                target_prefix=prefix, predictions=forecast,
                                forecast_wall_seconds=time.perf_counter() - fold_started))
    save(pilot / 'FORECASTS.json', predictions)
    save(pilot / 'FORECAST_SEAL.json', dict(sha256=digest(pilot / 'FORECASTS.json'), scored=False,
                                          numeric_responses_already_decoded_as_reciprocal_sources=True))
    scored = []
    for fold in predictions:
        for regimen in REGIMENS:
            truth = data[fold['target']][regimen][3:]
            errors = {}
            for method, prediction in fold['predictions'][regimen].items():
                signed = [p - y for p, y in zip(prediction, truth)]
                squared = [v ** 2 for v in signed]
                absolute = [abs(v) for v in signed]
                errors[method] = dict(signed=signed, squared=squared, absolute=absolute,
                                      mse=mean(squared), mae=mean(absolute))
            scored.append(dict(target=fold['target'], regimen=regimen, truth=truth, errors=errors))
    summary = {m: {metric: mean(g['errors'][m][metric] for g in scored) for metric in ('mse', 'mae')} for m in METHODS}
    passes = all(g['errors']['pooled_event_refit']['mse'] < g['errors'][baseline]['mse']
                 for g in scored for baseline in ('source_event', 'persistence'))
    result = dict(scored=scored, summary=summary, descriptive_gate=passes,
                  decision=('ORDINARY_FEEDBACK_ONLY_NO_NEW_CORE_GO' if passes else 'STOP_THIS_FIXED_POOLED_EVENT_UPDATE_CONFIGURATION'),
                  python=platform.python_version(), wall_seconds=time.perf_counter() - started,
                  scope='Declared-file correlated development cohort prediction; no biological independence or RSI')
    save(pilot / 'RESULT.json', result)
    print(json.dumps(dict(summary=summary, descriptive_gate=passes, decision=result['decision']), indent=2))
