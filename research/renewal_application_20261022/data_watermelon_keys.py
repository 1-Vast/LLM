"""Only key/missingness/format and frozen pooled support; no gate targets."""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/renewal_application'
SOURCE = BASE / 'root_sources/GSE150949_metaData_with_lineage_txt_gz.body'
OUT = BASE / 'data/WATERMELON_KEY_AUDIT.json'
MISSING = {'', 'NA', 'NaN', 'nan', 'None', 'null'}
SAMPLE_GROUP = {'1': 'day0', '2': 'day3_rep1', '3': 'day3_rep2',
                '4': 'day7_rep1', '5': 'day7_rep2',
                '6': 'day14_rep1', '7': 'day14_rep1', '8': 'day14_rep1',
                '9': 'day14_rep2', '10': 'day14_rep2', '11': 'day14_rep2'}


def excess(counter):
    return sum(value - 1 for value in counter.values())


def partition(token):
    value = int(hashlib.sha256(('watermelon-support-v1|' + token).encode()).hexdigest()[:8], 16) % 10
    return ('source' if value < 6 else 'development' if value < 8 else 'test')


def curves(groups, count_key):
    result = []
    for day in (0, 3, 7):
        names = ['day0'] if day == 0 else [f'day{day}_rep1', f'day{day}_rep2']
        names += ['day14_rep1', 'day14_rep2']
        pooled = set.intersection(*(set(groups[name]) for name in names))
        for threshold in (1, 2, 3, 5):
            tokens = [token for token in pooled if min(groups[name][token] for name in names) >= threshold]
            parts = Counter(partition(token) for token in tokens)
            result.append({'early_day': day, 'minimum_cells_each_group': threshold,
                           count_key: len(tokens),
                           'partitions': {name: parts[name] for name in ('source', 'development', 'test')}})
    return result


def main():
    assert not OUT.exists()
    protocol = OUT.parent / 'WATERMELON_KEY_AUDIT_PROTOCOL.md'
    frozen = {'protocol_sha256': hashlib.sha256(protocol.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    with (OUT.parent / 'WATERMELON_KEY_PRE_EXECUTION.json').open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, indent=2)
    raw, single = defaultdict(Counter), defaultdict(Counter)
    keys, nonmissing_keys, missing_keys, rows, cell_ids = Counter(), Counter(), Counter(), Counter(), Counter()
    selected_keys, selected_rows, selected_missing = Counter(), Counter(), Counter()
    joint_missing = Counter()
    formats = Counter()
    missing_by_sample = Counter()
    with gzip.open(SOURCE, 'rt', encoding='utf-8-sig', newline='') as stream:
        header = next(csv.reader(stream, delimiter='\t'))
        assert header == ['nGene', 'nUMI', 'orig.ident', 'percent.mito', 'sample_id',
                          'time_point', 'sample_name', 'sample_type', 'full_cell_barcode',
                          'lineage_barcode', 'clone_size']
        columns = ['__row_id__'] + header
        for record in csv.DictReader(stream, fieldnames=columns, delimiter='\t'):
            assert None not in record
            sample, cell, lineage, row_id = (record[name] for name in
                ('sample_id', 'full_cell_barcode', 'lineage_barcode', '__row_id__'))
            assert all(value is not None for value in (sample, cell, lineage, row_id))
            group = SAMPLE_GROUP[sample]
            missing_cell, missing_lineage = cell in MISSING, lineage in MISSING
            joint_missing[(missing_cell, missing_lineage)] += 1
            rows[row_id] += 1
            cell_ids[cell] += 1
            keys[(sample, cell)] += 1
            if missing_cell:
                missing_keys[(sample, cell)] += 1
                missing_by_sample[sample] += 1
            else:
                nonmissing_keys[(sample, cell)] += 1
            if not missing_lineage:
                raw[group][lineage] += 1
                formats[(len(lineage), ''.join(sorted(set(lineage))))] += 1
            if re.fullmatch('[ACGT]{30}', lineage):
                single[group][lineage] += 1
                selected_rows[row_id] += 1
                if missing_cell:
                    selected_missing[sample] += 1
                else:
                    selected_keys[(sample, cell)] += 1
    raw_curve = curves(raw, 'lineages')
    single_curve = curves(single, 'single_called_barcodes')
    raw_ref_path = BASE / 'root_sources/LINEAGE_SUPPORT_RESULT.json'
    single_ref_path = BASE / 'root_sources/SINGLE_BARCODE_SUPPORT_RESULT.json'
    raw_ref = json.loads(raw_ref_path.read_text(encoding='utf-8'))
    single_ref = json.loads(single_ref_path.read_text(encoding='utf-8'))
    assert raw_curve == raw_ref['support_curves']
    assert single_curve == single_ref['support_curves']
    assert excess(cell_ids) == raw_ref['duplicated_full_cell_identifiers']
    assert excess(keys) == single_ref['duplicate_sample_cell_keys']
    assert excess(rows) == single_ref['duplicate_row_identifiers']
    assert sum(selected_rows.values()) == single_ref['selected_rows']
    record = {'status': 'PASS_INDEPENDENT_KEY_AND_SUPPORT_DIAGNOSTIC', **frozen,
              'allowed_value_fields': ['sample_id', 'full_cell_barcode', '__row_id__', 'lineage_barcode'],
              'total_rows': sum(rows.values()),
              'all_row_identifiers': {'missing_rows': sum(count for key, count in rows.items() if key in MISSING),
                                      'unique': len(rows), 'duplicate_excess': excess(rows)},
              'joint_missingness': [{'full_cell_barcode_missing': key[0], 'lineage_barcode_missing': key[1],
                                     'rows': value} for key, value in sorted(joint_missing.items())],
              'all_sample_cell_keys_duplicate_excess': excess(keys),
              'missing_sample_cell_keys': {'rows': sum(missing_keys.values()), 'keys': len(missing_keys),
                                          'duplicate_excess': excess(missing_keys),
                                          'by_sample_id': dict(sorted(missing_by_sample.items()))},
              'nonmissing_sample_cell_keys': {'rows': sum(nonmissing_keys.values()), 'unique': len(nonmissing_keys),
                                             'duplicate_excess': excess(nonmissing_keys)},
              'selected_single30_subset': {'rows': sum(selected_rows.values()),
                                          'missing_full_cell_barcode_rows': sum(selected_missing.values()),
                                          'row_identifier_duplicate_excess': excess(selected_rows),
                                          'nonmissing_sample_cell_key_duplicate_excess': excess(selected_keys)},
              'all_duplicate_excess_exactly_missing_key_excess': excess(keys) == excess(missing_keys),
              'raw_token_curve_exact_match': True, 'single30_curve_exact_match': True,
              'raw_token_support_curves': raw_curve, 'single30_support_curves': single_curve,
              'reference_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in (raw_ref_path, single_ref_path)},
              'limits': ['Root failed assertion and original result/code remain untouched',
                         'No RNA, clone_size, per-gate target, HTTP or fits',
                         'Raw concatenated barcode token is not necessarily a biological clone',
                         'Sampling support is not biological signal/performance or independent task count',
                         'Matrix-header row-id correspondence must be authenticated before a future expression join']}
    with OUT.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ('raw_token_support_curves', 'single30_support_curves')}, indent=2))


if __name__ == '__main__':
    main()
