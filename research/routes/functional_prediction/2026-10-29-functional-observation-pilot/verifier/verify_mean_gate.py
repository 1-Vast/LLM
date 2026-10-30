import time
WALL_START = time.perf_counter()
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback
from collections import Counter

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent
SOURCE = Path(r'D:\MAESTRO\research\2026-10-29-functional-joint-discovery\sources\root\hts001_raw.body')
SOURCE_SHA = 'e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617'
PROTOCOL_RECEIPT_SHA = '682b8392597dbc9a06788369f679382deacba7eaac6f583e5068035cc94ec332'
CELLS = ['BR1', 'DS3', 'DS7', 'DS8', 'DS9', 'MGH', 'PC9']
ROLES = ['BDFHJLN', 'CEGIKMO']
ATTEMPTS = 0
TERMINATIONS = Counter()
STAGE = 'setup'
FIT_LOG = None


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in [
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage']]


def resources():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    info = MemoryCounters()
    info.cb = ctypes.sizeof(info)
    require(psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(info), info.cb), 'memory accounting failed')
    return dict(cpu_seconds=time.process_time(), wall_seconds=time.perf_counter() - WALL_START,
                peak_working_set_bytes=info.PeakWorkingSetSize)


def check_resources():
    usage = resources()
    require(usage['cpu_seconds'] <= 120, 'CPU ceiling exceeded')
    require(usage['wall_seconds'] <= 180, 'wall ceiling exceeded')
    require(usage['peak_working_set_bytes'] <= 512 * 1024 * 1024, 'working-set ceiling exceeded')
    return usage


def finite(value, label):
    require(bool(np.all(np.isfinite(value))), 'nonfinite ' + label)


def frozen_inputs():
    require(digest(EPISODE / 'protocol_receipt_v1_1.json') == PROTOCOL_RECEIPT_SHA, 'protocol receipt drift')
    receipt = json.loads((EPISODE / 'protocol_receipt_v1_1.json').read_text(encoding='utf-8'))
    checked = {}
    # Author implementation is neither opened nor hashed by this independent verifier.
    for name, expected in receipt['files'].items():
        if name in ('run_mean_gate.py', 'launch_primary.py'):
            continue
        actual = digest(EPISODE / name)
        require(actual == expected, 'frozen input drift: ' + name)
        checked[name] = actual
    meta = json.loads((EPISODE / 'metadata_qualification.json').read_text(encoding='utf-8'))
    draw_receipt = json.loads((EPISODE / 'bootstrap_input_receipt.json').read_text(encoding='utf-8'))
    draws = np.load(EPISODE / 'bootstrap_draws.npy', allow_pickle=False)
    require(draws.shape == (500, 7, 2, 7), 'draw shape mismatch')
    require(draws.dtype == np.dtype('int64'), 'draw type mismatch')
    require(bool(np.all((draws >= 0) & (draws <= 6))), 'draw range mismatch')
    require(draw_receipt['shape'] == [500, 7, 2, 7] and draw_receipt['dtype'] == 'int64', 'draw receipt mismatch')
    require(draw_receipt['seed'] == 20261029 and draw_receipt['generator'] == 'NumPy PCG64', 'draw generator mismatch')
    require(draw_receipt['sha256'] == checked['bootstrap_draws.npy'], 'draw identity mismatch')
    require(meta['source_sha256'] == SOURCE_SHA, 'metadata source mismatch')
    return meta, draws, checked


def read_whitelist(meta):
    global ATTEMPTS
    require(SOURCE.stat().st_size == 3039472, 'source size mismatch')
    require(digest(SOURCE) == SOURCE_SHA, 'source hash mismatch')
    expected = {}
    time_by_cell = {}
    for cell in CELLS:
        item = meta['cells'][cell]
        plate = 'HTS001_' + cell + '-2'
        require(item['plates'] == [plate] and len(item['trajectories']) == 28, 'plate/trajectory mismatch')
        well_set = {row + col for role in ROLES for row in role for col in ('02', '23')}
        require(set(item['wells']) == well_set, 'well roster mismatch')
        grid = sorted({float(p['time']) for tr in item['trajectories'] for p in tr['points'] if float(p['time']) < 72})
        require(9 <= len(grid) <= 15 and grid[-1] > grid[0], 'invalid eligible grid')
        time_by_cell[cell] = grid
        coordinates = set()
        for trajectory in item['trajectories']:
            require(trajectory['plate'] == plate and trajectory['well'] in well_set, 'trajectory identity mismatch')
            eligible = [p for p in trajectory['points'] if float(p['time']) < 72]
            require(sorted(float(p['time']) for p in eligible) == grid, 'incomplete trajectory grid')
            for point in eligible:
                row_number = int(point['source_row'])
                coordinate = (cell, plate, trajectory['well'], point['time'])
                require(row_number not in expected and coordinate not in coordinates, 'duplicate whitelist coordinate')
                expected[row_number] = coordinate
                coordinates.add(coordinate)
    values = {}
    with SOURCE.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        header = next(reader)
        needed = ['drug1', 'drug1.conc', 'drug1.units', 'cell.line', 'upid', 'well', 'time', 'cell.count']
        require(all(header.count(name) == 1 for name in needed), 'missing/duplicate header')
        positions = {name: header.index(name) for name in needed}
        rows_seen = 0
        for line_number, fields in enumerate(reader, start=2):
            rows_seen += 1
            require(len(fields) == len(header), 'malformed CSV row')
            # Index metadata only until every whitelist eligibility condition passes.
            drug = fields[positions['drug1']]
            if drug != 'control':
                require(line_number not in expected, 'required control identity changed')
                continue
            dose = float(fields[positions['drug1.conc']])
            require(math.isfinite(dose) and dose == 0.0, 'control dose not exact zero')
            frame = float(fields[positions['time']])
            require(math.isfinite(frame), 'nonfinite control time')
            if frame >= 72:
                require(line_number not in expected, 'required frame outside window')
                continue
            require(line_number in expected, 'unexpected eligible control row')
            cell, plate, well, time_text = expected[line_number]
            require(fields[positions['cell.line']] == cell and fields[positions['upid']] == plate,
                    'cell/plate mismatch before response access')
            require(fields[positions['well']] == well and fields[positions['time']] == time_text,
                    'well/time mismatch before response access')
            require(fields[positions['drug1.units']] == 'M', 'unit mismatch before response access')
            ATTEMPTS += 1  # Immediately precedes the only count-field access/conversion.
            count = float(fields[positions['cell.count']])
            require(math.isfinite(count) and count >= 0.0, 'invalid required control count')
            key = (cell, well, frame)
            require(key not in values, 'duplicate response coordinate')
            values[key] = count
            if ATTEMPTS % 100 == 0:
                check_resources()
    require(rows_seen == meta['source_rows'], 'source row count mismatch')
    require(len(values) == len(expected), 'missing required control response')
    plates = []
    for cell in CELLS:
        frames = np.asarray(time_by_cell[cell], dtype=np.float64)
        arrays = [np.asarray([[[values[(cell, row + col, t)] for t in frames]
                              for col in ('02', '23')] for row in role], dtype=np.float64)
                  for role in ROLES]
        plates.append((frames, arrays))
    return plates


def fit_plate(cell, frames, train, validation):
    check_resources()
    mean_train = train.mean(axis=(0, 1))
    mean_validation = validation.mean(axis=(0, 1))
    scale2 = float(np.mean(mean_train ** 2))
    require(math.isfinite(scale2) and scale2 > 0, 'nonpositive/nonfinite training scale')
    scale = math.sqrt(scale2)
    target = mean_train / scale
    u = (frames - frames[0]) / (frames[-1] - frames[0])
    basis0 = np.column_stack((np.ones_like(u), u))
    basis1 = np.column_stack((np.ones_like(u), u, u ** 2))
    fits = []
    for basis in (basis0, basis1):
        start = np.asarray([math.log(float(np.mean(target))), 0.0]) if not fits else np.r_[fits[0].x, 0.0]

        def residual(theta):
            check_resources()
            prediction = np.exp(basis @ theta)
            finite(prediction, 'optimizer prediction')
            return prediction - target

        def jacobian(theta):
            prediction = np.exp(basis @ theta)
            finite(prediction, 'Jacobian prediction')
            return prediction[:, None] * basis

        fitted = least_squares(residual, start, jac=jacobian, method='trf',
                               ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=200,
                               bounds=(-np.inf, np.inf))
        TERMINATIONS[str(fitted.status)] += 1
        FIT_LOG.write(json.dumps(dict(stage=STAGE, cell=cell, model='baseline' if not fits else 'curvature',
                                      success=bool(fitted.success), status=int(fitted.status),
                                      message=str(fitted.message), nfev=int(fitted.nfev),
                                      njev=None if fitted.njev is None else int(fitted.njev),
                                      parameters_normalized=[float(v) if math.isfinite(v) else repr(v) for v in fitted.x]),
                                 allow_nan=False) + '\n')
        FIT_LOG.flush()
        require(fitted.success and fitted.status > 0, 'optimizer failed: ' + str(fitted.message))
        finite(fitted.x, 'parameters')
        fits.append(fitted)
    model_results = []
    normalized_sses = []
    losses = []
    for basis, fitted in zip((basis0, basis1), fits):
        parameters = fitted.x.copy()
        parameters[0] += math.log(scale)
        prediction = np.exp(basis @ parameters)
        normalized_sse = float(np.sum(fitted.fun ** 2))
        raw_sse = float(np.sum((mean_train - prediction) ** 2))
        loss = float(np.mean((mean_validation - prediction) ** 2))
        finite([normalized_sse, raw_sse, loss], 'objective/loss')
        finite(prediction, 'raw prediction')
        finite(parameters, 'raw parameters')
        normalized_sses.append(normalized_sse)
        losses.append(loss)
        model_results.append(dict(parameters_raw=parameters.tolist(), prediction_raw=prediction.tolist(),
                                  training_SSE_normalized=normalized_sse, training_SSE_raw=raw_sse,
                                  validation_MSE_raw=loss, status=int(fitted.status), message=str(fitted.message),
                                  nfev=int(fitted.nfev), njev=int(fitted.njev)))
    require(normalized_sses[1] <= normalized_sses[0] + 1e-10 * (1 + normalized_sses[0]), 'nestedness violation')
    score = float((losses[0] - losses[1]) / scale2)
    finite(score, 'plate score')
    return dict(cell=cell, times=frames.tolist(), training_mean=mean_train.tolist(),
                validation_mean=mean_validation.tolist(), scale_squared=scale2,
                baseline=model_results[0], curvature=model_results[1], D=score)


def execute():
    global np, least_squares, STAGE, FIT_LOG
    # Exclusive creation prevents all automatic or manual replays of this computation.
    receipt_path = HERE / 'execution_receipt.json'
    with receipt_path.open('x', encoding='utf-8') as handle:
        json.dump(dict(state='STARTED_NO_REPLAY', count_access_attempts=0,
                       primary_code_or_results_read=False, script_sha256=digest(Path(__file__))), handle)
    result = dict(outcome='INCONCLUSIVE', point=None, bootstrap_completed=0,
                  primary_code_or_results_read=False, errors=[])
    try:
        check_resources()
        import numpy as np
        import scipy
        from scipy.optimize import least_squares
        FIT_LOG = (HERE / 'solver_results.jsonl').open('x', encoding='utf-8')
        result['solver'] = dict(name='scipy.optimize.least_squares', scipy_version=scipy.__version__,
                                numpy_version=np.__version__, method='trf', jacobian='analytic',
                                ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=200,
                                bounds='unbounded', dtype='float64')
        np.seterr(over='raise', invalid='raise', divide='raise')
        STAGE = 'frozen_input_validation'
        meta, draws, checked = frozen_inputs()
        result['checked_inputs'] = checked
        STAGE = 'control_only_count_parsing'
        check_resources()
        plates = read_whitelist(meta)
        STAGE = 'original_fits'
        check_resources()
        point = [fit_plate(cell, frames, arrays[0], arrays[1])
                 for cell, (frames, arrays) in zip(CELLS, plates)]
        delta = float(np.mean([p['D'] for p in point]))
        finite(delta, 'original Delta')
        result['point'] = dict(plates=point, Delta=delta)
        save(HERE / 'point_result.json', result['point'])
        bootstrap_deltas = []
        with (HERE / 'bootstrap_results.jsonl').open('x', encoding='utf-8') as full, \
             (HERE / 'bootstrap_scores.csv').open('x', encoding='utf-8', newline='') as simple:
            writer = csv.writer(simple)
            writer.writerow(['draw', 'status', 'Delta'] + ['D_' + c for c in CELLS])
            for b in range(500):
                STAGE = 'bootstrap_draw_' + str(b)
                record = dict(draw=b, status='INCONCLUSIVE', plates=[])
                try:
                    check_resources()
                    for c, (cell, (frames, arrays)) in enumerate(zip(CELLS, plates)):
                        record['plates'].append(fit_plate(cell, frames, arrays[0][draws[b, c, 0]],
                                                         arrays[1][draws[b, c, 1]]))
                    score = float(np.mean([p['D'] for p in record['plates']]))
                    finite(score, 'bootstrap Delta')
                    record.update(status='COMPLETE', Delta=score)
                    bootstrap_deltas.append(score)
                    writer.writerow([b, 'COMPLETE', score] + [p['D'] for p in record['plates']])
                    result['bootstrap_completed'] += 1
                except Exception as error:
                    record['error'] = str(error)
                    writer.writerow([b, 'INCONCLUSIVE', ''] + [''] * 7)
                    raise
                finally:
                    full.write(json.dumps(record, allow_nan=False) + '\n')
                    full.flush()
                    simple.flush()
        STAGE = 'classification'
        check_resources()
        q05, q95 = np.quantile(bootstrap_deltas, [0.05, 0.95], method='linear')
        positive_fraction = float(np.mean(np.asarray(bootstrap_deltas) > 0))
        finite([q05, q95, positive_fraction], 'stability summary')
        result.update(quantile_05=float(q05), quantile_95=float(q95),
                      fraction_positive=positive_fraction, bootstrap_Delta=bootstrap_deltas)
        if delta > 0 and q05 > 0:
            result['outcome'] = 'CONDITIONAL_HELDOUT_CURVATURE_GAIN'
        elif delta < 0 and q95 < 0:
            result['outcome'] = 'EXPONENTIAL_PREFERRED_IN_THIS_COMPARISON'
        check_resources()
    except Exception as error:
        result['outcome'] = 'INCONCLUSIVE'
        result['errors'].append(dict(stage=STAGE, type=type(error).__name__, message=str(error),
                                     traceback=traceback.format_exc()))
    result['count_access_attempts'] = ATTEMPTS
    if FIT_LOG is not None:
        FIT_LOG.close()
    result['termination_status_counts'] = dict(TERMINATIONS)
    result['uncompleted_draws'] = list(range(result['bootstrap_completed'], 500))
    try:
        check_resources()
    except Exception as error:
        result['outcome'] = 'INCONCLUSIVE'
        result['errors'].append(dict(stage='preoutput_resource_check', message=str(error)))
    save(HERE / 'verification_result.json', result)
    artifact_hashes = {name: digest(HERE / name) for name in (
        'point_result.json', 'bootstrap_results.jsonl', 'bootstrap_scores.csv', 'solver_results.jsonl', 'verification_result.json')
        if (HERE / name).exists()}
    usage = resources()
    within = usage['cpu_seconds'] <= 120 and usage['wall_seconds'] <= 180 and usage['peak_working_set_bytes'] <= 512 * 1024 * 1024
    if not within:
        result['outcome'] = 'INCONCLUSIVE'
        result['errors'].append(dict(stage='postoutput_resource_check', message='ceiling exceeded'))
        save(HERE / 'verification_result.json', result)
        artifact_hashes['verification_result.json'] = digest(HERE / 'verification_result.json')
    save(receipt_path, dict(state='FROZEN_NO_REPLAY', outcome=result['outcome'],
                            count_access_attempts=ATTEMPTS, bootstrap_completed=result['bootstrap_completed'],
                            primary_code_or_results_read=False, stage=STAGE, resources=resources(),
                            resource_checks_passed=within, artifact_sha256=artifact_hashes,
                            script_sha256=digest(Path(__file__)),
                            limits=dict(cpu_seconds=120, wall_seconds=180, peak_working_set_bytes=536870912),
                            limits_enforcement='cooperative; outer subprocess timeout; no OS CPU/memory hard limit'))
    return 0 if not result['errors'] else 1


if __name__ == '__main__':
    sys.exit(execute())
