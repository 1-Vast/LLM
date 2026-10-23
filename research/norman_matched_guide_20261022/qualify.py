"""Exact source-only chosen-guide pair and single-prior equivalence checks."""
import csv
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide'
ALIASES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP', 'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}


def masked_matrix(rows, pair_keys, selected_guides=None):
    header = rows[0][1:]
    if selected_guides is None:
        normalize = lambda g: ALIASES.get(g, g)
        assert len({normalize(g) for g in header}) == len(header)
        assert len({normalize(row[0]) for row in rows[1:]}) == len(rows) - 1
    else:
        assert len(set(selected_guides.values())) == len(selected_guides)
        inverse = {guide: gene for gene, guide in selected_guides.items()}
        normalize = lambda g: inverse.get(g)
    values, converted = {}, 0
    for row in rows[1:]:
        first = normalize(row[0])
        if first is None:
            continue
        for column, raw in zip(header, row[1:]):
            second = normalize(column)
            if second is None or first == second or '|'.join(sorted([first, second])) not in pair_keys:
                continue
            assert (first, second) not in values
            values[(first, second)] = float(raw) if raw.strip() else math.nan
            converted += 1
    return values, converted


def main():
    mapping = json.loads((OUT / 'IDENTITY.json').read_text())['gene_to_guide']
    source = pd.read_csv(ROOT / 'log/20261022/norman_function_reliability/SOURCE_REPLICATES.csv')
    assert len(source) == 3160 and source.pair.is_unique
    source = source[source.gene_a.isin(mapping) & source.gene_b.isin(mapping)].copy()
    keys = set(source.pair)
    original = ROOT / 'log/20261022/norman_functional_contract/data'
    with (OUT / 'root_sources/unfiltered_pairs.body').open(newline='') as stream:
        reconstructed, raw_count = masked_matrix(list(csv.reader(stream, delimiter='\t')), keys, mapping)
    with (original / 'processed_perturbseq_fitnesses.csv').open(newline='') as stream:
        candidate, candidate_count = masked_matrix(list(csv.reader(stream)), keys)
    pair_records = []
    orientation_differences = []
    for row in source.itertuples():
        values = [reconstructed.get((row.gene_a, row.gene_b), math.nan),
                  reconstructed.get((row.gene_b, row.gene_a), math.nan),
                  candidate.get((row.gene_a, row.gene_b), math.nan),
                  candidate.get((row.gene_b, row.gene_a), math.nan)]
        finite = all(math.isfinite(v) for v in values)
        if finite:
            orientation_differences.extend([abs(values[0] - values[2]), abs(values[1] - values[3])])
        raw_mean, candidate_mean = np.mean(values[:2]), np.mean(values[2:])
        pair_records.append({'pair': row.pair, 'gene_a': row.gene_a, 'gene_b': row.gene_b,
                             'original_gene_average_growth': row.growth,
                             'chosen_raw_growth': raw_mean, 'chosen_processed_growth': candidate_mean,
                             'both_orientations_finite': finite, 'absolute_difference': abs(raw_mean - candidate_mean)})
    pairs = pd.DataFrame(pair_records)
    pairs.to_csv(OUT / 'SOURCE_MATCHED_ENDPOINT.csv', index=False)
    single_raw = {}
    inverse = {guide: gene for gene, guide in mapping.items()}
    with (OUT / 'root_sources/unfiltered_singles.body').open(newline='') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row[''] in inverse:
                assert inverse[row['']] not in single_raw
                single_raw[inverse[row['']]] = float(row['b.mean'])
    single_candidate = {}
    with (original / 'single_fitnesses.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            gene = ALIASES.get(row['guide_target'], row['guide_target'])
            if gene in mapping:
                assert gene not in single_candidate
                single_candidate[gene] = float(row['chosen_guide_fitness']) if row['chosen_guide_fitness'].strip() else math.nan
    singles = pd.DataFrame([{'gene': gene, 'chosen_guide_id': mapping[gene],
                             'raw_b_mean': single_raw.get(gene, math.nan),
                             'candidate_chosen_prior': single_candidate.get(gene, math.nan)} for gene in sorted(mapping)])
    singles['absolute_difference'] = abs(singles.raw_b_mean - singles.candidate_chosen_prior)
    singles.to_csv(OUT / 'CHOSEN_SINGLE_PRIORS.csv', index=False)
    max_pair = float(pairs.absolute_difference.max())
    max_single = float(singles.absolute_difference.max())
    all_finite = bool(pairs.both_orientations_finite.all() and np.isfinite(singles[['raw_b_mean', 'candidate_chosen_prior']]).all().all())
    report = {'eligible_genes': len(mapping), 'eligible_source_pairs': len(pairs),
              'all_pair_and_single_values_finite': all_finite,
              'numeric_source_pair_cells_raw': raw_count, 'numeric_source_pair_cells_candidate': candidate_count,
              'max_pair_orientation_discrepancy': max(orientation_differences) if orientation_differences else None,
              'max_pair_mean_discrepancy': max_pair, 'max_chosen_single_prior_discrepancy': max_single,
              'development_values_converted': 0, 'protected_values_converted': 0,
              'status': 'LOCAL_SOURCE_NUMERICAL_EQUIVALENCE_SUPPORTED' if all_finite and max_pair <= 1e-10 and max_single <= 1e-10 and max(orientation_differences) <= 1e-10 else 'STOP_CURRENT_MATCHED_ENDPOINT_LINKAGE',
              'scope': 'Local chosen-guide endpoint and b.mean agreement, not historical pipeline completeness or predictive benefit'}
    (OUT / 'QUALIFICATION.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
