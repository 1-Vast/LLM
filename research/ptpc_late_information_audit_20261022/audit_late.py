"""Independent lxml audit of authorized HCT116 paired 24h preparation only."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import time
import warnings
import zipfile

from lxml import etree
import lxml
import numpy as np

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261022/ptpc_late_information'
OLD = ROOT/'log/20261022/ptpc_update_opportunity'
SOURCE = ROOT/'log/20261022/generative_repair_renewal/source/archive_followup'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REPORT = OUT/'source/LATE_PREPARED_AUDIT.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()


def main():
    started = time.perf_counter()
    access = json.loads((OUT/'ACCESS_FREEZE.json').read_text(encoding='utf-8-sig'))
    assert access['stage'] == 'ACCESS'
    for path, expected in access['bindings'].items():
        assert sha(ROOT/path) == expected, f'ACCESS binding changed: {path}'
    meta = json.loads((OUT/'PREPARATION.json').read_text(encoding='utf-8-sig'))
    assert sha(OUT/'LATE_PREPARED.npz') == meta['prepared_sha256']
    previous = json.loads((OLD/'BASELINE_PREPARATION.json').read_text(encoding='utf-8-sig'))
    identities = json.loads((SOURCE/'S8_IDENTITY_ROWS.json').read_text(encoding='utf-8-sig'))
    gate = json.loads((OLD/'source/HCT116_CONDITION_GROUPS.json').read_text(encoding='utf-8-sig'))
    labels = {g['Pert_ID']: int(next(iter(g['labels']))) for g in gate
              if g['Cell_line'] == 'HCT116' and not g['control'] and g['strict_complete_candidate'] and '6' in g['times']}
    old_tasks = previous['tasks']
    assert len(old_tasks) == len(labels) == 601 and sum(labels.values()) == 34
    assert len({t['chemical_group'] for t in old_tasks}) == 597
    assert all(t['label'] == labels[t['pert_id']] for t in old_tasks)
    selected_meta = [r for r in identities if r['Cell_line'] == 'HCT116' and r['Pert_time_(hrs)'] == '24' and r['Pert_ID'] in labels]
    available = {r['Pert_ID'] for r in selected_meta}
    matched = [i for i, t in enumerate(old_tasks) if t['pert_id'] in available]
    tasks = [old_tasks[i]['pert_id'] for i in matched]
    assert len(tasks) == 600 and len(set(tasks)) == 600
    assert set(tasks) == {g['Pert_ID'] for g in gate if g['Cell_line'] == 'HCT116' and g['strict_complete_candidate'] and set(g['times']) == {'6', '24'}}
    assert meta['matched_old_indices'] == matched and meta['condition_count'] == 600
    assert len(meta['tasks']) == 600
    for i, detail in zip(matched, meta['tasks']):
        assert all(detail[key] == val for key, val in old_tasks[i].items())
    selected_ids = {r['Sample_ID'] for r in selected_meta}
    global_contexts = defaultdict(set)
    for row in identities:
        if row['Sample_ID'] in selected_ids:
            global_contexts[row['Sample_ID']].add((row['Cell_line'], row['Pert_ID'], row['Pert_time_(hrs)']))
    assert all(len(v) == 1 for v in global_contexts.values())
    with np.load(OLD/'BASELINE_PREPARED.npz', allow_pickle=False) as old:
        old_data = {key: old[key].copy() for key in ('proteins', 'chemistry', 'labels')}
    with np.load(OUT/'LATE_PREPARED.npz', allow_pickle=False) as late:
        arrays = {key: late[key].copy() for key in ('early', 'late', 'chemistry', 'labels', 'tasks', 'matched_indices', 'chemical_groups')}
    assert np.array_equal(arrays['matched_indices'], matched)
    assert arrays['tasks'].tolist() == tasks
    assert np.array_equal(arrays['early'], old_data['proteins'][matched], equal_nan=True)
    assert np.array_equal(arrays['chemistry'], old_data['chemistry'][matched])
    assert np.array_equal(arrays['labels'], old_data['labels'][matched])
    assert np.array_equal(arrays['labels'], [labels[t] for t in tasks])
    expected_groups = [old_tasks[i]['chemical_group'] for i in matched]
    assert arrays['chemical_groups'].tolist() == expected_groups
    assert set(expected_groups) <= {t['chemical_group'] for t in old_tasks}
    archive_path = SOURCE/'archive.body'
    assert sha(archive_path) == 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133'
    with zipfile.ZipFile(archive_path) as archive:
        body = archive.read('TableS8_PTPC_info_0703.xlsx')
    member_sha = hashlib.sha256(body).hexdigest()
    assert member_sha == '540ec451edeca2bbbd08e53254cb9c09ba67b6f98727ff9c31e373a192290fdc'
    rows_by_context = defaultdict(list)
    observed = missing = selected_rows = total_rows = 0
    with zipfile.ZipFile(BytesIO(body)) as book:
        strings = etree.fromstring(book.read('xl/sharedStrings.xml')).findall(TAG+'si')
        def text(cell):
            if cell is None:
                return ''
            assert cell.find(TAG+'f') is None
            kind = cell.get('t', 'n')
            assert kind not in ('b', 'e')
            if kind == 's':
                return ''.join(n.text or '' for n in strings[int(cell.find(TAG+'v').text)].iter(TAG+'t'))
            if kind == 'inlineStr':
                return ''.join(n.text or '' for n in cell.iter(TAG+'t'))
            node = cell.find(TAG+'v')
            return (node.text or '') if node is not None else ''
        rels = {r.get('Id'): r.get('Target') for r in etree.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        target = None
        for sheet in etree.fromstring(book.read('xl/workbook.xml')).findall('.//'+TAG+'sheet'):
            if sheet.get('name') == 'C_protein_Matrix':
                target = rels[sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
        assert target
        target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        def coordinate(cell):
            letters = re.match('[A-Z]+', cell.get('r'))[0]
            return sum((ord(c)-64)*26**(len(letters)-j-1) for j, c in enumerate(letters))-1
        with book.open(target) as stream:
            for _, row in etree.iterparse(stream, events=('end',), tag=TAG+'row'):
                number = int(row.get('r'))
                cells = {coordinate(cell): cell for cell in row if cell.tag == TAG+'c'}
                if number == 1:
                    assert list(cells) == list(range(5172)) and text(cells[0]) == 'Sample_ID'
                else:
                    total_rows += 1
                    assert number == total_rows+1 and total_rows <= len(identities)
                    identity = identities[total_rows-1]
                    sample = text(cells.get(0))
                    assert sample == identity['Sample_ID'], 'Complete row-ID correspondence failed'
                    if identity['Cell_line'] == 'HCT116' and identity['Pert_time_(hrs)'] == '24' and identity['Pert_ID'] in available:
                        vector = np.full(5171, np.nan)
                        for index in range(1, 5172):
                            raw = text(cells.get(index)).strip()
                            if raw.casefold() in ('', 'na', 'n/a', 'nan'):
                                missing += 1
                            else:
                                value = float(raw)
                                assert math.isfinite(value) and value >= 0
                                vector[index-1] = np.log1p(value)
                                observed += 1
                        key = (identity['Cell_line'], identity['Pert_ID'], identity['Pert_time_(hrs)'], sample)
                        rows_by_context[key].append(vector)
                        selected_rows += 1
                row.clear()
                while row.getprevious() is not None:
                    del row.getparent()[0]
    assert total_rows == len(identities) == 2217
    assert selected_rows == len(selected_meta) == meta['selected_matrix_rows']
    assert len(rows_by_context) == len(selected_ids) == meta['unique_sample_ids']
    assert observed == meta['observed_abundance_cells'] and missing == meta['missing_abundance_cells']
    assert observed+missing == selected_rows*5171
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='All-NaN slice encountered', category=RuntimeWarning)
        samples = {key: np.nanmedian(np.stack(values), axis=0) for key, values in rows_by_context.items()}
        rebuilt = []
        for task, detail in zip(tasks, meta['tasks']):
            keys = sorted(k for k in samples if k[1] == task)
            assert keys
            assert [k[3] for k in keys] == detail['twenty_four_hour_sample_ids']
            rebuilt.append(np.nanmedian(np.stack([samples[k] for k in keys]), axis=0))
        rebuilt = np.stack(rebuilt).astype(np.float32)
    assert rebuilt.shape == arrays['late'].shape == (600, 5171)
    same = (rebuilt == arrays['late']) | (np.isnan(rebuilt) & np.isnan(arrays['late']))
    mismatches = int((~same).sum())
    assert mismatches == 0
    assert np.array_equal(np.isnan(rebuilt), np.isnan(arrays['late']))
    assert int(np.isfinite(rebuilt).sum()) == meta['aggregate_observed_cells']
    assert int(np.isnan(rebuilt).sum()) == meta['aggregate_missing_cells']
    def fold(key, salt, count):
        return int.from_bytes(hashlib.sha256((salt+'|'+key).encode('utf-8')).digest(), 'big') % count
    assignments = [(fold(key, 'PTPC_HCT116_DEV_V1', 5), fold(key, 'INNER', 3)) for key in expected_groups]
    groups_to_folds = defaultdict(set)
    for key, assignment in zip(expected_groups, assignments):
        groups_to_folds[key].add(assignment)
    assert all(len(v) == 1 for v in groups_to_folds.values())
    report = dict(status='PASS', created_utc=now(), parser='independent lxml', lxml_version=lxml.__version__,
        no_baseline_module_imported=True, access_bindings_match=True, access_freeze_sha256=sha(OUT/'ACCESS_FREEZE.json'),
        late_prepared_sha256=sha(OUT/'LATE_PREPARED.npz'), preparation_sha256=sha(OUT/'PREPARATION.json'),
        archive_sha256=sha(archive_path), member_sha256=member_sha,
        all_matrix_row_ids_verified=total_rows, selected_24h_rows=selected_rows, distinct_24h_sample_ids=len(rows_by_context),
        selected_context_collisions=0, paired_conditions=len(tasks), positive_condition_annotations=int(arrays['labels'].sum()),
        exact_metadata_intersection_and_order=True, old_matched_indices_exact=True,
        early_array_exact_common_subset=True, labels_exact_source_gate_and_old=True, chemistry_exact_old_subset=True,
        old_chemical_components=597, inherited_paired_chemical_components=len(set(expected_groups)), chemical_groups_exact_subset=True,
        cross_outer_or_inner_group_assignments=0, outer_fold_conditions=dict(Counter(a[0] for a in assignments)),
        observed_raw_24h_cells=observed, missing_raw_24h_cells=missing,
        transform='log1p per observed cell -> technical nanmedian -> sample nanmedian -> float32',
        rebuilt_shape=list(rebuilt.shape), coordinates_compared=int(rebuilt.size), mismatched_coordinates=mismatches,
        aggregate_observed_cells=int(np.isfinite(rebuilt).sum()), aggregate_missing_cells=int(np.isnan(rebuilt).sum()), missing_masks_exact=True,
        raw_Efficacy_cells_decoded=0, other_background_abundance_cells_decoded=0, six_hour_raw_abundance_cells_decoded=0,
        predictions_read=False, classifier_rerun=False, all_nan_warning_objects_collected=False,
        limitation='Preparation and inherited assignment audit only. No functional chronology, performance, new mechanism or RSI claim.',
        audit_script_sha256=sha(Path(__file__).resolve()), wall_seconds=time.perf_counter()-started)
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    seal_path = OUT/'source/LATE_PREPARED_AUDIT_SEAL.json'
    assert not seal_path.exists()
    seal_path.write_text(json.dumps(dict(created_utc=now(), files=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p))
        for p in (REPORT, Path(__file__).resolve())]), indent=2), encoding='utf-8')
    print(json.dumps(dict(**report, report_sha256=sha(REPORT), seal_sha256=sha(seal_path)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-preparation-ready', action='store_true')
    args = parser.parse_args()
    assert args.root_preparation_ready, 'Run only after root explicitly announces preparation completion'
    assert not REPORT.exists(), 'Refuse audit overwrite'
    try:
        main()
    except Exception as error:
        REPORT.write_text(json.dumps(dict(status='FAIL', created_utc=now(), error_type=type(error).__name__, error=str(error),
            audit_script_sha256=sha(Path(__file__).resolve())), indent=2), encoding='utf-8')
        raise
