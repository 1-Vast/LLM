"""Independent source/saved-output metric audit; no fitting or pilot imports."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'log/20261023/vuscope_prefix_diagnostic'
RUN = BASE/'pilot'
OUT = BASE/'critic'
METHODS = ['vuscope6','moving_midpoint7','independent_logistic','direct_selected','persistence']


def readj(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    freeze = readj(BASE/'FREEZE.json')
    checked = {name: sha(ROOT/name) == expected for name, expected in freeze['files'].items()}
    assert all(checked.values()), checked
    result_seal = readj(BASE/'RESULT_SEAL.json')
    result_checked = {name:sha(ROOT/name)==expected for name,expected in result_seal['files'].items()}
    assert all(result_checked.values()), result_checked
    archive_path = ROOT/'log/20261023/functional_transition_law/root_sources/release.zip.body'
    assert sha(archive_path) == freeze['archive_sha256']
    execution = readj(BASE/'EXECUTION.json')
    assert execution['returncode'] == 0
    prediction_file = RUN/'PREDICTIONS_BEFORE_OUTCOMES.json'
    assert sha(prediction_file) == readj(RUN/'PREDICTION_SEAL.json')['sha256']
    schedule, prediction = readj(BASE/'SCHEDULE.json'), readj(prediction_file)
    raw_saved, metrics_saved = readj(RUN/'OUTCOMES.json'), readj(RUN/'METRICS.json')
    summary_saved, gate_saved = readj(RUN/'SUMMARY.json'), readj(RUN/'GATE.json')
    eligibility = readj(RUN/'PREFIX_ELIGIBILITY.json')
    prefix_hours, future_hours = list(range(6,73,3)), list(range(75,121,3))
    requested = set(prefix_hours+future_hours)
    rebuilt, eligibility_rebuilt, sources = [], [], {}
    with ZipFile(archive_path) as archive:
        for member, info in schedule['files'].items():
            # Independently parse only elapsed/baseline/legal prefix/late requested responses.
            lines = archive.read(member).decode('utf-8-sig').splitlines()
            header_i = next(i for i,s in enumerate(lines) if 'Elapsed' in s.split('\t'))
            header = lines[header_i].split('\t')
            elapsed_i = header.index('Elapsed')
            wells = header[elapsed_i+1:]
            rows = {}
            for line in lines[header_i+1:]:
                fields = line.split('\t')
                if len(fields) < 2:
                    continue
                hour = float(fields[elapsed_i])
                if hour in requested:
                    assert hour not in rows and len(fields[elapsed_i+1:]) == len(wells)
                    rows[hour] = dict(zip(wells, map(float, fields[elapsed_i+1:])))
            assert set(rows) == requested
            cell = Path(member).name.split('_')[0]
            for label, entries in sorted(info['groups'].items()):
                entries = sorted(entries, key=lambda e:e['dose'])
                js = [e['well'] for e in entries]
                raw_prefix = np.array([[rows[t][w] for w in js] for t in prefix_hours])
                key = cell+'__'+label
                eligible = bool(np.isfinite(raw_prefix).all() and (raw_prefix>=0).all() and (raw_prefix[0]>0).all())
                if not eligible:
                    assert key not in prediction
                    continue
                eligibility_rebuilt.append(key)
                saved = prediction[key]
                assert saved['member'] == member and saved['wells'] == js
                assert saved['doses'] == [e['dose'] for e in entries]
                np.testing.assert_array_equal(raw_prefix[0], saved['baseline'])
                raw = np.array([[rows[t][w] for w in js] for t in future_hours])
                np.testing.assert_array_equal(raw, raw_saved[key])
                assert np.isfinite(raw).all() and (raw>=0).all()
                truth = raw/raw_prefix[0]
                for method in METHODS:
                    p = np.array(saved[method])
                    assert p.shape == (16,6) and np.isfinite(p).all() and (p>=0).all()
                    # Explicit scalar reductions, distinct from root's vectorized means.
                    squared = [[float((p[t,d]-truth[t,d])**2) for d in range(6)] for t in range(16)]
                    record = dict(key=key, cell=cell, label=label, method=method,
                        mse120=sum(squared[-1])/6,
                        mse_late=sum(sum(row) for row in squared)/96,
                        mae120=sum(abs(float(p[-1,d]-truth[-1,d])) for d in range(6))/6,
                        raw_mse120=sum(float((p[-1,d]*raw_prefix[0,d]-raw[-1,d])**2) for d in range(6))/6)
                    rebuilt.append(record)
            sources[member] = dict(requested_rows=len(rows), header_wells=len(wells))
    assert set(eligibility_rebuilt) == set(eligibility['eligible']) == set(prediction)
    assert {x['key'] for x in eligibility['exclusions']} == {
        Path(member).name.split('_')[0]+'__'+label for member,info in schedule['files'].items()
        for label in info['groups']} - set(prediction)
    index = {(r['key'],r['method']):r for r in metrics_saved}
    assert len(index) == len(rebuilt) == len(prediction)*5
    max_abs = 0.0
    for r in rebuilt:
        old = index[(r['key'],r['method'])]
        for field in ('mse120','mse_late','mae120','raw_mse120'):
            max_abs = max(max_abs, abs(r[field]-old[field]))
            np.testing.assert_allclose(r[field],old[field],rtol=1e-11,atol=1e-10)
    cells = sorted({r['cell'] for r in rebuilt})
    assert len(cells) == 4
    summary = {}
    for method in METHODS:
        rows = [r for r in rebuilt if r['method']==method]
        summary[method] = {field:sum(r[field] for r in rows)/len(rows) for field in ('mse120','mse_late','mae120','raw_mse120')}
        summary[method]['cells'] = {c:{f:sum(r[f] for r in rows if r['cell']==c)/sum(r['cell']==c for r in rows)
                for f in ('mse120','mse_late')} for c in cells}
        for field in ('mse120','mse_late','mae120','raw_mse120'):
            np.testing.assert_allclose(summary[method][field],summary_saved[method][field],rtol=1e-11,atol=1e-10)
        for cell in cells:
            for field in ('mse120','mse_late'):
                np.testing.assert_allclose(summary[method]['cells'][cell][field],summary_saved[method]['cells'][cell][field],rtol=1e-11,atol=1e-10)
    independent_index = {(r['key'],r['method']):r for r in rebuilt}
    primary_wins = sum(independent_index[(k,'moving_midpoint7')]['mse120'] < independent_index[(k,'vuscope6')]['mse120'] for k in prediction)
    cell_wins = [c for c in cells if all(summary['moving_midpoint7']['cells'][c][f] < summary['vuscope6']['cells'][c][f]
                                       for f in ('mse120','mse_late'))]
    ordinary = all(summary['moving_midpoint7'][f] < summary[m][f] for m in ('independent_logistic','direct_selected') for f in ('mse120','mse_late'))
    passed = len(cell_wins)>=3 and primary_wins>len(prediction)/2 and ordinary
    gate = dict(cell_wins_both=cell_wins,curve_wins_primary=primary_wins,curves=len(prediction),beats_both_ordinary_on_both=ordinary,
                decision='RETAIN_FOR_SEPARATE_REVIEW_ONLY' if passed else 'STOP_THIS_MOVING_MIDPOINT_CONFIGURATION')
    for k,v in gate.items():
        assert gate_saved[k] == v, (k,v,gate_saved[k])
    report = dict(status='PASS_INDEPENDENT_ARCHIVE_NORMALIZATION_METRIC_GATE_AUDIT',
        freeze_files_unchanged=checked, result_seal_files_unchanged=result_checked,
        archive_sha256=sha(archive_path), prediction_seal_verified=True,
        source_reconstruction=sources, groups=len(prediction), metric_records=len(rebuilt),
        max_absolute_metric_difference=max_abs, summary=summary, gate=gate,
        scope='No refit/imported pilot/model search; count normalization/eligibility/metrics/gate independently rebuilt. Root aggregates were disclosed before audit, so no blind-result claim.')
    (OUT/'RESULT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','groups','metric_records','max_absolute_metric_difference','gate')},indent=2))


if __name__ == '__main__':
    main()
