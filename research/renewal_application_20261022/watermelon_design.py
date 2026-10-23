"""Summarize only frozen whitelisted design strings in released metadata."""
from collections import Counter
import csv
import gzip
import io
import json

from lineage_followup import OUT


SPECS = (
    ('GSE150949_metaData_with_lineage_txt_gz.body', '\t',
     ('orig.ident', 'sample_id', 'time_point', 'sample_name', 'sample_type')),
    ('GSE150949_pooled_watermelon_metadata_matrix_csv_gz.body', ',',
     ('orig.ident', 'sample_id', 'sample_type', 'sample_pool', 'cell_line', 'droplet.type', 'experiment')),
)


def main():
    result = []
    for filename, delimiter, allowed in SPECS:
        with gzip.open(OUT / filename, 'rt', encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream, delimiter=delimiter)
            header = next(reader)
            positions = [header.index(name) for name in allowed]
            counts = Counter()
            widths = Counter()
            for fields in reader:
                widths[len(fields)] += 1
                offset = len(fields) - len(header)
                assert offset in (0, 1), (filename, len(fields), len(header))
                counts[tuple(fields[index + offset] for index in positions)] += 1
        result.append({'file': filename, 'header': header, 'allowed_fields': allowed,
                       'rows': sum(counts.values()), 'row_width_counts': dict(widths),
                       'design_tuples': [dict(zip(allowed, key), captured_rows=count)
                                         for key, count in sorted(counts.items())]})
    with (OUT / 'WATERMELON_DESIGN_RESULT.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
