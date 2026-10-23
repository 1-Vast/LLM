"""Independent selective-XML audit; never import the preparation/evaluation code."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import posixpath
import re
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/next_mechanism/source/cdk_review'
RUN = ROOT / 'log/20261022/cdk_middle_feedback'
DEST = RUN / 'review'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
EXPECTED_SOURCE = '36903d770ff3bd3bc5fd62c6ee19d8106871c9735e8591c0e722da05cf146608'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def payload(cell, shared):
    if cell is None:
        return None
    kind = cell.get('t', 'n')
    if kind in ('e', 'b'):
        raise ValueError('error_or_boolean_cell')
    value = cell.find(TAG + 'v')
    raw = value.text if value is not None else None
    if kind == 's' and raw is not None:
        return shared[int(raw)]
    if kind == 'inlineStr':
        return ''.join(node.text or '' for node in cell.iter(TAG + 't'))
    return raw


def count_value(cell, shared):
    if cell is not None and cell.find(TAG + 'f') is not None:
        value = cell.find(TAG + 'v')
        if value is None or not (value.text or '').strip():
            raise ValueError('formula_without_cached_count')
    raw = payload(cell, shared)
    if raw is None:
        return None
    try:
        number = Decimal(raw)
    except (InvalidOperation, TypeError):
        raise ValueError('nonnumeric_count') from None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError('invalid_nonnegative_integer_count')
    return int(number)


def companion_nonempty(cell):
    """Only inspect XML structure; never decode a Fraction numerical value."""
    return cell is not None and (
        cell.get('t') in ('e', 'b') or cell.find(TAG + 'f') is not None
        or any((node.text or '').strip() for node in cell.iter()
               if node.tag in (TAG + 'v', TAG + 't')))


def self_check():
    assert count_value(None, []) is None
    assert count_value(ET.fromstring('<c xmlns="' + TAG[1:-1] + '"><v>0</v></c>'), []) == 0
    cached = ET.fromstring('<c xmlns="' + TAG[1:-1] + '"><f>1+1</f><v>2</v></c>')
    assert count_value(cached, []) == 2
    uncached = ET.fromstring('<c xmlns="' + TAG[1:-1] + '"><f>1+1</f><v/></c>')
    try:
        count_value(uncached, [])
    except ValueError as error:
        assert str(error) == 'formula_without_cached_count'
    else:
        raise AssertionError('Uncached formula was accepted as zero')
    assert companion_nonempty(uncached)


def main():
    started = time.perf_counter()
    self_check()
    DEST.mkdir(parents=True, exist_ok=True)
    output = DEST / 'PREPARED_AUDIT.json'
    assert not output.exists(), 'Preserve the previous audit rather than overwrite it'
    source = SOURCE / 'table_s3.body'
    source_hash = sha(source)
    assert source_hash == EXPECTED_SOURCE
    specs = [b for b in json.loads((SOURCE / 'SAMPLE_HEADER_CONTRACT.json').read_text())['bindings']
             if b['treatment_label'] != 'Veh']
    assert len(specs) == 36
    raw = {b['sample_label']: {} for b in specs}
    stats = {b['sample_label']: Counter() for b in specs}
    masks = {b['sample_label']: bytearray() for b in specs}
    issues = []
    sheet_rows = {}

    with zipfile.ZipFile(source) as archive:
        shared = []
        with archive.open('xl/sharedStrings.xml') as stream:
            for _, element in ET.iterparse(stream, events=('end',)):
                if element.tag == TAG + 'si':
                    shared.append(''.join(t.text or '' for t in element.iter(TAG + 't')))
                    element.clear()
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in relationships}
        members = {}
        for sheet in book.find(TAG + 'sheets'):
            target = targets[sheet.get(REL)]
            members[sheet.get('name')] = (target.lstrip('/') if target.startswith('/')
                                          else posixpath.normpath('xl/' + target))

        for name in dict.fromkeys(b['sheet'] for b in specs):
            local = [b for b in specs if b['sheet'] == name]
            count_cols = {re.sub(r'\d+$', '', b['count_column']): b for b in local}
            fraction_cols = {re.sub(r'\d+$', '', b['count_column']):
                             re.sub(r'\d+$', '', b['fraction_column']) for b in local}
            permitted_structure = {'A', *count_cols, *fraction_cols.values()}
            seen_barcodes = set()
            row_number = 0
            row_cells = {}
            with archive.open(members[name]) as stream:
                for event, element in ET.iterparse(stream, events=('start', 'end')):
                    if event == 'start' and element.tag == TAG + 'row':
                        row_number = int(element.get('r'))
                        row_cells = {}
                    elif event == 'end' and element.tag == TAG + 'c':
                        match = re.fullmatch(r'([A-Z]+)(\d+)', element.get('r', ''))
                        assert match and int(match.group(2)) == row_number
                        if match.group(1) in permitted_structure:
                            row_cells[match.group(1)] = element
                        else:
                            element.clear()
                    elif event == 'end' and element.tag == TAG + 'row':
                        if row_number == 1:
                            for column, binding in count_cols.items():
                                assert payload(row_cells[column], shared) == binding['sample_label'] + '_Count'
                        else:
                            barcode = payload(row_cells.get('A'), shared)
                            assert isinstance(barcode, str) and barcode and barcode not in seen_barcodes
                            seen_barcodes.add(barcode)
                            for column, binding in count_cols.items():
                                label = binding['sample_label']
                                cell = row_cells.get(column)
                                sample_stats = stats[label]
                                sample_stats['rows'] += 1
                                if cell is not None:
                                    sample_stats['present_cells'] += 1
                                    sample_stats['cell_type_' + cell.get('t', 'n')] += 1
                                    if cell.find(TAG + 'f') is not None:
                                        sample_stats['formula_cells'] += 1
                                try:
                                    count = count_value(cell, shared)
                                except ValueError as error:
                                    issues.append({'sample': label, 'cell': column + str(row_number),
                                                   'error': str(error)})
                                    count = None
                                missing = count is None
                                masks[label].append(missing)
                                if missing:
                                    sample_stats['missing_count_cells'] += 1
                                    sample_stats['absent_cells' if cell is None else 'present_empty_cells'] += 1
                                    if companion_nonempty(row_cells.get(fraction_cols[column])):
                                        sample_stats['nonempty_fraction_at_missing_count'] += 1
                                        issues.append({'sample': label, 'cell': column + str(row_number),
                                                       'error': 'missing_count_with_fraction_payload_or_formula'})
                                else:
                                    sample_stats['count_sum'] += count
                                    sample_stats['stored_zero' if count == 0 else 'stored_positive'] += 1
                                    if count:
                                        raw[label][barcode] = count
                        element.clear()
            sheet_rows[name] = len(seen_barcodes)

    assert not issues, 'Invalid cells detected; no numerical comparison is valid: ' + repr(issues[:5])
    universe = sorted({barcode for b in specs if b['stage_label'] == 'Early'
                       for barcode in raw[b['sample_label']]})
    index = {barcode: position for position, barcode in enumerate(universe)}
    tasks = sorted({(b['selection_family'], b['genotype_label'], b['evolutionary_replicate']) for b in specs})
    positions = {task: position for position, task in enumerate(tasks)}
    stage_index = {'Early': 0, 'Middle': 1, 'Late_Resistant': 2}
    reconstructed = np.zeros((len(tasks), 3, len(universe) + 1))
    original_depth = np.zeros((len(tasks), 3))
    seen_samples = set()
    for binding in specs:
        task = (binding['selection_family'], binding['genotype_label'], binding['evolutionary_replicate'])
        i, stage = positions[task], stage_index[binding['stage_label']]
        assert (i, stage) not in seen_samples
        seen_samples.add((i, stage))
        label = binding['sample_label']
        depth = sum(raw[label].values())
        assert depth > 0 and depth == stats[label]['count_sum']
        original_depth[i, stage] = depth
        for barcode, count in raw[label].items():
            reconstructed[i, stage, index.get(barcode, len(universe))] += count
        reconstructed[i, stage] /= depth
    assert len(seen_samples) == 36

    metadata = json.loads((RUN / 'PREPARATION.json').read_text())
    prepared_path = RUN / 'prepared.npz'
    prepared_hash = sha(prepared_path)
    with np.load(prepared_path, allow_pickle=False) as prepared:
        actual = prepared['compositions']
        actual_depth = prepared['depth']
    checks = {
        'prepared_hash_matches_receipt': prepared_hash == metadata['prepared_sha256'],
        'source_hash_matches_receipt': source_hash == metadata['source_sha256'],
        'task_order_matches': [list(t) for t in tasks] == metadata['tasks'],
        'shape_matches': actual.shape == reconstructed.shape and list(actual.shape) == metadata['shape'],
        'all_compositions_finite_nonnegative': bool(np.isfinite(actual).all() and (actual >= 0).all()),
        'normalization_matches': bool(np.allclose(actual.sum(axis=-1), 1, atol=1e-14, rtol=0)),
        'original_count_sums_match_depth': bool(np.array_equal(actual_depth, original_depth)),
        'all_composition_coordinates_match': bool(np.allclose(actual, reconstructed, atol=1e-15, rtol=0)),
        'other_mass_matches': bool(np.array_equal(actual[..., -1], reconstructed[..., -1])),
        'all_early_other_zero': bool((reconstructed[:, 0, -1] == 0).all()),
        'metadata_other_mass_matches': bool(np.array_equal(np.array(metadata['other_mass']), reconstructed[..., -1])),
        'metadata_depth_matches': bool(np.array_equal(np.array(metadata['depth']), original_depth)),
        'metadata_omissions_match': all(metadata['omitted_count_cells'][b['sheet'] + '::' + b['sample_label']]
                                       == stats[b['sample_label']]['missing_count_cells'] for b in specs),
    }
    mask_artifact = DEST / 'PREPARED_MISSING_MASKS.npz'
    np.savez_compressed(mask_artifact, **{f'sample_{i}': np.packbits(np.frombuffer(masks[b['sample_label']], dtype=np.uint8))
                                       for i, b in enumerate(specs)})
    report = {
        'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
        'source_sha256': source_hash, 'prepared_sha256': prepared_hash,
        'audit_code_sha256': sha(Path(__file__)), 'shape': list(actual.shape),
        'cohort_early_universe_size': len(universe),
        'universe_identity_sha256': hashlib.sha256('\n'.join(universe).encode()).hexdigest(),
        'raw_sheet_barcode_rows': sheet_rows, 'original_count_sums': original_depth.tolist(),
        'other_mass': reconstructed[..., -1].tolist(),
        'max_absolute_composition_error': float(np.max(np.abs(actual - reconstructed))),
        'max_normalization_error': float(np.max(np.abs(actual.sum(axis=-1) - 1))),
        'sample_cell_categories': {b['sheet'] + '::' + b['sample_label']: dict(stats[b['sample_label']]) for b in specs},
        'mask_artifact': str(mask_artifact.relative_to(ROOT)), 'mask_artifact_sha256': sha(mask_artifact),
        'mask_order': [{'array': f'sample_{i}', 'sample': b['sheet'] + '::' + b['sample_label'],
                        'unpacked_length': len(masks[b['sample_label']]), 'row_order': 'worksheet barcode rows after header'}
                       for i, b in enumerate(specs)],
        'issues': issues,
        'reader_guard_assessment': 'Prepared reader lacks explicit uncached-formula rejection; this audit independently rejects it. Actual formula counts are reported, so a zero count establishes no present-data effect, not a general reader guarantee.',
        'scope': 'Conditional author-style sparse-zero composition; not biological absence or full exporter authentication',
        'result_json_opened': False, 'root_modules_imported': [],
        'fraction_values_decoded': False, 'vehicle_cells_decoded': False, 'S4_opened': False,
        'wall_seconds': time.perf_counter() - started,
    }
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'checks', 'shape', 'max_absolute_composition_error', 'wall_seconds')}))
    if not all(checks.values()):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
