"""Check single-perturbation target membership without decoding numerical fields."""
import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract'
DATA = OUT / 'data'
renames = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}
schema = json.loads((DATA / 'processed_fitnesses.csv.schema.json').read_text())
fitness_rows = {renames.get(g, g) for g in schema['row_ids']}
fitness_columns = {renames.get(g, g) for g in schema['header'][1:]}
targets = set()
with gzip.open(DATA / 'GSE133344_filtered_cell_identities.csv.gz', 'rt') as stream:
    for row in csv.DictReader(stream):
        identity = row['guide_identity']
        if identity:
            targets.add(identity.split('__')[0])
singles = set()
unclassified = []
for identity in sorted(targets):
    parts = identity.split('_')
    if len(parts) != 2:
        unclassified.append(identity)
        continue
    genes = [renames.get(g, g) for g in parts if not g.startswith('NegCtrl')]
    if len(genes) == 1:
        singles.add(genes[0])
overlap = singles & fitness_rows & fitness_columns
result = {'fitness_rows': len(fitness_rows), 'fitness_columns': len(fitness_columns),
          'rows_equal_columns': fitness_rows == fitness_columns,
          'unique_guide_target_strings': len(targets), 'single_target_genes': len(singles),
          'single_genes_in_fitness_axes': len(overlap), 'matched_single_genes': sorted(overlap),
          'single_genes_not_both_fitness_axes': sorted(singles - overlap),
          'unclassified_identity_strings': unclassified,
          'potential_unordered_nonself_pairs': len(overlap) * (len(overlap) - 1) // 2,
          'assay_missingness_checked': False, 'matrix_expression_acquired': False,
          'numeric_assay_or_cell_fields_decoded': False,
          'scope': 'Filtered identity membership only; not RNA matrix join or functional completeness'}
(OUT / 'IDENTITY_JOIN.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'matched_single_genes'}, indent=2))
