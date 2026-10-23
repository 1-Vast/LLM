"""Reconstruct only allowed source-pair endpoints from exact author guide tables."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_function_reliability'
RENAMES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP', 'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}


def target(guide):
    name = guide.split('_')[0]
    return RENAMES.get(name, name)


def parse_allowed(rows, allowed):
    header = rows[0][1:]
    values = defaultdict(dict)
    converted = 0
    for row in rows[1:]:
        first = target(row[0])
        for column, raw in zip(header, row[1:]):
            second = target(column)
            if first == second or '|'.join(sorted([first, second])) not in allowed:
                continue
            value = float(raw) if raw.strip() else math.nan
            values[(first, second)][(row[0], column)] = value
            converted += 1
    return values, converted


def sequential_mean(values):
    # Author averages rows (skipna), transposes, then averages original columns.
    columns = defaultdict(list)
    for (_, column), value in values.items():
        if math.isfinite(value):
            columns[column].append(value)
    means = [np.mean(v) for v in columns.values() if v]
    return float(np.mean(means)) if means else math.nan


def reconstruct(values, first, second):
    a = sequential_mean(values.get((first, second), {}))
    b = sequential_mean(values.get((second, first), {}))
    return (a + b) / 2 if math.isfinite(a) and math.isfinite(b) else math.nan


def main():
    existing = pd.read_csv(ROOT / 'log/20261022/norman_numeric_qualification/FUNCTION_SOURCE_DEVELOPMENT.csv')
    existing = existing[existing['split'].eq('source')].copy()
    assert len(existing) == existing.pair.nunique() == 3160
    allowed = set(existing.pair)
    tables, counts = {}, {}
    for rep in ['1', '2', 'Average']:
        with (OUT / 'root_sources' / (rep + '.body')).open(newline='') as stream:
            values, counts[rep] = parse_allowed(list(csv.reader(stream, delimiter='\t')), allowed)
        tables[rep] = values
    results = []
    for row in existing.itertuples():
        record = {'pair': row.pair, 'gene_a': row.gene_a, 'gene_b': row.gene_b, 'growth': row.growth}
        for rep, values in tables.items():
            record['replicate' + rep] = reconstruct(values, row.gene_a, row.gene_b)
            guide_values = values.get((row.gene_a, row.gene_b), {})
            record['finite_guide_cells_' + rep] = sum(math.isfinite(v) for v in guide_values.values())
        first = tables['1'].get((row.gene_a, row.gene_b), {})
        second = tables['2'].get((row.gene_a, row.gene_b), {})
        common = sorted(k for k in first if math.isfinite(first[k]) and math.isfinite(second[k]))
        record['within_pair_guide_replicate_mse'] = float(np.mean([(first[k] - second[k]) ** 2 for k in common]))
        record['within_pair_guide_sd_rep1'] = float(np.std([first[k] for k in common]))
        record['within_pair_guide_sd_rep2'] = float(np.std([second[k] for k in common]))
        results.append(record)
    result = pd.DataFrame(results)
    result.to_csv(OUT / 'SOURCE_REPLICATES.csv', index=False)
    complete = result[['replicate1', 'replicate2', 'replicateAverage']].notna().all(axis=1)
    identity_error = np.abs(result.replicateAverage - result.growth)
    finite_keys = {rep: {(orientation, key) for orientation, group in values.items()
                         for key, value in group.items() if math.isfinite(value)}
                   for rep, values in tables.items()}
    support_equal = finite_keys['1'] == finite_keys['2'] == finite_keys['Average']
    report = {'source_pairs': len(result), 'complete_replicate_pairs': int(complete.sum()),
              'numeric_guide_cells_converted': counts, 'non_source_values_converted': 0,
              'finite_guide_support_equal': support_equal,
              'finite_guide_cells': {rep: len(keys) for rep, keys in finite_keys.items()},
              'max_average_endpoint_reconstruction_error': float(identity_error.max()),
              'mean_average_endpoint_reconstruction_error': float(identity_error.mean()),
              'max_separately_averaged_replicates_difference': float(np.abs((result.replicate1 + result.replicate2) / 2 - result.replicateAverage).max()),
              'status': 'PASS_ENDPOINT_IDENTITY' if complete.all() and support_equal and identity_error.max() < 1e-12 else 'REVISE_ENDPOINT_OR_COVERAGE',
              'scope': 'Source-only endpoint reconstruction; not a variance/causal/noise-ceiling test'}
    (OUT / 'QUALIFICATION.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
