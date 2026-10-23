"""Prepare only the preregistered HCT116 late-state intersection on explicit run."""
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import time
import warnings
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_late_information'
OLD = ROOT / 'log/20261022/ptpc_update_opportunity'
SOURCE = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
EXPECTED = {
    SOURCE / 'archive.body': 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133',
    SOURCE / 'S8_IDENTITY_ROWS.json': 'cd669b35af37286171aa791c33a574ce39c8012a8d13ffc700e96fcaf955e537',
    OLD / 'BASELINE_PREPARED.npz': '7226306e1f7d978baf0b7587fe481b65e40cbf2d5047cbf5cbd8e5631247f379',
    OLD / 'BASELINE_PREPARATION.json': '06ee08615c0b00971d65b208063d0e8f66e3a126de264ecdb1323f0f8baf5f37',
}
WORKBOOK_SHA = '540ec451edeca2bbbd08e53254cb9c09ba67b6f98727ff9c31e373a192290fdc'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def value(cell, shared):
    if cell is None:
        return ''
    assert cell.find(TAG + 'f') is None, 'No formula-derived observations'
    assert cell.attrib.get('t') not in ('e', 'b'), 'Error/boolean observation'
    node = cell.find(TAG + 'v')
    if cell.attrib.get('t') == 's':
        return ''.join(t.text or '' for t in shared[int(node.text)].iter(TAG + 't'))
    if cell.attrib.get('t') == 'inlineStr':
        return ''.join(t.text or '' for t in cell.iter(TAG + 't'))
    return node.text if node is not None else ''


def column(address):
    number = 0
    for letter in re.match('[A-Z]+', address)[0]:
        number = number * 26 + ord(letter) - 64
    return number - 1


def select_rows(identities, old_tasks, expected_count):
    """Resolve only identities before any workbook protein cell is decoded."""
    eligible = {task['pert_id'] for task in old_tasks}
    assert len(eligible) == len(old_tasks), 'Duplicate old condition identity'
    selected = {i for i, row in enumerate(identities)
                if row['Cell_line'] == 'HCT116' and row['Pert_time_(hrs)'] == '24'
                and row['Pert_ID'] in eligible}
    selected_ids = {identities[i]['Sample_ID'] for i in selected}
    contexts = defaultdict(set)
    for row in identities:
        if row['Sample_ID'] in selected_ids:
            contexts[row['Sample_ID']].add((row['Cell_line'], row['Pert_ID'], row['Pert_time_(hrs)']))
    assert all(len(context) == 1 for context in contexts.values()), 'Selected Sample_ID spans condition/time/background'
    available = {identities[i]['Pert_ID'] for i in selected}
    matched = np.array([i for i, task in enumerate(old_tasks) if task['pert_id'] in available], dtype=int)
    assert len(matched) == expected_count, 'Unexpected paired condition count'
    return selected, matched


def decode_matrix(stream, shared, identities, selected, n_proteins=5171):
    """Read row IDs globally; resolve abundance cells only after row selection."""
    rows_by_id = defaultdict(list)
    ids_by_condition = defaultdict(set)
    observed = missing = selected_rows = 0
    position = -1
    header_seen = False
    for _, row in ET.iterparse(stream, events=('end',)):
        if row.tag != TAG + 'row':
            continue
        if row.attrib['r'] == '1':
            assert not header_seen
            header_seen = True
            assert len(row) == n_proteins + 1
            assert column(row[0].attrib['r']) == 0 and value(row[0], shared) == 'Sample_ID'
            assert [column(cell.attrib['r']) for cell in row] == list(range(n_proteins + 1))
            row.clear()
            continue
        assert header_seen
        position += 1
        assert position < len(identities) and int(row.attrib['r']) == position + 2
        meta = identities[position]
        id_cells = [cell for cell in row if column(cell.attrib['r']) == 0]
        assert len(id_cells) == 1 and value(id_cells[0], shared) == meta['Sample_ID'], 'Matrix/metadata ID mismatch'
        if position not in selected:
            row.clear()
            continue
        assert meta['Cell_line'] == 'HCT116' and meta['Pert_time_(hrs)'] == '24'
        vector = np.full(n_proteins, np.nan)
        seen = set()
        for cell in row:
            index = column(cell.attrib['r'])
            assert index not in seen and 0 <= index <= n_proteins
            seen.add(index)
            if index == 0:
                continue
            text = value(cell, shared)
            if text.strip().casefold() not in ('', 'na', 'n/a', 'nan'):
                number = float(text)
                assert np.isfinite(number) and number >= 0, 'Unqualified intensity scale'
                vector[index - 1] = np.log1p(number)
        observed += int(np.isfinite(vector).sum())
        missing += int(np.isnan(vector).sum())
        selected_rows += 1
        rows_by_id[meta['Sample_ID']].append(vector)
        ids_by_condition[meta['Pert_ID']].add(meta['Sample_ID'])
        row.clear()
    assert header_seen and position + 1 == len(identities)
    assert selected_rows == len(selected)
    return rows_by_id, ids_by_condition, {'observed_abundance_cells': observed,
                                        'missing_abundance_cells': missing,
                                        'selected_matrix_rows': selected_rows,
                                        'all_matrix_row_ids_verified': position + 1}


def aggregate(rows_by_id, ids_by_condition, tasks):
    # Do not record thousands of all-missing warnings in memory; preserve NaNs.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='All-NaN slice encountered', category=RuntimeWarning)
        per_sample = {sample: np.nanmedian(np.stack(rows), axis=0) for sample, rows in rows_by_id.items()}
        return np.stack([np.nanmedian(np.stack([per_sample[s] for s in sorted(ids_by_condition[t])]), axis=0)
                         for t in tasks])


def main():
    started = time.perf_counter()
    target = OUT / 'LATE_PREPARED.npz'
    report = OUT / 'PREPARATION.json'
    assert not target.exists() and not report.exists(), 'Refuse to overwrite prepared artifacts'
    access = json.loads((OUT / 'ACCESS_FREEZE.json').read_text(encoding='utf-8-sig'))
    assert access['stage'] == 'ACCESS'
    for name, expected in access['bindings'].items():
        assert sha256(ROOT / name) == expected, 'Access freeze mismatch: ' + name
    inputs = {}
    for path, expected in EXPECTED.items():
        actual = sha256(path)
        assert actual == expected, 'Input hash mismatch: ' + str(path)
        inputs[str(path.relative_to(ROOT)).replace('\\', '/')] = actual
    old_metadata = json.loads((OLD / 'BASELINE_PREPARATION.json').read_text(encoding='utf-8-sig'))
    assert old_metadata['prepared_sha256'] == EXPECTED[OLD / 'BASELINE_PREPARED.npz']
    assert len(old_metadata['tasks']) == 601
    identities = json.loads((SOURCE / 'S8_IDENTITY_ROWS.json').read_text(encoding='utf-8-sig'))
    selected, matched = select_rows(identities, old_metadata['tasks'], expected_count=600)
    details = [dict(old_metadata['tasks'][i]) for i in matched]
    tasks = [detail['pert_id'] for detail in details]
    with zipfile.ZipFile(SOURCE / 'archive.body') as outer:
        body = outer.read('TableS8_PTPC_info_0703.xlsx')
    assert hashlib.sha256(body).hexdigest() == WORKBOOK_SHA
    inputs['archive_member:TableS8_PTPC_info_0703.xlsx'] = WORKBOOK_SHA
    with zipfile.ZipFile(BytesIO(body)) as book:
        shared = ET.fromstring(book.read('xl/sharedStrings.xml')).findall(TAG + 'si') if 'xl/sharedStrings.xml' in book.namelist() else []
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        parts = {}
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).find(TAG + 'sheets'):
            part = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            parts[sheet.attrib['name']] = part.lstrip('/') if part.startswith('/') else 'xl/' + part
        with book.open(parts['C_protein_Matrix']) as stream:
            rows_by_id, ids_by_condition, counts = decode_matrix(stream, shared, identities, selected)
    proteins24 = aggregate(rows_by_id, ids_by_condition, tasks).astype(np.float32)
    for detail in details:
        detail['twenty_four_hour_sample_ids'] = sorted(ids_by_condition[detail['pert_id']])
    with np.load(OLD / 'BASELINE_PREPARED.npz', allow_pickle=False) as old:
        assert old['proteins'].shape == (601, 5171) and old['chemistry'].shape == (601, 2049)
        assert old['labels'].shape == (601,)
        assert np.array_equal(old['labels'], np.array([t['label'] for t in old_metadata['tasks']]))
        proteins6 = old['proteins'][matched]
        chemistry = old['chemistry'][matched]
        labels = old['labels'][matched]
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, early=proteins6, late=proteins24, chemistry=chemistry,
                        labels=labels, tasks=np.array(tasks), matched_indices=matched,
                        chemical_groups=np.array([detail['chemical_group'] for detail in details]))
    metadata = {'scope': 'Only metadata-selected HCT11624h paired old tasks; all other abundance cells unresolved',
                'tasks': details, 'matched_old_indices': matched.tolist(), 'condition_count': len(tasks),
                'protein_shape': list(proteins24.shape), 'inputs_sha256': inputs,
                'unique_sample_ids': len(rows_by_id), **counts,
                'aggregate_observed_cells': int(np.isfinite(proteins24).sum()),
                'aggregate_missing_cells': int(np.isnan(proteins24).sum()),
                'median_policy': 'log1p finite nonnegative observations, including observed zero; missing stays NaN; '
                                 'nanmedian technical rows per Sample_ID then nanmedian Sample_IDs per condition; '
                                 'All-NaN slice RuntimeWarnings suppressed without recording warning objects',
                'wall_seconds': time.perf_counter() - started, 'prepared_sha256': sha256(target)}
    report.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in metadata.items() if k not in ('tasks', 'matched_old_indices')}))


if __name__ == '__main__':
    main()
