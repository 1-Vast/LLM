"""Export only source/development pair labels; never numerically parse protected values."""
from collections import Counter
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/norman_functional_contract'
OUT = ROOT / 'log/20261022/norman_numeric_qualification'
OUT.mkdir(parents=True, exist_ok=True)
EXCLUDE = {'BAK1', 'BCL2L11'}


def allowed_values(matrix_rows, splits, eligible):
    """Convert only explicit source/dev nonself pair cells; keep missing distinct from0."""
    header = matrix_rows[0][1:]
    values = {}
    converted = 0
    for row in matrix_rows[1:]:
        first = row[0]
        if first not in eligible:
            continue
        for second, raw in zip(header, row[1:]):
            if first == second or second not in eligible:
                continue
            pair = '|'.join(sorted([first, second]))
            if splits.get(pair) not in ('source', 'development'):
                continue
            number = float(raw) if raw.strip() else math.nan
            values[(first, second)] = number
            converted += 1
    return values, converted


def main():
    with (BASE / 'PAIR_SPLITS.csv').open(newline='') as stream:
        split_rows = list(csv.DictReader(stream))
    splits = {r['pair']: r['split'] for r in split_rows}
    genes = set(json.loads((BASE / 'IDENTITY_JOIN.json').read_text())['matched_single_genes']) - EXCLUDE
    with (BASE / 'data/processed_fitnesses.csv').open(newline='') as stream:
        values, converted = allowed_values(list(csv.reader(stream)), splits, genes)
    records = []
    stats = Counter()
    asymmetries = []
    for row in split_rows:
        first, second = row['gene_a'], row['gene_b']
        if row['split'] == 'protected' or not {first, second} <= genes:
            continue
        stats[row['split'] + '_potential'] += 1
        a = values.get((first, second), math.nan)
        b = values.get((second, first), math.nan)
        if not math.isfinite(a) or not math.isfinite(b):
            stats[row['split'] + '_missing'] += 1
            continue
        asymmetries.append(abs(a - b))
        value = (a + b) / 2
        stats[row['split'] + '_finite'] += 1
        stats['real_zero_pairs'] += value == 0
        records.append({**row, 'growth': value, 'mirror_abs_difference': abs(a - b)})
    with (OUT / 'FUNCTION_SOURCE_DEVELOPMENT.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    priors = []
    with (BASE / 'data/single_fitnesses.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            gene = row['guide_target']
            if gene in genes:
                value = float(row['average_fitness'])
                assert math.isfinite(value)
                priors.append({'gene': gene, 'average_fitness': value})
    with (OUT / 'SINGLE_GROWTH_PRIORS.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['gene', 'average_fitness'])
        writer.writeheader()
        writer.writerows(priors)
    report = {'counts': dict(stats), 'numeric_matrix_cells_converted': converted,
              'protected_values_converted': 0, 'protected_missingness_checked': False,
              'max_source_development_mirror_difference': max(asymmetries),
              'single_growth_prior_genes': len(priors), 'panel_before_RNA_QC': len(genes)}
    (OUT / 'FUNCTION_MASK_REPORT.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
