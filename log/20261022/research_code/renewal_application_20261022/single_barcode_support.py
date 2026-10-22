"""Conservative single-called barcode support; counts are not growth or fate."""
from collections import Counter, defaultdict
import csv
import gzip
import json
import re

from lineage_followup import OUT
from lineage_support import EXPECTED, split


def main():
    groups = defaultdict(Counter)
    exclusions = Counter()
    sample_keys = Counter()
    row_ids = Counter()
    with gzip.open(OUT / 'GSE150949_metaData_with_lineage_txt_gz.body', 'rt', encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, delimiter='\t')
        header = next(reader)
        positions = {name: header.index(name) + 1 for name in
                     ('lineage_barcode', 'sample_name', 'sample_id', 'time_point', 'full_cell_barcode')}
        for fields in reader:
            assert len(fields) == len(header) + 1
            row = {name: fields[index] for name, index in positions.items()}
            row_ids[fields[0]] += 1
            sample_keys[(row['sample_id'], row['full_cell_barcode'])] += 1
            sample_id, time, group = EXPECTED[row['sample_name']]
            assert (sample_id, time) == (row['sample_id'], row['time_point'])
            lineage = row['lineage_barcode']
            if re.fullmatch('[ACGT]{30}', lineage) is None:
                exclusions[group] += 1
                continue
            groups[group][lineage] += 1
    curves = []
    for early in (0, 3, 7):
        names = ['day0', 'day14_rep1', 'day14_rep2'] if early == 0 else [
            'day' + str(early) + '_rep1', 'day' + str(early) + '_rep2', 'day14_rep1', 'day14_rep2']
        universe = set.intersection(*(set(groups[name]) for name in names))
        for threshold in (1, 2, 3, 5):
            selected = [barcode for barcode in universe if all(groups[name][barcode] >= threshold for name in names)]
            partitions = Counter(split(barcode) for barcode in selected)
            curves.append({'early_day': early, 'minimum_cells_each_group': threshold,
                           'single_called_barcodes': len(selected),
                           'partitions': {key: partitions[key] for key in ('source', 'development', 'test')}})
    result = {'kind': 'single_called_barcode_sampling_support_only',
              'selected_rows': sum(sum(count.values()) for count in groups.values()),
              'excluded_rows': sum(exclusions.values()),
              'groups': {name: {'unique_single_called_barcodes': len(count), 'selected_cells': sum(count.values()),
                                'excluded_cells': exclusions[name]} for name, count in sorted(groups.items())},
              'duplicate_sample_cell_keys': sum(count - 1 for count in sample_keys.values()),
              'duplicate_row_identifiers': sum(count - 1 for count in row_ids.values()),
              'support_curves': curves,
              'minimal_pilot_support_flags': {str(day): next(x['partitions']['test'] >= 30 for x in curves
                                                           if x['early_day'] == day and x['minimum_cells_each_group'] == 1)
                                              for day in (0, 3, 7)},
              'new_biological_fits': 0, 'raw_per_gate_targets_read': False}
    with (OUT / 'SINGLE_BARCODE_SUPPORT_RESULT.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    assert not result['duplicate_sample_cell_keys'] and not result['duplicate_row_identifiers']


if __name__ == '__main__':
    main()
