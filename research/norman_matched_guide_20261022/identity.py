"""Compare authoritative mapping variants without reading bulk phenotype columns."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide'
SRC = OUT / 'root_sources'
aliases = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP', 'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}
final = json.loads((SRC / 'chosen_final.schema.json').read_text())['gene_to_guide_id']
sharing = json.loads((SRC / 'chosen_sharing.schema.json').read_text())['gene_to_guide_id']
assert len(final.values()) == len(set(final.values()))
mapped = {aliases.get(g, g): guide for g, guide in final.items()}
existing = set(json.loads((ROOT / 'log/20261022/norman_functional_contract/IDENTITY_JOIN.json').read_text())['matched_single_genes']) - {'BAK1', 'BCL2L11'}
pair_schema = json.loads((SRC / 'unfiltered_pairs.schema.json').read_text())
row_ids, column_ids = set(pair_schema['row_ids']), set(pair_schema['header'][1:])
single_ids = set(json.loads((SRC / 'unfiltered_singles.schema.json').read_text())['row_ids'])
eligible = {gene: guide for gene, guide in mapped.items()
            if gene in existing and guide in row_ids & column_ids & single_ids}
report = {'final_map_genes': len(final), 'sharing_map_genes': len(sharing),
          'common_mapping_conflicts': [g for g in final.keys() & sharing.keys() if final[g] != sharing[g]],
          'sharing_only_genes': sorted(set(sharing) - set(final)),
          'current_RNA_panel': len(existing), 'eligible_final_map_RNA_genes': len(eligible),
          'RNA_genes_missing_final_map': sorted(existing - set(mapped)),
          'final_mapped_RNA_genes_missing_guide_axis_or_single_table': sorted((existing & set(mapped)) - set(eligible)),
          'gene_to_guide': eligible, 'numeric_assay_values_decoded': False,
          'decision': 'Use final_emaps mapping prospectively, no imputation/extra-sharing-gene rescue'}
(OUT / 'IDENTITY.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'gene_to_guide'}, indent=2))

