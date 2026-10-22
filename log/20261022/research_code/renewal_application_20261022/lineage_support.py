"""Boolean metadata support audit, without RNA, clone size or per-gate targets."""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json

from lineage_followup import OUT


EXPECTED = {
    '0': ('1', '0', 'day0'),
    '3_rep1': ('2', '3', 'day3_rep1'), '3_rep2': ('3', '3', 'day3_rep2'),
    '7_rep1': ('4', '7', 'day7_rep1'), '7_rep2': ('5', '7', 'day7_rep2'),
    '14_rep1_high': ('6', '14', 'day14_rep1'), '14_rep1_med': ('7', '14', 'day14_rep1'),
    '14_rep1_low': ('8', '14', 'day14_rep1'), '14_rep2_high': ('9', '14', 'day14_rep2'),
    '14_rep2_med': ('10', '14', 'day14_rep2'), '14_rep2_low': ('11', '14', 'day14_rep2'),
}
MISSING = {'', 'NA', 'NaN', 'nan', 'None', 'null'}


def split(lineage):
    number = int(hashlib.sha256(('watermelon-support-v1|' + lineage).encode()).hexdigest()[:8], 16) % 10
    return 'source' if number < 6 else 'development' if number < 8 else 'test'


def main():
    counts = defaultdict(Counter)
    missing = Counter()
    formats = Counter()
    cells = Counter()
    with gzip.open(OUT / 'GSE150949_metaData_with_lineage_txt_gz.body', 'rt', encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, delimiter='\t')
        header = next(reader)
        pos = {name: header.index(name) for name in
               ('lineage_barcode', 'full_cell_barcode', 'sample_name', 'sample_id', 'time_point')}
        for fields in reader:
            offset = len(fields) - len(header)
            assert offset == 1
            row = {name: fields[index + offset] for name, index in pos.items()}
            expected_id, expected_time, group = EXPECTED[row['sample_name']]
            assert (row['sample_id'], row['time_point']) == (expected_id, expected_time)
            cells[row['full_cell_barcode']] += 1
            lineage = row['lineage_barcode']
            if lineage in MISSING:
                missing[group] += 1
                continue
            formats[(len(lineage), ''.join(sorted(set(lineage))))] += 1
            counts[group][lineage] += 1
    groups = sorted(counts)
    intersections = {left: {right: len(counts[left].keys() & counts[right].keys()) for right in groups}
                     for left in groups}
    curves = []
    for early in (0, 3, 7):
        names = ['day0', 'day14_rep1', 'day14_rep2'] if early == 0 else [
            'day' + str(early) + '_rep1', 'day' + str(early) + '_rep2', 'day14_rep1', 'day14_rep2']
        universe = set.intersection(*(set(counts[name]) for name in names))
        for threshold in (1, 2, 3, 5):
            eligible = [lineage for lineage in universe if all(counts[name][lineage] >= threshold for name in names)]
            partition = Counter(split(lineage) for lineage in eligible)
            curves.append({'early_day': early, 'minimum_cells_each_group': threshold,
                           'lineages': len(eligible), 'partitions': {key: partition[key] for key in ('source', 'development', 'test')}})
    result = {
        'kind': 'metadata_sampling_support_only', 'biological_performance_evaluations': 0,
        'groups': {name: {'unique_lineages': len(counts[name]), 'captured_nonmissing_cells': sum(counts[name].values()),
                          'captured_missing_lineage_cells': missing[name]} for name in groups},
        'lineage_formats': [{'length': key[0], 'alphabet': key[1], 'rows': value} for key, value in sorted(formats.items())],
        'duplicated_full_cell_identifiers': sum(value - 1 for value in cells.values()),
        'intersection_matrix': intersections, 'support_curves': curves,
        'pilot_minimal_test_support_passes': {str(day): next(x['partitions']['test'] >= 30 for x in curves
                                                     if x['early_day'] == day and x['minimum_cells_each_group'] == 1)
                                              for day in (0, 3, 7)},
        'physical_cultures': 2, 'independent_later_research_tasks_established': 0,
    }
    with (OUT / 'LINEAGE_SUPPORT_RESULT.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
